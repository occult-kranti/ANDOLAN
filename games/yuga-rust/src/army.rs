//! Native Confluence lane routes, formations and fixed-step army authority.
mod combat;
use crate::combat::Receiver;
use crate::world::World;
use combat::Attack;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::BTreeMap;

const MAP: &str = include_str!("../../yuga-native/assets/world/confluence-map.json");
const STEP: f64 = 0.05;
type Point = [f32; 2];

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "snake_case")]
enum Role {
    Spearman,
    BowGuard,
    Commander,
    CannonCart,
    RoyalChariot,
}

impl Role {
    // Speeds (m/s) and body radii (m) from lane_minion.gd::STATS.
    fn motion(self) -> (f64, f32) {
        match self {
            Self::Spearman => (3.8, 0.39),
            Self::BowGuard => (3.6, 0.39),
            Self::Commander => (3.45, 0.39),
            Self::CannonCart => (2.8, 0.82),
            Self::RoyalChariot => (3.1, 0.88),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Team {
    Sun,
    Moon,
}

impl Team {
    fn other(self) -> Self {
        if self == Self::Sun {
            Self::Moon
        } else {
            Self::Sun
        }
    }
    fn name(self) -> &'static str {
        match self {
            Self::Sun => "sun",
            Self::Moon => "moon",
        }
    }
}

#[derive(Clone, Copy)]
struct Stats {
    hp: f32,
    damage: f32,
    range: f32,
    cooldown: u64,
    radius: f32,
    speed: f64,
    core_damage: f32,
    windup: u64,
    duration: u64,
    blast: f32,
    gold: u32,
    height: f32,
}
impl Role {
    fn stats(self) -> Stats {
        use Role::*;
        // Native timings in ticks, rounding windup releases up to the next 50ms step.
        let (hp, damage, range, cooldown, core_damage, windup, duration, blast, gold, height) =
            match self {
                Spearman => (75., 10., 2.15, 22, 7., 4, 11, 0., 18, 1.9),
                BowGuard => (55., 8., 11., 30, 7., 6, 11, 0., 24, 1.9),
                Commander => (150., 13., 2.55, 28, 12., 4, 11, 0., 45, 2.13),
                CannonCart => (220., 24., 18., 81, 20., 16, 24, 3., 70, 1.8),
                RoyalChariot => (340., 22., 5.5, 53, 25., 11, 20, 2.4, 110, 2.4),
            };
        let (speed, radius) = self.motion();
        Stats {
            hp,
            damage,
            range,
            cooldown,
            radius,
            speed,
            core_damage,
            windup,
            duration,
            blast,
            gold,
            height,
        }
    }
}

#[derive(Deserialize)]
struct LaneSpec {
    id: usize,
    name: String,
    points: Vec<[f32; 3]>,
}
#[derive(Deserialize)]
struct Bounds {
    actor_xz: [f32; 4],
}
#[derive(Deserialize)]
struct Map {
    bounds: Bounds,
    lanes: Vec<LaneSpec>,
}

struct Segment {
    start: Point,
    unit: Point,
    delta: Point,
    length: f64,
}
impl Segment {
    fn position(&self, along: f64, offset: f32) -> Point {
        // Godot Vector3::lerp narrows the path fraction to real_t before multiplying
        // the segment delta. Multiplying a normalized direction by distance can
        // change the floating-point tie at a body-separation boundary.
        let t = (along / self.length).clamp(0., 1.) as f32;
        let [dx, dz] = self.unit;
        [
            self.start[0] + self.delta[0] * t + dz * offset,
            self.start[1] + self.delta[1] * t - dx * offset,
        ]
    }
}

struct Lane {
    name: String,
    length: f64,
    segments: Vec<Segment>,
}

impl Lane {
    fn new(spec: LaneSpec) -> Result<Self, String> {
        if !(2..=32).contains(&spec.points.len())
            || spec
                .points
                .iter()
                .any(|p| !p.iter().all(|v| v.is_finite()) || p[1].abs() > 0.001)
        {
            return Err(format!("Invalid floor waypoints in lane {}", spec.id));
        }
        let mut segments = Vec::new();
        let mut total = 0.;
        for points in spec.points.windows(2) {
            let [x, _, z] = points[0];
            let dx = points[1][0] - x;
            let dz = points[1][2] - z;
            let length = (dx * dx + dz * dz).sqrt();
            if !(0.1..=1000.).contains(&length) {
                return Err(format!("Invalid segment in lane {}", spec.id));
            }
            segments.push(Segment {
                start: [x, z],
                unit: [dx / length, dz / length],
                delta: [dx, dz],
                length: length.into(),
            });
            total += f64::from(length);
        }
        if !(10.0..=2000.).contains(&total) {
            return Err(format!("Invalid length in lane {}", spec.id));
        }
        Ok(Self {
            name: spec.name,
            length: total,
            segments,
        })
    }

    fn sample(&self, team: Team, progress: f64, lateral: f32) -> (Point, f32) {
        let (distance, offset) = match team {
            Team::Sun => (progress, lateral),
            Team::Moon => (self.length - progress, -lateral),
        };
        let mut remaining = distance.clamp(0., self.length);
        for (i, seg) in self.segments.iter().enumerate() {
            if remaining <= seg.length || i + 1 == self.segments.len() {
                let sign = if team == Team::Moon { -1. } else { 1. };
                let yaw = (sign * seg.unit[0]).atan2(sign * seg.unit[1]);
                return (seg.position(remaining.min(seg.length), offset), yaw);
            }
            remaining -= seg.length;
        }
        unreachable!("A validated lane has a segment")
    }

    // Offset ranks change tangent at a bend. Check both sections as well as
    // the small connecting motion the native sampler makes across the join.
    fn corridor_clear(&self, world: &World, bounds: [f32; 4], offset: f32, radius: f32) -> bool {
        let [xmin, xmax, zmin, zmax] = bounds;
        let bounded = |[x, z]: Point| {
            x >= xmin + radius && x <= xmax - radius && z >= zmin + radius && z <= zmax - radius
        };
        let mut previous = None;
        for s in &self.segments {
            let from = s.position(0., offset);
            let to = s.position(s.length, offset);
            if !bounded(from)
                || !bounded(to)
                || !world.clear_line_with_margin(from, to, radius)
                || previous.is_some_and(|p| !world.clear_line_with_margin(p, from, radius))
            {
                return false;
            }
            previous = Some(to);
        }
        true
    }
}

struct Arena {
    lanes: Vec<Lane>,
}
impl Arena {
    fn load() -> Result<Self, String> {
        let world = World::load()?;
        let mut map: Map = serde_json::from_str(MAP).map_err(|e| e.to_string())?;
        map.lanes.sort_by_key(|l| l.id);
        if map.lanes.len() != 3 || map.lanes.iter().enumerate().any(|(id, l)| l.id != id) {
            return Err("Expected three distinct lane IDs 0..2".into());
        }
        let mut lanes = Vec::new();
        for spec in map.lanes {
            let lane = Lane::new(spec)?;
            // Both factions use the same +1.2/-1.2 infantry ranks, and all
            // vehicles follow the centre. Validate each distinct clearance.
            for (offset, radius) in [(-1.2, 0.39), (1.2, 0.39), (0., 0.88)] {
                if !lane.corridor_clear(&world, map.bounds.actor_xz, offset, radius) {
                    return Err(format!("Blocked formation corridor in {}", lane.name));
                }
            }
            lanes.push(lane);
        }
        Ok(Self { lanes })
    }
}

#[derive(Debug, Serialize)]
struct Marcher {
    team: Team,
    lane: usize,
    role: Role,
    lateral: f32,
    progress: f64,
    xz: Point,
    yaw_rad: f32,
    arrival_tick: Option<u32>,
}

impl Marcher {
    fn spawn(
        arena: &Arena,
        team: Team,
        lane: usize,
        role: Role,
        progress: f64,
        lateral: f32,
    ) -> Self {
        let (xz, yaw_rad) = arena.lanes[lane].sample(team, progress, lateral);
        Self {
            team,
            lane,
            role,
            lateral,
            progress,
            xz,
            yaw_rad,
            arrival_tick: None,
        }
    }

    fn advance(&mut self, lane: &Lane, ticks: u32) {
        let stride = self.role.motion().0 * STEP;
        for t in 1..=ticks {
            self.progress = (self.progress + stride).min(lane.length);
            if self.progress >= lane.length - 0.05 {
                self.arrival_tick = Some(t);
                break;
            }
        }
        (self.xz, self.yaw_rad) = lane.sample(self.team, self.progress, self.lateral);
    }
}

// One fresh event, in native insertion order. Each wave starts on a clear
// floor, the same fixture the native fifteen-wave cadence record uses.
fn formation(arena: &Arena, wave: u32) -> Result<Vec<Marcher>, String> {
    if wave == 0 {
        return Err("Wave numbers begin at 1".into());
    }
    use Role::*;
    let ranks = [
        (Spearman, 8., -1.2),
        (Spearman, 8., 1.2),
        (BowGuard, 5.4, -1.2),
        (BowGuard, 5.4, 1.2),
        (Commander, 2.8, 0.),
    ];
    let lanes: Vec<_> = (0..3).map(|i| ((wave - 1) % 3 + i) as usize % 3).collect();
    let teams = [Team::Sun, Team::Moon];
    let mut units = Vec::new();
    for &lane in &lanes {
        for team in teams {
            for (role, start, lateral) in ranks {
                units.push(Marcher::spawn(arena, team, lane, role, start, lateral));
            }
        }
    }
    if wave % 3 == 0 {
        for &lane in &lanes {
            for team in teams {
                units.push(Marcher::spawn(arena, team, lane, CannonCart, 5., 0.))
            }
        }
    }
    if wave % 5 == 0 {
        for team in teams {
            units.push(Marcher::spawn(arena, team, 1, RoyalChariot, 11.8, 0.))
        }
    }
    for (i, unit) in units.iter().enumerate() {
        if unit.progress > arena.lanes[unit.lane].length {
            return Err("Formation exceeds lane length".into());
        }
        for prior in &units[..i] {
            let dx = prior.xz[0] - unit.xz[0];
            let dz = prior.xz[1] - unit.xz[1];
            if dx * dx + dz * dz < (prior.role.motion().1 + unit.role.motion().1).powi(2) {
                return Err(format!("Spawn overlap in wave {wave} at {:?}", unit.xz));
            }
        }
    }
    Ok(units)
}

fn census(units: &[Marcher]) -> BTreeMap<Role, u32> {
    let mut roles = BTreeMap::from([
        (Role::Spearman, 0),
        (Role::BowGuard, 0),
        (Role::Commander, 0),
        (Role::CannonCart, 0),
        (Role::RoyalChariot, 0),
    ]);
    for u in units {
        *roles.get_mut(&u.role).unwrap() += 1;
    }
    roles
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::Value;

    #[test]
    fn matches_every_native_cadence_record_and_both_factions() {
        let arena = Arena::load().unwrap();
        let report: Value = serde_json::from_str(include_str!(
            "../../yuga-native/docs/evidence/siege-qa/army-final.json"
        ))
        .unwrap();
        let rows = report["checks"]
            .as_array()
            .unwrap()
            .iter()
            .find(|row| row["case"] == "fifteen_wave_events_keep_mirrored_siege_cadence")
            .unwrap();
        let waves = rows["evidence"]["waves"].as_array().unwrap();
        assert!(rows["passed"].as_bool().unwrap());
        assert_eq!(waves.len(), 14);
        assert!(formation(&arena, 0).is_err());
        assert_eq!(formation(&arena, 1).unwrap().len(), 30);
        for row in waves {
            let wave = row["wave"].as_u64().unwrap() as u32;
            let units = formation(&arena, wave).unwrap();
            assert_eq!(json!(census(&units)), row["roles"], "wave {wave}");
            for lane in 0..3 {
                let faction = |team| {
                    let mut counts = BTreeMap::new();
                    for unit in &units {
                        if unit.lane == lane && unit.team == team {
                            *counts.entry(unit.role).or_insert(0) += 1;
                        }
                    }
                    counts
                };
                assert_eq!(faction(Team::Sun), faction(Team::Moon));
            }
        }
    }

    #[test]
    fn bends_preserve_native_offset_and_reverse_heading() {
        let a = Arena::load().unwrap();
        let lane = &a.lanes[0];
        let first = lane.segments[0].length;
        let (entry, first_yaw) = lane.sample(Team::Sun, first, 1.2);
        let (after, next_yaw) = lane.sample(Team::Sun, first + 0.001, 1.2);
        assert!((entry[0] + 39.3826).abs() < 0.001 && (entry[1] + 86.9710).abs() < 0.001);
        assert!((after[0] + 38.8).abs() < 0.001 && (after[1] + 87.999).abs() < 0.001);
        assert!(first_yaw < -1.0 && next_yaw.abs() < 0.001);
        let (back, reverse_yaw) = lane.sample(Team::Moon, lane.length - first - 0.001, -1.2);
        assert_eq!(after, back);
        assert!((reverse_yaw.abs() - std::f32::consts::PI).abs() < 0.0001);
    }

    #[test]
    fn isolated_arrivals_stop_on_first_native_arrival_tick() {
        let arena = Arena::load().unwrap();
        for mut unit in formation(&arena, 15).unwrap() {
            let lane = &arena.lanes[unit.lane];
            let stride = unit.role.motion().0 * STEP;
            let ticks = ((lane.length - unit.progress - 0.05) / stride).ceil() as u32;
            unit.advance(lane, 20_000);
            assert_eq!(unit.arrival_tick, Some(ticks));
            assert!((lane.length - 0.05..=lane.length).contains(&unit.progress));
        }
    }

    // Independent oracle using the installed engine and the actual project
    // scripts. Deliberately separate from the dependency-free regression tests.
    #[test]
    #[ignore = "requires Godot 4.6.3 and the native project's imported resources"]
    fn compares_current_godot_spawn_order_and_uncontested_marches() {
        use std::{fs, path::Path, process::Command};
        let temp = std::env::temp_dir().join(format!("yuga-lanes-{}.gd", std::process::id()));
        let native = Path::new(env!("CARGO_MANIFEST_DIR")).join("../yuga-native");
        fs::write(&temp, r#"extends SceneTree
const Army = preload("res://scripts/lane_army.gd")
func _initialize() -> void:
    run.call_deferred()
func run() -> void:
    var army = Army.new()
    army.visual_enabled = false
    root.add_child(army)
    army.set_physics_process(false)
    var map = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
    assert(army.configure(map, null))
    var rows = []
    for wave in [1,3,5,15]:
        army._reset_state(false)
        army.wave_events = wave-1
        army._spawn_wave()
        for u in army.units:
            rows.append([wave, u.lane_id, u.team, u.role, u.progress, u.lateral, u.position.x, u.position.z, u.heading, u.STATS[u.role].speed, u.radius])
    var marches = []
    for lane in range(3):
        for team in ["sun", "moon"]:
            army._reset_state(false)
            army.siege_drill = true
            assert(army._spawn_specifications([{"team":team,"role":"spearman","lane":lane,"progress":8.0,"lateral":1.2}]))
            for tick in range(1,2001):
                army.step_simulation(0.05)
                if army.core_arrivals[lane] > 0:
                    marches.append([lane,team,tick,true,0,0])
                    break
                if tick in [1,205,1000,1200]:
                    var pos:Vector3 = army.units[0].position
                    marches.append([lane,team,tick,false,pos.x,pos.z])
    print("LANE_ORACLE ",JSON.stringify({"rows":rows,"marches":marches}))
    quit()
"#).unwrap();
        let output = Command::new(std::env::var("GODOT_BIN").unwrap_or_else(|_| "godot".into()))
            .args(["--headless", "--quit-after", "60", "--path"])
            .arg(native)
            .arg("--script")
            .arg(&temp)
            .output();
        fs::remove_file(temp).unwrap();
        let out = output.expect("launch headless Godot");
        assert!(
            out.status.success(),
            "{}",
            String::from_utf8_lossy(&out.stderr)
        );
        let stdout = String::from_utf8(out.stdout).unwrap();
        let witness: Value = serde_json::from_str(
            stdout
                .lines()
                .find_map(|l| l.strip_prefix("LANE_ORACLE "))
                .expect("Godot oracle output"),
        )
        .unwrap();
        let arena = Arena::load().unwrap();
        let mut rows = witness["rows"].as_array().unwrap().iter();
        for wave in [1, 3, 5, 15] {
            for u in formation(&arena, wave).unwrap() {
                let r = rows.next().unwrap();
                assert_eq!(
                    json!([wave, u.lane, u.team, u.role]),
                    Value::Array(r.as_array().unwrap()[..4].to_vec())
                );
                let yaw = r[8].as_f64().unwrap() - f64::from(u.yaw_rad);
                assert!(yaw.sin().abs() < 0.0001 && yaw.cos() > 0.9999);
                for (idx, ours) in [
                    (4, u.progress),
                    (5, u.lateral.into()),
                    (6, u.xz[0].into()),
                    (7, u.xz[1].into()),
                    (9, u.role.motion().0),
                    (10, u.role.motion().1.into()),
                ] {
                    assert!(
                        (r[idx].as_f64().unwrap() - ours).abs() < 0.001,
                        "wave {wave}, field {idx}, {r} vs {u:?}"
                    );
                }
            }
        }
        assert!(rows.next().is_none());
        let marches = witness["marches"].as_array().unwrap();
        let mut arrivals = 0;
        for r in marches {
            let lane = r[0].as_u64().unwrap() as usize;
            let team = match r[1].as_str() {
                Some("sun") => Team::Sun,
                Some("moon") => Team::Moon,
                _ => panic!("Unexpected oracle team {r}"),
            };
            let ticks = r[2].as_u64().unwrap() as u32;
            let mut u = Marcher::spawn(&arena, team, lane, Role::Spearman, 8., 1.2);
            u.advance(&arena.lanes[lane], ticks);
            if r[3] == true {
                assert_eq!(u.arrival_tick, Some(ticks));
                arrivals += 1;
            } else {
                assert_eq!(u.arrival_tick, None);
                for i in 0..2 {
                    assert!(
                        (r[4 + i].as_f64().unwrap() - f64::from(u.xz[i])).abs() < 0.001,
                        "march {r} vs {u:?}"
                    );
                }
            }
        }
        assert_eq!(arrivals, 6);
    }
}

pub fn isolated_wave(wave: u32, ticks: u32) -> Result<serde_json::Value, String> {
    let arena = Arena::load()?;
    let mut units = formation(&arena, wave)?;
    let roles = census(&units);
    for unit in &mut units {
        unit.advance(&arena.lanes[unit.lane], ticks);
    }
    let lanes: Vec<_> = arena
        .lanes
        .iter()
        .enumerate()
        .map(|(id, l)| json!({"id":id,"name":l.name,"length_m":l.length}))
        .collect();
    Ok(
        json!({"mode":"isolated_wave_march","wave":wave,"event_seconds":(u64::from(wave)-1)*30,
        "ticks_since_spawn":ticks,"tick_seconds":STEP,"lanes":lanes,"roles":roles,"units":units}),
    )
}

const ALIVE_CAP: usize = 72;
const CORPSE_CAP: usize = 24;
const TOTAL_CAP: usize = 96;
const WAVE_TICKS: u64 = 600;

struct Unit {
    id: u32,
    team: Team,
    role: Role,
    lane: usize,
    xz: Point,
    yaw_rad: f32,
    lateral: f32,
    progress: f64,
    hp: f32,
    shield: f32,
    shield_until: u32,
    death_tick: Option<u64>,
    target: Option<u32>,
    cooldown_until: u64,
    attack_until: u64,
    state: &'static str,
}
impl Unit {
    fn new(id: u32, m: &Marcher) -> Self {
        Self {
            id,
            team: m.team,
            role: m.role,
            lane: m.lane,
            xz: m.xz,
            yaw_rad: m.yaw_rad,
            lateral: m.lateral,
            progress: m.progress,
            hp: m.role.stats().hp,
            shield: 0.,
            shield_until: 0,
            death_tick: None,
            target: None,
            cooldown_until: 0,
            attack_until: 0,
            state: "walk",
        }
    }
    fn alive(&self) -> bool {
        self.death_tick.is_none()
    }
    fn overlaps(&self, at: Point, radius: f32) -> bool {
        let dx = self.xz[0] - at[0];
        let dz = self.xz[1] - at[1];
        let sum = self.role.stats().radius + radius;
        self.alive() && dx.abs() < sum && dz.abs() < sum && dx * dx + dz * dz < sum * sum
    }
}

#[derive(Clone, Copy, Debug)]
pub struct ArmyTarget {
    pub id: u32,
    pub team: Team,
    pub xz: Point,
    pub hp: f32,
    pub max_hp: f32,
    pub radius: f32,
    pub height: f32,
}

#[derive(Default)]
struct Counters {
    siege_windups: u32,
    siege_impacts: u32,
    siege_cancelled: u32,
    siege_hits: u32,
    siege_spawned_pairs: u32,
    siege_rejected_pairs: u32,
    rejected_groups: u32,
    arrivals: [u32; 3],
    losses: [u32; 3],
    separation_waits: u64,
    gold: [u32; 2],
    kills: [u32; 2],
}

pub struct Army {
    arena: Arena,
    units: Vec<Unit>,
    attacks: Vec<Attack>,
    tick: u64,
    wave: u32,
    wave_events: u32,
    next_id: u32,
    totals: Counters,
    cores: [f32; 2],
    winner: Option<&'static str>,
}

impl Army {
    pub fn load() -> Result<Self, String> {
        let arena = Arena::load()?;
        // Validate all combinations (3 lanes × 5 events) before a match starts.
        // Covers infantry/carts/chariots in all cyclic ordering permutations.
        for wave in 1..=15 {
            formation(&arena, wave)?;
        }
        let mut a = Self {
            arena,
            units: Vec::with_capacity(TOTAL_CAP),
            attacks: Vec::with_capacity(ALIVE_CAP),
            tick: 0,
            wave: 0,
            wave_events: 0,
            next_id: 1,
            totals: Counters::default(),
            cores: [100., 100.],
            winner: None,
        };
        a.spawn_wave();
        Ok(a)
    }
    pub fn reset(&mut self) {
        self.units.clear();
        self.attacks.clear();
        self.tick = 0;
        self.wave = 0;
        self.wave_events = 0;
        self.next_id = 1;
        self.totals = Counters::default();
        self.cores = [100., 100.];
        self.winner = None;
        self.spawn_wave();
    }
    pub fn finished(&self) -> bool {
        self.winner.is_some()
    }
    pub fn winner(&self) -> Option<&'static str> {
        self.winner
    }
    pub fn tick_index(&self) -> u32 {
        self.tick.min(u64::from(u32::MAX)) as u32
    }

    fn admit(&mut self, group: &[Marcher]) -> bool {
        if group.len() + self.units.len() > TOTAL_CAP
            || group.len() + self.units.iter().filter(|u| u.alive()).count() > ALIVE_CAP
            || self.next_id.checked_add(group.len() as u32).is_none()
        {
            return false;
        }
        // Within-wave pairwise separation was validated when this map loaded.
        if group.iter().any(|g| {
            self.units
                .iter()
                .any(|u| u.overlaps(g.xz, g.role.stats().radius))
        }) {
            return false;
        }
        for m in group {
            self.units.push(Unit::new(self.next_id, m));
            self.next_id += 1;
        }
        true
    }
    fn spawn_wave(&mut self) {
        self.wave_events = self.wave_events.saturating_add(1);
        let fresh = formation(&self.arena, self.wave_events)
            .expect("all canonical formation phases validated");
        let mut spawned = false;
        for group in fresh[..30].chunks_exact(10) {
            if self.admit(group) {
                spawned = true;
            } else {
                self.totals.rejected_groups += 1;
            }
        }
        for group in fresh[30..].chunks_exact(2) {
            if self.admit(group) {
                self.totals.siege_spawned_pairs += 1;
                spawned = true;
            } else {
                self.totals.siege_rejected_pairs += 1;
            }
        }
        if spawned {
            self.wave += 1;
        }
    }
    fn index(&self, id: u32) -> Option<usize> {
        self.units.binary_search_by_key(&id, |u| u.id).ok()
    }

    fn record_death(&mut self, i: usize, credit: Option<Team>) {
        let u = &mut self.units[i];
        let id = u.id;
        u.hp = 0.;
        u.death_tick = Some(self.tick);
        u.state = "fall";
        u.target = None;
        u.shield = 0.;
        u.shield_until = 0;
        self.totals.losses[u.lane] += 1;
        if let Some(team) = credit.filter(|team| *team != u.team) {
            let side = usize::from(team == Team::Moon);
            self.totals.gold[side] += u.role.stats().gold;
            self.totals.kills[side] += 1;
        }
        self.cancel_source_attacks(id);
        if self.units.iter().filter(|u| !u.alive()).count() > CORPSE_CAP {
            if let Some(oldest) = self.units.iter().position(|u| !u.alive() && u.id != id) {
                self.units.remove(oldest);
            }
        }
    }
    fn damage(&mut self, i: usize, amount: f32, by_hero: bool) -> bool {
        if self.finished() || !amount.is_finite() || amount <= 0. || amount > 1000. {
            return false;
        }
        let u = &mut self.units[i];
        if !u.alive() || (by_hero && u.team != Team::Moon) {
            return false;
        }
        let shield = u.shield.min(amount);
        u.shield -= shield;
        u.hp = (u.hp - (amount - shield)).max(0.);
        if u.hp <= 0. {
            self.record_death(i, by_hero.then_some(Team::Sun));
        }
        true
    }
    pub fn targets(&self) -> impl Iterator<Item = ArmyTarget> + '_ {
        self.units.iter().filter(|u| u.alive()).map(|u| {
            let stats = u.role.stats();
            ArmyTarget {
                id: u.id,
                team: u.team,
                xz: u.xz,
                hp: u.hp,
                max_hp: stats.hp,
                radius: stats.radius,
                height: stats.height,
            }
        })
    }
    pub fn receivers(&self) -> Vec<Receiver> {
        self.units
            .iter()
            .filter(|u| u.alive())
            .map(|u| {
                let stats = u.role.stats();
                let mut r = Receiver::new(u.id, u.team.name(), u.xz, u.hp.into(), stats.hp.into());
                r.shield = u.shield.into();
                r.shield_until = u.shield_until;
                r.radius = stats.radius;
                r.height = stats.height;
                r
            })
            .collect()
    }
    /// Apply a same-tick result from the hero authority. Units retain team,
    /// maximum health and position; repeated/dead/absent IDs cannot grant gold.
    pub fn apply_receivers(&mut self, after: &[Receiver]) {
        self.apply_receivers_for(after, Team::Sun);
    }
    pub fn apply_receivers_for(&mut self, after: &[Receiver], caster_team: Team) {
        if self.finished() {
            return;
        }
        for r in after {
            let Some(i) = self.index(r.id) else { continue };
            let u = &mut self.units[i];
            let stats = u.role.stats();
            if !u.alive()
                || r.team != u.team.name()
                || !r.hp.is_finite()
                || !r.shield.is_finite()
                || r.hp < 0.
                || r.hp > f64::from(stats.hp)
                || !(0.0..=100.).contains(&r.shield)
            {
                continue;
            }
            if u.team == caster_team {
                u.hp = u.hp.max(r.hp as f32);
                u.shield = r.shield as f32;
                u.shield_until = r.shield_until;
            } else {
                // Receiver.damage already consumed any shield. Reapplying the
                // strike here would double absorption or grant duplicate kills.
                u.shield = u.shield.min(r.shield as f32);
                if r.hp < f64::from(u.hp) {
                    u.hp = r.hp as f32;
                    if u.hp == 0. {
                        self.record_death(i, Some(caster_team));
                    }
                }
            }
        }
    }
    pub fn hero_hit(&mut self, id: u32, amount: f32) -> bool {
        self.index(id).is_some_and(|i| self.damage(i, amount, true))
    }
    pub fn hero_heal(&mut self, id: u32, amount: f32) -> bool {
        if self.finished() || !amount.is_finite() || !(0.000001..=1000.).contains(&amount) {
            return false;
        }
        let Some(i) = self.index(id) else {
            return false;
        };
        let u = &mut self.units[i];
        if u.team != Team::Sun || !u.alive() {
            return false;
        }
        let previous = u.hp;
        u.hp = (u.hp + amount).min(u.role.stats().hp);
        u.hp > previous
    }
    pub fn hero_shield(&mut self, id: u32, amount: f32, duration_ticks: u32) -> bool {
        if self.finished()
            || !amount.is_finite()
            || !(0.000001..=100.).contains(&amount)
            || !(1..=240).contains(&duration_ticks)
        {
            return false;
        }
        let Some(i) = self.index(id) else {
            return false;
        };
        let u = &mut self.units[i];
        if u.team != Team::Sun || !u.alive() {
            return false;
        }
        u.shield = u.shield.max(amount);
        u.shield_until = u
            .shield_until
            .max((self.tick.min(u64::from(u32::MAX)) as u32).saturating_add(duration_ticks));
        true
    }
    /// A clear central-lane hero entry point behind the foremost Sun guard.
    pub fn frontline_spawn(&self, world: &World) -> Point {
        self.frontline_spawn_for(world, Team::Sun)
    }
    pub fn frontline_spawn_for(&self, world: &World, team: Team) -> Point {
        let front = self
            .units
            .iter()
            .filter(|u| u.alive() && u.lane == 1 && u.team == team)
            .map(|u| u.progress)
            .fold(0., f64::max);
        let lane = &self.arena.lanes[1];
        for back in [4., 6., 8., 10.] {
            for side in [0., -2.8, 2.8] {
                let (p, _) = lane.sample(team, (front - back).max(0.), side);
                if world.ground_target_allowed(p) && !self.units.iter().any(|u| u.overlaps(p, 0.65))
                {
                    return p;
                }
            }
        }
        lane.sample(team, 0., 0.).0
    }
    pub fn step(&mut self, world: &World) {
        if self.finished() {
            return;
        }
        self.tick += 1;
        for u in &mut self.units {
            if self.tick >= u64::from(u.shield_until) {
                u.shield = 0.;
                u.shield_until = 0;
            }
        }
        self.units
            .retain(|u| u.death_tick.is_none_or(|death| self.tick - death < 24));
        self.prepare_combat(world);
        let mut core_damage = [0., 0.];
        for i in 0..self.units.len() {
            if !self.units[i].alive() || self.try_attack(i, world) {
                continue;
            }
            let u = &self.units[i];
            let s = u.role.stats();
            let lane = &self.arena.lanes[u.lane];
            let next = (u.progress + s.speed * STEP).min(lane.length);
            let (at, yaw) = lane.sample(u.team, next, u.lateral);
            // The static lane strips and their offset joins were cleared on load;
            // units still test live neighbors in stable insertion order each step.
            if self
                .units
                .iter()
                .any(|other| other.id != u.id && other.overlaps(at, s.radius))
            {
                self.totals.separation_waits += 1;
                continue;
            }
            let u = &mut self.units[i];
            u.progress = next;
            u.xz = at;
            u.yaw_rad = yaw;
            u.state = "walk";
            if next >= lane.length - 0.05 {
                let opposed = usize::from(u.team.other() == Team::Moon);
                core_damage[opposed] += s.core_damage;
                self.totals.arrivals[u.lane] += 1;
                u.state = "arrived";
                u.death_tick = Some(self.tick);
            }
        }
        self.units.retain(|u| u.state != "arrived");
        for (hp, damage) in self.cores.iter_mut().zip(core_damage) {
            *hp = (*hp - damage).max(0.);
        }
        self.winner = match (self.cores[0] <= 0., self.cores[1] <= 0.) {
            (true, true) => Some("draw"),
            (true, false) => Some("moon"),
            (false, true) => Some("sun"),
            _ => None,
        };
        if self.finished() {
            self.attacks.clear();
        } else if self.tick % WAVE_TICKS == 0 {
            self.spawn_wave();
        }
    }

    pub fn snapshot(&self) -> serde_json::Value {
        let units:Vec<_>=self.units.iter().map(|u|{
            let s=u.role.stats();
            json!({"id":u.id,"team":u.team,"role":u.role,"lane":u.lane,"xz":u.xz,"yaw_rad":u.yaw_rad,
                "hp":u.hp,"max_hp":s.hp,"radius":s.radius,"height":s.height,"shield":u.shield,"shield_until":u.shield_until,
                "state":u.state,"alive":u.alive(),"death_tick":u.death_tick,"attack_until":u.attack_until,"attack_duration_ticks":s.duration,"windup_ticks":s.windup,"target":u.target})
        }).collect();
        json!({"tick":self.tick,"wave":self.wave,"wave_events":self.wave_events,"winner":self.winner,"units":units,"attacks":self.attacks,
            "cores":{"sun":self.cores[0],"moon":self.cores[1]},"kills":self.totals.kills[0],"gold":self.totals.gold[0],"moon_kills":self.totals.kills[1],"moon_gold":self.totals.gold[1],"core_arrivals":self.totals.arrivals,
            "losses_by_lane":self.totals.losses,"separation_waits":self.totals.separation_waits,"rejected_formations":self.totals.rejected_groups,
            "siege":{"windups":self.totals.siege_windups,"impacts":self.totals.siege_impacts,"cancelled":self.totals.siege_cancelled,"hits":self.totals.siege_hits,
                    "pending":self.pending_siege(),"spawned_pairs":self.totals.siege_spawned_pairs,"rejected_pairs":self.totals.siege_rejected_pairs}})
    }
}

#[cfg(test)]
mod match_tests {
    use super::*;

