use std::{env, error::Error, fs, io::Write, path::PathBuf};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = env::args_os().skip(1).map(PathBuf::from).collect();
    if args.len() != 3 {
        return Err("Usage: hero_export <hero.glb> <motion-library.tres> <new-output.glb>".into());
    }
    let bytes =
        yuga_rust::hero::export_visual(&fs::read(&args[0])?, &fs::read_to_string(&args[1])?)?;
    let mut output = fs::File::create_new(&args[2])?;
    if let Err(error) = output.write_all(&bytes) {
        drop(output);
        fs::remove_file(&args[2])?;
        return Err(error.into());
    }
    println!("Wrote {} bytes to {}", bytes.len(), args[2].display());
    Ok(())
}
