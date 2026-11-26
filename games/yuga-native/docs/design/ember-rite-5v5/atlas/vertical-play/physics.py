#!/usr/bin/env python3
"""Reproduce the Mandala vertical-play timing and collision witnesses (standard library)."""

import argparse
from dataclasses import dataclass
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent
NATIVE = ATLAS.parents[3]
REPO = NATIVE.parents[1]
sys.path.insert(0, str(ATLAS))
from audit import audit_geometry, network, shortest, segment_distance
from ritual_rules import rule_constants


def source_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The architecture survey and the original GLB author both own an architecture.py.
# Load the studio's ground reader with its own sibling without shadowing the study.
massing = source_module("mandala_vertical_massing", ATLAS / "massing/architecture.py")
Architecture, world_xy = massing.Architecture, massing.world_xy
_saved_path = sys.path[:]
_previous = sys.modules.get("architecture")
try:
    sys.modules["architecture"] = massing
    GroundSurface = source_module(
        "mandala_vertical_studio", NATIVE / "art/mandala-map-studio/src/catalog.py"
    ).GroundSurface
finally:
    sys.path[:] = _saved_path
    if _previous is None:
        del sys.modules["architecture"]
    else:
        sys.modules["architecture"] = _previous

MAP = ATLAS / "maps/mandala.json"
FLOOR = ATLAS / "massing/mandala.glb"
BUILDING = HERE / "architecture.json"
KIT = NATIVE / "assets/design/rama-ability-kit.json"
RITUAL = REPO / "games/yuga-rust/src/ritual.rs"
RULES = rule_constants()
HZ = RULES["hz"]
DT = 1 / HZ
PREP = 20 * HZ
BARRIER = 40.0
RADIUS, HEIGHT = 0.45, 1.80
CROUCH_HEIGHT = 1.32
LADDER_MPS = 2.2
EPS = 1e-8
UP = (0.0, 0.0, 1.0)
HEROES = HERE / "heroes.json"
PROPOSED = json.loads(HEROES.read_text())["profiles"]
WIND_PROFILE = PROPOSED["vayu_flight"]
WIND = dict(
    id="vayu_flight",
    height_m=WIND_PROFILE["vertical_limit_m"],
    horizontal_mps=WIND_PROFILE["speed_mps"],
    ascent_mps=4.0,
    active_ticks=round(WIND_PROFILE["effect_or_max_travel_s"] * HZ),
    path_m=WIND_PROFILE["max_reach_m"],
    gravity_mps2=9.8,
    charges=WIND_PROFILE["charges"],
    cooldown_ticks=round(WIND_PROFILE["cooldown_s"] * HZ),
)
PROFILES = {}
for name, hero in (("kodanda", "Rama"), ("gandiva_line", "Arjuna"), ("sudarshana_return", "Krishna")):
    profile = PROPOSED[name]
    PROFILES[name] = dict(
        hero=hero,
        speed=profile["speed_mps"],
        reach=profile["max_reach_m"],
        radius=profile["radius_m"],
        tell=profile["windup_s"],
        contact=profile["damage"],
        socket_m=profile["standing_release_m"],
        cooldown_s=profile["cooldown_s"],
    )
    if "return_speed_mps" in profile:
        PROFILES[name]["return_speed"] = profile["return_speed_mps"]
RAMA = next(a for a in json.loads(KIT.read_text())["abilities"] if a["id"] == "kodanda")
for a, b in (
    ("speed", "speed_mps"),
    ("reach", "range_m"),
    ("radius", "radius_m"),
    ("tell", "windup_s"),
    ("contact", "damage"),
):
    if PROFILES["kodanda"][a] != RAMA[b]:
        raise ValueError("Kodanda geometry no longer matches the native design kit")
DUTIES = ("attack", "defence")
START = dict(attack="atk", defence="def")
GATE_SOCKETS = {
    "temple_s": (12.0, -35.3),
    "pyramid_s": (28.0, -36.0),
    "temple_n": (12.0, 35.3),
    "pyramid_n": (28.0, 35.3),
}


def vec(p):
    if len(p) != 3 or any(not isinstance(x, (float, int)) or not math.isfinite(x) for x in p):
        raise ValueError("finite [east, north, up] required")
    return tuple(float(x) for x in p)


def lerp(a, b, f):
    return tuple(x + (y - x) * f for x, y in zip(a, b))


def add(a, d, k=1.0):
    return tuple(x + y * k for x, y in zip(a, d))


def unit(delta):
    length = math.hypot(*delta)
    if length < EPS:
        raise ValueError("zero direction")
    return tuple(x / length for x in delta)


def clean(p):
    return [round(v + 0.0, 4) for v in p]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def box_distance_sq(p, lo, hi):
    return sum(max(l - x, x - h, 0.0) ** 2 for x, l, h in zip(p, lo, hi))


def sphere_box(a, b, radius, lo, hi):
    """First t in [0,1] at which a swept sphere touches the *rounded* box."""
    d = tuple(y - x for x, y in zip(a, b))
    if any(
        max(x, y) < l - radius - EPS or min(x, y) > h + radius + EPS for x, y, l, h in zip(a, b, lo, hi)
    ):
        return None
    if box_distance_sq(a, lo, hi) <= radius**2 + EPS:
        return 0.0
    cuts = {0.0, 1.0}
    for x, v, l, h in zip(a, d, lo, hi):
        if v:
            cuts.update(t for edge in (l, h) if 0 < (t := (edge - x) / v) < 1)
    cuts = sorted(cuts)
    for t0, t1 in zip(cuts, cuts[1:]):
        mid = (t0 + t1) / 2
        aa = bb = 0.0
        cc = -(radius**2)
        for x, v, l, h in zip(a, d, lo, hi):
            m = x + v * mid
            if l <= m <= h:
                continue
            offset = x - (l if m < l else h)
            aa += v * v
            bb += 2 * offset * v
            cc += offset * offset
        if (aa * t0 + bb) * t0 + cc <= EPS:
            return t0
        if aa > EPS:
            disc = bb * bb - 4 * aa * cc
            if disc >= -EPS:
                root = (-bb - math.sqrt(max(0.0, disc))) / (2 * aa)
                if t0 - EPS <= root <= t1 + EPS:
                    return max(t0, min(t1, root))
    return 1.0 if box_distance_sq(b, lo, hi) <= radius**2 + EPS else None


