"""Original in-place hero motion for the pinned MakeHuman skeleton.

Blender coordinates: Z up, -Y forward, anatomical left is +X. No copied motion
capture or external animation clips. Call after clothing/weapon skin binding:
    actions = author_animations(armature, "bow", "arjuna")
The returned dictionary contains idle/run/fire/cast/jump/defeat and three
ability-specific cast1/cast2/cast3 bpy Actions. Pass HeroDef abilities as the
fourth argument; a pinned roster fallback supports isolated technical checks.
The rig object and root bone never translate. Pelvic children provide vertical
body compression; they are pose motion, not actor locomotion. All rotations are
quaternions derived from the actual rest matrices and armature-space targets.
"""

import math

import bpy
from mathutils import Matrix, Quaternion, Vector


BASE_CLIPS = ("idle", "run", "fire", "cast", "jump", "defeat")
CLIP_NAMES = (*BASE_CLIPS, "cast1", "cast2", "cast3")
WEAPONS = ("bow", "mace", "staff", "spear", "chakram")
FPS = 30
IDENTITY = Quaternion((1, 0, 0, 0))

ROSTER_ABILITIES = {
    "rama": ("bolt", "dash", {"kind": "line", "mechanic": "dawn-volley", "windup": 1}),
    "ravana": ("ward", "pull", "nova"),
    "arjuna": ("burst", "dash", "line"),
    "duryodhana": ("burst", "ward", "cone"),
    "hanuman": ("leap", "heal", {"kind": "nova", "mechanic": "mountain-descent", "windup": .7}),
    "karna": ("line", "ward", "nova"),
    "bhima": ("cone", "leap", "nova"),
    "meghnad": ("slow", "dash", "burst"),
    "sita": ("heal", "slow", {"kind": "ward", "mechanic": "mithila-sanctuary", "windup": .8}),
    "draupadi": ("ward", "pull", "heal"),
    "subhadra": ("bolt", "heal", "summon"),
    "hidimbi": ("slow", "ward", "summon"),
    "chitrangada": ("dash", "cone", "ward"),
    "ulupi": ("pull", "heal", "slow"),
}


def _mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _smooth(t):
    return t * t * (3 - 2 * t)


