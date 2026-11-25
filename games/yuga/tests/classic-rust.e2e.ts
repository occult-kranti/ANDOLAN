import { expect, test, type Page } from '@playwright/test';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { HEROES } from '../shared/heroes';
import { arenaState, boot, localActor, nativeWalk, waitReady } from './browser-harness';

type Model = {
  id: string; heroId: string; loaded: boolean; fallback: boolean; skinned: boolean;
  bones: number; clips: string[]; transitions: Record<string,number>; pose: number[];
};
const digest = (b: Buffer) => createHash('sha256').update(b).digest('hex');
async function actorModel(page: Page) {
  return page.evaluate(() => {
    const debug = window.__YUGA as typeof window.__YUGA & {assets(): {instances: Model[]}};
    return debug.assets()?.instances.find(i=>i.id===debug.playerId());
  });
}

test('the fourteen Rust sparring kits use the Sangam arena and real player controls', async ({page}, info) => {
  test.setTimeout(22 * 60_000);
  const diagnostics=await boot(page);
  const checks:string[]=[];
  const heroes:Record<string,unknown>[]=[];
  const check = (value:boolean, description:string) => {expect(value,description).toBe(true);checks.push(description);};
  const list=page.locator('[data-hero]');
  await expect(list).toHaveCount(HEROES.length);
  check(HEROES.length===14,'all fourteen roster entries appear on the live selection screen');
  const wasmResponses = new Set<string>();
  page.on('response',r=>{if(r.url().includes('classic-roster.wasm')&&r.ok()) wasmResponses.add(new URL(r.url()).pathname);});
  const detailed = new Set(['rama','ravana','subhadra','ulupi']);
  for(const [index,hero] of HEROES.entries()) {
    await page.locator(`[data-hero="${hero.id}"]`).click();
    await page.locator('#sparring-play').click();
    await waitReady(page);
    await expect(page.locator('#hud')).toHaveAttribute('data-mode','sparring');
    await expect(page.locator('#match-mode')).toHaveText('RUST SPARRING',{ignoreCase:true});
    await expect(page.locator('#upgrades-open')).toBeHidden();
    const before=await arenaState(page);
    expect(before.room).toBe('RUST-SPARRING');
    const actor=await localActor(page);
    expect(actor.heroId).toBe(hero.id);
    for(const id of ['self','ally','enemy']) expect(before.actors.some(a=>a.id===id)).toBe(true);
    await expect.poll(async()=>{
      const m=await actorModel(page);return !!m?.loaded && m.skinned && !m.fallback && m.heroId===hero.id;
    },{timeout:60_000}).toBe(true);
    const model=(await actorModel(page))!;
    expect(model.bones).toBeGreaterThan(30);expect(model.clips).toContain('fire');
    const slots = detailed.has(hero.id) ? [0,1,2] : [index%3];
    const casts = [];
    if(detailed.has(hero.id)) {
      await nativeWalk(page,'KeyW',a=>a.z>actor.z+.3);
      const baseline=(await arenaState(page)).events.at(-1)?.id??0;
      await page.keyboard.down('KeyF');
      try {
        await expect.poll(async()=>(await arenaState(page)).events.some(e=>e.actorId==='self' && e.id>baseline && e.type==='shot'),
          {timeout:25_000}).toBe(true);
      } finally {await page.keyboard.up('KeyF');}
    }
    for(const slot of slots) {
      const baseline=(await arenaState(page)).events.at(-1)?.id??0;
      await page.keyboard.press(['KeyQ','KeyE','KeyR'][slot]);
      await expect.poll(async()=>(await localActor(page)).cooldowns[slot],{timeout:20_000}).toBeGreaterThan(0);
      await expect.poll(async()=>(await arenaState(page)).events.some(e=>e.id>baseline&&e.actorId==='self'&&e.type==='ability'),
        {timeout:22_000}).toBe(true);
      const event=(await arenaState(page)).events.find(e=>e.id>baseline&&e.actorId==='self'&&e.type==='ability')!;
      casts.push({slot,label:event.label,mechanic:hero.abilities[slot].kind,tick:(await arenaState(page)).tick});
      await expect.poll(async()=>!!(await localActor(page)).cast,{timeout:25_000}).toBe(false);
    }
    heroes.push({id:hero.id,role:hero.role,weapon:hero.weapon,bones:model.bones,clips:model.clips,casts,
      physical_movement_and_primary:detailed.has(hero.id)});
    if(hero.id==='rama') {
      await page.locator('#sparring-reset').click();await waitReady(page);
      await expect.poll(async()=>{const a=await localActor(page);return a.heroId==='rama' && a.cooldowns.every(c=>c===0) && Math.abs(a.x)<.01 && Math.abs(a.z)<.01;}).toBe(true);
      checks.push('reset restored Rama, his opening position and fresh ability cooldowns');
    }
    console.log('Rust graphical kit',hero.id,model.bones,'joints',casts.map(c=>c.label).join(', '));
    await page.locator('#sparring-roster').click();
    await expect(page.locator('#lobby')).toBeVisible();
  }
  check(wasmResponses.size>0,'the real Rust Wasm loaded from the Sangam application');
  check(heroes.length===14,'all fourteen skinned rigs entered sparring and accepted a physical ability command');
  await page.locator('#practice-play').click();
  await waitReady(page);
  expect((await arenaState(page)).room).not.toBe('RUST-SPARRING');
  expect((await arenaState(page)).actors.filter(a=>a.kind==='hero')).toHaveLength(6);
  await page.keyboard.press('Escape');await page.locator('#leave-game').click();
  await expect(page.locator('#lobby')).toBeVisible();
  checks.push('existing offline six-hero practice still starts and returns to the menu');
  expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);
  const evidence={
    scope:'Sangam Vite development, ordinary menu, keyboard and buttons, actual Wasm and imported PlayCanvas skins',
    checks,heroes,wasm_requests:[...wasmResponses],diagnostics,
    wasm_sha256:digest(await readFile(resolve('games/yuga/client/assets/classic-roster.wasm'))),
    test_sha256:digest(await readFile(resolve('games/yuga/tests/classic-rust.e2e.ts'))),
  };
  await writeFile(info.outputPath('classic-rust-graphical.json'),JSON.stringify(evidence,null,2)+'\n');
});
