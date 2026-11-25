//! A terminal driver for the same fixed-tick authority used by WebAssembly.
use serde_json::json;
use std::io::{self, BufRead, IsTerminal, Write};
use yuga_rust::{combat::Combat, world::World};

const HELP: &str = "status | aim X Z | move DX DZ TICKS | wait TICKS | cast SLOT GROUND_X GROUND_Z | reset | quit\nSlots 1–5: Gada, Kavacha, Udayana, Dahan, Mountain Pulse. One tick is 0.05 s.";

fn number(text: &str) -> Result<f32, String> {
    text.parse::<f32>()
        .ok()
        .filter(|x| x.is_finite())
        .ok_or_else(|| "expected a finite number".into())
}

fn ticks(text: &str) -> Result<u32, String> {
    text.parse::<u32>()
        .ok()
        .filter(|n| *n <= 12_000)
        .ok_or_else(|| "use 0–12000 ticks per command".into())
}

fn apply(line: &str, combat: &mut Combat, world: &World) -> Result<bool, String> {
    let words: Vec<_> = line.split_whitespace().collect();
    match words.as_slice() {
        [] => return Ok(true),
        ["quit"] => return Ok(false),
        ["help"] => {
            println!("{HELP}");
            return Ok(true);
        }
        ["status"] => {}
        ["aim", x, z] => combat.set_aim([number(x)?, number(z)?]),
        ["move", x, z, n] => {
            let movement = [number(x)?, number(z)?];
            for _ in 0..ticks(n)? {
                combat.tick(movement, world);
            }
        }
        ["wait", n] => {
            for _ in 0..ticks(n)? {
                combat.tick([0., 0.], world);
            }
        }
        ["cast", n, x, z] => {
            let slot: usize = n.parse().map_err(|_| "use slots 1–5")?;
            if !(1..=5).contains(&slot) {
                return Err("use slots 1–5".into());
            }
            combat.cast(slot - 1, [number(x)?, number(z)?], world)?;
        }
        ["reset"] => combat.reset(),
        _ => return Err(HELP.into()),
    }
    let s = combat.snapshot();
    println!(
        "{}",
        json!({"tick":s["tick"],"actor":s["actor"],"targets":s["targets"],"active":s["active"],"defeated":s["defeated"],"enemies":s["enemies"]})
    );
    Ok(true)
}

fn main() -> Result<(), String> {
    let world = World::load()?;
    let mut combat = Combat::load()?;
    if std::env::args().any(|arg| arg == "--map") {
        println!("{}", world.summary());
        return Ok(());
    }
    let stdin = io::stdin();
    let interactive = stdin.is_terminal();
    if interactive {
        println!("YUGA | Hanuman · Confluence practice\n{HELP}");
    }
    for line in stdin.lock().lines() {
        let command = line.map_err(|e| e.to_string())?;
        match apply(&command, &mut combat, &world) {
            Ok(true) => (),
            Ok(false) => break,
            Err(message) if interactive => eprintln!("{message}"),
            Err(message) => return Err(message),
        }
        io::stdout().flush().map_err(|e| e.to_string())?;
    }
    Ok(())
}
