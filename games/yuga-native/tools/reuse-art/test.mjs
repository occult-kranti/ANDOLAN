import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Document, NodeIO } from '@gltf-transform/core';
import { inspectContainer, transformStatic, run } from './static-world-preflight.mjs';
const io = new NodeIO();
async function fixture({ seam = false, transparent = false, skinned = false } = {}) {
  const doc = new Document(), buffer = doc.createBuffer();
  const a = (type, array) => doc.createAccessor().setType(type).setArray(array).setBuffer(buffer);
  const positions = a('VEC3', new Float32Array([0,0,0, 1,0,0, 1,1,0, 0,0,0, 1,1,0, 0,1,0]));
  const uv = a('VEC2', new Float32Array([0,0, 1,0, 1,1, seam ? .25 : 0,0, 1,1, 0,1]));
  const material = doc.createMaterial('test-material').setAlphaMode(transparent ? 'BLEND' : 'OPAQUE');
  const primitive = doc.createPrimitive().setAttribute('POSITION', positions).setAttribute('TEXCOORD_0', uv).setMaterial(material);
  const mesh = doc.createMesh('test-mesh').addPrimitive(primitive), node = doc.createNode('COL_test').setMesh(mesh).setTranslation([2,3,4]);
  if (skinned) node.setSkin(doc.createSkin('skin').addJoint(doc.createNode('joint')));
  doc.createScene('test-scene').addChild(node);
  return Buffer.from(await io.writeBinary(doc));
}
const mutateJSON = (bytes, edit) => {
  const n = bytes.readUInt32LE(12), j = JSON.parse(bytes.subarray(20,20+n)); edit(j);
  const text = Buffer.from(JSON.stringify(j)), json = Buffer.concat([text, Buffer.alloc((4-text.length%4)%4,32)]), tail = bytes.subarray(20+n);
  const out = Buffer.alloc(20+json.length+tail.length); bytes.copy(out,0,0,20); out.writeUInt32LE(out.length,8);out.writeUInt32LE(json.length,12);json.copy(out,20);tail.copy(out,20+json.length);return out;
};
test('exact weld reduces duplicate vertices while preserving orientation, UVs and metadata', async () => {
  const r = await transformStatic(await fixture()); assert.equal(r.before.vertices,6);assert.equal(r.after.vertices,4);assert.equal(r.after.triangles,2);
  assert.deepEqual(r.before.primitives,r.after.primitives);
});
test('same-position UV seam remains split', async () => {
  const r = await transformStatic(await fixture({seam:true}));assert.equal(r.after.vertices,5);
});
test('transparent and skinned sources are refused', async () => {
  await assert.rejects(transformStatic(await fixture({transparent:true})),/BLEND/);
  await assert.rejects(transformStatic(await fixture({skinned:true})),/skins\/animations/);
});
test('unsupported extensions, external payloads, malformed headers and animations are refused', async () => {
  const bytes = await fixture();
  for (const [edit, expected] of [[j=>j.extensionsUsed=['EXT_meshopt_compression'],/Unsupported extension/],[j=>j.buffers[0].uri='outside.bin',/embedded/],[j=>j.animations=[{}],/Static meshes/],[j=>j.meshes[0].primitives[0].mode=1,/triangle/],[j=>j.meshes[0].primitives[0].targets=[{}],/morph targets/]]) assert.throws(()=>inspectContainer(mutateJSON(bytes,edit)),expected);
  const bad=Buffer.from(bytes);bad.writeUInt32LE(1,4);assert.throws(()=>inspectContainer(bad),/GLB v2/);
});
test('metadata outside the preservation contract is refused', async () => {
  const bytes = await fixture();
  for (const edit of [j=>j.asset.copyright='author',j=>j.accessors[0].name='semantic-provenance',j=>j.accessors[0].extras={source:'artist'},j=>j.images=[{bufferView:0,mimeType:'image/png',extras:{rights:'author'}}]]) assert.throws(()=>inspectContainer(mutateJSON(bytes,edit)),/metadata/);
});
test('fresh external output only; input retained, repeated destination and repository destination refused', async () => {
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'yuga-static-preflight-')),input=path.join(dir,'input.glb'),output=path.join(dir,'out');
  try {
    const bytes=await fixture();await fs.writeFile(input,bytes);await run(input,output);assert.deepEqual(await fs.readFile(input),bytes);
    await assert.rejects(run(input,input),/may not contain the source/);
    await assert.rejects(run(input,output),/already exists/);
    await assert.rejects(run(input,path.join(path.dirname(fileURLToPath(import.meta.url)),'forbidden-output')),/outside the repository/);
    const link=path.join(dir,'linked');await fs.symlink(dir,link,'dir');await assert.rejects(run(input,path.join(link,'other')),/canonical/);
  } finally {await fs.rm(dir,{recursive:true,force:true});}
});