    #[test]
    fn persistent_spawn_is_atomic_and_rotates_first_refusal() {
        let mut army = Army::load().unwrap();
        assert_eq!(army.units.len(), 30);
        // Same pressure fixture as tests/lane_army_cases.gd.
        for _ in 0..2 {
            for u in &mut army.units {
                u.progress += 20.;
                (u.xz, u.yaw_rad) = army.arena.lanes[u.lane].sample(u.team, u.progress, u.lateral);
            }
            army.spawn_wave();
        }
        assert_eq!(army.units.len(), 72);
        assert_eq!((army.wave_events, army.wave), (3, 3));
        let prev = army.next_id;
        army.spawn_wave();
        assert_eq!(army.next_id, prev);
        let mut counts = BTreeMap::new();
        for u in &army.units {
            let i = usize::from(u.team == Team::Moon);
            counts.entry((u.lane, u.role)).or_insert([0, 0])[i] += 1;
        }
        assert!(counts.values().all(|p| p[0] == p[1]));
        assert!(army.totals.rejected_groups > 0 && army.totals.siege_rejected_pairs > 0);
        assert_eq!(army.wave, 3);
    }

    #[test]
    fn two_faction_hero_receivers_heal_shield_absorb_and_reward_once() {
        let mut a = Army::load().unwrap();
        let sun = a.targets().find(|u| u.team == Team::Sun).unwrap().id;
        let moon = a.targets().find(|u| u.team == Team::Moon).unwrap().id;
        let mut receivers = a.receivers();
        let ally = receivers.iter_mut().find(|u| u.id == sun).unwrap();
        ally.shield = 25.;
        ally.shield_until = 5;
        a.apply_receivers_for(&receivers, Team::Sun);
        let i = a.index(sun).unwrap();
        a.damage(i, 40., false);
        assert_eq!(a.units[i].hp, 60.);
        assert_eq!(a.units[i].shield, 0.);
        let mut receivers = a.receivers();
        for u in &mut receivers {
            if u.id == sun {
                u.hp += 8.;
            }
            if u.id == moon {
                u.hp = 0.;
            }
        }
        a.apply_receivers(&receivers);
        a.apply_receivers(&receivers);
        assert_eq!(a.units[a.index(sun).unwrap()].hp, 68.);
        assert_eq!(a.totals.gold, [18, 0]);
        assert_eq!(a.totals.kills, [1, 0]);
        let mut receivers = a.receivers();
        receivers.iter_mut().find(|u| u.id == sun).unwrap().hp = 0.;
        a.apply_receivers_for(&receivers, Team::Moon);
        a.apply_receivers_for(&receivers, Team::Moon);
        assert_eq!(a.totals.gold, [18, 18]);
        assert_eq!(a.totals.kills, [1, 1]);
        assert!(!a.hero_hit(moon, 8.) && !a.hero_hit(sun, 100.));
        let mut invalid = a.receivers();
        invalid[0].hp = f64::NAN;
        invalid[0].shield = f64::INFINITY;
        a.apply_receivers(&invalid);
        assert!(a
            .units
            .iter()
            .all(|u| u.hp.is_finite() && u.shield.is_finite()));
        let w = World::load().unwrap();
        let shielded = a
            .units
            .iter()
            .find(|u| u.alive() && u.team == Team::Sun)
            .unwrap()
            .id;
        assert!(a.hero_shield(shielded, 20., 2));
        a.step(&w);
        assert_eq!(a.units[a.index(shielded).unwrap()].shield, 20.);
        a.step(&w);
        assert_eq!(a.units[a.index(shielded).unwrap()].shield, 0.);
        a.reset();
        assert_eq!((a.units.len(), a.tick, a.wave), (30, 0, 1));
        assert_eq!(a.totals.gold, [0; 2]);
        assert_eq!(a.cores, [100.; 2]);
    }

