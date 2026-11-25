"""Reference-frame wardrobe on the existing weighted Hanuman rig.

Build under the active working scene. Each new adornment uses the character's
rest coordinates. The pose and camera are owned by the master shot recipe.
"""
from __future__ import annotations

from bisect import bisect_right
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

PIPELINE = Path(__file__).resolve().parents[3] / "yuga/art/pipeline"
sys.path.insert(0, str(PIPELINE))
from geometry import Sculpt

TAU = math.tau
HIDE = (
    "Split pleated battle drape", "Saffron selvedge", "Central red sash end",
    "Central stitched edge", "Central stitched hem", "Layered hide belt",
    "Cast belt piping", "Belt medallion", "Inset lotus seal",
    "Cuirass · continuous", "Bound bronze cuirass side", "Chased chest shell edge",
    "Shallow cast ribs", "Heart seal engraved socket", "Heart seal carnelian stone",
    "Sacred braided cord", "Layered bronze shoulder", "Shoulder chased lip",
    "Shoulder brass rivet", "Tapered bracer", "Bracer rolled rim",
    "Wrist chased ornament", "Bound greave cuff", "Greave bead edge",
    "Sandal soles", "Sandal leather straps", "Ankle bronze cording",
    "Vajra Gada ·", "Twined grip ring", "Haft collars",
    "Repoussé weapon bands", "Crown petals", "Vajra ember rivet",
    "Tail bronze binding", "Sweep at tail tip",
)


def smoothstep(low, high, value):
    t = min(1.0, max(0.0, (value - low) / (high - low)))
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, weight):
    return a + (b - a) * weight


def soft_fit(body, center, radial, expected, spread, weight):
    # From inside outward, take the first skin surface. A finished outline
    # must never jump to the opposite leg or a hand crossing this ray.
    hit, point, _, _ = body.ray_cast(center, radial, distance=expected + spread + .02)
    measured = (point - center).dot(radial) if hit else expected
    measured = max(expected - spread, min(expected + spread, measured))
    return mix(expected, measured, weight)


def ellipse_radius(x, y, a):
    return 1 / math.hypot(math.sin(a) / x, math.cos(a) / y)


def tagged_name(obj):
    return obj.name.removeprefix("LookDev - ").removeprefix("Match - ")


def working_copy(obj):
    if obj.data.users > 1:
        obj.data = obj.data.copy()


def body_shape(rig, body):
    names = {group.index: group.name for group in body.vertex_groups}
    weights = [
        [(names[group.group], group.weight) for group in vertex.groups if group.weight]
        for vertex in body.data.vertices
    ]
    tree = KDTree(len(body.data.vertices))
    for vertex in body.data.vertices:
        tree.insert(vertex.co, vertex.index)
    tree.balance()
    return Sculpt(rig, body, weights, tree)


def transfer_body_weights(sculpt, obj):
    """Interpolate donor deformation at the cloth location with the body KD tree."""
    obj.vertex_groups.clear()
    groups = {}
    for vertex in obj.data.vertices:
        joined = {}
        for _, index, distance in sculpt.tree.find_n(vertex.co, 7):
            influence = 1 / max(distance, .006) ** 3
            for name, weight in sculpt.weights[index]:
                joined[name] = joined.get(name, 0.0) + influence * weight
        selected = sorted(joined.items(), key=lambda entry: entry[1], reverse=True)[:4]
        total = sum(weight for _, weight in selected)
        for name, weight in selected:
            if name not in groups:
                groups[name] = obj.vertex_groups.new(name=name)
            groups[name].add([vertex.index], weight / total, "REPLACE")


def surface_material(name, dark, light, metallic, roughness, coarse, fine, depth, *, chased=False):
    mat = bpy.data.materials.new("Reference wardrobe · " + name)
    mat.diffuse_color = (*dark, 1.0)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    tex = nodes.new("ShaderNodeTexCoord")
    patina = nodes.new("ShaderNodeTexNoise")
    patina.inputs["Scale"].default_value = coarse
    patina.inputs["Detail"].default_value = 4.0
    patina.inputs["Roughness"].default_value = 0.64
    grain = nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = fine
    grain.inputs["Detail"].default_value = 2.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].position = 0.77
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    relief = nodes.new("ShaderNodeBump")
    relief.inputs["Distance"].default_value = depth
    relief.inputs["Strength"].default_value = 0.24
    rough = nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = max(0.1, roughness - 0.13)
    rough.inputs["To Max"].default_value = min(0.96, roughness + 0.12)
    links.new(tex.outputs["Object"], patina.inputs["Vector"])
    links.new(tex.outputs["Object"], grain.inputs["Vector"])
    links.new(patina.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(patina.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], shader.inputs["Roughness"])
    links.new(grain.outputs["Fac"], relief.inputs["Height"])
    links.new(relief.outputs["Normal"], shader.inputs["Normal"])
    if chased:
        # Use the garment UV tangent instead of a world direction. The fine
        # tool marks stay on each plate as the rig moves or the asset rotates.
        tool_marks = nodes.new("ShaderNodeVectorMath")
        tool_marks.operation = "MULTIPLY"
        tool_marks.inputs[1].default_value = (2.8, .42, 1.0)
        links.new(tex.outputs["UV"], tool_marks.inputs[0])
        links.new(tool_marks.outputs[0], grain.inputs["Vector"])
        shader.inputs["Anisotropic"].default_value = .21
        shader.inputs["Specular IOR Level"].default_value = .36
        ramp.color_ramp.elements[0].position = .31
        ramp.color_ramp.elements[1].position = .69
        ramp.color_ramp.elements.new(.53).color = tuple(mix(a, b, .34) for a, b in zip(dark, light)) + (1.0,)
    return mat