@dataclass(frozen=True)
class Solid:
    id: str
    lo: tuple
    hi: tuple
    kind: str = "cover"


@dataclass(frozen=True)
class Pawn:
    id: str
    duty: str
    feet: tuple
    radius: float = RADIUS
    height: float = HEIGHT
    shield: bool = False

    def spine(self):
        return (add(self.feet, UP, self.radius), add(self.feet, UP, self.height - self.radius))


def make_pads():
    pads = []
    for id_, duty, room, xy, w, d, h in (
        ("spice-loft", "attack", "atk", (5.2, -114.5), 3.2, 3.2, 2.4),
        ("cloth-loft", "attack", "yard_s", (52.0, -69.2), 4.2, 3.6, 3.2),
        ("water-loft", "defence", "def", (-5.2, 114.5), 3.2, 3.2, 2.4),
        ("scale-loft", "defence", "yard_n", (52.0, 69.2), 4.2, 3.6, 3.2),
    ):
        x, n = xy
        pads.append(
            dict(
                id=id_,
                title=id_.replace("-", " ").title(),
                duty=duty,
                room=room,
                center_xyz=[x, n, h],
                size_xz=[w, d],
                height_m=h,
                approach_xyz=[x - w / 2 - 0.60, n, 0.0],
                top_entry_xyz=[x - w / 2 + 0.65, n, h],
                egress_xyz=[x + w / 2 + 0.65, n, 0.0],
                climb_ticks=math.ceil((h + 0.65) / LADDER_MPS * HZ),
                access="West ladder",
                egress="East drop to the same court",
            )
        )
    for p in pads:
        x, n, h = p["center_xyz"]
        w = p["size_xz"][0]
        p["edge_xyz"] = [x + w / 2 - 0.65, n, h]
        p["edge_step_ticks"] = math.ceil(
            math.dist(p["edge_xyz"][:2], p["egress_xyz"][:2]) / RULES["speed"] * HZ
        )
        p["descent_ticks"] = p["edge_step_ticks"] + math.ceil(
            (math.sqrt(1 + 8 * h / (WIND["gravity_mps2"] * DT**2)) - 1) / 2
        )
    return pads


class World:
    def __init__(self):
        self.plan = json.loads(MAP.read_text())
        self.ground = GroundSurface(FLOOR)
        self.links, _ = audit_geometry(self.plan)
        self.pads = {s["id"]: s for s in make_pads()}
        self.solids = []
        # The mock-up owns the hard/soft taxonomy, including the four existing site props.
        arch = json.loads(BUILDING.read_text())
        self.entrances = arch["entrances"]
        self.site_covers = arch["covers"]
        for c in self.site_covers:
            if c["kind"] == "hard":
                self.solids.append(Solid(c["id"], vec(c["min_xyz"]), vec(c["max_xyz"])))
        for c in self.plan["cover"]:
            x, n = c["xz"]
            w, d = c["size"]
            y = self.ground.height(x, n)
            lo = (x - w / 2, n - d / 2, y)
            hi = (x + w / 2, n + d / 2, y + c["height"])
            if not any(math.dist(s.lo, lo) < 0.02 and math.dist(s.hi, hi) < 0.02 for s in self.solids):
                self.solids.append(Solid(slug(c["label"]), lo, hi))
        building = Architecture(self.plan)
        self.building = building
        for part in building.parts:
            if part.name.startswith("Fold threshold inlay"):
                continue
            points = [
                (*world_xy(x, n, building.node, building.bearing), z + building.level)
                for x, n, z in part.vertices
            ]
            lo, hi = zip(*[(min(values), max(values)) for values in zip(*points)])
            self.solids.append(Solid("pavilion-" + slug(part.name), lo, hi, "pavilion"))
        for room, (x, n) in GATE_SOCKETS.items():
            y = self.ground.height(x, n)
            self.solids.append(
                Solid("fold-face-" + room, (x - 2, n - 0.05, y), (x + 2, n + 0.05, y + 3.0), "fold-face")
            )
        for p in self.pads.values():
            x, n, h = p["center_xyz"]
            w, d = p["size_xz"]
            self.solids.append(
                Solid(p["id"], (x - w / 2, n - d / 2, h - 0.20), (x + w / 2, n + d / 2, h), "deck")
            )

    def floor(self, p):
        try:
            return self.ground.height(p[0], p[1])
        except ValueError:
            return None

    def has_floor(self, p, radius=RADIUS):
        return (
            all(
                self.floor(
                    (
                        p[0] + radius * math.cos(i * math.tau / 8),
                        p[1] + radius * math.sin(i * math.tau / 8),
                    )
                )
                is not None
                for i in range(8)
            )
            and self.floor(p) is not None
        )

    def walk_speed(self, p):
        for key, node in self.plan["nodes"].items():
            if all(abs(v - c) <= size / 2 for v, c, size in zip(p, node["xz"], node["size"])):
                incident = [e for e in self.links if key in (e.start, e.end)]
                return RULES["speed"] * (
                    RULES["water"] if all(e.kind == "water" for e in incident) else 1.0
                )
        near = []
        for edge in self.links:
            if edge.kind == "fold":
                continue
            for a, b in edge.segments():
                d = segment_distance(p[:2], a, b)
                if d <= edge.width / 2:
                    near.append((d, edge.kind))
        return RULES["speed"] * (RULES["water"] if near and min(near)[1] == "water" else 1.0)

    def on_deck(self, p):
        for pad in self.pads.values():
            x, n, h = pad["center_xyz"]
            w, d = pad["size_xz"]
            if (
                abs(p[2] - h) < 0.025
                and abs(p[0] - x) <= w / 2 - RADIUS + EPS
                and abs(p[1] - n) <= d / 2 - RADIUS + EPS
            ):
                return pad["id"]
        return None

    def ground_contact(self, p):
        y = self.floor(p)
        return y is not None and abs(p[2] - y) < 0.025 and self.has_floor(p)

    def solid_hit(self, a, b, radius, height=None, ignore=(), projectile=False):
        # A translated upright capsule is a point sweep of its bottom sphere against
        # boxes extended downward by the segment between its two spherical end caps.
        a, b = vec(a), vec(b)
        if height:
            a, b = add(a, UP, radius), add(b, UP, radius)
        hits = []
        for solid in self.solids:
            if solid.id in ignore or (solid.kind == "fold-face" and not projectile):
                continue
            lo = solid.lo
            if height:
                lo = (lo[0], lo[1], lo[2] - (height - 2 * radius))
            t = sphere_box(a, b, radius, lo, solid.hi)
            if t is not None:
                hits.append((t, solid.id))
        return min(hits, default=None)

    def floor_hit(self, a, b, r):
        # Triangle terrain is sampled under the projectile at <= 0.10 m. Refine
        # the first intersecting bracket to one part in 2^13. Empty sky is valid.
        def under(t):
            pos = lerp(a, b, t)
            y = self.floor(pos)
            return y is not None and pos[2] - r <= y + EPS

        if under(0.0):
            return (0.0, "surveyed-floor")
        steps = max(1, math.ceil(math.dist(a, b) / 0.10))
        for i in range(1, steps + 1):
            if not under(i / steps):
                continue
            lo, hi = (i - 1) / steps, i / steps
            for _ in range(13):
                mid = (lo + hi) / 2
                if under(mid):
                    hi = mid
                else:
                    lo = mid
            return (hi, "surveyed-floor")
        return None

    def segment_hit(self, a, b, r):
        hits = [
            h
            for h in (self.solid_hit(a, b, r, projectile=True), self.floor_hit(a, b, r))
            if h is not None
        ]
        return min(hits, default=None)

    def visible(self, a, b):
        return self.segment_hit(a, b, 0.0) is None


