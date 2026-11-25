"""Install three artist-only facial Actions on the shipped Hanuman in a separate Blender scene.

blender -b -t 2 --python-exit-code 1 -P face_actions.py -- --out /tmp/hanuman-expression-review
Run on an imported, unmodified enhanced GLB. install(rig, body) is also usable in a Blender script.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
import numpy as np
from PIL import Image, ImageDraw, ImageFont

THIS = Path(__file__).resolve().parent
PACK = THIS.parent
MODEL = PACK / "models/hanuman-enhanced.glb"
SHA = "6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a"
sys.path.insert(0, str(PACK / "render"))
from studio import init, camera_at, snap

BLINK = "Studio · Blink"
FOCUS = "Studio · Focus"
RECOVER = "Studio · Relaxed recovery"
KNOBS = {"lid": "studio_lid_fold", "brow": "studio_brow_focus", "mouth": "studio_mouth_relax"}
EYE_X, EYE_Y, EYE_Z = 0.0438413, -0.172916, 1.8856524
ZERO = Vector((0, 0, 0))
EYE_MATS = {"Eyes · dark amber iris", "Eyes · warm sclera"}
CORRECTIVES = ["Studio / fitted lid closure", "Studio / medial brow", "Studio / lip release"]


def clamp(v, lo=0.0, hi=1.0):
    return min(hi, max(lo, v))


def eased(a, b, v):
    t = clamp((v - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def local_group(obj, vertex, name):
    return sum(g.weight for g in vertex.groups if obj.vertex_groups[g.group].name == name)


def folded_lid(p, side, fold):
    """Fitted parametric outer lid (the donor's actual orbital ribbon + its upper lash ridge)."""
    # These two radii and lash slope come from the donor's orbital lid builder.
    dx = p.x - side * EYE_X
    dz = p.z - EYE_Z + 0.12 * side * dx
    if abs(dx) > 0.0314 or abs(dz) > 0.027 or not (-0.209 < p.y < -0.145):
        return p
    lo, hi = 0.0, 1.0
    for _ in range(14):
        m = (lo + hi) / 2
        ell = (dx / (0.020 + 0.009 * m)) ** 2 + (dz / (0.0083 + 0.016 * m)) ** 2
        if ell > 1:
            lo = m
        else:
            hi = m
    ring = (lo + hi) * 0.5 if not fold else 0.0
    sa = clamp(dz / (0.0083 + 0.016 * ring), -1.0, 1.0)
    if fold:
        sa = abs(sa)
    # Both margins meet slightly below centre. A small overlap also resolves subpixel cracks.
    fall = 1.0 - ring
    z = p.z - sa * 0.00865 * fall - 0.00165 * abs(sa) * fall - (0.00030 * fall if sa > 0 else 0)
    if fold:
        z -= 0.0003
    radius = 0.0302 if fold else 0.0298
    y_front = EYE_Y - math.sqrt(max(0.000006, radius * radius - dx * dx - (z - EYE_Z) ** 2))
    y = p.y + (y_front - p.y) * fall**0.70
    return Vector((p.x, y, z))


def setup_shapes(rig, ob):
    if not ob.data.shape_keys:
        ob.shape_key_add(name="Basis", from_mix=False)
    if any(ob.data.shape_keys.key_blocks.get(n) for n in CORRECTIVES):
        raise ValueError("Studio corrective shapes already exist")
    keys = [ob.shape_key_add(name=n, from_mix=False) for n in CORRECTIVES]
    mat_by_vert = {}
    for face in ob.data.polygons:
        name = ob.data.materials[face.material_index].name
        for i in face.vertices:
            mat_by_vert.setdefault(i, set()).add(name)
    counts = [0, 0, 0]
    for index, v in enumerate(ob.data.vertices):
        p = v.co.copy()
        side = 1 if p.x > 0 else -1
        mats = mat_by_vert.get(index, set())
        if not mats:
            continue
        if 0.010 < abs(p.x) < 0.083 and 1.855 < p.z < 1.916:
            is_lid = "Eyelids · roasted umber" in mats
            slit = "Face lines and pupil" in mats and local_group(ob, v, "head") > 0.995
            if is_lid or slit:
                target = folded_lid(p, side, slit)
                if (target - p).length > 1e-6:
                    keys[0].data[index].co = target
                    counts[0] += 1
        eyebrow = mats.intersection(
            {"Fur · dark copper clumps", "Hanuman | swept copper guard hair"}
        )
        if eyebrow and 0.012 < abs(p.x) < 0.099 and p.y < -0.105 and 1.895 < p.z < 1.930:
            f = (1.0 - eased(0.020, 0.097, abs(p.x))) * eased(1.895, 1.906, p.z)
            if f > 0.001:
                keys[1].data[index].co = p + Vector((-side * 0.0017 * f, 0, -0.0029 * f))
                counts[1] += 1
        if (
            mats.intersection({"Eyelids · roasted umber", "Face · warm recessed lines"})
            and 1.78 < p.z < 1.801
            and p.y < -0.19
            and abs(p.x) < 0.052
        ):
            f = eased(0.18, 0.24, -p.y) * (1.0 - eased(0.03, 0.052, abs(p.x)))
            keys[2].data[index].co = p + Vector((0, 0, -0.0012 * f))
            counts[2] += 1
    for key, prop in zip(keys, KNOBS.values()):
        rig[prop] = 0.0
        rig.id_properties_ui(prop).update(min=0, max=1, soft_min=0, soft_max=1)
        driver = key.driver_add("value").driver
        driver.type = "AVERAGE"
        var = driver.variables.new()
        var.name = "pose"
        var.type = "SINGLE_PROP"
        var.targets[0].id = rig
        var.targets[0].data_path = f'["{prop}"]'
    if min(counts) < 8:
        raise ValueError(f"Insufficient original facial surface coverage: {counts}")
    return counts


def translate(bone, vector):
    return bone.bone.matrix_local.to_3x3().normalized().inverted() @ Vector(vector)


def turn(bone, axis, degrees):
    return Quaternion(translate(bone, axis).normalized(), math.radians(degrees))


def make_action(rig, name, samples):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data.action = action
    for frame, strength in samples:

        def translate_key(name, displacement):
            b = rig.pose.bones[name]
            b.location = translate(b, np.asarray(displacement) * strength)
            b.keyframe_insert(data_path="location", frame=frame, group=name)

        def rotate_key(name, axis, amount):
            b = rig.pose.bones[name]
            b.rotation_mode = "QUATERNION"
            b.rotation_quaternion = turn(b, axis, amount * strength)
            b.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=name)

        for side in ("L", "R"):
            sign = 1 if side == "L" else -1
            if name == BLINK:
                rotate_key("orbicularis03." + side, (1, 0, 0), 2.7)
                rotate_key("orbicularis04." + side, (1, 0, 0), -1.2)
            elif name == FOCUS:
                rotate_key("eye." + side, (0, 0, 1), 4.5)
                translate_key("oculi01." + side, (-sign * 0.0008, 0, -0.0012))
                translate_key("oculi02." + side, (-sign * 0.0004, 0, -0.0006))
            else:
                translate_key("oris07." + side, (sign * 0.00055, 0, -0.00045))
        if name == RECOVER:
            rotate_key("jaw", (1, 0, 0), 0.75)
        keys = {BLINK: {"lid": 1}, FOCUS: {"lid": 0.12, "brow": 1}, RECOVER: {"mouth": 1}}[name]
        for short, magnitude in keys.items():
            prop = KNOBS[short]
            rig[prop] = strength * magnitude
            rig.keyframe_insert(data_path=f'["{prop}"]', frame=frame, group="Fitted surfaces")
    action.asset_mark()
    action.asset_data.description = {
        BLINK: "Upper and lower orbital actuation with a fitted lid-margin closure, then reopen.",
        FOCUS: "Medial brow set and a four-and-a-half degree binocular target shift.",
        RECOVER: "Closed-mouth lower-lip release and a three-quarter-degree jaw hinge, returning to rest.",
    }[name]
    for fc in action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
            k.handle_left_type = "AUTO_CLAMPED"
            k.handle_right_type = "AUTO_CLAMPED"
    return action


