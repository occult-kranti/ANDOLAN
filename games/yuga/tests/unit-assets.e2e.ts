import { test, expect, type Page } from '@playwright/test';
import { ArenaSimulation } from '../shared/simulation';
import { HEROES } from '../shared/heroes';
import { YUGA_PROTOCOL, type Actor, type ArenaSnapshot, type GameEvent, type Neutral, type UnitArchetype } from '../shared/types';
import { boot, waitReady, rendered, imageEvidence } from './browser-harness';

type UnitInstance={id:string;unitId:string;loaded:boolean;fallback:boolean;skeletons:number[];bones:number;clips:string[];state:string;action:string;animationTime:number;animated:boolean;pose:number[];transitions:Record<string,number>};
type UnitDiagnostics={assets:{unitId:string;state:string;skinnedPrimitives:number;animations:string[]}[];instances:UnitInstance[];fallback:{id:string;unitId:string}[]};
const units=(page:Page)=>page.evaluate(()=>(window.__YUGA as unknown as {assets():{units:UnitDiagnostics}}).assets().units);
const unit=(page:Page,id:string)=>units(page).then(value=>value.instances.find(instance=>instance.id===id));

// These fixtures control snapshots only. Model imports, skins, animation playback,
// UI, native menu actions and rendering all use the production client modules.
test('labelled seven-unit snapshots render real skins through idle, run, fire and defeat',async({page},info)=>{
 test.setTimeout(300_000);let snapshot:ArenaSnapshot|undefined,send:(()=>void)|undefined,timer:ReturnType<typeof setInterval>|undefined,moving:{x:number}|undefined,eventId=0;
 const events:GameEvent[]=[],evidence:unknown[]=[];
 await page.routeWebSocket('**/ws',socket=>socket.onMessage(raw=>{
  const message=JSON.parse(String(raw));if(message.type!=='join')return;
  const sim=new ArenaSimulation({room:'UNITS-FIXTURE',botsPerTeam:0});sim.addPlayer('unit-local','Unit fixture','rama','sun');snapshot=sim.snapshot();snapshot.actors[0]!.x=0;
  send=()=>{snapshot!.tick++;socket.send(JSON.stringify({type:'snapshot',snapshot:{...snapshot!,events}}));};
  socket.send(JSON.stringify({type:'welcome',protocol:YUGA_PROTOCOL,id:'unit-local',room:sim.room,token:'e'.repeat(48),snapshot}));timer=setInterval(()=>{if(snapshot){snapshot.time+=.1;if(moving)moving.x=Math.sin(snapshot.time*4)*.9;send?.();}},100);
 }));
 try{
  const diagnostics=await boot(page);await page.locator('#online-open').click();await page.locator('#join-room').click();await waitReady(page);await rendered(page);
  const inventory=await units(page);expect(inventory.assets).toHaveLength(7);expect(inventory.assets.every(asset=>asset.state==='ready'&&asset.skinnedPrimitives>0&&['idle','run','fire','defeat'].every(clip=>asset.animations.includes(clip)))).toBe(true);expect(inventory.fallback).toEqual([]);
  for(const unitId of ['soldier','city-watch','minister','king','yaksha','naga','sky-sentinel']){
   const local=snapshot!.actors.find(actor=>actor.id==='unit-local')!;snapshot!.actors=[local];for(const neutral of snapshot!.neutrals){neutral.health=0;neutral.state='dead';}
   let subject:Actor|Neutral;
   if(['soldier','city-watch','minister','king'].includes(unitId)){
    subject={...structuredClone(local),id:`fixture-${unitId}`,name:`Fixture ${unitId}`,kind:'minion',team:'moon',bot:true,connected:false,x:0,z:-59,yaw:Math.PI,health:100,maxHealth:100,minionRole:unitId==='king'?'siege':'escort',unitArchetype:unitId as UnitArchetype};snapshot!.actors.push(subject);
   }else{
    subject=snapshot!.neutrals.find(neutral=>neutral.species===unitId)!;subject.x=0;subject.z=-59;subject.yaw=Math.PI;subject.health=subject.maxHealth;subject.state='idle';subject.respawnAt=0;
   }
   send!();const id=subject.id;
   await expect.poll(async()=>(await unit(page,id))?.state,{message:`${unitId} actual idle skin`}).toBe('idle');
   const idle=(await unit(page,id))!;expect(idle).toMatchObject({unitId,loaded:true,fallback:false,animated:true});expect(idle.bones).toBeGreaterThan(5);expect(idle.skeletons.length).toBeGreaterThan(0);await imageEvidence(page,info,`unit-${unitId}-idle`);
   moving=subject;await expect.poll(async()=>(await unit(page,id))?.state,{message:`${unitId} actual run state`}).toBe('run');await expect.poll(async()=>(await unit(page,id))!.pose.some((value,index)=>Math.abs(value-(idle.pose[index]||0))>.0001)).toBe(true);await imageEvidence(page,info,`unit-${unitId}-run`);moving=undefined;
   await expect.poll(async()=>(await unit(page,id))?.state).toBe('idle');
   const beforeFire=(await unit(page,id))!.transitions.fire||0;events.push({id:++eventId,type:'shot',actorId:id,team:subject.team,label:`Fixture ${unitId} shot`,color:'#fff',x:subject.x,z:subject.z,time:snapshot!.time});send!();
   await expect.poll(async()=>(await unit(page,id))!.transitions.fire||0,{message:`${unitId} real fire transition`}).toBeGreaterThan(beforeFire);await page.screenshot({path:info.outputPath(`unit-${unitId}-fire.png`)});
   if(subject.kind!=='neutral'){snapshot!.actors=snapshot!.actors.filter(actor=>actor.id!==id);events.push({id:++eventId,type:'defeat',actorId:local.id,targetId:id,team:'sun',label:'Fixture unit defeated',color:'#fff',x:subject.x,z:subject.z,time:snapshot!.time});}
   else{subject.health=0;subject.state='dead';subject.respawnAt=snapshot!.time+40;}
   send!();await expect.poll(async()=>(await unit(page,id))?.state,{message:`${unitId} real defeat state`}).toBe('defeat');await expect.poll(async()=>(await unit(page,id))?.animationTime||0,{message:`${unitId} defeat advances beyond first pose`,intervals:[30,50]}).toBeGreaterThan(.35);const defeat=await unit(page,id);await page.screenshot({path:info.outputPath(`unit-${unitId}-defeat.png`)});evidence.push({unitId,idle,defeat});
  }
  expect((await units(page)).fallback).toEqual([]);expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);
  await info.attach('labelled-seven-unit-animations',{body:JSON.stringify({scope:'Explicit snapshot positions/movement/shot/death fixtures. Seven real GLBs and animation instances, no fallback. This is presentation/skin/clip evidence; no earned unit kill, physical traversal or server-authority claim.',inventory,evidence,errors:diagnostics},null,2),contentType:'application/json'});
 }finally{moving=undefined;if(timer)clearInterval(timer);}
});

