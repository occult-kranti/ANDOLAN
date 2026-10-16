import { expect, test, type Page, type TestInfo } from '@playwright/test';
import type { ReferenceSnapshot } from '../reference/types';

interface Metrics { ready: boolean; loading: boolean; playing: boolean; paused: boolean; yaw: number; pitch: number; warmFrames: number; renderedFrames: number; lastResult: { ok: boolean; code: string } | null }
interface LabApi { snapshot(): ReferenceSnapshot | undefined; metrics(): Metrics; assets(): { fallback: unknown[]; instances: { id: string; heroId: string; loaded: boolean; fallback: boolean }[] } | undefined }
const read = (page: Page) => page.evaluate(() => {
  const api = (window as unknown as { __YUGA_LAB: LabApi }).__YUGA_LAB;
  return { state: api.snapshot()!, metrics: api.metrics(), visibility: document.visibilityState, focus: document.activeElement?.id };
});
const actor = (value: Awaited<ReturnType<typeof read>>) => value.state.arena.actors.find(item => item.id === value.state.localId)!;

async function boot(page: Page) {
  const errors: string[] = [], consoleErrors: string[] = [];
  page.on('pageerror', error => errors.push(error.stack || error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  if (process.env.CI || process.env.YUGA_SOFTWARE_RENDERING === '1') await page.addInitScript(() => {
    // Test-only maximum10fps render budget; preserves callback cancellation,
    // timestamps and next-frame ordering. It never advances game time/state.
    const native = requestAnimationFrame.bind(window), queue = new Map<number, FrameRequestCallback>();
    let serial = 0, dispatching = false, scheduled = false;
    const schedule = () => {
      if (scheduled || dispatching || !queue.size) return;
      scheduled = true;
      window.setTimeout(() => native(time => {
        scheduled = false; dispatching = true;
        for (const id of [...queue.keys()]) { const callback = queue.get(id); queue.delete(id); if (callback) try { callback(time); } catch (error) { window.setTimeout(() => { throw error; }, 0); } }
        dispatching = false; schedule();
      }), 100);
    };
    window.requestAnimationFrame = callback => { const id = ++serial; queue.set(id, callback); schedule(); return id; };
    window.cancelAnimationFrame = id => { queue.delete(id); };
  });
  await page.goto('/'); await expect(page.locator('#lab-lobby')).toBeVisible();
  await page.locator('#lab-lobby-settings').click(); await page.locator('#lab-quality').selectOption('low'); await page.locator('#lab-resume').click();
  return { errors, consoleErrors };
}

async function launch(page: Page, mode: 'lane-economy' | 'control-point', hero = 'rama') {
  await page.locator(`[data-experiment="${mode}"]`).click(); await page.locator('#lab-hero').selectOption(hero); await page.locator('#lab-seed').fill('7301');
  await page.locator('#lab-launch').click(); await ready(page);
}

async function ready(page: Page) {
  await expect(page.locator('#lab-loading')).toBeHidden({ timeout: 120_000 });
  await expect.poll(async () => { const value = await read(page); return !!value.state && value.metrics.ready && value.metrics.warmFrames === 2; }).toBe(true);
  await expect(page.locator('#lab-hud')).toHaveAttribute('data-ready', 'true');
  const assets = await page.evaluate(() => (window as unknown as { __YUGA_LAB: LabApi }).__YUGA_LAB.assets());
  const value = await read(page);
  expect(assets?.instances.some(instance => instance.id === value.state.localId && instance.loaded && !instance.fallback)).toBe(true);
  expect(assets?.fallback).toEqual([]);
}

async function shot(page: Page) {
  const before = await read(page), ammo = before.state.weapons[before.state.localId]!.ammo;
  await page.keyboard.down('KeyF');
  try { await expect.poll(async () => { const value = await read(page); return value.state.weapons[value.state.localId]!.ammo; }).toBeLessThan(ammo); }
  finally { await page.keyboard.up('KeyF'); }
  const after = await read(page);
  expect(after.state.arena.events.some(event => event.actorId === after.state.localId && event.type === 'shot' && event.time >= before.state.arena.time)).toBe(true);
  return after;
}

async function settled(page: Page) {
  let previous = await read(page);
  await expect.poll(async () => {
    const next = await read(page), a = actor(previous), b = actor(next);
    const stopped = next.state.arena.tick > previous.state.arena.tick && b.lastInputSeq > a.lastInputSeq && Math.hypot(b.x - a.x, b.z - a.z) < .03;
    previous = next; return stopped;
  }, { timeout: 4_000, intervals: [70, 100] }).toBe(true);
  return previous;
}

async function capture(page: Page, info: TestInfo, name: string) {
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  await page.screenshot({ path: info.outputPath(`${name}.png`) });
}

async function insideDialog(page: Page, selector: string, dialog: string) {
  await expect(page.locator(selector)).toBeVisible();
  const layout = await page.locator(selector).evaluate((element, dialogSelector) => {
    const bounds = element.getBoundingClientRect(), frame = document.querySelector(dialogSelector)!.getBoundingClientRect();
    return { left: bounds.left, right: bounds.right, top: bounds.top, bottom: bounds.bottom,
      frame: { left: frame.left, right: frame.right, top: frame.top, bottom: frame.bottom }, width: innerWidth, height: innerHeight };
  }, dialog);
  expect(layout.left, `${selector} left edge`).toBeGreaterThanOrEqual(Math.max(0, layout.frame.left));
  expect(layout.right, `${selector} right edge`).toBeLessThanOrEqual(Math.min(layout.width, layout.frame.right));
  expect(layout.top, `${selector} top edge`).toBeGreaterThanOrEqual(Math.max(0, layout.frame.top));
  expect(layout.bottom, `${selector} bottom edge`).toBeLessThanOrEqual(Math.min(layout.height, layout.frame.bottom));
  return layout;
}

async function scoreboardClear(page: Page) {
  const score = await page.locator('.scoreboard').boundingBox(), menus = await page.locator('.match-tools').boundingBox();
  expect(score).not.toBeNull(); expect(menus).not.toBeNull();
  const overlap = Math.max(0, Math.min(score!.x + score!.width, menus!.x + menus!.width) - Math.max(score!.x, menus!.x))
    * Math.max(0, Math.min(score!.y + score!.height, menus!.y + menus!.height) - Math.max(score!.y, menus!.y));
  expect(overlap, 'Controls and Pause must not cover either score or its labels').toBe(0);
  return { score, menus, overlap };
}

async function evidence(page: Page, info: TestInfo, errors: { errors: string[]; consoleErrors: string[] }, details: unknown) {
  const current = await read(page).catch(() => null);
  await info.attach('reference-lab-observations', { body: JSON.stringify({ scope: 'Ordinary browser inputs, read-only diagnostics; no actor/health/clock injection. Software render cap is a functional budget, not hardware performance evidence.', ...errors, details, final: current }, null, 2), contentType: 'application/json' });
}

test('native lane launch, movement, aim, primary reload, paused forge and fresh restart', async ({ page }, info) => {
  const errors = await boot(page), details: unknown[] = [];
  try {
    await expect(page.locator('#lab-hero option')).toHaveCount(14);
    await capture(page, info, 'lab-desktop-lobby'); await launch(page, 'lane-economy');
    expect((await read(page)).state.objective).toBeNull();
    const initial = await read(page); await page.keyboard.down('KeyA');
    try { await expect.poll(async () => actor(await read(page)).x).toBeGreaterThan(actor(initial).x + 2); }
    finally { await page.keyboard.up('KeyA'); }
    await settled(page);
    await page.mouse.move(450, 250); await page.mouse.down(); await page.mouse.move(490, 230); await page.mouse.up();
    const aimed = await read(page); expect(aimed.metrics.yaw).toBeLessThan(-.05); expect(aimed.metrics.pitch).toBeGreaterThan(.04);
    details.push({ initial, aimed, fired: await shot(page) });
    await page.keyboard.press('KeyQ');
    await expect.poll(async () => actor(await read(page)).cooldowns[0]).toBeGreaterThan(0);
    await page.keyboard.press('KeyX');
    await expect.poll(async () => { const value = await read(page); return value.state.weapons[value.state.localId]!.reloadRemaining; }).toBeGreaterThan(0);
    await expect.poll(async () => { const value = await read(page); return value.state.weapons[value.state.localId]!.ammo; }, { timeout: 8_000 }).toBe(12);
    await page.keyboard.press('Escape'); await expect(page.locator('#lab-settings-dialog')).toBeVisible();
    const paused = await read(page);
    await page.keyboard.press('KeyW', { delay: 150 }); await page.keyboard.press('KeyF'); await page.keyboard.press('KeyQ'); await page.keyboard.press('KeyX');
    expect((await read(page)).state).toEqual(paused.state);
    await capture(page, info, 'lab-desktop-settings'); await page.locator('#lab-resume').click();
    await page.keyboard.press('KeyB'); await expect(page.locator('#lab-forge-dialog')).toBeVisible();
    const forgeTime = (await read(page)).state.arena.time;
    await page.locator('[data-upgrade="power"]').click();
    await expect(page.locator('#lab-forge-result')).toContainText('Upgrade purchased');
    let value = await read(page); expect(actor(value).credits).toBe(60); expect(actor(value).upgrades.power).toBe(1); expect(value.state.arena.time).toBe(forgeTime);
    expect(value.state.economy.receipts.filter(receipt => receipt.actorId === value.state.localId)).toMatchObject([{ kind: 'spend', amount: 120, balance: 60 }]);
    await page.locator('[data-upgrade="power"]').click(); await expect(page.locator('#lab-forge-result')).toContainText('Earn more credits');
    expect(actor(await read(page)).credits).toBe(60);
    await page.locator('#lab-forge-dialog [data-close]').click(); await capture(page, info, 'lab-desktop-game');
    await page.locator('#lab-pause').click(); const epoch = value.state.epoch;
    await page.locator('#lab-restart').click(); await ready(page); value = await read(page);
    expect(value.state.epoch).toBeGreaterThan(epoch); expect(value.state.arena.time).toBeLessThan(1);
    expect(actor(value).credits).toBe(180); expect(actor(value).upgrades.power).toBe(0); expect(value.state.weapons[value.state.localId]!.ammo).toBe(12);
    expect(value.state.economy.receipts.filter(receipt => receipt.actorId === value.state.localId)).toEqual([]);
    await page.locator('#lab-pause').click(); await page.locator('#lab-back').click(); await expect(page.locator('#lab-lobby')).toBeVisible();
    expect(errors.errors).toEqual([]); expect(errors.consoleErrors).toEqual([]);
  } finally { await evidence(page, info, errors, details); }
});

test.describe('mobile lab', () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  test('native touch controls, reachable settings and narrow lobby reflow', async ({ page }, info) => {
    const errors = await boot(page), details: unknown[] = [];
    const touch = await page.context().newCDPSession(page);
    try {
      await page.setViewportSize({ width: 320, height: 740 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(321);
      await capture(page, info, 'lab-mobile-320-lobby');
      await page.setViewportSize({ width: 390, height: 844 }); await launch(page, 'lane-economy', 'sita');
      const before = await read(page);
      const forward = await page.locator('[data-touch-key="KeyW"]').boundingBox(); expect(forward).not.toBeNull();
      await touch.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: forward!.x + forward!.width / 2, y: forward!.y + forward!.height / 2 }] });
      try { await expect.poll(async () => actor(await read(page)).z).toBeGreaterThan(actor(before).z + 1); }
      finally { await touch.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); }
      await settled(page);
      const fire = await page.locator('#lab-touch-fire').boundingBox(); expect(fire).not.toBeNull();
      await touch.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: fire!.x + fire!.width / 2, y: fire!.y + fire!.height / 2 }] });
      try { await expect.poll(async () => { const value = await read(page); return value.state.weapons[value.state.localId]!.ammo; }).toBeLessThan(12); }
      finally { await touch.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); }
      await page.locator('[data-ability="0"]').tap(); await expect.poll(async () => actor(await read(page)).cooldowns[0]).toBeGreaterThan(0);
      for (const selector of ['#lab-touch-fire', '#lab-reload', '[data-ability="0"]', '[data-touch-key="KeyW"]']) {
        const box = await page.locator(selector).boundingBox(); expect(box, selector).not.toBeNull();
        expect(box!.x).toBeGreaterThanOrEqual(0); expect(box!.x + box!.width).toBeLessThanOrEqual(391); expect(box!.y + box!.height).toBeLessThanOrEqual(845);
      }
      details.push({ before, after: await read(page) }); await capture(page, info, 'lab-mobile-game');
      await page.locator('#lab-pause').tap(); await expect(page.locator('#lab-settings-dialog')).toBeVisible();
      const dialogWidth = await page.locator('#lab-settings-dialog').evaluate(element => ({ scroll: element.scrollWidth, client: element.clientWidth }));
      expect(dialogWidth.scroll, 'Mobile settings must not require horizontal scrolling').toBeLessThanOrEqual(dialogWidth.client);
      const settingsBounds = [];
      for (const selector of ['#lab-quality', '#lab-lighting', '#lab-sensitivity', '#lab-sound-preview']) {
        await page.locator(selector).scrollIntoViewIfNeeded();
        settingsBounds.push({ selector, bounds: await insideDialog(page, selector, '#lab-settings-dialog') });
      }
      details.push({ dialogWidth, settingsBounds });
      await page.locator('#lab-settings-title').scrollIntoViewIfNeeded(); await capture(page, info, 'lab-mobile-settings');
      await page.locator('#lab-back').tap(); await expect(page.locator('#lab-lobby')).toBeVisible();
      expect(errors.errors).toEqual([]); expect(errors.consoleErrors).toEqual([]);
    } finally { await touch.detach(); await evidence(page, info, errors, details); }
  });
});

