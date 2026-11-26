import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { checkGlb, checkPackage } from './check.mjs';

const directory = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(directory, '../../games/yuga-native/art/daftar-route-lab');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.json')));
const original = fs.readFileSync(path.join(root, 'daftar-route-lab.glb'));

function changedJson(change) {
  const length = original.readUInt32LE(12);
  const value = JSON.parse(original.subarray(20, 20 + length));
  change(value);
  const text = Buffer.from(JSON.stringify(value));
  const padded = Buffer.alloc(Math.ceil(text.length / 4) * 4, 32); text.copy(padded);
  const rest = original.subarray(20 + length), result = Buffer.alloc(20 + padded.length + rest.length);
  original.copy(result, 0, 0, 20); result.writeUInt32LE(result.length, 8); result.writeUInt32LE(padded.length, 12);
  padded.copy(result, 20); rest.copy(result, 20 + padded.length);
  return result;
}

test('the delivered package has actual metre-scale vertex bounds, exact spawns and bound Blender evidence', () => {
  const result = checkPackage();
  assert.equal(result.nodes, 73);
  assert.equal(result.positionSamples, 11602);
  assert.deepEqual(result.gltfBoundsMinM, [-24, -0.4, -28]);
  assert.deepEqual(result.gltfBoundsMaxM, [24, 3.37, 28]);
  assert.equal(result.spawnMarkersVerified, 10);
  assert.equal(result.engineLaunchedByThisCheck, false);
  assert.equal(result.unrealExecuted, false);
});

test('truncated or external GLB payloads fail before geometry acceptance', () => {
  assert.throws(() => checkGlb(original.subarray(0, original.length - 4), manifest), /length/);
  assert.throws(() => checkGlb(changedJson(value => { value.buffers[0].uri = 'https://example.test/mesh.bin'; }), manifest), /External/);
  assert.throws(() => checkGlb(changedJson(value => { value.accessors[0].byteOffset = 2 ** 30; }), manifest), /escapes/);
});

test('scene scale and spawn placement are measured from the actual GLB', () => {
  assert.throws(() => checkGlb(changedJson(value => { value.nodes.forEach(node => { node.scale = [100, 100, 100]; }); }), manifest), /bounds/);
  assert.throws(() => checkGlb(changedJson(value => {
    const node = value.nodes.find(row => row.extras?.spawn_id === 'spawn_south_01'); node.translation[0] += 1;
  }), manifest), /Spawn coordinate/);
  assert.throws(() => checkGlb(changedJson(value => {
    const node = value.nodes.find(row => row.extras?.spawn_id === 'spawn_south_01'); delete node.extras.spawn_id;
  }), manifest), /ten spawn/);
});

test('edited artifacts and stale reimport receipts cannot reuse the original package acceptance', t => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'daftar-route-integrity-'));
  t.after(() => fs.rmSync(temporary, { recursive: true, force: true }));
  fs.cpSync(root, temporary, { recursive: true });
  fs.appendFileSync(path.join(temporary, 'build_route_lab.py'), '\n# Synthetic tamper fixture only.\n');
  assert.throws(() => checkPackage(temporary), /Procedural source/);
  fs.copyFileSync(path.join(root, 'build_route_lab.py'), path.join(temporary, 'build_route_lab.py'));
  const evidence = JSON.parse(fs.readFileSync(path.join(temporary, 'geometry-acceptance.json')));
  evidence.manifest_sha256 = '0'.repeat(64);
  fs.writeFileSync(path.join(temporary, 'geometry-acceptance.json'), JSON.stringify(evidence));
  assert.throws(() => checkPackage(temporary), /Stored Blender evidence/);
});

test('artifact paths cannot escape the reviewed package directory', t => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'daftar-route-path-'));
  t.after(() => fs.rmSync(temporary, { recursive: true, force: true }));
  const changed = structuredClone(manifest);
  changed.files = { '../outside.bin': { bytes: 1, sha256: '0'.repeat(64) }, ...changed.files };
  fs.writeFileSync(path.join(temporary, 'manifest.json'), JSON.stringify(changed));
  assert.throws(() => checkPackage(temporary), /direct children/);
});
