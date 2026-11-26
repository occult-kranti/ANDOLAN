mod bsp;
mod glb;

use anyhow::{bail, ensure, Context, Result};
use sha2::{Digest, Sha256};
use std::ffi::OsString;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::Path;

// Linear RGB gain applied to base colour, leaving alpha untouched.
const JADE: [f64; 3] = [0.035, 0.52, 0.31];

fn atomic_output(
    path: &Path,
    write: impl FnOnce(&mut BufWriter<&mut File>) -> Result<()>,
) -> Result<()> {
    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    fs::create_dir_all(parent)?;
    let mut tmp = tempfile::NamedTempFile::new_in(parent)?;
    {
        let mut writer = BufWriter::new(tmp.as_file_mut());
        write(&mut writer)?;
        writer.flush()?;
    }
    tmp.persist(path).context("installing complete output")?;
    Ok(())
}

fn distinct(input: &Path, output: &Path) -> Result<()> {
    if output.exists() {
        ensure!(
            input.canonicalize()? != output.canonicalize()?,
            "use a separate output path"
        );
    }
    Ok(())
}

fn hash(data: &[u8]) -> String {
    format!("{:x}", Sha256::digest(data))
}

fn main() -> Result<()> {
    let a: Vec<OsString> = std::env::args_os().skip(1).collect();
    match (a.first().and_then(|s| s.to_str()), a.len()) {
        (Some("bsp"), 6) => {
            let source=Path::new(&a[1]); let target=Path::new(&a[5]); distinct(source,target)?;
            let bytes=fs::read(source).context("opening original BSP")?;
            ensure!(hash(&bytes)==a[2].to_string_lossy().to_ascii_lowercase(),"BSP fingerprint differs from the authoring input");
            let faces:Vec<usize>=serde_json::from_slice(&fs::read(&a[3])?)?;
            bsp::write(&bytes, &faces, Path::new(&a[4]), target)
        }
        (Some("glb"),3) => {
            let source=Path::new(&a[1]);let target=Path::new(&a[2]);distinct(source,target)?;
            glb::write(source,target)
        }
        (Some("nav"),5) => {
            let source=Path::new(&a[1]);let target=Path::new(&a[4]);distinct(source,target)?;
            let mut nav=fs::read(source)?;
            ensure!(nav.len()>16 && &nav[0..4]==b"\xCE\xFA\xED\xFE" && u32::from_le_bytes(nav[4..8].try_into()?)==16,"expected Source NAV v16");
            let original=u32::try_from(fs::metadata(&a[2])?.len())?;
            let variant=u32::try_from(fs::metadata(&a[3])?.len())?;
            ensure!(u32::from_le_bytes(nav[12..16].try_into()?)==original, "NAV belongs to another BSP size");
            nav[12..16].copy_from_slice(&variant.to_le_bytes());
            atomic_output(target, |w| Ok(w.write_all(&nav)?))?;
            println!("Updated the NAV v16 BSP-size field from {original} to {variant}.");
            Ok(())
        }
        _ => bail!("usage:\n  yuga-map-finish bsp ORIGINAL.bsp EXPECTED_SHA256 floor-faces.json MATERIAL_OVERLAY_DIRECTORY OUT.bsp\n  yuga-map-finish glb BASELINE.glb JADE.glb\n  yuga-map-finish nav ORIGINAL.nav ORIGINAL.bsp JADE.bsp OUT.nav"),
    }
}
