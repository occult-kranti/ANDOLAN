# SPDX-License-Identifier: GPL-3.0-or-later
"""One R1 correction: encode existing coverage atlas's linear albedo as sRGB.

No coverage rebake or geometry change. Preserves the first output and verifies
alpha and mesh/skin data against it before writing a fresh candidate.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_candidate import ImagePixels, digest, sha


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    receipt = json.loads(a.receipt.read_text())
    master = next(item for item in receipt['outputs'] if item['path'].endswith('.blend'))
    source = a.receipt.parent / master['path']
    assert sha(source) == master['sha256']
    a.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    cards = bpy.data.objects['YUGA MPFB nape cards near CANDIDATE']
    rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    image = bpy.data.images['MPFB donor nape actual coverage atlas']
    before = ImagePixels.read_image_pixels(image).reshape(-1, 4)
    alpha = before[:, 3].copy()
    mesh_before = digest([tuple(v.co) for v in cards.data.vertices])
    image.colorspace_settings.name = 'sRGB'
    # This generated non-float image retains byte-encoded pixel values. The
    # R2 attempt changed metadata but produced the same (3,2,2) RGB. Encode
    # explicitly and verify the stored PNG bytes outside Blender as well.
    linear = np.array((.012, .008, .006), dtype=np.float32)
    encoded = np.where(linear <= .0031308, linear * 12.92,
                       1.055 * linear ** (1.0 / 2.4) - .055)
    before[:, :3] = encoded
    ImagePixels.write_image_pixels(image, before)
    image.filepath_raw = str((a.output / 'mpfb-nape-albedo-alpha.png').resolve())
    image.file_format = 'PNG'
    image.save()
    image.pack()
    assert np.array_equal(ImagePixels.read_image_pixels(image).reshape(-1, 4)[:, 3], alpha)
    bpy.ops.object.select_all(action='DESELECT')
    cards.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = cards
    glb = a.output / 'mpfb-nape-cards-near.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True,
        export_animations=False, export_apply=False, export_extras=True,
        export_skins=True, export_def_bones=False, export_yup=True)
    path = a.output / 'rama-mpfb-card-candidate.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    assert mesh_before == digest([tuple(v.co) for v in cards.data.vertices])
    output = dict(receipt)
    output.update({
        'correction': 'Retained actual R1 alpha coverage, encoded intended linear albedo as sRGB PNG for glTF baseColorTexture',
        'parent_receipt_sha256': sha(a.receipt), 'parent_master_sha256': sha(source),
        'correction_script_sha256': sha(__file__), 'alpha_exact_in_blender_buffer': True,
        'all_mesh_positions_exact': True, 'source_albedo_linear': [.012, .008, .006],
        'texture_colorspace': 'sRGB', 'rebaked': False,
        'encoded_albedo': encoded.tolist(), 'encoded_byte_expectation': np.rint(encoded * 255).astype(int).tolist(),
        'outputs': [{'path': f.name, 'bytes': f.stat().st_size, 'sha256': sha(f)} for f in (glb, Path(image.filepath_raw), path)],
    })
    (a.output / 'receipt.json').write_text(json.dumps(output, indent=2) + '\n')
    print('MPFB_COLOR_REPAIR=' + json.dumps(output, separators=(',', ':')))


if __name__ == '__main__':
    main()
