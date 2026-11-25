"""Refine Hanuman's large body planes on the weighted source and its existing groom.

The added relief follows pectoral girdle, flexor and superficial calf anatomy.
It operates in rig rest space before wardrobe fitting. The exact same field
moves the limb hairs, so their roots stay on the skin as the body changes.
"""

from collections import Counter
from math import exp

import bpy
from mathutils import Matrix, Vector


BODY = "Hanuman · contiguous skinned anatomy"
GROOM = "Hanuman match · arm and calf guard hairs"
FRONT = Vector((0, -1, 0))
UP = Vector((0, 0, 1))
LOOKDEV_PREFIX = "LookDev - "

# Study references: OpenStax Anatomy and Physiology 2e §11.5 and §11.6, and
# Practice Drawing This's Dynamic Torso and Bridgman Arm. No donor geometry.


def ramp(lower, upper, value):
    t = max(0.0, min(1.0, (value - lower) / (upper - lower)))
    return t * t * (3.0 - 2.0 * t)


def hill(value, center, width):
    return exp(-((value - center) / width) ** 2)


def window(t, start, end, fade):
    return ramp(start, start + fade, t) * (1.0 - ramp(end - fade, end, t))


class LimbAxis:
    def __init__(self, start, end, surface_side):
        self.start = start
        self.vector = end - start
        self.length_squared = self.vector.length_squared
        direction = self.vector.normalized()
        self.surface_side = (surface_side - direction * surface_side.dot(direction)).normalized()

    def surface(self, point, start, end, reach):
        delta = point - self.start
        t = delta.dot(self.vector) / self.length_squared
        if not start < t < end:
            return None
        radial = delta - t * self.vector
        distance = radial.length
        if not .002 < distance < reach:
            return None
        normal = radial.normalized()
        edge = window(distance, .002, reach, .025)
        return t, normal, normal.dot(self.surface_side), edge

    def upper_arm(self, point):
        surface = self.surface(point, .09, .94, .18)
        if surface is None:
            return Vector()
        t, normal, anterior, edge = surface
        # Biceps sits in front of the humerus. The triceps is broader and further
        # down the upper arm. Both forms fade before the elbow hinge.
        biceps = .0105 * hill(t, .54, .24) * ramp(-.16, .92, anterior)
        triceps = .0085 * hill(t, .63, .29) * ramp(.05, .98, -anterior)
        return normal * (biceps + triceps) * edge * window(t, .09, .94, .19)

    def forearm(self, point):
        surface = self.surface(point, .05, .77, .13)
        if surface is None:
            return Vector()
        t, normal, radial_side, edge = surface
        # The proximal thumb-side flexor is full before tapering into its tendon.
        flexor = .010 * hill(t, .25, .22) * ramp(.0, .94, radial_side)
        opposing = .005 * hill(t, .33, .24) * ramp(.14, .98, -radial_side)
        return normal * (flexor + opposing) * edge * window(t, .05, .77, .15)

    def calf(self, point):
        surface = self.surface(point, .21, .88, .14)
        if surface is None:
            return Vector()
        t, normal, anterior, edge = surface
        # A lifted posterior belly and a long, flatter tibial plane. Both
        # terminate above the ankle bones and stay underneath the garment fit.
        gastrocnemius = .013 * hill(t, .43, .22) * ramp(-.22, .90, -anterior)
        tibia = -.0035 * hill(t, .65, .22) * ramp(.38, .96, anterior)
        return normal * (gastrocnemius + tibia) * edge * window(t, .21, .88, .17)


def axes_for_side(rig, side):
    def head(name):
        return rig.data.bones[f"{name}.{side}"].head_local.copy()

    shoulder, elbow, wrist = (head(name) for name in ("upperarm01", "lowerarm01", "wrist"))
    thumb = head("finger1-1")
    return (
        LimbAxis(shoulder, elbow, FRONT),
        LimbAxis(elbow, wrist, thumb - wrist),
        LimbAxis(head("lowerleg01"), head("foot"), FRONT),
    )


