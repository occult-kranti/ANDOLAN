"""Executable Mandala vertical-play witnesses; run with python3 -m unittest discover."""

import math
import unittest
import physics as m


class Mandala(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = m.World()
        cls.report = m.build(cls.world)
        cls.traces = {t["id"]: t for t in cls.report["traces"]}

    def test_closed_sweeps_do_not_tunnel_or_inflate_corners(self):
        lo = (0.0, 0.0, 0.0)
        hi = (1.0, 1.0, 1.0)
        self.assertAlmostEqual(m.sphere_box((-4, 0.5, 0.5), (8, 0.5, 0.5), 0.25, lo, hi), 3.75 / 12)
        self.assertIsNone(m.sphere_box((-0.4, -0.4, 0.5), (-0.4, -0.4, 0.8), 0.5, lo, hi))
        self.assertAlmostEqual(m.sphere_box((-0.3, -0.4, -1), (-0.3, -0.4, 2), 0.5, lo, hi), 1 / 3)
        self.assertIsNone(m.sphere_box((2, 2, 2), (2, 2, 2), 0.5, lo, hi))
        self.assertEqual(m.sphere_box((0.5, 0.5, 0.5), (0.5, 0.5, 0.5), 0.0, lo, hi), 0.0)

    def test_reject_nonfinite_and_zero_cast(self):
        for bad in ((0, 0, float("nan")), (1, 1, float("inf")), (1, 1)):
            with self.assertRaises(ValueError):
                m.vec(bad)
        with self.assertRaises(ValueError):
            m.shot(self.world, "zero", "Zero", "a", "kodanda", (0, 0, 1), (0, 0, 1))

    def test_private_setup_side_and_fresh_press(self):
        s = m.Setup(self.world)
        for i in range(5):
            s.join("s" + str(i), "sun")
            s.join("m" + str(i), "moon")
        self.assertEqual(len(s.observe("s1")), 5)
        self.assertFalse(any(k[0] == "m" for k in s.observe("s1")))
        self.assertTrue(s.select("s0", "Hanuman"))
        for _ in range(m.PREP - 1):
            s.advance()
        self.assertEqual(s.phase, "prepare")
        for action in ("cast", "fold", "wind", "kindle", "quench"):
            self.assertFalse(s.press("s0", action, True))
        pre = s.actors["s0"].feet
        s.advance()
        self.assertEqual(s.phase, "live")
        self.assertFalse(s.select("s0", "Arjuna"))
        self.assertEqual(s.actors["s0"].feet, pre)
        for action in ("cast", "fold", "wind", "kindle", "quench"):
            self.assertFalse(s.press("s0", action, True))
            s.press("s0", action, False)
            self.assertTrue(s.press("s0", action, True))
        for rnd, expected in (
            (12, "attack"),
            (13, "defence"),
            (24, "defence"),
            (25, "attack"),
            (26, "defence"),
            (30, "defence"),
        ):
            reset = m.Setup(self.world, rnd)
            reset.join("s", "sun")
            self.assertEqual(reset.actors["s"].duty, expected)
            self.assertFalse(reset.held)
            self.assertFalse(reset.kits)

    def test_full_height_body_barriers_at_release(self):
        for d, gate, sign in (("attack", -40.45, 1), ("defence", 40.45, -1)):
            for y in (0.0, 2.4, 6.4, 100.0):
                self.assertTrue(m.barrier_ok(d, (3, gate, y)))
                self.assertFalse(m.barrier_ok(d, (3, gate + sign * 0.001, y)))
            s = m.Setup(self.world)
            side = "sun" if d == "attack" else "moon"
            s.join("actor", side)
            x = 3 if d == "attack" else 8.5206
            s.actors["actor"] = m.Pawn("actor", d, (x, gate - sign * 0.12, 0.0))
            self.assertTrue(s.walk("actor", (0, sign)))
            self.assertAlmostEqual(s.actors["actor"].feet[1], gate)
            self.assertFalse(s.walk("actor", (0, sign)))
            s.advance()
            self.assertFalse(s.walk("actor", (0, sign)))
            s.tick = m.PREP
            self.assertTrue(s.walk("actor", (0, sign)))
            self.assertAlmostEqual(s.actors["actor"].feet[1], gate + sign * 0.25)

    def test_forward_and_home_climbs_both_sides_full_path_and_exit(self):
        for pad in self.world.pads.values():
            d = pad["duty"]
            s = m.Setup(self.world)
            s.join("hero", "sun" if d == "attack" else "moon")
            p = s.actors["hero"]
            s.actors["hero"] = m.Pawn("hero", d, tuple(pad["approach_xyz"]))
            self.assertTrue(s.climb("hero", pad["id"]))
            s.advance()
            self.assertGreater(s.actors["hero"].feet[2], 0.0)
            self.assertFalse(s.walk("hero", (1, 0)))
            self.assertTrue(s.cancel_climb("hero"))
            self.assertEqual(s.actors["hero"].feet, tuple(pad["approach_xyz"]))
            self.assertTrue(s.climb("hero", pad["id"]))
            for _ in range(pad["climb_ticks"]):
                s.advance()
            self.assertEqual(s.actors["hero"].feet, tuple(pad["top_entry_xyz"]))
            self.assertFalse(s.dismount("hero"))
            target = pad["edge_xyz"][0]
            while s.actors["hero"].feet[0] < target - 0.01:
                dx = min(1, (target - s.actors["hero"].feet[0]) / 0.25)
                self.assertTrue(s.walk("hero", (dx, 0)))
                s.advance()
            self.assertTrue(s.dismount("hero"))
            self.assertFalse(s.ability_allowed("hero"))
            for _ in range(pad["descent_ticks"]):
                s.advance()
            self.assertEqual(s.actors["hero"].feet, tuple(pad["egress_xyz"]))
            self.assertTrue(self.world.ground_contact(s.actors["hero"].feet))
            self.assertLess(m.access_time(self.world, pad), 20.0)
            self.assertEqual(m.access_time(self.world, pad) > 10.0, pad["room"] not in ("atk", "def"))

    def test_climb_ownership_reservation_and_occupied_landing(self):
        p = self.world.pads["cloth-loft"]
        s = m.Setup(self.world)
        s.join("a", "sun")
        s.join("b", "sun")
        s.join("c", "moon")
        s.actors["a"] = m.Pawn("a", "attack", tuple(p["approach_xyz"]))
        s.actors["c"] = m.Pawn("c", "defence", tuple(p["approach_xyz"]))
        self.assertFalse(s.climb("c", "cloth-loft"))
        s.actors["b"] = m.Pawn("b", "attack", tuple(p["top_entry_xyz"]))
        self.assertFalse(s.climb("a", "cloth-loft"))
        s.actors["b"] = m.Pawn("b", "attack", (49.0, -68.0, 0.0))
        s.actors["c"] = m.Pawn("c", "defence", (0.0, 112.0, 0.0))
        self.assertTrue(s.climb("a", "cloth-loft"))
        self.assertFalse(s.free("b", p["approach_xyz"]))
        self.assertFalse(s.free("b", p["top_entry_xyz"]))
        for _ in range(p["climb_ticks"]):
            s.advance()
        s.actors["a"] = m.Pawn("a", "attack", tuple(p["edge_xyz"]))
        s.actors["b"] = m.Pawn("b", "attack", tuple(p["egress_xyz"]))
        self.assertFalse(s.dismount("a"))

    def test_wet_speed_and_fixture_boundaries(self):
        self.assertEqual(self.world.walk_speed((-52, 0, 0)), 4.25)
        self.assertEqual(self.world.walk_speed((0, 0, 0)), 5.0)
        s = m.Setup(self.world)
        s.join("p", "sun")
        s.tick = m.PREP
        s.actors["p"] = m.Pawn("p", "attack", (-52.0, 0.0, -0.3))
        self.assertTrue(s.walk("p", (1, 0)))
        self.assertAlmostEqual(s.actors["p"].feet[0] + 52, 0.2125)
        self.assertFalse(self.world.has_floor((-68.0, -128.0, 0.0)))

    def test_opening_advantages_are_seconds_and_optional_folds_shorten_only_b(self):
        opens = {(o["duty"], o["site"]): o for o in self.report["openings"]}
        for (d, site), o in opens.items():
            self.assertTrue(m.barrier_ok(d, o["start_xyz"]))
            self.assertLess(o["live_s"], o["ten_second_live_s"])
            self.assertLess(o["ten_second_live_s"], o["baseline_s"])
            if site == "a":
                self.assertEqual(o["fold_permitted"]["live_s"], o["live_s"])
            else:
                self.assertLess(o["fold_permitted"]["live_s"], o["live_s"] - 2.0)
        self.assertAlmostEqual(
            opens["attack", "a"]["live_s"] - opens["defence", "a"]["live_s"], 0.826, places=3
        )
        self.assertAlmostEqual(
            opens["attack", "b"]["live_s"] - opens["defence", "b"]["live_s"], 1.444, places=3
        )

    def test_two_site_chakra_shields_late_cross_and_distinct_ally(self):
        for t in (self.traces["a-disc-return"], self.traces["b-disc-return"]):
            hits = [e for e in t["events"] if e["type"] in ("contact", "shield-contact")]
            self.assertEqual(
                [(e["id"], e["leg"], e["amount"]) for e in hits],
                [("shielded-guard", "out", 30.0), ("late-crosser", "return", 30.0)],
            )
            self.assertEqual(t["ticks"], 32)
            self.assertEqual(t["points"][-1][1:], t["origin_xyz"])
            self.assertEqual(next(e["tick"] for e in t["events"] if e["type"] == "turn"), 20)
            self.assertLessEqual(max(math.dist(p[1:], t["origin_xyz"]) for p in t["points"]), 12.0001)

    def test_controlled_wind_path_not_displacement_and_recharge(self):
        f = m.Flight(self.world, (0, -0.9, 0))
        self.assertFalse(f.launch("prepare"))
        self.assertTrue(f.launch())
        for _ in range(24):
            f.step(0, 1)
        for _ in range(24):
            f.step(0, -1)
        self.assertAlmostEqual(f.path, 12.0)
        self.assertAlmostEqual(f.feet[1], -0.9)
        self.assertAlmostEqual(f.feet[2], 4.0)
        self.assertFalse(f.launch())
        for _ in range(30):
            f.step()
        self.assertEqual(f.state, "grounded")
        self.assertFalse(f.launch())
        while f.tick < 319:
            f.step()
        self.assertFalse(f.launch())
        f.step()
        self.assertTrue(f.launch())
        for _ in range(10):
            f.step(1, 1)
        self.assertAlmostEqual(f.path, 2.5)

    def test_blocked_ally_and_no_stack_or_free_heights(self):
        a = m.Pawn("ally", "attack", (0.0, 0.0, 0.0))
        self.assertTrue(m.overlaps((0.0, 0.0, 0.8), a))
        self.assertFalse(m.Flight(self.world, (0.0, 0.0, 1.8)).launch())
        f = m.Flight(self.world, (-1.0, 0.0, 0.0))
        self.assertTrue(f.launch())
        f.step(1, 0, False, True, (a,))
        self.assertAlmostEqual(f.feet[0], -1.0)
        self.assertIsNotNone(m.pawn_sweep((-3, 0, 0), (3, 0, 0), a))
        self.assertIsNone(m.pawn_sweep((-3, 0, 2), (3, 0, 2), a))

    def test_ground_surface_roof_and_architectural_solids(self):
        roof = self.traces["pavilion-wind"]
        self.assertAlmostEqual(
            roof["peak_feet_m"], self.world.building.clear_height - m.HEIGHT, places=3
        )
        self.assertIn("ceiling", [e["type"] for e in roof["events"]])
        for id_ in ("a-wind", "b-wind"):
            t = self.traces[id_]
            self.assertEqual(t["peak_feet_m"], 4.0)
            self.assertAlmostEqual(t["horizontal_path_m"], 6.0)
            self.assertEqual(next(e["tick"] for e in t["events"] if e["type"] == "grounded"), 42)
        ground = self.world.segment_hit((0, 0, 3), (0, 0, -1), 0.25)
        self.assertEqual(ground[1], "surveyed-floor")
        self.assertAlmostEqual(ground[0], 0.6875, places=4)
        self.assertTrue(
            self.traces["pavilion-crown-arrow"]["events"][-1]["id"].startswith("pavilion-course-")
        )

    def test_both_sites_full_short_soft_and_shoulder_silhouette(self):
        for id_, cover in (("a-screen", "bell-screen"), ("b-cabinet", "dye-cabinet")):
            self.assertEqual(self.traces[id_ + "-blocked"]["events"][-1]["id"], cover)
            self.assertEqual(self.traces[id_ + "-elevated"]["events"][-1]["id"], "airborne-opponent")
        for body in ("a-trace-table", "b-bale-bench"):
            self.assertEqual(self.traces[body + "-low"]["events"][-1]["id"], body)
            self.assertEqual(self.traces[body + "-high"]["events"][-1]["id"], "elevated-guard")
        for c in self.world.site_covers:
            if c["kind"] == "soft":
                x, n = c["center_xz"]
                self.assertIsNone(self.world.segment_hit((x, n, 0.27), (x + 0.05, n, 0.27), 0.05))
        q = self.report["cover_crosscheck"]
        self.assertEqual(len(q), 14)
        self.assertEqual(sum(p["visible_ground"] + p["visible_reverse"] for p in q), 0)
        self.assertEqual(sum(p["visible_air"] for p in q), 29)

    def test_cast_phase_enemy_capsule_range_and_shield_before_wall(self):
        cast = lambda *args, **kw: m.shot(self.world, "test", "Test", "a", *args, **kw)
        off = cast("kodanda", (0, 0, 1), (0, 1, 1), phase="prepare")
        self.assertFalse(off["events"])
        self.assertEqual(off["ticks"], 0)
        t = cast("gandiva_line", (0, 0, 7), (0, 1, 8))
        self.assertEqual(t["verdict"], "Maximum range")
        self.assertAlmostEqual(math.dist(t["origin_xyz"], t["points"][-1][1:]), 30.0, places=3)
        # Same contact fraction: stationary target spine just behind the wall face.
        shield = m.Pawn("e", "defence", (-6.8, -5.5 + 0.45, 0), shield=True)
        t = cast("kodanda", (-6.8, -8, 1.0), (-6.8, 0, 1.0), (shield,))
        self.assertEqual(t["events"][-1]["id"], "bell-screen")

    def test_all_four_fold_directions_and_occupied_exit(self):
        for src, dest, turns in (
            ("temple_s", "pyramid_s", 1),
            ("pyramid_s", "temple_s", -1),
            ("temple_n", "pyramid_n", -1),
            ("pyramid_n", "temple_n", 1),
        ):
            start = self.world.plan["nodes"][src]["xz"]
            p = m.Pawn("p", "attack", (*start, 0.0))
            self.assertIsNone(m.fold(self.world, p, (0, 1), src, 30, phase="prepare"))
            self.assertIsNone(m.fold(self.world, p, (0, 1), src, 29))
            out = m.fold(self.world, p, (0, 1), src, 30)
            self.assertEqual(out[1], (turns, 0))
            self.assertEqual(out[0][:2], tuple(self.world.plan["nodes"][dest]["xz"]))
            ally = m.Pawn("a", "attack", out[0])
            self.assertIsNone(m.fold(self.world, p, (0, 1), src, 30, others=(ally,)))
            air = m.Pawn("p", "attack", (*start, 0.5))
            self.assertIsNone(m.fold(self.world, air, (0, 1), src, 30))
        self.assertEqual(self.traces["north-fold-arrow"]["events"][-1]["id"], "fold-face-temple_n")
        self.assertEqual(self.traces["south-fold-chakra"]["events"][-1]["id"], "fold-face-temple_s")

    def test_fresh_fold_hold_no_auto_bounce_and_interrupt_on_move(self):
        src = "temple_s"
        p = m.Pawn("p", "attack", (12, -32, 0))
        h = m.FoldHold()
        h.step(self.world, p, (0, 1), src, True, phase="prepare")
        for _ in range(32):
            self.assertIsNone(h.step(self.world, p, (0, 1), src, True))
        h.step(self.world, p, (0, 1), src, False)
        for _ in range(20):
            self.assertIsNone(h.step(self.world, p, (0, 1), src, True))
        h.step(self.world, p, (0, 1), src, True, moving=True)
        for _ in range(29):
            self.assertIsNone(h.step(self.world, p, (0, 1), src, True))
        out = h.step(self.world, p, (0, 1), src, True)
        p = m.Pawn("p", "attack", out[0])
        for _ in range(35):
            self.assertIsNone(h.step(self.world, p, out[1], "pyramid_s", True))

    def test_grounded_objective_offset_defender_and_no_air_prep(self):
        for site in ("a", "b"):
            x, n = self.world.plan["nodes"][site]["xz"]
            hero = m.Pawn("planter", "attack", (x + 2.8, n, 0.0))
            guard = m.Pawn("guard", "defence", (x + 4.2, n, 0.0))
            false_guard = m.Pawn("far", "defence", (x, n, 0.0))
            self.assertTrue(m.can_rite(self.world, "kindle", hero, site))
            self.assertFalse(m.can_rite(self.world, "kindle", hero, site, phase="prepare"))
            for motion in ("thrust", "fall", "climb", "fold"):
                self.assertFalse(m.can_rite(self.world, "kindle", hero, site, motion=motion))
            self.assertTrue(m.can_rite(self.world, "quench", guard, site, vessel=hero.feet))
            self.assertFalse(m.can_rite(self.world, "quench", false_guard, site, vessel=hero.feet))
            self.assertFalse(m.can_rite(self.world, "kindle", m.Pawn("x", "attack", (x, n, 3)), site))
            rite = m.RiteDrill(site)
            for _ in range(79):
                rite.step(self.world, [hero], {hero.id})
            self.assertEqual(rite.step(self.world, [hero], {hero.id}, {hero.id}), "idle")
            for _ in range(79):
                rite.step(self.world, [hero], {hero.id})
            self.assertEqual(rite.step(self.world, [hero], {hero.id}), "lit")
            ally = m.Pawn("other", "defence", (x + 4.0, n + 0.8, 0.0))
            for _ in range(69):
                rite.step(self.world, [ally, guard], {ally.id, guard.id})
            self.assertEqual(rite.progress, 69)
            self.assertEqual(rite.step(self.world, [ally, guard], {ally.id, guard.id}), "quenched")

    def test_simultaneous_heal_resolves_after_damage_no_composition_boost(self):
        casters = [m.Pawn("one", "attack", (-1, 0, 0)), m.Pawn("two", "attack", (1, 0, 0))]
        ally = m.Pawn("three", "attack", (0, 0, 0))
        enemy = m.Pawn("four", "defence", (0, 0.5, 0))
        amounts = m.simultaneous_support(self.world, casters, [ally, enemy], {"three": 296, "four": 260})
        self.assertEqual(amounts, {"three": {"one": 2.0, "two": 2.0}})
        self.assertEqual(m.simultaneous_support(self.world, casters, [ally], {"three": 0}), {})
        self.assertEqual(
            m.simultaneous_support(self.world, casters, [ally], {"three": 270})["three"],
            {"one": 12.0, "two": 12.0},
        )

    def test_return_resweeps_hard_field_and_targets_moving_between_snapshots(self):
        t = self.traces["a-return-screen"]
        self.assertEqual([e["type"] for e in t["events"]], ["release", "turn", "occluded"])
        self.assertEqual(t["events"][-1]["id"], "a-counter-screen")
        self.assertGreater(t["events"][-1]["tick"], 20)

        # Relative motion without the fixed receiver ever occupying the shot centre
        # at tick endpoints. Opposed trajectories cross between two 20 Hz samples.
        def crossing(leg, t):
            return (m.Pawn("cross", "defence", ((-1.5 if t <= 4 else 1.5), 1.5, 0.0)),)

        t = m.shot(self.world, "moving", "Moving", "a", "kodanda", (0, 0, 1.0), (0, 8, 1.0), crossing)
        self.assertEqual(t["events"][-1]["id"], "cross")
        self.assertEqual(t["ticks"], 5)

    def test_launch_from_registered_roof_has_relative_cap_and_commanded_landing(self):
        pad = self.world.pads["cloth-loft"]
        f = m.Flight(self.world, pad["center_xyz"])
        self.assertTrue(f.launch())
        for _ in range(28):
            f.step()
        self.assertAlmostEqual(f.feet[2], pad["height_m"] + 4.0)
        for _ in range(30):
            f.step(hold=False)
        self.assertEqual(f.state, "grounded")
        self.assertEqual(self.world.on_deck(f.feet), "cloth-loft")
        self.assertFalse(f.launch())

    def test_occupied_and_unmarked_cover_never_create_objective_perch(self):
        f = m.Flight(self.world, (3.95, -5.0, 0.0))
        self.assertTrue(f.launch())
        for _ in range(20):
            f.step()
        for _ in range(8):
            f.step(0, -1)
        for _ in range(30):
            f.step(hold=False)
        self.assertEqual(f.state, "grounded")
        self.assertTrue(self.world.ground_contact(f.feet))
        self.assertIn("reset", [e["type"] for e in f.events])
        self.assertIsNone(self.world.solid_hit(f.feet, f.feet, m.RADIUS, m.HEIGHT))

    def test_quench_handoff_restarts_and_cover_can_block_ally_pulse(self):
        rite = m.RiteDrill("b")
        rite.vessel = (42.8, 0.0, 0.0)
        p = m.Pawn("a", "defence", (43.0, 0.0, 0.0))
        q = m.Pawn("b", "defence", (42.0, 0.75, 0.0))
        for _ in range(68):
            rite.step(self.world, [p, q], {"a", "b"})
        self.assertEqual(rite.progress, 68)
        self.assertEqual(rite.step(self.world, [p, q], {"a", "b"}, {"a"}), "quench")
        self.assertEqual((rite.seat, rite.progress), ("b", 1))
        for _ in range(68):
            rite.step(self.world, [p, q], {"b"})
        self.assertEqual(rite.step(self.world, [p, q], {"b"}), "quenched")
        c = m.Pawn("caster", "attack", (3.95, -8.25, 0))
        ally = m.Pawn("ally", "attack", (3.95, -5.7, 0))
        self.assertEqual(m.simultaneous_support(self.world, [c], [ally], {"ally": 240}), {})

    def test_finite_endpoints_registered_floors_and_all_feet_are_clear(self):
        for t in self.traces.values():
            self.assertEqual(t["points"][0][1:], t["origin_xyz"])
            self.assertTrue(all(all(math.isfinite(x) for x in p) for p in t["points"]))
            self.assertEqual(t["points"][-1][0], t["ticks"])
            self.assertTrue(all(a[0] <= b[0] for a, b in zip(t["points"], t["points"][1:])))
        for pad in self.world.pads.values():
            for k in ("approach_xyz", "egress_xyz"):
                p = pad[k]
                self.assertTrue(self.world.ground_contact(p))
                self.assertIsNone(self.world.solid_hit(p, p, m.RADIUS, m.HEIGHT))
            self.assertEqual(self.world.on_deck(pad["top_entry_xyz"]), pad["id"])


if __name__ == "__main__":
    unittest.main()