def barrier_ok(duty, p, r=RADIUS):
    if duty not in DUTIES:
        raise ValueError("unknown duty")
    return p[1] + r <= -BARRIER + EPS if duty == "attack" else p[1] - r >= BARRIER - EPS


def pawn_sweep(a, b, other, r=RADIUS, h=HEIGHT):
    # Minkowski sum of both upright capsule spines; use true spherical corners.
    lo, hi = other.spine()
    lo = (lo[0], lo[1], lo[2] - (h - 2 * r))
    return sphere_box(add(a, UP, r), add(b, UP, r), r + other.radius - 1e-6, lo, hi)


def overlaps(p, other, r=RADIUS, h=HEIGHT):
    return pawn_sweep(p, p, other, r, h) is not None


def duties(round_number):
    if not 1 <= round_number <= 30:
        raise ValueError("round out of series")
    sun_attacks = round_number <= 12 or (round_number >= 25 and round_number % 2 == 1)
    return {
        "sun": "attack" if sun_attacks else "defence",
        "moon": "defence" if sun_attacks else "attack",
    }


class Setup:
    """Two-sided drill model. State mutation occurs only on a legal step."""

    def __init__(self, world, round_number=1):
        self.world = world
        self.round_number = round_number
        self.roles = duties(round_number)
        self.tick = 0
        self.actors = {}
        self.climbs = {}
        self.descents = {}
        self.kits = {}
        self.held = set()
        self.moved_at = {}

    @property
    def phase(self):
        return "prepare" if self.tick < PREP else "live"

    def join(self, seat, team):
        duty = self.roles[team]
        node = self.world.plan["nodes"][START[duty]]
        # A ten-seat layout is valid without sharing capsules before first input.
        count = sum(a.duty == duty for a in self.actors.values())
        if seat in self.actors or count >= 5:
            raise ValueError("duplicate seat or full duty")
        self.actors[seat] = Pawn(
            seat, duty, (node["xz"][0] + (0, -1.2, 1.2, -2.4, 2.4)[count], node["xz"][1], node["y"])
        )

    def observe(self, seat):
        observer = self.actors[seat]
        # This geometry model emits only same-duty positions. Live enemy vision
        # must come from the server's visibility policy when integrated.
        return {k: p.feet for k, p in self.actors.items() if p.duty == observer.duty}

    def select(self, seat, kit):
        if self.phase != "prepare" or seat not in self.actors:
            return False
        self.kits[seat] = kit
        return True

    def ability_allowed(self, seat):
        return (
            seat in self.actors
            and self.phase == "live"
            and seat not in self.climbs
            and seat not in self.descents
        )

    def press(self, seat, action, down):
        key = (seat, action)
        if not down:
            self.held.discard(key)
            return False
        if key in self.held:
            return False
        self.held.add(key)
        return action in ("cast", "wind", "fold", "kindle", "quench") and self.ability_allowed(seat)

    def advance(self):
        self.tick += 1
        for seat, (pad, elapsed) in list(self.climbs.items()):
            p = self.actors[seat]
            start = pad["approach_xyz"]
            top = pad["top_entry_xyz"]
            elapsed += 1
            lift = math.ceil(pad["height_m"] / LADDER_MPS * HZ)
            sill = (start[0], start[1], top[2])
            pos = (
                lerp(start, sill, elapsed / lift)
                if elapsed <= lift
                else lerp(sill, top, (elapsed - lift) / (pad["climb_ticks"] - lift))
            )
            if (
                not self.free(seat, pos)
                or self.world.solid_hit(p.feet, pos, RADIUS, HEIGHT, ignore=(pad["id"],))
                or (self.phase == "prepare" and not barrier_ok(p.duty, pos))
            ):
                self.cancel_climb(seat)
                continue
            self.actors[seat] = Pawn(seat, p.duty, pos)
            if elapsed >= pad["climb_ticks"]:
                del self.climbs[seat]
            else:
                self.climbs[seat] = (pad, elapsed)
        for seat, (pad, elapsed) in list(self.descents.items()):
            p = self.actors[seat]
            start = pad["edge_xyz"]
            end = pad["egress_xyz"]
            elapsed += 1
            side = pad["edge_step_ticks"]
            past = (end[0], end[1], start[2])
            if elapsed <= side:
                pos = lerp(start, past, elapsed / side)
            else:
                falling = elapsed - side
                pos = (
                    *end[:2],
                    max(end[2], start[2] - 0.5 * WIND["gravity_mps2"] * DT**2 * falling * (falling + 1)),
                )
            if not self.free(seat, pos):
                # Preactivated reservations make this reachable only with a new body
                # supplied externally. Freeze the dismount, retry next tick.
                continue
            self.actors[seat] = Pawn(seat, p.duty, pos)
            if elapsed >= pad["descent_ticks"]:
                del self.descents[seat]
            else:
                self.descents[seat] = (pad, elapsed)

    def free(self, seat, pos, old=None):
        if any(pawn_sweep(old or pos, pos, p) is not None for k, p in self.actors.items() if k != seat):
            return False
        for k, (pad, _) in self.climbs.items():
            if k != seat and any(
                math.dist(pos, pad[marker]) < 2 * RADIUS for marker in ("approach_xyz", "top_entry_xyz")
            ):
                return False
        for k, (pad, _) in self.descents.items():
            if k != seat and math.dist(pos, pad["egress_xyz"]) < 2 * RADIUS:
                return False
        return True

    def climb(self, seat, pad_id):
        p = self.actors[seat]
        pad = self.world.pads.get(pad_id)
        if (
            not pad
            or seat in self.climbs
            or (self.phase == "prepare" and pad["duty"] != p.duty)
            or not self.world.ground_contact(p.feet)
            or math.dist(p.feet, pad["approach_xyz"]) > 0.35
            or not self.free(seat, pad["top_entry_xyz"])
        ):
            return False
        if any(c[0]["id"] == pad["id"] for k, c in self.climbs.items() if k != seat):
            return False
        self.climbs[seat] = (pad, 0)
        return True

    def cancel_climb(self, seat):
        climbing = self.climbs.pop(seat, None)
        if not climbing:
            return False
        p = self.actors[seat]
        self.actors[seat] = Pawn(seat, p.duty, tuple(climbing[0]["approach_xyz"]))
        return True

    def dismount(self, seat):
        p = self.actors[seat]
        pad = self.world.pads.get(self.world.on_deck(p.feet))
        if not pad or seat in self.descents or seat in self.climbs:
            return False
        x, n, h = pad["center_xyz"]
        w, d = pad["size_xz"]
        if math.dist(p.feet, (x + w / 2 - 0.65, n, h)) > 0.36:
            return False
        end = tuple(pad["egress_xyz"])
        if not self.free(seat, end) or not self.world.ground_contact(end):
            return False
        self.descents[seat] = (pad, 0)
        return True

    def walk(self, seat, direction):
        p = self.actors[seat]
        dx, dn = direction
        if not math.isfinite(dx) or not math.isfinite(dn):
            raise ValueError("finite input required")
        length = math.hypot(dx, dn)
        if (
            length < EPS
            or seat in self.climbs
            or seat in self.descents
            or self.moved_at.get(seat) == self.tick
        ):
            return False
        self.moved_at[seat] = self.tick
        speed = self.world.walk_speed(p.feet)
        scale = speed * DT / max(1.0, length)
        end = (p.feet[0] + dx * scale, p.feet[1] + dn * scale, p.feet[2])
        if self.phase == "prepare" and not barrier_ok(p.duty, end):
            end = (end[0], -BARRIER - RADIUS if p.duty == "attack" else BARRIER + RADIUS, end[2])
        if not self.world.has_floor(end):
            return False
        deck = self.world.on_deck(p.feet)
        if deck and self.world.on_deck(end) != deck:
            return False
        if not deck:
            end = (*end[:2], self.world.floor(end))
        if (
            self.world.solid_hit(p.feet, end, RADIUS, HEIGHT, ignore=(deck,))
            or not self.free(seat, end, p.feet)
            or math.dist(p.feet, end) < EPS
        ):
            return False
        self.actors[seat] = Pawn(seat, p.duty, end)
        return True