def neutral(rig):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for name in KNOBS.values():
        rig[name] = 0.0
    bpy.context.view_layer.update()


def install(rig, body, library=None):
    if len(rig.data.bones) != 167 or not all(
        s in rig.pose.bones for s in ("orbicularis03.L", "oculi01.R", "oris07.L", "jaw")
    ):
        raise ValueError("Requires the pinned YUGA Hanuman 167-joint rig")
    for track in rig.animation_data_create().nla_tracks:
        track.mute = True
    if any(bpy.data.actions.get(n) is not None for n in (BLINK, FOCUS, RECOVER)):
        raise ValueError("The motion library is already installed")
    neutral(rig)
    counts = setup_shapes(rig, body)
    actions = {}
    if library:
        with bpy.data.libraries.load(str(library), link=False) as (available, loaded):
            names = (BLINK, FOCUS, RECOVER)
            if not all(n in available.actions for n in names):
                raise ValueError("Incomplete face action library")
            loaded.actions = list(names)
        return {a.name: a for a in loaded.actions}, counts
    for name, frames in (
        (BLINK, [(1, 0), (4, 1), (6, 1), (12, 0)]),
        (FOCUS, [(1, 0), (9, 1), (18, 1), (28, 0)]),
        (RECOVER, [(1, 0), (8, 1), (13, 0.75), (26, 0)]),
    ):
        neutral(rig)
        actions[name] = make_action(rig, name, frames)
    neutral(rig)
    return actions, counts


