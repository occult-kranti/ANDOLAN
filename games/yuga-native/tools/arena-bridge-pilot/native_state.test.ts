import assert from 'node:assert/strict';
import test from 'node:test';
import { validNativeState } from './vertical_simulation.js';

const ids = new Map([['aaaaaaaaaaaaaaaa', 0], ['bbbbbbbbbbbbbbbb', 1]]);
const fixture = 'a'.repeat(64), contract = 'b'.repeat(64);
export function state() {
  return {schema:1,nativeTick:60,nativeTime:1,stage:'stacked',stageTime:1,epoch:0,done:false,fixtureHash:fixture,contractHash:contract,revision:1,rejectedPackets:0,
    actors:[...ids].map(([id,slot])=>({id,x:12,y:3.2+slot*3,z:1,yaw:0,pitch:0,bridgeAckSeq:1,bridgeInputTick:58,bridgeSlot:slot,bridgeEpoch:0,nativeTick:60,grounded:true,support:slot?'deck-upper':'deck-lower',shot:{},velocity:[0,0,0]}))};
}
test('actual two-slot native wire shape has a positive control',()=>assert.ok(validNativeState(state(),undefined,ids,fixture,contract)));
const edits:Record<string,(value:ReturnType<typeof state>)=>void>={
  wrong_map:v=>{v.fixtureHash='c'.repeat(64);},wrong_contract:v=>{v.contractHash='c'.repeat(64);},
  duplicate_identity:v=>{v.actors[1].id=v.actors[0].id;},unknown_identity:v=>{v.actors[1].id='cccccccccccccccc';},
  duplicate_slot:v=>{v.actors[1].bridgeSlot=0;},wrong_native_tick:v=>{v.actors[0].nativeTick=59;},
  wrong_actor_epoch:v=>{v.actors[0].bridgeEpoch=1;},missing_velocity:v=>{v.actors[0].velocity=[];},
  nonfinite_velocity:v=>{v.actors[0].velocity[1]=Infinity;},extreme_velocity:v=>{v.actors[0].velocity[1]=1e308;},
  nonbool_grounded:v=>{(v.actors[0] as any).grounded='true';},nonfinite_elevation:v=>{v.actors[0].y=NaN;},
  bad_pitch:v=>{v.actors[0].pitch=4;},future_input_tick:v=>{v.actors[0].bridgeInputTick=100;},
  fake_time:v=>{v.nativeTime=2;},fake_stage:v=>{v.stage='underpass';},bad_done:v=>{(v as any).done=1;},
  early_done:v=>{v.done=true;},incoherent_stage_offset:v=>{v.stageTime=1.9;},
  future_epoch:v=>{v.epoch=1;v.stage='ramp-stairs';for(const a of v.actors)a.bridgeEpoch=1;},
};
for(const[name,edit]of Object.entries(edits))test('backend refuses '+name,()=>{const value=state();edit(value);assert.equal(validNativeState(value,undefined,ids,fixture,contract),false);});
test('same epoch cannot hide a teleport or acknowledgement rollback',()=>{
  const previous=state(),next=state();next.nativeTick=63;next.nativeTime=1.05;next.stageTime=1.05;for(const a of next.actors)a.nativeTick=63;
  assert.ok(validNativeState(next,previous,ids,fixture,contract));
  next.actors[0].x=900;assert.equal(validNativeState(next,previous,ids,fixture,contract),false);
  next.actors[0].x=12;next.actors[0].bridgeAckSeq=0;assert.equal(validNativeState(next,previous,ids,fixture,contract),false);
});
test('native clock accepts floating stage boundaries and final done clamping',()=>{
  const boundary=state();boundary.nativeTick=120;boundary.nativeTime=1.999999999999998;boundary.stageTime=boundary.nativeTime;for(const a of boundary.actors)a.nativeTick=120;
  assert.ok(validNativeState(boundary,undefined,ids,fixture,contract));
  const done=state();Object.assign(done,{nativeTick:603,nativeTime:10.05,epoch:5,stage:'expiry',stageTime:1,done:true});for(const a of done.actors){a.nativeTick=603;a.bridgeEpoch=5;}
  assert.ok(validNativeState(done,undefined,ids,fixture,contract));
  done.done=false;assert.equal(validNativeState(done,undefined,ids,fixture,contract),false);
});