class Flight:
    """Steer relative to the supported launch, then gravity; allies never recharge/lift."""

    def __init__(self, world, feet):
        self.world = world
        self.feet = vec(feet)
        self.start_y = self.feet[2]
        self.elapsed = 0
        self.path = 0.0
        self.tick = 0
        self.ready_at = 0
        self.state = "grounded"
        self.fall_speed = 0.0
        self.safe_history = [self.feet]
        self.last_ground = self.feet
        self.events = []

    def event(self, kind, id_):
        self.events.append(dict(tick=self.tick, type=kind, id=id_, xyz=clean(self.feet)))

    def launch(self, phase="live"):
        if (
            phase != "live"
            or self.state != "grounded"
            or self.tick < self.ready_at
            or not (self.world.ground_contact(self.feet) or self.world.on_deck(self.feet))
        ):
            return False
        self.start_y = self.feet[2]
        self.safe_history = [self.feet]
        self.path = 0.0
        self.elapsed = 0
        self.state = "thrust"
        self.fall_speed = 0.0
        self.ready_at = self.tick + WIND["cooldown_ticks"]
        self.event("launch", "vayu_flight")
        return True

    def step(self, dx=0.0, dn=0.0, rise=True, hold=True, others=()):
        if not math.isfinite(dx) or not math.isfinite(dn):
            raise ValueError("finite input required")
        self.tick += 1
        if self.state == "grounded":
            return self.feet
        if not hold or self.elapsed >= WIND["active_ticks"]:
            self.state = "fall"
        if self.state == "thrust":
            self.elapsed += 1
            magnitude = math.hypot(dx, dn)
            scale = min(WIND["horizontal_mps"] * DT, WIND["path_m"] - self.path) / max(1.0, magnitude)
            attempted = add(self.feet, (dx, dn, 0.0), max(0.0, scale))

            def free(pos):
                return self.world.has_floor(pos) and not any(
                    pawn_sweep(self.feet, pos, ally) is not None for ally in others
                )

            hit = self.world.solid_hit(
                self.feet, attempted, RADIUS, HEIGHT, ignore=(self.world.on_deck(self.feet),)
            )
            if hit:
                attempted = lerp(self.feet, attempted, max(0.0, hit[0] - 0.001))
                self.event("slide-stop", hit[1])
            if free(attempted):
                self.path += math.dist(self.feet[:2], attempted[:2])
                self.feet = attempted
            if rise:
                higher = (
                    *self.feet[:2],
                    min(self.start_y + WIND["height_m"], self.feet[2] + WIND["ascent_mps"] * DT),
                )
                hit = self.world.solid_hit(
                    self.feet, higher, RADIUS, HEIGHT, ignore=(self.world.on_deck(self.feet),)
                )
                if hit:
                    higher = lerp(self.feet, higher, max(0.0, hit[0] - 0.001))
                    if not any(e["id"] == hit[1] and e["type"] == "ceiling" for e in self.events):
                        self.event("ceiling", hit[1])
                if free(higher):
                    self.feet = higher
            below = (*self.feet[:2], self.world.floor(self.feet))
            if not self.world.solid_hit(self.feet, below, RADIUS, HEIGHT) and not any(
                overlaps(below, ally) for ally in others
            ):
                self.safe_history.append(below)
            return self.feet
        self.fall_speed += WIND["gravity_mps2"] * DT
        end = add(self.feet, UP, -self.fall_speed * DT)
        floor = self.world.floor(end)
        if floor is None:
            self.feet = self.last_ground
            self.state = "grounded"
            self.event("reset", "last-supported")
            return self.feet
        support = floor
        support_id = "surveyed-floor"
        for pad in self.world.pads.values():
            x, n, z = pad["center_xyz"]
            w, d = pad["size_xz"]
            if (
                self.feet[2] + EPS >= z >= end[2] - EPS
                and abs(end[0] - x) <= w / 2 - RADIUS
                and abs(end[1] - n) <= d / 2 - RADIUS
            ):
                support = z
                support_id = pad["id"]
                break
        if end[2] <= support + EPS:
            end = (*end[:2], support)
        hit = self.world.solid_hit(self.feet, end, RADIUS, HEIGHT, ignore=(support_id,))
        # No standing on another pawn, decorative roof, or unmarked cover top.
        # A failed landing restores this standalone drill's prior supported takeoff.
        if hit or any(overlaps(end, ally) for ally in others):
            safe = next(
                (
                    p
                    for p in reversed(self.safe_history)
                    if not any(overlaps(p, ally) for ally in others)
                ),
                None,
            )
            if safe is None:
                self.event("landing-held", "occupied")
                return self.feet
            self.feet = safe
            self.state = "grounded"
            self.event("reset", hit[1] if hit else "occupied")
            return self.feet
        self.feet = end
        if end[2] <= support + EPS:
            self.last_ground = end
            self.state = "grounded"
            self.event("grounded", support_id)
        return self.feet


