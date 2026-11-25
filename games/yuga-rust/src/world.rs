//! Ground-plane authority for the native Confluence map, in metres (X, Z).
use parry2d::math::{Isometry, Point, Vector};
use parry2d::query::{cast_shapes, contact, PointQuery, Ray, RayCast, ShapeCastOptions};
use parry2d::shape::{Ball, Cuboid};
use serde::Deserialize;
use serde_json::{json, Value};

const MAP: &str = include_str!("../../yuga-native/assets/world/confluence-map.json");
const SKIN: f32 = 0.001;

#[derive(Deserialize)]
struct Bounds {
    actor_xz: [f32; 4],
    floor_y: f32,
    hero_radius: f32,
}

#[derive(Deserialize)]
struct BoxSpec {
    id: String,
    position: [f32; 3],
    size: [f32; 3],
    anchor: String,
    collision_layer: u32,
}

#[derive(Deserialize)]
struct Traversal {
    native_collision_boxes: Vec<BoxSpec>,
}

#[derive(Deserialize)]
struct Manifest {
    id: String,
    schema_version: u32,
    revision: u32,
    bounds: Bounds,
    lanes: Vec<serde::de::IgnoredAny>,
    props: Vec<serde::de::IgnoredAny>,
    lights: Vec<serde::de::IgnoredAny>,
    waters: Vec<serde::de::IgnoredAny>,
    authority_collision_boxes: Vec<BoxSpec>,
    traversal: Traversal,
}

#[derive(Debug)]
struct Solid {
    pose: Isometry<f32>,
    shape: Cuboid,
}

#[derive(Debug)]
pub struct World {
    solids: Vec<Solid>,
    ball: Ball,
    // Permitted actor-center range, already inset by the actor radius.
    limits: [f32; 4],
    summary: Value,
}

impl World {
    pub fn load() -> Result<Self, String> {
        Self::parse(MAP)
    }

    fn parse(text: &str) -> Result<Self, String> {
        let map: Manifest = serde_json::from_str(text).map_err(|e| e.to_string())?;
        let [left, right, north, south] = map.bounds.actor_xz;
        let radius = map.bounds.hero_radius;
        if map.schema_version != 1
            || ![left, right, north, south, radius, map.bounds.floor_y]
                .iter()
                .all(|v| v.is_finite())
            || radius <= 0.0
            || right - left <= 2.0 * radius
            || south - north <= 2.0 * radius
        {
            return Err("Unsupported Confluence schema or invalid actor bounds".into());
        }
        let mut solids = Vec::new();
        for spec in map
            .authority_collision_boxes
            .iter()
            .chain(&map.traversal.native_collision_boxes)
        {
            if spec.anchor != "base_center"
                || !spec.position.iter().all(|v| v.is_finite())
                || !spec.size.iter().all(|v| v.is_finite() && *v > 0.0)
            {
                return Err(format!("Invalid base-centered cuboid {}", spec.id));
            }
            if spec.collision_layer & 1 == 0
                || spec.position[1] > map.bounds.floor_y
                || spec.position[1] + spec.size[1] <= map.bounds.floor_y
            {
                continue;
            }
            solids.push(Solid {
                pose: Isometry::translation(spec.position[0], spec.position[2]),
                shape: Cuboid::new(Vector::new(spec.size[0] / 2., spec.size[2] / 2.)),
            });
        }
        let summary = json!({
            "id": map.id, "revision": map.revision, "lanes": map.lanes.len(),
            "props": map.props.len(), "lights": map.lights.len(), "waters": map.waters.len(),
            "authority_boxes": map.authority_collision_boxes.len(),
            "traversal_boxes": map.traversal.native_collision_boxes.len(),
            "ground_solids": solids.len(), "hero_radius": radius, "actor_xz": map.bounds.actor_xz
        });
        Ok(Self {
            solids,
            ball: Ball::new(radius),
            limits: [
                left + radius,
                right - radius,
                north + radius,
                south - radius,
            ],
            summary,
        })
    }

    pub fn summary(&self) -> Value {
        self.summary.clone()
    }