def clavicle_form(point):
    x, y, z = point
    lateral = abs(x)
    if not (.012 < lateral < .245 and -.204 < y < -.055 and 1.571 < z < 1.715):
        return Vector()
    extents = window(lateral, .012, .245, .067) * ramp(-.057, -.130, y) * (
        1.0 - ramp(1.693, 1.715, z))
    # A chest platform plus smaller clavicular relief avoids a carved line.
    platform = .0048 * hill(z, 1.630 + lateral * .12, .060)
    crest = .0063 * hill(z, 1.657 + lateral * .13, .022)
    return extents * (FRONT * (platform + crest) + UP * crest * .36)


def displacement(point, axes):
    x, _, z = point
    side = "L" if x >= 0 else "R"
    if .262 < abs(x) < .781 and 1.216 < z < 1.704:
        upper, forearm, _ = axes[side]
        arm = upper.upper_arm(point) + forearm.forearm(point)
        edge = window(abs(x), .262, .781, .04) * window(z, 1.216, 1.704, .045)
        return f"arm.{side}", arm * edge
    if .13 < abs(x) < .409 and .134 < z < .455:
        edge = window(abs(x), .13, .409, .037) * window(z, .134, .455, .035)
        return f"calf.{side}", axes[side][2].calf(point) * edge
    if 1.571 < z < 1.715 and .012 < abs(x) < .245:
        return "clavicle", clavicle_form(point)
    return "", Vector()


def in_detail_zone(point):
    x, _, z = point
    lateral = abs(x)
    return ((.262 < lateral < .781 and 1.216 < z < 1.704)
            or (.13 < lateral < .409 and .134 < z < .455)
            or (.012 < lateral < .245 and 1.571 < z < 1.715))


def sculpt_mesh(obj, rig, axes, strength):
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    to_rig = rig.matrix_world.inverted() @ obj.matrix_world
    from_rig = to_rig.inverted().to_3x3()
    rig_space = to_rig == Matrix.Identity(4)
    hits = Counter()
    maximum = 0.0
    for vertex in obj.data.vertices:
        point = vertex.co if rig_space else to_rig @ vertex.co
        if not in_detail_zone(point):
            continue
        region, offset = displacement(point, axes)
        if offset.length_squared < 1e-12:
            continue
        offset *= strength
        vertex.co += offset if rig_space else from_rig @ offset
        maximum = max(maximum, offset.length)
        hits[region] += 1
    obj.data.update()
    return {"regions": dict(hits), "max_displacement_m": round(maximum, 6)}


def apply(scene, profile):
    """Refine the active candidate while preserving topology, weights and clips."""
    config = (profile or {}).get("body_detail", {})
    if not config.get("enabled", True):
        return {"enabled": False}
    strength = float(config.get("strength", 1.0))
    if not 0.0 < strength <= 1.35:
        raise ValueError("Body detail strength must be in (0, 1.35]")
    rig = next(obj for obj in scene.objects if obj.type == "ARMATURE")
    if bpy.context.scene != scene or rig.data.pose_position != "REST":
        raise ValueError("Apply the body detail in the active scene's rest pose before wardrobe fitting")
    selected = {obj.name.removeprefix(LOOKDEV_PREFIX): obj for obj in scene.objects}
    body = next(obj for name, obj in selected.items() if name.startswith(BODY))
    if body.get("Hanuman body detail"):
        raise ValueError("The body detail is already applied to this source")
    axes = {side: axes_for_side(rig, side) for side in ("L", "R")}
    results = {"skin": sculpt_mesh(body, rig, axes, strength)}
    if groom := selected.get(GROOM):
        results["groom"] = sculpt_mesh(groom, rig, axes, strength)
    body["Hanuman body detail"] = strength
    return {"enabled": True, "strength": strength, **results}
