//! Hero-only rules through ordinary public movement and cast inputs.
use serde_json::{json, Value};
use yuga_rust::{
    battle::{Battle, CastInput, Hero, Motion, LIMIT_TICKS},
    world::World,
};

fn point(state: &Value) -> [f32; 2] {
    serde_json::from_value(state["actor"]["pos"].clone()).unwrap()
}

fn walk_duel(battle: &mut Battle, world: &World, dest: [[f32; 2]; 2]) {
    let starts = [
        point(&battle.snapshot(0).unwrap()),
        point(&battle.snapshot(1).unwrap()),
    ];
    let distance = starts
        .iter()
        .zip(dest)
        .map(|(p, q)| (q[0] - p[0]).hypot(q[1] - p[1]))
        .fold(0., f32::max);
    let ticks = (distance / 0.25).ceil().max(1.) as u32;
    let motions: Vec<_> = starts
        .iter()
        .zip(dest)
        .enumerate()
        .map(|(i, (p, q))| Motion {
            movement: [
                (q[0] - p[0]) / (0.25 * ticks as f32),
                (q[1] - p[1]) / (0.25 * ticks as f32),
            ],
            aim: [0., if i == 0 { 1. } else { -1. }],
        })
        .collect();
    for _ in 0..ticks {
        battle.step(&motions, world);
    }
    for (i, target) in dest.iter().enumerate() {
        let p = point(&battle.snapshot(i).unwrap());
        assert!(
            (p[0] - target[0]).hypot(p[1] - target[1]) < 0.01,
            "seat {i} stopped at {p:?}"
        );
    }
}

#[test]
fn ten_hero_seats_are_clear_and_no_waves_spawn() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Hanuman; 10]).unwrap();
    let snapshots: Vec<_> = (0..10).map(|seat| battle.snapshot(seat).unwrap()).collect();
    for (seat, s) in snapshots.iter().enumerate() {
        assert_eq!(s["ruleset"], "hero_skirmish");
        assert_eq!(s["army"]["waves_enabled"], false);
        assert_eq!(s["army"]["units"], json!([]));
        assert_eq!(s["score"], json!({"sun": 0, "moon": 0, "target": 25}));
        assert_eq!(s["roster"].as_array().unwrap().len(), 9);
        assert_eq!(
            s["actor"]["team"],
            if seat % 2 == 0 { "sun" } else { "moon" }
        );
        assert!(world.ground_target_allowed(point(s)));
        for other in snapshots.iter().take(seat) {
            let p = point(s);
            let q = point(other);
            assert!((p[0] - q[0]).hypot(p[1] - q[1]) >= 1.3, "spawn collision");
        }
    }
    for _ in 0..1201 {
        battle.step(&[], &world);
    }
    let s = battle.snapshot(0).unwrap();
    assert_eq!(s["army"]["tick"], 1201);
    assert_eq!(s["army"]["units"], json!([]));
    assert_eq!(s["army"]["attacks"], json!([]));
    assert_eq!(s["army"]["wave"], 0);
    assert_eq!(s["remaining_ticks"], LIMIT_TICKS - 1201);
    assert!(battle.winner().is_none());
}

#[test]
fn five_vs_five_hero_knockouts_count_and_end_the_match() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Hanuman; 10]).unwrap();
    let duel = [[11., -1.], [11., 1.]];
    for expected in 1..=25 {
        walk_duel(&mut battle, &world, duel);
        for _ in 0..250 {
            let _ = battle.cast(
                0,
                CastInput {
                    slot: 0,
                    ground: duel[1],
                    aim: [0., 1.],
                },
                &world,
            );
            battle.step(&[], &world);
            if battle.snapshot(0).unwrap()["score"]["sun"] == expected {
                break;
            }
        }
        let s = battle.snapshot(0).unwrap();
        assert_eq!(
            s["score"],
            json!({"sun": expected, "moon": 0, "target": 25})
        );
        assert_eq!(battle.snapshot(1).unwrap()["score"], s["score"]);
        if expected < 25 {
            assert!(battle.winner().is_none());
            for _ in 0..60 {
                battle.step(&[], &world);
            }
            assert_eq!(battle.snapshot(1).unwrap()["actor"]["alive"], true);
        }
    }
    assert_eq!(battle.winner(), Some("sun"));
    let frozen = battle.snapshot(0).unwrap();
    battle.step(&[Motion::default(); 10], &world);
    assert_eq!(battle.snapshot(0).unwrap(), frozen);
}

#[test]
fn tied_target_continues_until_a_team_takes_the_lead() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Hanuman; 10]).unwrap();
    let duel = [[11., -1.], [11., 1.]];
    for expected in 1..=25 {
        walk_duel(&mut battle, &world, duel);
        for _ in 0..250 {
            for seat in 0..2 {
                let _ = battle.cast(
                    seat,
                    CastInput {
                        slot: 0,
                        ground: duel[1 - seat],
                        aim: [0., if seat == 0 { 1. } else { -1. }],
                    },
                    &world,
                );
            }
            battle.step(&[], &world);
            if battle.snapshot(0).unwrap()["score"]["sun"] == expected {
                break;
            }
        }
        assert_eq!(
            battle.snapshot(0).unwrap()["score"],
            json!({"sun": expected, "moon": expected, "target": 25})
        );
        assert!(
            battle.winner().is_none(),
            "simultaneous target scores must remain tied"
        );
        for _ in 0..60 {
            battle.step(&[], &world);
        }
    }
    walk_duel(&mut battle, &world, duel);
    for _ in 0..250 {
        let _ = battle.cast(
            0,
            CastInput {
                slot: 0,
                ground: duel[1],
                aim: [0., 1.],
            },
            &world,
        );
        battle.step(&[], &world);
        if battle.winner().is_some() {
            break;
        }
    }
    assert_eq!(battle.winner(), Some("sun"));
    assert_eq!(
        battle.snapshot(0).unwrap()["score"],
        json!({"sun": 26, "moon": 25, "target": 25})
    );
}

#[test]
fn five_vs_five_tied_timeout_is_a_draw() {
    let world = World::load().unwrap();
    let mut battle = Battle::with_hero_roster(&world, &[Hero::Hanuman; 10]).unwrap();
    for _ in 0..LIMIT_TICKS {
        battle.step(&[], &world);
    }
    assert_eq!(battle.winner(), Some("draw"));
    assert_eq!(battle.snapshot(0).unwrap()["remaining_ticks"], 0);
}
