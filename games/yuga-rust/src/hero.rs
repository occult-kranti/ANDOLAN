//! Convert the native trial's text AnimationLibrary into the same hero GLB's animation channels.
//! Supports the position and quaternion track subset exported by pack_ability_motion.gd.
use gltf::binary::Glb;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap};

type Error = Box<dyn std::error::Error>;
const CLIPS: [&str; 5] = ["fire", "cast2", "cast1", "tail_sweep", "mountain_pulse"];

#[derive(Default)]
struct Track {
    bone: String,
    path: String,
    interpolation: Option<&'static str>,
    keys: Vec<f32>,
    enabled: bool,
}

#[derive(Default)]
struct Clip {
    resource_id: String,
    name: String,
    length: f32,
    release: Option<f32>,
    contact: Option<f32>,
    tracks: BTreeMap<usize, Track>,
}

fn parse_library(source: &str, visual_sha: &str) -> Result<Vec<Clip>, Error> {
    let mut clips = Vec::new();
    let mut current: Option<Clip> = None;
    let mut verified_visual = false;
    let mut bindings = BTreeMap::new();
    if source.lines().next() != Some("[gd_resource type=\"AnimationLibrary\" format=3]") {
        return Err("Expected Godot format 3 text AnimationLibrary".into());
    }
    for line in source.lines() {
        if line.starts_with("[sub_resource ") || line == "[resource]" {
            if let Some(done) = current.take() {
                clips.push(done);
            }
            if line.starts_with("[sub_resource ") {
                if !line.starts_with("[sub_resource type=\"Animation\" ") {
                    return Err("Unsupported resource inside animation library".into());
                }
                let resource_id = line
                    .strip_prefix("[sub_resource type=\"Animation\" id=\"")
                    .and_then(|s| s.strip_suffix("\"]"))
                    .ok_or("Invalid animation resource ID")?;
                current = Some(Clip {
                    resource_id: resource_id.to_owned(),
                    ..Clip::default()
                });
            }
            continue;
        }
        if let Some(entry) = line.strip_prefix("&\"") {
            let (name, id) = entry
                .trim_end_matches(',')
                .split_once("\": SubResource(\"")
                .ok_or("Invalid AnimationLibrary binding")?;
            let id = id.strip_suffix("\")").ok_or("Invalid binding ID")?;
            if bindings.insert(name.to_owned(), id.to_owned()).is_some() {
                return Err("Duplicate AnimationLibrary binding".into());
            }
            continue;
        }
        let Some((key, value)) = line.split_once(" = ") else {
            continue;
        };
        if key == "metadata/visual_source_sha256" {
            verified_visual = value.trim_matches('"') == visual_sha;
        }
        let Some(clip) = current.as_mut() else {
            continue;
        };
        match key {
            "resource_name" => clip.name = value.trim_matches('"').to_owned(),
            "length" => clip.length = value.parse()?,
            "loop_mode" if value != "0" => return Err("Ability clips must be one-shot".into()),
            "metadata/hanuman_release_phase" => clip.release = Some(value.parse()?),
            "metadata/hanuman_impact_phase" => clip.contact = Some(value.parse()?),
            _ if key.starts_with("tracks/") => {
                let (idx, field) = key[7..]
                    .split_once('/')
                    .ok_or("Missing animation track field")?;
                let track = clip.tracks.entry(idx.parse()?).or_default();
                match field {
                    "type" => {
                        track.path = match value {
                            "\"rotation_3d\"" => "rotation",
                            "\"position_3d\"" => "translation",
                            _ => return Err(format!("Unsupported track type {value}").into()),
                        }
                        .to_owned()
                    }
                    "path" => {
                        track.bone = value
                            .strip_prefix("NodePath(\"YugaHeroRig/Skeleton3D:")
                            .and_then(|s| s.strip_suffix("\")"))
                            .ok_or("Expected a track on Hanuman's skeleton")?
                            .to_owned()
                    }
                    "enabled" => track.enabled = value.parse()?,
                    "interp" => {
                        track.interpolation = Some(match value {
                            "0" => "STEP",
                            "1" => "LINEAR",
                            _ => return Err("Unsupported Godot animation interpolation".into()),
                        })
                    }
                    "keys" => {
                        let packed = value
                            .strip_prefix("PackedFloat32Array(")
                            .and_then(|text| text.strip_suffix(')'))
                            .ok_or("Invalid track keys")?;
                        track.keys = packed
                            .split(',')
                            .map(|v| v.trim().parse())
                            .collect::<Result<_, _>>()?;
                    }
                    "imported" | "loop_wrap" => (),
                    other => return Err(format!("Unsupported animation field {other}").into()),
                }
            }
            _ => (),
        }
    }
    if current.is_some() || !verified_visual {
        return Err("Incomplete library or mismatched source model SHA-256".into());
    }
    let names: BTreeSet<_> = clips.iter().map(|clip| clip.name.as_str()).collect();
    if clips.len() != CLIPS.len() || names != CLIPS.into_iter().collect() {
        return Err("Expected the five distinct Hanuman ability motions".into());
    }
    if bindings.len() != clips.len()
        || clips
            .iter()
            .any(|clip| bindings.get(&clip.name) != Some(&clip.resource_id))
    {
        return Err("AnimationLibrary bindings disagree with the named ability clips".into());
    }
    Ok(clips)
}