class _Pose:
    """Small forward-kinematics evaluator; never guesses native Euler axes."""

    def __init__(self, rig):
        self.rig = rig
        self.bones = rig.data.bones
        self.rest = {b.name: b.matrix_local.to_quaternion().normalized() for b in self.bones}
        self.rot = {}
        self.loc = {}
        self.cache = {}
        self.scale = self.bones["head"].tail_local.z / 1.85745
        self.string_tension = 0.0

    def world(self, name):
        if name in self.cache:
            return self.cache[name]
        b = self.bones[name]
        if b.parent:
            ph, pq = self.world(b.parent.name)
            delta = pq @ self.rest[b.parent.name].inverted()
            head = ph + delta @ (b.head_local - b.parent.head_local)
            before = delta @ self.rest[name]
        else:
            head, before = b.head_local.copy(), self.rest[name]
        head += before @ self.loc.get(name, Vector((0, 0, 0)))
        q = (before @ self.rot.get(name, IDENTITY)).normalized()
        self.cache[name] = head, q
        return head, q

    def set_rotation(self, name, quaternion):
        self.rot[name] = quaternion.normalized()
        self.cache.clear()

    def rotate(self, name, x=0, y=0, z=0):
        # Rotation axes are named in the anatomical rest frame, converted into
        # this bone's arbitrary native roll before use as a local quaternion.
        q = Quaternion((0, 0, 1), math.radians(z)) @ Quaternion((0, 1, 0), math.radians(y)) @ Quaternion((1, 0, 0), math.radians(x))
        rest = self.rest[name]
        self.set_rotation(name, rest.inverted() @ q @ rest)

    def aim(self, name, direction):
        direction = Vector(direction).normalized()
        rest = self.rest[name]
        desired = (rest @ Vector((0, 1, 0))).rotation_difference(direction) @ rest
        parent = self.bones[name].parent
        before = self.world(parent.name)[1] @ self.rest[parent.name].inverted() @ rest if parent else rest
        self.set_rotation(name, before.inverted() @ desired)

    def hand_orientation(self, name, forward, weapon_axis):
        # Native palm is XY, fingers extend +Y, and +Z is its normal. A shaft
        # crosses the fist along native X; using Z would pierce the open palm.
        y = Vector(forward).normalized()
        x = Vector(weapon_axis)
        x = (x - y * x.dot(y)).normalized()
        if x.length < .1:
            raise ValueError("Hand-forward and weapon axis must not be parallel")
        z = x.cross(y).normalized()
        desired = Matrix((x, y, z)).transposed().to_quaternion()
        self.orient(name, desired)

    def orient(self, name, desired):
        rest = self.rest[name]
        parent = self.bones[name].parent
        before = self.world(parent.name)[1] @ self.rest[parent.name].inverted() @ rest
        self.set_rotation(name, before.inverted() @ desired)

    def shift_hips(self, height):
        # Native root has no body-surface weights; these three children carry
        # the body. Keep root fixed and translate all three by the same delta.
        delta = Vector((0, 0, height * self.scale))
        for name in ("pelvis.L", "pelvis.R", "spine05"):
            parent = self.bones[name].parent.name
            before = self.world(parent)[1] @ self.rest[parent].inverted() @ self.rest[name]
            self.loc[name] = before.inverted() @ delta
        self.cache.clear()

    def chain(self, names, target, pole):
        # Native upper/lower limbs each contain two collinear/twist sections.
        # Aim both sections, rather than treating the first small bone as the
        # entire limb or bending the twist joint into an extra elbow.
        upper1, upper2, lower1, lower2 = names
        origin = self.world(upper1)[0]
        target = Vector(target) * self.scale
        pole = Vector(pole) * self.scale
        a = self.bones[upper1].length + self.bones[upper2].length
        b = self.bones[lower1].length + self.bones[lower2].length
        offset = target - origin
        distance = max(abs(a - b) + .002, min(offset.length, a + b - .003))
        direction = offset.normalized()
        bend = pole - origin
        bend -= direction * bend.dot(direction)
        if bend.length < .0001:
            bend = direction.cross(Vector((0, 1, 0)))
        bend.normalize()
        along = (a * a - b * b + distance * distance) / (2 * distance)
        elbow = origin + direction * along + bend * math.sqrt(max(0, a * a - along * along))
        endpoint = origin + direction * distance
        for name in (upper1, upper2):
            self.aim(name, elbow - origin)
        for name in (lower1, lower2):
            self.aim(name, endpoint - elbow)

    def arm(self, side, hand, elbow, forward=(0, -.9, -.15), weapon_axis=(0, 0, 1)):
        self.chain([f"{part}.{side}" for part in ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02")], hand, elbow)
        self.hand_orientation(f"wrist.{side}", forward, weapon_axis)

    def leg(self, side, ankle, knee, toe_angle=0):
        self.chain([f"{part}.{side}" for part in ("upperleg01", "upperleg02", "lowerleg01", "lowerleg02")], ankle, knee)
        angle = math.radians(toe_angle)
        self.aim(f"foot.{side}", (0, -math.cos(angle), -math.sin(angle)))

    def grip(self, side, amount):
        # Explicit circular finger segments wrap the X-axis handle at native
        # palm (0,.105,+/-.025). Native left/right palms mirror their Z axis.
        wrist = f"wrist.{side}"
        wrist_rest = self.rest[wrist]
        wrist_now = self.world(wrist)[1]
        sign = 1 if side == "R" else -1
        closure = min(1, max(0, amount / .85))
        for finger in range(1, 6):
            for segment in range(1, 4):
                name = f"finger{finger}-{segment}.{side}"
                bone = self.bones[name]
                baseline = wrist_rest.inverted() @ self.rest[name]
                direction = wrist_rest.inverted() @ (bone.tail_local - bone.head_local).normalized()
                if finger == 1:
                    x, y, z = ((.15, .95, .27), (-.45, .75, .48), (-.8, .35, .48))[segment - 1]
                    target = Vector((x, y, z * sign)).normalized()
                else:
                    angle = math.radians((45, 110, 170)[segment - 1])
                    target = Vector((0, math.cos(angle), sign * math.sin(angle)))
                closed = direction.rotation_difference(target) @ baseline
                # Native thumb-web weights tolerate a modest opposing pose;
                # full target rotation pinches the web into a sharp fold.
                desired = wrist_now @ baseline.slerp(closed, closure * .45 if finger == 1 else closure)
                self.orient(name, desired)

    def bow_string(self):
        if "bowstring" not in self.bones:
            return
        self.loc.pop("bowstring", None)
        self.cache.clear()
        rest_head, _ = self.world("bowstring")
        hand, hand_q = self.world("wrist.L")
        grip = hand + hand_q @ (Vector((0, .105, -.025)) * self.scale)
        target = rest_head.lerp(grip, min(1, max(0, self.string_tension)))
        parent = self.bones["bowstring"].parent.name
        before = self.world(parent)[1] @ self.rest[parent].inverted() @ self.rest["bowstring"]
        self.loc["bowstring"] = before.inverted() @ (target - rest_head)
        self.cache.clear()


def _bow_hold(p, release=0):
    p.arm("R", (-.03, -.49 + .02 * release, 1.60), (-.48, -.30, 1.47), (0, -1, 0))
    p.arm("L", _mix((.10, -.16, 1.60), (.28, .01, 1.62), release), (.50, .08, 1.50), (-1, 0, 0))
    p.string_tension = 1 - release


def _ready(p, weapon):
    p.shift_hips(-.035)
    p.rotate("spine03", x=2)
    p.leg("L", (.21, -.075, .085), (.25, -.6, .55), 24)
    p.leg("R", (-.21, .045, .085), (-.25, -.6, .55), 24)
    if weapon == "bow":
        # Bow socket is wrist.R; left hand reaches the string near the cheek.
        _bow_hold(p)
    elif weapon == "mace":
        p.arm("R", (-.28, -.28, 1.25), (-.46, .04, 1.16), (0, -.5, .65))
        p.arm("L", (.28, -.14, 1.05), (.5, .04, 1.15))
    elif weapon == "spear":
        p.arm("R", (-.28, -.20, 1.11), (-.47, .1, 1.15), (0, -.75, -.65), (0, -.65, .75))
        p.arm("L", (.15, -.31, 1.23), (.4, -.07, 1.28), (-.25, -.9, .15))
    elif weapon == "staff":
        p.arm("R", (-.29, -.19, 1.13), (-.48, .02, 1.23), (0, -.65, .5))
        p.arm("L", (.29, -.19, 1.12), (.49, .02, 1.22))
    else:
        p.arm("R", (-.29, -.27, 1.25), (-.48, .04, 1.2), (0, -.8, .2))
        p.arm("L", (.28, -.17, 1.12), (.49, .02, 1.17))
    p.grip("R", .85)
    p.grip("L", .25 if weapon == "staff" else .65)


def _sample(rig, weapon, clip, phase):
    p = _Pose(rig)
    _ready(p, weapon)
    if clip == "idle":
        breath = math.sin(phase * 2 * math.pi)
        p.rotate("spine02", x=breath * .65)
        p.rotate("spine01", x=-breath * .45)
        p.rotate("neck01", x=breath * .35)
        p.shift_hips(-.035 + breath * .003)
    elif clip == "run":
        angle = phase * 2 * math.pi
        p.shift_hips(-.045 + .025 * math.cos(angle * 2))
        p.rotate("spine05", z=4 * math.sin(angle))
        p.rotate("spine02", x=10, z=-7 * math.sin(angle))
        p.rotate("head", x=-5)
        for side, sign in (("L", 1), ("R", -1)):
            cycle = angle + (0 if sign == 1 else math.pi)
            travel = math.sin(cycle)
            lift = max(0, math.cos(cycle)) ** 2
            p.leg(side, (sign * .19, -.28 * travel, .085 + .19 * lift), (sign * .23, -.7, .55), 20 + 12 * max(0, -travel))
            if weapon != "bow":
                p.arm(side, (sign * .29, -.19 + .18 * travel, 1.11 + .06 * lift), (sign * .48, .1, 1.25), (0, -.85, .1))
    elif clip == "fire":
        # Release/contact begins near the authoritative shot; remaining time
        # is follow-through and recovery, rather than a late visible attack.
        wind = max(0, 1 - abs(phase - .08) / .08)
        strike = max(0, 1 - abs(phase - .26) / .18)
        recover = _smooth(min(1, max(0, (phase - .42) / .58)))
        if weapon == "bow":
            release = min(1, max(0, (phase - .10) / .12)) * (1 - recover)
            p.rotate("spine02", z=-4 * release)
            _bow_hold(p, release)
            p.grip("L", .8 * (1 - release))
        elif weapon == "mace":
            drive = max(wind, strike)
            p.rotate("spine02", x=12 * strike, z=8 * strike - 6 * wind)
            hand = _mix((-.28, -.28, 1.25), (-.26, -.10, 1.87), wind)
            hand = _mix(hand, (-.13, -.57, 1.03), strike)
            p.arm("R", hand, (-.5, -.02, 1.58), _mix((0, -.5, .65), (0, -.2, 1), strike), _mix((0, 0, 1), (0, -1, -.2), strike))
            p.arm("L", (.27, -.27, 1.15 + .15 * drive), (.55, -.05, 1.3))
        elif weapon == "spear":
            p.rotate("spine02", x=7 * strike, z=-9 * strike)
            p.arm("R", (-.17, -.20 - .38 * strike + .10 * wind, 1.23), (-.46, -.08, 1.23), _mix((0, -.75, -.65), (0, -.05, -1), strike), _mix((0, -.65, .75), (0, -1, .05), strike))
            p.arm("L", (.12, -.31 - .15 * strike, 1.23), (.37, -.12, 1.25), (0, -1, .04))
        elif weapon == "staff":
            p.rotate("spine02", x=5 * strike)
            p.arm("R", (-.20, -.19 - .30 * strike, 1.13 + .18 * strike), (-.47, -.05, 1.3), (0, -.75, .25))
            p.arm("L", (.24, -.19 - .20 * strike, 1.12 + .25 * strike), (.47, -.05, 1.25), (0, -.9, .1))
            p.grip("L", .15)
        else:
            p.rotate("spine02", z=16 * strike - 8 * wind)
            p.arm("R", (-.29 + .37 * wind, -.27 - .28 * strike, 1.25 + .15 * strike), (-.55, -.13, 1.4), (.45 * strike, -.8, .1))
            p.arm("L", (.31, -.15 + .13 * strike, 1.12), (.5, .07, 1.3))
    elif clip == "cast":
        p.string_tension = 0
        lift = math.sin(math.pi * phase) ** .7
        p.shift_hips(-.035 - .06 * math.sin(math.pi * phase))
        p.leg("L", (.21, -.075, .085), (.25, -.6, .55), 24)
        p.leg("R", (-.21, .045, .085), (-.25, -.6, .55), 24)
        p.rotate("spine02", x=-5 * lift)
        p.rotate("head", x=-6 * lift)
        for side, sign in (("L", 1), ("R", -1)):
            start = (.29 * sign, -.19, 1.13)
            target = (.43 * sign, -.31, 1.70 if side == "L" else 1.63)
            p.arm(side, _mix(start, target, lift), (.64 * sign, -.02, 1.43), (0, -.65, .55))
        p.grip("L", .08)
    elif clip == "jump":
        p.string_tension = 0
        tuck = math.sin(math.pi * phase)
        p.shift_hips(-.035 - .035 * tuck)
        p.rotate("spine02", x=10 * tuck)
        for side, sign in (("L", 1), ("R", -1)):
            p.leg(side, (.21 * sign, .12 * tuck, .085 + .32 * tuck), (.25 * sign, -.6, .5), 24 + 18 * tuck)
            p.arm(side, (.34 * sign, -.19, 1.1 + .25 * tuck), (.57 * sign, -.03, 1.3))
    elif clip == "defeat":
        p.string_tension = 0
        fall = _smooth(min(1, phase / .8))
        p.shift_hips(-.035 - .44 * fall)
        p.rotate("spine05", x=15 * fall)
        p.rotate("spine03", x=19 * fall)
        p.rotate("spine01", x=14 * fall)
        p.rotate("neck01", x=12 * fall)
        p.rotate("head", x=10 * fall)
        for side, sign in (("L", 1), ("R", -1)):
            p.leg(side, (.21 * sign, .12 * fall, .085), (.23 * sign, -.65, .35), 24)
            p.arm(side, (.33 * sign, -.22 - .16 * fall, 1.1 - .82 * fall), (.58 * sign, -.12, .7), _mix((0, -.9, -.15), (0, -.1, -1), fall) if side == "R" else (0, -.9, -.15), _mix((0, 0, 1), (0, -1, .1), fall) if side == "R" else (0, 0, 1))
            p.grip(side, .55 if side == "R" else .15 + .2 * (1 - fall))
    return p


def _planted(p, drop):
    p.shift_hips(drop)
    p.leg("L", (.21, -.075, .085), (.25, -.6, .55), 24)
    p.leg("R", (-.21, .045, .085), (-.25, -.6, .55), 24)


def _ability_sample(rig, weapon, ability, phase, seconds):
    kind = ability["kind"]
    mechanic = ability.get("mechanic")
    windup = float(ability.get("windup", 0))
    now = phase * seconds
    if mechanic == "dawn-volley":
        p = _sample(rig, weapon, "idle", 0)
        tension = min(1, now / max(.01, windup))
        after = max(0, now - windup)
        recover = _smooth(min(1, after / .6))
        _planted(p, -.035 - .045 * tension * (1 - recover))
        p.rotate("spine02", z=-5 * tension * (1 - recover))
        pulse = math.sin(min(.36, after) / .36 * 3 * math.pi) ** 2 if after < .36 else 0
        _bow_hold(p, pulse)
        p.grip("L", .75 * (1 - pulse))
        return p
    if mechanic == "mountain-descent":
        if now <= windup:
            tension = _smooth(min(1, now / max(.01, windup)))
            p = _sample(rig, weapon, "idle", 0)
            _planted(p, -.035 - .15 * tension)
            p.rotate("spine02", x=14 * tension)
            p.arm("R", (-.3, -.15 + .13 * tension, 1.22 + .12 * tension), (-.52, .08, 1.35), (0, -.55, .5))
            p.arm("L", (.3, -.16 + .19 * tension, 1.1), (.51, .1, 1.2))
            return p
        flight = min(1, (now - windup) / .65)
        p = _sample(rig, weapon, "jump", flight)
        impact = max(0, (flight - .62) / .38)
        p.rotate("spine02", x=10 + impact * 14)
        p.arm("R", (-.23, -.25 - .22 * impact, 1.52 - .58 * impact), (-.48, -.03, 1.4), (0, -.2, 1), (0, -1, -.2))
        return p
    if mechanic == "mithila-sanctuary":
        lift_phase = .5 * min(1, now / max(.01, windup)) if now <= windup else .5 + .5 * min(1, (now - windup) / .6)
        p = _sample(rig, weapon, "cast", lift_phase)
        p.grip("L", .04)
        return p
    if kind in ("bolt", "line"):
        return _sample(rig, weapon, "fire", phase)
    if kind in ("dash", "leap"):
        p = _sample(rig, weapon, "jump", phase)
        lean = math.sin(math.pi * phase)
        p.rotate("spine02", x=(22 if kind == "dash" else 13) * lean)
        if kind == "dash":
            p.leg("R", (-.21, .22 * lean, .085 + .16 * lean), (-.23, -.55, .5), 30)
            p.leg("L", (.21, -.20 * lean, .085 + .10 * lean), (.23, -.55, .5), 20)
        return p
    if kind in ("heal", "ward"):
        p = _sample(rig, weapon, "cast", phase)
        bloom = math.sin(math.pi * phase)
        if kind == "heal":
            p.arm("L", (.34, -.31, 1.12 + .54 * bloom), (.56, -.1, 1.36), (0, -.7, .6))
        else:
            p.arm("L", (.30, -.23 - .26 * bloom, 1.22 + .18 * bloom), (.53, -.04, 1.35), (0, -1, 0))
        p.grip("L", .03)
        return p
    p = _sample(rig, weapon, "idle", 0)
    p.string_tension = 0
    power = math.sin(math.pi * phase)
    if kind in ("burst", "cone"):
        sweep = math.sin(phase * math.pi * 2) * power
        p.rotate("spine02", z=23 * sweep, x=6 * power)
        if weapon == "bow":
            _bow_hold(p, power)
        else:
            p.arm("R", (-.26 + .40 * sweep, -.25 - .24 * power, 1.23 + .10 * power), (-.50, -.04, 1.40), (0, -.2, .9), (.5 * sweep, -1, .12))
            p.arm("L", (.28, -.15, 1.12 + .16 * power), (.53, .04, 1.25))
    elif kind in ("slow", "pull"):
        sweep = math.sin(phase * math.pi * 2)
        reach = power if kind == "slow" else max(0, 1 - abs(phase - .3) / .3)
        p.rotate("spine02", z=7 * sweep)
        p.arm("L", (.27 + .20 * sweep, -.17 - .30 * reach, 1.13 + .22 * power), (.57, -.02, 1.34), (0, -.8, .25))
        p.grip("L", .04 if kind == "slow" else .8 * max(0, (phase - .3) / .7))
    elif kind == "summon":
        _planted(p, -.035 - .07 * power)
        p.rotate("spine02", x=7 * power)
        p.arm("R", (-.24, -.28, 1.13 - .28 * power), (-.47, -.04, 1.22), (0, -1, 0), (0, 0, 1))
        p.arm("L", (.34, -.22, 1.14 + .44 * power), (.55, -.02, 1.38), (0, -.65, .55))
        p.grip("L", .03)
    elif kind == "nova":
        _planted(p, -.035 - .055 * power)
        p.rotate("spine02", x=-7 * power)
        for side, sign in (("L", 1), ("R", -1)):
            p.arm(side, (.29 * sign + .22 * sign * power, -.19, 1.15 + .30 * power), (.68 * sign, 0, 1.38), (sign * .55, -.75, .15))
        p.grip("L", .05)
    else:
        raise ValueError(f"Unsupported ability kind: {kind}")
    return p


def author_animations(armature, weapon_class, hero_id="", abilities=None):
    """Return nine named bpy Actions, leaving the rig in its idle ready pose.

    The caller retains ownership of export and any preceding proof actions.
    Existing actions named Idle/RigProof are removed only when currently bound
    to this rig or unused. Production callers should build one hero per scene.
    """
    if armature.type != 'ARMATURE':
        raise TypeError("author_animations expects a Blender armature object")
    if weapon_class not in WEAPONS:
        raise ValueError(f"Unsupported hero weapon: {weapon_class}")
    required = {"root", "spine05", "spine03", "spine02", "spine01", "head", "neck01"}
    required.update(f"{part}.{side}" for side in ("L", "R") for part in ("pelvis", "upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist", "upperleg01", "upperleg02", "lowerleg01", "lowerleg02", "foot"))
    missing = sorted(required - set(armature.data.bones.keys()))
    if missing:
        raise ValueError(f"Native MakeHuman rig is missing bones: {missing}")
    animation = armature.animation_data_create()
    previous = animation.action
    animation.action = None
    for action in list(bpy.data.actions):
        if action.name.lower() in (*CLIP_NAMES, "rigproof") and (action == previous or action.users == 0 or action.get("yuga_original_motion")):
            bpy.data.actions.remove(action)
    scene = bpy.context.scene
    scene.render.fps = FPS
    actions = {}
    specs = {
        "idle": (120, [i / 8 for i in range(9)]),
        "run": (24, [i / 8 for i in range(9)]),
        "fire": (21 if weapon_class != "bow" else 24, [0, .08, .14, .26, .42, .65, .82, 1]),
        "cast": (36, [0, .10, .25, .45, .6, .8, 1]),
        "jump": (24, [0, .15, .35, .5, .7, .85, 1]),
        "defeat": (36, [0, .12, .3, .5, .7, .8, 1]),
    }
    definitions = abilities if abilities is not None else ROSTER_ABILITIES.get(hero_id, ("bolt", "ward", "nova"))
    if len(definitions) != 3:
        raise ValueError("Each hero requires exactly three ability definitions")
    ability_clips = {}
    for index, definition in enumerate(definitions, 1):
        definition = {"kind": definition} if isinstance(definition, str) else dict(definition)
        clip = f"cast{index}"
        tail = .65 if definition.get("mechanic") == "mountain-descent" else .6
        windup = float(definition.get("windup", 0))
        seconds = windup + tail if definition.get("mechanic") else (.65 if definition["kind"] == "dash" else 1)
        duration = round(seconds * FPS)
        phases = {i / 12 for i in range(13)}
        if windup:
            phases.add(windup / (duration / FPS))
            for extra in (.06, .12, .18, .24, .30, .36):
                if windup + extra < duration / FPS:
                    phases.add((windup + extra) / (duration / FPS))
        specs[clip] = duration, sorted(phases)
        ability_clips[clip] = definition
    for clip, (duration, phases) in specs.items():
        samples = [_ability_sample(armature, weapon_class, ability_clips[clip], phase, duration / FPS) if clip in ability_clips else _sample(armature, weapon_class, clip, phase) for phase in phases]
        for sample in samples:
            sample.bow_string()
        controlled = set().union(*(set(p.rot) | set(p.loc) for p in samples)) | required
        action = bpy.data.actions.new(clip)
        action.use_fake_user = True
        action["yuga_original_motion"] = True
        action["yuga_weapon"] = weapon_class
        action["yuga_hero"] = hero_id
        action["yuga_loop"] = clip in ("idle", "run")
        action["yuga_root_motion"] = False
        if clip in ability_clips:
            action["yuga_ability_kind"] = ability_clips[clip]["kind"]
            action["yuga_ability_mechanic"] = ability_clips[clip].get("mechanic", "standard")
            action["yuga_release_seconds"] = float(ability_clips[clip].get("windup", 0))
        animation.action = action
        previous_quaternions = {}
        for phase, pose in zip(phases, samples):
            frame = 1 + round(duration * phase)
            for bone in armature.pose.bones:
                bone.rotation_mode = 'QUATERNION'
                q = pose.rot.get(bone.name, IDENTITY).copy()
                if bone.name in previous_quaternions and q.dot(previous_quaternions[bone.name]) < 0:
                    q.negate()
                previous_quaternions[bone.name] = q.copy()
                bone.rotation_quaternion = q
                bone.location = pose.loc.get(bone.name, (0, 0, 0))
                bone.scale = (1, 1, 1)
                if bone.name in controlled:
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
                    if bone.name in ("root", "pelvis.L", "pelvis.R", "spine05", "bowstring"):
                        bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
        for curve in action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR'
        actions[clip] = action
    animation.action = actions["idle"]
    scene.frame_start = 1
    scene.frame_end = 121
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return actions


def validate_deformation(armature, body, actions):
    """Sample every frame on the evaluated weighted body, returning evidence.

    This detects frozen skin, nonfinite/exploding vertices, root drift and loop
    seams. It reports joint trajectories and ground bounds, but does not claim
    garment collision or subjective motion quality. Pass the continuous body
    mesh, not a weapon or an unweighted proxy. Suitable for the asset build gate.
    """
    import numpy as np

    if set(actions) != set(CLIP_NAMES):
        raise AssertionError("Expected six base and three ability-specific actions")
    scene = bpy.context.scene
    old_action, old_frame = armature.animation_data.action, scene.frame_current
    evidence = {}
    try:
        for clip, action in actions.items():
            armature.animation_data.action = action
            first = last = None
            maximum_motion = root_motion = 0.0
            moved = 0
            bounds = []
            tracks = {name: [] for name in ("wrist.L", "wrist.R", "foot.L", "foot.R", "head")}
            start, end = (round(v) for v in action.frame_range)
            for frame in range(start, end + 1):
                scene.frame_set(frame)
                bpy.context.view_layer.update()
                mesh = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
                coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
                mesh.vertices.foreach_get("co", coordinates)
                coordinates = coordinates.reshape((-1, 3))
                if not np.isfinite(coordinates).all():
                    raise AssertionError(f"{clip} frame {frame}: nonfinite skin")
                if first is None:
                    first = coordinates.copy()
                distances = np.linalg.norm(coordinates - first, axis=1)
                maximum_motion = max(maximum_motion, float(distances.max()))
                moved = max(moved, int((distances > .005).sum()))
                bounds.append((coordinates.min(axis=0), coordinates.max(axis=0)))
                last = coordinates.copy()
                root_motion = max(root_motion, armature.location.length, armature.pose.bones["root"].location.length)
                for name, values in tracks.items():
                    values.append(tuple(armature.pose.bones[name].head))
            lower = np.array([b[0] for b in bounds]).min(axis=0)
            upper = np.array([b[1] for b in bounds]).max(axis=0)
            seam = float(np.linalg.norm(last - first, axis=1).max())
            if root_motion > 1e-6:
                raise AssertionError(f"{clip}: translated actor root {root_motion}")
            if maximum_motion < .001:
                raise AssertionError(f"{clip}: skin did not actually move")
            if float((upper - lower).max()) > 3.5:
                raise AssertionError(f"{clip}: body deformation escaped plausible bounds")
            if float(lower[2]) < -.035:
                raise AssertionError(f"{clip}: body penetrated ground by more than 35mm")
            if clip in ("idle", "run") and seam > 1e-4:
                raise AssertionError(f"{clip}: weighted-body loop seam {seam}")
            paths = {name: {"distance": float(np.linalg.norm(np.diff(np.array(points), axis=0), axis=1).sum()), "range": (np.array(points).max(axis=0) - np.array(points).min(axis=0)).tolist()} for name, points in tracks.items()}
            evidence[clip] = {"frames": end - start + 1, "maxVertexMotion": maximum_motion, "verticesMoved5mm": moved, "meshMinimum": lower.tolist(), "meshMaximum": upper.tolist(), "rootTranslation": root_motion, "loopGap": seam, "jointPaths": paths}
    finally:
        armature.animation_data.action = old_action
        scene.frame_set(old_frame)
        bpy.context.view_layer.update()
    return evidence
