/** Build a non-colliding PBR replacement for the existing rock_island prefab. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {mergeDocuments,unpartition} from '@gltf-transform/functions';

const here=path.dirname(fileURLToPath(import.meta.url));
const native=path.resolve(here,'../../..');
const root=path.resolve(native,'../..');
const baseZip=path.resolve(process.env.YUGA_BASE_GAME_ZIP || path.join(root,'games/yuga-rust/downloads/yuga-rust-confluence.zip'));
const originalNature=path.join(native,'assets/world/nature.glb');
const originalMap=path.join(native,'assets/world/confluence-map.json');
const compactRock=path.join(here,'art/rock-projectile.glb');
const out=path.resolve(process.argv[2] || '/tmp/yuga-ghat-replacement');
const plan=JSON.parse(await readFile(path.join(here,'candidate-plan.json'),'utf8'));
const lod=JSON.parse(await readFile(path.join(here,'evidence/lod/lod-build.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const [zipBytes,natureBytes,mapBytes,rockBytes]=await Promise.all([readFile(baseZip),readFile(originalNature),readFile(originalMap),readFile(compactRock)]);
assert.equal(sha(zipBytes),plan.source_game_zip_sha256,'Released game ZIP changed');
assert.equal(sha(natureBytes),plan.nature_glb_sha256,'Original nature GLB changed');
assert.equal(sha(mapBytes),plan.base_map_sha256,'Original map changed');
assert.equal(sha(rockBytes),lod.output_sha256,'Compact rock changed');

const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const target=await io.readBinary(natureBytes);
const scene=target.getRoot().getDefaultScene();
const beforeNames=scene.listChildren().map(n=>n.getName()).sort();
const old=scene.listChildren().find(n=>n.getName()==='rock_island');
assert.ok(old && old.getMesh() && !old.listChildren().length,'Original rock prefab is unexpected');
const oldMesh=old.getMesh();
scene.removeChild(old);
old.dispose();
if (!target.getRoot().listNodes().some(n=>n.getMesh()===oldMesh)) oldMesh.dispose();
const replacement=await io.readBinary(rockBytes);
const graph=mergeDocuments(target,replacement);
const incomingScene=graph.get(replacement.getRoot().getDefaultScene());
const incoming=incomingScene.listChildren();
assert.equal(incoming.length,1);
incoming[0].setName('rock_island');
scene.addChild(incoming[0]);
incomingScene.dispose();
await target.transform(unpartition());
const afterNames=scene.listChildren().map(n=>n.getName()).sort();
assert.deepEqual(afterNames,beforeNames,'Preset inventory changed');
const merged=await io.writeBinary(target);

const html=execFileSync('unzip',['-p',baseZip,'yuga-rust.html'],{maxBuffer:150*1024*1024}).toString('utf8');
const marker='<script id="payload" type="application/json">';
const start=html.indexOf(marker)+marker.length,end=html.indexOf('</script>',start);
assert.ok(start>=marker.length&&end>start,'Game payload missing');
const payload=JSON.parse(html.slice(start,end));
assert.deepEqual(payload.map,JSON.parse(mapBytes));
assert.equal(sha(Buffer.from(payload.blobs.nature,'base64')),plan.nature_glb_sha256);
payload.blobs.nature=Buffer.from(merged).toString('base64');
payload.notices+='\n\nGhat Coast candidate uses Rock Face 01 by Dario Barresi, Poly Haven, CC0. https://polyhaven.com/a/rock_face_01 .';
const candidate=html.slice(0,start)+JSON.stringify(payload).replace(/</g,'\\u003c')+html.slice(end);
await mkdir(out,{recursive:true});
await writeFile(path.join(out,'yuga-rust.html'),candidate);
await writeFile(path.join(out,'nature-candidate.glb'),merged);
await writeFile(path.join(out,'map-candidate.json'),mapBytes);
const result={
  scope:'The existing two non-colliding rock_island placements use a PBR rock; all map values and authority are unchanged.',
  source_game_zip_sha256:plan.source_game_zip_sha256,original_html_sha256:sha(Buffer.from(html)),
  candidate_html_sha256:sha(Buffer.from(candidate)),base_map_sha256:sha(mapBytes),
  original_nature_sha256:sha(natureBytes),compact_rock_sha256:sha(rockBytes),
  merged_nature_sha256:sha(merged),nature_bytes:merged.length,
  before_presets:beforeNames,after_presets:afterNames,source_triangles:908,replacement_triangles:lod.reduced_triangles,
  rock_placements:2, estimated_added_triangles:2*(lod.reduced_triangles-908),
  attribution:'Rock Face 01 by Dario Barresi, Poly Haven, CC0 1.0; https://polyhaven.com/a/rock_face_01'
};
await writeFile(path.join(out,'build.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