def fabric(path):
    mat = surface_material("handwoven madder", (.044, .0045, .0035), (.164, .019, .011),
                           0, .78, 14, 950, .0026)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Sheen Weight"].default_value = .23
    shader.inputs["Specular IOR Level"].default_value = .29
    if path and Path(path).is_file():
        swatch = bpy.data.images.load(str(Path(path).resolve()), check_existing=True)
        if not swatch.packed_file:
            swatch.pack()
        tex = nodes.new("ShaderNodeTexImage")
        tex.name = "Pinned madder weave"
        tex.image = swatch
        tex.extension = "REPEAT"
        uv = nodes.new("ShaderNodeTexCoord")
        frequency = nodes.new("ShaderNodeVectorMath")
        frequency.operation = "SCALE"
        frequency.inputs["Scale"].default_value = 2.4
        pigment = nodes.new("ShaderNodeMixRGB")
        pigment.blend_type = "MULTIPLY"
        pigment.inputs[0].default_value = 1
        pigment.inputs[2].default_value = (.51, .125, .092, 1)
        links.new(uv.outputs["UV"], frequency.inputs[0])
        links.new(frequency.outputs[0], tex.inputs["Vector"])
        links.new(tex.outputs["Color"], pigment.inputs[1])
        links.new(pigment.outputs[0], shader.inputs["Base Color"])
        bump = next(node for node in nodes if node.type == "BUMP")
        links.new(tex.outputs["Color"], bump.inputs["Height"])
    return mat


def palette(profile):
    return {
        "cloth": fabric(profile.get("cloth_texture")),
        "border": surface_material("dyed woven hems", (.078, .024, .008), (.19, .065, .022),
                                   0.05, .69, 21, 760, .0023),
        "bronze": surface_material("hammered patinated bronze", (.051, .028, .014), (.264, .144, .067),
                                   .57, .55, 17, 270, .00185, chased=True),
        "recess": surface_material("oxidized engraving grooves", (.029, .018, .010), (.115, .064, .030),
                                   .48, .60, 30, 430, .0011, chased=True),
        "gold": surface_material("cast brass edges", (.173, .079, .025), (.50, .263, .083),
                                 .54, .50, 20, 340, .0011, chased=True),
        "grip": surface_material("oiled cord grip", (.021, .010, .008), (.052, .024, .015),
                                 .04, .64, 19, 820, .0017),
        "stone": surface_material("polished carnelian", (.22, .021, .010), (.64, .118, .028),
                                  .26, .23, 43, 220, .0007),
        "tuft": surface_material("dark chestnut tuft", (.012, .0027, .0015), (.111, .020, .006),
                                 0, .53, 20, 520, .00095),
        "tuft_light": surface_material("auburn plume guard hairs", (.034,.007,.0025), (.154,.042,.013),
                                       0, .53, 21, 510, .0007),
        "tail": surface_material("copper tail coat", (.071,.020,.007), (.247,.080,.028),
                                 0,.59,20,550,.0013),
        "tail_light": surface_material("warm copper rim hair", (.112,.031,.009), (.332,.114,.037),
                                       0, .60, 19, 470, .0007),
    }


