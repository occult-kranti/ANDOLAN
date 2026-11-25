/** Derive a compact, normal-mapped projectile candidate from a CC0 rock. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {simplify, tangents, unweld, weld} from '@gltf-transform/functions';
import {MeshoptSimplifier} from 'meshoptimizer';

const here=path.dirname(fileURLToPath(import.meta.url));
const native=path.resolve(here,'../../..');
const source=path.join(native,'art/world-landmark-study/sources/rock_face_01/rock_face_01_1k.gltf');
const output=path.resolve(process.argv[2] || '/tmp/yuga-ghat-lod');
const settings=JSON.parse(await readFile(path.join(here,'lod-settings.json'),'utf8'));
const plan=JSON.parse(await readFile(path.join(here,'candidate-plan.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sourceBytes=await readFile(source);
assert.equal(sha(sourceBytes),settings.source_gltf_sha256,'CC0 source digest mismatch');
for(const [filename,expected] of Object.entries(plan.rock_files_sha256))
  assert.equal(sha(await readFile(path.join(path.dirname(source),filename))),expected,'Rock dependency changed: '+filename);
const input=JSON.parse(sourceBytes.toString('utf8'));
const sourcePos=input.accessors[input.meshes[0].primitives[0].attributes.POSITION];
const originalTriangles=input.accessors[input.meshes[0].primitives[0].indices].count/3;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc=await io.read(source);
const root=doc.getRoot();
const scene=root.getDefaultScene();
assert.equal(scene.listChildren().length,1);
await MeshoptSimplifier.ready;
const {generateTangents}=createRequire(import.meta.url)('mikktspace');
await doc.transform(weld(), simplify({simplifier:MeshoptSimplifier,ratio:settings.ratio,error:settings.error,lockBorder:settings.lock_border}), unweld(), tangents({generateTangents}), weld());
const primitive=root.listMeshes()[0].listPrimitives()[0];
const reducedTriangles=primitive.getIndices().getCount()/3;
const reducedVertices=primitive.getAttribute('POSITION').getCount();
assert.ok(reducedTriangles>0 && reducedTriangles<=settings.max_triangles, 'Triangle target not met: '+reducedTriangles);
const child=scene.listChildren()[0];
const size=sourcePos.max.map((v,i)=>v-sourcePos.min[i]);
child.setScale(size.map(v=>1/v)).setTranslation([
  -(sourcePos.min[0]+sourcePos.max[0])/(2*size[0]),
  -sourcePos.min[1]/size[1],
  -(sourcePos.min[2]+sourcePos.max[2])/(2*size[2]),
]);
const parent=doc.createNode('rock_face_01_compact');
parent.addChild(child);
scene.addChild(parent);
const glb=await io.writeBinary(doc);
await mkdir(output,{recursive:true});
await writeFile(path.join(output,'rock-projectile.glb'),glb);
const report={
 source:'https://polyhaven.com/a/rock_face_01',
 source_author:'Dario Barresi',
 source_license:'CC0 1.0',
 source_gltf_sha256:settings.source_gltf_sha256,
 output_sha256:sha(glb),output_bytes:glb.length,
 method:{library:'glTF-Transform 4.5.1 simplify + meshoptimizer 1.3.0',
   ratio:settings.ratio,error:settings.error,lock_border:settings.lock_border,
   tangent:'MikkTSpace 1.1.1; unweld, generate tangents, bitwise weld'},
 original_triangles:originalTriangles,reduced_triangles:reducedTriangles,
 original_vertices:sourcePos.count,reduced_vertices:reducedVertices,
 texture_names:root.listTextures().map(t=>t.getName()),
 prefab:'rock_face_01_compact', normalized_parent:'1×1×1 bounds using source AABB; base Y=0',
 scope:'Candidate for visual inspection; no game integration or GPU timing.'
};
await writeFile(path.join(output,'lod-build.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