    #[test]
    fn simultaneous_arrivals_draw_and_game_freezes() {
        let mut a = Army::load().unwrap();
        let w = World::load().unwrap();
        a.units.retain(|u| u.id == 1 || u.id == 6);
        assert_eq!(a.units.len(), 2);
        for u in &mut a.units {
            let lane = &a.arena.lanes[u.lane];
            u.progress = lane.length - 0.15;
            u.lateral = 0.;
            (u.xz, u.yaw_rad) = lane.sample(u.team, u.progress, 0.);
        }
        a.cores = [7., 7.];
        a.step(&w);
        assert_eq!(a.winner(), Some("draw"));
        assert_eq!(a.cores, [0., 0.]);
        assert!(a.attacks.is_empty());
        assert_eq!(a.totals.arrivals, [2, 0, 0]);
        let end = a.snapshot();
        a.step(&w);
        assert_eq!(end, a.snapshot());
    }

    #[test]
    fn a_hero_can_turn_a_full_match_through_ordinary_last_hits() {
        let mut a = Army::load().unwrap();
        let w = World::load().unwrap();
        for _ in 0..4000 {
            // One active player hypothetically controlling all three lanes.
            // Inputs below apply legal damage, without forcing any core state.
            if a.tick % 20 == 0 {
                let enemies: Vec<_> = a
                    .targets()
                    .filter(|u| u.team == Team::Moon)
                    .map(|u| u.id)
                    .collect();
                for id in enemies {
                    assert!(a.hero_hit(id, 1000.));
                }
            }
            a.step(&w);
            if a.finished() {
                break;
            }
        }
        assert_eq!(a.winner(), Some("sun"));
        assert!(a.totals.kills[0] > 30);
        assert_eq!(a.cores, [100., 0.]);
        assert!(a.totals.arrivals.iter().sum::<u32>() > 0);
    }