fn append(doc: &mut Value, field: &str, row: Value) -> Result<usize, Error> {
    let rows = doc[field]
        .as_array_mut()
        .ok_or_else(|| format!("Missing GLB {field} array"))?;
    let index = rows.len();
    rows.push(row);
    Ok(index)
}

fn accessor(
    doc: &mut Value,
    bin: &mut Vec<u8>,
    values: &[f32],
    width: usize,
) -> Result<usize, Error> {
    let offset = bin.len();
    for &value in values {
        bin.extend_from_slice(&value.to_le_bytes());
    }
    let view = append(
        doc,
        "bufferViews",
        json!({
            "buffer":0, "byteOffset":offset, "byteLength":bin.len()-offset
        }),
    )?;
    let ty = match width {
        1 => "SCALAR",
        3 => "VEC3",
        4 => "VEC4",
        _ => return Err("Unexpected accessor size".into()),
    };
    let mut info =
        json!({"bufferView":view, "componentType":5126, "count":values.len()/width, "type":ty});
    if width == 1 {
        info["min"] = json!([values.first().ok_or("Empty animation sampler")?]);
        info["max"] = json!([values.last().unwrap()]);
    }
    append(doc, "accessors", info)
}

// PlayCanvas interpolates quaternion components and normalizes the result. Godot's
// rotation tracks use shortest-path slerp. Split long arcs only, so linear consumers
// reproduce the authoring curve even between the original Blender keys.
fn refine_rotation_arcs(seconds: &[f32], values: &[f32]) -> (Vec<f32>, Vec<f32>) {
    const MAX_HALF_ANGLE: f64 = 0.06;
    let mut times = vec![seconds[0]];
    let mut quats = values[..4].to_vec();
    for (index, span) in seconds.windows(2).enumerate() {
        let a = &values[index * 4..index * 4 + 4];
        let b = &values[index * 4 + 4..index * 4 + 8];
        let dot: f64 = a
            .iter()
            .zip(b)
            .map(|(&x, &y)| f64::from(x) * f64::from(y))
            .sum();
        let angle = dot.abs().min(1.0).acos();
        let steps = ((angle / MAX_HALF_ANGLE).ceil() as usize).max(1);
        for step in 1..steps {
            let t = step as f64 / steps as f64;
            times.push(span[0] + (span[1] - span[0]) * t as f32);
            let weight_a = ((1.0 - t) * angle).sin() / angle.sin();
            let weight_b = (t * angle).sin() / angle.sin() * dot.signum();
            for i in 0..4 {
                quats.push((weight_a * f64::from(a[i]) + weight_b * f64::from(b[i])) as f32);
            }
        }
        times.push(span[1]);
        quats.extend_from_slice(b);
    }
    (times, quats)
}

