use super::{
    geometry::{Geometry, Solid},
    model::*,
};
use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Deserialize)]
struct Export {
    schema: u32,
    heroes: Vec<Hero>,
    solids: Vec<Solid>,
    rules: Rules,
}
pub struct Lab {
    pub heroes: Vec<Hero>,
    pub units: Vec<Actor>,
    pub shots: Vec<Shot>,
    pub zones: Vec<Zone>,
    pub world: Geometry,
    pub rules: Rules,
    pub time: f64,
    pub tick: u64,
    pub serial: u64,
}
impl Lab {
    pub fn load(id: &str) -> Result<Self, String> {
        let data: Export =
            serde_json::from_str(include_str!("../../../assets/classic-roster.json"))
                .map_err(|e| e.to_string())?;
        if data.schema != 1 {
            return Err("Unsupported roster export".into());
        }
        let mut units = Vec::new();
        for (name, team, hero, pos, injury) in [
            ("self", "sun", id, [0., 0.], 70.),
            ("ally", "sun", "rama", [1., 2.], 70.),
            ("enemy", "moon", "ravana", [0., 3.], 0.),
        ] {
            let index = data
                .heroes
                .iter()
                .position(|h| h.id == hero)
                .ok_or_else(|| format!("Unknown hero {hero}"))?;
            let mut unit = Actor::new(name, team, index, &data.heroes[index], pos);
            unit.hp -= injury;
            units.push(unit);
        }
        Ok(Self {
            heroes: data.heroes,
            units,
            shots: Vec::new(),
            zones: Vec::new(),
            world: Geometry::new(data.solids),
            rules: data.rules,
            time: 0.,
            tick: 0,
            serial: 0,
        })
    }
    pub fn snapshot(&self, accepted: Option<bool>) -> Value {
        json!({"tick":self.tick,"time":self.time,"units":self.units,"projectiles":self.shots,"zones":self.zones,"accepted":accepted})
    }
    pub fn command(&mut self, input: &Input) -> Result<Value, String> {
        let i = self
            .units
            .iter()
            .position(|u| u.id == input.actor.as_deref().unwrap_or("self") && u.kind == "hero")
            .ok_or("Choose self, ally or enemy")?;
        if input.ticks > 3600
            || input.cast.is_some_and(|s| s >= 3)
            || !input
                .movement
                .into_iter()
                .chain([input.pitch, input.yaw.unwrap_or(0.)])
                .all(f64::is_finite)
        {
            return Err("Expected a finite input, slot 0..2 and at most 3600 ticks".into());
        }
        let yaw = input.yaw.unwrap_or(self.units[i].yaw);
        let yaw = yaw.sin().atan2(yaw.cos());
        let pitch = input.pitch.clamp(-1.35, 1.35);
        let accepted = input.cast.map(|slot| self.cast(i, slot, yaw, pitch));
        for _ in 0..input.ticks {
            self.step(i, input, yaw, pitch);
        }
        Ok(self.snapshot(accepted))
    }
    pub fn shoot(
        &mut self,
        i: usize,
        damage: f64,
        speed: f64,
        radius: f64,
        life: f64,
        yaw: f64,
        pitch: f64,
    ) {
        if self.shots.len() >= self.rules.max_projectiles {
            return;
        }
        let unit = &self.units[i];
        let (dx, dy, dz) = (
            yaw.sin() * pitch.cos(),
            pitch.sin(),
            yaw.cos() * pitch.cos(),
        );
        self.shots.push(Shot {
            owner: unit.id.clone(),
            team: unit.team,
            x: unit.pos[0] + dx * 0.8,
            z: unit.pos[1] + dz * 0.8,
            y: unit.y + if unit.kind == "hero" { 1.2 } else { 0.7 },
            vx: dx * speed,
            vy: dy * speed,
            vz: dz * speed,
            damage,
            radius,
            life,
        });
    }
    fn advance_shots(&mut self) {
        let world = &self.world;
        let units = &mut self.units;
        self.shots.retain_mut(|p| {
            let dt = DT.min(p.life);
            p.life = (p.life - dt).max(0.);
            let steps = ((p.vx.hypot(p.vy).hypot(p.vz) * dt / 0.35).ceil() as u32).max(1);
            for _ in 0..steps {
                p.x += p.vx * dt / f64::from(steps);
                p.y += p.vy * dt / f64::from(steps);
                p.z += p.vz * dt / f64::from(steps);
                if world.shot_blocked(p.x, p.y, p.z, p.radius) {
                    return false;
                }
                for unit in units.iter_mut().filter(|u| u.team != p.team && u.hp > 0.) {
                    let (cy, body) = if unit.kind == "hero" {
                        (1.1, 0.95)
                    } else {
                        (0.7, 0.6)
                    };
                    if (unit.pos[0] - p.x)
                        .hypot(unit.y + cy - p.y)
                        .hypot(unit.pos[1] - p.z)
                        <= body + p.radius
                    {
                        unit.hurt(p.damage);
                        return false;
                    }
                }
            }
            p.life > 0.
        });
    }
    fn fire(&mut self, i: usize, pitch: f64) {
        let unit = &self.units[i];
        if unit.fire_cd > 0. || unit.cast.is_some() || unit.hp <= 0. {
            return;
        }
        let hero = &self.heroes[unit.kit];
        let (damage, speed, radius, life, interval) = if unit.kind == "hero" {
            (
                hero.damage,
                hero.projectile_speed,
                0.32,
                1.7,
                hero.fire_interval,
            )
        } else {
            (unit.attack, 25., 0.24, 0.6, 1.05)
        };
        self.shoot(i, damage, speed, radius, life, unit.yaw, pitch);
        self.units[i].fire_cd = interval;
    }
    fn sentinel(&mut self, i: usize) {
        let unit = &self.units[i];
        let (pos, team) = (unit.pos, unit.team);
        let nearest = self
            .units
            .iter()
            .filter(|u| {
                u.team != team
                    && u.hp > 0.
                    && distance(pos, u.pos) <= 11.
                    && self.world.line_clear(pos, u.pos)
            })
            .min_by(|a, b| {
                let score =
                    |u: &Actor| distance(pos, u.pos) - if u.kind == "hero" { 4. } else { 0. };
                score(a).total_cmp(&score(b))
            });
        let mut aimed = false;
        if let Some(target) = nearest {
            let d = distance(pos, target.pos);
            let height = target.y + if target.kind == "hero" { 1.1 } else { 0.7 };
            self.units[i].yaw = (target.pos[0] - pos[0]).atan2(target.pos[1] - pos[1]);
            self.fire(i, (height - 0.7).atan2(d.max(0.1)));
            if d < 8. {
                return;
            }
            aimed = true;
        }
        let z = if team == "sun" { 66. } else { -66. };
        let waypoints = [[4.5, -z], [4.5, z]];
        let mut ix = self.units[i].waypoint;
        if distance(pos, waypoints[ix]) < 3. && ix == 0 {
            ix = 1;
            self.units[i].waypoint = 1;
        }
        let [x, z] = waypoints[ix];
        let d = distance(pos, [x, z]);
        if d > 0.1 {
            if !aimed {
                self.units[i].yaw = (x - pos[0]).atan2(z - pos[1]);
            }
            let step = 4.3 * DT * if self.units[i].slow > 0. { 0.55 } else { 1. };
            self.units[i].pos = self.world.move_actor(
                pos,
                [(x - pos[0]) * step / d, (z - pos[1]) * step / d],
                0.42,
            );
        }
    }
    fn step(&mut self, selected: usize, input: &Input, yaw: f64, pitch: f64) {
        self.tick += 1;
        self.time += DT;
        let len = self.units.len();
        for i in 0..len {
            let u = &mut self.units[i];
            if u.expires_at.is_some_and(|t| self.time >= t) {
                u.hp = 0.;
                continue;
            }
            for cd in &mut u.cds {
                *cd = (*cd - DT).max(0.);
            }
            u.fire_cd = (u.fire_cd - DT).max(0.);
            u.ward = (u.ward - DT).max(0.);
            u.slow = (u.slow - DT).max(0.);
            if u.ward == 0. {
                u.shield = 0.;
            }
            if u.hp <= 0. {
                u.respawn = (u.respawn - DT).max(0.);
                if u.kind == "hero" && u.respawn == 0. {
                    u.hp = u.max_hp;
                    u.pos = [0., if u.team == "sun" { -66. } else { 66. }];
                    u.shield = 60.;
                    u.ward = 3.;
                    u.y = 0.;
                    u.vy = 0.;
                }
                continue;
            }
            if self.advance_cast(i) {
                continue;
            }
            let u = &mut self.units[i];
            if u.kind == "minion" {
                self.sentinel(i);
                continue;
            }
            if distance(u.pos, [0., if u.team == "sun" { -69. } else { 69. }]) < 12. {
                u.hp = (u.hp + 18. * DT).min(u.max_hp);
            }
            if i == selected {
                let mv = input.movement.map(|v| v.clamp(-1., 1.));
                let factor = self.heroes[u.kit].speed * DT * if u.slow > 0. { 0.55 } else { 1. }
                    / mv[0].hypot(mv[1]).max(1.);
                u.pos = self.world.move_actor(u.pos, mv.map(|v| v * factor), 0.65);
                u.yaw = yaw;
                if input.fire {
                    self.fire(i, pitch);
                }
            }
            let u = &mut self.units[i];
            let jump = i == selected && input.jump;
            if jump && !u.jumping && u.y <= 0. {
                u.vy = 9.;
            }
            u.jumping = jump;
            if u.y > 0. || u.vy > 0. {
                u.vy -= 18. * DT;
                u.y = (u.y + u.vy * DT).max(0.);
                if u.y == 0. {
                    u.vy = 0.;
                }
            }
        }
        for zone in &mut self.zones {
            let local_dt = DT.min(zone.life);
            zone.life -= DT;
            for unit in self.units.iter_mut().filter(|u| {
                u.hp > 0.
                    && distance(u.pos, [zone.x, zone.z]) <= zone.radius
                    && self.world.line_clear([zone.x, zone.z], u.pos)
            }) {
                if zone.mechanic == Some(Mechanic::MithilaSanctuary) && unit.team == zone.team {
                    unit.hp = (unit.hp + zone.power * local_dt).min(unit.max_hp);
                }
                if zone.kind == Kind::Slow && zone.life > 0. && unit.team != zone.team {
                    unit.slow = unit.slow.max(0.5);
                    unit.hurt(zone.power * DT);
                }
            }
        }
        self.zones.retain(|z| z.life > 0.);
        self.advance_shots();
        self.units.retain(|u| u.kind == "hero" || u.hp > 0.);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shield_absorbs_enemy_attack_and_cover_blocks_the_same_arc() {
        let mut lab = Lab::load("draupadi").unwrap();
        assert!(lab.cast(0, 0, 0., 0.));
        assert_eq!(lab.units[0].shield, 46.);
        assert!(lab.cast(2, 2, std::f64::consts::PI, 0.)); // Enemy Ravana's Crownfire
        assert_eq!(lab.units[0].shield, 0.);
        assert_eq!(lab.units[0].hp, 340. - 70. - 44.);
        assert_eq!(lab.units[1].hp, 230. - 44.);
        let mut lab = Lab::load("bhima").unwrap();
        lab.units[0].pos = [-13., -18.];
        lab.units[2].pos = [-10., -21.];
        assert!(!lab.world.line_clear(lab.units[0].pos, lab.units[2].pos));
        assert!(lab.cast(0, 0, 3. * std::f64::consts::PI / 4., 0.));
        assert_eq!(lab.units[2].hp, 390.);
    }

    #[test]
    fn leaving_locked_landing_avoids_damage_and_cooldown_rejection_preserves_state() {
        let mut lab = Lab::load("hanuman").unwrap();
        let c = Input {
            cast: Some(2),
            pitch: -0.35,
            ..Default::default()
        };
        assert_eq!(lab.command(&c).unwrap()["accepted"], true);
        let before = lab.snapshot(None);
        assert_eq!(lab.command(&c).unwrap()["accepted"], false);
        assert_eq!(before, lab.snapshot(None));
        let dodge = Input {
            actor: Some("enemy".into()),
            movement: [0., 1.],
            ticks: 23,
            ..Default::default()
        };
        lab.command(&dodge).unwrap();
        assert_eq!(lab.units[2].hp, 390.);
        assert!(lab.units[2].pos[1] > 10.);
        assert_eq!(lab.units[0].y, 0.);
        assert!(lab.units[0].cast.is_none());
    }

    #[test]
    fn missing_actor_and_invalid_command_do_not_mutate_the_session() {
        let mut lab = Lab::load("ulupi").unwrap();
        for command in [
            Input {
                actor: Some("wrong".into()),
                ticks: 1,
                ..Default::default()
            },
            Input {
                cast: Some(42),
                ..Default::default()
            },
            Input {
                ticks: 3601,
                ..Default::default()
            },
            Input {
                pitch: f64::INFINITY,
                ..Default::default()
            },
        ] {
            assert!(lab.command(&command).is_err());
            assert_eq!(lab.tick, 0);
        }
        assert!(Lab::load("unknown").is_err());
    }
}