def dress(sculpt, mat, length):
    rig = sculpt.rig
    for side, sign in (("L", 1), ("R", -1)):
        hip = rig.data.bones["upperleg01." + side].head_local
        knee = rig.data.bones["lowerleg01." + side].head_local
        shin = rig.data.bones["lowerleg02." + side].head_local

        def leg(u, t, phase=sign * .47):
            a = TAU * u
            z = 1.106 - length * t + .057 * t ** 8 * (1 - math.cos(a + sign * .32))
            center = hip.lerp(knee, min(1, max(0, (1.06 - z) / (1.06 - knee.z))))
            if z < knee.z:
                center = knee.lerp(shin, (knee.z - z) / (knee.z - shin.z))
            center.z = z
            radial = Vector((math.sin(a), -math.cos(a), 0))
            prior = ellipse_radius(mix(.145, .087, t), mix(.199, .099, t), a)
            body_radius = soft_fit(sculpt.body, center, radial, prior, .043, .29)
            sweep = a * 7 - t * 9.1 + phase
            gather = (
                .016 * math.cos(sweep)
                + .018 * (max(0.0, math.sin(sweep)) ** 4)
                + .009 * (max(0.0, math.cos(a * 11 + t * 5.2)) ** 2)
            )
            fullness = math.sin(math.pi * min(1, t)) ** .8
            knee_support=.044*math.exp(-((z-knee.z)/.105)**2)*max(0,math.cos(a))**2
            return center + radial * (body_radius + .034 + fullness * (.047 + gather) + knee_support)

        bone = "upperleg01." + side
        folds = sculpt.cloth("Ref · gathered dhoti leg " + side, leg, mat["cloth"],
                            rows=64, columns=88, wrap=True, bone=bone)
        # Blend on the actual donor joints. A linear thigh/shin blend left
        # skin breakthrough on the bent knees in the first test shot.
        transfer_body_weights(sculpt, folds)
        hem_bone = "lowerleg01." + side
        hem=sculpt.cloth("Ref · deep embroidered hem " + side,
                     lambda u, v: leg(u, .920 + v * .080) + Vector((math.sin(TAU*u), -math.cos(TAU*u), 0))*.0045,
                     mat["border"], rows=7, columns=88, wrap=True, bone=hem_bone)
        transfer_body_weights(sculpt, hem)
        for bounds in (.929, .984):
            thread=sculpt.tube("Ref · doubled hem thread " + side,
                               [leg(k / 96, bounds) + Vector((math.sin(TAU*k/96), -math.cos(TAU*k/96), 0))*.006
                                for k in range(97)], .0024, mat["gold"], hem_bone, 6)
            transfer_body_weights(sculpt, thread)
        for stitch in range(38):
            seam = [(stitch + offset) / 38 for offset in (0, .13, .22, .35)]
            points = [
                leg(u, v) + Vector((math.sin(TAU*u), -math.cos(TAU*u), 0)) * .007
                for u, v in zip(seam, (.946, .968, .968, .946))
            ]
            thread = sculpt.tube("Ref · embroidered chevron " + side, points, .00095, mat["gold"], hem_bone, 5)
            transfer_body_weights(sculpt, thread)

        def draped(u, v):
            # Broad fabric spirals from buckle to outer kneewrap: the front
            # fan sits over the ballooned under-folds on the same weighted leg.
            a = sign * (.10 + .92 * v + (u - .45) * (.76 + .57 * v))
            p = leg((a / TAU) % 1.0, .03 + .72 * v)
            radial = Vector((math.sin(a), -math.cos(a), 0))
            lift = .009 + .015 * smoothstep(.02,.26,v) + .007 * math.cos(TAU * (u * 3.7 + v * .61)) + .009 * u
            p += radial * lift
            p.z += .046 * (1.0 - u) * v
            return p

        panel = sculpt.cloth("Ref · diagonal hip fold " + side, draped, mat["cloth"],
                            rows=42, columns=30, bone=bone)
        thick = panel.modifiers.new("Woven edge thickness · 2mm", "SOLIDIFY")
        thick.thickness = .002
        for s in (.025, .08, .965):
            sculpt.tube("Ref · draped selvedge " + side,
                        [draped(s, k/48) for k in range(49)], .0019,
                        mat["gold"] if s != .08 else mat["border"], bone, 6)

    def front(u, v):
        x = (u - .5) * (.219 - .029 * v)
        z = 1.122 - .481 * v + .066 * v ** 8 * abs(2 * u - 1) ** 1.7
        y = -.238 - .038 * math.sin(math.pi * v * .92)
        y -= .011 * (math.cos(TAU * u * 3.0 + v * 1.6) + .38 * math.cos(TAU*u*5))
        return Vector((x, y, z))

    s = sculpt
    def lining(u, v):
        point = front(u, v)
        point.x *= 1.14
        point.y += .016 - .02 * v
        point.z -= .14 * v
        return point
    s.cloth("Ref · inner crossover tabard", lining, mat["cloth"], rows=34, columns=29, bone="spine05")
    s.tube("Ref · inner tabard brocade edge", [lining(j/44, .979) for j in range(45)],
           .0032, mat["border"], "spine05", 7)
    s.cloth("Ref · hanging center panel", front, mat["cloth"], rows=49, columns=32, bone="spine05")
    for p in (.056, .105, .895, .944):
        s.tube("Ref · tabard woven pinstripe",
               [front(p, j/68) + Vector((0,-.002,0)) for j in range(69)],
               .00165, mat["gold"] if p in (.056,.944) else mat["border"], "spine05", 6)
    s.tube("Ref · pointed tabard hem", [front(j / 48, .988) for j in range(49)],
           .0022, mat["gold"], "spine05", 7)
    lotus = front(.5, .81) + Vector((0,-.013, .010))
    engraved_lotus(s, lotus, Vector((1,0,0)), Vector((0,0,1)), .072, mat["gold"], "spine05")


def engraved_lotus(s, center, x, y, width, mat, bone):
    for bend in (-.74, -.39, 0.0, .39, .74):
        petals = []
        for i in range(27):
            t = i / 26
            along = 2 * t if t <= .5 else 2 * (1 - t)
            sign = 1 if t <= .5 else -1
            spread = sign * .16 * math.sin(math.pi * along)
            petals.append(center + width * (
                x * (bend * along + spread) + y * ((.62 - .31 * abs(bend)) * along)))
        s.tube("Ref · lotus chased petal", petals, .00165, mat, bone, 6)


