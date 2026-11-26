import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { GroundPlan, Rehearsal } from "./engine.mjs";
import { REHEARSAL_SCORE, RehearsalAudio, resolveRehearsalCue } from "./audio.mjs";

const page = readFileSync(new URL("../rehearsal.html", import.meta.url), "utf8");
const { maps, rules } = JSON.parse(page.match(/<script type="application\/json" id="atlas-data">(.*?)<\/script>/s)[1]);
const plans = Object.fromEntries(maps.map(map => [map.id, new GroundPlan(map)]));
const north = [0, 1];
const origin = [-7, -93]; // A clear, walkable section of the Spice Gate to South Temple approach.
const ranges = [
  ["footstep", 18], ["quench_start", 18], ["hanuman_leap", 20],
  ["kali_tandava", 25], ["kindle_start", 30]
];

function hear(type, at, listener = origin, facing = north, plan = plans.mandala) {
  return resolveRehearsalCue(plan, listener, facing, { type, at });
}

test("the adaptive score follows the authored loop, entry times, mix positions and fire-clock duration", () => {
  const score = JSON.parse(readFileSync(new URL("../../../../../art/yagna-audio/score.json", import.meta.url), "utf8"));
  assert.equal(REHEARSAL_SCORE.loopSeconds, score.loop_beats * 60 / score.tempo_bpm);
  assert.equal(REHEARSAL_SCORE.burnSeconds, score.ritual_seconds);
  assert.equal(REHEARSAL_SCORE.burnSeconds, rules.burn / rules.hz);
  assert.equal(REHEARSAL_SCORE.entryFadeSeconds, score.entry_fade_seconds);
  assert.deepEqual(REHEARSAL_SCORE.stems, Object.entries(score.stems)
    .map(([key, stem]) => ({ key, at: stem.entry_seconds, pan: stem.pan })));
});

test("each tactical cue reaches its last legal centimetre and stops across its radius", () => {
  for (const [type, radius] of ranges) {
    for (const distance of [0, radius / 2, radius - .01, radius, radius + .01]) {
      const at = [origin[0], origin[1] + distance];
      assert.ok(plans.mandala.canStand(at));
      const receipt = hear(type, at);
      if (distance > radius) {
        assert.equal(receipt, null, type + " outside radius");
      } else {
        assert.ok(receipt?.gain > 0, type + " at " + distance + " m");
        assert.ok(receipt.text.length > 0);
      }
    }
    const near = hear(type, [origin[0], origin[1] + 2]);
    const far = hear(type, [origin[0], origin[1] + radius]);
    assert.ok(near.gain > far.gain);
    assert.equal(hear(type, [NaN, origin[1]]), null);
    assert.equal(hear(type, undefined), null);
  }
  // These legal Mandala positions are 10.8 m apart in X and 14.4 m apart in Z.
  const listener = [-49, 63], source = [-38.2, 77.4];
  assert.ok(plans.mandala.canStand(listener) && plans.mandala.canStand(source));
  for (const type of ["footstep", "quench_start"]) {
    assert.ok(Number.isFinite(hear(type, source, listener)?.gain));
    assert.equal(hear(type, [source[0], source[1] + .000002], listener), null);
  }
});

test("turning the listener changes the bearing of a stationary source", () => {
  const listener = [0, -112], at = [4, -112];
  const right = hear("footstep", at, listener);
  const left = hear("footstep", at, listener, [0, -1]);
  const ahead = hear("footstep", at, listener, [1, 0]);
  assert.ok(right.pan > 0 && left.pan < 0);
  assert.ok(Math.abs(ahead.pan) < .001);
  assert.notEqual(right.direction, left.direction);
  assert.notEqual(right.text, left.text);
});

test("low cover, tall cover, masonry and a ray grazing a wall have distinct readings", () => {
  const blocked = hear("footstep", [-3.8, -3.5], [-9.8, -3.5]);
  const clear = hear("footstep", [-3.8, 1.5], [-9.8, 1.5]);
  const lectern = hear("footstep", [9.7, 6.6], [3.7, 6.6]);
  const graze = hear("footstep", [-3.8, -1.5], [-9.8, -1.5]);
  const wing = hear("footstep", [26, -34], [25, -37]);
  assert.equal(blocked.occluded, true);
  assert.equal(clear.occluded, false);
  assert.ok(blocked.gain > 0 && blocked.gain < lectern.gain && lectern.gain < clear.gain);
  assert.ok(blocked.cutoff < lectern.cutoff && lectern.cutoff < clear.cutoff);
  assert.equal(graze.occluded, false);
  assert.equal(wing.occluded, true);
  const room = hear("footstep", [27, -30], [27, -33]);
  assert.equal(room.room, plans.mandala.data.architecture.name);
  assert.equal(clear.room, null);
});

