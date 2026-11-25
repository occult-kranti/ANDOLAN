"""Build an editable, standalone Vanara Sena presentation study in Blender 4.3.

This is a studio animation using a supplied Hanuman rig and original VFX. It is
not a new playable character clip or the authoritative gameplay simulation.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
MASTER = NATIVE / "art/hanuman-hero-finish/blender/hanuman.blend"
MODEL = NATIVE / "art/hanuman-hero-finish/models/hanuman-enhanced.glb"
PROFILE = NATIVE.parent / "yuga-rust/assets/vanara-sena.json"
MASTER_SHA = "f0fc5798d7cfec0afc2ae084b8b8f5a76950ad94bcc1ec9f89fbc24f5952e7b0"
MODEL_SHA = "6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a"
ABILITY = json.loads(PROFILE.read_text())
FPS = 30
RELEASE = 1 + round(ABILITY["timing"]["windup_s"] * FPS)
END = RELEASE + round(ABILITY["timing"]["active_s"] * FPS)
RECOVERY = RELEASE + round(ABILITY["timing"]["recovery_s"] * FPS)
RADIUS = float(ABILITY["geometry"]["radius_m"])
if ABILITY["id"] != "vanara_sena" or ABILITY["geometry"]["kind"] != "disk" or ABILITY["motion"] != "cast2":
    raise ValueError("The Vanara Sena study requires its matching disk profile and cast2 clip")


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def key(obj, prop, entries):
    for frame, value in entries:
        setattr(obj, prop, value)
        obj.keyframe_insert(data_path=prop, frame=frame)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def clear_nla(rig):
    data = rig.animation_data_create()
    data.action = None
    for track in list(data.nla_tracks):
        data.nla_tracks.remove(track)
    data.use_nla = True
    return data


def strip(rig, action, start, duration, repeat=1):
    track = rig.animation_data.nla_tracks.new()
    track.name = "Sena study · " + action.name
    item = track.strips.new("Sena study · " + action.name, start, action)
    item.scale = duration / max(0.001, action.frame_range[1] - action.frame_range[0])
    item.repeat = repeat
    item.extrapolation = "HOLD_FORWARD"


def emit_material(name, color, intensity, opacity=1.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, opacity)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    surface = tree.nodes.new("ShaderNodeBsdfPrincipled")
    surface.inputs["Base Color"].default_value = (*color, 1.0)
    surface.inputs["Roughness"].default_value = .48
    surface.inputs["Metallic"].default_value = .15
    surface.inputs["Emission Color"].default_value = (*color, 1.0)
    surface.inputs["Emission Strength"].default_value = intensity
    if opacity < 1:
        transparent = tree.nodes.new("ShaderNodeBsdfTransparent")
        mix = tree.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = opacity
        tree.links.new(transparent.outputs[0], mix.inputs[1])
        tree.links.new(surface.outputs[0], mix.inputs[2])
        tree.links.new(mix.outputs[0], out.inputs["Surface"])
        material.surface_render_method = "DITHERED"
    else:
        tree.links.new(surface.outputs[0], out.inputs["Surface"])
    return material


def ring(collection, material, name, radius, width, center):
    segments = 96
    verts, faces = [], []
    for i in range(segments):
        a = math.tau * i / segments
        verts.extend([(math.cos(a) * (radius - width / 2), math.sin(a) * (radius - width / 2), 0),
                      (math.cos(a) * (radius + width / 2), math.sin(a) * (radius + width / 2), 0)])
    for i in range(segments):
        n = (i + 1) % segments
        faces.append((2 * i, 2 * n, 2 * n + 1, 2 * i + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = center
    return obj


def hair_strand(collection, material):
    curve = bpy.data.curves.new("Single gold strand · animated", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 16
    curve.bevel_depth = .009
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(2)
    curve.materials.append(material)
    strand = bpy.data.objects.new("A hair, carried by Vayu · study", curve)
    collection.objects.link(strand)
    points = [
        (RELEASE-12, [(0.21, -.16, 1.96), (.17, -.20, 2.04), (.15, -.25, 1.94)]),
        (RELEASE-6,[(0.19, -.20, 1.94), (.13, -.27, 1.98), (.10, -.32, 1.87)]),
        (RELEASE,[(0.08, -.30, 1.87), (.03, -.43, 1.86), (.01, -.50, 1.84)]),
        (RELEASE+4,[(0.02, -.42, 1.85), (.0, -.78, 2.00), (.0, -1.05, 1.83)]),
    ]
    for frame, coords in points:
        for point, co in zip(spline.bezier_points, coords):
            point.co = co
            point.handle_left_type = point.handle_right_type = "AUTO"
            point.keyframe_insert(data_path="co", frame=frame)
    key(strand, "hide_render", [(1,True),(RELEASE-13,True),(RELEASE-12,False),
                                (RELEASE+4,False),(RELEASE+5,True)])
    for fcurve in strand.animation_data.action.fcurves:
        for point in fcurve.keyframe_points:
            point.interpolation = "CONSTANT"
    return strand


def petal_mesh(mat):
    mesh = bpy.data.meshes.new("Shared original leaf / petal mesh")
    verts = [(0,0,0),(.08,.04,0),(.095,.16,.025),(0,.28,0),(-.095,.16,.025),(-.08,.04,0)]
    mesh.from_pydata(verts, [], [(0,1,2,3,4,5)])
    mesh.materials.append(mat)
    return mesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "vanara-sena-study.blend")
    parser.add_argument("--receipt", type=Path, default=HERE / "timeline.json")
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    if digest(MASTER) != MASTER_SHA or digest(MODEL) != MODEL_SHA:
        raise ValueError("Hanuman source scene or original model differs from its pinned baseline")
    bpy.ops.wm.open_mainfile(filepath=str(MASTER), load_ui=False)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end, scene.render.fps = 1, END+12, FPS
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = bool(getattr(bpy.app.build_options, "openimagedenoise", False))
    scene.cycles.max_bounces = 4
    scene.cycles.transparent_max_bounces = 6
    scene.render.threads_mode, scene.render.threads = "FIXED", 2
    scene.render.resolution_x, scene.render.resolution_y = 640, 360
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"

    for c in list(bpy.data.collections):
        if c.name == "Presentation VFX · editable":
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
    rig = bpy.data.objects["YugaHeroRig"]
    hero = bpy.data.objects["Hanuman skinned hero"]
    if len(rig.pose.bones) != 167:
        raise ValueError("Unexpected Hanuman skeleton")
    action = bpy.data.actions.get("cast2_YugaHeroRig")
    strike = bpy.data.actions.get("fire_YugaHeroRig")
    if not action or not strike:
        raise ValueError("Expected cast2 and fire actions in the master")
    clear_nla(rig)
    strip(rig, action, 1, RECOVERY-1)

    controls = bpy.data.collections.new("Sena · animator controls")
    scene.collection.children.link(controls)
    effects = bpy.data.collections.new("Sena · spirit study effects")
    scene.collection.children.link(effects)
    handle = bpy.data.objects.new("Left wrist · hair-to-breath path", None)
    controls.objects.link(handle)
    handle.empty_display_type, handle.empty_display_size = "SPHERE", .09
    key(handle, "location", [
        (1,(.323,-.216,1.247)), (RELEASE-12,(.25,-.21,1.72)),
        (RELEASE-7,(.19,-.20,1.90)), (RELEASE-2,(.11,-.30,1.79)),
        (RELEASE+3,(.06,-.49,1.70)), (RECOVERY,(.30,-.34,1.30))])
    ik = rig.pose.bones["lowerarm02.L"].constraints.new("IK")
    ik.name, ik.target, ik.chain_count = "Sena study · left arm reach", handle, 4
    for frame, value in [(1,0),(RELEASE-15,.25),(RELEASE-11,.9),(RELEASE-7,1),
                         (RELEASE,1),(RELEASE+6,.45),(RECOVERY,0)]:
        ik.influence = value
        ik.keyframe_insert(data_path="influence", frame=frame)

    gold = emit_material("Sena · leaf-gold light", (1.0,.47,.12), .8)
    pale = emit_material("Sena · soft ivory sparks", (1.0,.77,.37), 1.2)
    ghost_skin = emit_material("Sena · spectral amber", (.85,.31,.06), .18, .68)
    ghost_armor = emit_material("Sena · spectral bronze", (1.0,.57,.14), .36, .72)
    ghost_cloth = emit_material("Sena · spectral saffron", (.74,.19,.035), .17, .68)
    ghost_eye = emit_material("Sena · spectral dark detail", (.12,.036,.009), .02, .74)
    hair_strand(effects, pale)
    target = (0,-4.0,.045)
    boundary = ring(effects, gold, "Sena · target boundary", RADIUS, .035, target)
    key(boundary, "hide_render", [(1,False),(END,False),(END+1,True)])
    if boundary.animation_data and boundary.animation_data.action:
        for fc in boundary.animation_data.action.fcurves:
            for pt in fc.keyframe_points: pt.interpolation = "CONSTANT"
    center = ring(effects, pale, "Sena · focus ring", .22, .025, (0,-4.0,.06))
    key(center, "scale", [(1,(.3,)*3),(RELEASE,(1.5,)*3),(32,(.6,)*3),(END,(1.,)*3),(END+1,(.001,)*3)])
    ghosts=[]
    for i in range(5):
        angle = math.radians(-115 + 230*i/4)
        x, y = 2.05*math.sin(angle), -4 + 2.05*math.cos(angle)
        spirit_rig = rig.copy()
        spirit_rig.name = f"Sena guardian {i+1} · rig"
        effects.objects.link(spirit_rig)
        spirit_rig.animation_data_clear()
        for bone in spirit_rig.pose.bones:
            for constraint in list(bone.constraints):
                bone.constraints.remove(constraint)
        clear_nla(spirit_rig)
        strip(spirit_rig, strike, RELEASE+5+i, 18, repeat=2.3)
        spirit = hero.copy()
        spirit.name = f"Sena guardian {i+1} · skinned silhouette"
        effects.objects.link(spirit)
        spirit.parent = spirit_rig
        spirit.matrix_parent_inverse.identity()
        for modifier in spirit.modifiers:
            if modifier.type == "ARMATURE": modifier.object = spirit_rig
        for slot in spirit.material_slots:
            source_name = slot.material.name if slot.material else ""
            slot.link = "OBJECT"
            if "Eyes" in source_name or "pupil" in source_name:
                slot.material = ghost_eye
            elif "Armor" in source_name or "brass" in source_name or "jewel" in source_name:
                slot.material = ghost_armor
            elif "Drapery" in source_name or "Straps" in source_name:
                slot.material = ghost_cloth
            else:
                slot.material = ghost_skin
        spirit_rig.location = (x,y,0)
        spirit_rig.rotation_euler.z = math.atan2(-x,-4-y)
        growth = RELEASE+4+i
        key(spirit_rig, "scale", [(1,(.001,)*3),(growth-2,(.001,)*3),(growth+4,(.52,)*3),
                                   (END-10,(.52,)*3),(END,(.001,)*3)])
        key(spirit_rig, "location", [(growth-2,(x,y,-.12)),(growth+4,(x,y,.08)),
                                      (37,(x*.92,-4+(y+4)*.92,.10)),
                                      (57,(x,y,.06)),(END,(x,y,.6))])
        ghosts.append({"index":i+1,"x":round(x,4),"y":round(y,4),"material":"shared spectral materials"})

    petal = petal_mesh(pale)
    for i in range(15):
        a = math.tau*i/15
        obj = bpy.data.objects.new(f"Sena wind petal {i+1:02}", petal)
        effects.objects.link(obj)
        r = .7 + .13*(i%4)
        key(obj,"location",[(1,(.08,-.32,1.83)),(18,(.08,-.32,1.83)),
                             (RELEASE+16,(r*math.cos(a),-4+r*math.sin(a),.4+(i%3)*.2)),
                             (END,(1.8*r*math.cos(a),-4+1.8*r*math.sin(a),1.8+(i%4)*.3))])
        key(obj,"rotation_euler",[(18,(0,0,a)),(52,(a,2*a,3*a)),(END,(2*a,4*a,6*a))])
        key(obj,"scale",[(1,(.001,)*3),(RELEASE-1,(.001,)*3),(RELEASE+7,(.8,)*3),
                          (END-10,(.8,)*3),(END,(.001,)*3)])

    camera = bpy.data.objects["Portrait and action lens"]
    camera.animation_data_clear()
    camera.data.type = "ORTHO"
    # The windup needs an intentional close-up; cut to the wide tactical view
    # at release, so the entire zone and all five silhouettes are visible.
    for frame, location, look, width in [
        (1,(3.0,-6.0,2.8),(0,-.1,1.55),2.75),
        (RELEASE,(3.0,-6.0,2.8),(0,-.1,1.55),2.75),
        (RELEASE+1,(7.0,-9.5,6.5),(0,-2.5,1.05),8.4),
        (END+12,(7.0,-9.5,6.5),(0,-2.5,1.05),8.4),
    ]:
        camera.location = location
        aim(camera,look)
        camera.data.ortho_scale = width
        camera.keyframe_insert(data_path="location",frame=frame)
        camera.keyframe_insert(data_path="rotation_euler",frame=frame)
        camera.data.keyframe_insert(data_path="ortho_scale",frame=frame)
    for data in (camera.animation_data,camera.data.animation_data):
        for fc in data.action.fcurves:
            for point in fc.keyframe_points: point.interpolation = "CONSTANT"
    scene.camera = camera
    for label, frame in [("Call begins",1),("Release / 12th authority tick",RELEASE),
                         ("Spirit formation",30),("Five coordinated echoes",48),
                         ("Zone expires / 52nd authority tick",END)]:
        scene.timeline_markers.new(label, frame=frame)
    scene.frame_set(1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()), compress=True)
    receipt = {
        "scope":"Offline editable animation study; five skinned spectral echoes are not autonomous game agents or a new runtime clip.",
        "blender":bpy.app.version_string,"fps":FPS,"authority_hz":20,
        "scene_frames":{"start":1,"release":RELEASE,"recovery":RECOVERY,"field_end":END,"tail":END+12},
        "relative_seconds":{"release":(RELEASE-1)/FPS,"field_end":(END-1)/FPS},
        "zone_radius_m":RADIUS,"example_target_distance_m":4,"ghost_count":5,
        "source_scene_sha256":MASTER_SHA,"source_model_sha256":MODEL_SHA,"ability_profile_sha256":digest(PROFILE),
        "cast_action":action.name,"ghost_action":strike.name,"source_joints":len(rig.pose.bones),
        "ghosts":ghosts,"render_engine":"Cycles CPU, preview 4 samples, 640x360",
        "limitations":["Hand-to-hair proximity is a staged IK illustration, not a production contact solve.",
                       "Ghosts reuse the Hanuman rig and do not represent independent finalized characters.",
                       "Sound, balance, actual movement/collision and runtime imports require separate verification."]}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    main()