def set_stone(s, label, center, normal, across, radii, mat, bone):
    """Cast an oval setting into its support and lay a low cabochon in it."""
    axis = (across - normal * across.dot(normal)).normalized()
    tangent = normal.cross(axis)
    width, height, dome = radii

    def ring(u, size, offset):
        a = TAU*u
        return center + (axis*(width*math.cos(a)) + tangent*(height*math.sin(a)))*size + normal*offset

    rim = ((1.01,-.004),(1.00,.001),(1.04,.004),(.96,.007),(.82,.007),(.76,.004),(.70,.001))
    s.cloth("Ref · cast bezel "+label,
            lambda u,v: ring(u,*rim[round(v*(len(rim)-1))]),
            mat["gold"], rows=len(rim)-1, columns=48, wrap=True, bone=bone)
    def jewel(u,v):
        pitch = math.pi*v/2
        return ring(u, .77*max(.0005,math.cos(pitch)), .0033+dome*math.sin(pitch))
    s.cloth("Ref · inset carnelian "+label,jewel,mat["stone"],
            rows=14, columns=48, wrap=True, bone=bone)


def fit_torso_weights(s, objects):
    """Keep the cast plate and its fine relief on the same torso chain."""
    bones = [s.rig.data.bones[f"spine0{i}"] for i in (4,3,2,1)]
    heights = [bone.head_local.z for bone in bones]
    for obj in objects:
        obj.vertex_groups.clear()
        groups = [obj.vertex_groups.new(name=bone.name) for bone in bones]
        for vertex in obj.data.vertices:
            upper = bisect_right(heights,vertex.co.z)
            if upper == 0 or upper == len(bones):
                groups[min(upper,len(bones)-1)].add([vertex.index],1.0,"REPLACE")
                continue
            lower = upper-1
            above = smoothstep(heights[lower],heights[upper],vertex.co.z)
            groups[lower].add([vertex.index],1-above,"REPLACE")
            groups[upper].add([vertex.index],above,"REPLACE")


def cuirass(s, mat):
    rib_heights = (.21, .38, .56, .72)
    first_component = len(s.objects)

    def rise(u):
        wing = abs(u-.5)*2
        return .119 * wing ** .62 - .019 * math.sin(TAU*wing)

    def shell(u, v):
        a = (u - .5) * 3.78
        wing = abs(a) / 1.89
        z = mix(1.174 + .044 * wing ** 1.5,
                1.667 - .075 * math.exp(-(a / .63) ** 2) - .025 * wing ** 3,
                v)
        center = Vector((0, .014, z))
        ray = Vector((math.sin(a), -math.cos(a), 0))
        prior = ellipse_radius(mix(.203, .302, math.sin(v*math.pi/2)),
                               mix(.197, .153, smoothstep(.66,1,v)) + .025*math.sin(v*math.pi), a)
        distance = sum(
            soft_fit(s.body, center, Vector((math.sin(a+d), -math.cos(a+d), 0)),
                     prior, .062, .53)*weight
            for d, weight in ((-.10, .22), (0, .56), (.10, .22))
        )
        protrusion = .029 + .037 * math.sin(math.pi * v) * (1 - .47 * wing)
        p = center + ray * (distance + protrusion)
        if abs(a) < 1.48:
            # Protect the forward muscles from intersecting the plate.
            # Avoid the arm at the outer taper and allow the sculpt stage
            # to adjust muscle volume before this shell is built.
            depths = []
            for dx, weight in ((-.012,.20),(0,.60),(.012,.20)):
                hit, q, _, _ = s.body.ray_cast((p.x+dx,-.49,z),(0,1,0),distance=.46)
                depths.append((max(-.34,q.y) if hit else p.y)*weight)
            skin_y = sum(depths)
            front = 1-smoothstep(1.16,1.48,abs(a))
            p.y = mix(p.y,min(p.y,skin_y-.026-.024*math.sin(math.pi*v)),front)
        rib_u = (u-.074)/.852
        if 0 < rib_u < 1:
            lip = min(abs(v-(height+rise(rib_u))) for height in rib_heights)
            p -= ray*.0036*math.exp(-(lip/.016)**2)*math.sin(math.pi*rib_u)**.42
        return p

    plate = s.cloth("Ref · dark forged cuirass", shell, mat["bronze"], rows=84, columns=92)
    solid = plate.modifiers.new("Plate thickness · 5mm", "SOLIDIFY")
    solid.thickness = .005
    for furthest in (.021, .982):
        s.tube("Ref · rolled horizontal breastplate edge",
               [shell(j/84,furthest) for j in range(85)], .0042, mat["gold"], sides=8)
    for u in (.014, .986, .50):
        s.tube("Ref · raised torso ridge", [shell(u,j/60) for j in range(61)],
               .0034, mat["gold"], sides=8)
    for r in rib_heights:
        def seam(u, offset=0):
            return shell(mix(.074, .926, u), r + rise(u) + offset)
        s.tube("Ref · shaded fold beneath armor seam",
               [seam(k/72,-.008) for k in range(73)],.0033,mat["recess"],sides=7)
        s.tube("Ref · cast winged armor seam", [seam(k/62) for k in range(63)],
               .0025, mat["gold"], sides=8)
        for u in (.115,.215,.785,.885):
            p = seam(u) + Vector((0,-.002,.017))
            s.ellipsoid("Ref · hammered chest stud", p, (.0035,.0022,.0035), mat["gold"], None, 10, 6)
    for direction in (-1,1):
        for row, base in enumerate((.287,.456,.633,.797)):
            def chased(u,v):
                return shell(.5+direction*u,v) + Vector((0,-.0013,0))
            for branch in (-1,1):
                points = []
                for i in range(25):
                    t = i/24
                    u = .104 + .156*t
                    v = base + .094*t + .018*branch*math.sin(math.pi*t)
                    points.append(chased(u,v))
                s.tube("Ref · mirrored brass leaf chase",points,.0012,mat["gold"],sides=6)
            if row == 3:
                for leaf in range(4):
                    u = .115+.035*leaf
                    mark = [chased(u+.028*t, base+.023*leaf+.023*math.sin(math.pi*t)) for t in (i/14 for i in range(15))]
                    s.tube("Ref · inset chest foliage veins",mark,.00086,mat["gold"],sides=5)
    heart = shell(.50,.788)
    heart_up = shell(.5,.808)-shell(.5,.768)
    across = Vector((1,0,0))
    set_stone(s, "heart", heart, across.cross(heart_up).normalized(), across,
              (.032,.046,.018),mat,"spine01")
    fit_torso_weights(s,s.objects[first_component:])

    def buckle_body(u,v):
        a=TAU*u
        z=1.075+.087*v
        radial=Vector((math.sin(a),-math.cos(a),0))
        center=Vector((0,.013,z))
        prior = ellipse_radius(.213, .208 if math.cos(a)>0 else .144, a)
        radius = soft_fit(s.body, center, radial, prior, .034, .35)
        return center + radial * (radius + .036 + .006*math.sin(math.pi*v))

    s.cloth("Ref · cast bronze waist belt", buckle_body, mat["bronze"], rows=10, columns=88, wrap=True, bone="spine05")
    for v in (.025,.10,.88,.985):
        s.tube("Ref · belt struck lip", [buckle_body(k/90,v) for k in range(91)],
               .004 if v in (.025,.985) else .0016, mat["gold"], "spine05", 7)
    for j in range(15):
        a=(j-7)/29
        p=buckle_body(a,.50)
        s.ellipsoid("Ref · belt stud", p, (.006,.005,.006), mat["gold"], "spine05", 12, 8)
    # Use the actual cloth depth to keep the buckle ahead of the beginnning of the tabard.
    center=Vector((0,min(-.252,buckle_body(0,.51).y-.009),1.122))
    s.ellipsoid("Ref · round carved belt buckle",center,(.058,.018,.061),mat["bronze"],"spine05",40,16)
    ring = [center+Vector((.051*math.sin(TAU*i/64),-.018,.052*math.cos(TAU*i/64))) for i in range(65)]
    s.tube("Ref · round buckle gold rim", ring,.0034,mat["gold"],"spine05",8)
    engraved_lotus(s,center+Vector((0,-.020,-.013)),Vector((1,0,0)),Vector((0,0,1)),.047,mat["gold"],"spine05")


