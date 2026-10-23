import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {initialize, inspectContainer, transformStatic} from '../../../../tools/reuse-art-next/webp-static-preflight.mjs';

const runtime=await initialize(process.env.YUGA_REUSE_DEPENDENCIES);
const sha=b=>createHash('sha256').update(b).digest('hex');
const rows=[];
const pack=(json,binary)=>{
  const text=Buffer.from(JSON.stringify(json));
  const padded=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]);
  const bin=Buffer.concat([binary,Buffer.alloc((4-binary.length%4)%4)]);
  const out=Buffer.alloc(28+padded.length+bin.length);
  out.writeUInt32LE(0x46546c67,0);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);
  out.writeUInt32LE(padded.length,12);out.writeUInt32LE(0x4e4f534a,16);padded.copy(out,20);
  out.writeUInt32LE(bin.length,20+padded.length);out.writeUInt32LE(0x004e4942,24+padded.length);bin.copy(out,28+padded.length);
  return out;
};
const positions=Buffer.from(new Float32Array([-0,0,0,1,0,0,0,1,0]).buffer);
const normals=Buffer.from(new Float32Array([0,-0,1,0,0,1,0,0,1]).buffer);
const colours=Buffer.from([255,0,0,255,0,255,0,255,0,0,255,255]);
const indices=Buffer.from(new Uint16Array([0,1,2]).buffer);
const binary=Buffer.concat([positions,normals,colours,indices,Buffer.alloc(2)]);
const json={asset:{version:'2.0',generator:'YUGA independent review fixture'},buffers:[{byteLength:binary.length}],bufferViews:[{buffer:0,byteOffset:0,byteLength:36},{buffer:0,byteOffset:36,byteLength:36},{buffer:0,byteOffset:72,byteLength:12},{buffer:0,byteOffset:84,byteLength:6}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[0,0,0],max:[1,1,0]},{bufferView:1,componentType:5126,count:3,type:'VEC3'},{bufferView:2,componentType:5121,count:3,type:'VEC4',normalized:true},{bufferView:3,componentType:5123,count:3,type:'SCALAR'}],meshes:[{name:'triangle',extras:{author:'independent fixture'},primitives:[{attributes:{POSITION:0,NORMAL:1,COLOR_0:2},indices:3,material:0,extras:{protected:'primitive'}}]}],materials:[{name:'fixture material',extras:{protected:'material'}}],nodes:[{name:'fixture node',mesh:0,translation:[1,2,3],extras:{protected:'node'}}],scenes:[{nodes:[0],extras:{protected:'scene'}}],scene:0};
const input=pack(json,binary);
const mutate=(edit,bin=binary)=>{const j=structuredClone(json);edit(j);return pack(j,bin);};
const check=async(name,fn)=>{try{await fn();rows.push({name,passed:true});}catch(error){rows.push({name,passed:false,error:String(error)});}};

await check('normalized integer colors and signed-zero float attributes retain oriented identity',async()=>{
  const result=await transformStatic(input);
  assert.deepEqual(result.before.primitives,result.after.primitives);
  assert.equal(result.before.triangles,1);assert.equal(result.after.triangles,1);
});
await check('reversing winding changes full attribute identity',async()=>{
  const reversed=Buffer.from(binary);reversed.writeUInt16LE(2,84);reversed.writeUInt16LE(0,88);
  const a=await transformStatic(input),b=await transformStatic(pack(json,reversed));
  assert.notEqual(a.after.primitives[0].orientedAttributeTriangles,b.after.primitives[0].orientedAttributeTriangles);
});
await check('out-of-range actual triangle indices rejected',async()=>{
  const bad=Buffer.from(binary);bad.writeUInt16LE(65535,84);
  await assert.rejects(transformStatic(pack(json,bad)),/Out-of-range index/);
});
await check('NaN in an actual normal stream rejected',async()=>{
  const bad=Buffer.from(binary);bad.writeFloatLE(NaN,36);
  await assert.rejects(transformStatic(pack(json,bad)),/Nonfinite/);
});
await check('relative, local file, data and HTTPS external references rejected before fetch',async()=>{
  const original=globalThis.fetch;let fetched=0;
  globalThis.fetch=()=>{fetched++;throw Error('unexpected fetch');};
  try{
    for(const uri of ['../outside.bin','file:///etc/passwd','data:application/octet-stream;base64,AAAA','https://invalid.example/data.bin']){
      await assert.rejects(transformStatic(mutate(j=>j.buffers[0].uri=uri)),/embedded/);
      await assert.rejects(transformStatic(mutate(j=>j.images=[{uri}])),/embedded/);
    }
    assert.equal(fetched,0);
  }finally{globalThis.fetch=original;}
});
await check('undeclared supported material extension refused',async()=>{
  assert.throws(()=>inspectContainer(mutate(j=>j.materials[0].extensions={KHR_materials_emissive_strength:{emissiveStrength:2.5}})),/Undeclared/);
});
await check('required extension absent from used list refused',async()=>{
  assert.throws(()=>inspectContainer(mutate(j=>j.extensionsRequired=['KHR_materials_emissive_strength'])),/missing from extensionsUsed/);
});
await check('supported extension misplaced on a node refused',async()=>{
  assert.throws(()=>inspectContainer(mutate(j=>{j.extensionsUsed=['KHR_materials_emissive_strength'];j.nodes[0].extensions={KHR_materials_emissive_strength:{emissiveStrength:2.5}};})),/placement/);
});
await check('copyright and accessor provenance never silently discarded',async()=>{
  for(const edit of [j=>j.asset.copyright='test rights holder',j=>j.accessors[0].extras={source:'protected provenance'}]){
    await assert.rejects(transformStatic(mutate(edit)),/metadata/);
  }
});
await check('fractional, negative and string accessor references refused',async()=>{
  for(const index of [-1,.5,'0']){
    await assert.rejects(transformStatic(mutate(j=>j.meshes[0].primitives[0].attributes.POSITION=index)),/accessor|POSITION/i);
  }
});
await check('source buffer range overflow refused before decoder',async()=>{
  assert.throws(()=>inspectContainer(mutate(j=>j.bufferViews[0].byteLength=1e9)),/exceeds/);
});
await check('a correctly declared emissive extension survives import and output',async()=>{
  const bytes=mutate(j=>{j.extensionsUsed=['KHR_materials_emissive_strength'];j.materials[0].extensions={KHR_materials_emissive_strength:{emissiveStrength:2.5}};});
  const result=await transformStatic(bytes),j=inspectContainer(result.candidate);
  assert.equal(j.materials[0].extensions.KHR_materials_emissive_strength.emissiveStrength,2.5);
});
const moduleUrl=new URL('../../../../tools/reuse-art-next/webp-static-preflight.mjs',import.meta.url);
const report={scope:'Independent small offline adapter counterexamples. No rendered, asset-rights, hardware or game-completion acceptance.',passed:rows.every(r=>r.passed),cases:rows.length,checks:rows,module_sha256:sha(await fs.readFile(moduleUrl)),fixture_sha256:sha(input),dependency_lock_sha256:runtime.sourceLockSha256};
const output=process.argv[2];
if(output)await fs.writeFile(output,JSON.stringify(report,null,2)+'\n');
process.stdout.write(JSON.stringify(report,null,2)+'\n');
process.exitCode=report.passed?0:1;
