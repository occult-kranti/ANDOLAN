import { test, expect } from '@playwright/test';
import { boot, localActor, waitReady, imageEvidence } from './browser-harness';
import type { ArenaWorld } from '../client/world';

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
 expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);await info.attach('native-fixed-lighting',{body:JSON.stringify({scope:'Native settings at an unchanged ordinary Practice spawn; actual low/high day/night frames and reload persistence. Fixed modes are user settings, not clock injection. This does not claim a full natural480-second lighting cycle or hardware frame-rate performance.',samples,errors:diagnostics},null,2),contentType:'application/json'});
});
