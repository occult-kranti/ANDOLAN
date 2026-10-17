"""Independent read-only identity and pixel measurements for the archived LOD take."""
from pathlib import Path
import hashlib
import json
import math
import struct
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[4]
ARCHIVE = HERE.parents[1] / 'lod/native-capture-r1'


def pin(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def pixels(path):
    with Image.open(path) as image:
        assert image.size == (1280, 960)
        return np.asarray(image.convert('RGB'))


def source_geometry(path):
    blob = path.read_bytes()
    length = struct.unpack_from('<I', blob, 12)[0]
    gltf = json.loads(blob[20:20 + length])
    return {node['name']: sum(gltf['accessors'][primitive['indices']]['count'] // 3
                             for primitive in gltf['meshes'][node['mesh']]['primitives'])
            for node in gltf['nodes'] if 'mesh' in node}


report_path = ARCHIVE / 'lod-capture.json'
report = json.loads(report_path.read_text())
assert report['complete'] and report['source_unchanged'] and not report['failure']
assert len(report['pairs']) == 6 and len(report['frames']) == 30
assert report['source_sha256'] == report['source_after_sha256']
verified_sources = 0
for source, expected in report['source_sha256'].items():
    assert pin(NATIVE / source.removeprefix('res://'))['sha256'] == expected, source
    verified_sources += 1
for source, receipt in report['imports'].items():
    assert receipt['fresh']
    for key, digest_key in [('metadata', 'metadata_sha256'), ('imported', 'sha256'), ('stamp', 'stamp_sha256')]:
        assert pin(NATIVE / receipt[key].removeprefix('res://'))['sha256'] == receipt[digest_key], source
for source, expected in report['material_texture_pins'].items():
    assert pin(NATIVE / source.removeprefix('res://'))['sha256'] == expected, source

out = {'identity_passed': True, 'capture_report': pin(report_path),
       'verified_runtime_sources': verified_sources, 'verified_imports': len(report['imports']),
       'material_texture_pins': len(report['material_texture_pins']), 'source_geometry': {},
       'pairs': [], 'frames': [], 'glint_measurement': {}, 'supporting_files': {}}
for name in ['rama-hero.glb', 'rama-hero-mid.glb', 'rama-hero-far.glb']:
    path = NATIVE / 'assets/heroes' / name
    geometry = source_geometry(path)
    out['source_geometry'][name] = {'file': pin(path), 'triangles_by_mesh': geometry,
                                    'total_triangles': sum(geometry.values())}
for pair in report['pairs']:
    ref, selected = pair['reference'], pair['candidate']
    assert ref['camera'] == selected['camera'] and ref['state_sha256'] == selected['state_sha256']
    assert selected['lod']['live_rigs'] == 1 and selected['lod']['live_bones'] == 164
    assert selected['lod']['level'] == pair['selected_level']
    images = []
    decoded = []
    for shot in [ref, selected]:
        path = ARCHIVE / shot['file']
        item = pin(path)
        assert item['sha256'] == shot['sha256']
        images.append({'file': shot['file'], **item})
        decoded.append(pixels(path))
    bounds = ref['camera']['rest_aabb_pixels']
    x0, y0 = max(0, math.floor(bounds[0][0])), max(0, math.floor(bounds[0][1]))
    x1, y1 = min(1280, math.ceil(bounds[1][0])), min(960, math.ceil(bounds[1][1]))
    delta = np.abs(decoded[0][y0:y1, x0:x1].astype(np.int16) - decoded[1][y0:y1, x0:x1].astype(np.int16))
    out['pairs'].append({'pose': pair['pose'], 'target_hero_pixels': pair['target_hero_pixels'],
                         'selected_level': pair['selected_level'], 'images': images,
                         'rest_aabb_roi_xyxy': [x0, y0, x1, y1],
                         'roi_mean_abs_channel_delta': float(delta.mean()),
                         'roi_pixels_any_channel_delta_gt32': int((delta.max(axis=2) > 32).sum()),
                         'same_frozen_state_sha256': ref['state_sha256'],
                         'reference_draw_primitives': ref['rendered_primitives'],
                         'selected_draw_primitives': selected['rendered_primitives'],
                         'reference_draw_calls': ref['draw_calls'], 'selected_draw_calls': selected['draw_calls']})
for frame in report['frames']:
    shot = frame['image']; path = ARCHIVE / shot['file']; identity = pin(path)
    assert identity['sha256'] == shot['sha256']
    assert shot['lod']['live_rigs'] == 1 and shot['lod']['live_bones'] == 164
    assert shot['tree_paused'] and (frame['index'] == 0 or frame['physics_tick_delta'] == 4)
    out['frames'].append({'index': frame['index'], 'file': shot['file'], **identity,
                          'target_hero_pixels': frame['target_hero_pixels'], 'level': shot['lod']['level'],
                          'state_sha256': shot['state_sha256'], 'inspected': True,
                          'observation': 'Pale quiver/head-area glint; exact same-camera partner confirms pixels.'
                          if frame['index'] in [9, 20] else
                          'No obvious silhouette hole, detached bow/skin or large garment shift observed at this sample.'})
for index in [8, 9, 10, 19, 20, 21]:
    path = ARCHIVE / ('frame-%05d.png' % index)
    region = pixels(path)[390:440, 610:655]
    brightest = np.unravel_index(np.argmax(region.min(axis=2)), region.shape[:2])
    out['glint_measurement'][str(index)] = {
        'roi_xyxy': [610, 390, 655, 440],
        'decoded_roi_rgb_sha256': hashlib.sha256(region.tobytes()).hexdigest(),
        'pixels_min_rgb_gt200': int((region.min(axis=2) > 200).sum()),
        'brightest_by_min_channel_rgb': region[brightest].tolist(),
        'level': report['frames'][index]['image']['lod']['level']}
for index in [9, 20]:
    name = 'frame-%05d.png' % index
    assert pin(HERE / name) == pin(ARCHIVE / name), name
assert out['glint_measurement']['9']['decoded_roi_rgb_sha256'] == out['glint_measurement']['20']['decoded_roi_rgb_sha256']
assert out['glint_measurement']['9']['pixels_min_rgb_gt200'] == 505
for name in ['capture-run.json', 'camera-video.json', 'rama-lod-camera.mp4', 'capture.godot.log']:
    out['supporting_files'][name] = pin(ARCHIVE / name)
log = (ARCHIVE / 'capture.godot.log').read_text()
out['engine_log'] = {'errors': log.count('ERROR:'), 'warnings': log.count('WARNING:')}
assert out['engine_log'] == {'errors': 0, 'warnings': 0}
out['scope'] = ('Identity and pixel debugging measurements, not image-quality scores. '
                'All42 original PNGs are reviewed and hashed; the30-frame camera sequence moves around '
                'one frozen actualQ windup. No continuous deformation, hardwareFPS or finalLOD-art acceptance.')
(HERE / 'proof.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'identity_passed': True, 'sources': verified_sources, 'imports': len(report['imports']),
                  'pairs': 6, 'camera_frames': 30, 'engine_log': out['engine_log'],
                  'glint_pixels_9_and_20': 505, 'result': 'LIMITED: controlled182px near/mid comparison pending'}))
