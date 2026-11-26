//! Reassemble a Source 1 level without moving any pre-existing game-lump data.
//! The public vbsp reader supplies the header types. Static props remain opaque.
use crate::{atomic_output, hash};
use anyhow::{ensure, Context, Result};
use binrw::BinRead;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::{Cursor, Write};
use std::ops::Range;
use std::path::Path;
use vbsp::{BspVersion, Header, LumpEntry};
use zip::{write::FileOptions, CompressionMethod, ZipArchive, ZipWriter};

const TEXDATA: usize = 2;
const TEXINFO: usize = 6;
const FACES: usize = 7;
const PAK: usize = 40;
const STRINGS: usize = 43;
const OFFSETS: usize = 44;
const HDR_FACES: usize = 58;
const FACE_BYTES: usize = 56;
const INFO_BYTES: usize = 72;
const TEXDATA_BYTES: usize = 32;

fn range(e: LumpEntry, size: usize) -> Result<Range<usize>> {
    let start = e.offset as usize;
    let end = start
        .checked_add(e.length as usize)
        .context("lump exceeds address space")?;
    ensure!(end <= size, "lump extends beyond the input");
    Ok(start..end)
}
fn nonnegative(slice: &[u8]) -> Result<usize> {
    Ok(usize::try_from(i32::from_le_bytes(slice.try_into()?))?)
}
fn named_material(table: &[u8], strings: &[u8], record: &[u8]) -> Result<String> {
    let index = nonnegative(&record[12..16])?
        .checked_mul(4)
        .context("bad material name index")?;
    let off = nonnegative(
        table
            .get(index..index + 4)
            .context("bad string table index")?,
    )?;
    let tail = strings.get(off..).context("string beyond texture data")?;
    let end = tail
        .iter()
        .position(|x| *x == 0)
        .context("unterminated material name")?;
    let name = std::str::from_utf8(&tail[..end])?
        .replace('\\', "/")
        .to_ascii_lowercase();
    ensure!(
        !name.is_empty()
            && !name.starts_with('/')
            && !name
                .split('/')
                .any(|s| s.is_empty() || s == "." || s == "..")
            && !name.chars().any(char::is_control),
        "invalid texture name"
    );
    Ok(name)
}