def guards(s, mat):
    for side, sign in (("L",1), ("R",-1)):
        shoulder = s.rig.data.bones["upperarm01." + side]
        center = shoulder.head_local + Vector((sign * .064, -.013, -.041))

        def plate(u, t):
            yaw = TAU*u
            pitch = .015 + t*(1.63+.28*math.cos(yaw))
            wiggle = .003 * t*t*math.cos(7*yaw)
            return center+Vector((
                (.178+wiggle)*math.sin(pitch)*math.cos(yaw),
                (.165+wiggle)*math.sin(pitch)*math.sin(yaw),
                .142*math.cos(pitch)-sign*.036*math.sin(pitch)*math.cos(yaw),
            ))

        shell = s.cloth("Ref · domed fitted pauldron " + side, plate, mat["bronze"],
                        rows=23, columns=67, wrap=True, bone=shoulder.name)
        solid = shell.modifiers.new("Forged shoulder shell", "SOLIDIFY")
        solid.thickness = .004
        for v in (.775,.861,.972):
            s.tube("Ref · pauldron carved lip " + side, [plate(k/72,v) for k in range(73)],
                   .006 if v > .9 else .0025, mat["gold"], shoulder.name, 8)
        for index in range(9):
            u = (index + .5) / 9
            ridge = [plate(u, .29+.46*j/15) + Vector((0,0,.003)) for j in range(16)]
            s.tube("Ref · fine radiating shoulder chase " + side,
                   ridge, .00115, mat["gold"], shoulder.name, 5)
        for index in range(10):
            p = plate(index / 10, .89)
            s.ellipsoid("Ref · low domed pauldron rivet",p,(.006,.006,.006),
                        mat["gold"],shoulder.name,12,7)

        for role, bone, percent, half, width in (
            ("lotus forearm bracer", "lowerarm02." + side, .48, .081, .078),
            ("narrow bronze ankle cuff", "lowerleg02." + side, .69, .047, .062),
        ):
            section = s.rig.data.bones[bone]
            point = section.head_local.lerp(section.tail_local, percent)
            up = (section.head_local - section.tail_local).normalized()
            east = up.cross(Vector((0,-1,0))).normalized()
            if east.length < .01:
                east = up.cross(Vector((1,0,0))).normalized()
            south = east.cross(up)
            def rim(u,t):
                a=TAU*u
                radial = east*math.sin(a)+south*math.cos(a)
                p = point + up*(2*t-1)*half
                bound=soft_fit(s.body,p,radial,width,.043,.56)
                return p+radial*(bound+.015+.005*math.sin(math.pi*t) + .0025*math.cos(a*4))
            s.cloth("Ref · "+role+" "+side, rim, mat["bronze"], rows=18, columns=62, wrap=True, bone=bone)
            for v in (.018,.148,.855,.985):
                s.tube("Ref · stepped wrist and ankle beading", [rim(j/76,v) for j in range(77)],
                       .0044 if v in (.018,.985) else .00165, mat["gold"],bone,7)
            # Chase the actual cuff surface on all sides so a posed wrist
            # cannot hide every motif behind the front of a rest-pose plane.
            for panel in range(4):
                for bend in (-.79,-.39,0,.39,.79):
                    petals = []
                    for change in range(23):
                        t = change / 22
                        along = 1 - abs(2*t-1)
                        theta = panel/4 + .066*bend*along + .012*math.sin(TAU*t)
                        z = .29 + (.43-.21*abs(bend))*along
                        surface = rim(theta,z)
                        normal = east*math.sin(TAU*theta) + south*math.cos(TAU*theta)
                        petals.append(surface + normal*.0015)
                    s.tube("Ref · cuff chased lotus petals",petals,.0018,mat["gold"],bone,5)