    #[test]
    fn fixed_inputs_replay_to_same_state() {
        let mut a = Army::load().unwrap();
        let mut b = Army::load().unwrap();
        let w = World::load().unwrap();
        for _ in 0..640 {
            a.step(&w);
            b.step(&w);
        }
        assert_eq!(a.snapshot(), b.snapshot());
        assert_eq!(a.wave_events, 2);
        let p = a.frontline_spawn_for(&w, Team::Moon);
        assert!(w.ground_target_allowed(p) && !a.units.iter().any(|u| u.overlaps(p, 0.65)));
    }

    #[test]
    #[ignore = "twenty simulated minutes; run with the optimized release profile"]
    fn twenty_minute_full_match_stays_bounded_and_all_lanes_fight() {
        let mut a = Army::load().unwrap();
        let w = World::load().unwrap();
        let mut peak = [0usize; 5];
        let mut kinds = BTreeMap::new();
        for _ in 0..24_000 {
            a.step(&w);
            let living = a.units.iter().filter(|u| u.alive()).count();
            let dead = a.units.len() - living;
            peak[0] = peak[0].max(living);
            peak[1] = peak[1].max(dead);
            peak[2] = peak[2].max(a.attacks.len());
            peak[3] = peak[3].max(a.pending_siege());
            peak[4] = peak[4].max(a.units.len());
            assert!(
                living <= 72
                    && dead <= 24
                    && a.units.len() <= 96
                    && a.attacks.len() <= 72
                    && a.pending_siege() <= 32
            );
            assert!(a.units.windows(2).all(|p| p[0].id < p[1].id));
            assert!(a
                .units
                .iter()
                .all(|u| u.hp >= 0. && u.xz.iter().all(|v| v.is_finite())));
            for u in &a.units {
                kinds.insert(u.role, ());
            }
        }
        assert_eq!(a.tick, 24_000);
        assert_eq!(a.wave_events, 41);
        assert_eq!(kinds.len(), 5);
        assert_eq!(peak[0], 72);
        assert!(a.totals.losses.iter().all(|v| *v > 0));
        assert!(a.totals.siege_impacts > 0 && a.totals.siege_hits > 0);
        // Compare independently recorded Godot evidence, including peak populations
        // sampled throughout the match rather than only the final survivors.
        let native: serde_json::Value = serde_json::from_str(include_str!(
            "../../yuga-native/docs/evidence/siege-qa/army-final.json"
        ))
        .unwrap();
        let case = native["checks"]
            .as_array()
            .unwrap()
            .iter()
            .find(|c| c["case"] == "twenty_minute_advancing_simulation_stays_finite_and_bounded")
            .unwrap();
        let ev = &case["evidence"];
        assert_eq!(case["passed"], true);
        assert_eq!(ev["ticks"], a.tick);
        assert_eq!(ev["last_match_defeats_by_lane"], json!(a.totals.losses));
        assert_eq!(ev["windups"], a.totals.siege_windups);
        assert_eq!(ev["impacts"], a.totals.siege_impacts);
        for (idx, key) in ["alive", "corpses", "attacks", "siege_attacks", "nodes"]
            .iter()
            .enumerate()
        {
            assert_eq!(ev["peak"][key], peak[idx] as u64, "peak {key}");
        }
        assert_eq!(a.cores, [100., 44.]);
        assert_eq!(a.totals.arrivals, [0, 8, 0]);
        println!("Rust 20-minute soak: peaks [live, corpses, queued, siege, nodes] {peak:?}; losses {:?}; siege hits {}",a.totals.losses,a.totals.siege_hits);
    }
}
