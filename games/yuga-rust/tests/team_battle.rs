//! Six live player seats using only public match inputs and the original Confluence world.
use serde_json::Value;
use std::collections::BTreeSet;
use yuga_rust::{
    battle::{Battle, CastInput, Hero, Motion, ENTRY_TICKS, LIMIT_TICKS},
    world::World,
};

const NEAR: [[f32; 2]; 6] = [
    [10., -1.],
    [10., 1.],
    [9., -1.],
    [9., 1.],
    [11., -1.],
    [11., 1.],
];

fn point(v: &Value) -> [f32; 2] {
    serde_json::from_value(v.clone()).unwrap()
}
fn state(b: &Battle, seat: usize) -> Value {
    b.snapshot(seat).unwrap()
}
fn hp(b: &Battle, i: usize) -> f64 {
    state(b, i)["actor"]["hp"].as_f64().unwrap()
}
fn shield(b: &Battle, i: usize) -> f64 {
    state(b, i)["actor"]["shield"].as_f64().unwrap()
}
fn advance(b: &mut Battle, w: &World, n: u32) {
    for _ in 0..n {
        b.step(&[], w);
    }
}
fn cast(b: &mut Battle, w: &World, seat: usize, slot: usize, ground: [f32; 2]) {
    b.cast(
        seat,
        CastInput {
            slot,
            ground,
            aim: [0., if seat % 2 == 0 { 1. } else { -1. }],
        },
        w,
    )
    .unwrap();
}
fn position_all(b: &mut Battle, w: &World) {
    let starts: Vec<_> = (0..6)
        .map(|i| point(&state(b, i)["actor"]["pos"]))
        .collect();
    let ticks = (starts
        .iter()
        .zip(NEAR)
        .map(|(p, q)| (p[0] - q[0]).hypot(p[1] - q[1]))
        .fold(0., f32::max)
        / 0.25)
        .ceil() as u32;
    let moves: Vec<_> = starts
        .iter()
        .zip(NEAR)
        .enumerate()
        .map(|(seat, (p, q))| Motion {
            movement: [
                (q[0] - p[0]) / (0.25 * ticks as f32),
                (q[1] - p[1]) / (0.25 * ticks as f32),
            ],
            aim: [0., if seat % 2 == 0 { 1. } else { -1. }],
        })
        .collect();
    for _ in 0..ticks {
        b.step(&moves, w);
    }
    for (seat, target) in NEAR.into_iter().enumerate() {
        let p = point(&state(b, seat)["actor"]["pos"]);
        assert!(
            (p[0] - target[0]).hypot(p[1] - target[1]) < 0.001,
            "seat {seat} could not walk to fixture: {p:?}"
        );
    }
}

