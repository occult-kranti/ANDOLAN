/** Check the candidate changes only the visual rock prefab, preserving map and game state. */
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';

const here=path.dirname(fileURLToPath(import.meta.url));
const native=path.resolve(here,'../../..'),root=path.resolve(native,'../..');
const directory=path.resolve(process.argv[2] || '/tmp/yuga-ghat-replacement');
const zip=path.resolve(process.env.YUGA_BASE_GAME_ZIP || path.join(root,'games/yuga-rust/downloads/yuga-rust-confluence.zip'));
const originalGlb=path.join(native,'assets/world/nature.glb');
const compact=path.join(here,'art/rock-projectile.glb');
const candidate=path.join(directory,'nature-candidate.glb');
const digest=b=>createHash('sha256').update(b).digest('hex');
const [oldBytes,newBytes,rockBytes]=await Promise.all([readFile(originalGlb),readFile(candidate),readFile(compact)]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const [oldDoc,newDoc,rockDoc]=await Promise.all([io.readBinary(oldBytes),io.readBinary(newBytes),io.readBinary(rockBytes)]);
const oldNodes=oldDoc.getRoot().getDefaultScene().listChildren();
const newNodes=newDoc.getRoot().getDefaultScene().listChildren();
assert.deepEqual(oldNodes.map(n=>n.getName()).sort(),newNodes.map(n=>n.getName()).sort());
const bytes=accessor=>accessor ? Buffer.from(accessor.getArray().buffer,accessor.getArray().byteOffset,accessor.getArray().byteLength) : null;
let streams=0, primitives=0;
for (const old of oldNodes.filter(n=>n.getName()!=='rock_island')) {
  const replacement=newNodes.find(n=>n.getName()===old.getName());
  const a=old.getMesh().listPrimitives(),b=replacement.getMesh().listPrimitives();
  assert.equal(a.length,b.length);
  for (let i=0;i<a.length;i++) {
    assert.equal(a[i].getMode(),b[i].getMode());
    assert.equal(a[i].getMaterial()?.getName(),b[i].getMaterial()?.getName());
    assert.deepEqual(bytes(a[i].getIndices()),bytes(b[i].getIndices()));
    assert.deepEqual(a[i].listSemantics().sort(),b[i].listSemantics().sort());
    for (const semantic of a[i].listSemantics()) {
      assert.deepEqual(bytes(a[i].getAttribute(semantic)),bytes(b[i].getAttribute(semantic)));
      streams++;
    }
    primitives++;
  }
}
const rock=newNodes.find(n=>n.getName()==='rock_island');
assert.equal(rock.listChildren().length,1);
const primitive=rock.listChildren()[0].getMesh().listPrimitives()[0];
assert.equal(primitive.getIndices().getCount()/3,2823);
const shaTextures=[];
for (const texture of rockDoc.getRoot().listTextures()) {
  const match=newDoc.getRoot().listTextures().filter(t=>t.getName()===texture.getName());
  assert.equal(match.length,1);
  assert.equal(digest(match[0].getImage()),digest(texture.getImage()));
  shaTextures.push({name:texture.getName(),sha256:digest(texture.getImage())});
}
const originalHtml=execFileSync('unzip',['-p',zip,'yuga-rust.html'],{maxBuffer:150*1024*1024}).toString('utf8');
const editedHtml=(await readFile(path.join(directory,'yuga-rust.html'))).toString('utf8');
const tag='<script id="payload" type="application/json">';
function split(html){const start=html.indexOf(tag)+tag.length,end=html.indexOf('</script>',start);return [html.slice(0,start),JSON.parse(html.slice(start,end)),html.slice(end)];}
const [headA,payloadA,tailA]=split(originalHtml),[headB,payloadB,tailB]=split(editedHtml);
assert.equal(headA,headB);assert.equal(tailA,tailB);
assert.deepEqual(payloadA.map,payloadB.map);
const mapHash=digest(Buffer.from(JSON.stringify(payloadB.map)));
assert.equal(digest(Buffer.from(payloadB.blobs.nature,'base64')),digest(newBytes));
delete payloadA.blobs.nature;delete payloadB.blobs.nature;
delete payloadA.notices;delete payloadB.notices;
assert.deepEqual(payloadA,payloadB);
const {validateBytes}=createRequire(import.meta.url)('gltf-validator');
const validation=await validateBytes(new Uint8Array(newBytes),{uri:'nature-candidate.glb',maxIssues:0,writeTimestamp:false});
assert.equal(validation.issues.numErrors,0);
assert.equal(validation.issues.numWarnings,0);
const report={passed:true,baseline_nature_sha256:digest(oldBytes),candidate_nature_sha256:digest(newBytes),
  baseline_html_sha256:digest(Buffer.from(originalHtml)),candidate_html_sha256:digest(Buffer.from(editedHtml)),
  other_prefabs_verified:oldNodes.length-1,other_primitives_verified:primitives,other_attribute_streams_verified:streams,
  map_json_equal:true,game_script_equal:true,other_payload_equal:true,wasm_sha256:digest(Buffer.from(payloadB.blobs.wasm,'base64')),
  map_logical_sha256:mapHash,replacement_root:'rock_island',replacement_triangles:2823,texture_hashes:shaTextures,
  validation:{version:validation.validatorVersion,errors:0,warnings:0},
  scope:'Only the nature GLB rock prefab and attribution changed in the offline candidate. The map, game code, other embedded assets and WASM remain identical.'};
await writeFile(path.join(directory,'replacement-review.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
