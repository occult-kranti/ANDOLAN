//! Compare two published Source readers on the same unmodified file.
//! Able to survey an authored text .map as a separate format.
use std::error::Error;
use std::io;
use std::path::Path;

fn invalid(message: &str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidData, message)
}

fn survey_bsp(raw: &[u8]) -> Result<(), Box<dyn Error>> {
    let limits = vformats::Limits::default();
    let bsp = vformats::bsp::parse(raw, &limits)?;
    let vertices = bsp.vertices(&limits)?;
    let faces = bsp.faces(&limits)?;
    let models = bsp.models(&limits)?;
    let displacements = bsp.displacement_infos(&limits)?;
    let displacement_vertices = bsp.displacement_verts(&limits)?;
    let displaced_faces = faces.iter().filter(|face| face.displacement >= 0);
    for face in displaced_faces.clone() {
        if face.displacement as usize >= displacements.len() {
            return Err(invalid("a face references a missing displacement").into());
        }
    }
    println!(
        "vformats: VBSP {} revision {}, {} vertices, {} faces, {} brush models",
        bsp.version(),
        bsp.map_revision(),
        vertices.len(),
        faces.len(),
        models.len()
    );
    println!(
        "{} displacement records, {} displaced face references, {} displacement vertices",
        displacements.len(),
        displaced_faces.count(),
        displacement_vertices.len()
    );
    if let Some(props) = bsp.static_props(&limits)? {
        for instance in &props.props {
            let leaf_end = usize::from(instance.first_leaf) + usize::from(instance.leaf_count);
            if usize::from(instance.model_index) >= props.models.len()
                || leaf_end > props.leaves.len()
            {
                return Err(invalid("a static prop references a missing model or leaf").into());
            }
        }
        println!(
            "sprp v{}, {:?}, {}-byte records: {} dictionary names, {} leaf indices, {} instances",
            props.version,
            props.layout,
            props.stride,
            props.models.len(),
            props.leaves.len(),
            props.props.len()
        );
    }
    match vbsp::Bsp::read(raw) {
        Ok(map) => println!(
            "vbsp: {} vertices, {} faces, {} models, {} static props",
            map.vertices.len(),
            map.faces.len(),
            map.models().count(),
            map.static_props().count()
        ),
        Err(error) => println!("vbsp compatibility result: {error}"),
    }
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let paths = std::env::args_os().skip(1).collect::<Vec<_>>();
    if paths.is_empty() {
        return Err(
            invalid("usage: yuga-map-format-probe map.bsp [other.bsp | map.map ...]").into(),
        );
    }
    for arg in paths {
        let path = Path::new(&arg);
        let raw = std::fs::read(path)?;
        println!("{} ({} bytes)", path.display(), raw.len());
        if raw.starts_with(b"VBSP") {
            survey_bsp(&raw)?;
        } else if path
            .extension()
            .and_then(|s| s.to_str())
            .is_some_and(|s| s.eq_ignore_ascii_case("map"))
        {
            let map = std::str::from_utf8(&raw)?
                .parse::<shalrath::repr::Map>()
                .map_err(|_| invalid("shalrath rejected text map"))?;
            println!("shalrath: {} entities", map.0.len());
        } else {
            return Err(invalid("expected Source 1 VBSP or a Quake-family text .map").into());
        }
    }
    Ok(())
}
