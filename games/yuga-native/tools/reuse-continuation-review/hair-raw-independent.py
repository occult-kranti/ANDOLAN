#!/usr/bin/env python3
"""Raw donor-card/skin/source preservation review, independent of Blender code."""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import struct
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--hair', type=Path, required=True)
parser.add_argument('--masked', type=Path, required=True)
parser.add_argument('--mask', type=Path, required=True)
parser.add_argument('--old-atlas', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
if not args.report.is_absolute() or args.report.exists(): parser.error('Fresh absolute report required')
canonical = Path(__file__).resolve().parents[2] / 'assets/heroes/rama-hero.glb'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def glb(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw))
    count, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(raw[20:20+count])
    size, tag = struct.unpack_from('<II', raw, 20+count)
    assert tag == 0x004e4942
    return doc, raw[28+count:28+count+size]
def accessor(doc, data, key):
    a = doc['accessors'][key]; view = doc['bufferViews'][a['bufferView']]
    components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    code = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
    fmt = '<' + code * components; size = struct.calcsize(fmt)
    offset = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', size)
    assert offset + (a['count']-1)*stride+size <= len(data)
    return [struct.unpack_from(fmt, data, offset+i*stride) for i in range(a['count'])]

c, cb = glb(canonical); h, hb = glb(args.hair); m, mb = glb(args.masked)
proof = json.loads(args.mask.read_text()); checks = []
def check(name, accepted, detail=None): checks.append({'name': name, 'passed': bool(accepted), 'detail': detail})
check('canonical-hero-hash-remains-approved', sha(canonical) == 'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e')
check('masked-hero-preserves-every-original-binary-byte', mb[:len(cb)] == cb, {'original_bytes': len(cb)})
assert len(m['accessors']) == len(c['accessors']) + 1 and len(m['bufferViews']) == len(c['bufferViews']) + 1
mi, pi = proof['mesh_index'], proof['primitive_index']
original_indices = [r[0] for r in accessor(c, cb, c['meshes'][mi]['primitives'][pi]['indices'])]
masked_indices = [r[0] for r in accessor(m, mb, m['meshes'][mi]['primitives'][pi]['indices'])]
selected = set(proof['selected_accessor_vertex_ids']); removed = set(proof['removed_triangle_ids'])
expected = []; mixed = 0
for index in range(len(original_indices)//3):
    corners = original_indices[index*3:index*3+3]; member = [v in selected for v in corners]
    mixed += int(any(member) and not all(member))
    if index not in removed: expected += corners
check('exact-approved-nape-triangles-removed-no-mixed-protected-faces', masked_indices == expected and mixed == 0 and len(removed) == 7344, {'removed': len(removed), 'mixed_faces': mixed})
reverted = copy.deepcopy(m)
reverted['accessors'].pop(); reverted['bufferViews'].pop()
reverted['meshes'][mi]['primitives'][pi]['indices'] = c['meshes'][mi]['primitives'][pi]['indices']
reverted['buffers'][0]['byteLength'] = c['buffers'][0]['byteLength']
check('all-other-json-structure-remains-identical', reverted == c)
head = next(i for i, node in enumerate(h['nodes']) if node.get('name') == 'head')
joint_names = lambda doc: [doc['nodes'][index]['name'] for index in doc['skins'][0]['joints']]
check('164-canonical-bone-names-and-order', len(h['skins'][0]['joints']) == 164 and joint_names(h) == joint_names(c))
primitive = h['meshes'][0]['primitives'][0]
attrs = primitive['attributes']; points = accessor(h, hb, attrs['POSITION'])
joints = accessor(h, hb, attrs['JOINTS_0']); weights = accessor(h, hb, attrs['WEIGHTS_0'])
head_index = h['skins'][0]['joints'].index(head)
def head_binding(js, ws): return len(js) == len(ws) == len(points) and all(j[0] == head_index and w == (1., 0., 0., 0.) for j, w in zip(js, ws))
check('all-card-vertices-bind-only-to-canonical-head', head_binding(joints, weights), {'vertices': len(points), 'head_joint': head_index})
wrong = copy.deepcopy(joints); wrong[0] = (0, *wrong[0][1:])
check('one-wrong-bone-influence-counterexample-detected', not head_binding(wrong, weights))
zero = copy.deepcopy(weights); zero[0] = (0., 0., 0., 0.)
check('one-unweighted-vertex-counterexample-detected', not head_binding(joints, zero))
uv = accessor(h, hb, attrs['TEXCOORD_0'])
indices = accessor(h, hb, primitive['indices'])
check('bounded-finite-card-geometry-and-UV', len(points) == 2304 and len(indices)//3 == 2160 and all(math.isfinite(v) for point in points for v in point) and all(0 <= v <= 1 for row in uv for v in row) and max(row[0] for row in indices) < len(points))
material = h['materials'][primitive['material']]
check('single-two-sided-dielectric-covered-surface', len(h['meshes']) == len(h['meshes'][0]['primitives']) == 1 and material['doubleSided'] and material['alphaMode'] == 'BLEND' and material['pbrMetallicRoughness']['metallicFactor'] == 0)
view = h['bufferViews'][h['images'][0]['bufferView']]
atlas = Image.open(io.BytesIO(hb[view.get('byteOffset', 0):view.get('byteOffset', 0)+view['byteLength']])).convert('RGBA')
old = Image.open(args.old_atlas).convert('RGBA')
check('actual-baked-alpha-retained-exact-through-color-correction', atlas.size == old.size == (1024, 1024) and atlas.getchannel('A').tobytes() == old.getchannel('A').tobytes())
check('glTF-sRGB-albedo-encoded-as-reviewed', all(pixel[:3] == (29, 22, 18) for pixel in atlas.getdata()), {'encoded_rgb': list(atlas.getpixel((0, 0)))[:3], 'alpha_extrema': atlas.getchannel('A').getextrema()})
check('asset-does-not-add-animation-owner', not h.get('animations'))
report = {'kind': 'independent-native-hair-raw-review', 'source': {str(p): sha(p) for p in (canonical, args.hair, args.masked, args.mask, args.old_atlas)},
          'checks': checks, 'passed': all(row['passed'] for row in checks),
          'scope': 'Raw protected source/card/skin/atlas eligibility only; no visual, body contact, motion continuity, LOD or hardware acceptance.'}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': len(checks), 'failed': [row['name'] for row in checks if not row['passed']]}))
raise SystemExit(0 if report['passed'] else 1)