def can_rite(world, action, seat, site, *, phase="live", vessel=None, motion="grounded"):
    if (
        motion != "grounded"
        or phase != "live"
        or site not in ("a", "b")
        or not world.ground_contact(seat.feet)
    ):
        return False
    centre = world.plan["nodes"][site]["xz"]
    if action == "kindle":
        return seat.duty == "attack" and math.dist(seat.feet[:2], centre) <= RULES["siteRadius"] + EPS
    if action != "quench" or seat.duty != "defence" or vessel is None:
        return False
    vessel = vec(vessel)
    return (
        world.ground_contact(vessel)
        and math.dist(vessel[:2], centre) <= RULES["siteRadius"] + EPS
        and math.dist(seat.feet, vessel) <= RULES["reach"] + EPS
        and world.visible(add(seat.feet, UP, 0.3), add(vessel, UP, 0.3))
    )


def fold(world, seat, facing, room, ticks, *, phase="live", others=(), stationary=True):
    if (
        phase != "live"
        or ticks < round(1.5 * HZ)
        or not stationary
        or not world.ground_contact(seat.feet)
    ):
        return None
    links = [e for e in world.plan["links"] if e["kind"] == "fold" and room in (e["from"], e["to"])]
    if not links:
        return None
    e = links[0]
    src = world.plan["nodes"][room]["xz"]
    if math.dist(seat.feet[:2], src) > e["width"] / 2 - RADIUS + EPS:
        return None
    forward = e["from"] == room
    turns = e["quarter_turns"] * (1 if forward else -1)
    exit_room = e["to"] if forward else e["from"]
    end = world.plan["nodes"][exit_room]

    def turn(p):
        return (p[1], -p[0]) if turns > 0 else (-p[1], p[0])

    offset = turn((seat.feet[0] - src[0], seat.feet[1] - src[1]))
    dest = (*[a + b for a, b in zip(end["xz"], offset)], end["y"])
    if (
        not world.ground_contact(dest)
        or world.solid_hit(dest, dest, RADIUS, HEIGHT)
        or any(overlaps(dest, p) for p in others)
    ):
        return None
    return dest, turn(facing), turns


class FoldHold:
    """A fresh, hands-on channel. A rejected prep press never becomes a live cast."""

    def __init__(self):
        self.key = None
        self.progress = 0
        self.latched = False

    def step(self, world, seat, facing, room, down, *, phase="live", others=(), moving=False):
        if not down:
            self.key = None
            self.progress = 0
            self.latched = False
            return None
        if phase != "live":
            self.latched = True
            self.progress = 0
            return None
        if self.latched:
            return None
        key = (seat.id, room)
        legal = fold(world, seat, facing, room, round(1.5 * HZ), others=(), stationary=not moving)
        if not legal:
            self.key = None
            self.progress = 0
            return None
        if self.key != key:
            self.key = key
            self.progress = 0
        self.progress += 1
        if self.progress < round(1.5 * HZ):
            return None
        self.latched = True
        return fold(world, seat, facing, room, self.progress, others=others)


class RiteDrill:
    """One static site/vessel check; Rust owns the actual round, scoring and timer precedence."""

    def __init__(self, site):
        self.site = site
        self.vessel = None
        self.seat = None
        self.progress = 0
        self.finished = False

    def step(self, world, pawns, held, damage=(), motion=None, phase="live"):
        if self.finished:
            return "finished"
        action = "quench" if self.vessel is not None else "kindle"
        candidates = {
            p.id: p
            for p in pawns
            if p.id in held
            and p.id not in damage
            and can_rite(
                world,
                action,
                p,
                self.site,
                vessel=self.vessel,
                phase=phase,
                motion=(motion or {}).get(p.id, "grounded"),
            )
        }
        chosen = self.seat if self.seat in candidates else min(candidates, default=None)
        if not chosen:
            self.seat = None
            self.progress = 0
            return "idle"
        self.progress = self.progress + 1 if self.seat == chosen else 1
        self.seat = chosen
        if self.progress < RULES[action]:
            return action
        self.seat = None
        self.progress = 0
        if action == "kindle":
            self.vessel = candidates[chosen].feet
            return "lit"
        self.finished = True
        return "quenched"