def weapon(s, mat, reference):
    wrist=s.rig.data.bones["wrist.R"]
    # Existing R5 right-palm contact offset, preserved in wrist space.
    pivot = Vector((0.0,.11465,.02730))
    head_center = float(reference.get("mace_head_center_m", .632))
    radius = float(reference.get("mace_head_radius_m", .232))
    if not .54 <= head_center <= .96 or not .15 <= radius <= .34:
        raise ValueError("Mace proportions fall outside the editorial fit bounds")
    def point(along, theta=0.0, radial=0.0):
        return wrist.matrix_local @ (pivot + Vector((along, radial*math.sin(theta),-radial*math.cos(theta))))

    def lathe(name, ranges, material, columns=74):
        def sample(u, t):
            index = min(len(ranges)-1, round(t*(len(ranges)-1)))
            a=TAU*u
            along, r, flute = ranges[index]
            return point(along, a, r*(1+flute*math.cos(a*9)))
        s.cloth(name,sample,material,rows=len(ranges)-1,columns=columns,wrap=True,bone=wrist.name)
        return sample

    end = head_center - .222
    lathe("Ref · burnished gada core", [(-.400,.002,0),(-.393,.024,0),(-.372,.033,0),(-.355,.029,0),(end-.010,.031,0),(end+.035,.046,0)],mat["bronze"])
    lathe("Ref · gada dark continuous grip", [(-.361,.032,0),(-.30,.033,0),(end-.090,.036,0),(end-.033,.037,0)],mat["grip"])
    turns = round((end+.34)/.033)
    spiral = [point(mix(-.362,end-.035,j/540), TAU*turns*j/540,.037) for j in range(541)]
    s.tube("Ref · winding gada leather seams",spiral,.0022,mat["border"],wrist.name,6)
    neck = [(end-.065,.034,0), (end-.025,.046,0), (end+.018,.062,0), (end+.062,.103,.02)]
    lathe("Ref · solid cast gada throat",neck,mat["bronze"])
    for t,r in ((-.391,.028),(-.363,.036),(end-.063,.040),(end-.013,.050),(end+.029,.075),(end+.047,.091)):
        s.tube("Ref · gada forged collar",
               [point(t,TAU*k/55,r) for k in range(56)],.0037,mat["gold"],wrist.name,8)
    flute_count = 9
    head_bands = (.133,.187,.813,.867)

    def bell(u, t, relief=0):
        a = TAU*u
        shape = math.sin(math.pi*t)
        phase = flute_count*a
        lobe = math.cos(phase)
        # Broader shoulders on each cast segment and a narrow incision
        # along the valley. The flutes fade out into the two collars.
        raised = .095 * shape ** 1.35 * (.86*lobe - .14*math.cos(2*phase))
        chase = .0040*math.exp(-((1+lobe)/.020)**2)*shape**1.8
        groove = .0024 * math.exp(-(min(abs(t-band) for band in head_bands)/.012)**2)
        r = max(.016, radius * shape ** .62 * (1+raised)) - chase - groove
        return point(head_center+.222*(2*t-1), a, r+relief)

    s.cloth("Ref · oval nine-fluted gada head",bell,mat["bronze"],rows=72,columns=162,wrap=True,bone=wrist.name)
    for v in head_bands:
        s.tube("Ref · incised gada orb band",[bell(k/162,v,.0014) for k in range(163)],
               .0021,mat["gold"],wrist.name,7)
    for petal in range(flute_count):
        trough = (petal+.5)/flute_count
        s.tube("Ref · oxidized gada flute seam",[bell(trough,.15+k*.70/64,.0013) for k in range(65)],
               .0024,mat["recess"],wrist.name,7)
        for side in (-1,1):
            u = trough + side*.009
            s.tube("Ref · fine soldered gada flute edge",[bell(u,.175+k*.65/64,.0005) for k in range(65)],
                   .00115,mat["gold"],wrist.name,6)
        for v in (.343,.657):
            center_u = petal / flute_count
            p = bell(center_u,v)
            longitudinal = bell(center_u,v+.002)-bell(center_u,v-.002)
            circumferential = bell(center_u+.001,v)-bell(center_u-.001,v)
            normal = longitudinal.cross(circumferential).normalized()
            radial = p-point(head_center+.222*(2*v-1))
            if normal.dot(radial) < 0:
                normal.negate()
            set_stone(s, "gada rivet", p, normal, longitudinal,
                      (.016,.016,.007),mat,wrist.name)
    # Keep the source object names through this separate shot. Recalculate the
    # visual markers from the same definition so any head/skull clearance audit
    # follows the sculpt, not R5's smaller prop.
    return point(0), point(head_center), radius


