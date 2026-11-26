//! Vanara Sena exercises the real 20 Hz authority, not visual-only effects.
use serde_json::Value;
use yuga_rust::{
    battle::{Battle, CastInput, Hero, Motion},
    combat::{Combat, GroundAim, Receiver},
    world::World,
};

const SLOT: usize = 5;
const TARGET: [f32; 2] = [0., -52.5];

fn advance_combat(combat: &mut Combat, world: &World, ticks: u32) {
    for _ in 0..ticks {
        combat.tick([0., 0.], world);
    }
}

fn assert_near(actual: f64, expected: f64) {
    assert!(
        (actual - expected).abs() < 1e-7,
        "expected {expected}, got {actual}"
    );
}

fn health(combat: &Combat, id: u32) -> f64 {
    combat.receivers().iter().find(|r| r.id == id).unwrap().hp
}

#[test]
fn the_default_drill_can_demonstrate_an_ally_only_sena_without_hitting_a_guard() {
    let world = World::load().unwrap();
    let mut combat = Combat::load().unwrap();
    // The eastern rim includes the wounded escort and misses all three guards.
    combat.cast(SLOT, [3.9, -51.5], &world).unwrap();
    advance_combat(&mut combat, &world, 12);
    let state = combat.snapshot();
    let impact = state["events"]
        .as_array()
        .unwrap()
        .iter()
        .find(|e| e["kind"] == "impact")
        .unwrap();
    let receipts = impact["receipts"].as_array().unwrap();
    assert_eq!(receipts.len(), 1);
    assert_eq!(receipts[0]["unit"], 4);
    assert_eq!(receipts[0]["heal"], 12.);
    assert_eq!(receipts[0]["damage"], 0.);
    advance_combat(&mut combat, &world, 40);
    assert_near(health(&combat, 4), 102.);
    assert_near(combat.actor().hp, 275.);
    combat.reset();
    assert_near(health(&combat, 4), 90.);
}

#[test]
fn zone_has_authoritative_timing_damage_radius_and_friendly_fire_boundaries() {
    let world = World::load().unwrap();
    let mut combat = Combat::load().unwrap();
    combat.set_receivers(vec![
        Receiver::new(1, "moon", TARGET, 100., 100.),
        Receiver::new(2, "sun", TARGET, 100., 100.),
        Receiver::new(3, "moon", [3., TARGET[1]], 100., 100.),
        Receiver::new(4, "moon", [3.01, TARGET[1]], 100., 100.),
    ]);
    let start = combat.snapshot();
    assert_eq!(start["abilities"].as_array().unwrap().len(), 6);
    assert_eq!(start["abilities"][SLOT]["id"], "vanara_sena");
    assert_eq!(start["abilities"][SLOT]["full_cooldown_ticks"], 400);
    combat.cast(SLOT, TARGET, &world).unwrap();
    assert!(combat.cast(SLOT, TARGET, &world).is_err());
    advance_combat(&mut combat, &world, 11);
    assert_near(health(&combat, 1), 100.);
    assert_eq!(combat.snapshot()["active"]["phase"], "windup");
    advance_combat(&mut combat, &world, 1);
    assert_near(health(&combat, 1), 88.);
    assert_near(health(&combat, 3), 88.);
    assert_near(health(&combat, 2), 100.);
    assert_near(health(&combat, 4), 100.);
    let after_impact = combat.snapshot();
    let impacts: Vec<_> = after_impact["events"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|e| e["id"] == "vanara_sena" && e["kind"] == "impact")
        .collect();
    assert_eq!(impacts.len(), 1);
    assert_eq!(impacts[0]["tick"], 12);
    advance_combat(&mut combat, &world, 40);
    assert_near(health(&combat, 1), 72.);
    assert_near(health(&combat, 3), 72.);
    assert_near(health(&combat, 2), 100.);
    assert_near(health(&combat, 4), 100.);
    assert!(combat.snapshot()["casts"].as_array().unwrap().is_empty());
    advance_combat(&mut combat, &world, 100);
    assert_near(health(&combat, 1), 72.);
    assert!(combat.cast(SLOT, TARGET, &world).is_err());
    advance_combat(&mut combat, &world, 248);
    assert_eq!(combat.snapshot()["tick"], 400);
    assert_eq!(combat.snapshot()["abilities"][SLOT]["cooldown_ticks"], 0);
    assert!(combat.cast(SLOT, TARGET, &world).is_ok());
}

