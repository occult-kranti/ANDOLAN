//! One authoritative native match over stdin/stdout. The WebSocket host assigns seats.
use serde::Deserialize;
use serde_json::json;
use std::io::{self, BufRead, Write};
use yuga_rust::{
    battle::{Battle, CastInput, Hero, Motion},
    world::World,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Roster {
    sun: Hero,
    moon: Hero,
}

#[derive(Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct Input {
    motion: Motion,
    casts: Vec<CastInput>,
    reload: bool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Frame {
    players: [Input; 2],
    ticks: u8,
}

fn send(game: &Battle, out: &mut impl Write, accepted: [Option<bool>; 2]) -> io::Result<()> {
    serde_json::to_writer(
        &mut *out,
        &json!({"states":[game.snapshot(0),game.snapshot(1)],"accepted":accepted}),
    )?;
    out.write_all(b"\n")?;
    out.flush()
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut lines = io::stdin().lock().lines();
    let Some(roster) = lines.next() else {
        return Ok(());
    };
    let roster: Roster = serde_json::from_str(&roster?)?;
    let world = World::load()?;
    let mut game = Battle::load(&world, roster.sun, Some(roster.moon))?;
    let mut out = io::stdout().lock();
    send(&game, &mut out, [None, None])?;
    for command in lines {
        let frame: Frame = serde_json::from_str(&command?)?;
        if !(1..=4).contains(&frame.ticks) || frame.players.iter().any(|p| p.casts.len() > 4) {
            return Err("Invalid room frame".into());
        }
        let mut accepted = [None, None];
        for (seat, player) in frame.players.iter().enumerate() {
            if player.reload {
                game.reload(seat);
            }
            for cast in &player.casts {
                accepted[seat] = Some(game.cast(seat, *cast, &world).is_ok());
            }
        }
        let motions = [frame.players[0].motion, frame.players[1].motion];
        for _ in 0..frame.ticks {
            game.step(&motions, &world);
        }
        send(&game, &mut out, accepted)?;
    }
    Ok(())
}
