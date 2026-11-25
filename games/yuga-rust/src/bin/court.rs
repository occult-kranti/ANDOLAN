//! Offline vertical support and capsule/headroom queries for the authored Sun west wind court.
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    env,
};

const FIXTURE: &str = include_str!("../../assets/court/native.json");
const SOURCES: &[(&str, &[u8])] = &[
    (
        "scenes/confluence_world.tscn",
        include_bytes!("../../../yuga-native/scenes/confluence_world.tscn"),
    ),
    (
        "scripts/traversal_landmarks.gd",
        include_bytes!("../../../yuga-native/scripts/traversal_landmarks.gd"),
    ),
    (
        "scripts/confluence_world.gd",
        include_bytes!("../../../yuga-native/scripts/confluence_world.gd"),
    ),
    (
        "scripts/player.gd",
        include_bytes!("../../../yuga-native/scripts/player.gd"),
    ),
    (
        "assets/world/confluence-map.json",
        include_bytes!("../../../yuga-native/assets/world/confluence-map.json"),
    ),
];
type Point = [f64; 3];
#[derive(Clone, Deserialize)]
struct Solid {
    name: String,
    min: Point,
    max: Point,
}
impl Solid {
    fn contains(&self, p: Point) -> bool {
        (0..3).all(|i| p[i] >= self.min[i] && p[i] <= self.max[i])
    }
    fn above_xz(&self, p: Point) -> bool {
        [0, 2]
            .into_iter()
            .all(|i| p[i] >= self.min[i] && p[i] <= self.max[i])
    }
}
#[derive(Deserialize)]
struct SurfaceCase {
    name: String,
    origin: Point,
    max_drop: f64,
    start_blocked: bool,
    surface_y: Option<f64>,
    ceiling_y: Option<f64>,
    can_stand: bool,
}
#[derive(Deserialize)]
struct CapsuleCase {
    name: String,
    feet: Point,
    blocked: bool,
}
#[derive(Deserialize)]
struct Court {
    schema: u32,
    engine: String,
    landmark: String,
    origin: Point,
    capsule_radius: f64,
    capsule_height: f64,
    floor_lift: f64,
    sources: BTreeMap<String, String>,
    solids: Vec<Solid>,
    samples: Vec<SurfaceCase>,
    occupancy: Vec<CapsuleCase>,
}
#[derive(Serialize, Debug)]
struct Support {
    start_blocked: bool,
    surface_y: Option<f64>,
    surface_name: Option<String>,
    ceiling_y: Option<f64>,
    can_stand: bool,
}
impl Court {
    fn load() -> Result<Self, String> {
        let c: Self = serde_json::from_str(FIXTURE).map_err(|e| e.to_string())?;
        let names: BTreeSet<_> = c.solids.iter().map(|s| &s.name).collect();
        if c.schema != 1
            || c.landmark != "sun-lift-west"
            || c.sources.len() != SOURCES.len()
            || c.solids.len() != 37
            || c.solids.len() != names.len()
            || c.samples.is_empty()
            || c.occupancy.is_empty()
            || c.capsule_radius <= 0.
            || c.capsule_height < 2. * c.capsule_radius
            || c.floor_lift <= 0.
            || c.solids.iter().any(|b| {
                (0..3)
                    .any(|i| !b.min[i].is_finite() || !b.max[i].is_finite() || b.min[i] >= b.max[i])
            })
        {
            return Err("Invalid canonical wind-court fixture".into());
        }
        for &(name, bytes) in SOURCES {
            if c.sources.get(name) != Some(&format!("{:x}", Sha256::digest(bytes))) {
                return Err(format!("Changed native source {name}; regenerate fixture"));
            }
        }
        Ok(c)
    }
    fn valid_query(&self, p: Point) -> Result<(), String> {
        if !p.iter().all(|v| v.is_finite())
            || (p[0] - self.origin[0]).abs() > 5.5
            || (p[2] - self.origin[2]).abs() > 5.5
            || !(-2.0..=24.0).contains(&p[1])
        {
            return Err(
                "Point outside this isolated court's 11 × 11 m X/Z query region or height range"
                    .into(),
            );
        }
        Ok(())
    }
    /// Squared distance from a vertical capsule's centreline segment to each native box.
    fn blocked(&self, feet: Point) -> bool {
        let r = self.capsule_radius;
        let low = feet[1] + r;
        let high = feet[1] + self.capsule_height - r;
        self.solids.iter().any(|b| {
            let dx = (b.min[0] - feet[0]).max(feet[0] - b.max[0]).max(0.);
            let dy = (b.min[1] - high).max(low - b.max[1]).max(0.);
            let dz = (b.min[2] - feet[2]).max(feet[2] - b.max[2]).max(0.);
            dx * dx + dy * dy + dz * dz < r * r
        })
    }
    fn support(&self, origin: Point, drop: f64) -> Result<Support, String> {
        self.valid_query(origin)?;
        if !drop.is_finite() || drop <= 0. || drop > 32. {
            return Err("Drop must lie in (0,32] metres".into());
        }
        let mut out = Support {
            start_blocked: false,
            surface_y: None,
            surface_name: None,
            ceiling_y: None,
            can_stand: false,
        };
        if self.solids.iter().any(|s| s.contains(origin)) {
            out.start_blocked = true;
            return Ok(out);
        }
        for b in self.solids.iter().filter(|b| b.above_xz(origin)) {
            let y = b.max[1];
            if y < origin[1] && y >= origin[1] - drop && out.surface_y.is_none_or(|v| y > v) {
                out.surface_y = Some(y);
                out.surface_name = Some(b.name.clone());
            }
            let ceiling = b.min[1];
            if ceiling > origin[1]
                && ceiling <= origin[1] + 16.
                && out.ceiling_y.is_none_or(|v| ceiling < v)
            {
                out.ceiling_y = Some(ceiling);
            }
        }
        if let Some(y) = out.surface_y {
            out.can_stand = !self.blocked([origin[0], y + self.floor_lift, origin[2]])
        }
        Ok(out)
    }
    fn verify(&self) -> Result<serde_json::Value, String> {
        let mut worst = 0.0f64;
        let mut raw_support = 0;
        let mut can_stand = 0;
        let mut ceilings = 0;
        let mut blocked_capsules = 0;
        let mut mismatches = Vec::new();
        for c in &self.samples {
            let sample = self.support(c.origin, c.max_drop)?;
            let mut same =
                c.start_blocked == sample.start_blocked && c.can_stand == sample.can_stand;
            for (a, b) in [
                (c.surface_y, sample.surface_y),
                (c.ceiling_y, sample.ceiling_y),
            ] {
                match (a, b) {
                    (Some(x), Some(y)) => {
                        let delta = (x - y).abs();
                        worst = worst.max(delta);
                        same &= delta <= 0.003
                    }
                    (None, None) => (),
                    _ => same = false,
                }
            }
            if !same {
                mismatches.push(format!(
                    "{} at {:?}: Rust {:?}, Godot blocked {} floor {:?} ceiling {:?} stand {}",
                    c.name,
                    c.origin,
                    sample,
                    c.start_blocked,
                    c.surface_y,
                    c.ceiling_y,
                    c.can_stand
                ));
            }
            raw_support += usize::from(sample.surface_y.is_some());
            can_stand += usize::from(sample.can_stand);
            ceilings += usize::from(sample.ceiling_y.is_some());
        }
        for c in &self.occupancy {
            self.valid_query(c.feet)?;
            let blocked = self.blocked(c.feet);
            blocked_capsules += usize::from(blocked);
            if blocked != c.blocked {
                mismatches.push(format!(
                    "{} capsule {:?}: Rust {blocked}, Godot {}",
                    c.name, c.feet, c.blocked
                ));
            }
        }
        if !mismatches.is_empty() {
            return Err(mismatches.join("\n"));
        }
        Ok(
            json!({"landmark":self.landmark,"native_engine":self.engine,"solids_including_floor":self.solids.len(),
            "surface_cases":self.samples.len(),"raw_support_found":raw_support,"standable":can_stand,
            "overhead_faces_found":ceilings,"capsule_cases":self.occupancy.len(),"blocked_capsules":blocked_capsules,
            "max_ray_height_error_m":worst,"capsule_radius":self.capsule_radius,"capsule_height":self.capsule_height,
            "fixture_sha256":format!("{:x}",Sha256::digest(FIXTURE.as_bytes()))}),
        )
    }
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let court = Court::load()?;
    let args: Vec<_> = env::args().skip(1).collect();
    let result=match args.iter().map(String::as_str).collect::<Vec<_>>().as_slice(){
        []|["verify"]=>court.verify()?,
        ["surface",x,y,z,drop]=>serde_json::to_value(court.support([x.parse()?,y.parse()?,z.parse()?],drop.parse()?)?)?,
        ["capsule",x,y,z]=>{let feet=[x.parse()?,y.parse()?,z.parse()?];court.valid_query(feet)?;
            json!({"feet":feet,"blocked":court.blocked(feet)})}
        _=>return Err("Usage: court [verify | surface <world-x> <ray-start-y> <world-z> <drop-metres> | capsule <world-x> <feet-y> <world-z>]".into()),
    };
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn physics_fixture_and_obsolete_box_negative_control() {
        let mut c = Court::load().unwrap();
        assert!(c.verify().is_ok());
        // The previous eight-metre footprint incorrectly fills the recess.
        let [x, y, z] = c.origin;
        c.solids.push(Solid {
            name: "OldWindCourt".into(),
            min: [x - 4., y, z - 4.],
            max: [x + 4., y + 8., z + 4.],
        });
        assert!(c.verify().is_err());
    }
    #[test]
    fn rejects_disconnected_or_nonfinite_queries() {
        let c = Court::load().unwrap();
        assert!(c.support([0., 8., 0.], 12.).is_err());
        assert!(c.support(c.origin, f64::NAN).is_err());
        assert!(c
            .support([c.origin[0], f64::INFINITY, c.origin[2]], 12.)
            .is_err());
    }
}
