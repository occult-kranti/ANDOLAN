"""Reopen a saved presentation stage and validate actual authored/imported data."""
import bpy
from pathlib import Path
from mathutils import Vector
import hashlib
import json
import math
import sys

args = sys.argv[sys.argv.index('--') + 1:]
scene_path, output_path = map(Path, args)
if output_path.exists():
    raise RuntimeError('Fresh verification receipt required')
bpy.ops.wm.open_mainfile(filepath=str(scene_path.resolve()))
scene = bpy.context.scene
checks = []

def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})

rigs = [o for o in scene.objects if o.type == 'ARMATURE']
check('one_exact_164_bone_rig', len(rigs) == 1 and len(rigs[0].data.bones) == 164)
check('nine_embedded_baseline_actions_retained', len(bpy.data.actions) == 9)
check('selected_embedded_idle_pose', len(rigs) == 1 and rigs[0].animation_data.action.name.startswith('idle_'))
check('accepted_hero_three_render_meshes', sum(o.type == 'MESH' and not o.hide_render for o in bpy.data.collections['01 Accepted Rama — unchanged source'].objects) == 3)
check('all_positions_finite', all(all(math.isfinite(x) for x in v.co) for o in scene.objects if o.type == 'MESH' for v in o.data.vertices))
check('packed_render_images', all(bool(im.packed_file) for im in bpy.data.images if im.size[0] > 0 and im.type != 'RENDER_RESULT'))
check('three_cc0_sandstone_maps_loaded', sum('sandstone_blocks_05_' in im.name for im in bpy.data.images) == 3)
check('bounded_CPU_render_settings', scene.render.engine == 'CYCLES' and scene.cycles.device == 'CPU' and scene.render.threads == 2 and not scene.cycles.use_denoising)
check('source_scope_label_retained', 'Presentation prototype' in scene.get('stage_scope', '') and 'Deadlock-parity' in scene.get('stage_scope', ''))
source_hashes = json.loads(scene['source_hashes_json'])
check('exact_source_bindings_retained', len(source_hashes) == 8 and all(len(v) == 64 for v in source_hashes.values()))
report = {'schema_version': 1, 'scene_path': scene_path.name, 'scene_sha256': hashlib.sha256(scene_path.read_bytes()).hexdigest(),
          'blender': bpy.app.version_string, 'checks': checks, 'all_passed': all(c['passed'] for c in checks),
          'scope': 'Reopened Blender source/data verification only; no additional render, gameplay or hardware-FPS claim.'}
output_path.write_text(json.dumps(report, indent=2) + '\n')
print('YUGA_STAGE_VERIFY=' + json.dumps(report, separators=(',', ':')))
if not report['all_passed']:
    raise RuntimeError('Stage verification failed')
