import { expect, type Page, type TestInfo } from '@playwright/test';
import type { Actor } from '../shared/types';

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
export async function keyboardYaw(page:Page,target:number){
 const end=Date.now()+12_000;let held='';try{while(Date.now()<end){const actor=await localActor(page),delta=Math.atan2(Math.sin(target-actor.yaw),Math.cos(target-actor.yaw));if(Math.abs(delta)<.10)return;const next=delta>0?'KeyJ':'KeyL';if(next!==held){if(held)await page.keyboard.up(held);await page.keyboard.down(next);held=next;}await page.waitForTimeout(45);}throw new Error(`Keyboard aim failed: ${JSON.stringify({target,actor:await localActor(page)})}`);}finally{if(held)await page.keyboard.up(held);}
}
