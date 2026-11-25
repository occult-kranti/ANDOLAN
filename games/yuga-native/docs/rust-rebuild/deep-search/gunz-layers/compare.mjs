// Compare actual authored rotation channels at identical clocks, then isolate each overlay scheduler.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { AnimClip, Quat, ANIM_LAYER_OVERWRITE } from "playcanvas";
import { GlbParser } from "playcanvas/build/playcanvas/src/framework/parsers/glb-parser.js";
import { AnimBlend } from "playcanvas/build/playcanvas/src/framework/anim/evaluator/anim-blend.js";
import { AnimTargetValue } from "playcanvas/build/playcanvas/src/framework/anim/evaluator/anim-target-value.js";
import { AnimComponentLayer } from "playcanvas/build/playcanvas/src/framework/components/anim/component-layer.js";

const here = fileURLToPath(new URL(".", import.meta.url));
const [binary, output] = process.argv.slice(2);
assert(binary, "node compare.mjs <prepared-rust-probe> [report.json]");
const root = resolve(here, "../../../../../..");
const asset = "games/yuga/client/assets/heroes/hanuman.glb";
const raw = await readFile(resolve(root, asset));
const length = raw.readUInt32LE(12);
const doc = JSON.parse(raw.subarray(20, 20 + length));
const bin = raw.subarray(28 + length);
const names = doc.skins[0].joints.map(i => doc.nodes[i].name);
const skinSize = names.length;
assert.equal(new Set(names).size, skinSize);
for (const key of ["meshes", "skins", "materials", "textures", "images", "samplers"]) delete doc[key];
for (const node of doc.nodes) { delete node.mesh; delete node.skin; }
doc.animations = doc.animations.filter(a => ["run", "fire", "idle"].includes(a.name));
const options = { skipMeshes: true, buffer: { processAsync: (_, callback) => callback(null, new Uint8Array(bin)) } };
const model = await new Promise((ok, fail) => {
    const data = new TextEncoder().encode(JSON.stringify(doc)).buffer;
    GlbParser.parse("hanuman.gltf", "", data, null, { loader: { _app: null } }, options, [], (e, result) => e ? fail(e) : ok(result));
});
const track = name => model.animations.find(t => t.name === name);
const run = track("run"), fire = track("fire");
// These are the discrete hooks exercised below. Stop if the live controller changes this contract.
const heroController = await readFile(resolve(root, "games/yuga/client/hero-models.ts"), "utf8");
const policy = {
    attackCapS: Number(heroController.match(/actionName === 'fire' \? ([.\d]+) :/)?.[1]),
    enterS: Number(heroController.match(/upper\.blendToWeight\(1, ([.\d]+)\)/)?.[1]),
    exitS: Number(heroController.match(/if \(!fading\) \{ upper\.blendToWeight\(0, ([.\d]+)\)/)?.[1]),
};
assert(Object.values(policy).every(v => Number.isFinite(v) && v > 0), "Review YUGA action timing hooks");
assert(heroController.includes("['spine03', 'Spine2', 'Chest']"), "Review YUGA's upper-body split");
const idlePaths = track("idle").curves.flatMap(c => c.paths);
const chosen = idlePaths.find(p => ["spine03", "Spine2", "Chest"].includes(p.entityPath.at(-1))).entityPath;
const prefix = chosen.join("/");
const curveByJoint = tr => new Map(tr.curves.flatMap((c, i) =>
    c.paths.filter(p => p.propertyPath.at(-1) === "localRotation").map(p => [p.entityPath.at(-1), { c, i, path: p.entityPath.join("/") }])
));
const runCurves = curveByJoint(run), fireCurves = curveByJoint(fire);
const masked = names.map(name => {
    const path = runCurves.get(name).path;
    return path === prefix || path.startsWith(prefix + "/");
});
const dt = 1 / 120, runStart = 0.67, frames = 144;
const payload = [[run.duration, fire.duration, runStart, dt, frames, names.length].join(" ")];
let maxTickErrorSeconds = 0, stepKeys = 0;
function curveWords(tr, lookup, name) {
    const { c } = lookup.get(name);
    const times = tr.inputs[c.input].data, values = tr.outputs[c.output].data;
    assert.equal(values.length, 4 * times.length);
    if (c.interpolation === 0) {
        for (let i = 4; i < values.length; i++) assert.equal(values[i], values[i % 4], "A moving STEP track needs an explicit donor adapter.");
        stepKeys++;
    } else { assert.equal(c.interpolation, 1); }
    const out = [times.length];
    times.forEach((t, i) => {
        const tick = Math.round(t * 4800);
        maxTickErrorSeconds = Math.max(maxTickErrorSeconds, Math.abs(t - tick / 4800));
        out.push(tick, ...values.subarray(4 * i, 4 * i + 4));
    });
    return out;
}
names.forEach((name, i) => payload.push([+masked[i], ...curveWords(run, runCurves, name), ...curveWords(fire, fireCurves, name)].join(" ")));
const result = spawnSync(binary, [], { input: payload.join("\n"), encoding: "utf8", maxBuffer: 20e6 });
if (result.error || result.status !== 0) throw Error(result.error?.message || result.stderr);
const rows = result.stdout.trim().split("\n");
assert.equal(rows.length, frames);
const runClip = new AnimClip(run), fireClip = new AnimClip(fire);
function makeBlend() {
    const comp = { layers: [], normalizeWeights: false, dirtifyTargets() {} };
    const stubController = { update() {} };
    const lower = new AnimComponentLayer("Base", stubController, comp, 1, ANIM_LAYER_OVERWRITE);
    const upper = new AnimComponentLayer("Action", stubController, comp, 0, ANIM_LAYER_OVERWRITE);
    comp.layers.push(lower, upper);
    return { upper, blend: (base, action, useAction) => {
        const v = new AnimTargetValue(comp, AnimTargetValue.TYPE_QUAT);
        v.baseValue = [0, 0, 0, 1];
        v.setMask(0, 1); v.setMask(1, +useAction);
        v.updateValue(0, base);
        v.counter++;
        v.updateValue(1, action);
        return v.value;
    }};
}
const production = makeBlend(), controlled = makeBlend();
production.upper.blendToWeight(1, policy.enterS);
const norm = q => { const n = Math.hypot(...q); return q.map(v => v / n); };
function degrees(a, b) {
    const p = norm(a), q = norm(b);
    const sign = p.reduce((s, v, j) => s + v * q[j], 0) < 0 ? -1 : 1;
    const chord = Math.hypot(...p.map((v, i) => v - sign * q[i]));
    return 4 * Math.asin(Math.min(1, chord / 2)) * 180 / Math.PI;
}
const worst = {};
function measure(key, angle, joint, frame) {
    assert(Number.isFinite(angle));
    if (!worst[key] || angle > worst[key].degrees) worst[key] = { degrees: angle, joint, frame };
}
const timeline = [], milestones = {};
let donorLast = 0, yugaLast = 0, release = false, wrapped = false, prev = runStart;
rows.forEach((line, f) => {
    const row = line.split(" ").map(Number), [runTime, fireTime, weight] = row;
    assert.equal(row.length, 3 + names.length * 4);
    const elapsed = (f + 1) * dt;
    // YUGA starts actionUntil at the time of the event and checks it on successive updates.
    if (!release && f * dt >= Math.min(policy.attackCapS, fire.duration)) {
        release = true;
        production.upper.blendToWeight(0, policy.exitS);
    }
    production.upper.update(dt);
    controlled.upper.weight = weight;
    if (weight > 1e-5) donorLast = elapsed;
    if (production.upper.weight > 1e-5) yugaLast = elapsed;
    if (weight >= .99999 && !milestones.donorFullS) milestones.donorFullS = elapsed;
    if (production.upper.weight >= .99999 && !milestones.yugaFullS) milestones.yugaFullS = elapsed;
    if (f % 6 === 0 || [1, 2, 3, 5, 71, 83, 87, 92].includes(f)) {
        timeline.push({ elapsedS: elapsed, donorWeight: weight, yugaWeight: production.upper.weight });
    }
    if (runTime < prev) wrapped = true;
    prev = runTime;
    run.eval(runTime, runClip.snapshot);
    fire.eval(fireTime, fireClip.snapshot);
    names.forEach((name, i) => {
        const base = norm(runClip.snapshot._results[runCurves.get(name).i]);
        const action = norm(fireClip.snapshot._results[fireCurves.get(name).i]);
        const rust = row.slice(3 + 4 * i, 7 + 4 * i);
        const matched = controlled.blend(base, action, masked[i]);
        const live = production.blend(base, action, masked[i]);
        measure("matchedWeight", degrees(rust, matched), name, f + 1);
        measure("productionEnvelope", degrees(rust, live), name, f + 1);
        const fireCurve = fireCurves.get(name).c;
        if (masked[i] && weight >= .99999 && fireCurve.interpolation === 1 &&
            fire.inputs[fireCurve.input].data.some(key => Math.abs(key - fireTime) < 0.000002)) {
            measure("fullWeightMovingActionOnKey", degrees(rust, matched), name, f + 1);
        }
        if (!masked[i]) measure("lowerBodyVsUnmodifiedRun", degrees(rust, base), name, f + 1);
        if (masked[i]) measure("upperBodyActionVsPlainRun", degrees(matched, base), name, f + 1);
    });
});
Object.assign(milestones, { donorLastOverlayS: donorLast, yugaLastOverlayS: yugaLast });
assert(wrapped && !masked[names.indexOf("upperleg01.L")] && masked[names.indexOf("wrist.R")]);
assert.equal(names.filter(n => n === "Bip01 Spine1").length, 0);
assert(maxTickErrorSeconds < 0.000001);
assert(worst.lowerBodyVsUnmodifiedRun.degrees < 0.05 && worst.fullWeightMovingActionOnKey.degrees < 0.05, JSON.stringify(worst));
assert(worst.upperBodyActionVsPlainRun.degrees > 5 && worst.productionEnvelope.degrees > worst.matchedWeight.degrees);
assert(worst.matchedWeight.degrees < 8.5 && worst.productionEnvelope.degrees < 79, "Review the wrist and recovery poses");
const selected = worst.matchedWeight;
const keyCurve = fireCurves.get(selected.joint).c;
const times = fire.inputs[keyCurve.input].data;
const actionTime = Number(rows[selected.frame - 1].split(" ", 2)[1]);
const right = times.findIndex(t => t >= actionTime);
assert(right > 0);
const keys = fire.outputs[keyCurve.output].data;
const leftKey = keys.slice(4 * (right - 1), 4 * right);
const rightKey = keys.slice(4 * right, 4 * right + 4);
const keyInterval = {
    joint: selected.joint, actionTime, leftSeconds: times[right - 1], rightSeconds: times[right],
    fraction: (actionTime - times[right - 1]) / (times[right] - times[right - 1]),
    endpointRotationDegrees: degrees(leftKey, rightKey),
};
// Offline bake experiment on the measured interval. New keys follow the original shortest
// spherical arc. Existing PlayCanvas normalized-linear interpolation then reads those keys.
const toQuat = key => new Quat(...norm(key));
const toArray = q => [q.x, q.y, q.z, q.w];
const spherical = t => toArray(new Quat().slerp(toQuat(leftKey), toQuat(rightKey), t));
const midpointBake = [1, 2, 4].map(segments => {
    let maxDegrees = 0;
    for (let j = 0; j <= 120; j++) {
        const t = j / 120;
        const segment = Math.min(segments - 1, Math.floor(t * segments));
        const baked = spherical(segment / segments);
        AnimBlend.blend(baked, spherical((segment + 1) / segments), t * segments - segment, "quaternion");
        maxDegrees = Math.max(maxDegrees, degrees(baked, spherical(t)));
    }
    return { segments, extraKeys: segments - 1, samples: 121, maxDegrees };
});
assert(midpointBake[2].maxDegrees < .2 && midpointBake[0].maxDegrees > 7);
const round = (_, value) => typeof value === "number" ? Number(value.toFixed(8)) : value;
const report = {
    donor: "OpenRsG/GunZRs@485575b7451912ed1d62661c388663b08dce4faf",
    donorMath: "glam 0.32.1", playcanvas: JSON.parse(await readFile(resolve(root, "node_modules/playcanvas/package.json"))).version,
    asset, sha256: createHash("sha256").update(raw).digest("hex"),
    clips: { runSeconds: run.duration, fireSeconds: fire.duration, baseStartsAt: runStart },
    split: { donorDefault: "Bip01 Spine1", matches: 0, yugaPath: prefix, upper: masked.filter(Boolean).length, lower: masked.filter(x => !x).length },
    frequencyHz: 1 / dt, frames, rotationPairs: frames * names.length, constantStepTracks: stepKeys, maxTickErrorSeconds, runWrapped: wrapped,
    policy, milestones, worst, largestMatchedWeightKeyInterval: keyInterval, wristIntervalBake: midpointBake, timeline,
};
const json = JSON.stringify(report, round, 2) + "\n";
if (output) await writeFile(output, json);
console.log(JSON.stringify({ ...report, timeline: undefined }, round, 2));