def shot(
    world,
    id_,
    title,
    site,
    profile,
    origin,
    target,
    receivers=(),
    source_duty="attack",
    phase="live",
    fields=None,
):
    origin, target = vec(origin), vec(target)
    cfg = PROFILES[profile]
    trace = dict(
        id=id_,
        title=title,
        site=site,
        hero=cfg["hero"],
        kind=profile,
        origin_xyz=clean(origin),
        target_xyz=clean(target),
        points=[[0, *clean(origin)]],
        events=[],
    )

    def event(t, name, p, id_):
        trace["events"].append(dict(tick=t, type=name, id=id_, xyz=clean(p)))

    def end(t, why, p):
        trace.update(ticks=t, verdict=why)
        if trace["points"][-1][1:] != clean(p):
            trace["points"].append([t, *clean(p)])
        return trace

    if phase != "live":
        return end(0, "Preparation rejects the cast", origin)
    direction = unit(tuple(b - a for a, b in zip(origin, target)))
    tick = math.ceil(cfg["tell"] * HZ - 1e-9)
    event(tick, "release", origin, profile)
    trace["points"].append([tick, *clean(origin)])
    pos = origin
    hit_ids = set()
    disc = "return_speed" in cfg
    previous = {p.id: p for p in (receivers("out", tick) if callable(receivers) else receivers)}
    for leg in ("out", "return") if disc else ("out",):
        length = cfg["reach"]
        travelled = 0.0
        velocity = cfg.get("return_speed") if leg == "return" else cfg["speed"]
        sign = -1 if leg == "return" else 1
        while travelled < length - EPS:
            tick += 1
            stride = min(velocity * DT, length - travelled)
            nxt = add(pos, direction, stride * sign)
            # Pre-authorized scripted actor motion is sampled on each simulation tick.
            actors = receivers(leg, tick) if callable(receivers) else receivers
            hits = []
            solid = world.segment_hit(pos, nxt, cfg["radius"])
            if solid is not None:
                hits.append((solid[0], 0, solid[1], "occluded"))
            for field in fields(leg, tick) if fields else ():
                collision = sphere_box(pos, nxt, cfg["radius"], field.lo, field.hi)
                if collision is not None:
                    hits.append((collision, 0, field.id, "occluded"))
            for pawn in actors:
                if pawn.id in hit_ids or pawn.duty == source_duty:
                    continue
                old = previous.get(pawn.id, pawn)
                delta = tuple(b - a for a, b in zip(old.feet, pawn.feet))
                lo, hi = old.spine()
                t = sphere_box(pos, add(nxt, delta, -1.0), cfg["radius"] + pawn.radius, lo, hi)
                if t is not None:
                    hits.append((t, 1, pawn.id, "shield-contact" if pawn.shield else "contact"))
            previous = {p.id: p for p in actors}
            for t, _, key, kind in sorted(hits):
                here = lerp(pos, nxt, t)
                event(tick, kind, here, key)
                if kind == "occluded":
                    return end(tick, "Stopped by " + key, here)
                hit_ids.add(key)
                trace["events"][-1].update(leg=leg, amount=cfg["contact"])
                if not disc:
                    return end(tick, "Contact with " + key, here)
            pos = nxt
            travelled += stride
            trace["points"].append([tick, *clean(pos)])
        if disc and leg == "out":
            event(tick, "turn", pos, "frozen-release-anchor")
    event(tick, "return" if disc else "expire", pos, "cast-anchor" if disc else "range")
    return end(tick, "Returned to the release anchor" if disc else "Maximum range", pos)


def simultaneous_support(world, casters, allies, hp_after_damage, max_hp=300.0):
    # Native Battle credits each eligible caster proportionally against the finite
    # missing health, after lethal damage; identical casts have equal weights.
    received = {}
    for ally in allies:
        hp = hp_after_damage[ally.id]
        if hp <= 0 or hp >= max_hp:
            continue
        senders = sorted(
            {
                caster.id
                for caster in casters
                if caster.id != ally.id
                and caster.duty == ally.duty
                and math.dist(caster.feet, ally.feet) <= 3.0
                and world.visible(add(caster.feet, UP, 1.0), add(ally.feet, UP, 1.0))
            }
        )
        if senders:
            restored = min(max_hp - hp, 12.0 * len(senders))
            received[ally.id] = {source: restored / len(senders) for source in senders}
    return received


def dry_route(world, duty, goal):
    links = [e for e in world.links if e.kind in ("walk", "ramp")]
    total, nodes, kinds = shortest(
        network(links),
        START[duty],
        goal,
        {START["defence" if duty == "attack" else "attack"]} | ({"a", "b"} - {goal}),
    )
    pieces = []
    for u, v, k in zip(nodes, nodes[1:], kinds):
        edge = next(e for e in links if {e.start, e.end} == {u, v} and e.kind == k)
        pts = edge.points if u == edge.start else list(reversed(edge.points))
        total_len = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
        for a, b in zip(pts, pts[1:]):
            pieces.append((a, b, edge.time * math.dist(a, b) / total_len, u, v))
    return total, nodes, pieces


def released_start(world, duty, goal, seconds, precision=3):
    total, nodes, segments = dry_route(world, duty, goal)
    remain = float(seconds)
    at = tuple(world.plan["nodes"][START[duty]]["xz"])
    spent = 0.0
    setup_room = nodes[0]
    for a, b, t, u, v in segments:
        if remain <= EPS:
            break
        f = min(1.0, remain / t)
        end = lerp(a, b, f)
        if not barrier_ok(duty, end):
            edge = -BARRIER - RADIUS if duty == "attack" else BARRIER + RADIUS
            f = max(0.0, (edge - a[1]) / (b[1] - a[1]))
            end = lerp(a, b, f)
        k = t * f
        spent += k
        remain -= k
        at = end
        setup_room = v if f >= 1 - EPS else u
        if f < 1 - EPS:
            break
    if not world.has_floor(at) or not barrier_ok(duty, at):
        raise ValueError("illegal opening witness")
    return dict(
        duty=duty,
        site=goal,
        start_room=nodes[0],
        baseline_s=round(total, precision),
        setup_room=setup_room,
        setup_xy=clean(at),
        start_xyz=clean((*at, world.floor(at))),
        safe_setup_s=round(spent, precision),
        live_s=round(total - spent, precision),
        saved_s=round(spent, precision),
        dry_via=list(nodes),
        prep_budget_s=seconds,
    )


