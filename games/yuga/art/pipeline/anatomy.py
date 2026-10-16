"""Original importer of separately licensed CC0 MakeHuman data, not its code."""
import json
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


def build_anatomy(source, variant, height, width=1.0, face_width=1.0):
    vertices, uvs, faces, face_uvs = [], [], [], []
    group = ''
    for line in (source / 'makehuman-base.obj').read_text().splitlines():
        if line.startswith('v '): vertices.append(Vector(tuple(map(float, line.split()[1:4]))))
        elif line.startswith('vt '): uvs.append(tuple(map(float, line.split()[1:3])))
        elif line.startswith('g '): group = line[2:]
        elif line.startswith('f ') and group == 'body':
            tokens = [t.split('/') for t in line.split()[1:]]
            faces.append([int(t[0]) - 1 for t in tokens])
            face_uvs.append([int(t[1]) - 1 for t in tokens])
    for line in (source / f'adult-{variant}.target').read_text().splitlines():
        if not line or line.startswith('#'): continue
        row = line.split(); vertices[int(row[0])] += Vector(tuple(map(float, row[1:4])))
    used = sorted(set(i for f in faces for i in f)); remap = {old: new for new, old in enumerate(used)}
    low = min(vertices[i].y for i in used); scale = height / (max(vertices[i].y for i in used) - low)
    def transform(v):
        z = (v.y - low) * scale
        w = width if z < height * .82 else face_width
        return Vector((v.x * scale * w, -v.z * scale * (1 + (width - 1) * .55), z))
    all_vertices = [transform(v) for v in vertices]
    mesh = bpy.data.meshes.new('CC0 anatomical topology')
    mesh.from_pydata([all_vertices[i] for i in used], [], [[remap[i] for i in f] for f in faces]); mesh.update()
    body = bpy.data.objects.new('Continuous anatomical surface', mesh); bpy.context.collection.objects.link(body)
    uv = mesh.uv_layers.new(name='UVMap')
    for polygon, source_uv in zip(mesh.polygons, face_uvs):
        polygon.use_smooth = True
        for li, ui in zip(polygon.loop_indices, source_uv): uv.data[li].uv = uvs[ui]
    skeleton = json.loads((source / 'default.mhskel').read_text())
    armature = bpy.data.armatures.new('CC0 native 163 joint skeleton')
    rig = bpy.data.objects.new('YugaHeroRig', armature); bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    joints = {name: sum((all_vertices[i] for i in ids), Vector()) / len(ids) for name, ids in skeleton['joints'].items()}
    for name, definition in skeleton['bones'].items():
        bone = armature.edit_bones.new(name); bone.head = joints[definition['head']]; bone.tail = joints[definition['tail']]
        if (bone.tail - bone.head).length < 1e-5: bone.tail = bone.head + Vector((0, 0, .005))
    for name, definition in skeleton['bones'].items():
        bone = armature.edit_bones[name]
        if definition['parent']: bone.parent = armature.edit_bones[definition['parent']]
        plane = skeleton['planes'].get(definition.get('rotation_plane'))
        if plane:
            a, b, c = [joints[k] for k in plane]; normal = (b-a).cross(c-a)
            if normal.length > 1e-8: bone.align_roll(normal.normalized())
    bpy.ops.object.mode_set(mode='OBJECT')
    weight_map = [[] for _ in used]
    for bone, entries in json.loads((source / 'default_weights.mhw').read_text())['weights'].items():
        if bone not in armature.bones: continue
        for index, weight in entries:
            if index in remap and weight > 0: weight_map[remap[index]].append((bone, weight))
    for i, entries in enumerate(weight_map):
        entries.sort(key=lambda entry: entry[1], reverse=True); entries = entries[:4]
        assert entries, f'Unweighted anatomical vertex {i}'
        total = sum(w for _, w in entries); weight_map[i] = [(b, w / total) for b, w in entries]
    bind(body, rig, weight_map)
    tree = KDTree(len(mesh.vertices))
    for v in mesh.vertices: tree.insert(v.co, v.index)
    tree.balance()
    return body, rig, weight_map, tree


def bind(obj, rig, weights):
    groups = {}
    for index, entries in enumerate(weights):
        for name, weight in entries:
            if name not in groups: groups[name] = obj.vertex_groups.new(name=name)
            groups[name].add([index], weight, 'REPLACE')
    modifier = obj.modifiers.new('Skin deformation', 'ARMATURE'); modifier.object = rig
    obj.parent = rig
