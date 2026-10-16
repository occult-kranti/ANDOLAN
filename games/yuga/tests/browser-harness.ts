import { expect, type Page, type TestInfo } from '@playwright/test';
import type { Actor, ArenaSnapshot } from '../shared/types';

export const arenaState=(page:Page)=>page.evaluate(()=>window.__YUGA.snapshot()!);
export const localActor=(page:Page)=>page.evaluate(()=>window.__YUGA.snapshot()!.actors.find(actor=>actor.id===window.__YUGA.playerId())!);
export async function boot(page:Page){
 const errors:string[]=[],consoleErrors:string[]=[];
 page.on('pageerror',error=>errors.push(error.stack||error.message));
 page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text());});
 if(process.env.CI||process.env.YUGA_SOFTWARE_RENDERING==='1')await page.addInitScript(()=>{
  if(window.__yugaQAFrameCap)return;window.__yugaQAFrameCap=true;
  const native=requestAnimationFrame.bind(window),queue=new Map<number,FrameRequestCallback>();let next=0,queued=false,dispatching=false,last=performance.now()-100,timer:number|undefined;
  const schedule=()=>{if(!queue.size||queued||dispatching||timer!==undefined)return;timer=window.setTimeout(()=>{timer=undefined;queued=true;native(time=>{queued=false;dispatching=true;for(const id of[...queue.keys()]){const callback=queue.get(id);queue.delete(id);if(callback)try{callback(time);}catch(error){window.setTimeout(()=>{throw error;},0);}}dispatching=false;last=performance.now();schedule();});},Math.max(0,100-performance.now()+last));};
  window.requestAnimationFrame=callback=>{const id=++next;queue.set(id,callback);schedule();return id;};window.cancelAnimationFrame=id=>{queue.delete(id);};
 });
 await page.goto('/');await page.waitForFunction(()=>!!window.__YUGA);await expect(page.locator('#lobby')).toBeVisible();
 await page.locator('#lobby-settings').click();await page.locator('#quality').selectOption('low');await page.locator('#resume-game').click();
 return{errors,consoleErrors};
}
export async function waitReady(page:Page){await expect(page.locator('#loading')).toBeHidden({timeout:120_000});await expect.poll(()=>page.evaluate(()=>!!window.__YUGA.snapshot()&&window.__YUGA.metrics().ready)).toBe(true);}
export async function rendered(page:Page){await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));}
export async function imageEvidence(page:Page,info:TestInfo,name:string){await rendered(page);await page.screenshot({path:info.outputPath(`${name}.png`)});}
export async function nativeWalk(page:Page,key:string,until:(actor:Actor)=>boolean,timeout=20_000){
 await page.keyboard.down(key);try{await expect.poll(async()=>{const actor=await localActor(page);expect(actor.health,`Native route died at ${actor.x},${actor.z}`).toBeGreaterThan(0);return until(actor);},{timeout,intervals:[60,100]}).toBe(true);}finally{await page.keyboard.up(key);}
}
export async function inputObservation(page:Page){
 return page.evaluate(()=>{const state=window.__YUGA.snapshot()!,metrics=window.__YUGA.metrics();return{state,metrics,actor:state.actors.find(actor=>actor.id===window.__YUGA.playerId())!,visibility:document.visibilityState,focus:document.activeElement?.id,dialog:document.querySelector('dialog[open]')?.id};});
}
/** Native bounded key pulses; every decision uses one coherent received state and
 * the actual client aim. Authority yaw may lag a rendered frame or network tick. */
export async function keyboardYaw(page:Page,target:number|((state:ArenaSnapshot,actor:Actor)=>number)){
 const end=Date.now()+12_000;let last:Awaited<ReturnType<typeof inputObservation>>|undefined;
 while(Date.now()<end){
  last=await inputObservation(page);
  const desired=typeof target==='number'?target:target(last.state,last.actor),delta=Math.atan2(Math.sin(desired-last.metrics.yaw),Math.cos(desired-last.metrics.yaw));
  if(Math.abs(delta)<.10)return;
  if(!last.metrics.ready||last.dialog||last.visibility!=='visible'||last.actor.health<=0)throw new Error(`Native aim unavailable: ${JSON.stringify(last)}`);
  const sequence=last.actor.lastInputSeq;
  await page.keyboard.press(delta>0?'KeyJ':'KeyL',{delay:Math.max(30,Math.min(160,Math.abs(delta)/1.6*750))});
  // A neutral, newer input observation avoids deciding from the pre-pulse packet.
  await expect.poll(async()=>(await localActor(page)).lastInputSeq,{timeout:3_000,intervals:[30,50]}).toBeGreaterThan(sequence);
 }
 throw new Error(`Native keyboard aim timed out: ${JSON.stringify(last)}`);
}

/** Native pointer-lock mouse correction after coarse keyboard rotation. The click
 * can fire an ordinary basic shot; this is gameplay, never a silent aim command. */
export async function mouseAimAt(page:Page,targetId:string,tolerance=.006){
 const viewport=page.viewportSize()!;let x=viewport.width*.5,y=viewport.height*.42;
 await page.mouse.click(x,y);await expect.poll(()=>page.evaluate(()=>document.pointerLockElement?.id)).toBe('arena');
 for(let i=0;i<5;i++){
  const observation=await inputObservation(page),actor=observation.actor,target=observation.state.neutrals.find(n=>n.id===targetId)??observation.state.actors.find(a=>a.id===targetId);
  if(!target)throw new Error(`Native mouse target missing: ${targetId}`);
  const yaw=Math.atan2(target.x-actor.x,target.z-actor.z),pitch=Math.atan2(target.y+1.1-actor.y-1.2,Math.hypot(target.x-actor.x,target.z-actor.z));
  const dyaw=Math.atan2(Math.sin(yaw-observation.metrics.yaw),Math.cos(yaw-observation.metrics.yaw)),dpitch=pitch-observation.metrics.pitch;
  if(Math.abs(dyaw)<tolerance&&Math.abs(dpitch)<tolerance)return observation;
  const sensitivity=Number(await page.locator('#sensitivity').inputValue())/100;
  x-=dyaw/(.0025*sensitivity);y-=dpitch/(.0025*sensitivity);await page.mouse.move(x,y);
 }
 throw new Error(`Native mouse correction failed: ${JSON.stringify(await inputObservation(page))}`);
}