def access_time(world, pad):
    spawn = world.plan["nodes"][START[pad["duty"]]]["xz"]
    centre = world.plan["nodes"][pad["room"]]["xz"]
    if pad["room"] == START[pad["duty"]]:
        base = math.dist(spawn, pad["approach_xyz"][:2]) / RULES["speed"]
    else:
        base, _, _ = dry_route(world, pad["duty"], pad["room"])
        base += math.dist(centre, pad["approach_xyz"][:2]) / RULES["speed"]
    return math.ceil(base * HZ - EPS) / HZ + pad["climb_ticks"] / HZ


def flight_trace(world, id_, title, site, origin, controls):
    flight = Flight(world, origin)
    if not flight.launch():
        raise ValueError("illegal flight start")
    points = [[0, *clean(origin)]]
    for dx, dn, rise, hold in controls:
        points.append([flight.tick + 1, *clean(flight.step(dx, dn, rise, hold))])
    if flight.state != "grounded":
        raise ValueError(f"{id_} ends mid-flight")
    return dict(
        id=id_,
        title=title,
        site=site,
        hero="Hanuman",
        kind=WIND["id"],
        origin_xyz=clean(origin),
        target_xyz=points[-1][1:],
        points=points,
        events=flight.events,
        ticks=flight.tick,
        verdict="Grounded after {:.2f} m of horizontal thrust".format(flight.path),
        peak_feet_m=max(row[3] for row in points),
        horizontal_path_m=round(flight.path, 3),
    )


def witnesses(world):
    traces = []

    def arrow(id_, title, site, ability, start, end, others=()):
        traces.append(shot(world, id_, title, site, ability, start, end, others))

    for site in ("a", "b"):
        x, n = world.plan["nodes"][site]["xz"]
        a = (x, n - 3.5, PROFILES["kodanda"]["socket_m"])
        b = (x, n + 3.5, 1.45)
        arrow(
            site + "-dry-shot",
            "Across the " + ("bell" if site == "a" else "weighbeam") + " apron",
            site,
            "kodanda",
            a,
            b,
            (Pawn("opposing-guard", "defence", (x, n + 3.0, 0.0)),),
        )
        origin = (x - 0.5, n - 4.5, 1.35)
        target = (x - 0.5, n + 7.5, 1.35)

        def sidestep(leg, t, x=x, n=n):
            # Strafe at 5 m/s from tick 17. The outward segment clears the body
            # before the crossing. Relative-motion sweeps catch the return contact.
            east = x + 1.75 - min(2.25, max(0.0, (t - 16) * RULES["speed"] * DT))
            return (
                Pawn("shielded-guard", "defence", (x - 0.5, n - 0.3, 0.0), shield=True),
                Pawn("late-crosser", "defence", (east, n + 3.0, 0.0)),
                Pawn("allied-channel", "attack", (x - 0.5, n - 2.0, 0.0)),
            )

        arrow(
            site + "-disc-return",
            "Guarded outstroke and late return contact",
            site,
            "sudarshana_return",
            origin,
            target,
            sidestep,
        )
    for id_, site, x, n, w in (("a-screen", "a", -6.8, -3.5, 4.0), ("b-cabinet", "b", 46.8, 2.5, 5.0)):
        arrow(
            id_ + "-blocked",
            "Standing release into full cover",
            site,
            "kodanda",
            (x, n - w / 2 - 1.2, 1.561),
            (x, n + w / 2 + 1.0, 1.561),
        )
        arrow(
            id_ + "-elevated",
            "High release over full cover",
            site,
            "gandiva_line",
            (x, n - w / 2 - 1.2, 3.65),
            (x, n + w / 2 + 1.0, 3.65),
            (Pawn("airborne-opponent", "defence", (x, n + w / 2 + 1.0, 2.6)),),
        )
    for site, cx, n, ident in (("a", 3.95, -7.05, "a-trace-table"), ("b", 45.6, -7.55, "b-bale-bench")):
        arrow(
            ident + "-low",
            "Low flying disc against the " + ("trace table" if site == "a" else "bale bench"),
            site,
            "sudarshana_return",
            (cx - 2.7, n, 1.35),
            (cx + 4, n, 1.35),
        )
        arrow(
            ident + "-high",
            "Elevated aim clears the " + ("trace table" if site == "a" else "bale bench"),
            site,
            "gandiva_line",
            (cx - 2.7, n, 2.15),
            (cx + 3, n, 2.15),
            (Pawn("elevated-guard", "defence", (cx + 2.9, n, 0.75)),),
        )
    counter = Solid("a-counter-screen", (6.325, 0.5, 0.0), (6.675, 3.5, 2.2), "field")
    traces.append(
        shot(
            world,
            "a-return-screen",
            "A late screen breaks the return",
            "a",
            "sudarshana_return",
            (-3.0, 2.0, 1.35),
            (9.0, 2.0, 1.35),
            fields=lambda leg, t: (counter,) if leg == "return" else (),
        )
    )
    arrow(
        "south-fold-chakra",
        "The return disc meets the south threshold",
        "b",
        "sudarshana_return",
        (12.0, -37.4, 1.35),
        (12.0, -30.0, 1.35),
    )
    arrow(
        "north-fold-arrow",
        "The arrow meets the north threshold",
        "b",
        "kodanda",
        (12.0, 37.4, 1.561),
        (12.0, 30.0, 1.561),
    )
    arrow(
        "pavilion-crown-arrow",
        "Upward shot beneath the pavilion",
        "b",
        "kodanda",
        (28.0, -32.0, 1.561),
        (28.0, -32.0, 8.0),
    )
    for s, x in (("a", 0.0), ("b", 40.0)):
        traces.append(
            flight_trace(
                world,
                s + "-wind",
                "Rise over the " + ("bell" if s == "a" else "weighbeam") + " apron",
                s,
                (x, -3.0, 0.0),
                [(0.0, 1.0, True, True)] * 24 + [(0.0, 0.0, False, False)] * 22,
            )
        )
    traces.append(
        flight_trace(
            world,
            "pavilion-wind",
            "The lintel limits ascent",
            "b",
            (28.0, -32.0, 0.0),
            [(0.0, 0.0, True, True)] * 26 + [(0.0, 0.0, False, False)] * 23,
        )
    )
    return traces


