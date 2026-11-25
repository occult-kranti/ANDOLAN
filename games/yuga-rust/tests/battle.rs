//! Black-box integration tests. No fixture teleports, forced kills or private state.
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use yuga_rust::{
    army::Team,
    battle::{Battle, CastInput, Hero, Motion, ENTRY_TICKS, LIMIT_TICKS},
    world::World,
};

type Point = [f32; 2];
fn pos(state: &Value) -> Point {
    serde_json::from_value(state["actor"]["pos"].clone()).unwrap()
}
fn direction(a: Point, b: Point) -> Point {
    let d = [b[0] - a[0], b[1] - a[1]];
    let n = d[0].hypot(d[1]);
    if n < 1e-6 {
        [0., 1.]
    } else {
        [d[0] / n, d[1] / n]
    }
}
fn distance(a: Point, b: Point) -> f32 {
    (a[0] - b[0]).hypot(a[1] - b[1])
}
fn motion(movement: Point, aim: Point) -> Motion {
    Motion { movement, aim }
}
fn advance(b: &mut Battle, w: &World, n: u32) {
    for _ in 0..n {
        b.step(&[], w);
    }
}
fn digest(state: &Value) -> String {
    format!("{:x}", Sha256::digest(serde_json::to_vec(state).unwrap()))
}
fn input(slot: usize, p: Point, q: Point) -> CastInput {
    CastInput {
        slot,
        aim: direction(p, q),
        ground: q,
    }
}

// Move both players into an empty area beside Temple avenue using ordinary
// walking inputs. Movement speed is 5 m/s, shared by both native hero kits.
fn walk_to(b: &mut Battle, w: &World, dest: [Point; 2]) {
    let start = [pos(&b.snapshot(0).unwrap()), pos(&b.snapshot(1).unwrap())];
    let length = distance(start[0], dest[0]).max(distance(start[1], dest[1]));
    let n = (length / 0.25).ceil().max(1.) as u32;
    let m = std::array::from_fn::<_, 2, _>(|i| {
        motion(
            [
                (dest[i][0] - start[i][0]) / (0.25 * n as f32),
                (dest[i][1] - start[i][1]) / (0.25 * n as f32),
            ],
            direction(dest[i], dest[1 - i]),
        )
    });
    for _ in 0..n {
        b.step(&m, w);
    }
    for (i, at) in dest.into_iter().enumerate() {
        assert!(distance(pos(&b.snapshot(i).unwrap()), at) < 0.001);
    }
}

#[test]
fn both_hero_kits_damage_real_troops_on_both_sides() {
    let w = World::load().unwrap();
    for pair in [[Hero::Hanuman, Hero::Rama], [Hero::Rama, Hero::Hanuman]] {
        let mut b = Battle::load(&w, pair[0], Some(pair[1])).unwrap();
        let mut enemies: [Vec<u32>; 2] = [vec![], vec![]];
        for (seat, hero) in pair.iter().enumerate() {
            let state = b.snapshot(seat).unwrap();
            let p = pos(&state);
            let friendly = if seat == 0 { Team::Sun } else { Team::Moon };
            let closest = b
                .army
                .targets()
                .filter(|u| u.team != friendly)
                .min_by(|a, c| distance(p, a.xz).total_cmp(&distance(p, c.xz)))
                .unwrap();
            enemies[seat] = b
                .army
                .targets()
                .filter(|u| u.team != friendly)
                .map(|u| u.id)
                .collect();
            assert_eq!(
                state["enemies"],
                (enemies[seat].len() + 1) as u64,
                "snapshot includes the live opposing player"
            );
            let slot = if *hero == Hero::Hanuman { 4 } else { 1 };
            b.cast(seat, input(slot, p, closest.xz), &w).unwrap();
        }
        advance(&mut b, &w, 35);
        for (seat, hero) in pair.iter().enumerate() {
            let s = b.snapshot(seat).unwrap();
            let hit = s["events"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|e| e["kind"] == "impact")
                .flat_map(|e| e["receipts"].as_array().unwrap())
                .any(|r| {
                    let (id, d) = if *hero == Hero::Hanuman {
                        (&r["unit"], &r["damage"])
                    } else {
                        (&r["unit_id"], &r["damage_applied"])
                    };
                    id.as_u64()
                        .is_some_and(|id| enemies[seat].contains(&(id as u32)))
                        && d.as_f64().unwrap_or(0.) > 0.
                });
            assert!(
                hit,
                "{hero:?} in seat {seat} failed to strike enemy troop; events {}",
                s["events"]
            );
        }
    }
}