def mesh_fibers(s, name, fibers, material, highlights):
    """Batch round tapered fibers while preserving each root's skin weights."""
    vertices, faces, weights, pigments = [], [], [], []
    side_count = 4
    cross_axis = Vector((0,1,0))
    for points, radius, root_weights, pigment in fibers:
        start = len(vertices)
        last = len(points)-1
        for i, point in enumerate(points):
            tangent = (points[min(last,i+1)]-points[max(0,i-1)]).normalized()
            across = tangent.cross(cross_axis)
            if across.length_squared < .0001:
                across = tangent.cross(Vector((0,0,1)))
            across.normalize()
            opposite = tangent.cross(across)
            taper = radius * (.11+.89*(1-i/last)**.71)
            vertices.extend(point+taper*u for u in (across,opposite,-across,-opposite))
            weights.extend([root_weights]*side_count)
            if i:
                prior = start+(i-1)*side_count
                for k in range(side_count):
                    a,b = prior+k,prior+(k+1)%side_count
                    faces.append((a,b,b+side_count,a+side_count))
                    pigments.append(pigment)
    result = s.mesh(name,vertices,faces,material,weights=weights)
    result.data.materials.append(highlights)
    for polygon,pigment in zip(result.data.polygons,pigments):
        polygon.material_index = pigment
    result["vertices_per_fiber"] = len(fibers[0][0])*side_count
    return result