#[test]
fn targeting_rejects_out_of_range_nonfinite_airborne_and_occluded_points() {
    let world = World::load().unwrap();
    let mut combat = Combat::load().unwrap();
    let origin = [0., -55.];
    assert_eq!(
        combat.ground_aim(SLOT, origin, 0., [0., -45.], &world),
        GroundAim::Clear
    );
    assert_eq!(
        combat.ground_aim(SLOT, origin, 0., [0., -44.99], &world),
        GroundAim::OutOfRange
    );
    assert_eq!(
        combat.ground_aim(SLOT, origin, 0., [f32::NAN, -55.], &world),
        GroundAim::Unavailable
    );
    assert!(combat.cast(SLOT, [0., -44.99], &world).is_err());
    assert!(combat.cast(SLOT, [f32::NAN, -55.], &world).is_err());
    assert_eq!(combat.snapshot()["abilities"][SLOT]["cooldown_ticks"], 0);

    let a = [-10., -20.];
    let b = [-12., -18.];
    assert!(world.ground_target_allowed(a) && world.ground_target_allowed(b));
    assert!(
        !world.clear_line(a, b),
        "fixture must touch a real wall corner"
    );
    assert_eq!(
        combat.ground_aim(SLOT, a, 0., b, &world),
        GroundAim::Obstructed
    );
    combat.set_position(a);
    assert!(combat.cast(SLOT, b, &world).is_err());
    assert_eq!(combat.snapshot()["abilities"][SLOT]["cooldown_ticks"], 0);

    combat.reset();
    combat.set_aim([0., 1.]);
    combat.cast(2, origin, &world).unwrap();
    advance_combat(&mut combat, &world, 8);
    let snapshot = combat.snapshot();
    let height = snapshot["actor"]["y"].as_f64().unwrap() as f32;
    let pos: [f32; 2] = serde_json::from_value(snapshot["actor"]["pos"].clone()).unwrap();
    assert!(height > 0.35);
    assert_eq!(
        combat.ground_aim(SLOT, pos, height, pos, &world),
        GroundAim::InvalidOrigin
    );
    assert!(combat.cast(SLOT, pos, &world).is_err());
    assert_eq!(combat.snapshot()["abilities"][SLOT]["cooldown_ticks"], 0);
}

#[test]
fn opponents_can_leave_the_zone_and_cover_blocks_its_damage() {
    let world = World::load().unwrap();
    let mut combat = Combat::load().unwrap();
    combat.set_receivers(vec![Receiver::new(1, "moon", TARGET, 100., 100.)]);
    combat.cast(SLOT, TARGET, &world).unwrap();
    advance_combat(&mut combat, &world, 12);
    assert_near(health(&combat, 1), 88.);
    combat.set_receivers(vec![Receiver::new(1, "moon", [4., TARGET[1]], 88., 100.)]);
    advance_combat(&mut combat, &world, 40);
    assert_near(health(&combat, 1), 88.);

    let center = [-10., -20.];
    let behind_corner = [-12., -18.];
    assert!(!world.clear_line(center, behind_corner));
    combat.reset();
    combat.set_position(center);
    combat.set_receivers(vec![
        Receiver::new(1, "moon", behind_corner, 100., 100.),
        Receiver::new(2, "moon", [-8., -20.], 100., 100.),
        Receiver::new(3, "sun", behind_corner, 50., 100.),
        Receiver::new(4, "sun", [-8., -20.], 50., 100.),
    ]);
    combat.cast(SLOT, center, &world).unwrap();
    advance_combat(&mut combat, &world, 52);
    assert_near(health(&combat, 1), 100.);
    assert_near(health(&combat, 2), 72.);
    assert_near(health(&combat, 3), 50.);
    assert_near(health(&combat, 4), 62.);
}

