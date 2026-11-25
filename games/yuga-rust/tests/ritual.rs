//! Behavioural boundaries for the isolated Ember Rite rules experiment.
use yuga_rust::{
    army::Team,
    ritual::{
        Actor, ChannelKind, Reason, RitualRound, Series, SeriesOutcome, Site, Vessel, BURN_TICKS,
        IGNITE_TICKS, QUENCH_TICKS, ROUND_TICKS, SEATS,
    },
};

fn actors() -> [Actor; SEATS] {
    let mut actors = [Actor {
        position: [10., 0.],
        alive: true,
        connected: true,
        grounded: true,
        reachable: true,
        damaged: false,
        interact: false,
    }; SEATS];
    actors[0].position = [0., 0.];
    actors
}

fn round() -> RitualRound {
    RitualRound::new(
        Team::Sun,
        [
            Site {
                center: [0., 0.],
                radius: 3.,
            },
            Site {
                center: [20., 0.],
                radius: 3.,
            },
        ],
        0,
        [0., 0.],
    )
    .unwrap()
}

fn step_n(game: &mut RitualRound, actors: &[Actor; SEATS], n: u32) {
    for _ in 0..n {
        game.step(actors).unwrap();
    }
}

fn ignite(game: &mut RitualRound, actors: &mut [Actor; SEATS]) {
    actors[0].interact = true;
    step_n(game, actors, IGNITE_TICKS);
    actors[0].interact = false;
    assert!(matches!(
        game.vessel(),
        Vessel::Burning {
            site: 0,
            remaining: BURN_TICKS,
            ..
        }
    ));
}

#[test]
fn one_carrier_ignites_for_four_seconds_and_the_fire_lasts_forty_more() {
    let mut game = round();
    let mut a = actors();
    a[0].interact = true;
    step_n(&mut game, &a, IGNITE_TICKS - 1);
    assert_eq!(game.channel().unwrap().progress, IGNITE_TICKS - 1);
    assert!(matches!(game.vessel(), Vessel::Carried { .. }));
    game.step(&a).unwrap();
    assert!(matches!(
        game.vessel(),
        Vessel::Burning {
            remaining: BURN_TICKS,
            ..
        }
    ));
    step_n(&mut game, &a, BURN_TICKS - 1);
    assert_eq!(game.outcome(), None);
    game.step(&a).unwrap();
    assert_eq!(game.outcome().unwrap().winner, Team::Sun);
    assert_eq!(game.outcome().unwrap().reason, Reason::FireCompleted);
    let tick = game.tick();
    assert!(game.step(&a).is_err());
    assert_eq!(game.tick(), tick);
}

#[test]
fn damage_release_airborne_or_leaving_the_site_cancels_ignition() {
    for interruption in 0..5 {
        let mut game = round();
        let mut a = actors();
        a[0].interact = true;
        step_n(&mut game, &a, 25);
        match interruption {
            0 => a[0].damaged = true,
            1 => a[0].interact = false,
            2 => a[0].grounded = false,
            3 => a[0].position = [3.01, 0.],
            _ => a[0].reachable = false,
        }
        game.step(&a).unwrap();
        assert_eq!(game.channel(), None);
        a[0].damaged = false;
        a[0].interact = true;
        a[0].grounded = true;
        a[0].reachable = true;
        a[0].position = [0., 0.];
        step_n(&mut game, &a, IGNITE_TICKS - 1);
        assert_eq!(game.channel().unwrap().progress, IGNITE_TICKS - 1);
        game.step(&a).unwrap();
        assert!(matches!(game.vessel(), Vessel::Burning { .. }));
    }
}

#[test]
fn dropped_vessel_persists_and_only_an_attacker_can_recover_it() {
    let mut game = round();
    let mut a = actors();
    a[0].position = [1., 0.];
    game.step(&a).unwrap();
    a[0].position = [2., 0.];
    a[0].alive = false;
    game.step(&a).unwrap();
    assert_eq!(game.vessel(), &Vessel::Dropped { at: [1., 0.] });
    a[1].position = [1., 0.];
    a[1].interact = true;
    step_n(&mut game, &a, 80);
    assert_eq!(game.vessel(), &Vessel::Dropped { at: [1., 0.] });
    for seat in [2, 4] {
        a[seat].position = [1., 0.];
        a[seat].interact = true;
    }
    game.step(&a).unwrap();
    assert!(matches!(game.vessel(), Vessel::Carried { seat: 2, .. }));
    assert_eq!(game.channel(), None); // pickup cannot also start ignition in this tick
}

#[test]
fn elimination_order_keeps_the_lit_objective_alive_after_attackers_fall() {
    let mut game = round();
    let mut a = actors();
    ignite(&mut game, &mut a);
    for seat in (0..SEATS).step_by(2) {
        a[seat].alive = false;
    }
    game.step(&a).unwrap();
    assert_eq!(game.outcome(), None);
    a[1].position = [0., 0.];
    a[1].interact = true;
    step_n(&mut game, &a, QUENCH_TICKS);
    assert_eq!(game.outcome().unwrap().reason, Reason::Quenched);
    assert_eq!(game.outcome().unwrap().winner, Team::Moon);

    let mut pre = round();
    let mut all_dead = actors();
    for actor in &mut all_dead {
        actor.alive = false;
    }
    pre.step(&all_dead).unwrap();
    assert_eq!(pre.outcome().unwrap().winner, Team::Moon);

    let mut post = round();
    let mut both = actors();
    ignite(&mut post, &mut both);
    for actor in &mut both {
        actor.alive = false;
    }
    post.step(&both).unwrap();
    assert_eq!(post.outcome().unwrap().winner, Team::Sun);
}