def tail_tuft(s, mat, scene):
    base = next(obj for obj in scene.objects if tagged_name(obj).startswith("Curved articulated Vayu tail"))
    working_copy(base)
    count, sides = 85, 16
    if len(base.data.vertices) != count*sides:
        raise ValueError("Unexpected tail tube topology")
    original = [
        sum((base.data.vertices[j*sides+k].co for k in range(sides)), Vector()) / sides
        for j in range(count)
    ]
    centers = []
    crest_start = 42
    for j in range(crest_start):
        lower_arc = smoothstep(18,54,j)
        centers.append(original[j] + lower_arc * Vector((.13,-.045,0)))

    # These are rest-space silhouette anchors sampled seven rings apart.
    # A shared tangent at each knot gives a continuous round return and
    # leaves the existing four deformation links and their weights intact.
    lower_arc = smoothstep(18,54,crest_start)
    anchors = [
        centers[crest_start-7],
        original[crest_start] + lower_arc * Vector((.13,-.045,0)),
        Vector((.822,.296,1.178)),
        Vector((.732,.281,1.419)),
        Vector((.637,.293,1.622)),
        Vector((.643,.311,1.812)),
        Vector((.721,.323,1.910)),
        Vector((.822,.338,1.854)),
    ]
    anchors.append(anchors[-1] + (anchors[-1]-anchors[-2]))
    for j in range(crest_start,count):
        section, sub = divmod(j-crest_start,7)
        if not sub:
            centers.append(anchors[section+1])
            continue
        t = sub / 7
        p0, p1, p2, p3 = anchors[section:section+4]
        m1, m2 = (p2-p0)*.5, (p3-p1)*.5
        centers.append(p1*(2*t**3-3*t**2+1) + m1*(t**3-2*t**2+t) +
                       p2*(-2*t**3+3*t**2) + m2*(t**3-t**2))

    coat = []
    names = {group.index: group.name for group in base.vertex_groups}
    for j, center in enumerate(centers):
        first, last = max(0,j-1), min(count-1,j+1)
        tangent = (centers[last]-centers[first]).normalized()
        original_tangent = (original[last]-original[first]).normalized()
        spin = original_tangent.rotation_difference(tangent)
        width = 1 + .33*smoothstep(14,40,j) + .05*smoothstep(61,74,j) - 1.11*smoothstep(75,84,j)
        for k in range(sides):
            vert = base.data.vertices[j*sides+k]
            out = spin @ ((vert.co - original[j]) * width)
            vert.co = center + out
            if j < 15:
                continue
            pattern=math.sin(j*88.721+k*29.115)
            outward=out.normalized()
            sideways=tangent.cross(outward)
            root = vert.co-outward*.002+sideways*(.0038*pattern)
            span = .012 + .020*(.5+.5*pattern) + .008*smoothstep(55,74,j)
            lift = .0038+.0083*(.5+.5*math.cos(j*73.17+k*43.191))
            points=[
                root+tangent*(span*v)+outward*(lift*math.sin(v*math.pi*.70))+
                sideways*(.0052*pattern*v*v)
                for v in (0,.24,.48,.73,1)
            ]
            weights = [(names[group.group],group.weight) for group in vert.groups if group.weight]
            coat.append((points,.00038+.00038*(.5+.5*pattern),weights,int(pattern>.32)))
    base.data.update()
    base.material_slots[0].link="OBJECT"
    base.material_slots[0].material=mat["tail"]
    mesh_fibers(s,"Ref · close copper tail groom",coat,mat["tail"],mat["tail_light"])

    root, end = centers[77], centers[84]
    control_a = end + Vector((.028,.003,-.035))
    control_b = end + Vector((.024,-.007,-.213))
    tip = end + Vector((.139,.014,-.155))

    def plume(t):
        u=1-t
        return root*u**3 + control_a*(3*u*u*t) + control_b*(3*u*t*t) + tip*t**3

    def plume_frame(t):
        tangent = (plume(min(1,t+.004))-plume(max(0,t-.004))).normalized()
        a = tangent.cross(Vector((0,1,0))).normalized()
        return a, tangent.cross(a)

    def volume(t):
        return (.023 + .009*smoothstep(.05,.31,t))*(1-.983*smoothstep(.37,1,t))

    def pelt(u,t):
        a,b=plume_frame(t)
        radial=a*math.cos(TAU*u)+b*(.78*math.sin(TAU*u))
        return plume(t) + radial * volume(t)

    s.cloth("Ref · rounded chestnut plume core",pelt,mat["tuft"],rows=36,columns=28,wrap=True,bone="tail_04")
    fibers=[]
    strand_count = 328
    # Quasiperiodic starters cover the volume without repeating clumps.
    for i in range(strand_count):
        phase = TAU*((i*.61803398875)%1.0)
        noise = .5+.5*math.sin(i*17.39)
        start = .265*((i*.41421356237)%1.0)
        flyaway = i%11 in (0,4)
        stop = .75+.25*((i*.73205080757)%1.0) if flyaway else .64+.32*((i*.73205080757)%1.0)
        points=[]
        for step in range(15):
            t=step/14
            station=mix(start,stop,t)
            a,b=plume_frame(station)
            theta=phase+(.20*noise-.1)*t+.21*math.sin(4*t+i)*t*t
            normal=a*math.cos(theta)+b*(.82*math.sin(theta))
            extrusion=mix(-.004,.004+.013*noise,smoothstep(.0,.35,t))
            flutter=a*(.010+.015*noise+.022*flyaway)*t**4*math.sin(phase+5*t)
            points.append(plume(station)+normal*(volume(station)+extrusion)+flutter)
        fibers.append((points,.00062+.00085*noise,[("tail_04",1.0)],int(noise>.64 or flyaway)))
    mesh_fibers(s,"Ref · layered tail tuft fibers",fibers,mat["tuft"],mat["tuft_light"])
    return {"tuft_strands":strand_count,"guard_hairs":len(coat),
            "modified_tail_vertices":count*sides,"tip_rest_m":list(end)}


def apply(scene, reference_profile):
    """Assemble a more faithful hero-shot wardrobe on the active R5 rig."""
    if scene != bpy.context.scene:
        raise ValueError("Activate the working scene before applying Hanuman wardrobe")
    if any(obj.name.startswith("Ref · dark forged cuirass") for obj in scene.objects):
        raise ValueError("Wardrobe already exists in this scene")
    profile = reference_profile.get("wardrobe", {})
    rig = next(obj for obj in scene.objects if obj.type == "ARMATURE")
    body = next(obj for obj in scene.objects if tagged_name(obj).startswith("Hanuman · contiguous skinned anatomy"))
    hidden = []
    for obj in list(scene.objects):
        if tagged_name(obj).startswith(HIDE):
            obj.hide_render = True
            obj.hide_set(True)
            hidden.append(obj.name)
    s=body_shape(rig,body)
    mats=palette(profile)
    dress(s,mats,float(profile.get("dhoti_length_m",.669)))
    cuirass(s,mats)
    guards(s,mats)
    grip, bulb, radius=weapon(s,mats,profile)
    tail=tail_tuft(s,mats,scene)
    return {
        "wardrobe_new_meshes": len(s.objects)-1,
        "wardrobe_vertices": sum(len(o.data.vertices) for o in s.objects[1:]),
        "wardrobe_hidden_originals": len(hidden),
        "weapon_grip_rest_m": list(grip),
        "weapon_bulb_rest_m": list(bulb),
        "weapon_bulb_radius_m": radius,
        "tail": tail,
    }
