/** Verify original YUGA mesh streams and every sampled donor triangle attribute. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';

const here=path.dirname(fileURLToPath(import.meta.url));
const native=path.resolve(here,'../../..');
const dir=path.resolve(process.argv[2] || '/tmp/yuga-ghat-candidate');
const base=path.join(native,'assets/world/nature.glb');
const source=path.join(native,'art/world-landmark-study/sources/rock_face_01/rock_face_01_1k.gltf');
const candidate=path.join(dir,'nature-candidate.glb');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const [original,donor,merged]=await Promise.all([io.read(base),io.read(source),io.read(candidate)]);
const sha=data=>createHash('sha256').update(data).digest('hex');
const primitives=mesh=>mesh.listPrimitives();
const array=accessor=>accessor?.getArray();
const bytes=accessor=>accessor ? Buffer.from(array(accessor).buffer,array(accessor).byteOffset,array(accessor).byteLength) : null;
function byName(document,name) {
  const result=document.getRoot().listMeshes().filter(mesh=>mesh.getName()===name);
  assert.equal(result.length,1, 'mesh identity '+name);
  return result[0];
}
const baseMeshes=original.getRoot().listMeshes();
let streams=0;
for(const mesh of baseMeshes) {
  const a=primitives(mesh), b=primitives(byName(merged,mesh.getName()));
  assert.equal(a.length,b.length,mesh.getName()+' primitive count');
  for(let i=0;i<a.length;i++) {
    assert.equal(a[i].getMode(),b[i].getMode());
    assert.equal(a[i].getMaterial()?.getName(),b[i].getMaterial()?.getName());
    assert.deepEqual(bytes(a[i].getIndices()),bytes(b[i].getIndices()));
    assert.deepEqual(a[i].listSemantics().sort(),b[i].listSemantics().sort());
    for(const semantic of a[i].listSemantics()) {
      assert.deepEqual(bytes(a[i].getAttribute(semantic)),bytes(b[i].getAttribute(semantic)),mesh.getName()+' '+semantic);
      streams++;
    }
  }
}
const sourceMesh=donor.getRoot().listMeshes()[0];
const outMesh=byName(merged,sourceMesh.getName());
const s=primitives(sourceMesh)[0], t=primitives(outMesh)[0];
const si=array(s.getIndices()),ti=array(t.getIndices());
assert.equal(si.length,ti.length);
const components={POSITION:3,NORMAL:3,TEXCOORD_0:2};
for(const [attribute,width] of Object.entries(components)) {
  const sourceData=array(s.getAttribute(attribute)),resultData=array(t.getAttribute(attribute));
  for(let i=0;i<si.length;i++) for(let j=0;j<width;j++)
    assert.equal(sourceData[si[i]*width+j],resultData[ti[i]*width+j],attribute+' triangle '+Math.floor(i/3));
}
assert.ok(t.getAttribute('TANGENT'),'normal-mapped rock tangent missing');
const textureResults=[];
for(const texture of donor.getRoot().listTextures()) {
  const matches=merged.getRoot().listTextures().filter(t=>t.getName()===texture.getName());
  assert.equal(matches.length,1,'texture '+texture.getName());
  assert.equal(sha(texture.getImage()),sha(matches[0].getImage()),'texture bytes');
  textureResults.push({name:texture.getName(),sha256:sha(texture.getImage()),bytes:texture.getImage().length});
}
const result={
  baseline_sha256:sha(await readFile(base)),candidate_sha256:sha(await readFile(candidate)),
  original_meshes:baseMeshes.length,original_primitive_attribute_streams_verified:streams,
  donor_triangles:si.length/3,donor_triangle_position_normal_uv_components_verified:si.length*8,
  generated_tangents:true,donor_textures:textureResults,
  method:'Original indexed YUGA buffers matched byte-for-byte after glTF-Transform merge. Every source rock triangle position, normal and UV component matched the generated tangent-bearing rock. Texture bytes were compared after embedding.',
};
await writeFile(path.join(dir,'geometry-review.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
