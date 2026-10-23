"""Blender-only source inspection and four actual CPU-rendered prop views."""
import bpy
from mathutils import Vector
from pathlib import Path
import hashlib
import json
import math
import sys
import time

args = sys.argv[sys.argv.index('--') + 1:]
source, output = Path(args[0]), Path(args[1])
output.mkdir(parents=True, exist_ok=False)
started = time.monotonic()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not objects:
    raise RuntimeError('No imported mesh')
vertices = sum(len(o.data.vertices) for o in objects)
if vertices > 2000000:
    raise RuntimeError('Mesh exceeds inspection budget')
if any(not all(math.isfinite(v) for v in p.co) for o in objects for p in o.data.vertices):
    raise RuntimeError('Nonfinite vertex')
details = []
for o in objects:
    o.data.calc_loop_triangles()
    details.append({'object': o.name, 'vertices': len(o.data.vertices),
                    'triangles': len(o.data.loop_triangles),
                    'uv_layers': len(o.data.uv_layers),
                    'materials': [m.name if m else None for m in o.data.materials]})
points = [o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
low = Vector([min(p[i] for p in points) for i in range(3)])
high = Vector([max(p[i] for p in points) for i in range(3)])
center, size = (low + high) / 2, max(high - low)
if not math.isfinite(size) or size <= 0:
    raise RuntimeError('Degenerate bounds')
images = [{'name': im.name, 'size': list(im.size), 'packed': bool(im.packed_file)}
          for im in bpy.data.images]
if any(not all(dim > 0 for dim in im['size']) for im in images):
    raise RuntimeError('Missing image dimensions')
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('Inspection studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.22, .25, .31, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .4
bpy.ops.mesh.primitive_plane_add(size=size * 20, location=(center.x, center.y, low.z - size * .01))
floor = bpy.context.object
mat = bpy.data.materials.new('Neutral inspection floor')
mat.diffuse_color = (.16, .18, .22, 1)
floor.data.materials.append(mat)
def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
for name, offset, power, color in [
    ('key', (2, -3, 4), 600, (1, .85, .67)),
    ('fill', (-3, -1, 2), 300, (.62, .78, 1)),
    ('rim', (1, 3, 3), 700, (1, .93, .81)),
]:
    data = bpy.data.lights.new(name, type='AREA')
    data.energy, data.color, data.shape, data.size = power * size * size, color, 'DISK', size * 3
    light = bpy.data.objects.new(name, data);scene.collection.objects.link(light)
    light.location = center + Vector(offset) * size;aim(light, center)
data = bpy.data.cameras.new('Inspection camera')
camera = bpy.data.objects.new('Inspection camera', data);scene.collection.objects.link(camera)
scene.camera = camera
data.type = 'ORTHO';data.ortho_scale = size * 1.25
renders = []
for name, offset in [('front', (1.5, -3, 1.2)), ('side', (3, 1, 1.2)),
                     ('rear', (-1.5, 3, 1.2)), ('opposite', (-3, -1, 1.2))]:
    camera.location = center + Vector(offset) * size;aim(camera, center)
    path = output / (name + '.png');scene.render.filepath = str(path)
    before = time.monotonic();bpy.ops.render.render(write_still=True)
    renders.append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'seconds': time.monotonic() - before})
report = {'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'blender': bpy.app.version_string, 'vertices': vertices, 'objects': details,
          'images': images, 'bounds_min': list(low), 'bounds_max': list(high),
          'actual_scale_qualified': False, 'render_engine': 'Cycles CPU', 'samples': 16,
          'denoising': False, 'renders': renders, 'elapsed_seconds': time.monotonic() - started,
          'acceptance': 'Source import and actual static inspection views only; no runtime promotion, collision, LOD, rig or animation acceptance.'}
(output / 'inspection.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'vertices': vertices, 'triangles': sum(x['triangles'] for x in details),
                  'images': len(images), 'renders': len(renders)}))
