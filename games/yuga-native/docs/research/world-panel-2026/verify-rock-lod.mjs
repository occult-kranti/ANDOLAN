/** Check the compact rock geometry and source texture bytes. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';

const here=path.dirname(fileURLToPath(import.meta.url));
const native=path.resolve(here,'../../..');
const source=path.join(native,'art/world-landmark-study/sources/rock_face_01/rock_face_01_1k.gltf');
const glb=path.resolve(process.argv[2] || path.join(here,'art/rock-projectile.glb'));
const reportPath=path.resolve(process.argv[3] || '/tmp/yuga-rock-lod-validation.json');
const {validateBytes}=createRequire(import.meta.url)('gltf-validator');
const bytes=await readFile(glb);
const result=await validateBytes(new Uint8Array(bytes),{uri:'rock-projectile.glb',maxIssues:0,writeTimestamp:false});
assert.equal(result.issues.numErrors,0,'Khronos errors');
assert.equal(result.issues.numWarnings,0,'Khronos warnings');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const [original,candidate]=await Promise.all([io.read(source),io.readBinary(bytes)]);
const root=candidate.getRoot();
const prefab=root.listScenes()[0].listChildren().find(node=>node.getName()==='rock_face_01_compact');
assert.ok(prefab && prefab.listChildren().length===1,'normalized prefab missing');
const primitive=root.listMeshes()[0].listPrimitives()[0];
const triangles=primitive.getIndices().getCount()/3;
assert.equal(triangles,2823);
assert.ok(primitive.getAttribute('TANGENT'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const textures=[];
for(const texture of original.getRoot().listTextures()) {
  const match=root.listTextures().filter(t=>t.getName()===texture.getName());
  assert.equal(match.length,1);
  assert.equal(sha(match[0].getImage()),sha(texture.getImage()),texture.getName());
  textures.push({name:texture.getName(),sha256:sha(texture.getImage()),bytes:texture.getImage().length});
}
const report={file:path.basename(glb),sha256:sha(bytes),bytes:bytes.length,
  validator:result.validatorVersion,errors:result.issues.numErrors,warnings:result.issues.numWarnings,
  triangles,vertices:primitive.getAttribute('POSITION').getCount(),tangents:true,textures,
  normalized_root:prefab.getName(),scope:'Standalone GLB and source bytes; no game integration or GPU profiling'};
await writeFile(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