#[test]
fn mirrored_duel_hits_simultaneously_and_respawns_after_sixty_ticks() {
    let w = World::load().unwrap();
    let mut b = Battle::load(&w, Hero::Hanuman, Some(Hero::Hanuman)).unwrap();
    let duel = [[11., -1.], [11., 1.]];
    walk_to(&mut b, &w, duel);
    let mut accepted = [0; 2];
    let mut damage_ticks = vec![];
    let mut prior = 300.;
    let mut death_tick = None;
    for _ in 0..250 {
        for seat in 0..2 {
            if b.cast(seat, input(0, duel[seat], duel[1 - seat]), &w)
                .is_ok()
            {
                accepted[seat] += 1;
            }
        }
        b.step(&[], &w);
        let s = b.snapshot(0).unwrap();
        let hp = s["actor"]["hp"].as_f64().unwrap();
        let other = s["opponent"]["actor"]["hp"].as_f64().unwrap();
        assert_eq!(
            hp, other,
            "seat order changed a simultaneous hit on tick {}",
            s["tick"]
        );
        if hp < prior {
            damage_ticks.push(b.army.tick_index());
            prior = hp;
        }
        if hp == 0. {
            death_tick = Some(b.army.tick_index());
            assert_eq!(s["respawn_ticks"], 60);
            assert_eq!(s["opponent"]["respawn_ticks"], 60);
            assert_eq!(s["knockouts"], 1);
            assert_eq!(s["opponent"]["knockouts"], 1);
            for seat in 0..2 {
                assert!(b
                    .cast(seat, input(0, duel[seat], duel[1 - seat]), &w)
                    .is_err());
            }
            break;
        }
    }
    assert_eq!(accepted, [9, 9]);
    assert_eq!(damage_ticks.len(), 9);
    let death = death_tick.unwrap();
    advance(&mut b, &w, 59);
    let dead = b.snapshot(0).unwrap();
    assert_eq!(dead["respawn_ticks"], 1);
    assert_eq!(dead["actor"]["alive"], false);
    b.step(&[], &w);
    for seat in 0..2 {
        let s = b.snapshot(seat).unwrap();
        assert_eq!(b.army.tick_index(), death + 60);
        assert_eq!(s["respawn_ticks"], 0);
        assert_eq!(s["actor"]["hp"], 300.);
        assert_eq!(s["actor"]["shield"], 0.);
        assert!(distance(pos(&s), duel[seat]) > 1. && w.ground_target_allowed(pos(&s)));
        assert!(b.cast(seat, input(0, pos(&s), duel[seat]), &w).is_ok());
    }
}

#[test]
fn invalid_seats_vectors_slots_and_ground_cannot_commit_actions() {
    let w = World::load().unwrap();
    let mut a = Battle::load(&w, Hero::Rama, None).unwrap();
    let mut valid = Battle::load(&w, Hero::Rama, None).unwrap();
    let p = pos(&a.snapshot(0).unwrap());
    let ground = [p[0], p[1] + 2.];
    let before = a.snapshot(0).unwrap();
    let mut invalid = input(0, p, ground);
    invalid.aim = [f32::NAN, 0.];
    for (seat, cast) in [
        (2, input(0, p, ground)),
        (0, input(99, p, ground)),
        (0, invalid),
        (
            0,
            CastInput {
                slot: 0,
                ground: [f32::INFINITY, 1.],
                aim: [0., 1.],
            },
        ),
    ] {
        assert!(a.cast(seat, cast, &w).is_err());
    }
    assert!(a.snapshot(1).is_none());
    assert_eq!(a.snapshot(0).unwrap(), before);
    a.step(&[motion([f32::NAN, 1.], [f32::INFINITY, f32::NAN])], &w);
    valid.step(&[], &w);
    assert_eq!(a.snapshot(0).unwrap(), valid.snapshot(0).unwrap());
    assert!(a.cast(0, input(3, p, [p[0] + 80., p[1]]), &w).is_err());
    let s = a.snapshot(0).unwrap();
    assert!(s["casts"].as_array().unwrap().is_empty());
    assert_eq!(s["ammo"], s["max_ammo"]);
    assert!(a.cast(0, input(3, p, p), &w).is_ok());
}