test("the two Measure Well basins and dry central sill are distinguishable in captions", () => {
  const well = plans.ayodhya;
  const sill = well.data.nodes.well.xz;
  const dry = hear("footstep", sill, sill, north, well);
  for (const { ring } of well.basins) {
    const centre = [0, 1].map(axis => ring.reduce((sum, p) => sum + p[axis], 0) / ring.length);
    const wet = hear("footstep", centre, sill, north, well);
    assert.ok(well.canStand(centre));
    assert.equal(wet.surface, "water");
    assert.notEqual(dry.surface, wet.surface);
    assert.notEqual(dry.text, wet.text);
  }
});

test("local actions and public results expose only their intended spatial information", () => {
  const stranger = [origin[0], origin[1] + 4];
  for (const type of ["cancel", "drop", "recover", "fold_start", "fold", "handoff"]) {
    assert.ok(hear(type, origin), type + " local");
    assert.equal(hear(type, stranger), null, type + " from another position");
  }
  for (const type of ["kindled", "quenched", "burned", "expired"]) {
    const own = hear(type, origin), remote = hear(type, [564.27, 981.64]);
    assert.ok(own, type);
    assert.equal(own.pan, 0);
    assert.deepEqual(remote, own, type + " is independent of supplied source coordinates");
  }
  assert.equal(hear("hidden_enemy", stranger), null);
  for (const gate of plans.mandala.folds) {
    const entry = plans.mandala.data.nodes[gate.from].xz, exit = plans.mandala.data.nodes[gate.to].xz;
    assert.equal(hear("fold_start", entry, exit), null);
    assert.equal(hear("fold", exit, entry), null);
  }
});

test("steps count actual travel and a blocked fold emits no arrival at either mouth", () => {
  const mandala = plans.mandala, events = [];
  const walk = new Rehearsal(mandala, rules, "explore", "atk", "a", event => events.push(event));
  for (let i = 0; i < 150; i++) walk.step({ z: -1 });
  assert.ok(events.filter(event => event.type === "footstep").length > 0);
  const stop = [...walk.position];
  events.length = 0;
  for (let i = 0; i < 150; i++) walk.step({ z: -1 });
  assert.deepEqual(walk.position, stop);
  assert.deepEqual(events, []);
  const blocked = structuredClone(mandala.data);
  const gate = mandala.folds[0];
  blocked.cover.push({ xz: blocked.nodes[gate.to].xz, size: [2, 2], height: 2, label: "Blocked exit" });
  const runner = new Rehearsal(new GroundPlan(blocked), rules, "explore", gate.from, "a", event => events.push(event));
  for (let i = 0; i < gate.seconds * rules.hz; i++) runner.step({ hold: true });
  assert.deepEqual(runner.position, blocked.nodes[gate.from].xz);
  assert.ok(events.some(event => event.type === "fold_start"));
  assert.ok(!events.some(event => event.type === "fold"));
});

test("one muted listener receives eligible captions once per event ID and can reuse IDs next round", () => {
  const received = [];
  const audio = new RehearsalAudio({ onCaption: cue => { if (cue) received.push(cue); } });
  audio.setMix({ enabled: false, master: 0, mono: true, captions: true });
  for (let round = 0; round < 30; round++) {
    audio.reset();
    audio.listen(plans.mandala, origin, north);
    const start = received.length;
    const event = { type: "kindle_start", at: origin, id: 1 };
    audio.emit({ type: "footstep", at: [origin[0], origin[1] + 18.01], id: 2 });
    audio.emit(event);
    audio.emit(event);
    audio.emit({ type: "cancel", at: [origin[0], origin[1] + 4], id: 3 });
    assert.equal(received.length - start, 1, "round " + (round + 1));
  }
  audio.setMix({ captions: false });
  const start = received.length;
  audio.emit({ type: "kindled", site: "a", id: 4 });
  assert.equal(received.length, start);
});
