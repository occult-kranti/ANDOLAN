//! Bake only the five authored release / contact markers into the simulation.
use std::{collections::BTreeMap, env, fs, path::PathBuf};

const SOURCE: &str = "../yuga-native/assets/heroes/hanuman/hanuman-ability-motion.tres";

fn main() {
    println!("cargo:rerun-if-changed={SOURCE}");
    let text = fs::read_to_string(SOURCE).expect("read the Godot ability animation library");
    let mut clips = BTreeMap::<String, (Option<f32>, Option<f32>)>::new();
    let mut clip = None;
    for line in text.lines() {
        if let Some(value) = line.strip_prefix("resource_name = ") {
            let name = value.trim_matches('"').to_owned();
            assert!(clips.insert(name.clone(), (None, None)).is_none());
            clip = Some(name);
        } else if let Some((key, value)) = line.split_once(" = ") {
            if matches!(
                key,
                "metadata/hanuman_release_phase" | "metadata/hanuman_impact_phase"
            ) {
                let markers = clips.get_mut(clip.as_ref().expect("named motion")).unwrap();
                let slot = if key.ends_with("release_phase") {
                    &mut markers.0
                } else {
                    &mut markers.1
                };
                let phase = value.parse::<f32>().expect("numeric motion marker");
                assert!(phase > 0. && phase < 1. && slot.replace(phase).is_none());
            }
        }
    }
    let mut generated = String::from("const MOTION_MARKERS: &[(&str, f32, Option<f32>)] = &[\n");
    for (name, (release, impact)) in clips {
        let release = release.expect("every ability clip needs a release mark");
        assert!(impact.is_none_or(|value| value > release));
        generated += &format!("    ({name:?}, {release:?}, {impact:?}),\n");
    }
    generated += "];\n";
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").unwrap()).join("motion_markers.rs"),
        generated,
    )
    .expect("write ability motion markers");
}