#[test]
fn quench_needs_one_uninterrupted_defender_and_wins_on_the_last_fire_tick() {
    let mut game = round();
    let mut a = actors();
    ignite(&mut game, &mut a);
    step_n(&mut game, &a, BURN_TICKS - QUENCH_TICKS);
    a[1].position = [0., 0.];
    a[1].interact = true;
    step_n(&mut game, &a, QUENCH_TICKS);
    assert_eq!(game.outcome().unwrap().winner, Team::Moon);
    assert_eq!(game.outcome().unwrap().reason, Reason::Quenched);

    let mut game = round();
    let mut a = actors();
    ignite(&mut game, &mut a);
    a[1].position = [0., 0.];
    a[1].interact = true;
    a[3].position = [0., 0.];
    a[3].interact = true;
    step_n(&mut game, &a, 25);
    assert_eq!(game.channel().unwrap().progress, 25); // two players do not double speed
    a[1].damaged = true;
    game.step(&a).unwrap();
    let takeover = game.channel().unwrap();
    assert_eq!(
        (takeover.kind, takeover.seat, takeover.progress),
        (ChannelKind::Quench, 3, 1)
    );
}

#[test]
fn exact_round_clock_allows_a_completed_ignite_but_not_a_late_one() {
    let mut game = round();
    let mut a = actors();
    step_n(&mut game, &a, ROUND_TICKS - IGNITE_TICKS);
    a[0].interact = true;
    step_n(&mut game, &a, IGNITE_TICKS);
    assert!(matches!(game.vessel(), Vessel::Burning { .. }));
    assert_eq!(game.outcome(), None);

    let mut game = round();
    let mut a = actors();
    step_n(&mut game, &a, ROUND_TICKS - IGNITE_TICKS + 1);
    a[0].interact = true;
    step_n(&mut game, &a, IGNITE_TICKS - 1);
    assert_eq!(game.outcome().unwrap().reason, Reason::TimeExpired);
    assert_eq!(game.outcome().unwrap().winner, Team::Moon);
}

#[test]
fn invalid_observations_and_sites_never_advance_the_round() {
    let mut game = round();
    let mut a = actors();
    a[3].position[0] = f32::NAN;
    assert!(game.step(&a).is_err());
    assert_eq!(game.tick(), 0);
    assert_eq!(game.channel(), None);
    let overlap = [
        Site {
            center: [0., 0.],
            radius: 3.,
        },
        Site {
            center: [3., 0.],
            radius: 3.,
        },
    ];
    assert!(RitualRound::new(Team::Sun, overlap, 0, [0., 0.]).is_err());
    assert!(RitualRound::new(Team::Moon, overlap, 0, [0., 0.]).is_err());
}

#[test]
fn wrong_team_and_interrupted_defenders_cannot_complete_a_quench() {
    let mut game = round();
    let mut a = actors();
    ignite(&mut game, &mut a);
    a[0].interact = true; // the attacker remains beside the vessel
    step_n(&mut game, &a, QUENCH_TICKS);
    assert_eq!(game.channel(), None);
    assert_eq!(game.outcome(), None);

    a[1].position = [0., 0.];
    a[1].interact = true;
    step_n(&mut game, &a, QUENCH_TICKS - 1);
    assert_eq!(game.channel().unwrap().progress, QUENCH_TICKS - 1);
    a[1].damaged = true;
    game.step(&a).unwrap();
    assert_eq!(game.channel(), None);
    assert_eq!(game.outcome(), None);
}

#[test]
fn ignition_uses_a_single_site_and_accepts_its_boundary() {
    let mut game = round();
    let mut a = actors();
    a[0].position = [3.001, 0.];
    a[0].interact = true;
    game.step(&a).unwrap();
    assert_eq!(game.channel(), None);
    a[0].position = [3., 0.];
    step_n(&mut game, &a, 15);
    assert_eq!(game.channel().unwrap().site, 0);
    a[0].position = [20., 0.];
    game.step(&a).unwrap();
    assert_eq!(game.channel().unwrap().site, 1);
    assert_eq!(game.channel().unwrap().progress, 1);
    step_n(&mut game, &a, IGNITE_TICKS - 1);
    assert!(matches!(game.vessel(), Vessel::Burning { site: 1, .. }));
}

#[test]
fn halftime_and_overtime_pairing_produce_a_clear_winner_or_draw() {
    let mut game = Series::default();
    for i in 0..24 {
        assert_eq!(
            game.attackers(),
            Some(if i < 12 { Team::Sun } else { Team::Moon })
        );
        game.record(if i % 2 == 0 { Team::Sun } else { Team::Moon })
            .unwrap();
    }
    assert_eq!(game.score(), [12, 12]);
    assert_eq!(game.attackers(), Some(Team::Sun));
    game.record(Team::Sun).unwrap();
    assert_eq!(game.outcome(), None); // 13–12 is not a match win in overtime
    assert_eq!(game.attackers(), Some(Team::Moon));
    game.record(Team::Sun).unwrap();
    assert_eq!(game.outcome(), Some(SeriesOutcome::Winner(Team::Sun)));
    assert!(game.record(Team::Moon).is_err());

    let mut drawn = Series::default();
    for i in 0..30 {
        drawn
            .record(if i % 2 == 0 { Team::Sun } else { Team::Moon })
            .unwrap();
    }
    assert_eq!(drawn.score(), [15, 15]);
    assert_eq!(drawn.outcome(), Some(SeriesOutcome::Draw));

    let mut regulation = Series::default();
    for _ in 0..13 {
        regulation.record(Team::Moon).unwrap();
    }
    assert_eq!(
        regulation.outcome(),
        Some(SeriesOutcome::Winner(Team::Moon))
    );
}