// Deterministic restart and long-run receipt. Hash only checkpoints, keeping the
// per-tick workload identical to playing without a renderer or JSON observers.
fn timed_replay(w: &World) -> Value {
    let mut b = Battle::load(w, Hero::Hanuman, Some(Hero::Rama)).unwrap();
    let start = b.snapshot(0).unwrap();
    assert_eq!(b.army.tick_index(), ENTRY_TICKS);
    let mut checkpoints = vec![];
    let mut shielded = false;
    let mut expired = false;
    let mut hp_before_ward = 0.0;
    const LATE: u32 = 15 * 60 * 20;
    for t in ENTRY_TICKS..LIMIT_TICKS {
        if t == ENTRY_TICKS {
            let s = b.snapshot(0).unwrap();
            let p = pos(&s);
            let target = pos(&s["opponent"]);
            b.cast(0, input(4, p, target), w).unwrap();
            let r = b.snapshot(1).unwrap();
            let q = pos(&r);
            b.cast(1, input(1, q, p), w).unwrap();
        }
        if t == LATE {
            let s = b.snapshot(1).unwrap();
            let p = pos(&s);
            assert_eq!(s["actor"]["shield"], 0.);
            hp_before_ward = s["actor"]["hp"].as_f64().unwrap();
            b.cast(1, input(3, p, p), w).unwrap();
        }
        b.step(&[], w);
        let tick = b.army.tick_index();
        if tick == LATE + 11 {
            let s = b.snapshot(1).unwrap();
            assert_eq!(s["actor"]["shield"], 55.);
            shielded = true;
        } else if tick == LATE + 102 {
            let s = b.snapshot(1).unwrap();
            assert_eq!(s["actor"]["shield"], 0.);
            assert_eq!(
                s["actor"]["hp"],
                (hp_before_ward + 45.).min(s["actor"]["max_hp"].as_f64().unwrap()),
                "90 healing ticks should add 45 HP and expiry must leave it intact"
            );
            expired = true;
        }
        if matches!(tick, 600 | 3000 | 12000 | LIMIT_TICKS) {
            let s = b.snapshot(0).unwrap();
            checkpoints.push(json!({"tick":tick,"snapshot_sha256":digest(&s),"cores":s["army"]["cores"],"winner":s["winner"]}));
        }
        if tick < LIMIT_TICKS {
            assert!(
                b.winner().is_none(),
                "core fell before the clock settlement at {tick}"
            );
        }
    }
    assert!(shielded && expired);
    let frozen = b.snapshot(0).unwrap();
    let (sun, moon) = (
        &frozen["army"]["cores"]["sun"],
        &frozen["army"]["cores"]["moon"],
    );
    let (sun, moon) = (sun.as_f64().unwrap(), moon.as_f64().unwrap());
    let expected = if sun > moon {
        "sun"
    } else if moon > sun {
        "moon"
    } else {
        "draw"
    };
    assert_eq!(b.winner(), Some(expected));
    assert_eq!(frozen["remaining_ticks"], 0);
    for i in 0..2 {
        assert!(b.cast(i, input(0, [0., 0.], [0., 1.]), w).is_err());
    }
    for _ in 0..120 {
        b.step(
            &[motion([1., 0.], [1., 0.]), motion([-1., 0.], [-1., 0.])],
            w,
        );
    }
    assert_eq!(frozen, b.snapshot(0).unwrap());
    json!({"schema":1,"fixture":"Sun Hanuman and Moon Rama on native Confluence lanes","tick_hz":20,
        "entry_tick":ENTRY_TICKS,"end_tick":LIMIT_TICKS,"played_ticks":LIMIT_TICKS-ENTRY_TICKS,
        "input_schedule":[{"tick_before_step":ENTRY_TICKS,"sun":"Mountain Pulse at Moon spawn","moon":"Piercing Dawn towards Sun spawn"},
            {"tick_before_step":LATE,"moon":"Guardian Circle on own position"}],
        "checkpoint_encoding":"SHA-256 of compact native serde_json serialization of the Sun-seat Battle snapshot",
        "start_snapshot_sha256":digest(&start),"checkpoints":checkpoints,"winner":expected,"freeze_ticks_checked":120,
        "ward":{"start_tick":LATE,"shield_at_tick":LATE+11,"shield":55,"expired_by_tick":LATE+102,"hp_before":hp_before_ward,"hp_after":(hp_before_ward+45.).min(300.)},
        "reproduce":"cargo test --release --locked --manifest-path games/yuga-rust/Cargo.toml --test battle timed_full_match_restarts_replays_and_freezes -- --nocapture"})
}

