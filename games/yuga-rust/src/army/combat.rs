//! Lane target decisions, committed strikes and simultaneous damage eligibility.
//! Mirrors lane_army.gd::_acquire_targets and step_simulation's attack phase.
use super::{Army, Role, Team, Unit};
use crate::world::World;
use serde::Serialize;

const ATTACK_CAP: usize = 72;
const SIEGE_ATTACK_CAP: usize = 32;

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub(super) enum Attack {
    Normal {
        source: u32,
        team: Team,
        role: Role,
        target: u32,
        origin: [f32; 3],
        point: [f32; 2],
        start_tick: u64,
        due_tick: u64,
        damage: f32,
        reach: f32,
    },
    Siege {
        id: u32,
        source: u32,
        team: Team,
        role: Role,
        origin: [f32; 3],
        point: [f32; 2],
        start_tick: u64,
        due_tick: u64,
        damage: f32,
        radius: f32,
    },
}

impl Attack {
    fn source(&self) -> u32 {
        match self {
            Self::Normal { source, .. } | Self::Siege { source, .. } => *source,
        }
    }
    fn due_tick(&self) -> u64 {
        match self {
            Self::Normal { due_tick, .. } | Self::Siege { due_tick, .. } => *due_tick,
        }
    }
}

fn distance_sq([ax, az]: [f32; 2], [bx, bz]: [f32; 2]) -> f32 {
    let dx = ax - bx;
    let dz = az - bz;
    dx * dx + dz * dz
}

// Unit IDs increase in insertion order. Retiring a body preserves this order.
// Keep IDs in receipts; another simultaneous hit can retire an older corpse.
fn index_of(units: &[Unit], id: u32) -> Option<usize> {
    units.binary_search_by_key(&id, |u| u.id).ok()
}

impl Army {
    pub(super) fn pending_siege(&self) -> usize {
        self.attacks
            .iter()
            .filter(|a| matches!(a, Attack::Siege { .. }))
            .count()
    }

    pub(super) fn cancel_source_attacks(&mut self, id: u32) {
        self.attacks.retain(|strike| {
            if strike.source() != id {
                return true;
            }
            if matches!(strike, Attack::Siege { .. }) {
                self.totals.siege_cancelled += 1;
            }
            false
        });
    }

    fn acquire_targets(&mut self, world: &World) {
        for i in 0..self.units.len() {
            let seeker = &self.units[i];
            if seeker.death_tick.is_some() {
                continue;
            }
            let mut nearest_sq = seeker.role.stats().range.max(16.).powi(2);
            let mut choice = None;
            let enemy = seeker.team.other();
            for other in &self.units {
                if other.death_tick.is_some() || other.lane != seeker.lane || other.team != enemy {
                    continue;
                }
                let sq = distance_sq(seeker.xz, other.xz);
                // Strict comparison leaves an equal-distance tie with the first
                // unit in native spawn order and excludes the acquisition boundary.
                if sq < nearest_sq && world.clear_line(seeker.xz, other.xz) {
                    choice = Some(other.id);
                    nearest_sq = sq;
                }
            }
            self.units[i].target = choice;
        }
    }