test('native control court traversal, contest, normal-clock result and replay', async ({ page }, info) => {
  test.setTimeout(420_000);
  await page.setViewportSize({ width: 480, height: 400 });
  const errors = await boot(page), route: unknown[] = [], observations: unknown[] = [];
  let contested = false, captured = false, scoring = false;
  try {
    await launch(page, 'control-point', 'bhima');
    observations.push({ layoutAtLaunch: await scoreboardClear(page) });
    const started = Date.now();
    // Ordinary released pulses enter the clear corridor beside the friendly tower.
    for (let pulse = 0; pulse < 20; pulse++) {
      const value = await read(page), self = actor(value); route.push({ time: value.state.arena.time, x: self.x, z: self.z, health: self.health });
      expect(self.health).toBeGreaterThan(0);
      if (self.x >= 4.5 && self.x <= 7.5) break;
      await page.keyboard.press(self.x < 4.5 ? 'KeyA' : 'KeyD', { delay: 150 }); await settled(page);
    }
    expect(actor(await read(page)).x).toBeGreaterThanOrEqual(4.5); expect(actor(await read(page)).x).toBeLessThanOrEqual(7.5);
    await page.keyboard.down('KeyW');
    try {
      await expect.poll(async () => {
        const value = await read(page), self = actor(value); route.push({ time: value.state.arena.time, x: self.x, z: self.z, health: self.health });
        expect(self.health, 'Normal native approach must reach the court alive').toBeGreaterThan(0);
        return self.z;
      }, { timeout: 25_000, intervals: [100, 200] }).toBeGreaterThan(-3);
    } finally { await page.keyboard.up('KeyW'); }
    const arrived = await settled(page), self = actor(arrived), point = arrived.state.objective!;
    expect(Math.hypot(self.x - point.x, self.z - point.z)).toBeLessThanOrEqual(point.radius);
    await capture(page, info, 'lab-control-native-court');
    await shot(page); await page.keyboard.press('KeyQ');
    await expect.poll(async () => {
      const value = await read(page), objective = value.state.objective!;
      contested ||= objective.contested; captured ||= objective.owner !== null; scoring ||= objective.scores.sun + objective.scores.moon > 0;
      if (observations.length < 650) observations.push({ time: value.state.arena.time, phase: value.state.phase, winner: value.state.winner, point: objective, self: { x: actor(value).x, z: actor(value).z, health: actor(value).health, deaths: actor(value).deaths } });
      return value.state.phase;
    }, { timeout: 300_000, intervals: [500] }).toBe('finished');
    const finished = await read(page);
    expect(contested).toBe(true); expect(captured).toBe(true); expect(scoring).toBe(true);
    expect(finished.state.arena.time).toBeLessThanOrEqual(240.000001); expect(finished.state.winner).not.toBeNull(); expect(finished.state.reason).not.toBe('');
    await expect(page.locator('#lab-result-dialog')).toBeVisible();
    expect(await page.locator('#lab-result-dialog').evaluate(element => element.scrollTop), 'Result must initially open at its heading').toBe(0);
    await expect(page.locator('#lab-result-title')).toBeFocused();
    const resultLayout = { heading: await insideDialog(page, '#lab-result-title', '#lab-result-dialog'), reason: await insideDialog(page, '#lab-result-reason', '#lab-result-dialog') };
    await capture(page, info, 'lab-control-normal-result');
    await page.keyboard.press('Tab'); await expect(page.locator('#lab-result-restart')).toBeFocused();
    const restartLayout = await insideDialog(page, '#lab-result-restart', '#lab-result-dialog');
    await page.keyboard.press('Tab'); await expect(page.locator('#lab-result-back')).toBeFocused();
    const backLayout = await insideDialog(page, '#lab-result-back', '#lab-result-dialog');
    observations.push({ resultLayout, restartLayout, backLayout });
    await capture(page, info, 'lab-control-result-actions');
    observations.push({ normalClockWallMilliseconds: Date.now() - started, terminalReason: finished.state.reason, fixture: false });
    await page.locator('#lab-result-restart').click(); await ready(page);
    const replay = await read(page); expect(replay.state.epoch).toBeGreaterThan(finished.state.epoch); expect(replay.state.arena.time).toBeLessThan(1);
    expect(replay.state.objective).toMatchObject({ owner: null, progress: 0, scores: { sun: 0, moon: 0 } });
    expect(replay.state.weapons[replay.state.localId]!.ammo).toBe(12); expect(actor(replay).credits).toBe(180);
    await shot(page); await page.keyboard.press('KeyQ'); await expect.poll(async () => actor(await read(page)).cooldowns[0]).toBeGreaterThan(0);
    expect(errors.errors).toEqual([]); expect(errors.consoleErrors).toEqual([]);
  } finally { await evidence(page, info, errors, { route, observations, contested, captured, scoring, viewportScope: '480×400 functional software-render budget; no hardware performance claim.' }); }
});