#[test]
fn six_real_seats_have_stable_identity_and_nonrecursive_snapshots() {
    let w = World::load().unwrap();
    for n in [0, 3, 4, 5, 7, 8] {
        assert!(Battle::with_roster(&w, &vec![Hero::Hanuman; n]).is_err());
    }
    let duel = Battle::with_roster(&w, &[Hero::Rama; 2]).unwrap();
    assert!(state(&duel, 0).get("roster").is_none());
    let solo = Battle::with_roster(&w, &[Hero::Hanuman]).unwrap();
    assert!(state(&solo, 0)["opponent"].is_null());
    let heroes = [
        Hero::Rama,
        Hero::Hanuman,
        Hero::Hanuman,
        Hero::Rama,
        Hero::Rama,
        Hero::Hanuman,
    ];
    let b = Battle::with_roster(&w, &heroes).unwrap();
    assert!(b.snapshot(6).is_none());
    let all: Vec<_> = (0..6).map(|i| state(&b, i)).collect();
    let ids: BTreeSet<_> = all
        .iter()
        .map(|p| p["actor"]["id"].as_u64().unwrap())
        .collect();
    assert_eq!(ids.len(), 6);
    for i in 0..6 {
        let s = &all[i];
        let team = if i % 2 == 0 { "sun" } else { "moon" };
        assert_eq!(s["seat"], i);
        assert_eq!(s["team"], team);
        assert_eq!(s["actor"]["team"], team);
        assert_eq!(s["actor"]["aim"][1], if i % 2 == 0 { 1. } else { -1. });
        let remote = s["roster"].as_array().unwrap();
        assert_eq!(
            remote
                .iter()
                .map(|s| s["seat"].as_u64().unwrap() as usize)
                .collect::<Vec<_>>(),
            (0..6).filter(|&seat| seat != i).collect::<Vec<_>>()
        );
        for p in remote {
            let remote_seat = p["seat"].as_u64().unwrap() as usize;
            assert_eq!(p["actor"], all[remote_seat]["actor"]);
            assert_eq!(p["hero"], all[remote_seat]["hero"]);
            assert!(p["events"].is_array() && p["abilities"].is_array());
            assert!(p.get("army").is_none() && p.get("roster").is_none());
            let x = point(&p["actor"]["pos"]);
            let y = point(&s["actor"]["pos"]);
            assert!((x[0] - y[0]).hypot(x[1] - y[1]) >= 1.3);
        }
        assert_eq!(s["opponent"]["seat"], 1 - i % 2);
        assert!(s["opponent"].get("events").is_none());
    }
}

#[test]
fn allied_healing_and_ward_reach_both_teammates_from_either_side() {
    let w = World::load().unwrap();
    for side in [0usize, 1] {
        let mut b = Battle::with_roster(
            &w,
            &[
                Hero::Hanuman,
                Hero::Hanuman,
                Hero::Rama,
                Hero::Rama,
                Hero::Hanuman,
                Hero::Hanuman,
            ],
        )
        .unwrap();
        position_all(&mut b, &w);
        cast(&mut b, &w, 1 - side, 0, NEAR[side]);
        advance(&mut b, &w, 5);
        for i in 0..6 {
            assert_eq!(hp(&b, i), if i % 2 == side { 266. } else { 300. });
        }
        let archer = 2 + side;
        cast(&mut b, &w, archer, 3, NEAR[side]);
        advance(&mut b, &w, 11);
        for i in 0..6 {
            assert_eq!(shield(&b, i), if i % 2 == side { 55. } else { 0. });
        }
        advance(&mut b, &w, 10);
        for i in 0..6 {
            assert_eq!(hp(&b, i), if i % 2 == side { 271. } else { 300. });
        }
        cast(&mut b, &w, 4 + side, 4, NEAR[side]);
        advance(&mut b, &w, 23);
        for i in 0..6 {
            assert_eq!(
                hp(&b, i),
                if i % 2 == side { 300. } else { 235. },
                "side {side}, actor {i}"
            );
            assert_eq!(shield(&b, i), if i % 2 == side { 55. } else { 0. });
        }
        let view = state(&b, 4 + side);
        let ids: BTreeSet<_> = std::iter::once(&view)
            .chain(view["roster"].as_array().unwrap().iter())
            .map(|p| p["actor"]["id"].as_u64().unwrap())
            .collect();
        let affected: BTreeSet<_> = view["events"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|e| e["kind"] == "impact" && e["slot"] == 4)
            .flat_map(|e| e["receipts"].as_array().unwrap())
            .filter_map(|r| r["unit"].as_u64())
            .filter(|id| ids.contains(id))
            .collect();
        assert_eq!(
            affected, ids,
            "every living hero, including the caster, had the published ID"
        );
        advance(&mut b, &w, 69);
        for i in 0..6 {
            assert_eq!(shield(&b, i), 0.);
        }
    }
}