    pub(super) fn prepare_combat(&mut self, world: &World) {
        if self.tick % 4 == 1 {
            self.acquire_targets(world);
        }
        if !self
            .attacks
            .iter()
            .any(|strike| strike.due_tick() <= self.tick)
        {
            return;
        }
        let units = &self.units;
        let mut hits = Vec::new();
        // Evaluate every due receipt against the same live state, then apply
        // eligible hits. Both sides can land a lethal blow on the same tick.
        self.attacks.retain(|strike| {
            if strike.due_tick() > self.tick {
                return true;
            }
            let caster = index_of(units, strike.source())
                .map(|i| &units[i])
                .filter(|u| u.death_tick.is_none());
            match strike {
                Attack::Normal {
                    target,
                    reach,
                    damage,
                    ..
                } => {
                    if let (Some(u), Some(i)) = (caster, index_of(units, *target)) {
                        let v = &units[i];
                        if v.death_tick.is_none()
                            && distance_sq(u.xz, v.xz) <= (reach + 1.).powi(2)
                            && world.clear_line(u.xz, v.xz)
                        {
                            hits.push((v.id, *damage, false));
                        }
                    }
                }
                Attack::Siege {
                    point,
                    radius,
                    team,
                    damage,
                    ..
                } => {
                    if caster.is_some_and(|u| world.clear_line(u.xz, *point)) {
                        self.totals.siege_impacts += 1;
                        for v in units {
                            if v.death_tick.is_none()
                                && v.team != *team
                                && distance_sq(v.xz, *point)
                                    <= (radius + v.role.stats().radius).powi(2)
                                && world.clear_line(*point, v.xz)
                            {
                                hits.push((v.id, *damage, true));
                            }
                        }
                    } else {
                        self.totals.siege_cancelled += 1;
                    }
                }
            }
            false
        });
        for (id, damage, siege) in hits {
            if let Some(i) = index_of(&self.units, id) {
                if self.damage(i, damage, false) && siege {
                    self.totals.siege_hits += 1;
                }
            }
        }
    }

