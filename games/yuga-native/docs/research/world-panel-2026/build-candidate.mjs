/** Build an offline YUGA browser candidate with a licensed coastal rock kit.
 * The shipped WASM, user inputs and collisions are preserved byte-for-byte.
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { mergeDocuments, tangents, unpartition, unweld, weld } from '@gltf-transform/functions';

const here = path.dirname(fileURLToPath(import.meta.url));
const native = path.resolve(here, '../../..');
const root = path.resolve(native, '../..');
const zip = path.resolve(process.env.YUGA_BASE_GAME_ZIP ||
  path.join(root, 'games/yuga-rust/downloads/yuga-rust-confluence.zip'));
const output = path.resolve(process.argv[2] || '/tmp/yuga-ghat-candidate');
const rockDir = path.join(native, 'art/world-landmark-study/sources/rock_face_01');
const rockGltf = path.join(rockDir, 'rock_face_01_1k.gltf');
const nature = path.join(native, 'assets/world/nature.glb');
const mapPath = path.join(native, 'assets/world/confluence-map.json');
const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const source = JSON.parse(await readFile(path.join(here, 'candidate-plan.json'), 'utf8'));
const zipBytes = await readFile(zip);
assert.equal(digest(zipBytes), source.source_game_zip_sha256, 'release ZIP changed');
const originalMap = await readFile(mapPath);
const natureBytes = await readFile(nature);
const rockBytes = await readFile(rockGltf);
assert.equal(digest(originalMap), source.base_map_sha256, 'base map changed');
assert.equal(digest(natureBytes), source.nature_glb_sha256, 'base nature kit changed');
assert.equal(digest(rockBytes), source.rock_gltf_sha256, 'source rock changed');
for (const [filename, expected] of Object.entries(source.rock_files_sha256)) {
  assert.equal(digest(await readFile(path.join(rockDir, filename))), expected,
    'Rock dependency changed: ' + filename);
}

// Original GLTF geometry and maps are retained. A parent node maps the donor's
// raw bounds to the unit-size preset convention expected by the YUGA map.
const rockJson = JSON.parse(rockBytes.toString('utf8'));
const positionAccessor = rockJson.accessors[rockJson.meshes[0].primitives[0].attributes.POSITION];
const minimum = positionAccessor.min;
const maximum = positionAccessor.max;
const size = maximum.map((v, i) => v - minimum[i]);
const childScale = size.map(v => 1 / v);
const childTranslation = [
  -(minimum[0] + maximum[0]) / (2 * size[0]),
  -minimum[1] / size[1],
  -(minimum[2] + maximum[2]) / (2 * size[2]),
];
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const target = await io.readBinary(natureBytes);
const targetScene = target.getRoot().getDefaultScene();
const beforeNodes = targetScene.listChildren().map(node => node.getName()).sort();
const donor = await io.read(rockGltf);
const { generateTangents } = createRequire(import.meta.url)('mikktspace');
await donor.transform(unweld(), tangents({ generateTangents }), weld());
const mapping = mergeDocuments(target, donor);
const donorScene = mapping.get(donor.getRoot().getDefaultScene());
const donorNodes = donorScene.listChildren();
assert.equal(donorNodes.length, 1);
const actor = target.createNode(source.asset);
const child = donorNodes[0];
child.setScale(childScale).setTranslation(childTranslation);
actor.addChild(child);
targetScene.addChild(actor);
donorScene.dispose();
await target.transform(unpartition());
const mergedBytes = await io.writeBinary(target);

// The released document is an entire offline distribution. Change only its
// visible map payload, nature kit and source notice for this local study.
const releasedHtml = execFileSync('unzip', ['-p', zip, 'yuga-rust.html'], {maxBuffer: 150 * 1024 * 1024}).toString('utf8');
const marker = '<script id="payload" type="application/json">';
const start = releasedHtml.indexOf(marker) + marker.length;
const end = releasedHtml.indexOf('</script>', start);
assert.ok(start >= marker.length && end > start, 'offline payload missing');
const payload = JSON.parse(releasedHtml.slice(start, end));
assert.deepEqual(payload.map, JSON.parse(originalMap));
assert.equal(digest(Buffer.from(payload.blobs.nature, 'base64')), source.nature_glb_sha256);
const map = payload.map;
const natureKit = map.kit_sources.find(kit => kit.id === 'nature');
assert.ok(natureKit && !natureKit.presets.includes(source.asset));
natureKit.presets.push(source.asset);
for (const placement of source.placements) {
  map.props.push({
    ...placement, kit: 'nature', preset: source.asset, collision: 'none'
  });
}
payload.blobs.nature = Buffer.from(mergedBytes).toString('base64');
payload.notices += '\n\nGhat Coast art candidate: Rock Face 01 by Dario Barresi, Poly Haven, CC0. https://polyhaven.com/a/rock_face_01 .';
const candidateHtml = releasedHtml.slice(0, start)
  + JSON.stringify(payload).replace(/</g, '\\u003c')
  + releasedHtml.slice(end);
await mkdir(output, {recursive: true});
await writeFile(path.join(output, 'yuga-rust.html'), candidateHtml);
await writeFile(path.join(output, 'nature-candidate.glb'), mergedBytes);
await writeFile(path.join(output, 'map-candidate.json'), JSON.stringify(map, null, 2) + '\n');
const manifest = {
  source_game_zip_sha256: source.source_game_zip_sha256,
  original_html_sha256: digest(Buffer.from(releasedHtml)),
  candidate_html_sha256: digest(Buffer.from(candidateHtml)),
  map_sha256: digest(Buffer.from(JSON.stringify(map))),
  merged_nature_sha256: digest(mergedBytes),
  nature_bytes: mergedBytes.length,
  added_asset: source.asset,
  donor_vertices: positionAccessor.count,
  donor_triangles: rockJson.accessors[rockJson.meshes[0].primitives[0].indices].count / 3,
  donor_unit_bounds: {minimum, maximum, childScale, childTranslation},
  before_nodes: beforeNodes,
  after_nodes: targetScene.listChildren().map(node => node.getName()).sort(),
  placements: source.placements,
  effect: 'visual placement only; original Rust/WASM and authority are retained',
};
await writeFile(path.join(output, 'build.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify(manifest, null, 2));
