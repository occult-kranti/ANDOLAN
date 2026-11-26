import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { GroundPlan } from "../rehearsal/engine.mjs";

const page = readFileSync(new URL("fieldbook.html", import.meta.url), "utf8");
const field = JSON.parse(page.match(/id="field-data">([^<]+)<\/script>/)[1]);
test("every physical site connection has two reachable, collision-backed shelter records", () => {
  let entries = 0;
  for (const map of field.maps) {
    const plan = new GroundPlan(map);
    for (const site of ["a", "b"]) {
      const room = map.nodes[site],
        entrances = map.entrances.filter((e) => e.site === site);
      const physical = map.links.filter(
        (link) => [link.from, link.to].includes(site) && link.kind !== "fold",
      );
      assert.deepEqual(
        entrances.map((e) => e.approach).sort(),
        physical.map((l) => (l.from === site ? l.to : l.from)).sort(),
      );
      assert.ok(plan.canStand(room.xz));
      for (const entry of entrances) {
        const ids = new Set(entry.pockets.map((p) => p.cover_id));
        assert.equal(ids.size, 2);
        entries++;
        for (const pocket of entry.pockets) {
          const block = map.studyCovers.find((c) => c.id === pocket.cover_id);
          assert.ok(block && block.collision !== false);
          assert.equal(plan.canStand(block.center_xz), false, block.id);
          for (const key of [
            "threat_xz",
            "hide_xz",
            "body_hide_xz",
            "reverse_body_hide_xz",
            "peek_xz",
            "reverse_threat_xz",
            "reverse_hide_xz",
            "reverse_peek_xz",
          ]) {
            if (pocket[key])
              assert.ok(
                plan.canStand(pocket[key]),
                map.id + " / " + entry.id + " / " + key,
              );
          }
          // The same floor and collision solver that moves the browser pawn must allow the final peek.
          for (const prefix of ["", "reverse_"]) {
            const from = pocket[prefix + "hide_xz"],
              to = pocket[prefix + "peek_xz"];
            if (from)
              assert.ok(
                plan.canReach(from, to, 10),
                map.id + " / " + entry.id + " / peek",
              );
            const deep = pocket[prefix + "body_hide_xz"];
            if (deep)
              assert.ok(
                plan.canReach(deep, from, 1),
                map.id + " / " + entry.id + " / shoulder",
              );
          }
        }
      }
    }
  }
  assert.equal(entries, 27);
});
test("all recorded side and plan charts use finite ordered tick samples", () => {
  assert.equal(field.rate, 20);
  const ids = new Set();
  for (const trace of field.traces) {
    assert.ok(!ids.has(trace.id));
    ids.add(trace.id);
    assert.ok(trace.points.length > 1);
    assert.ok(trace.ticks >= trace.points.at(-1)[0]);
    for (const [i, p] of trace.points.entries()) {
      assert.ok(p.length === 4 && p.every(Number.isFinite));
      if (i) assert.ok(p[0] >= trace.points[i - 1][0]);
    }
    for (const e of trace.events)
      assert.ok(e.xyz.length === 3 && e.xyz.every(Number.isFinite));
  }
  assert.ok(ids.size >= 19);
});
