import { test, expect, type Page } from '@playwright/test';
import { HEROES } from '../shared/heroes';
import { HERO_GUIDES } from '../shared/hero-guide';
import { boot, arenaState, localActor, waitReady, imageEvidence, rendered } from './browser-harness';

async function start(page:Page){await page.locator('#practice-play').click();await waitReady(page);}
async function roster(page:Page){await page.keyboard.press('Escape');await page.locator('#leave-game').click();await expect(page.locator('#lobby')).toBeVisible();}

test('native optional practice goals preserve pause, complete actions, dismiss and exclude online',async({page},info)=>{
 test.setTimeout(180_000);const diagnostics=await boot(page);
 await expect(page.locator('#practice-focus')).toHaveValue('');await start(page);await expect(page.locator('#practice-goal')).toBeHidden();await roster(page);
 await page.locator('#practice-focus').selectOption('ability');await start(page);await expect(page.locator('#practice-goal-title')).toHaveText('Try an ability');await expect(page.locator('#practice-goal')).not.toHaveClass(/complete/);
 await page.keyboard.press('Escape');const paused=await arenaState(page);await page.keyboard.press('KeyQ');await page.waitForTimeout(350);expect((await arenaState(page)).time).toBe(paused.time);expect((await localActor(page)).cooldowns[0]).toBe(0);await expect(page.locator('#practice-goal')).not.toHaveClass(/complete/);
 await page.locator('#resume-game').click();await page.keyboard.press('KeyQ');await expect(page.locator('#practice-goal-progress')).toHaveText('Your ability started.');await expect.poll(async()=>(await localActor(page)).cooldowns[0]).toBeGreaterThan(0);await imageEvidence(page,info,'practice-native-ability-complete');
 await page.locator('#practice-dismiss').focus();await page.keyboard.press('Space');await expect(page.locator('#practice-goal')).toBeHidden();await expect(page.locator('#arena')).toBeFocused();await rendered(page);expect((await localActor(page)).y).toBe(0);
 await page.keyboard.press('Escape');await page.locator('#resume-game').click();await expect(page.locator('#practice-goal')).toBeHidden();await roster(page);
 await page.locator('#practice-focus').selectOption('upgrade');await start(page);await expect(page.locator('#practice-goal')).not.toHaveClass(/complete/);await page.keyboard.press('KeyB');const forgeTime=(await arenaState(page)).time;await page.locator('#buy-power').click();await expect.poll(async()=>(await localActor(page)).upgrades.power).toBe(1);expect((await arenaState(page)).time).toBe(forgeTime);await expect(page.locator('#practice-goal-progress')).toHaveText('Your upgrade rank increased.');await page.locator('#upgrades-dialog [data-close]').click();await expect(page.locator('#practice-goal')).toHaveClass(/complete/);await imageEvidence(page,info,'practice-native-paused-upgrade');await roster(page);
 // The selected optional goal remains in the roster, but a real server match has no tracker.
 await expect(page.locator('#practice-focus')).toHaveValue('upgrade');await page.locator('#online-open').click();await page.locator('#player-name').fill('Optional goal QA');await page.locator('#join-room').click();await waitReady(page);expect((await arenaState(page)).room).not.toBe('PRACTICE');await expect(page.locator('#practice-goal')).toBeHidden();await page.keyboard.press('KeyQ');await expect.poll(async()=>(await localActor(page)).cooldowns[0]).toBeGreaterThan(0);await expect(page.locator('#practice-goal')).toBeHidden();
 await info.attach('native-practice-goals',{body:JSON.stringify({scope:'Ordinary UI and native Q/Space, local practice authority and actual local WebSocket. Free play bypass, paused skill rejection, goal completion, keyboard dismissal without jumping, per-match reset, paused forge purchase and online exclusion. No actor/timer/command injection.',errors:diagnostics},null,2),contentType:'application/json'});expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);
});