fn new_pack(original: &[u8], overlays: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>> {
    let mut pak =
        ZipArchive::new(Cursor::new(original)).context("unable to open original map pak")?;
    for name in overlays.keys() {
        ensure!(
            !pak.file_names()
                .any(|existing| existing.eq_ignore_ascii_case(name)),
            "material namespace already present: {name}"
        );
    }
    // Raw copy preserves the compressed contents and CRC of each original member.
    // CS:GO reads the map's pak through its lump bounds and simple stored entries.
    let mut out = ZipWriter::new(Cursor::new(Vec::with_capacity(original.len())));
    for i in 0..pak.len() {
        out.raw_copy_file(pak.by_index_raw(i)?)?;
    }
    let options = FileOptions::default().compression_method(CompressionMethod::Stored);
    for (name, data) in overlays {
        out.start_file(name, options)?;
        out.write_all(data)?;
    }
    Ok(out.finish()?.into_inner())
}

pub fn write(source: &[u8], faces: &[usize], overlay: &Path, dest: &Path) -> Result<()> {
    let mut r = Cursor::new(source);
    let header = Header::read_le(&mut r).context("invalid Valve BSP header")?;
    ensure!(
        header.version == BspVersion::Version21,
        "this validated adapter requires CS:GO Source 1 BSP v21"
    );
    let mut entries = [LumpEntry::default(); 64];
    for entry in &mut entries {
        *entry = LumpEntry::read_le(&mut r)?;
        range(*entry, source.len())?;
    }
    let get = |id: usize| -> Result<&[u8]> {
        ensure!(
            entries[id].ident == 0,
            "compressed editable lump {id} requires another adapter"
        );
        Ok(&source[range(entries[id], source.len())?])
    };
    let mut infos = get(TEXINFO)?.to_vec();
    let mut texdata = get(TEXDATA)?.to_vec();
    let mut names = get(STRINGS)?.to_vec();
    let mut offsets = get(OFFSETS)?.to_vec();
    ensure!(
        infos.len() % INFO_BYTES == 0
            && texdata.len() % TEXDATA_BYTES == 0
            && offsets.len() % 4 == 0,
        "unknown texture record versions"
    );
    let mut regular = get(FACES)?.to_vec();
    let mut hdr = get(HDR_FACES)?.to_vec();
    ensure!(
        !regular.is_empty()
            && regular.len() % FACE_BYTES == 0
            && (hdr.is_empty() || hdr.len() == regular.len()),
        "unsupported LDR/HDR face layout"
    );
    ensure!(
        !faces.is_empty()
            && faces.windows(2).all(|w| w[0] < w[1])
            && faces[faces.len() - 1] < regular.len() / FACE_BYTES,
        "face indices must be sorted, unique and inside the source face table"
    );

    let bake: Value = serde_json::from_slice(&fs::read(overlay.join("bake.json"))?)?;
    ensure!(
        bake["source_bsp_sha256"] == hash(source),
        "material bake is for a different source map"
    );
    let tex_count = texdata.len() / TEXDATA_BYTES;
    let info_count = infos.len() / INFO_BYTES;
    let mut old_to_new_info = BTreeMap::new();
    let mut old_to_new_data = BTreeMap::new();
    let mut new_members = BTreeMap::new();
    let mut marked_info = BTreeSet::new();
    for &index in faces {
        let off = index * FACE_BYTES + 10;
        for lump in [&regular, &hdr].into_iter().filter(|l| !l.is_empty()) {
            let id = usize::try_from(i16::from_le_bytes(lump[off..off + 2].try_into()?))?;
            ensure!(id < info_count, "face {index} has unknown texinfo {id}");
            marked_info.insert(id);
        }
    }
    for old in marked_info {
        let mut info = infos[old * INFO_BYTES..(old + 1) * INFO_BYTES].to_vec();
        let id = nonnegative(&info[68..72])?;
        ensure!(id < tex_count, "unknown original texdata");
        let new_id = if let Some(&value) = old_to_new_data.get(&id) {
            value
        } else {
            let mut data = texdata[id * TEXDATA_BYTES..(id + 1) * TEXDATA_BYTES].to_vec();
            let original = named_material(&offsets, &names, &data)?;
            let alias = format!("yuga_dustlab/jade_{id}");
            let key = format!("materials/{alias}.vmt");
            let mapping = bake["materials"]
                .as_array()
                .context("bake material list missing")?
                .iter()
                .find(|row| row["id"].as_u64() == Some(id as u64))
                .context("missing ground material bake")?;
            ensure!(
                mapping["source"] == original && mapping["output"] == key,
                "material table does not match original texdata {id}"
            );
            let body = fs::read(overlay.join(&key))?;
            let text = std::str::from_utf8(&body)?;
            ensure!(
                text.contains(&format!("materials/{original}.vmt")),
                "patch loses original material"
            );
            new_members.insert(key, body);
            let name_id = i32::try_from(offsets.len() / 4)?;
            offsets.extend_from_slice(&i32::try_from(names.len())?.to_le_bytes());
            names.extend_from_slice(alias.as_bytes());
            names.push(0);
            data[12..16].copy_from_slice(&name_id.to_le_bytes());
            let new_id = i32::try_from(texdata.len() / TEXDATA_BYTES)?;
            texdata.extend_from_slice(&data);
            old_to_new_data.insert(id, new_id);
            new_id
        };
        info[68..72].copy_from_slice(&new_id.to_le_bytes());
        let new_info = i16::try_from(infos.len() / INFO_BYTES)
            .context("too many texinfo records for a dface")?;
        infos.extend_from_slice(&info);
        old_to_new_info.insert(old, new_info);
    }
    for &id in faces {
        let at = id * FACE_BYTES + 10;
        for lump in [&mut regular, &mut hdr]
            .into_iter()
            .filter(|l| !l.is_empty())
        {
            let old = usize::try_from(i16::from_le_bytes(lump[at..at + 2].try_into()?))?;
            lump[at..at + 2].copy_from_slice(&old_to_new_info[&old].to_le_bytes());
        }
    }
    let textures = bake["textures"]
        .as_array()
        .context("bake texture list missing")?;
    for image in textures {
        let key = image["output"].as_str().context("unlabelled VTF")?;
        let stem = key
            .strip_prefix("materials/yuga_dustlab/tex_")
            .and_then(|s| s.strip_suffix(".vtf"))
            .context("invalid generated texture path")?;
        ensure!(
            stem.len() == 16 && stem.bytes().all(|b| b.is_ascii_hexdigit()),
            "invalid generated texture name"
        );
        let body = fs::read(overlay.join(key))?;
        ensure!(
            hash(&body) == image["sha256"] && body.starts_with(b"VTF\0"),
            "incorrect baked VTF {key}"
        );
        ensure!(
            new_members.insert(key.into(), body).is_none(),
            "duplicate generated VTF"
        );
    }
    let pak = new_pack(get(PAK)?, &new_members)?;
    let mut updates = BTreeMap::from([
        (TEXDATA, texdata),
        (TEXINFO, infos),
        (FACES, regular),
        (STRINGS, names),
        (OFFSETS, offsets),
    ]);
    if !hdr.is_empty() {
        updates.insert(HDR_FACES, hdr);
    }
    let original_pak = range(entries[PAK], source.len())?;
    // Retain every immutable lump at its original absolute address, including sprp/dprp.
    // Reuse the old trailing pak slot when it is the last structured region.
    let tail_pak = entries.iter().enumerate().all(|(id, e)| {
        id == PAK
            || e.length == 0
            || u64::from(e.offset) + u64::from(e.length) <= original_pak.start as u64
    });
    let prefix = if tail_pak {
        original_pak.start
    } else {
        source.len()
    };
    let mut data = source[..prefix].to_vec();
    for (id, buf) in updates.into_iter().chain(std::iter::once((PAK, pak))) {
        data.resize(data.len().next_multiple_of(4), 0);
        let offset = i32::try_from(data.len())?;
        let len = i32::try_from(buf.len())?;
        let row = 8 + id * 16;
        data[row..row + 4].copy_from_slice(&offset.to_le_bytes());
        data[row + 4..row + 8].copy_from_slice(&len.to_le_bytes());
        data.extend_from_slice(&buf);
    }
    data.resize(data.len().next_multiple_of(4), 0);
    atomic_output(dest, |out| Ok(out.write_all(&data)?))?;
    println!("Reassembled {} bytes, {} floor faces, {} private texinfos, {} private VMTs and {} tinted albedos. Unmodified game lumps retain absolute offsets.",data.len(),faces.len(),old_to_new_info.len(),old_to_new_data.len(),textures.len());
    Ok(())
}
