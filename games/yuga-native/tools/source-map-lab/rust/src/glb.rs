use crate::{atomic_output, JADE};
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::fs::File;
use std::io::{BufReader, Read, Write};
use std::path::Path;

fn recolour(root: &mut Value) -> Result<usize> {
    let mut changed = 0;
    let materials = root["materials"]
        .as_array_mut()
        .context("missing glTF materials")?;
    for m in materials {
        if m.pointer("/extras/yugaGround").and_then(Value::as_bool) != Some(true) {
            continue;
        }
        let pbr = m["pbrMetallicRoughness"]
            .as_object_mut()
            .context("marked material has no PBR definition")?;
        let original = pbr
            .get("baseColorFactor")
            .cloned()
            .unwrap_or(json!([1.0, 1.0, 1.0, 1.0]));
        let mut rgba = original
            .as_array()
            .context("invalid baseColorFactor")?
            .clone();
        ensure!(rgba.len() == 4, "baseColorFactor must have four channels");
        for (channel, &gain) in rgba.iter_mut().zip(JADE.iter()) {
            *channel = json!(channel.as_f64().context("base colour is not numeric")? * gain);
        }
        pbr.insert("baseColorFactor".into(), Value::Array(rgba));
        changed += 1;
    }
    ensure!(changed > 0, "no material explicitly marked as ground");
    Ok(changed)
}

pub fn write(source: &Path, output: &Path) -> Result<()> {
    let file = File::open(source)?;
    let length = file.metadata()?.len();
    let mut input = BufReader::new(file);
    let mut header = [0u8; 20];
    input.read_exact(&mut header)?;
    ensure!(
        &header[..4] == b"glTF"
            && u32::from_le_bytes(header[4..8].try_into()?) == 2
            && &header[16..] == b"JSON",
        "requires binary glTF 2.0 with a JSON first chunk"
    );
    ensure!(
        u64::from(u32::from_le_bytes(header[8..12].try_into()?)) == length,
        "invalid GLB length"
    );
    let old_len = u32::from_le_bytes(header[12..16].try_into()?) as usize;
    ensure!(
        length >= 20 + old_len as u64 && old_len % 4 == 0,
        "invalid JSON chunk"
    );
    let mut doc = vec![0u8; old_len];
    input.read_exact(&mut doc)?;
    let mut root = serde_json::from_slice(&doc)?;
    let changed = recolour(&mut root)?;
    let mut bytes = serde_json::to_vec(&root)?;
    bytes.resize(bytes.len().next_multiple_of(4), b' ');
    let total = u32::try_from(length - old_len as u64 + bytes.len() as u64)?;
    header[8..12].copy_from_slice(&total.to_le_bytes());
    header[12..16].copy_from_slice(&u32::try_from(bytes.len())?.to_le_bytes());
    atomic_output(output, |out| {
        out.write_all(&header)?;
        out.write_all(&bytes)?;
        let copied = std::io::copy(&mut input, out)?;
        ensure!(
            copied == length - 20 - old_len as u64,
            "incomplete geometry buffer copy"
        );
        Ok(())
    })?;
    println!("Tinted {changed} explicitly marked ground materials. Copied all geometry and image chunks verbatim.");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn preserves_alpha_and_wall() {
        let mut d = json!({"materials":[{"extras":{"yugaGround":true},"pbrMetallicRoughness":{"baseColorFactor":[0.5,0.5,0.5,0.7]}},{"name":"wall"}]});
        assert_eq!(recolour(&mut d).unwrap(), 1);
        assert_eq!(
            d["materials"][0]["pbrMetallicRoughness"]["baseColorFactor"],
            json!([0.0175, 0.26, 0.155, 0.7])
        );
        assert_eq!(d["materials"][1], json!({"name":"wall"}));
    }
}