fn replace_clip(
    doc: &mut Value,
    blob: &mut Vec<u8>,
    bones: &HashMap<String, usize>,
    clip: Clip,
) -> Result<(), Error> {
    let release = clip.release.ok_or("Missing motion release phase")?;
    let contact = clip.contact;
    if !clip.length.is_finite()
        || clip.length <= 0.0
        || !(0.0..=1.0).contains(&release)
        || contact.is_some_and(|v| !(release..=1.0).contains(&v))
    {
        return Err("Invalid clip length or markers".into());
    }
    let needs_contact = matches!(clip.name.as_str(), "cast1" | "mountain_pulse");
    if needs_contact != contact.is_some() || contact.is_some_and(|v| v <= release) {
        return Err("Ability contact marker missing, unexpected or at release".into());
    }
    let motions = doc["animations"]
        .as_array()
        .ok_or("No embedded animations")?;
    let index = motions
        .iter()
        .position(|v| v["name"].as_str() == Some(&clip.name))
        .ok_or_else(|| format!("Missing GLB clip {}", clip.name))?;
    let mut channels = Vec::new();
    let mut samplers = Vec::new();
    let mut latest_key = 0.0_f32;
    let mut times: HashMap<Vec<u32>, usize> = HashMap::new();
    let mut targets = BTreeSet::new();
    for track in clip.tracks.into_values().filter(|t| t.enabled) {
        let node = *bones
            .get(&track.bone)
            .ok_or_else(|| format!("Missing joint {}", track.bone))?;
        if !targets.insert((node, track.path.clone())) {
            return Err("Duplicate bone/property channel in one clip".into());
        }
        let width = match track.path.as_str() {
            "rotation" => 4,
            "translation" => 3,
            _ => return Err("Missing track type".into()),
        };
        let stride = width + 2;
        if track.keys.is_empty()
            || track.keys.len() % stride != 0
            || track.keys.iter().any(|x| !x.is_finite())
        {
            return Err("Invalid key count or nonfinite channel".into());
        }
        let mut seconds = Vec::new();
        let mut values = Vec::new();
        for key in track.keys.chunks_exact(stride) {
            if key[1] != 1.0
                || key[0] < 0.0
                || key[0] > clip.length + 1e-5
                || seconds.last().is_some_and(|prev| key[0] <= *prev)
            {
                return Err("Invalid key time, ordering or easing".into());
            }
            seconds.push(key[0]);
            if width == 4 {
                let norm = key[2..].iter().map(|x| x * x).sum::<f32>().sqrt();
                if (norm - 1.0).abs() > 0.002 {
                    return Err("Non-unit animation quaternion".into());
                }
                values.extend(key[2..].iter().map(|x| x / norm));
            } else {
                values.extend_from_slice(&key[2..]);
            }
        }
        if width == 4 && track.interpolation == Some("LINEAR") {
            (seconds, values) = refine_rotation_arcs(&seconds, &values);
        }
        latest_key = latest_key.max(*seconds.last().unwrap());
        let key: Vec<u32> = seconds.iter().map(|x| x.to_bits()).collect();
        let input = if let Some(&idx) = times.get(&key) {
            idx
        } else {
            let idx = accessor(doc, blob, &seconds, 1)?;
            times.insert(key, idx);
            idx
        };
        let output = accessor(doc, blob, &values, width)?;
        channels.push(json!({"sampler":samplers.len(),"target":{"node":node,"path":track.path}}));
        samplers.push(json!({"input":input,"output":output,"interpolation":track.interpolation.ok_or("Missing interpolation")?}));
    }
    if channels.is_empty() || (latest_key - clip.length).abs() > 1e-5 {
        return Err("Animation samples do not span the declared action duration".into());
    }
    let mut meta = json!({"source":"hanuman-ability-motion.tres", "duration_s":clip.length,"release_phase":release});
    if let Some(v) = contact {
        meta["impact_phase"] = json!(v);
    }
    let motion = &mut doc["animations"][index];
    motion["samplers"] = json!(samplers);
    motion["channels"] = json!(channels);
    motion["extras"]["yuga"] = meta;
    Ok(())
}