    fn clamp(&self, point: Vector<f32>) -> Vector<f32> {
        Vector::new(
            point.x.clamp(self.limits[0], self.limits[1]),
            point.y.clamp(self.limits[2], self.limits[3]),
        )
    }

    /// Invalid saved or externally supplied positions can begin inside a collider.
    fn recover_position(&self, mut point: Vector<f32>) -> Vector<f32> {
        point = self.clamp(point);
        for solid in &self.solids {
            if let Some(hit) = contact(
                &solid.pose,
                &solid.shape,
                &Isometry::from(point),
                &self.ball,
                0.,
            )
            .expect("Parry supports ball/cuboid contact")
            {
                if hit.dist < 0. {
                    point = self.clamp(point + *hit.normal1 * (SKIN - hit.dist));
                }
            }
        }
        point
    }

    /// Sweep the actor disc along a displacement, including the eight native traversal decks.
    pub fn move_actor(&self, from: [f32; 2], delta: [f32; 2]) -> [f32; 2] {
        if !from.iter().all(|v| v.is_finite()) {
            return [0., 0.];
        }
        let mut point = self.recover_position(Vector::from(from));
        if !delta.iter().all(|v| v.is_finite()) {
            return point.into();
        }
        let mut remaining = Vector::from(delta);
        // Distances beyond the whole map need only retain their heading. Compute in f64
        // so even finite f32::MAX input keeps a finite shape-cast argument.
        let max_travel =
            2.0 * ((self.limits[1] - self.limits[0]).hypot(self.limits[3] - self.limits[2]));
        let length = f64::from(delta[0]).hypot(f64::from(delta[1]));
        if length > f64::from(max_travel) {
            remaining *= (f64::from(max_travel) / length) as f32;
        }
        for _ in 0..4 {
            let distance = remaining.norm();
            if distance < 1.0e-6 {
                break;
            }
            let mut first = None;
            let mut consider = |t: f32, normal: Vector<f32>| {
                if (0.0..=1.0).contains(&t)
                    && remaining.dot(&normal) < -1.0e-6
                    && first.as_ref().is_none_or(|(best, _)| t < *best)
                {
                    first = Some((t, normal));
                }
            };
            for (axis, lower, upper) in [
                (0, self.limits[0], self.limits[1]),
                (1, self.limits[2], self.limits[3]),
            ] {
                let v = remaining[axis];
                if v != 0. {
                    let mut n = Vector::zeros();
                    n[axis] = -v.signum();
                    let bound = if v > 0. { upper } else { lower };
                    consider((bound - point[axis]) / v, n);
                }
            }
            let actor = Isometry::from(point);
            for solid in &self.solids {
                let options = ShapeCastOptions {
                    max_time_of_impact: 1.,
                    stop_at_penetration: false,
                    ..Default::default()
                };
                if let Some(hit) = cast_shapes(
                    &solid.pose,
                    &Vector::zeros(),
                    &solid.shape,
                    &actor,
                    &remaining,
                    &self.ball,
                    options,
                )
                .expect("Parry supports ball/cuboid shape casts")
                {
                    consider(hit.time_of_impact, *hit.normal1);
                }
            }
            let Some((time, normal)) = first else {
                point += remaining;
                break;
            };
            point += remaining * (time - SKIN / distance).max(0.);
            remaining *= 1. - time;
            remaining -= normal * remaining.dot(&normal);
        }
        self.clamp(point).into()
    }

    fn floor_bounds(&self, margin: f32) -> [f32; 4] {
        let offset = margin - self.ball.radius;
        [
            self.limits[0] + offset,
            self.limits[1] - offset,
            self.limits[2] + offset,
            self.limits[3] - offset,
        ]
    }

    /// Cast the segment against the horizontally expanded blockers used by the lane authority.
    fn wall_fraction(&self, from: Point<f32>, to: Point<f32>, margin: f32) -> Option<f32> {
        let ray = Ray::new(from, to - from);
        self.solids
            .iter()
            .filter_map(|solid| {
                let expanded = Cuboid::new(solid.shape.half_extents.add_scalar(margin));
                if ray.dir == Vector::zeros() {
                    return expanded.contains_point(&solid.pose, &from).then_some(0.);
                }
                expanded.cast_ray(&solid.pose, &ray, 1., true)
            })
            .reduce(f32::min)
    }

