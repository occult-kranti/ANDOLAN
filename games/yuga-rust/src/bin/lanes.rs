//! Inspect Confluence formations or run a persistent match without a renderer.
use yuga_rust::{
    army::{isolated_wave, Army},
    world::World,
};
fn main() -> Result<(), String> {
    const USAGE: &str =
        "lanes [wave-number [ticks-since-spawn]] | lanes --match ticks   (20 ticks/s)";
    let args: Vec<_> = std::env::args().skip(1).collect();
    if matches!(args.as_slice(),[v] if v=="--help" || v=="-h") {
        println!("{USAGE}");
        return Ok(());
    }
    let number = |s: &str| s.parse::<u32>().map_err(|_| USAGE.to_owned());
    let state = match args.as_slice() {
        [] => isolated_wave(1, 0)?,
        [wave] => isolated_wave(number(wave)?, 0)?,
        [mode, n] if mode == "--match" => {
            let world = World::load()?;
            let mut army = Army::load()?;
            for _ in 0..number(n)? {
                army.step(&world);
                if army.finished() {
                    break;
                }
            }
            army.snapshot()
        }
        [wave, n] => isolated_wave(number(wave)?, number(n)?)?,
        _ => return Err(USAGE.into()),
    };
    println!("{state}");
    Ok(())
}
