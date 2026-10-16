import { test, expect } from '@playwright/test';
import { boot, localActor, waitReady, imageEvidence, nativeWalk, keyboardYaw } from './browser-harness';
import type { ArenaWorld } from '../client/world';
import type { Actor } from '../shared/types';

test('native fixed day and night lighting persists and renders the same arena position',async({page},info)=>{
 test.setTimeout(180_000);const diagnostics=await boot(page);await page.locator('#practice-play').click();await waitReady(page);const position=await localActor(page),samples=[];
 for(const quality of ['low','high'])for(const mode of ['day','night']){
  await page.keyboard.press('Escape');await page.locator('#quality').selectOption(quality);await page.locator('#lighting').selectOption(mode);await page.locator('#resume-game').click();
  const lighting=()=>page.evaluate(()=>(window.__YUGA as unknown as{assets():ReturnType<ArenaWorld['assetDiagnostics']>}).assets().lighting);
  await expect.poll(async()=>(await lighting()).sample.phase).toBe(mode==='day'?'Day':'Night');const sample=await lighting(),actor=await localActor(page);expect(actor.x).toBe(position.x);expect(actor.z).toBe(position.z);
  samples.push({quality,mode,lighting:sample,position:{x:actor.x,z:actor.z}});await imageEvidence(page,info,`environment-${quality}-${mode}`);
 }
 await page.reload();await page.waitForFunction(()=>!!window.__YUGA);await page.locator('#lobby-settings').click();await expect(page.locator('#lighting')).toHaveValue('night');await expect(page.locator('#quality')).toHaveValue('high');await page.locator('#lighting').selectOption('cycle');await page.locator('#quality').selectOption('low');await page.locator('#resume-game').click();await page.locator('#practice-play').click();await waitReady(page);
 expect((await page.evaluate(()=>(window.__YUGA as unknown as{assets():ReturnType<ArenaWorld['assetDiagnostics']>}).assets().lighting)).mode).toBe('cycle');
 // Approach west along the allied spawn edge before heading north. Crossing
 // the active central fight is unnecessary for this coastal geometry check.
 const route:Array<{x:number;z:number;health:number;lastInputSeq:number}>=[];
 const observed=(until:(actor:Actor)=>boolean)=>(actor:Actor)=>{expect([actor.x,actor.z,actor.health,actor.lastInputSeq].every(Number.isFinite)).toBe(true);route.push({x:actor.x,z:actor.z,health:actor.health,lastInputSeq:actor.lastInputSeq});return until(actor);};
 try{await nativeWalk(page,'KeyD',observed(actor=>actor.x<-46),25_000);await nativeWalk(page,'KeyW',observed(actor=>actor.z>5),35_000);}finally{await info.attach('native-coastal-route',{body:JSON.stringify({scope:'Ordinary D along the allied spawn edge, then W up the western corridor. Default bots, clock and combat remain active; read-only finite position/health/input-sequence observations, no teleport or state injection.',route},null,2),contentType:'application/json'});}
 await keyboardYaw(page,-1.35);await page.keyboard.press('KeyK',{delay:60});
 await expect.poll(()=>page.evaluate(()=>window.__YUGA.snapshot()!.neutrals.find(n=>n.campId==='west-reeds')!.health),{timeout:35_000}).toBeGreaterThan(0);
 const coastPosition=await localActor(page);expect(coastPosition.health).toBeGreaterThan(0);
 for(const mode of ['day','night']){await page.keyboard.press('Escape');await page.locator('#lighting').selectOption(mode);await page.locator('#resume-game').click();await imageEvidence(page,info,`environment-native-coast-${mode}`);samples.push({quality:'low',mode,lighting:await page.evaluate(()=>(window.__YUGA as unknown as{assets():ReturnType<ArenaWorld['assetDiagnostics']>}).assets().lighting),position:{x:coastPosition.x,z:coastPosition.z}});}
 expect((await localActor(page)).health).toBeGreaterThan(0);
 expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);await info.attach('native-fixed-lighting',{body:JSON.stringify({scope:'Native settings at an unchanged ordinary Practice spawn; actual low/high day/night frames and reload persistence. Then ordinary D/W movement reaches the western court for real guardian/gateway/marsh day/night frames. Fixed modes are user settings, not actor or clock injection. This does not claim a full natural480-second lighting cycle or hardware frame-rate performance.',samples,errors:diagnostics},null,2),contentType:'application/json'});
});