    /// Point-to-point ground sight line. Touching a solid counts as occlusion.
    pub fn clear_line(&self, from: [f32; 2], to: [f32; 2]) -> bool {
        self.clear_line_with_margin(from, to, 0.)
    }

    /// Recheck a locked straight route with its own kit clearance at release.
    pub fn clear_line_with_margin(&self, from: [f32; 2], to: [f32; 2], margin: f32) -> bool {
        let a = Point::from(from);
        let b = Point::from(to);
        margin.is_finite()
            && margin >= 0.
            && (b - a).iter().all(|v| v.is_finite())
            && self.wall_fraction(a, b, margin).is_none()
    }

    /// Fixed disks may not be targeted outside the playable floor or on a blocker.
    pub fn ground_target_allowed(&self, at: [f32; 2]) -> bool {
        let [x, z] = at;
        let [xmin, xmax, zmin, zmax] = self.floor_bounds(0.05);
        (xmin..=xmax).contains(&x)
            && (zmin..=zmax).contains(&z)
            && self
                .wall_fraction(Point::from(at), Point::from(at), 0.05)
                .is_none()
    }

    /// Straight-line movement intent. The actor's disc still sweeps the actual travel.
    pub fn vault_endpoint(
        &self,
        from: [f32; 2],
        aim: [f32; 2],
        range: f32,
        clearance: f32,
    ) -> Option<[f32; 2]> {
        if !self.ground_target_allowed(from)
            || !range.is_finite()
            || range <= 0.
            || !clearance.is_finite()
            || clearance < 0.
        {
            return None;
        }
        let unit = Vector::from(aim).try_normalize(0.0001)?;
        let start = Point::from(from);
        let end = start + unit * range;
        if !end.iter().all(|v| v.is_finite()) {
            return None;
        }
        let fraction = self
            .wall_fraction(start, end, clearance)
            .map_or(1., |t| (t - 0.025).max(0.));
        let point = start + (end - start) * fraction;
        let [xmin, xmax, zmin, zmax] = self.floor_bounds(clearance);
        if xmin > xmax || zmin > zmax {
            return None;
        }
        let target = Point::new(point.x.clamp(xmin, xmax), point.y.clamp(zmin, zmax));
        ((target - start).norm() >= 0.5).then(|| [target.x, target.y])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn close(a: f32, b: f32, tolerance: f32) {
        assert!((a - b).abs() <= tolerance, "{a} versus {b}");
    }

    #[test]
    fn loads_native_ground_solids_and_preserves_clear_routes() {
        let w = World::load().unwrap();
        assert_eq!(w.summary()["ground_solids"], 16);
        assert_eq!(w.summary()["lanes"], 3);
        for x in [-40., 0., 40.] {
            let end = w.move_actor([x, -85.], [0., 170.]);
            close(end[1], 85., 0.002);
        }
        // Traversal decks and art-only water represent different geometry.
        assert!(!w.clear_line([-20., -100.], [-20., -75.]));
        assert!(w.clear_line([0., -112.], [0., 112.]));
    }

    #[test]
    fn high_speed_disc_stops_and_slides_along_wall() {
        let w = World::load().unwrap();
        let end = w.move_actor([0., -28.], [-120., 0.]);
        close(end[0], -11. + 0.65, 0.008);
        let slide = w.move_actor([0., -32.], [-25., 8.]);
        close(slide[0], -11. + 0.65, 0.015);
        close(slide[1], -24., 0.015);
        let tangent = w.move_actor(slide, [0., 1.]);
        close(tangent[1], -23., 0.015);
    }

    #[test]
    fn round_corner_clearance_map_bounds_and_input_edges() {
        let w = World::load().unwrap();
        // Near the (-11,-19) wall corner a round disc fits the square's cutaway.
        let outside = [-10.50, -18.50];
        assert_eq!(w.move_actor(outside, [0., 0.]), outside);
        assert!(!w.clear_line([-40., -28.], [0., -28.]));
        assert!(!w.clear_line([-11., -19.], [-11., -19.]));
        assert!(w.clear_line([0., 0.], [0., 0.]));
        assert!(!w.clear_line([f32::NAN, 0.], [0., 0.]));
        let escaped = w.move_actor([20., 28.], [0., 0.]);
        assert!(w.clear_line(escaped, escaped));
        let edge = w.move_actor([0., 0.], [0., f32::MAX]);
        close(edge[1], 127.35, 0.006);
        let back = w.move_actor(edge, [0., -1.]);
        close(back[1], edge[1] - 1.0, 0.005);
    }

    #[test]
    fn cast_floor_and_vault_plan_use_native_margins() {
        let w = World::load().unwrap();
        assert!(w.clear_line([-10.8, -36.], [-10.8, -20.]));
        assert!(!w.clear_line_with_margin([-10.8, -36.], [-10.8, -20.], 0.48));
        assert!(!w.clear_line_with_margin([0., 0.], [0., 1.], f32::NAN));
        assert!(w.ground_target_allowed([67.9, 0.]));
        assert!(!w.ground_target_allowed([68., 0.]));
        assert!(!w.ground_target_allowed([-10.96, -28.]));
        assert!(w.ground_target_allowed([-10.94, -28.]));
        assert!(w.clear_line([0., 126.], [0., 135.])); // Clear sight alone cannot authorize a cast.
        assert!(!w.ground_target_allowed([0., 135.]));
        let near_wall = w.vault_endpoint([-8., -28.], [-1., 0.], 8.5, 0.48).unwrap();
        close(near_wall[0], -10.3075, 0.002);
        assert!(w
            .vault_endpoint([-10.45, -28.], [-1., 0.], 8.5, 0.48)
            .is_none());
        let near_edge = w.vault_endpoint([0., 126.9], [0., 1.], 8.5, 0.48).unwrap();
        close(near_edge[1], 127.52, 0.002);
        let actual = w.move_actor([0., 126.9], [0., near_edge[1] - 126.9]);
        close(actual[1], 127.35, 0.003);
        assert!(w.vault_endpoint([0., 0.], [0., 0.], 8.5, 0.48).is_none());
    }

    #[test]
    fn practice_actors_and_map_visuals_agree_with_the_ground_contract() {
        use crate::combat::Combat;
        let world = World::load().unwrap();
        let game = Combat::load().unwrap().snapshot();
        let actor: [f32; 2] = serde_json::from_value(game["actor"]["pos"].clone()).unwrap();
        for unit in std::iter::once(&game["actor"]).chain(game["targets"].as_array().unwrap()) {
            let at: [f32; 2] = serde_json::from_value(unit["pos"].clone()).unwrap();
            assert_eq!(world.move_actor(at, [0., 0.]), at);
            assert!(world.ground_target_allowed(at) && world.clear_line(actor, at));
        }
        let m: Value = serde_json::from_str(MAP).unwrap();
        for solid in m["authority_collision_boxes"].as_array().unwrap() {
            let visual = m["props"]
                .as_array()
                .unwrap()
                .iter()
                .find(|p| p["authority_collision_id"] == solid["id"])
                .unwrap();
            assert_eq!(visual["position"], solid["position"]);
            assert_eq!(visual["scale"], solid["size"]);
        }
        for solid in m["traversal"]["native_collision_boxes"].as_array().unwrap() {
            let visual = m["traversal"]["landmarks"]
                .as_array()
                .unwrap()
                .iter()
                .find(|l| l["id"] == solid["landmark_id"])
                .unwrap();
            assert_eq!(visual["position"], solid["position"]);
            assert_eq!(visual["size"], solid["size"]);
        }
    }

    #[test]
    fn rejects_bad_geometry_instead_of_creating_broken_colliders() {
        let mut m: Value = serde_json::from_str(MAP).unwrap();
        m["authority_collision_boxes"][0]["size"][0] = json!(-1);
        assert!(World::parse(&m.to_string()).is_err());
        m["authority_collision_boxes"] = json!([]);
        m["bounds"]["hero_radius"] = json!(100);
        assert!(World::parse(&m.to_string()).is_err());
    }
}