#[test]
fn interrupted_windup_cannot_damage_and_does_not_refund_cooldown() {
    let world = World::load().unwrap();
    let mut combat = Combat::load().unwrap();
    combat.set_receivers(vec![
        Receiver::new(1, "moon", TARGET, 100., 100.),
        Receiver::new(2, "sun", TARGET, 50., 100.),
    ]);
    combat.cast(SLOT, TARGET, &world).unwrap();
    advance_combat(&mut combat, &world, 11);
    combat.interrupt();
    advance_combat(&mut combat, &world, 52);
    assert_near(health(&combat, 1), 100.);
    assert_near(health(&combat, 2), 50.);
    let snapshot = combat.snapshot();
    assert!(snapshot["casts"].as_array().unwrap().is_empty());
    assert!(
        snapshot["abilities"][SLOT]["cooldown_ticks"]
            .as_u64()
            .unwrap()
            > 0
    );
    assert!(!snapshot["events"]
        .as_array()
        .unwrap()
        .iter()
        .any(|e| e["id"] == "vanara_sena" && (e["kind"] == "release" || e["kind"] == "impact")));
}

fn position_duel(battle: &mut Battle, world: &World) {
    let target: [[f32; 2]; 2] = [[11., -1.], [11., 1.]];
    let mut positions: [[f32; 2]; 2] = [[0.; 2]; 2];
    for (i, pos) in positions.iter_mut().enumerate() {
        *pos = serde_json::from_value(battle.snapshot(i).unwrap()["actor"]["pos"].clone()).unwrap();
    }
    let distance = positions
        .iter()
        .zip(target)
        .map(|(p, q)| (q[0] - p[0]).hypot(q[1] - p[1]))
        .fold(0., f32::max);
    let ticks = (distance / 0.25).ceil() as u32;
    let motions: Vec<_> = positions
        .iter()
        .zip(target)
        .enumerate()
        .map(|(seat, (p, q))| Motion {
            movement: [
                (q[0] - p[0]) / (ticks as f32 * 0.25),
                (q[1] - p[1]) / (ticks as f32 * 0.25),
            ],
            aim: [0., if seat == 0 { 1. } else { -1. }],
        })
        .collect();
    for _ in 0..ticks {
        battle.step(&motions, world);
    }
    for (seat, expected) in target.iter().enumerate() {
        let pos: [f32; 2] =
            serde_json::from_value(battle.snapshot(seat).unwrap()["actor"]["pos"].clone()).unwrap();
        assert!(
            (pos[0] - expected[0]).hypot(pos[1] - expected[1]) < 0.01,
            "seat {seat}: {pos:?}"
        );
    }
}

fn cast_match(
    b: &mut Battle,
    w: &World,
    seat: usize,
    slot: usize,
    point: [f32; 2],
) -> Result<(), String> {
    b.cast(
        seat,
        CastInput {
            slot,
            ground: point,
            aim: [0., if seat % 2 == 0 { 1. } else { -1. }],
        },
        w,
    )
}

#[test]
fn a_real_opponent_can_knock_out_the_caster_before_release() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Hanuman; 2]).unwrap();
    position_duel(&mut battle, &world);
    for _ in 0..8 {
        cast_match(&mut battle, &world, 1, 0, [11., -1.]).unwrap();
        for _ in 0..12 {
            battle.step(&[], &world);
        }
    }
    assert_near(
        battle.snapshot(0).unwrap()["actor"]["hp"].as_f64().unwrap(),
        28.,
    );
    let defender_hp = battle.snapshot(1).unwrap()["actor"]["hp"].as_f64().unwrap();
    cast_match(&mut battle, &world, 0, SLOT, [11., 1.]).unwrap();
    cast_match(&mut battle, &world, 1, 0, [11., -1.]).unwrap();
    for _ in 0..5 {
        battle.step(&[], &world);
    }
    assert_eq!(battle.snapshot(0).unwrap()["actor"]["alive"], false);
    for _ in 0..60 {
        battle.step(&[], &world);
    }
    assert_near(
        battle.snapshot(1).unwrap()["actor"]["hp"].as_f64().unwrap(),
        defender_hp,
    );
    assert_eq!(
        battle.snapshot(0).unwrap()["army"]["units"],
        serde_json::json!([])
    );
}

