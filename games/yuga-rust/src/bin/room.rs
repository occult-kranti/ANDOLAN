//! One authoritative native match over stdin/stdout. The WebSocket host assigns seats.
use serde::Deserialize;
use serde_json::json;
use std::io::{self, BufRead, Write};
use yuga_rust::{
    battle::{Battle, CastInput, Hero, Motion},
    world::World,
};

#[derive(Deserialize)]
#[serde(untagged, deny_unknown_fields)]
enum Roster {
    Duel { sun: Hero, moon: Hero },
    Squad { heroes: [Hero; 6] },
    FiveTeam { heroes: [Hero; 10] },
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
    players: Vec<Input>,
    ticks: u8,
}

fn send(game: &Battle, out: &mut impl Write, accepted: &[Option<bool>]) -> io::Result<()> {
    let states: Vec<_> = (0..accepted.len())
        .map(|seat| game.snapshot(seat))
        .collect();
    serde_json::to_writer(&mut *out, &json!({"states":states,"accepted":accepted}))?;
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
    let heroes = match roster {
        Roster::Duel { sun, moon } => vec![sun, moon],
        Roster::Squad { heroes } => heroes.to_vec(),
        Roster::FiveTeam { heroes } => heroes.to_vec(),
    };
    let mut game = Battle::with_hero_roster(&world, &heroes)?;
    let mut accepted = vec![None; heroes.len()];
    let mut out = io::stdout().lock();
    send(&game, &mut out, &accepted)?;
    for command in lines {
        let frame: Frame = serde_json::from_str(&command?)?;
        if frame.players.len() != heroes.len()
            || !(1..=4).contains(&frame.ticks)
            || frame.players.iter().any(|p| {
                p.casts.len() > 4
                    || !p
                        .motion
                        .movement
                        .iter()
                        .chain(&p.motion.aim)
                        .all(|v| v.is_finite())
                    || p.casts
                        .iter()
                        .any(|cast| !cast.ground.iter().chain(&cast.aim).all(|v| v.is_finite()))
            })
        {
            return Err("Invalid room frame".into());
        }
        accepted.fill(None);
        for (seat, player) in frame.players.iter().enumerate() {
            if player.reload {
                game.reload(seat);
            }
            for cast in &player.casts {
                accepted[seat] = Some(game.cast(seat, *cast, &world).is_ok());
            }
        }
        let motions: Vec<_> = frame.players.iter().map(|p| p.motion).collect();
        for _ in 0..frame.ticks {
            game.step(&motions, &world);
        }
        send(&game, &mut out, &accepted)?;
    }
    Ok(())
}