def cover_crosscheck(world):
    """Independent full-world sweeps (including terrain), using the survey's eye samples."""
    report = []
    for door in world.entrances:
        for pocket in door["pockets"]:
            posture = pocket["posture"]
            exposed = 0
            lo_eye = 1.15 if posture == "crouched" else 1.6
            top = CROUCH_HEIGHT if posture == "crouched" else HEIGHT
            counts = []
            for tag, higher, eye, target in (
                ("approach", 0.0, pocket["threat_xz"], pocket["hide_xz"]),
                ("reverse", 0.0, pocket["reverse_threat_xz"], pocket["reverse_hide_xz"]),
                ("raised", 4.0, pocket["threat_xz"], pocket["hide_xz"]),
            ):
                origin = (*eye, world.floor(eye) + 1.60 + higher)
                direction = unit((target[0] - eye[0], target[1] - eye[1], 0.0))
                blocked = 0
                own = 0
                for h in (0.15, lo_eye, top):
                    for w in (-0.28, 0.0, 0.28):
                        end = (
                            target[0] - w * direction[1],
                            target[1] + w * direction[0],
                            world.floor(target) + h,
                        )
                        hit = world.segment_hit(origin, end, 0.0)
                        if hit is not None:
                            blocked += 1
                            if hit[1] == pocket["cover_id"]:
                                own += 1
                counts.append(9 - blocked)
                if tag != "raised" and own != 9:
                    raise ValueError(
                        f"{door['id']}/{pocket['cover_id']}: {tag} has {own}/9 named-cover contacts"
                    )
            if counts[2] != pocket["visible_air_rays"]:
                raise ValueError(
                    f"{door['id']}/{pocket['cover_id']}: {counts[2]} exposed air rays, expected {pocket['visible_air_rays']}"
                )
            report.append(
                dict(
                    entrance=door["id"],
                    cover=pocket["cover_id"],
                    visible_ground=counts[0],
                    visible_reverse=counts[1],
                    visible_air=counts[2],
                    rays_per_stance=9,
                )
            )
    return report


def from_perch(world, pad, site):
    # Register return to the indicated court before following an audited dry line.
    links = [e for e in world.links if e.kind in ("walk", "ramp")]
    total, path, _ = shortest(
        network(links),
        pad["room"],
        site,
        {START["defence" if pad["duty"] == "attack" else "attack"]} | ({"a", "b"} - {site}),
    )
    centre = world.plan["nodes"][pad["room"]]["xz"]
    across = math.dist(pad["top_entry_xyz"], pad["edge_xyz"]) / RULES["speed"]
    back_to_room = math.dist(pad["egress_xyz"][:2], centre) / RULES["speed"]
    return dict(
        live_s=round(across + pad["descent_ticks"] / HZ + back_to_room + total, 3), dry_via=list(path)
    )


def build(world):
    pads = list(world.pads.values())
    for pad in pads:
        pad["spawn_to_top_s"] = round(access_time(world, pad), 3)
        pad["release_to_site"] = {s: from_perch(world, pad, s) for s in ("a", "b")}
    paths = [MAP, FLOOR, KIT, HEROES, RITUAL, ATLAS / "massing/architecture.py"]
    if BUILDING.exists():
        paths.append(BUILDING)
    openings = [released_start(world, duty, site, 20) for duty in DUTIES for site in ("a", "b")]
    for o in openings:
        old = released_start(world, o["duty"], o["site"], 10)
        o["ten_second_live_s"], o["ten_second_start_xyz"] = old["live_s"], old["start_xyz"]
        origin = START[o["duty"]]
        dest = o["site"]
        t, path, kinds = shortest(
            network(world.links), origin, dest, {"atk", "def", "a", "b"} - {origin, dest}
        )
        if path[1] != o["dry_via"][1]:
            raise ValueError(
                "Revise the opening witness; dry and optional fold routes now diverge before release"
            )
        o["fold_permitted"] = {
            "baseline_s": round(t, 3),
            "live_s": round(t - released_start(world, o["duty"], dest, 20, 12)["safe_setup_s"], 3),
            "rooms": list(path),
            "link_kinds": list(kinds),
        }
    return dict(
        schema=1,
        district="mandala",
        axes=["east", "north", "up"],
        rules={
            **RULES,
            "prepare_ticks": PREP,
            "capsule_radius_m": RADIUS,
            "standing_m": HEIGHT,
            "crouched_m": CROUCH_HEIGHT,
            "wind": WIND,
            "projectiles": PROFILES,
            "climb_mps": LADDER_MPS,
        },
        barriers=[
            dict(
                duty=d,
                north_m=-BARRIER if d == "attack" else BARRIER,
                centre_limit_m=-BARRIER - RADIUS if d == "attack" else BARRIER + RADIUS,
                full_height=True,
            )
            for d in DUTIES
        ],
        pads=pads,
        openings=openings,
        traces=witnesses(world),
        cover_crosscheck=cover_crosscheck(world),
        source_sha256={
            str(path.relative_to(REPO)): sha256(path.read_bytes()).hexdigest() for path in paths
        },
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    data = build(World())
    out = HERE / "physics.json"
    encoded = json.dumps(data, indent=2, allow_nan=False, ensure_ascii=False) + "\n"
    if args.check:
        if not out.exists() or encoded != out.read_text():
            raise SystemExit("Stale vertical-play/physics.json")
    else:
        out.write_text(encoded)
    print(
        f"{len(data['traces'])} trajectories, {len(data['pads'])} climb setups, {len(data['openings'])} dry opening comparisons"
    )


if __name__ == "__main__":
    main()
