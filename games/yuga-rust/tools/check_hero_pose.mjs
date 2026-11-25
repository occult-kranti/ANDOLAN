// Cross-engine pose oracle. The test keeps the exact node tree, animation accessors and BIN.
// Removing render-only resources from the in-memory JSON lets the production parser run on a CPU.
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { AnimClip, AnimEvaluator, DefaultAnimBinder } from "playcanvas";
import { GlbParser } from "playcanvas/build/playcanvas/src/framework/parsers/glb-parser.js";

const [asset, reference] = process.argv.slice(2);
if (!asset || !reference) throw Error("Usage: node check_hero_pose.mjs <export.glb> <native.json>");
const raw = await readFile(asset);
const native = JSON.parse(await readFile(reference, "utf8"));
const jsonBytes = raw.readUInt32LE(12);
const doc = JSON.parse(raw.subarray(20, 20 + jsonBytes).toString());
const bin = raw.subarray(20 + jsonBytes + 8);
for (const key of ["meshes", "skins", "materials", "textures", "images", "samplers"]) delete doc[key];
for (const node of doc.nodes) {
    delete node.mesh;
    delete node.skin;
}
const options = { skipMeshes: true, buffer: { processAsync: (_buffer, callback) => callback(null, new Uint8Array(bin)) } };
const resources = await new Promise((resolve, reject) => {
    GlbParser.parse("pose.gltf", "", new TextEncoder().encode(JSON.stringify(doc)).buffer,
        null, { loader: { _app: null } }, options, [], (error, value) => error ? reject(error) : resolve(value));
});

const bones = native.bones.map(name => resources.nodes.find(node => node.name === name));
const rama = native.hero_id === "rama";
if (bones.some(bone => !bone) || bones.length !== (rama ? 164 : 167)) throw Error("Source skeleton mismatch");
const scene = resources.scenes[0];
const rest = resources.nodes.map(n => [n.getLocalPosition().clone(), n.getLocalRotation().clone(), n.getLocalScale().clone()]);
const measurements = {};
let count = 0;
for (const [name, samples] of Object.entries(native.clips)) {
    resources.nodes.forEach((n, i) => {
        n.setLocalPosition(rest[i][0]);
        n.setLocalRotation(rest[i][1]);
        n.setLocalScale(rest[i][2]);
    });
    const track = resources.animations.find(a => a.name === name);
    if (!track || track.curves.length === 0) throw Error(`Missing track ${name}`);
    const clip = new AnimClip(track, 0, 1, false, false);
    const evaluator = new AnimEvaluator(new DefaultAnimBinder(scene));
    evaluator.addClip(clip);
    let maxPosition = 0, maxBasis = 0, worst = "";
    for (const { time, values } of samples) {
        clip.time = time;
        evaluator.update(0);
        const length = bones.length * 12;
        if (values.length !== length || !Number.isFinite(time)) throw Error("Invalid native pose data");
        for (let joint = 0; joint < bones.length; joint++) {
            const matrix = bones[joint].getWorldTransform().data;
            for (let column = 0; column < 4; column++) {
                const index = joint * 12 + column * 3;
                const delta = Math.hypot(...[0, 1, 2].map(i => matrix[column * 4 + i] - values[index + i]));
                if (!Number.isFinite(delta)) throw Error("Nonfinite pose");
                if (column < 3) maxBasis = Math.max(delta, maxBasis);
                else if (delta > maxPosition) { maxPosition = delta; worst = `${bones[joint].name}@${time}s`; }
            }
            count++;
        }
    }
    measurements[name] = { samples: samples.length, maxPosition, maxBasis, worst };
}
console.log(JSON.stringify({ godot: native.engine, sha256: createHash("sha256").update(raw).digest("hex"),
    source_glb_sha256: native.source_glb_sha256, source_motion_sha256: native.source_motion_sha256,
    jointPoses: count, measurements }, null, 2));
if (Object.keys(measurements).length !== (rama ? 10 : 5) ||
    Object.values(measurements).some(m => m.maxPosition > .0002 || m.maxBasis > .0002)) process.exitCode = 1;
