//! An independent, authored floor fixture for the pinned clipmap_iw4 example target.
use clipmap_iw4::{ClipMeshRef, TraceExtents, trace_through_mesh_with_census};

fn main() {
    let vertices = [
        [-2.0, -2.0, 0.0],
        [2.0, -2.0, 0.0],
        [2.0, 2.0, 0.0],
        [-2.0, 2.0, 0.0],
    ];
    let floor_indices = [0, 2, 1, 0, 3, 2];
    let reversed_indices = [0, 1, 2, 0, 2, 3];
    let surface_flags = [17, 34];

    for (case, indices, x, should_hit) in [
        ("inside", &floor_indices, 0.5, true),
        ("outside", &floor_indices, 3.0, false),
        ("opposite winding", &reversed_indices, 0.5, false),
    ] {
        let floor = ClipMeshRef::from_linear(&vertices, indices, &surface_flags);
        let trace = TraceExtents::new([x, 0.0, 3.0], [x, 0.0, -3.0], [0.0; 3], [0.0; 3], 1);
        let (hit, stats) = trace_through_mesh_with_census(&floor, &trace);
        println!(
            "{case}: fraction={}, normal={:?}, flags={}, triangle tests={}",
            hit.fraction, hit.normal, hit.surface_flags, stats.tris_tested
        );
        assert_eq!(hit.fraction < 1.0, should_hit);
        if should_hit {
            assert!((hit.fraction - (3.0 - 0.125) / 6.0).abs() < 1e-6);
            assert_eq!(hit.normal, [0.0, 0.0, 1.0]);
            assert_eq!(hit.surface_flags, 17);
        }
    }
}