/// Preserve the complete visual asset and six other animations, replacing the five action clips.
/// Geometry data, textures and the skin keep their existing byte ranges.
pub fn export_visual(base: &[u8], motion: &str) -> Result<Vec<u8>, Error> {
    let clips = parse_library(motion, &format!("{:x}", Sha256::digest(base)))?;
    let glb = Glb::from_slice(base)?;
    let mut doc: Value = serde_json::from_slice(&glb.json)?;
    let mut blob = glb.bin.ok_or("Expected embedded GLB buffer")?.into_owned();
    let buffers = doc["buffers"].as_array().ok_or("Missing GLB buffers")?;
    if buffers.len() != 1
        || buffers[0].get("uri").is_some()
        || buffers[0]["byteLength"]
            .as_u64()
            .is_none_or(|len| len > blob.len() as u64)
    {
        return Err("Expected one embedded visual buffer".into());
    }
    // Each animation accessor starts on the glTF-required 4-byte boundary.
    while blob.len() % 4 != 0 {
        blob.push(0);
    }
    let skins = doc["skins"].as_array().ok_or("Expected a skinned hero")?;
    if skins.len() != 1 {
        return Err("Expected a single hero skin".into());
    }
    let joints = skins[0]["joints"].as_array().ok_or("Missing joints")?;
    let mut bones = HashMap::new();
    for joint in joints {
        let id = joint.as_u64().ok_or("Invalid joint index")? as usize;
        let name = doc["nodes"][id]["name"]
            .as_str()
            .ok_or("Missing joint name")?;
        if bones.insert(name.to_owned(), id).is_some() {
            return Err("Ambiguous joint name".into());
        }
    }
    for clip in clips {
        replace_clip(&mut doc, &mut blob, &bones, clip)?;
    }
    doc["buffers"][0]["byteLength"] = json!(blob.len());
    let final_glb = Glb {
        header: glb.header,
        json: serde_json::to_vec(&doc)?.into(),
        bin: Some(blob.into()),
    }
    .to_vec()?;
    gltf::Gltf::from_slice(&final_glb)?;
    Ok(final_glb)
}

#[cfg(test)]
mod tests {
    use super::*;
    const MOTION: &str =
        include_str!("../../yuga-native/assets/heroes/hanuman/hanuman-ability-motion.tres");

    #[test]
    fn rejects_wrong_base() {
        assert!(export_visual(b"wrong rig", MOTION).is_err());
    }

    #[test]
    fn steep_rotation_refinement_retains_original_times_and_shortest_arc() {
        let s = 0.5_f32.sqrt();
        let (times, values) = refine_rotation_arcs(&[0.0, 1.0], &[0., 0., 0., 1., 0., 0., -s, -s]);
        assert!(times.len() > 2);
        assert_eq!((times[0], *times.last().unwrap()), (0., 1.));
        for (&t, q) in times.iter().zip(values.chunks_exact(4)) {
            let theta = t * std::f32::consts::FRAC_PI_4;
            // The two antipodal representations describe the same orientation.
            let agreement = (q[2] * theta.sin() + q[3] * theta.cos()).abs();
            assert!((agreement - 1.).abs() < 1e-5);
        }
    }

    #[test]
    fn rejects_unhandled_interpolation() {
        let invalid = MOTION.replacen("/interp = 1", "/interp = 3", 1);
        assert!(parse_library(
            &invalid,
            "9de9e032d55685dffd51734bef98c241024283c5d23767646b5c68ca782dec7e"
        )
        .is_err());
    }
}
