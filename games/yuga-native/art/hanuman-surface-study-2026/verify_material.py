"""Verify the separate candidate changes one material and appends texture bytes only."""
import argparse
import copy
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'hanuman-hero-finish/tools'))
from surfaces import read_gltf  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=HERE.parent / 'hanuman-facial-refinement-2026/hanuman-face-candidate.glb')
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    baseline, original = read_gltf(args.source)
    candidate, revised = read_gltf(args.candidate)
    unchanged = ['accessors', 'meshes', 'skins', 'nodes', 'animations', 'scenes', 'samplers']
    for name in unchanged:
        assert baseline.get(name) == candidate.get(name), f'{name} changed'
    assert revised[:len(original)] == original, 'original binary bytes changed'
    assert baseline['bufferViews'] == candidate['bufferViews'][:len(baseline['bufferViews'])]
    assert baseline['images'] == candidate['images'][:len(baseline['images'])]
    assert baseline['textures'] == candidate['textures'][:len(baseline['textures'])]
    assert len(candidate['images']) == len(baseline['images']) + 3
    assert len(candidate['textures']) == len(baseline['textures']) + 3
    changed = [i for i, (a, b) in enumerate(zip(baseline['materials'], candidate['materials'])) if a != b]
    assert len(changed) == 1
    before, after = baseline['materials'][changed[0]], candidate['materials'][changed[0]]
    assert before['name'] == after['name'] == 'Vanara · painted copper anatomy'
    assert before['normalTexture']['scale'] == after['normalTexture']['scale']
    assert before['normalTexture']['index'] != after['normalTexture']['index']
    assert before['pbrMetallicRoughness']['metallicRoughnessTexture']['index'] != after['pbrMetallicRoughness']['metallicRoughnessTexture']['index']
    assert 'baseColorTexture' not in before['pbrMetallicRoughness'] and 'baseColorTexture' in after['pbrMetallicRoughness']
    remainder_before, remainder_after = copy.deepcopy(before), copy.deepcopy(after)
    del remainder_after['pbrMetallicRoughness']['baseColorTexture']
    for remainder in (remainder_before, remainder_after):
        del remainder['normalTexture']['index']
        del remainder['pbrMetallicRoughness']['metallicRoughnessTexture']['index']
    assert remainder_before == remainder_after, 'unrelated body material property changed'
    indices = [after['normalTexture']['index'],
               after['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
               after['pbrMetallicRoughness']['baseColorTexture']['index']]
    assert len(set(indices)) == 3 and all(i >= len(baseline['textures']) for i in indices)

    def pixels(index):
        texture = candidate['textures'][index]
        image = candidate['images'][texture['source']]
        assert image['mimeType'] == 'image/png'
        view = candidate['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        with Image.open(io.BytesIO(revised[start:start + view['byteLength']])) as decoded:
            assert decoded.size == (1024, 1024)
            return np.asarray(decoded.convert('RGB'), dtype=np.uint8)

    normal, packed, color = [pixels(i) for i in indices]
    vector = normal.astype(np.float32) / 127.5 - 1.
    lengths = np.linalg.norm(vector, axis=-1)
    assert np.isfinite(lengths).all() and np.max(np.abs(lengths - 1.)) < .02
    assert (vector[..., 2] > 0).all(), 'normal map contains a reversed blue channel'
    assert np.array_equal(color[..., 0], color[..., 1]) and np.array_equal(color[..., 1], color[..., 2])
    result = {
        'result': 'pass', 'source_sha256': sha(args.source), 'candidate_sha256': sha(args.candidate),
        'unchanged_tables': unchanged, 'original_binary_bytes_preserved': len(original),
        'changed_material': after['name'], 'added_images': 3, 'added_textures': 3,
        'changed_slots': ['normalTexture', 'metallicRoughnessTexture', 'baseColorTexture'],
        'normal_scale': after['normalTexture']['scale'],
        'normal_length_range': [float(lengths.min()), float(lengths.max())],
        'normal_blue_positive_fraction': float(np.mean(vector[..., 2] > 0)),
        'roughness_green_range': [int(packed[..., 1].min()), int(packed[..., 1].max())],
        'basecolor_range': [int(color.min()), int(color.max())],
        'limitations': 'Structural equality only: visual quality, UV seams, real-game import and physical GPU memory are not proven.'
    }
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
