import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { initialize, libraries, inspectContainer, transformStatic, run } from './webp-static-preflight.mjs';

const runtime = await initialize();
const { Document, io, EXTTextureWebP } = runtime;
// Original one-pixel RGB128 lossless WebP, generated with Pillow for this fixture.
const WEBP = Buffer.from('524946461e000000574542505650384c110000002f000000000750c00216b0ff8188e87f0000', 'hex');
export async function fixture({ seam = false, transparent = false, skinned = false, animated = false, webp = false, reverse = false, padding = [] } = {}) {
  const doc = new Document(), buffer = doc.createBuffer();
  const a = (type, array) => doc.createAccessor().setType(type).setArray(array).setBuffer(buffer);
  const positions = a('VEC3', new Float32Array([0,0,0,1,0,0,1,1,0,0,0,0,1,1,0,0,1,0]));
  const uv = a('VEC2', new Float32Array([0,0,1,0,1,1,seam ? .25 : 0,0,1,1,0,1]));
  const material = doc.createMaterial('source-material').setAlphaMode(transparent ? 'BLEND' : 'OPAQUE').setExtras({ purpose:'original fixture' });
  if (webp) {
    doc.createExtension(EXTTextureWebP).setRequired(true);
    const texture = doc.createTexture('original-pixel').setMimeType('image/webp').setImage(Buffer.concat([WEBP,Buffer.from(padding)]));
    material.setBaseColorTexture(texture);
    material.getBaseColorTextureInfo().setWrapS(33071).setWrapT(33648).setMagFilter(9728);
  }
  const prim = doc.createPrimitive().setAttribute('POSITION',positions).setAttribute('TEXCOORD_0',uv).setMaterial(material).setExtras({ role:'surface' });
  if (reverse) prim.setIndices(a('SCALAR',new Uint16Array([2,1,0,5,4,3])));
  const mesh = doc.createMesh('fixture-mesh').addPrimitive(prim).setExtras({ author:'YUGA fixture' });
  const node = doc.createNode('source-node').setMesh(mesh).setTranslation([2,3,4]).setExtras({ protected:'node metadata' });
  if (skinned) node.setSkin(doc.createSkin('skin').addJoint(doc.createNode('joint')));
  if (animated) {
    const sample=doc.createAnimationSampler().setInput(a('SCALAR',new Float32Array([0,1]))).setOutput(a('VEC3',new Float32Array([0,0,0,1,0,0])));
    doc.createAnimation('source-action').addSampler(sample).addChannel(doc.createAnimationChannel().setSampler(sample).setTargetNode(node).setTargetPath('translation'));
  }
  doc.createScene('source-scene').addChild(node);
  return Buffer.from(await io.writeBinary(doc));
}
export const mutateJSON=(bytes,edit)=>{
  const n=bytes.readUInt32LE(12),j=JSON.parse(bytes.subarray(20,20+n));edit(j);
  const text=Buffer.from(JSON.stringify(j)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]),tail=bytes.subarray(20+n);
  const out=Buffer.alloc(20+json.length+tail.length);bytes.copy(out,0,0,20);out.writeUInt32LE(out.length,8);out.writeUInt32LE(json.length,12);json.copy(out,20);tail.copy(out,20+json.length);return out;
};