#[test]
fn timed_full_match_restarts_replays_and_freezes() {
    let w = World::load().unwrap();
    let receipt = timed_replay(&w);
    assert_eq!(
        receipt,
        timed_replay(&w),
        "a fresh match diverged under identical player input"
    );
    println!("YUGA_MATCH_SOAK {}", receipt);
}

#[test]
fn guardian_circle_applies_to_real_allied_waves_and_expires_for_both_factions() {
    let world = World::load().unwrap();
    for caster in 0..2 {
        let mut battle = Battle::load(&world, Hero::Rama, Some(Hero::Rama)).unwrap();
        let faction = if caster == 0 { Team::Sun } else { Team::Moon };
        let before = battle.snapshot(caster).unwrap();
        let p = pos(&before);
        let target = battle
            .army
            .targets()
            .filter(|u| u.team == faction)
            .min_by(|a, b| distance(p, a.xz).total_cmp(&distance(p, b.xz)))
            .unwrap();
        battle.cast(caster, input(3, p, target.xz), &world).unwrap();
        advance(&mut battle, &world, 10);
        assert!(battle.army.receivers().iter().all(|r| r.shield == 0.));
        battle.step(&[], &world);
        let troops = battle.army.receivers();
        let chosen = troops.iter().find(|r| r.id == target.id).unwrap();
        assert_eq!(chosen.shield, 55.);
        assert!(troops
            .iter()
            .all(|r| r.shield == 0. || r.team == chosen.team));
        advance(&mut battle, &world, 91);
        assert!(battle.army.receivers().iter().all(|r| r.shield == 0.));
        assert_eq!(battle.snapshot(caster).unwrap()["actor"]["shield"], 0.);
    }
}

#[test]
fn time_limit_awards_the_stronger_surviving_core() {
    let world = World::load().unwrap();
    let mut match_state = Battle::load(&world, Hero::Rama, None).unwrap();
    advance(&mut match_state, &world, LIMIT_TICKS - ENTRY_TICKS - 1);
    assert_eq!(match_state.winner(), None);
    let before = match_state.snapshot(0).unwrap();
    assert_eq!(before["remaining_ticks"], 1);
    assert_eq!(before["army"]["cores"], json!({"sun": 100.0, "moon": 44.0}));
    match_state.step(&[], &world);
    assert_eq!(match_state.winner(), Some("sun"));
    assert_eq!(match_state.army.winner(), None, "both cores survived");
    let final_state = match_state.snapshot(0).unwrap();
    assert_eq!(final_state["remaining_ticks"], 0);
    assert_eq!(final_state["army"]["cores"], before["army"]["cores"]);
}
