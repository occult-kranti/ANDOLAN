// Exercise the authority and art bytes that a player actually downloads.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const { values } = parseArgs({
  options: {
    zip: {
      type: 'string',
      default: fileURLToPath(
        new URL('../downloads/yuga-rust-confluence.zip', import.meta.url),
      ),
    },
    report: { type: 'string' },
  },
});
const member = (name) =>
  execFileSync('unzip', ['-p', values.zip, name], {
    maxBuffer: 128 * 1024 * 1024,
  });
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const manifest = JSON.parse(member('build.json'));
const html = member('yuga-rust.html');
assert.equal(sha(html), manifest.html_sha256);
const data = JSON.parse(
  html
    .toString()
    .match(
      /<script id="payload" type="application\/json">([^<]+)<\/script>/,
    )[1],
);
const model = Buffer.from(data.blobs.hero, 'base64');
assert.equal(sha(model), manifest.blobs.hero.sha256);
if (manifest.hanuman.edition === 'hero-finish') {
  assert.deepEqual(
    model,
    await readFile(
      new URL(
        '../../yuga-native/art/hanuman-hero-finish/models/hanuman-enhanced.glb',
        import.meta.url,
      ),
    ),
  );
} else assert.equal(manifest.hanuman.edition, 'native-motion-export');
const gltf = JSON.parse(model.subarray(20, 20 + model.readUInt32LE(12)));
assert.deepEqual(
  gltf.animations.map((a) => a.name).sort(),
  manifest.hanuman.clips,
);
assert.ok(
  gltf.images.every((image) => image.bufferView !== undefined),
  'all hero textures are embedded',
);
for (const rule of data.kit.abilities)
  assert.ok(manifest.hanuman.clips.includes(rule.motion), rule.motion);
const cover = Buffer.from(data.blobs.cover, 'base64');
assert.equal(sha(cover), manifest.blobs.cover.sha256);
assert.equal(data.coverMime, manifest.cover.mime);
if (data.coverMime === 'image/webp') {
  assert.equal(cover.toString('ascii', 8, 12), 'WEBP');
  assert.deepEqual(
    cover,
    await readFile(
      new URL(
        '../../yuga-native/art/hanuman-hero-finish/design/hanuman-portrait-target.webp',
        import.meta.url,
      ),
    ),
  );
}
const rules = Buffer.from(data.blobs.wasm, 'base64');
assert.deepEqual(
  rules,
  member('yuga-rust.wasm'),
  'players and the room run identical rules',
);
const { instance } = await WebAssembly.instantiate(rules);
const api = instance.exports;
const decode = (p, n) =>
  JSON.parse(Buffer.from(api.memory.buffer, p, n).toString());
const snapshot = (seat) =>
  seat === null
    ? decode(api.trial_snapshot(), api.trial_snapshot_len())
    : decode(api.duel_snapshot(seat), api.duel_snapshot_len());
assert.equal(api.trial_ground_aim(4, 0, 0, 0, 0, 0), 4);
assert.equal(api.trial_start(), 1);
assert.equal(api.trial_ground_aim(4, -13, -18, 0, -10, -21), 2);
assert.equal(api.trial_ground_aim(4, 0, -55, 0.351, 0, -52), 3);
assert.equal(api.trial_ground_aim(4, 0, -55, 0, NaN, -52), 4);
assert.equal(api.trial_ground_aim(99, 0, -55, 0, 0, -52), 4);
const modes = {};
for (const mode of ['practice', 'lane', 'sun-duel', 'moon-duel']) {
  const seat = mode === 'sun-duel' ? 0 : mode === 'moon-duel' ? 1 : null;
  const start = () =>
    seat === null
      ? api.trial_select(mode === 'practice' ? 0 : 1)
      : api.duel_start(0, 0);
  let clear = 0,
    denied = 0,
    probes = 0;
  // Verify each point on a fresh authority so a real cast cannot mask spatial rules with its cooldown.
  for (const [dx, dz] of [
    [0, 0],
    [0, 3],
    [-3, 3],
    [0, 14],
    [0, 14.01],
    [16, 0],
    [6, 6],
  ]) {
    assert.equal(start(), 1);
    const before = snapshot(seat),
      [x, z] = before.actor.pos;
    const target = [x + dx, z + dz * (before.actor.team === 'moon' ? -1 : 1)];
    const preview = () =>
      api.trial_ground_aim(4, x, z, before.actor.y, ...target);
    const code = preview();
    for (let i = 0; i < 192; i++) {
      assert.equal(preview(), code);
      probes++;
    }
    assert.deepEqual(
      snapshot(seat),
      before,
      'preview cannot advance combat or consume a cooldown',
    );
    const accepted =
      seat === null
        ? api.trial_cast(4, ...target, 0, 1)
        : api.duel_cast(seat, 4, ...target, 0, 1);
    assert.equal(
      accepted,
      Number(code === 0),
      mode + ' spatial prediction vs command',
    );
    accepted ? clear++ : denied++;
    const after = snapshot(seat);
    assert.equal(after.abilities[4].cooldown_ticks > 0, !!accepted);
    if (accepted) assert.equal(after.active.id, 'mountain_pulse');
  }
  assert.ok(clear && denied);
  modes[mode] = { clear, denied, repeated_probes: probes };
}
const report = {
  edition: manifest.hanuman.edition,
  zip_sha256: sha(await readFile(values.zip)),
  html_sha256: sha(html),
  model_sha256: sha(model),
  model_bytes: model.length,
  clips: manifest.hanuman.clips,
  skin_joints: gltf.skins.map((s) => s.joints.length),
  surfaces: gltf.meshes.flatMap((m) => m.primitives).length,
  cover_sha256: sha(cover),
  cover_mime: data.coverMime,
  rules_sha256: sha(rules),
  modes,
};
if (values.report)
  await writeFile(values.report, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