    /// Returns true whenever native movement is suppressed (including while
    /// waiting for the cooldown or a free queue slot in striking distance).
    pub(super) fn try_attack(&mut self, index: usize, world: &World) -> bool {
        let source = &self.units[index];
        if source.death_tick.is_some() {
            return true;
        }
        let target = source
            .target
            .and_then(|id| index_of(&self.units, id))
            .map(|i| &self.units[i]);
        let stats = source.role.stats();
        let Some(v) = target.filter(|v| {
            v.death_tick.is_none()
                && v.team != source.team
                && distance_sq(source.xz, v.xz) <= stats.range.powi(2)
                && world.clear_line(source.xz, v.xz)
        }) else {
            return source.attack_until > self.tick.saturating_add(2);
        };
        let [tx, tz] = v.xz;
        let target_id = v.id;
        let yaw = (tx - source.xz[0]).atan2(tz - source.xz[1]);
        let siege = matches!(source.role, Role::CannonCart | Role::RoyalChariot);
        let ready = source.cooldown_until <= self.tick
            && self.attacks.len() < ATTACK_CAP
            && (!siege || self.pending_siege() < SIEGE_ATTACK_CAP);
        let u = &mut self.units[index];
        u.yaw_rad = yaw;
        if !ready {
            return true;
        }
        u.cooldown_until = self.tick.saturating_add(stats.cooldown);
        u.attack_until = self.tick.saturating_add(stats.duration);
        let due_tick = self.tick.saturating_add(stats.windup);
        let [x, z] = u.xz;
        let attack = if siege {
            let (height, forward) = if u.role == Role::CannonCart {
                (0.99, 0.632)
            } else {
                (1.33, 0.70)
            };
            u.state = "siege_windup";
            self.totals.siege_windups += 1;
            Attack::Siege {
                id: self.totals.siege_windups,
                source: u.id,
                team: u.team,
                role: u.role,
                origin: [x + yaw.sin() * forward, height, z + yaw.cos() * forward],
                point: [tx, tz],
                start_tick: self.tick,
                due_tick,
                damage: stats.damage,
                radius: stats.blast,
            }
        } else {
            u.state = if u.role == Role::BowGuard {
                "aim"
            } else {
                "swing"
            };
            Attack::Normal {
                source: u.id,
                team: u.team,
                role: u.role,
                target: target_id,
                origin: [x, 0., z],
                point: [tx, tz],
                start_tick: self.tick,
                due_tick,
                damage: stats.damage,
                reach: stats.range,
            }
        };
        self.attacks.push(attack);
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Isolate receivers exactly as the native headless siege QA does. Keep
    // their real IDs and use true attack code without independent route motion.
    fn fixture(role: Role, distance: f32) -> (Army, World) {
        let mut army = Army::load().unwrap();
        let world = World::load().unwrap();
        army.units.truncate(4);
        for (u, (team, x, z)) in army.units.iter_mut().zip([
            (Team::Sun, 0., -distance),
            (Team::Moon, 0., distance),
            (Team::Sun, 0.5, distance),
            (Team::Moon, 0., 35.),
        ]) {
            u.team = team;
            u.xz = [x, z];
            u.lane = 1;
            u.role = Role::Spearman;
            u.hp = Role::Spearman.stats().hp;
        }
        army.units[0].role = role;
        army.units[0].hp = role.stats().hp;
        army.tick = 1;
        army.prepare_combat(&world);
        assert_eq!(army.units[0].target, Some(army.units[1].id));
        (army, world)
    }

    #[test]
    fn both_vehicle_windups_and_impacts_match_native_receipts() {
        let record: serde_json::Value = serde_json::from_str(include_str!(
            "../../../yuga-native/docs/evidence/siege-qa/army-final.json"
        ))
        .unwrap();
        for (role, name, offset) in [
            (Role::CannonCart, "cannon_cart", 8.),
            (Role::RoyalChariot, "royal_chariot", 2.),
        ] {
            let label = format!("{name}_telegraph_precedes_exactly_one_impact");
            let case = record["checks"]
                .as_array()
                .unwrap()
                .iter()
                .find(|r| r["case"] == label)
                .unwrap();
            let e = &case["evidence"];
            assert_eq!(case["passed"], true);
            let (mut army, world) = fixture(role, offset);
            assert!(army.try_attack(0, &world));
            assert_eq!(army.attacks.len(), 1);
            let Attack::Siege {
                id,
                due_tick,
                origin,
                point,
                damage,
                radius,
                ..
            } = army.attacks[0]
            else {
                panic!("expected siege strike")
            };
            let due = (e["receipts"][0]["observed_time"].as_f64().unwrap() * 20.).round() as u64;
            assert_eq!(id, 1);
            assert_eq!(due_tick, due);
            assert_eq!(point, [0., offset]);
            assert_eq!(damage, e["windup"]["damage"].as_f64().unwrap() as f32);
            assert!((radius - e["windup"]["radius"].as_f64().unwrap() as f32).abs() < 1e-5);
            let values: Vec<f32> = e["windup"]["origin"]
                .as_str()
                .unwrap()
                .trim_matches(['(', ')'])
                .split(',')
                .map(|n| n.trim().parse().unwrap())
                .collect();
            for (got, want) in origin.into_iter().zip(values) {
                assert!((got - want).abs() < 1e-4);
            }
            army.tick = due - 1;
            army.prepare_combat(&world);
            assert_eq!(army.units[1].hp, 75.);
            assert_eq!(army.totals.siege_hits, 0);
            army.tick = due;
            army.prepare_combat(&world);
            army.prepare_combat(&world);
            assert_eq!(army.units[1].hp, e["health"].as_f64().unwrap() as f32);
            assert_eq!(army.units[2].hp, 75.);
            assert_eq!(army.totals.siege_impacts, 1);
            assert_eq!(army.totals.siege_hits, 1);
            assert_eq!(army.pending_siege(), 0);
        }
    }

    #[test]
    fn siege_uses_locked_ground_and_cancels_when_source_dies() {
        let (mut army, world) = fixture(Role::CannonCart, 8.);
        assert!(army.try_attack(0, &world));
        army.units[1].xz = [5.5, 8.]; // Original target escapes.
        army.units[3].xz = [0.9, 8.]; // Another enemy enters the disk.
        army.tick = 17;
        army.prepare_combat(&world);
        assert_eq!(army.units[1].hp, 75.);
        assert_eq!(army.units[3].hp, 51.);
        assert_eq!(army.units[2].hp, 75.);
        let (mut army, world) = fixture(Role::RoyalChariot, 2.);
        assert!(army.try_attack(0, &world));
        assert!(army.damage(0, 1000., false));
        assert_eq!(army.pending_siege(), 0);
        army.tick = 22;
        army.prepare_combat(&world);
        assert_eq!(army.totals.siege_cancelled, 1);
        assert_eq!(army.totals.siege_impacts, 0);
        assert_eq!(army.units[1].hp, 75.);
    }

    #[test]
    fn infantry_eligibility_is_simultaneous_and_tracks_live_target() {
        let (mut army, world) = fixture(Role::Spearman, 1.);
        for u in &mut army.units[..2] {
            u.hp = 1.;
        }
        // Make their 5 Hz decisions with no third candidate in reach.
        army.units.truncate(2);
        army.prepare_combat(&world);
        assert!(army.try_attack(0, &world));
        assert!(army.try_attack(1, &world));
        assert_eq!(army.attacks.len(), 2);
        army.tick = 5;
        army.prepare_combat(&world);
        assert!(army.units.iter().all(|u| u.death_tick == Some(5)));

        let (mut army, world) = fixture(Role::BowGuard, 4.);
        assert!(army.try_attack(0, &world));
        army.units[1].xz = [0., 15.]; // Outside bow range + 1 m impact tolerance.
        army.tick = 20;
        army.prepare_combat(&world);
        assert_eq!(army.units[1].hp, 75.);
    }

    #[test]
    fn target_ties_choose_first_visible_enemy_in_same_lane() {
        let (mut army, world) = fixture(Role::Spearman, 1.);
        army.units[2].team = Team::Moon;
        army.units[2].lane = 0;
        army.units[2].xz = [0., -0.99];
        army.units[3].xz = army.units[1].xz;
        army.prepare_combat(&world);
        assert_eq!(army.units[0].target, Some(army.units[1].id));
        army.units[1].xz = [0., 17.];
        army.units[3].xz = [0., 15.]; // 16 m from seeker, excluded.
        army.prepare_combat(&world);
        assert_eq!(army.units[0].target, None);
        army.units[0].xz = [-9., -28.];
        army.units[1].xz = [-12., -28.];
        army.prepare_combat(&world);
        assert_eq!(army.units[0].target, None);
    }

    #[test]
    fn native_stationary_refire_ticks_for_all_five_roles() {
        // Observed in Godot 4.6.3 over 200 fixed steps with one held receiver.
        // Repeated floating-point subtraction delays vehicle refire by one tick.
        let records: &[(Role, &[u64])] = &[
            (
                Role::Spearman,
                &[1, 23, 45, 67, 89, 111, 133, 155, 177, 199],
            ),
            (Role::BowGuard, &[1, 31, 61, 91, 121, 151, 181]),
            (Role::Commander, &[1, 29, 57, 85, 113, 141, 169, 197]),
            (Role::CannonCart, &[1, 82, 163]),
            (Role::RoyalChariot, &[1, 54, 107, 160]),
        ];
        for &(role, expected) in records {
            let (mut army, world) = fixture(role, 1.);
            let mut commits = Vec::new();
            for t in 1..=200 {
                army.units[1].hp = 1000.;
                army.tick = t;
                army.prepare_combat(&world);
                let previous = army.units[0].cooldown_until;
                assert!(army.try_attack(0, &world));
                if army.units[0].cooldown_until != previous {
                    commits.push(t);
                }
            }
            assert_eq!(commits, expected, "refire ticks for {role:?}");
        }
    }

    #[test]
    fn full_queues_hold_fire_without_spending_cooldown() {
        for (role, cap) in [
            (Role::CannonCart, SIEGE_ATTACK_CAP),
            (Role::BowGuard, ATTACK_CAP),
        ] {
            let (mut army, world) = fixture(role, 1.);
            assert!(army.try_attack(0, &world));
            let shot = army.attacks[0].clone();
            army.attacks.resize(cap, shot);
            army.units[0].cooldown_until = 0;
            army.units[0].attack_until = 0;
            assert!(army.try_attack(0, &world));
            assert_eq!(army.attacks.len(), cap);
            assert_eq!(army.units[0].cooldown_until, 0);
        }
    }
}
