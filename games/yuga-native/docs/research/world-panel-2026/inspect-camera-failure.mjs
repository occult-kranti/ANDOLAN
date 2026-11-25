/** Reconstruct the released authority snapshot where the Sun camera enters a wall. */
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../../../../..');
const zip=path.join(root,'games/yuga-rust/downloads/yuga-rust-confluence.zip');
const map=JSON.parse(await readFile(path.join(root,'games/yuga-native/assets/world/confluence-map.json'),'utf8'));
const wasm=execFileSync('unzip',['-p',zip,'yuga-rust.wasm']);
const {instance}=await WebAssembly.instantiate(wasm,{});
const a=instance.exports;
assert.equal(a.duel_start(0,0),1);
for(let i=0;i<240;i++)a.duel_step(-1,0,0,1,-1,0,0,-1);
const pointer=a.duel_snapshot(0);
const state=JSON.parse(Buffer.from(a.memory.buffer,pointer,a.duel_snapshot_len()));
const [x,z]=state.actor.pos, camera=[x+1.35,4.4,z-8.4];
const box=map.authority_collision_boxes.find(s=>s.id==='authority-solid-4');
assert.ok(box);
const min=[box.position[0]-box.size[0]/2,box.position[1],box.position[2]-box.size[2]/2];
const max=[box.position[0]+box.size[0]/2,box.position[1]+box.size[1],box.position[2]+box.size[2]/2];
assert.ok(camera.every((v,i)=>v>min[i]&&v<max[i]),'camera outside authority volume');
assert.ok(z-map.bounds.hero_radius>max[2],'hero clearance does not hold');
const png=await readFile(path.join(here,'evidence/baseline-camera-inside-wall.png'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const result={
  actor:state.actor.pos, team:state.actor.team, tick:state.tick,
  step:'240 authority duel steps with both teams moving -X at full input',
  camera:camera.map(v=>+v.toFixed(6)), collider:box.id, collider_min:min,collider_max:max,
  actor_body_gap_to_collider_m:+(z-map.bounds.hero_radius-max[2]).toFixed(6),
  image:'baseline-camera-inside-wall.png', image_sha256:sha(png),wasm_sha256:sha(wasm),
  note:'The released renderer uses the listed fixed camera offset. A matching real browser screenshot shows the interior wall hiding the hero and aiming field. The screenshot used a staged room transport with an actual released-WASM state.'
};
await writeFile(path.join(here,'evidence/camera-occlusion.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
