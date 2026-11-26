"""Regression tests for the documented numerical hero budgets; run with unittest."""

import json
import math
import unittest

import hero_rules as rules


class Study(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = rules.load()
        cls.skills = cls.data["profiles"]

    def test_unique_roster_and_unmodified_live_bow(self):
        rules.check(self.data)

    def test_two_legs_still_one_hit_per_target(self):
        disk = self.skills["sudarshana_return"]
        self.assertEqual(rules.first_contact_counts([5, 8], [9, 8, 5]), (5, 8, 9))
        self.assertEqual(rules.first_contact_counts([], [8, 8]), (8,))
        half = disk["max_reach_m"]
        self.assertAlmostEqual(half / disk["speed_mps"] + half / disk["return_speed_mps"], 1.35)
        self.assertAlmostEqual(half / disk["speed_mps"] + disk["windup_s"], 1.0)

    def test_vertical_range_is_consumed_by_pitch(self):
        for key in ("kodanda", "gandiva_line", "sudarshana_return"):
            r = self.skills[key]["max_reach_m"]
            run, rise = rules.reach(r, 30)
            self.assertAlmostEqual(math.hypot(run, rise), r)
            self.assertLess(run, r)
            self.assertAlmostEqual(rise, r * 0.5)

    def test_cross_site_and_pavilion_remain_grounded_objectives(self):
        j = json.loads((rules.HERE.parent / "maps/mandala.json").read_text())
        nodes = j["nodes"]
        flight = self.skills["vayu_flight"]
        distance = rules.xz_distance(nodes["a"]["xz"], nodes["b"]["xz"])
        self.assertEqual(distance, 40)
        self.assertEqual(distance - 2 * 3 - flight["max_reach_m"], 22)
        h = nodes["bank"]["y"] + flight["vertical_limit_m"]
        self.assertAlmostEqual(h, 5.8)
        self.assertLess(
            h + self.data["field_rig"]["common"]["standing_height_m"], j["architecture"]["height"]
        )
        self.assertEqual(flight["max_reach_m"], flight["speed_mps"] * flight["effect_or_max_travel_s"])

    def test_quench_follows_the_actual_vessel(self):
        # x=4.0 is outside a 3 m disk but 1.2 m from a valid x=2.8 placement.
        self.assertGreater(rules.xz_distance((4, 0), (0, 0)), 3)
        self.assertLess(rules.xz_distance((4, 0), (2.8, 0)), 1.5)
        self.assertGreater(rules.xz_distance((4.4, 0), (2.8, 0)), 1.5)
        self.assertNotEqual(self.skills["vayu_flight"]["shape"], "teleport")


class CrossPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from importlib.util import module_from_spec, spec_from_file_location

        path = rules.NATIVE / "art/mandala-map-studio/src/catalog.py"
        spec = spec_from_file_location("mandala_render_catalog_for_hero_test", path)
        catalog = module_from_spec(spec)
        spec.loader.exec_module(catalog)
        cls.floor = catalog.GroundSurface(rules.HERE.parent / "massing/mandala.glb")
        cls.architecture = json.loads((rules.HERE / "architecture.json").read_text())
        cls.physics = json.loads((rules.HERE / "physics.json").read_text())
        cls.hard = {c["id"]: c for c in cls.architecture["covers"] if c["kind"] == "hard"}
        cls.rig = rules.load()["field_rig"]["common"]

    @staticmethod
    def first_face(start, end, box):
        """Solve each boundary plane separately and accept intersections inside its four edges."""
        low, high = box["min_xyz"], box["max_xyz"]
        if all(a <= value <= b for a, value, b in zip(low, start, high)):
            return 0.0
        direction = [b - a for a, b in zip(start, end)]
        hits = []
        for axis, delta in enumerate(direction):
            if abs(delta) < 1e-10:
                continue
            for bound in (low[axis], high[axis]):
                t = (bound - start[axis]) / delta
                if 0 < t <= 1 and all(
                    low[i] - 1e-7 <= start[i] + t * direction[i] <= high[i] + 1e-7
                    for i in range(3)
                    if i != axis
                ):
                    hits.append(t)
        return min(hits, default=None)

    def visible(self, origin, target):
        hits = [
            (t, key)
            for key, box in self.hard.items()
            if (t := self.first_face(origin, target, box)) is not None
        ]
        return min(hits)[1] if hits else None

    def test_seven_doors_fourteen_pockets_and_two_eyes(self):
        entries = self.architecture["entrances"]
        self.assertEqual(
            {e["id"] for e in entries},
            {"a-bank", "a-mid", "a-temple_s", "a-temple_n", "b-mid", "b-pyramid_s", "b-pyramid_n"},
        )
        self.assertTrue(all(not c["landable"] for c in self.architecture["covers"]))
        ground_rays = 0
        for entrance in entries:
            self.assertEqual(len({p["cover_id"] for p in entrance["pockets"]}), 2)
            for p in entrance["pockets"]:
                for prefix in ("", "reverse_"):
                    ox, oy = p[prefix + "threat_xz"]
                    x, y = p[prefix + "hide_xz"]
                    length = math.hypot(x - ox, y - oy)
                    side = (-(y - oy) / length, (x - ox) / length)
                    ground = self.floor.height(x, y)
                    target_eye = self.rig[p["posture"].replace("crouched", "crouch") + "_eye_m"]
                    top = self.rig[p["posture"].replace("crouched", "crouch") + "_height_m"]
                    eye = [ox, oy, self.floor.height(ox, oy) + self.rig["standing_eye_m"]]
                    points = [
                        (x + side[0] * off, y + side[1] * off, ground + h)
                        for h in (0.15, target_eye, top)
                        for off in (-0.28, 0, 0.28)
                    ]
                    self.assertTrue(
                        all(self.visible(eye, target) == p["cover_id"] for target in points),
                        (entrance["id"], p["cover_id"], prefix),
                    )
                    ground_rays += len(points)
                    px, py = p[prefix + "peek_xz"]
                    self.assertIsNone(
                        self.visible(eye, (px, py, self.floor.height(px, py) + target_eye))
                    )
                    if prefix == "":
                        eye[2] += rules.load()["profiles"]["vayu_flight"]["vertical_limit_m"]
                        self.assertEqual(
                            sum(self.visible(eye, target) is None for target in points),
                            p["visible_air_rays"],
                        )
        self.assertEqual(ground_rays, 252)

    def test_physics_profiles_and_field_counter_windows(self):
        source = rules.load()["profiles"]
        runtime = self.physics["rules"]
        self.assertEqual(runtime["standing_m"], self.rig["standing_height_m"])
        self.assertEqual(runtime["capsule_radius_m"], self.rig["hurt_radius_m"])
        for key, p in runtime["projectiles"].items():
            self.assertEqual(
                (p["reach"], p["speed"], p["radius"], p["tell"], p["contact"]),
                tuple(
                    source[key][s]
                    for s in ("max_reach_m", "speed_mps", "radius_m", "windup_s", "damage")
                ),
            )
        witnesses = {t["id"]: t for t in self.physics["traces"]}
        for id, cover in (("a-trace-table-low", "a-trace-table"), ("b-bale-bench-low", "b-bale-bench")):
            e = witnesses[id]["events"]
            self.assertEqual((e[-1]["tick"], e[-1]["type"], e[-1]["id"]), (7, "occluded", cover))
            high = witnesses[id[:-3] + "high"]["events"]
            self.assertEqual((high[-1]["tick"], high[-1]["type"]), (11, "contact"))
        for site in ("a", "b"):
            contact = [
                e
                for e in witnesses[site + "-disc-return"]["events"]
                if e["type"] in ("contact", "shield-contact")
            ]
            self.assertEqual([(e["tick"], e["leg"]) for e in contact], [(10, "out"), (24, "return")])
            self.assertEqual(len({e["id"] for e in contact}), 2)
            self.assertEqual(witnesses[site + "-wind"]["events"][-1]["tick"], 42)
        self.assertEqual(witnesses["pavilion-wind"]["events"][1]["type"], "ceiling")
        self.assertLess(
            witnesses["pavilion-wind"]["peak_feet_m"], source["vayu_flight"]["vertical_limit_m"]
        )