test('labelled action-age and resume snapshots preserve recent casts without replaying old history',async({page},info)=>{
 test.setTimeout(180_000);let snapshot:ArenaSnapshot|undefined,send:(()=>void)|undefined,timer:ReturnType<typeof setInterval>|undefined;const events:GameEvent[]=[];
 await page.routeWebSocket('**/ws',socket=>socket.onMessage(raw=>{
  const message=JSON.parse(String(raw));if(message.type!=='join')return;
  const sim=new ArenaSimulation({room:'AGE-FIXTURE',botsPerTeam:0});sim.addPlayer('age-local','Animation age fixture','rama','sun');snapshot=sim.snapshot();snapshot.time=10;
  send=()=>{snapshot!.tick++;socket.send(JSON.stringify({type:'snapshot',snapshot:{...snapshot!,events}}));};socket.send(JSON.stringify({type:'welcome',protocol:YUGA_PROTOCOL,id:'age-local',room:sim.room,token:'f'.repeat(48),snapshot}));timer=setInterval(()=>send?.(),100);
 }));
 const rig=()=>page.evaluate(()=>(window.__YUGA as unknown as {assets():{instances:{id:string;transitions:Record<string,number>;state:string;action:string}[]}}).assets().instances.find(instance=>instance.id==='age-local')!);
 try{
  const diagnostics=await boot(page);await page.locator('#online-open').click();await page.locator('#join-room').click();await waitReady(page);await rendered(page);
  const actor=snapshot!.actors[0]!,ability=(slot:number,id:number,age:number):GameEvent=>({id,type:'ability',actorId:actor.id,team:actor.team,label:HEROES.find(hero=>hero.id==='rama')!.abilities[slot]!.name,color:'#fff',time:snapshot!.time-age,x:actor.x,z:actor.z});
  const initial=await rig();events.push(ability(0,1,.9));send!();await expect.poll(async()=>(await rig()).transitions.cast1||0).toBeGreaterThan(initial.transitions.cast1||0);const recent=await rig();
  const beforeOld=recent.transitions.cast2||0;events.push(ability(1,2,2.1));send!();await rendered(page);expect((await rig()).transitions.cast2||0).toBe(beforeOld);
  await page.keyboard.press('Escape');await expect(page.locator('#pause-dialog')).toBeVisible();events.push(ability(2,3,0));send!();await page.locator('#resume-game').click();await rendered(page);expect((await rig()).transitions.cast3||0).toBe(initial.transitions.cast3||0);
  events.push(ability(2,4,0));send!();await expect.poll(async()=>(await rig()).transitions.cast3||0).toBeGreaterThan(initial.transitions.cast3||0);
  expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);await info.attach('labelled-action-age-fixture',{body:JSON.stringify({scope:'Mocked authority snapshots and controlled event ages .9s/2.1s; native menu open/resume. Validates renderer freshness and history-baseline rules only, not native combat success or network latency.',initial,recent,final:await rig(),errors:diagnostics},null,2),contentType:'application/json'});
 }finally{if(timer)clearInterval(timer);}
});
