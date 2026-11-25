//! Headless, uncontested lane march. See docs/rust-rebuild/ARMIES.md for the Godot comparison.
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::BTreeMap;
use yuga_rust::world::World;

const MAP: &str = include_str!("../../../yuga-native/assets/world/confluence-map.json");
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
enum Team {
    Sun,
    Moon,
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
    length: f64,
}
impl Segment {
    fn position(&self, along: f64, offset: f32) -> Point {
        let [dx, dz] = self.unit;
        [
            self.start[0] + dx * along as f32 + dz * offset,
            self.start[1] + dz * along as f32 - dx * offset,
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

fn main() -> Result<(), String> {
    const USAGE:&str = "lanes [wave-number [ticks-since-spawn]]  (default 1 0, 20 ticks/s). One clear-spawn wave; units march in isolation.";
    let args: Vec<_> = std::env::args().skip(1).collect();
    if matches!(args.as_slice(),[v] if v=="--help" || v=="-h") {
        println!("{USAGE}");
        return Ok(());
    }
    if args.len() > 2 {
        return Err(USAGE.into());
    }
    let number = |i: usize, default: u32| {
        args.get(i).map_or(Ok(default), |a| {
            a.parse::<u32>().map_err(|_| USAGE.to_owned())
        })
    };
    let wave = number(0, 1)?;
    let ticks = number(1, 0)?;
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
    println!(
        "{}",
        json!({"mode":"isolated_wave_march","wave":wave,"event_seconds":(u64::from(wave)-1)*30,
        "ticks_since_spawn":ticks,"tick_seconds":STEP,"lanes":lanes,"roles":roles,"units":units})
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::Value;

    #[test]
    fn matches_every_native_cadence_record_and_both_factions() {
        let arena = Arena::load().unwrap();
        let report: Value = serde_json::from_str(include_str!(
            "../../../yuga-native/docs/evidence/siege-qa/army-final.json"
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
