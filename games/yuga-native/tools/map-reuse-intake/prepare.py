#!/usr/bin/env python3
"""Reuse existing CC0 map and material sources in a fresh isolated Godot project."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PROJECT = ROOT / 'games/yuga-native'
SOURCE = PROJECT / 'assets/environment/lanka_courtyard.glb'
EXPECTED = '1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bad_uri_fixture():
    document = json.dumps({'asset': {'version': '2.0'}, 'buffers': [{'uri': 'https://invalid.example/map.bin', 'byteLength': 4}]}).encode()
    document += b' ' * (-len(document) % 4)
    return struct.pack('<IIIII', 0x46546C67, 2, 28 + len(document) + 4, len(document), 0x4E4F534A) + document + struct.pack('<II', 4, 0x004E4942) + b'\0' * 4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        raise ValueError('fresh outside-checkout project required')
    if sha(SOURCE) != EXPECTED:
        raise ValueError('existing canonical map source changed')
    metadata = json.loads((PROJECT / 'assets/environment/lanka_courtyard.metadata.json').read_text())
    if not metadata['license'].startswith('CC0-1.0') or metadata['coordinate_system'] != 'metres; GLB Y-up; XZ ground, y=0 walking surface':
        raise ValueError('approved license/unit contract changed')
    raw = SOURCE.read_bytes()
    document = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
    element = next(node for node in document['nodes'] if node.get('name') == 'COL_BEVEL_Warm_carved_sandstone')
    if set(element) != {'name', 'mesh'}:
        raise ValueError('source element transform contract changed')
    primitive = document['meshes'][element['mesh']]['primitives'][0]
    accessor = document['accessors'][primitive['attributes']['POSITION']]
    output.mkdir(parents=True)
    (output / 'assets').mkdir()
    (output / 'assets/courtyard.glb').symlink_to(SOURCE)
    (output / 'art').mkdir()
    (output / 'art/source-kits').symlink_to(PROJECT / 'art/source-kits', target_is_directory=True)
    rows = [{'source': str(SOURCE.relative_to(ROOT)), 'sha256': EXPECTED, 'role': 'readonly source symlink; original CC0 map geometry'}]
    for name in ['project.godot', 'map_loader.gd', 'test_intake.gd', 'preview.gd']:
        source = HERE / name
        shutil.copyfile(source, output / name)
        rows.append({'source': str(source.relative_to(ROOT)), 'sha256': sha(source), 'role': 'bounded integration harness'})
    material_source = PROJECT / 'tools/wind-court-pilot/pbr_material.gd'
    shutil.copyfile(material_source, output / 'pbr_material.gd')
    rows.append({'source': str(material_source.relative_to(ROOT)), 'sha256': sha(material_source), 'role': 'exact existing verified CC0 material adapter'})
    (output / 'bad-uri.glb').write_bytes(bad_uri_fixture())
    (output / 'source-manifest.json').write_text(json.dumps({'schema': 1, 'files': rows, 'source_metadata': metadata, 'element_accessor_bounds': {'min': accessor['min'], 'max': accessor['max']}, 'scope': 'isolated source intake; no canonical mutation or runtime promotion'}, indent=2) + '\n')
    print(json.dumps({'project': str(output), 'map_bytes_copied': 0, 'source_sha256': EXPECTED}))


if __name__ == '__main__':
    main()
