//! Classic YUGA balance data on a small, controllable sparring court.
#[path = "roster/abilities.rs"]
mod abilities;
#[path = "roster/geometry.rs"]
mod geometry;
#[path = "roster/lab.rs"]
mod lab;
#[path = "roster/model.rs"]
mod model;

use lab::Lab;
use model::Input;
use serde_json::json;
use std::io::{self, BufRead, Write};

fn number<T: std::str::FromStr>(raw: Option<&&str>, name: &str) -> Result<T, String> {
    raw.and_then(|s| s.parse().ok())
        .ok_or_else(|| format!("Expected {name}"))
}
fn play(lab: &mut Lab) -> Result<(), String> {
    let hero = &lab.heroes[lab.units[0].kit];
    let mut yaw = 0.;
    let mut pitch = 0.;
    println!(
        "{} · {}",
        hero.name,
        hero.abilities
            .iter()
            .enumerate()
            .map(|(i, a)| format!("{} {}", i + 1, a.name))
            .collect::<Vec<_>>()
            .join(" / ")
    );
    println!("Face the Moon sparring partner at X 0, Z 3. Your injured ally is at X 1, Z 2.");
    println!("Commands: aim <yaw> <pitch> (radians), cast <1..3>, shoot <ticks>, move <x> <z> <ticks>, jump <ticks>, wait <ticks>, quit");
    for line in io::stdin().lock().lines() {
        let line = line.map_err(|e| e.to_string())?;
        let args: Vec<_> = line.split_whitespace().collect();
        if args.is_empty() {
            continue;
        }
        if args[0] == "quit" {
            break;
        }
        let parsed = (|| {
            let mut cmd = Input {
                yaw: Some(yaw),
                pitch,
                ..Default::default()
            };
            match args[0] {
                "aim" => {
                    let (y, p): (f64, f64) =
                        (number(args.get(1), "yaw")?, number(args.get(2), "pitch")?);
                    if !y.is_finite() || !p.is_finite() {
                        return Err("Expected finite angles".to_string());
                    }
                    yaw = y;
                    pitch = p;
                    cmd.yaw = Some(y);
                    cmd.pitch = p;
                }
                "cast" => {
                    let s: usize = number(args.get(1), "slot 1..3")?;
                    if !(1..=3).contains(&s) {
                        return Err("Choose slot 1..3".into());
                    }
                    cmd.cast = Some(s - 1);
                }
                "move" => {
                    cmd.movement = [number(args.get(1), "x")?, number(args.get(2), "z")?];
                    cmd.ticks = number(args.get(3), "ticks")?;
                }
                "shoot" | "jump" | "wait" => {
                    cmd.ticks = number(args.get(1), "ticks")?;
                    cmd.fire = args[0] == "shoot";
                    cmd.jump = args[0] == "jump";
                }
                _ => return Err("Unknown command".into()),
            }
            Ok(cmd)
        })();
        match parsed.and_then(|cmd| lab.command(&cmd)) {
            Ok(state) => {
                let actor = &lab.units[0];
                let enemy = &lab.units[2];
                println!("tick {} · position [{:.2}, {:.2}] · HP {:.1} + {:.1} shield · ally {:.1} · enemy {:.1} · KOs {} · cooldowns {:.1?}{}",
                    lab.tick,actor.pos[0],actor.pos[1],actor.hp,actor.shield,lab.units[1].hp,enemy.hp,enemy.deaths,actor.cds,
                    if state["accepted"]==false{" · cast unavailable"}else{""});
            }
            Err(e) => println!("{e}"),
        }
    }
    Ok(())
}

fn run() -> Result<(), String> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.first().is_some_and(|s| s == "--list") {
        for h in &Lab::load("rama")?.heroes {
            println!(
                "{}\t{}\t{}",
                h.id,
                h.name,
                h.abilities
                    .iter()
                    .map(|a| a.name.as_str())
                    .collect::<Vec<_>>()
                    .join(" / ")
            );
        }
        return Ok(());
    }
    let interactive = args.first().is_some_and(|s| s == "--play");
    let id = args
        .get(usize::from(interactive))
        .map(String::as_str)
        .unwrap_or("rama");
    let mut lab = Lab::load(id)?;
    if interactive {
        return play(&mut lab);
    }
    let mut stdout = io::BufWriter::new(io::stdout().lock());
    let emit = |v: &serde_json::Value, out: &mut io::BufWriter<_>| -> io::Result<()> {
        serde_json::to_writer(&mut *out, v)?;
        writeln!(out)?;
        out.flush()
    };
    emit(&lab.snapshot(None), &mut stdout).map_err(|e| e.to_string())?;
    for line in io::stdin().lock().lines() {
        let raw = line.map_err(|e| e.to_string())?;
        let result = serde_json::from_str::<Input>(&raw)
            .map_err(|e| e.to_string())
            .and_then(|cmd| lab.command(&cmd));
        emit(
            &result.unwrap_or_else(|err| json!({"error":err,"tick":lab.tick})),
            &mut stdout,
        )
        .map_err(|e| e.to_string())?;
    }
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