#[test]
fn three_attackers_on_each_team_land_together_and_respawn_at_distinct_positions() {
    let w = World::load().unwrap();
    let mut b = Battle::with_roster(&w, &[Hero::Hanuman; 6]).unwrap();
    position_all(&mut b, &w);
    let ids: Vec<_> = (0..6)
        .map(|i| state(&b, i)["actor"]["id"].as_u64().unwrap())
        .collect();
    for round in 0..3 {
        for seat in 0..6 {
            cast(&mut b, &w, seat, 0, NEAR[1 - seat % 2]);
        }
        advance(&mut b, &w, 5);
        for seat in 0..6 {
            assert_eq!(
                hp(&b, seat),
                (300.0_f64 - 102. * f64::from(round + 1)).max(0.)
            );
        }
        if round != 2 {
            advance(&mut b, &w, 7);
        }
    }
    for seat in 0..6 {
        let s = state(&b, seat);
        assert_eq!(s["respawn_ticks"], 60);
        assert_eq!(s["knockouts"], 1);
    }
    advance(&mut b, &w, 59);
    for seat in 0..6 {
        assert_eq!(hp(&b, seat), 0.);
    }
    advance(&mut b, &w, 1);
    let mut live: Vec<[f32; 2]> = vec![];
    for (seat, id) in ids.into_iter().enumerate() {
        let s = state(&b, seat);
        let p = point(&s["actor"]["pos"]);
        assert!(w.ground_target_allowed(p));
        assert_eq!(s["actor"]["hp"], 300.);
        assert_eq!(s["actor"]["id"], id);
        assert_eq!(s["respawn_ticks"], 0);
        assert!(live.iter().all(|q| (q[0] - p[0]).hypot(q[1] - p[1]) >= 1.3));
        live.push(p);
    }
}

#[test]
fn idle_team_match_replays_to_the_same_timeout_and_freezes_all_seats() {
    let w = World::load().unwrap();
    let run = || {
        let mut b = Battle::with_roster(
            &w,
            &[
                Hero::Rama,
                Hero::Hanuman,
                Hero::Hanuman,
                Hero::Rama,
                Hero::Rama,
                Hero::Hanuman,
            ],
        )
        .unwrap();
        advance(&mut b, &w, LIMIT_TICKS - ENTRY_TICKS - 1);
        assert!(b.winner().is_none());
        advance(&mut b, &w, 1);
        let frozen: Vec<_> = (0..6).map(|i| state(&b, i)).collect();
        let cores = &frozen[0]["army"]["cores"];
        let sun = cores["sun"].as_f64().unwrap();
        let moon = cores["moon"].as_f64().unwrap();
        let expected = if sun == moon {
            "draw"
        } else if sun > moon {
            "sun"
        } else {
            "moon"
        };
        assert_eq!(b.winner(), Some(expected));
        assert_eq!(frozen[0]["remaining_ticks"], 0);
        advance(&mut b, &w, 4);
        for i in 0..6 {
            assert_eq!(frozen[i], state(&b, i));
        }
        frozen
    };
    assert_eq!(run(), run());
}

#[test]
fn ward_releasing_on_a_lethal_tick_does_not_revive_its_caster_or_teammates() {
    let w = World::load().unwrap();
    let mut b = Battle::with_roster(
        &w,
        &[
            Hero::Hanuman,
            Hero::Hanuman,
            Hero::Rama,
            Hero::Hanuman,
            Hero::Hanuman,
            Hero::Hanuman,
        ],
    )
    .unwrap();
    position_all(&mut b, &w);
    for attackers in [&[1, 3, 5][..], &[1, 3, 5][..], &[1, 3][..]] {
        for seat in attackers {
            cast(&mut b, &w, *seat, 0, NEAR[0]);
        }
        advance(&mut b, &w, 12);
    }
    for i in [0, 2, 4] {
        assert_eq!(hp(&b, i), 28.);
    }
    cast(&mut b, &w, 2, 3, NEAR[2]);
    advance(&mut b, &w, 6);
    cast(&mut b, &w, 1, 0, NEAR[0]);
    advance(&mut b, &w, 5);
    for i in [0, 2, 4] {
        assert_eq!(hp(&b, i), 0.);
        assert_eq!(shield(&b, i), 0.);
        assert_eq!(state(&b, i)["respawn_ticks"], 60);
    }
}