test('existing exact weld/reorder preserves full oriented attribute surface, seams and metadata',async()=>{
  const a=await transformStatic(await fixture()),b=await transformStatic(await fixture({seam:true}));
  assert.equal(a.before.vertices,6);assert.equal(a.after.vertices,4);assert.equal(a.after.triangles,2);
  assert.equal(b.after.vertices,5);assert.deepEqual(a.before.primitives,a.after.primitives);
});
test('required embedded WebP payload and sampler/material metadata survive exact optimization',async()=>{
  const input=await fixture({webp:true}),result=await transformStatic(input);
  const before=await io.readBinary(input),after=await io.readBinary(result.candidate);
  assert.deepEqual(Buffer.from(before.getRoot().listTextures()[0].getImage()),Buffer.from(after.getRoot().listTextures()[0].getImage()));
  assert.deepEqual(before.getRoot().listMaterials()[0].getExtras(),after.getRoot().listMaterials()[0].getExtras());
  assert.equal(after.getRoot().listMaterials()[0].getBaseColorTextureInfo().getWrapT(),33648);
  assert.ok(inspectContainer(result.candidate).extensionsRequired.includes('EXT_texture_webp'));
});
test('valid publisher padding is retained as image bytes rather than trimmed',async()=>{
  const input=await fixture({webp:true,padding:[32,32]}),r=await transformStatic(input);
  const image=(await io.readBinary(r.candidate)).getRoot().listTextures()[0].getImage();
  assert.deepEqual(Buffer.from(image),Buffer.concat([WEBP,Buffer.from([32,32])]));
});
test('winding reversal changes the exact oriented surface identity',async()=>{
  const a=await transformStatic(await fixture()),b=await transformStatic(await fixture({reverse:true}));
  assert.notEqual(a.after.primitives[0].orientedAttributeTriangles,b.after.primitives[0].orientedAttributeTriangles);
});
test('skins, animation, morph targets and transparent ordering are never silently stripped',async()=>{
  for(const options of [{skinned:true},{animated:true}])await assert.rejects(transformStatic(await fixture(options)),/skins\/animations/);
  await assert.rejects(transformStatic(await fixture({transparent:true})),/BLEND/);
  assert.throws(()=>inspectContainer(mutateJSON(awaitedPlain,j=>j.meshes[0].primitives[0].targets=[{}])),/morph targets/);
});
const awaitedPlain=await fixture();
test('external buffer/image requests are rejected before any global fetch',async()=>{
  const original=globalThis.fetch;let calls=0;globalThis.fetch=()=>{calls++;throw Error('Network must not be used');};
  try {
    for(const edit of [j=>j.buffers[0].uri='https://invalid.example/mesh.bin',j=>j.images=[{uri:'https://invalid.example/image.webp'}]])await assert.rejects(transformStatic(mutateJSON(awaitedPlain,edit)),/embedded/);
    assert.equal(calls,0);
  }finally{globalThis.fetch=original;}
});
test('unknown nested or required extensions fail closed',()=>{
  for(const edit of [j=>j.extensionsRequired=['EXT_meshopt_compression'],j=>j.nodes[0].extensions={UNKNOWN_private:{}},j=>j.extensionsUsed='EXT_texture_webp'])assert.throws(()=>inspectContainer(mutateJSON(awaitedPlain,edit)),/extension/i);
});
test('undeclared, misplaced and malformed supported extensions fail closed',()=>{
  for(const edit of [
    j=>j.extensionsRequired=['KHR_materials_emissive_strength'],
    j=>j.materials[0].extensions={KHR_materials_emissive_strength:{emissiveStrength:2}},
    j=>{j.extensionsUsed=['KHR_materials_emissive_strength'];j.nodes[0].extensions={KHR_materials_emissive_strength:{emissiveStrength:2}};},
    j=>{j.extensionsUsed=['KHR_materials_emissive_strength'];j.materials[0].extensions={KHR_materials_emissive_strength:{emissiveStrength:-1}};},
    j=>j.extensionsUsed=['EXT_texture_webp','EXT_texture_webp'],
    j=>j.materials[0].extensions=[],
  ])assert.throws(()=>inspectContainer(mutateJSON(awaitedPlain,edit)),/extension/i);
});
test('truncated, unaligned and extra GLB chunks are refused',()=>{
  const short=awaitedPlain.subarray(0,awaitedPlain.length-4);assert.throws(()=>inspectContainer(short),/complete/);
  const unaligned=Buffer.from(awaitedPlain);unaligned.writeUInt32LE(unaligned.readUInt32LE(12)-1,12);assert.throws(()=>inspectContainer(unaligned),/alignment/);
  const extra=Buffer.concat([awaitedPlain,Buffer.alloc(8)]);extra.writeUInt32LE(extra.length,8);assert.throws(()=>inspectContainer(extra),/one bounded JSON/);
});
test('accessor overflow, huge counts, mismatched streams and invalid index layout are refused',()=>{
  for(const edit of [j=>j.accessors[0].count=2_000_001,j=>j.accessors[0].byteOffset=1e9,j=>j.accessors[1].count=5,j=>j.accessors[0].sparse={}])assert.throws(()=>inspectContainer(mutateJSON(awaitedPlain,edit)),/Accessor|count|stream|Sparse/i);
  const indexed=mutateJSON(awaitedPlain,j=>{j.meshes[0].primitives[0].indices=0;});assert.throws(()=>inspectContainer(indexed),/index accessor/);
});
test('nonfinite vertex values cannot be accepted by the surface oracle',async()=>{
  const bad=Buffer.from(awaitedPlain),j=inspectContainer(bad),n=bad.readUInt32LE(12),a=j.accessors[j.meshes[0].primitives[0].attributes.POSITION],v=j.bufferViews[a.bufferView];
  bad.writeFloatLE(Number.NaN,28+n+(v.byteOffset||0)+(a.byteOffset||0));
  await assert.rejects(transformStatic(bad),/Nonfinite/);
});
test('WebP declaration/fallback/payload inconsistencies are refused',async()=>{
  const input=await fixture({webp:true});
  for(const edit of [j=>j.extensionsRequired=[],j=>j.textures[0].source=0,j=>j.images[0].mimeType='image/avif',j=>j.bufferViews[j.images[0].bufferView].byteLength-=4])assert.throws(()=>inspectContainer(mutateJSON(input,edit)),/WebP|image payload/);
  await assert.rejects(transformStatic(await fixture({webp:true,padding:[77,77]})),/WebP/);
});
test('unproven provenance/accessor/image metadata is refused rather than discarded',async()=>{
  for(const edit of [j=>j.asset.copyright='rights holder',j=>j.accessors[0].extras={proof:'source'},j=>j.images=[{bufferView:0,mimeType:'image/png',extras:{rights:'protected'}}]])assert.throws(()=>inspectContainer(mutateJSON(awaitedPlain,edit)),/metadata/);
});
test('only fresh outside-checkout output is accepted and exact source bytes survive',async()=>{
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'yuga-webp-static-')),input=path.join(dir,'input.glb'),out=path.join(dir,'output');
  try{
    const bytes=await fixture({webp:true});await fs.writeFile(input,bytes);await run(input,out);assert.deepEqual(await fs.readFile(input),bytes);
    const report=JSON.parse(await fs.readFile(path.join(out,'report.json')));assert.equal(report.preserved.inputUnchanged,true);
    await assert.rejects(run(input,out),/already exists/);await assert.rejects(run(input,input),/may not contain/);
    await assert.rejects(run(input,path.join(path.dirname(fileURLToPath(import.meta.url)),'forbidden')),/outside the repository/);
    const link=path.join(dir,'link');await fs.symlink(dir,link,'dir');await assert.rejects(run(input,path.join(link,'other')),/canonical/);
  }finally{await fs.rm(dir,{recursive:true,force:true});}
});
test('a different dependency lock is refused before loading modules',async()=>{
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'yuga-webp-lock-'));
  try{await fs.writeFile(path.join(dir,'package-lock.json'),'{}');await assert.rejects(libraries(dir),/lock must match/);}finally{await fs.rm(dir,{recursive:true,force:true});}
});
