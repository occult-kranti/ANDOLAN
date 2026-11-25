//! Static Sangam City geometry used by the classic TypeScript roster drill.
//! shared/map.ts and shared/simulation.ts use different bounds for bodies and shots.
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct Solid {
    pub x: f64,
    pub z: f64,
    pub w: f64,
    pub d: f64,
    pub height: f64,
}

impl Solid {
    fn contains_xz(&self, x: f64, z: f64, radius: f64) -> bool {
        (x - self.x).abs() < self.w / 2.0 + radius && (z - self.z).abs() < self.d / 2.0 + radius
    }
}

#[derive(Debug, Clone)]
pub struct Geometry {
    solids: Vec<Solid>,
}

impl Geometry {
    pub fn new(solids: Vec<Solid>) -> Self {
        Self { solids }
    }

    pub fn blocked(&self, x: f64, z: f64, radius: f64) -> bool {
        !x.is_finite()
            || !z.is_finite()
            || !radius.is_finite()
            || radius < 0.0
            || x.abs() > 68.0 - radius
            || z.abs() > 82.0 - radius
            || self.solids.iter().any(|s| s.contains_xz(x, z, radius))
    }

    /// Mirrors ArenaSimulation.move with the drill's empty live-structure list.
    pub fn move_actor(&self, mut pos: [f64; 2], delta: [f64; 2], radius: f64) -> [f64; 2] {
        let distance = delta[0].hypot(delta[1]);
        if !distance.is_finite() || !radius.is_finite() || radius < 0.0 {
            return pos;
        }
        let slices = (distance / 0.35).ceil().max(1.0);
        let dx = delta[0] / slices;
        let dz = delta[1] / slices;
        for _ in 0..slices as usize {
            let previous = pos;
            if !self.blocked(pos[0] + dx, pos[1], radius) {
                pos[0] += dx;
            }
            if !self.blocked(pos[0], pos[1] + dz, radius) {
                pos[1] += dz;
            }
            if pos == previous {
                break;
            }
        }
        pos
    }

    /// The classic sampler checks only interior points every 0.8 m or less.
    pub fn line_clear(&self, a: [f64; 2], b: [f64; 2]) -> bool {
        let dx = b[0] - a[0];
        let dz = b[1] - a[1];
        let distance = dx.hypot(dz);
        if !distance.is_finite() {
            return false;
        }
        let slices = (distance / 0.8).ceil();
        for i in 1..slices as usize {
            let fraction = i as f64 / slices;
            if self.blocked(a[0] + dx * fraction, a[1] + dz * fraction, 0.0) {
                return false;
            }
        }
        true
    }

    /// Downward pitch intersects the floor from the actor's 1.2 m eye offset.
    /// The last clear half-metre sample is the locked ground position.
    pub fn ground_aim(
        &self,
        origin: [f64; 2],
        y: f64,
        yaw: f64,
        pitch: f64,
        range: f64,
    ) -> [f64; 2] {
        if ![origin[0], origin[1], y, yaw, pitch, range]
            .iter()
            .all(|v| v.is_finite())
        {
            return origin;
        }
        let horizontal = if pitch < -0.08 {
            range.min((y + 1.2) / -pitch.tan())
        } else {
            range
        };
        let mut target = origin;
        let (dx, dz) = yaw.sin_cos();
        let mut dist = 0.5;
        while dist <= horizontal {
            let next = [origin[0] + dx * dist, origin[1] + dz * dist];
            if self.blocked(next[0], next[1], 0.0) {
                break;
            }
            target = next;
            dist += 0.5;
        }
        target
    }

    /// Test the environment at one projectile sweep sample, before a target hit.
    /// The caller advances in 3D increments of at most 0.35 m as in stepProjectiles.
    pub fn shot_blocked(&self, x: f64, y: f64, z: f64, radius: f64) -> bool {
        ![x, y, z, radius].iter().all(|v| v.is_finite())
            || radius < 0.0
            || x.abs() > 70.0
            || z.abs() > 84.0
            || !(0.05..=35.0).contains(&y)
            || self
                .solids
                .iter()
                .any(|s| y < s.height && s.contains_xz(x, z, radius))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn court() -> Geometry {
        Geometry::new(vec![Solid {
            x: -20.0,
            z: -28.0,
            w: 18.0,
            d: 18.0,
            height: 10.0,
        }])
    }

    #[test]
    fn classic_hero_slides_with_x_first_slices_and_strict_edges() {
        let g = court();
        assert!(!g.blocked(-10.35, -28., 0.65));
        assert!(g.blocked(-10.351, -28., 0.65));
        let at = g.move_actor([-8., -28.], [-5., 3.], 0.65);
        assert!((at[0] - (-10.058823529411764)).abs() < 1e-12 && (at[1] + 25.).abs() < 1e-12);
        assert_eq!(g.move_actor([67.35, 81.35], [2., 3.], 0.65), [67.35, 81.35]);
        assert_eq!(g.move_actor([0., 0.], [f64::INFINITY, 0.], 0.65), [0., 0.]);
    }

    #[test]
    fn sight_excludes_endpoints_and_downward_aim_quantizes_before_cover() {
        let g = court();
        assert!(g.line_clear([-10.8, -28.], [-11.3, -28.]));
        assert!(!g.line_clear([-9., -28.], [-18., -28.]));
        assert!(g.line_clear([-11., -30.], [-11., -26.]));
        assert!(!g.line_clear([0., 0.], [f64::NAN, 0.]));
        let wall = g.ground_aim([-8., -28.], 0., -std::f64::consts::FRAC_PI_2, 0., 18.);
        assert_eq!(wall, [-11., -28.]);
        assert_eq!(g.ground_aim([0., 0.], 0., 0., -0.5, 20.), [0., 2.]);
        assert_eq!(g.ground_aim([0., 0.], 2., 0., -0.5, 20.), [0., 5.5]);
        assert_eq!(g.ground_aim([0., 0.], 0., 0., -0.08, 19.8), [0., 19.5]);
    }

    #[test]
    fn projectile_bounds_clear_rooftops_and_expand_walls_by_its_own_radius() {
        let g = court();
        assert!(g.shot_blocked(-10.85, 9.99, -28., 0.2));
        assert!(!g.shot_blocked(-10.85, 9.99, -28., 0.1));
        assert!(!g.shot_blocked(-20., 10., -28., 0.2));
        assert!(!g.shot_blocked(70., 0.05, 84., 0.2));
        assert!(!g.shot_blocked(70., 35., 84., 0.2));
        assert!(g.shot_blocked(70.001, 3., 0., 0.2));
        assert!(g.shot_blocked(0., 0.049, 0., 0.2));
        assert!(g.shot_blocked(0., 35.001, 0., 0.2));
    }
}
