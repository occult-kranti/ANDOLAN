/** Build an offline CC0 boulder candidate; never installs a runtime asset. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {simplify,tangents,unweld,weld} from '@gltf-transform/functions';
import {MeshoptSimplifier} from 'meshoptimizer';

const input=path.resolve(process.argv[2] || '/tmp/yuga-open-cliff-study/rock_07');
const output=path.resolve(process.argv[3] || '/tmp/yuga-rock07-study');
const expected={
  'rock_07_1k.gltf':'efcc2dcaa133ff8ad5c865dc2135772e8f5dbc83fa38db2ee2cf25382436b6e6',
  'rock_07.bin':'e4a532a6d6cf4a08c288f501b790f32cba0528136a29959ce774c3cd39369e7e',
  'textures/rock_07_arm_1k.jpg':'1ed76e9a8542c76bdc6b7b018720ae1f52cd75d9f5ae719f613de3f5032cf4da',
  'textures/rock_07_diff_1k.jpg':'8ff1965aa1664cc4abcc0131c44ee2b97ab14d6e131d7a51429ff261eeb101c8',
  'textures/rock_07_nor_gl_1k.jpg':'57cb2210951aeb376164fce5f7c65f03e5599def04873b56cad0f173c275d78d',
};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
for (const [file,hash] of Object.entries(expected)) {
  assert.equal(sha(await readFile(path.join(input,file))),hash,'Unexpected input: '+file);
}
const source=JSON.parse(await readFile(path.join(input,'rock_07_1k.gltf'),'utf8'));
const mesh=source.meshes[0].primitives[0];
const positions=source.accessors[mesh.attributes.POSITION];
const dimensions=positions.max.map((v,i)=>v-positions.min[i]);
const longest=Math.max(...dimensions);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc=await io.read(path.join(input,'rock_07_1k.gltf'));
await MeshoptSimplifier.ready;
const {generateTangents}=createRequire(import.meta.url)('mikktspace');
await doc.transform(weld(),simplify({simplifier:MeshoptSimplifier,ratio:0.2,error:0.03,lockBorder:false}),unweld(),tangents({generateTangents}),weld());
const scene=doc.getRoot().getDefaultScene();
const child=scene.listChildren()[0];
assert.equal(scene.listChildren().length,1);
child.setScale([1/longest,1/longest,1/longest]).setTranslation([
  -(positions.min[0]+positions.max[0])/(2*longest),
  -positions.min[1]/longest,
  -(positions.min[2]+positions.max[2])/(2*longest),
]);
const parent=doc.createNode('rock_07_compact');
parent.addChild(child);
scene.addChild(parent);
const glb=await io.writeBinary(doc);
const {validateBytes}=createRequire(import.meta.url)('gltf-validator');
const validation=await validateBytes(new Uint8Array(glb),{uri:'rock07-compact.glb',maxIssues:0,writeTimestamp:false});
assert.equal(validation.issues.numErrors,0);
assert.equal(validation.issues.numWarnings,0);
const primitive=doc.getRoot().listMeshes()[0].listPrimitives()[0];
const report={
 source:'https://polyhaven.com/a/rock_07',author:'Jenelle van Heerden',license:'CC0 1.0',
 license_url:'https://polyhaven.com/license',input_sha256:expected,
 output_sha256:sha(glb),output_bytes:glb.length,
 original_triangles:source.accessors[mesh.indices].count/3,
 reduced_triangles:primitive.getIndices().getCount()/3,
 original_dimensions:dimensions,normalized_dimensions:dimensions.map(d=>d/longest),
 normalization:'Uniform scale to longest axis 1, horizontal centered, base Y=0; preserves original shape.',
 reduction:'glTF-Transform 4.5.1, meshoptimizer 1.3.0, ratio 0.2, error 0.03; MikkTSpace tangents',
 validation:{validator:validation.validatorVersion,errors:validation.issues.numErrors,warnings:validation.issues.numWarnings},
 scope:'Offline candidate only; no game integration, in-game visual test, collision or performance claim.'
};
await mkdir(output,{recursive:true});
await writeFile(path.join(output,'rock07-compact.glb'),glb);
await writeFile(path.join(output,'rock07-build.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