test('labelled eight-second practice module fixture resets goal progress on Play again',async({page},info)=>{
 let replacements=0;
 await page.route('**/client/connection.ts*',async route=>{
  const response=await route.fetch(),body=await response.text();
  const pattern=/new ArenaSimulation\(\{\s*room:\s*["']PRACTICE["'],\s*seed:\s*20261016\s*\}\)/;
  expect(body).toMatch(pattern);replacements++;
  await route.fulfill({response,body:body.replace(pattern,'new ArenaSimulation({room:"PRACTICE",seed:20261016,duration:8})')});
 });
 const diagnostics=await boot(page);await page.locator('#practice-focus').selectOption('ability');await start(page);await page.keyboard.press('KeyQ');await expect(page.locator('#practice-goal')).toHaveClass(/complete/);await expect(page.locator('#result-dialog')).toBeVisible({timeout:25_000});expect((await arenaState(page)).duration).toBe(8);
 await page.locator('#play-again').click();await waitReady(page);await expect(page.locator('#practice-goal')).toBeVisible();await expect(page.locator('#practice-goal')).not.toHaveClass(/complete/);await expect(page.locator('#practice-goal-progress')).toHaveText('Waiting for your next action');expect((await localActor(page)).cooldowns[0]).toBe(0);await page.keyboard.press('KeyQ');await expect(page.locator('#practice-goal')).toHaveClass(/complete/);await imageEvidence(page,info,'fixture-practice-replay-goal');
 expect(replacements).toBe(1);expect(diagnostics.errors).toEqual([]);await info.attach('labelled-practice-replay-fixture',{body:JSON.stringify({scope:'Intercepted development connection-module response changes only Practice duration from480 to8 seconds. Native Q and Play Again verify goal/result UI reset; this is not a normal match completion or replacement for the separately archived480-second native soak.',replacements,errors:diagnostics},null,2),contentType:'application/json'});
});

test('mobile hero guides and optional practice focus fit portrait and landscape',async({browser},info)=>{
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1}),page=await context.newPage();
 try{
  const diagnostics=await boot(page);await page.locator('#hero-guide-summary').tap();
  for(const hero of HEROES){await page.locator(`[data-hero="${hero.id}"]`).tap();await expect(page.locator('#hero-first-action')).toHaveText(HERO_GUIDES[hero.id as keyof typeof HERO_GUIDES].firstAction);for(const note of HERO_GUIDES[hero.id as keyof typeof HERO_GUIDES].abilityNotes)await expect(page.locator('#hero-guide-copy')).toContainText(note);for(const label of ['Power','Vitality','Tempo'])await expect(page.locator('#hero-guide-copy')).toContainText(label);}
  await page.locator('[data-hero="rama"]').tap();await imageEvidence(page,info,'mobile-hero-guide');await page.locator('#practice-focus').selectOption('ability');await start(page);
  const bounds=[];
  for(const viewport of[{width:390,height:844},{width:844,height:390}]){
   await page.setViewportSize(viewport);await rendered(page);await expect(page.locator('#practice-goal')).toBeVisible();
   const boxes=await page.evaluate(()=>{const rect=(id:string)=>{const r=document.getElementById(id)!.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};};return{goal:rect('practice-goal'),pad:rect('touch-pad'),shoot:rect('shoot'),skill:rect('ability-0'),overflow:document.documentElement.scrollWidth>innerWidth};});
   expect(boxes.overflow).toBe(false);expect(boxes.goal.x).toBeGreaterThanOrEqual(0);expect(boxes.goal.right).toBeLessThanOrEqual(viewport.width);expect(boxes.goal.bottom).toBeLessThanOrEqual(viewport.height);
   for(const control of[boxes.pad,boxes.shoot,boxes.skill])expect(boxes.goal.right<=control.x||control.right<=boxes.goal.x||boxes.goal.bottom<=control.y||control.bottom<=boxes.goal.y,'Practice focus must not overlap a primary touch control').toBe(true);
   bounds.push({viewport,...boxes});await imageEvidence(page,info,`mobile-practice-goal-${viewport.width}`);
  }
  await page.locator('#ability-0').tap();await expect(page.locator('#practice-goal')).toHaveClass(/complete/);await page.locator('#practice-dismiss').tap();await expect(page.locator('#practice-goal')).toBeHidden();expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);
  await info.attach('native-mobile-practice-goals',{body:JSON.stringify({scope:'Native Chromium touch emulation and real practice state; fourteen guide texts and portrait/landscape control separation. Not physical-device ergonomics or performance.',bounds,errors:diagnostics},null,2),contentType:'application/json'});
 }finally{await context.close();}
});
