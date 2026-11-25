"""Create a separate Hanuman look-dev scene using a packed PNG visual reference.

Start Blender with the exact source .blend. No runtime asset is exported.
The original scene and data stay in the new file for matched comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

BRANCH_NAME = 'Hanuman - Look Development'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def studio_branch(source):
    """Share read-only mesh, armature and action data; copy the presentation."""
    saved_slots = {obj: [(slot.link, slot.material) for slot in obj.material_slots]
                   for obj in source.objects if obj.type == 'MESH'}
    bpy.ops.scene.new(type='EMPTY')
    branch = bpy.context.scene
    branch.name = BRANCH_NAME
    if source.world:
        branch.world = source.world.copy()
    originals = list(source.objects)
    copies, materials = {}, {}
    for obj in originals:
        clone = obj.copy()
        clone.name = 'LookDev - ' + obj.name
        branch.collection.objects.link(clone)
        copies[obj] = clone
        if obj.type in {'CAMERA', 'LIGHT'}:
            clone.data = obj.data.copy()
        if obj.type == 'MESH':
            for index, slot in enumerate(clone.material_slots):
                original_material = saved_slots[obj][index][1]
                if original_material is None:
                    continue
                if original_material not in materials:
                    copy = original_material.copy()
                    copy.name = 'LookDev - ' + original_material.name
                    materials[original_material] = copy
                slot.link = 'OBJECT'
                slot.material = materials[original_material]

    for obj, clone in copies.items():
        if obj.parent in copies:
            clone.parent = copies[obj.parent]
            clone.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
        for modifier in clone.modifiers:
            if modifier.type == 'ARMATURE' and modifier.object in copies:
                modifier.object = copies[modifier.object]

    for obj, slots in saved_slots.items():
        if [(slot.link, slot.material) for slot in obj.material_slots] != slots:
            raise RuntimeError(f'Look development modified the original material slots: {obj.name}')
    branch.camera = copies[source.camera]
    branch.frame_set(source.frame_current, subframe=source.frame_subframe)
    return branch, copies, materials


def pack_png(path: Path, role: str):
    if path.suffix.lower() != '.png':
        raise ValueError(f'The {role} image must be a PNG')
    image = bpy.data.images.load(str(path), check_existing=False)
    image.pack()
    image_hash = sha256(path)
    if not image.packed_file or hashlib.sha256(image.packed_file.data).hexdigest() != image_hash:
        raise RuntimeError(f'Packed {role} bytes do not match the supplied PNG')
    image.name = f'{role} - {path.stem}'
    image.filepath = '//'+path.name
    image['origin'] = role
    image['reference_sha256'] = image_hash
    image['runtime_asset'] = False
    return image


def pack_reference(scene, path: Path, role: str, position):
    image = pack_png(path,role)
    image_hash = image['reference_sha256']
    collection = bpy.data.collections.new('Visual reference - viewport only')
    scene.collection.children.link(collection)
    collection.hide_render = True
    collection['runtime_asset'] = False
    collection['reference_sha256'] = image_hash
    board = bpy.data.objects.new('Reference board - ' + role, None)
    collection.objects.link(board)
    board.empty_display_type = 'IMAGE'
    board.data = image
    board.empty_display_size = 1.75
    board.rotation_euler = (math.pi / 2, 0, 0)
    board.location = position
    board.hide_render = True
    board.hide_select = True
    board['purpose'] = 'Visual development only'
    board['runtime_asset'] = False
    return image, collection, board


def use_cloth_swatch(materials, path: Path, uv_repeat: float):
    """Replace only the editable red fabric albedo, using the existing UVs."""
    source, material = next((original,copy) for original,copy in materials.items()
                            if original.name == 'Drapery · red madder dyed weave')
    shader = material.node_tree.nodes.get('Principled BSDF')
    base = shader.inputs['Base Color'].links[0].from_node
    normal = shader.inputs['Normal'].links[0].from_node
    normal_image = normal.inputs['Color'].links[0].from_node.image
    if base.type != 'TEX_IMAGE' or normal.type != 'NORMAL_MAP':
        raise ValueError('Expected madder cloth with an albedo image and tangent normal map')
    original_base = source.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node
    original_image = original_base.image
    diffuse = pack_png(path,'imagegen-cloth-albedo')
    diffuse.colorspace_settings.name = 'sRGB'
    base.image = diffuse
    base.extension = 'REPEAT'
    if uv_repeat != 1.0:
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        coordinate = base.inputs['Vector']
        if coordinate.is_linked:
            uv = coordinate.links[0].from_socket
        else:
            coordinates = nodes.new('ShaderNodeTexCoord')
            coordinates.label = 'Existing cloth UVs'
            coordinates.location = (base.location.x-440, base.location.y)
            uv = coordinates.outputs['UV']
        repeat = nodes.new('ShaderNodeVectorMath')
        repeat.operation = 'SCALE'
        repeat.label = 'Look development color repeat'
        repeat.location = (base.location.x-220, base.location.y)
        repeat.inputs['Scale'].default_value = uv_repeat
        links.new(uv, repeat.inputs[0])
        links.new(repeat.outputs['Vector'], coordinate)
    if original_base.image != original_image or base.image == original_image:
        raise RuntimeError('The cloth look changed the original actor texture slot')
    return {'file':path.name,'sha256':diffuse['reference_sha256'],
            'pixels':list(diffuse.size),'material':material.name,
            'base_color_node':base.name,'extension':base.extension,
            'color_uv_repeat':uv_repeat,
            'existing_normal_image':normal_image.name}


def face_toward(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z','Y').to_euler()


def apply_profile(scene, copies, materials, profile):
    if 'exposure' in profile:
        scene.view_settings.exposure = float(profile['exposure'])
    if 'resolution' in profile:
        scene.render.resolution_x, scene.render.resolution_y = profile['resolution']
        scene.render.resolution_percentage = 100
    if 'world' in profile:
        bg = scene.world.node_tree.nodes.get('Background')
        bg.inputs['Color'].default_value = (*profile['world']['color'],1)
        bg.inputs['Strength'].default_value = profile['world']['strength']
    camera = profile.get('camera', {})
    if camera:
        scene.camera.location = camera['position']
        face_toward(scene.camera,camera['target'])
        if 'ortho_scale' in camera:
            scene.camera.data.type = 'ORTHO'
            scene.camera.data.ortho_scale = camera['ortho_scale']
        elif 'lens_mm' in camera:
            scene.camera.data.type = 'PERSP'
            scene.camera.data.lens = camera['lens_mm']
    lights = {obj.name: copy for obj,copy in copies.items() if obj.type == 'LIGHT'}
    for name, spec in profile.get('lights', {}).items():
        light = lights[name]
        if 'position' in spec:
            light.location = spec['position']
        if 'target' in spec:
            face_toward(light,spec['target'])
        if 'color' in spec:
            light.data.color = spec['color']
        if 'power' in spec:
            light.data.energy = spec['power']
        if 'size' in spec:
            light.data.size = spec['size']
        if 'size_y' in spec:
            light.data.shape = 'RECTANGLE'
            light.data.size_y = spec['size_y']

    effects = {material.name: copy for material,copy in materials.items()}
    controls = {'roughness':'Roughness','metallic':'Metallic',
                'specular':'Specular IOR Level','subsurface':'Subsurface Weight'}
    for name, spec in profile.get('materials', {}).items():
        material = effects[name]
        nodes = material.node_tree.nodes
        shader = nodes.get('Principled BSDF')
        for key, value in spec.items():
            if key in controls:
                shader.inputs[controls[key]].default_value = float(value)
            elif key == 'normal_strength':
                normal = next(node for node in nodes if node.type == 'NORMAL_MAP')
                normal.inputs['Strength'].default_value = float(value)
            elif key == 'tint':
                socket = shader.inputs['Base Color']
                links = material.node_tree.links
                if socket.is_linked:
                    upstream = socket.links[0].from_socket
                    tint_node = nodes.new('ShaderNodeMixRGB')
                    tint_node.name = 'LookDev tint'
                    tint_node.blend_type = 'MULTIPLY'
                    tint_node.inputs[0].default_value = 1.0
                    tint_node.inputs[2].default_value = (*value,1)
                    links.new(upstream,tint_node.inputs[1])
                    links.new(tint_node.outputs[0],socket)
                else:
                    socket.default_value = (*value,1)
            else:
                raise ValueError(f'Unknown material control {key!r}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--reference-kind', required=True,
                        choices=('imagegen','studio-test'))
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--cloth-texture', type=Path,
                        help='Flat ImageGen color swatch for the editable madder cloth')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--render', type=Path,
                        help='Optional new PNG rendered from the editable look-dev scene')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source_path = Path(bpy.data.filepath).resolve()
    if sha256(source_path) != args.source_sha256:
        raise ValueError(f'Blender source digest differs from expected {args.source_sha256}')
    if args.output.exists() or source_path == args.output.resolve() or args.output.suffix != '.blend':
        raise ValueError('Write a new .blend path to preserve source and earlier looks')
    if args.render and (args.render.exists() or args.render.suffix.lower() != '.png'):
        raise ValueError('Write a new PNG for the look development render')
    profile = json.loads(args.profile.read_text()) if args.profile else {}
    uv_repeat = profile.get('cloth_color_uv_repeat', 1.0)
    if type(uv_repeat) not in (int,float) or not math.isfinite(uv_repeat) or not .25 <= uv_repeat <= 12.0:
        raise ValueError('Cloth color UV repeat must be finite and between 0.25 and 12')
    source = bpy.context.scene
    if source.camera is None or BRANCH_NAME in bpy.data.scenes:
        raise ValueError('Use the original Hanuman studio Blender scene as source')
    branch,copies,materials = studio_branch(source)
    cloth = use_cloth_swatch(materials,args.cloth_texture.resolve(),float(uv_repeat)) if args.cloth_texture else None
    apply_profile(branch,copies,materials,profile)
    image,collection,board = pack_reference(branch,args.reference.resolve(),args.reference_kind,
        profile.get('reference_position',(2.2,0,1.15)))
    actor = [(original,clone) for original,clone in copies.items()
             if original.type in {'MESH','ARMATURE'}]
    if any(original.data != clone.data for original,clone in actor):
        raise RuntimeError('Anatomy or rig data was duplicated unexpectedly')
    arms = [(original,clone) for original,clone in actor if original.type == 'ARMATURE']
    if len(arms) != 1 or arms[0][0].animation_data.action != arms[0][1].animation_data.action:
        raise RuntimeError('The look development scene does not share the original actor action')

    branch['source_blend_sha256'] = args.source_sha256
    branch['reference_origin'] = args.reference_kind
    branch['runtime_export'] = False
    args.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()),compress=True)
    if sha256(source_path) != args.source_sha256:
        raise RuntimeError('Original studio source file changed')
    receipt = {
        'source_sha256':args.source_sha256,
        'source_scene':source.name,'lookdev_scene':branch.name,
        'blend_sha256':sha256(args.output),'reference_name':args.reference.name,
        'reference_sha256':image['reference_sha256'],
        'reference_kind':args.reference_kind,'reference_pixels':list(image.size),
        'reference_viewport_only':collection.hide_render and board.hide_render,
        'cloth_texture':cloth,
        'mesh_and_rig_data_shared':len(actor),
        'materials_editable_per_scene':len(materials),
        'shared_action_count':len(bpy.data.actions),
        'bone_count':len(arms[0][0].data.bones),
        'external_libraries':len(bpy.data.libraries),
        'profile_sha256':sha256(args.profile) if args.profile else None,
    }
    if args.render:
        args.render.parent.mkdir(parents=True,exist_ok=True)
        branch.render.filepath = str(args.render.resolve())
        bpy.ops.render.render(write_still=True)
        receipt['render'] = {'file':args.render.name,'sha256':sha256(args.render),
                             'scene':branch.name,'renderer':branch.render.engine,
                             'size':[branch.render.resolution_x,branch.render.resolution_y]}
    args.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('HANUMAN_LOOKDEV '+json.dumps(receipt))


if __name__ == '__main__':
    main()