#[test]
fn rama_cannot_use_the_hanuman_only_sixth_slot() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Rama, Hero::Hanuman]).unwrap();
    let start = battle.snapshot(0).unwrap();
    let target: [f32; 2] = serde_json::from_value(start["actor"]["pos"].clone()).unwrap();
    assert!(battle
        .cast(
            0,
            CastInput {
                slot: SLOT,
                ground: target,
                aim: [-1., 0.]
            },
            &world
        )
        .is_err());
    assert_eq!(
        battle.snapshot(0).unwrap()["abilities"]
            .as_array()
            .unwrap()
            .len(),
        5
    );
    assert_eq!(battle.snapshot(0).unwrap()["actor"], start["actor"]);
}

#[test]
fn ten_seat_match_represents_one_authoritative_cast_in_remote_views() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Hanuman; 10]).unwrap();
    let motions: Vec<_> = (0..10)
        .map(|seat| Motion {
            movement: [0., if seat % 2 == 0 { 1. } else { -1. }],
            aim: [0., if seat % 2 == 0 { 1. } else { -1. }],
        })
        .collect();
    for _ in 0..60 {
        battle.step(&motions, &world);
    }
    let target: [f32; 2] =
        serde_json::from_value(battle.snapshot(1).unwrap()["actor"]["pos"].clone()).unwrap();
    let sun_before = battle.snapshot(0).unwrap()["actor"]["hp"].as_f64().unwrap();
    let moon_before = battle.snapshot(1).unwrap()["actor"]["hp"].as_f64().unwrap();
    cast_match(&mut battle, &world, 0, SLOT, target).unwrap();
    let local = battle.snapshot(0).unwrap();
    let remote = battle.snapshot(1).unwrap();
    let other: &Value = remote["roster"]
        .as_array()
        .unwrap()
        .iter()
        .find(|v| v["seat"] == 0)
        .unwrap();
    assert_eq!(other["casts"], local["casts"]);
    assert_eq!(other["casts"][0]["id"], "vanara_sena");
    for _ in 0..52 {
        battle.step(&[], &world);
    }
    assert_near(
        battle.snapshot(0).unwrap()["actor"]["hp"].as_f64().unwrap(),
        sun_before,
    );
    assert_near(
        battle.snapshot(1).unwrap()["actor"]["hp"].as_f64().unwrap(),
        moon_before - 28.,
    );
    for seat in 0..10 {
        let s = battle.snapshot(seat).unwrap();
        assert_eq!(s["army"]["units"], serde_json::json!([]));
        assert_eq!(s["roster"].as_array().unwrap().len(), 9);
    }
}

#[test]
fn simultaneous_allied_sena_fields_accumulate_without_friendly_damage() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Hanuman; 6]).unwrap();
    let motions: Vec<_> = (0..6)
        .map(|seat| Motion {
            movement: [0., if seat % 2 == 0 { 1. } else { -1. }],
            aim: [0., if seat % 2 == 0 { 1. } else { -1. }],
        })
        .collect();
    for _ in 0..60 {
        battle.step(&motions, &world);
    }
    let target: [f32; 2] =
        serde_json::from_value(battle.snapshot(1).unwrap()["actor"]["pos"].clone()).unwrap();
    let ally_before = battle.snapshot(0).unwrap()["actor"]["hp"].as_f64().unwrap();
    let enemy_before = battle.snapshot(1).unwrap()["actor"]["hp"].as_f64().unwrap();
    cast_match(&mut battle, &world, 0, SLOT, target).unwrap();
    cast_match(&mut battle, &world, 2, SLOT, target).unwrap();
    for _ in 0..12 {
        battle.step(&[], &world);
    }
    assert_near(
        battle.snapshot(1).unwrap()["actor"]["hp"].as_f64().unwrap(),
        enemy_before - 24.,
    );
    for _ in 0..40 {
        battle.step(&[], &world);
    }
    assert_near(
        battle.snapshot(1).unwrap()["actor"]["hp"].as_f64().unwrap(),
        enemy_before - 56.,
    );
    assert_near(
        battle.snapshot(0).unwrap()["actor"]["hp"].as_f64().unwrap(),
        ally_before,
    );
}
