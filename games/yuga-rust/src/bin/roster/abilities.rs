use super::{lab::Lab, model::*};
use std::f64::consts::PI;

impl Lab {
    fn zone(
        &mut self,
        i: usize,
        slot: usize,
        ability: &Ability,
        pos: Point,
        power: f64,
        life: f64,
        mechanic: Option<Mechanic>,
    ) {
        if self.zones.len() >= self.rules.max_zones {
            self.zones.remove(0);
        }
        let id = self.next_object();
        self.zones.push(Zone {
            id,
            owner: self.units[i].id.clone(),
            slot,
            team: self.units[i].team,
            kind: ability.kind,
            mechanic,
            x: pos[0],
            z: pos[1],
            radius: ability.radius,
            power,
            life,
            duration: life,
        });
    }
    fn summon(&mut self, i: usize, slot: usize, ability: &Ability) {
        let caster = &self.units[i];
        let center = caster.pos;
        let team = caster.team;
        let kit = caster.kit;
        let owner = caster.id.clone();
        for offset in [-1.3, 1.3] {
            if self.units.len() >= self.rules.max_actors {
                return;
            }
            let spawn = [center[0] + offset, center[1]];
            let points = std::iter::once(spawn).chain([1.3, 2.6].into_iter().flat_map(|radius| {
                (0..8).map(move |j| {
                    let a = f64::from(j) * PI / 4.;
                    [spawn[0] + a.cos() * radius, spawn[1] + a.sin() * radius]
                })
            }));
            if let Some(pos) = points
                .into_iter()
                .find(|p| !self.world.blocked(p[0], p[1], 0.42))
            {
                self.serial += 1;
                let mut unit = Actor::new(
                    &format!("summon-{}", self.serial),
                    team,
                    kit,
                    &self.heroes[kit],
                    pos,
                );
                unit.kind = "minion";
                unit.max_hp = 105.;
                unit.hp = 105.;
                unit.attack = ability.power;
                unit.expires_at = Some(self.time + (ability.duration * 3.).max(6.));
                let z = if team == "sun" { 66. } else { -66. };
                unit.waypoint = usize::from(distance(pos, [4.5, z]) < distance(pos, [4.5, -z]));
                self.events.push(
                    EventKind::Ability,
                    Source {
                        actor: &owner,
                        team,
                        slot: Some(slot),
                    },
                    Some(&unit.id),
                    None,
                    pos,
                    self.time,
                );
                self.units.push(unit);
            }
        }
    }
    pub fn cast(&mut self, i: usize, slot: usize, yaw: f64, pitch: f64) -> bool {
        let actor = &mut self.units[i];
        if actor.hp <= 0. || actor.cast.is_some() || actor.cds[slot] > 0. {
            return false;
        }
        let ability = self.heroes[actor.kit].abilities[slot].clone();
        let origin = actor.pos;
        let team = actor.team;
        let owner = actor.id.clone();
        let source = Source {
            actor: &owner,
            team,
            slot: Some(slot),
        };
        self.events
            .push(EventKind::Ability, source, None, None, origin, self.time);
        actor.yaw = yaw;
        actor.cds[slot] = ability.cooldown;
        let mut point = self
            .world
            .ground_aim(origin, actor.y, yaw, pitch, ability.range);
        if let Some(mechanic) = ability.mechanic {
            if mechanic == Mechanic::MithilaSanctuary {
                point = origin;
            }
            let release = self.time + ability.windup.unwrap_or(0.8);
            actor.cast = Some(Cast {
                slot,
                mechanic,
                release,
                end: release
                    + if mechanic == Mechanic::MountainDescent {
                        0.45
                    } else {
                        0.
                    },
                origin,
                target: point,
                yaw,
                pitch,
                phase: "windup",
            });
            return true;
        }
        let mut zone = origin;
        match ability.kind {
            Kind::Bolt | Kind::Line => {
                let (speed, radius) = if ability.kind == Kind::Line {
                    (62., 0.5)
                } else {
                    (38., 0.75)
                };
                self.shoot(
                    i,
                    Some(slot),
                    ability.power,
                    speed,
                    radius,
                    (ability.range / speed).max(0.3),
                    yaw,
                    pitch,
                );
                return true;
            }
            Kind::Burst | Kind::Cone | Kind::Nova => {
                for u in self
                    .units
                    .iter_mut()
                    .filter(|u| u.team != team && u.hp > 0. && self.world.line_clear(origin, u.pos))
                {
                    let d = distance(origin, u.pos);
                    let a = (u.pos[0] - origin[0]).atan2(u.pos[1] - origin[1]) - yaw;
                    let hit = if ability.kind == Kind::Nova {
                        d <= ability.radius
                    } else {
                        d <= ability.range
                            && a.cos()
                                > if ability.kind == Kind::Cone {
                                    0.55
                                } else {
                                    0.25
                                }
                    };
                    if hit {
                        self.events.hurt(source, u, ability.power, u.pos, self.time);
                    }
                }
            }
            Kind::Heal | Kind::Ward => {
                for u in self.units.iter_mut().filter(|u| {
                    u.team == team
                        && u.hp > 0.
                        && distance(u.pos, origin) <= ability.radius
                        && self.world.line_clear(origin, u.pos)
                }) {
                    if ability.kind == Kind::Heal {
                        self.events.heal(source, u, ability.power, self.time);
                    } else {
                        self.events
                            .ward(source, u, ability.power, ability.duration, self.time);
                    }
                }
            }
            Kind::Dash | Kind::Leap => {
                actor.pos = self.world.move_actor(
                    origin,
                    [yaw.sin() * ability.range, yaw.cos() * ability.range],
                    0.65,
                );
                if ability.kind == Kind::Leap {
                    actor.vy = 9.;
                }
                zone = actor.pos;
            }
            Kind::Slow => {
                let life = ability.duration.max(1.);
                self.zone(i, slot, &ability, point, ability.power / life, life, None);
                return true;
            }
            Kind::Pull => {
                for u in self.units.iter_mut().filter(|u| {
                    u.team != team
                        && u.hp > 0.
                        && distance(u.pos, point) <= ability.radius
                        && self.world.line_clear(origin, u.pos)
                }) {
                    self.events.hurt(source, u, ability.power, u.pos, self.time);
                    let d = distance(u.pos, point);
                    if d > 0.1 && u.hp > 0. {
                        let f = d.min(6.) / d;
                        u.pos = self.world.move_actor(
                            u.pos,
                            [(point[0] - u.pos[0]) * f, (point[1] - u.pos[1]) * f],
                            if u.kind == "hero" { 0.65 } else { 0.42 },
                        );
                    }
                }
                zone = point;
            }
            Kind::Summon => self.summon(i, slot, &ability),
        }
        self.zone(i, slot, &ability, zone, 0., 0.7, None);
        true
    }
    pub fn advance_cast(&mut self, i: usize) -> bool {
        let Some(mut cast) = self.units[i].cast.take() else {
            return false;
        };
        self.units[i].yaw = cast.yaw;
        if self.time + 1e-7 < cast.release {
            self.units[i].cast = Some(cast);
            return true;
        }
        let ability = self.heroes[self.units[i].kit].abilities[cast.slot].clone();
        let team = self.units[i].team;
        let owner = self.units[i].id.clone();
        let source = Source {
            actor: &owner,
            team,
            slot: Some(cast.slot),
        };
        match cast.mechanic {
            Mechanic::DawnVolley => {
                for spread in [-0.12, 0., 0.12] {
                    self.shoot(
                        i,
                        Some(cast.slot),
                        ability.power,
                        62.,
                        0.5,
                        ability.range / 62.,
                        cast.yaw + spread,
                        cast.pitch,
                    );
                }
            }
            Mechanic::MountainDescent => {
                let phase = ((self.time - cast.release) / 0.45).clamp(0., 1.);
                cast.phase = "travel";
                let unit = &mut self.units[i];
                let pos = unit.pos;
                let dest: [f64; 2] = std::array::from_fn(|axis| {
                    cast.origin[axis] + (cast.target[axis] - cast.origin[axis]) * phase - pos[axis]
                });
                unit.pos = self.world.move_actor(pos, dest, 0.65);
                unit.y = (PI * phase).sin() * 5.;
                unit.vy = 0.;
                if self.time + 1e-7 < cast.end {
                    unit.cast = Some(cast);
                    return true;
                }
                unit.y = 0.;
                let center = unit.pos;
                for u in self.units.iter_mut().filter(|u| {
                    u.hp > 0.
                        && distance(u.pos, center) <= ability.radius
                        && self.world.line_clear(center, u.pos)
                }) {
                    if u.team == team {
                        self.events.heal(source, u, 45., self.time);
                    } else {
                        self.events.hurt(source, u, ability.power, u.pos, self.time);
                    }
                }
                self.zone(i, cast.slot, &ability, center, 0., 0.7, None);
            }
            Mechanic::MithilaSanctuary => {
                for u in self.units.iter_mut().filter(|u| {
                    u.team == team
                        && u.hp > 0.
                        && distance(u.pos, cast.origin) <= ability.radius
                        && self.world.line_clear(cast.origin, u.pos)
                }) {
                    self.events
                        .ward(source, u, ability.power, ability.duration, self.time);
                }
                self.zone(
                    i,
                    cast.slot,
                    &ability,
                    cast.origin,
                    9.,
                    ability.duration,
                    Some(Mechanic::MithilaSanctuary),
                );
            }
        }
        true
    }
}
