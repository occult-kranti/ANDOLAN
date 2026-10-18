"""Four unchanged authoring cameras. Execute only with the shared raster lane."""
import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'clay-framing-r3'))
from projection_contract import points, census, fits


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-scene-sha256', required=True)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    scene_path = Path(bpy.data.filepath)
    assert sha(scene_path) == args.expected_scene_sha256
    assert not args.output.exists()
    assert shutil.disk_usage('/workspace').free >= 500*1024**2
    args.output.mkdir(parents=True)
    scene = bpy.context.scene
    # Same raw CPU32sample policy as the retained C1/C2 actual captures; the
    # installed Blender lacks OpenImageDenoise. Never save these runtime flags.
    scene.cycles.device = 'CPU'
    scene.cycles.use_denoising = False
    assert scene.cycles.samples == 32
    hair, context = points(scene)
    projections = census(scene, hair, context)
    assert all(fits(b) for row in projections.values() for b in row.values())
    result = dict(scope='Actual coarse Blender authoring clay; not runtime or animated cast evidence',
                  scene_sha256=args.expected_scene_sha256, helper_sha256=sha(__file__),
                  blender_version=bpy.app.version_string, samples=scene.cycles.samples,
                  use_denoising=False, preflight_only=args.preflight,
                  source_glb_sha256=scene['source_glb_sha256'], views=[])
    for name, projection in projections.items():
        scene.camera = bpy.data.objects['VIEW_'+name]
        row = dict(id=name, projection=projection,
                   camera_matrix_world=[list(r) for r in scene.camera.matrix_world],
                   lens_mm=scene.camera.data.lens)
        if not args.preflight:
            assert shutil.disk_usage('/workspace').free >= 500*1024**2
            destination = args.output/(name+'.png')
            scene.render.filepath = str(destination)
            started = time.monotonic()
            bpy.ops.render.render(write_still=True)
            row.update(png_sha256=sha(destination), png_bytes=destination.stat().st_size,
                       render_seconds=time.monotonic()-started)
        result['views'].append(row)
        (args.output/'capture.json').write_text(json.dumps(result, indent=2)+'\n')
        print('VOLUME_VIEW', name, 'PREFLIGHT' if args.preflight else 'ACTUAL', flush=True)
    result['complete'] = len(result['views']) == 4
    result['saved_scene_unchanged'] = sha(scene_path) == args.expected_scene_sha256
    assert result['complete'] and result['saved_scene_unchanged']
    (args.output/'capture.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