def evaluate(rig, act, frame):
    neutral(rig)
    rig.animation_data.action = act
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


def sample_eye(ob):
    deps = bpy.context.evaluated_depsgraph_get()
    obj = ob.evaluated_get(deps)
    mesh = obj.data
    xyz = np.zeros(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", xyz)
    xyz = xyz.reshape(-1, 3)
    mask = (abs(xyz[:, 0]) < 0.1) & (xyz[:, 2] > 1.84) & (xyz[:, 2] < 1.94)
    faces = []
    eye = []
    for f in ob.data.polygons:
        ids = list(f.vertices)
        if not any(mask[ids]):
            continue
        name = mesh.materials[f.material_index].name
        pupil = name == "Face lines and pupil" and any(
            sum(local_group(ob, ob.data.vertices[i], n) for n in ("eye.L", "eye.R")) > 0.9
            for i in ids
        )
        faces.append(ids)
        eye.append(name in EYE_MATS or pupil)
    tree = BVHTree.FromPolygons(xyz.tolist(), faces, all_triangles=True)
    out = {}
    for s in (-1, 1):
        n = 0
        for dx in np.linspace(-0.018, 0.018, 36):
            for dz in np.linspace(-0.010, 0.010, 22):
                _, _, idx, _ = tree.ray_cast(
                    Vector((s * EYE_X + dx, -0.50, EYE_Z + dz)), Vector((0, 1, 0)), 0.50
                )
                n += int(idx is not None and eye[idx])
        out["L" if s == 1 else "R"] = n
    return out


def region_bounds(rig):
    return {
        n: np.asarray(rig.pose.bones[n].matrix).copy()
        for n in ("neck01", "neck02", "neck03", "head", "jaw", "eye.L", "eye.R")
    }


def lookbook(tmp, output):
    paths = [tmp / (s + ".png") for s in ("neutral", "blink", "focus", "recover")]
    shots = [Image.open(p).convert("RGB") for p in paths]
    w, h = shots[0].size
    pad = 14
    label = 56
    sheet = Image.new("RGB", (2 * w + 3 * pad, 2 * (h + label) + 3 * pad), "#182328")
    d = ImageDraw.Draw(sheet)
    fontfile = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(fontfile, 17) if Path(fontfile).exists() else ImageFont.load_default()
    small = (
        ImageFont.truetype(fontfile, 13) if Path(fontfile).exists() else ImageFont.load_default()
    )
    captions = [
        ("Neutral rig", "Rest pose"),
        ("Blink", "F4  ·  upper lid meets lower lid"),
        ("Focus", "F9  ·  eyes turn 4.5° to character left"),
        ("Relaxed recovery", "F8  ·  soft jaw and lower lip"),
    ]
    for i, (img, (title, sub)) in enumerate(zip(shots, captions)):
        x = pad + (i % 2) * (w + pad)
        y = pad + (i // 2) * (h + label + pad)
        sheet.paste(img, (x, y))
        d.text((x, y + h + 6), title, font=font, fill="#ffffff")
        d.text((x, y + h + 31), sub, font=small, fill="#c0d2d2")
    sheet.save(output, "WEBP", quality=93, method=6)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=THIS)
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument(
        "--scene",
        type=Path,
        help="Save a separate artist .blend with the rig, fitted shapes and actions installed",
    )
    ap.add_argument("--size", type=int, default=360)
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument(
        "--use-library", type=Path, help="Prepare a fresh model and append the three stored actions"
    )
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    if hashlib.sha256(MODEL.read_bytes()).hexdigest() != SHA:
        raise ValueError("Unexpected donor")
    import tempfile

    args.out.mkdir(exist_ok=True, parents=True)
    scene, rig, cam, lights = init(MODEL, args.threads, args.samples, False)
    (ob,) = [
        o
        for o in scene.objects
        if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == rig for m in o.modifiers)
    ]
    actions, counts = install(rig, ob, args.use_library)
    scene.render.fps = 30
    camera_at(cam, lights, 6, 1, (0, -0.10, 1.875), 0.305)
    neutral(rig)
    baseline = region_bounds(rig)
    neutral_px = sample_eye(ob)
    # An ablation on the actual rig establishes why the imported orbital surface needs the
    # corrective: keep both orbicularis tracks active and temporarily disable only the lid shape.
    evaluate(rig, actions[BLINK], 4)
    margin = ob.data.shape_keys.key_blocks[CORRECTIVES[0]]
    margin.mute = True
    bpy.context.view_layer.update()
    bones_only = sample_eye(ob)
    margin.mute = False
    neutral(rig)
    if min(bones_only.values()) < 50:
        raise ValueError(
            "Recheck donor anatomy: the orbital bones alone now appear to close the eye"
        )
    result = {}
    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        for short, name, peak in [
            ("neutral", None, 1),
            ("blink", BLINK, 4),
            ("focus", FOCUS, 9),
            ("recover", RECOVER, 8),
        ]:
            if name:
                evaluate(rig, actions[name], peak)
            else:
                neutral(rig)
            eye = sample_eye(ob)
            bounds = region_bounds(rig)
            protected = ["neck01", "neck02", "neck03", "head"]
            if name != RECOVER:
                protected.append("jaw")
            if name != FOCUS:
                protected += ["eye.L", "eye.R"]
            drift = max(float(np.max(np.abs(bounds[n] - baseline[n]))) for n in protected)
            if drift > 1e-6:
                raise ValueError(f"{short} moved a protected joint ({drift})")
            result[short] = {
                "frame": peak,
                "visible_eye_rays": eye,
                "protected_max_matrix_delta": drift,
                "shape_values": {s: round(float(rig[n]), 5) for s, n in KNOBS.items()},
                "relative_rotation_degrees": {
                    n: round(
                        math.degrees(
                            Quaternion(np.asarray(rig.pose.bones[n].rotation_quaternion)).angle
                        ),
                        4,
                    )
                    for n in ("jaw", "eye.L", "eye.R")
                },
            }
            print(short, result[short], flush=True)
            if not args.skip_render:
                snap(scene, tmp / (short + ".png"), (args.size, int(args.size * 0.80)))
        for name, action in actions.items():
            evaluate(rig, action, int(action.frame_range[1]))
            if max(abs(float(rig[k])) for k in KNOBS.values()) > 2e-6:
                raise ValueError(f"{name} did not release its corrective at the final frame")
            for n, base in baseline.items():
                if np.max(np.abs(np.asarray(rig.pose.bones[n].matrix) - base)) > 2e-6:
                    raise ValueError(f"{name} failed neutral return at {n}")
        if not args.skip_render:
            lookbook(tmp, args.out / "face-contact-sheet.webp")
    if min(neutral_px.values()) < 100 or max(result["blink"]["visible_eye_rays"].values()) > 4:
        raise ValueError(f"Full blink did not close the real eye aperture: {result}")
    actionfile = args.out / "hanuman-face-actions.blend"
    if args.use_library is None:
        bpy.data.libraries.write(
            str(actionfile), set(actions.values()), fake_user=True, compress=True
        )
    else:
        actionfile = args.use_library
    if args.scene is not None:
        if args.scene.resolve() in (actionfile.resolve(), MODEL.resolve()):
            raise ValueError("Choose a new .blend file for the artist study")
        args.scene.parent.mkdir(parents=True, exist_ok=True)
        evaluate(rig, actions[BLINK], 1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(args.scene.resolve()), compress=True)
    record = {
        "source_sha256": SHA,
        "blender": bpy.app.version_string,
        "fps": 30,
        "render_samples": None if args.skip_render else args.samples,
        "capture_size": None if args.skip_render else [args.size, int(args.size * 0.8)],
        "action_library_sha256": hashlib.sha256(actionfile.read_bytes()).hexdigest(),
        "source_file_unchanged": hashlib.sha256(MODEL.read_bytes()).hexdigest() == SHA,
        "blink_without_lid_corrective_visible_eye_rays": bones_only,
        "grid_rays_per_eye": 36 * 22,
        "corrective_vertices": dict(zip(CORRECTIVES, map(int, counts))),
        "observations": result,
        "actions": {
            name: {"frames": list(map(int, a.frame_range)), "curves": len(a.fcurves)}
            for name, a in actions.items()
        },
    }
    (args.out / "verification.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
