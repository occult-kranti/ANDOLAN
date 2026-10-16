import { test, expect, type Page } from '@playwright/test';
import type { CommandMessage, InputMessage, ResultMessage, Vec2 } from '../packages/protocol/src/index';
import { CONTRACTS, CITY_OUTCOMES } from '../packages/content/src/contracts';
import { Simulation } from '../packages/sim/src/index';
import { isBlocked, landmark } from '../packages/sim/src/world';

type Intent = Omit<InputMessage, 'type' | 'seq'>;
declare global {
  interface Window {
    __betaIntent?: { axes: Intent; sequence: number; timer: number };
    __betaEvents?: { type: string; code?: string; target: string; at: number; hidden: boolean; focused: boolean }[];
  }
}
const rest: Intent = { moveX: 0, moveZ: 0, forward: 0, turn: 0, sprint: false };
const errors = new WeakMap<Page, string[]>();
const commands = new WeakMap<Page, CommandMessage[]>();
const results = new WeakMap<Page, ResultMessage[]>();
const distance = (a: Vec2, b: Vec2) => Math.hypot(a.x - b.x, a.z - b.z);
const state = (page: Page) => page.evaluate(() => window.__ANDOLAN.snapshot());
const identity = (page: Page) => page.evaluate(() => window.__ANDOLAN.playerId());
async function player(page: Page) { const id = await identity(page); return (await state(page)).players.find(item => item.id === id)!; }
const audio = (page: Page) => page.evaluate(() => window.__ANDOLAN.audio());

async function load(page: Page) {
  errors.set(page, []); commands.set(page, []); results.set(page, []);
  page.on('pageerror', error => errors.get(page)!.push(error.message));
  // Observe real traffic without retaining bearer-token join/welcome messages.
  page.on('websocket', socket => {
    socket.on('framesent', frame => {
      try { const message = JSON.parse(String(frame.payload)); if (message.type === 'command') commands.get(page)!.push(message); } catch { /* Not JSON application traffic. */ }
    });
    socket.on('framereceived', frame => {
      try { const message = JSON.parse(String(frame.payload)); if (message.type === 'result') results.get(page)!.push(message); } catch { /* Not JSON application traffic. */ }
    });
  });
  if (process.env.CI || process.env.ANDOLAN_SOFTWARE_RENDERING === '1') {
    await page.addInitScript(() => {
      if (window.__qaFrameSchedulerInstalled) return;
      window.__qaFrameSchedulerInstalled = true;
      const nativeRequest = window.requestAnimationFrame.bind(window);
      const queued = new Map<number, FrameRequestCallback>();
      let handle = 0, timer: number | undefined, nativeQueued = false, dispatching = false;
      let finishedAt = performance.now() - 100;
      const schedule = () => {
        if (!queued.size || timer !== undefined || nativeQueued || dispatching) return;
        timer = window.setTimeout(() => {
          timer = undefined; nativeQueued = true;
          nativeRequest(timestamp => {
            nativeQueued = false; dispatching = true;
            for (const id of [...queued.keys()]) {
              const callback = queued.get(id); queued.delete(id);
              if (callback) try { callback(timestamp); } catch (error) { window.setTimeout(() => { throw error; }, 0); }
            }
            dispatching = false; finishedAt = performance.now(); schedule();
          });
        }, Math.max(0, 100 - (performance.now() - finishedAt)));
      };
      window.requestAnimationFrame = callback => { const id = ++handle; queued.set(id, callback); schedule(); return id; };
      window.cancelAnimationFrame = id => { queued.delete(id); };
    });
  }
  await page.addInitScript(() => { if (!localStorage.getItem('andolan.settings')) localStorage.setItem('andolan.settings', JSON.stringify({ quality: 'low' })); });
  await page.goto('/');
  await ready(page);
}
async function ready(page: Page) {
  await page.waitForFunction(() => !!window.__ANDOLAN, undefined, { timeout: 90_000 });
  await expect(page.locator('#loading')).toBeHidden();
}
async function frames(page: Page) {
  await page.evaluate(() => new Promise<void>(resolve => {
    let n = 0;
    const next = () => { if (++n === 4) resolve(); else requestAnimationFrame(next); };
    requestAnimationFrame(next);
  }));
}
async function title(page: Page) {
  await page.keyboard.press('Escape');
  await expect(page.locator('#settings-dialog')).toBeVisible();
  await page.locator('#return-title').click();
  await expect(page.locator('#title')).toBeVisible();
}
async function join(page: Page, name: string, room = '') {
  await page.locator('#play-private').click();
  await expect(page.locator('#gameplay')).toHaveValue('freeroam');
  await page.locator('#player-name').fill(name);
  await page.locator('#room-input').fill(room);
  await page.getByRole('button', { name: 'Join the city' }).click();
  await expect.poll(async () => (await state(page)).room).not.toBe('PREVIEW');
  await expect.poll(async () => (await state(page)).gameplay).toBe('freeroam');
  if (room) await expect.poll(async () => (await state(page)).room).toBe(room);
}
async function startIntent(page: Page) {
  await page.evaluate(axes => {
    const controller = { axes, sequence: 8_000_000_000_000_000, timer: 0 };
    controller.timer = window.setInterval(() => window.__ANDOLAN.connection().input({ type: 'input', seq: ++controller.sequence, ...controller.axes }), 35);
    window.__betaIntent = controller;
  }, rest);
}
async function intent(page: Page, axes: Partial<Intent>) {
  await page.evaluate(axes => { window.__betaIntent!.axes = axes; }, { ...rest, ...axes });
}
async function walkOpenAvenue(page: Page, target: Vec2, radius = 3.5) {
  const from = await player(page), length = distance(from, target);
  for (let d = 0; d <= length; d += .35) expect(isBlocked(from.x + (target.x - from.x) * d / length, from.z + (target.z - from.z) * d / length, .7)).toBe(false);
  const deadline = Date.now() + 100_000;
  for (;;) {
    if (Date.now() > deadline) throw new Error(`Ordinary walking timed out: ${JSON.stringify(await player(page))}`);
    const p = await player(page), remaining = distance(p, target);
    if (remaining <= radius) {
      // Cached proximity alone does not prove the walk has stopped or that the
      // connection is fresh. Observe this ordinary neutral packet on the server.
      const stop = await page.evaluate(axes => {
        const controller = window.__betaIntent!;
        controller.axes = axes;
        const seq = ++controller.sequence, tick = window.__ANDOLAN.snapshot().tick;
        window.__ANDOLAN.connection().input({ type: 'input', seq, ...axes });
        return { seq, tick };
      }, rest);
      await expect.poll(async () => {
        const snapshot = await state(page), id = await identity(page);
        return snapshot.tick > stop.tick && snapshot.players.find(person => person.id === id)!.lastInputSeq >= stop.seq;
      }).toBe(true);
      if (distance(await player(page), target) <= radius) return;
      continue;
    }
    await intent(page, { moveX: (target.x - p.x) / remaining, moveZ: (target.z - p.z) / remaining, sprint: true });
    await page.waitForTimeout(85);
  }
}
async function driveRoute(page: Page, vehicleId: string, route: Vec2[]) {
  const deadline = Date.now() + 180_000;
  for (const point of route) {
    for (;;) {
      const car = (await state(page)).vehicles.find(vehicle => vehicle.id === vehicleId)!;
      const remaining = distance(car, point);
      if (remaining < 3.2) break;
      if (Date.now() > deadline) throw new Error(`Ordinary driving timed out: ${JSON.stringify({ car, point })}`);
      const desired = Math.atan2(point.x - car.x, point.z - car.z);
      const angle = Math.atan2(Math.sin(desired - car.heading), Math.cos(desired - car.heading));
      const targetSpeed = Math.abs(angle) > .5 ? 3 : Math.min(8, Math.max(2.5, remaining * .7));
      await intent(page, { forward: Math.max(-1, Math.min(1, (targetSpeed - car.speed) / 8)), turn: Math.max(-1, Math.min(1, angle * 1.8)) });
      await page.waitForTimeout(85);
    }
  }
  await intent(page, rest);
  await expect.poll(async () => Math.abs((await state(page)).vehicles.find(vehicle => vehicle.id === vehicleId)!.speed)).toBeLessThan(.2);
}
async function sendAndObserve(page: Page, command: CommandMessage, count = 1) {
  await page.evaluate(message => window.__ANDOLAN.connection().command(message), command);
  await expect.poll(() => results.get(page)!.filter(result => result.commandId === command.id).length).toBeGreaterThanOrEqual(count);
  return results.get(page)!.filter(result => result.commandId === command.id).at(-1)!;
}
async function entryEvidence(page: Page) {
  const snapshot = await state(page), id = await identity(page);
  const person = snapshot.players.find(item => item.id === id)!;
  const van = snapshot.vehicles.find(item => item.id === 'van-01')!;
  return { tick: snapshot.tick, time: snapshot.time, person, van, distance: distance(person, van), browser: await page.evaluate(() => ({ hidden: document.hidden, focused: document.hasFocus(), activeElement: document.activeElement?.id, modal: document.querySelector('dialog[open]')?.id, status: document.querySelector('#status-text')?.textContent, statusDot: (document.querySelector('#status-dot') as HTMLElement)?.style.background, intent: window.__betaIntent?.axes, events: window.__betaEvents })), commands: commands.get(page), results: results.get(page) };
}
async function chooseJob(page: Page, jobId: string) {
  await page.locator('#jobs-open').click();
  await selectJob(page, jobId);
  await expect(page.locator('#job-start')).toBeEnabled();
  await page.locator('#job-start').click();
  await expect.poll(async () => (await state(page)).contracts.active?.jobId).toBe(jobId);
  await expect(page.locator('#jobs-dialog')).toBeHidden();
  await expect(page.locator('#world')).toBeFocused();
}
async function selectJob(page: Page, jobId: string) {
  if (await page.locator('#job-select').isVisible()) await page.locator('#job-select').selectOption(jobId);
  else await page.locator(`[data-job-id="${jobId}"]`).click();
}

test('solo City practice preserves earned Story and uses native opt-in audio', async ({ page }, testInfo) => {
  test.setTimeout(150_000);
  await load(page);
  expect(await audio(page)).toMatchObject({ started: false, muted: true, contextState: 'uninitialized' });
  await frames(page); await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-title-low.png') });
  await page.locator('#play-story').click();
  await page.keyboard.press('KeyE'); await expect(page.locator('#mission-dialog')).toBeVisible();
  await page.locator('#dialog-continue').click();
  await page.keyboard.press('KeyF'); await expect(page.locator('#driving')).toBeVisible();
  await page.keyboard.press('KeyF'); await expect(page.locator('#driving')).toBeHidden();
  await title(page);
  const earned = await page.evaluate(() => localStorage.getItem('andolan.story.v1'));
  expect(JSON.parse(earned!).mission.stage).toBe('clinic-drive');
  await page.locator('#play-practice').focus(); await page.keyboard.press('Enter');
  await expect.poll(async () => (await state(page)).gameplay).toBe('freeroam');
  await expect(page.locator('#crew-count')).toContainText('Solo practice');
  await frames(page); await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-practice-low.png') });
  await page.keyboard.press('KeyJ'); await expect(page.locator('#jobs-dialog')).toBeVisible();
  await expect(page.locator('[data-job-id]')).toHaveCount(CONTRACTS.length);
  await page.locator('[data-job-id="print-run"]').click();
  await expect(page.locator('#job-start')).toBeDisabled();
  await expect(page.locator('#job-start')).toContainText('4 REPUTATION');
  await page.locator('[data-job-id="pool-car-recall"]').click();
  await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-job-board.png') });
  await page.locator('#job-start').click();
  await expect.poll(async () => (await state(page)).contracts.active?.stageId).toBe('locate');
  await expect(page.locator('#jobs-dialog')).toBeHidden();
  await expect(page.locator('#world')).toBeFocused();
  await page.keyboard.press('KeyE');
  await expect.poll(async () => (await state(page)).contracts.active?.stageId).toBe('check');
  await page.keyboard.press('Escape');
  expect((await audio(page)).started).toBe(false);
  await expect.poll(async () => (await audio(page)).active).toBe(false);
  const preferencesBeforePreview = await page.evaluate(() => localStorage.getItem('andolan.settings'));
  await page.locator('#sound-preview').click();
  await expect.poll(async () => (await audio(page)).previewing, { intervals: [30] }).toBe(true);
  await expect.poll(async () => (await audio(page)).outputRms, { intervals: [30] }).toBeGreaterThan(.000001);
  const previewRms = (await audio(page)).outputRms;
  expect(await audio(page)).toMatchObject({ muted: true, active: false });
  await expect.poll(async () => (await audio(page)).previewing).toBe(false);
  await expect.poll(async () => (await audio(page)).contextState).toBe('suspended');
  expect(await page.evaluate(() => localStorage.getItem('andolan.settings'))).toBe(preferencesBeforePreview);
  await expect(page.locator('#sound-preview')).toHaveText('Test sound');
  await page.locator('#sound').click();
  await expect.poll(async () => (await audio(page)).muted).toBe(false);
  await page.getByRole('button', { name: 'Close settings' }).click();
  await expect.poll(async () => (await audio(page)).contextState).toBe('running');
  const startedAt = (await audio(page)).contextTime;
  await expect.poll(async () => (await audio(page)).contextTime).toBeGreaterThan(startedAt + .1);
  await expect.poll(async () => (await audio(page)).outputRms).toBeGreaterThan(.000001);
  const audibleRms = (await audio(page)).outputRms;
  await page.keyboard.press('Escape');
  await page.locator('#volume').press('Home');
  await page.getByRole('button', { name: 'Close settings' }).click();
  await expect.poll(async () => (await audio(page)).contextState).toBe('running');
  await expect.poll(async () => (await audio(page)).outputRms).toBeLessThan(audibleRms * .05);
  expect((await audio(page)).contextState).toBe('running');
  const attenuatedRms = (await audio(page)).outputRms;
  await page.keyboard.press('Escape');
  for (let n = 0; n < 10; n++) await page.locator('#volume').press('ArrowRight');
  await page.locator('#music').check();
  expect(await audio(page)).toMatchObject({ started: true, muted: false, volume: .1, music: true });
  await page.locator('#sound').click();
  await page.getByRole('button', { name: 'Close settings' }).click();
  await expect.poll(async () => (await audio(page)).active).toBe(true);
  await expect.poll(async () => (await audio(page)).contextState).toBe('suspended');
  expect(await audio(page)).toMatchObject({ muted: true, activeVoices: 0 });
  await page.keyboard.press('Escape');
  await page.locator('#sound').click();
  await page.locator('#quality').selectOption('high');
  await page.getByRole('button', { name: 'Close settings' }).click();
  await expect.poll(async () => (await audio(page)).contextState).toBe('running');
  await frames(page); await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-practice-high.png') });
  await page.keyboard.press('Escape'); await page.locator('#quality').selectOption('low');
  await page.getByRole('button', { name: 'Close settings' }).click();
  await page.keyboard.press('KeyF'); await expect(page.locator('#driving')).toBeVisible();
  const before = await player(page);
  await page.keyboard.down('KeyW');
  try { await expect.poll(async () => distance(await player(page), before)).toBeGreaterThan(3); }
  finally { await page.keyboard.up('KeyW'); }
  await expect.poll(async () => Math.abs((await state(page)).vehicles[0]!.speed)).toBeLessThan(.2);
  expect((await audio(page)).activeVoices).toBeLessThanOrEqual(24);
  await page.keyboard.press('KeyF'); await expect(page.locator('#driving')).toBeHidden();
  await page.keyboard.press('KeyJ');
  const accepted = page.waitForEvent('dialog'); const cancellation = page.locator('#job-cancel').click();
  const confirmation = await accepted; expect(confirmation.type()).toBe('confirm'); await confirmation.accept(); await cancellation;
  await expect.poll(async () => (await state(page)).contracts.active).toBeNull();
  expect((await state(page)).contracts.progression).toEqual({ credits: 0, reputation: 0, project: 0, completed: 0 });
  await page.getByRole('button', { name: 'Close city jobs' }).click();
  const audioEvidence = await audio(page);
  await title(page);
  await expect.poll(async () => (await audio(page)).contextState).toBe('suspended');
  expect(await page.evaluate(() => localStorage.getItem('andolan.story.v1'))).toBe(earned);
  expect(await page.evaluate(() => !!localStorage.getItem('andolan.city.v1'))).toBe(true);
  await page.reload(); await ready(page);
  expect(await audio(page)).toMatchObject({ started: false, muted: true, contextState: 'uninitialized' });
  await page.locator('#play-story').click();
  const resumed = await state(page), saved = JSON.parse(earned!);
  expect(resumed.gameplay).toBe('story'); expect(resumed.mission).toEqual(saved.mission);
  expect((await player(page)).x).toBe(saved.players[0].x); expect((await player(page)).z).toBe(saved.players[0].z);
  await expect.poll(async () => (await audio(page)).contextState).toBe('running');
  expect(await audio(page)).toMatchObject({ volume: .1, music: true });
  await testInfo.attach('multiplayer-beta-audio-and-save.json', { body: JSON.stringify({ scope: 'Native WebAudio lifecycle, explicit muted preview and post-master waveform; no subjective listening claim. Story checkpoint earned with normal UI.', audio: audioEvidence, previewRms, audibleRms, attenuatedRms, previewPreservedPreferences: true, preservedStoryStage: resumed.mission.stage }, null, 2), contentType: 'application/json' });
  expect(errors.get(page)).toEqual([]);
});

test('mobile multiplayer entry and city job briefing stay reachable', async ({ browser }, testInfo) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });
  const page = await context.newPage();
  try {
    await load(page); await frames(page);
    for (const id of ['play-private', 'play-online', 'play-practice', 'play-story']) await expect(page.locator(`#${id}`)).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-mobile-title.png') });
    await page.locator('#play-private').click();
    await expect(page.locator('#gameplay')).toHaveValue('freeroam');
    await page.locator('#gameplay').selectOption('story'); await expect(page.locator('#gameplay')).toHaveValue('story');
    await page.locator('#server-input').scrollIntoViewIfNeeded(); await expect(page.locator('#server-input')).toBeInViewport();
    await page.getByRole('button', { name: 'Close lobby' }).click();
    await page.locator('#play-practice').click();
    await page.locator('#jobs-open').click();
    await selectJob(page, 'clinic-restock');
    await page.locator('#job-start').scrollIntoViewIfNeeded(); await expect(page.locator('#job-start')).toBeInViewport();
    await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-mobile-job-board.png') });
    await page.locator('#job-start').click();
    await expect.poll(async () => (await state(page)).contracts.active?.stageId).toBe('load');
    await expect(page.locator('#jobs-dialog')).toBeHidden();
    await expect(page.locator('#world')).toBeFocused();
    await expect(page.locator('#mission-title')).toHaveText('Clinic Restock');
    await frames(page); await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-mobile-objective.png') });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(errors.get(page)).toEqual([]);
  } finally { await context.close(); }
});

test('two real clients deliver a bound van job once, resume identity and share late-join rewards', async ({ browser }, testInfo) => {
  test.setTimeout(480_000);
  const first = await browser.newContext({ viewport: { width: 400, height: 500 } });
  const second = await browser.newContext({ viewport: { width: 400, height: 500 } });
  const host = await first.newPage(), guest = await second.newPage();
  const stages: string[] = [];
  try {
    await load(host); await join(host, 'Beta Driver');
    const room = (await state(host)).room, hostId = await identity(host);
    await load(guest); await join(guest, 'Beta Runner', room);
    const guestId = await identity(guest);
    for (const page of [host, guest]) await expect.poll(async () => (await state(page)).players.filter(p => p.connected).length).toBe(2);
    const baseline = (await state(host)).contracts.progression;
    await chooseJob(host, 'clinic-restock');
    const active = (await state(host)).contracts.active!;
    stages.push(active.stageId);
    await expect.poll(async () => (await state(guest)).contracts.active?.instanceId).toBe(active.instanceId);
    const remote: CommandMessage = { type: 'command', id: 'beta_remote_load', action: 'job_interact', target: active.instanceId, value: 'load' };
    expect(await sendAndObserve(guest, remote)).toMatchObject({ ok: false, code: 'TOO_FAR' });
    expect((await state(host)).contracts.progression).toEqual(baseline);
    expect((await state(host)).contracts.active?.stageId).toBe('load');
    await host.evaluate(() => {
      window.__betaEvents = [];
      for (const type of ['keydown', 'keyup', 'close', 'blur']) document.addEventListener(type, event => {
        window.__betaEvents!.push({ type, code: (event as KeyboardEvent).code, target: (event.target as HTMLElement).id, at: performance.now(), hidden: document.hidden, focused: document.hasFocus() });
      }, true);
    });
    await startIntent(host); await startIntent(guest);
    const van = (await state(host)).vehicles.find(vehicle => vehicle.id === 'van-01')!;
    await Promise.all([walkOpenAvenue(host, van), walkOpenAvenue(guest, van)]);
    await testInfo.attach('van-before-native-entry.json', { body: JSON.stringify(await entryEvidence(host), null, 2), contentType: 'application/json' });
    await host.keyboard.press('KeyF'); await expect.poll(async () => (await player(host)).seat).toBe(0);
    await guest.keyboard.press('KeyF'); await expect.poll(async () => (await player(guest)).seat).toBe(1);
    expect((await player(host)).vehicleId).toBe('van-01'); expect((await player(guest)).vehicleId).toBe('van-01');
    await driveRoute(host, 'van-01', [{ x: 48, z: 0 }, { x: -48, z: 0 }, { x: -48, z: -65 }]);
    expect(distance(await player(host), landmark('mill')!)).toBeLessThan(8);
    await expect(host.locator('#interact-text')).toHaveText('Load the vehicle');
    await host.keyboard.press('KeyE');
    await expect.poll(async () => (await state(host)).contracts.active?.stageId).toBe('drive');
    stages.push('drive');
    const loaded = (await state(host)).contracts.active!;
    expect(loaded).toMatchObject({ cargo: true, vehicleId: 'van-01', participants: [hostId] });
    await expect.poll(async () => (await state(guest)).contracts.active?.stageId).toBe('drive');
    const loadCommand = commands.get(host)!.filter(command => command.action === 'job_interact' && command.value === 'load').at(-1)!;
    expect(await sendAndObserve(host, loadCommand, 2)).toMatchObject({ ok: true, code: 'JOB_STAGE_COMPLETE' });
    expect((await state(host)).contracts.active?.stageId).toBe('drive');
    expect((await state(host)).contracts.progression).toEqual(baseline);

    // Reload the actual participant; sessionStorage keeps its accepted bearer identity.
    await guest.reload(); await ready(guest); await join(guest, 'Beta Runner', room);
    expect(await identity(guest)).toBe(guestId);
    await expect.poll(async () => (await state(guest)).contracts.active?.stageId).toBe('drive');
    expect((await state(guest)).contracts.active).toMatchObject({ instanceId: active.instanceId, cargo: true, vehicleId: 'van-01' });
    await expect(guest.locator('#crew-dialog')).toBeHidden();
    await guest.locator('#crew-open').click();
    await expect(guest.locator('#crew-recap')).toContainText('Clinic Restock');
    await guest.getByRole('button', { name: 'Close crew' }).click();
    expect((await player(guest)).vehicleId).toBeNull();
    await guest.keyboard.press('KeyF'); await expect.poll(async () => (await player(guest)).seat).toBe(1);
    const resumedVan = (await state(guest)).vehicles.find(vehicle => vehicle.id === 'van-01')!;
    expect(resumedVan.occupants.filter(id => id === guestId)).toHaveLength(1);
    await driveRoute(host, 'van-01', [{ x: -48, z: -48 }, { x: 52, z: -48 }]);
    for (const page of [host, guest]) await expect.poll(async () => (await state(page)).contracts.active?.stageId).toBe('unload');
    stages.push('unload');
    await frames(host); await host.screenshot({ path: testInfo.outputPath('multiplayer-beta-van-at-clinic.png') });
    await guest.keyboard.press('KeyF'); await expect.poll(async () => (await player(guest)).vehicleId).toBeNull();
    await expect(guest.locator('#interact-text')).toHaveText('Unload the delivery');
    await guest.keyboard.press('KeyE');
    for (const page of [host, guest]) await expect.poll(async () => (await state(page)).contracts.active).toBeNull();
    const reward = { credits: 100, reputation: 2, project: 1, completed: 1 };
    for (const page of [host, guest]) {
      expect((await state(page)).contracts.progression).toEqual(reward);
      await expect(page.locator('#crew-progress')).toContainText('100 credits');
    }
    const outcome = (await state(host)).contracts.recent[0]!;
    expect(outcome).toMatchObject({ instanceId: active.instanceId, status: 'completed', credits: 100, reputation: 2, project: 1 });
    expect(outcome.participants.sort()).toEqual([hostId, guestId].sort());
    const completedCommand = commands.get(guest)!.filter(command => command.action === 'job_interact' && command.value === 'unload').at(-1)!;
    expect(await sendAndObserve(guest, completedCommand, 2)).toMatchObject({ ok: true, code: 'JOB_COMPLETE' });
    expect(await sendAndObserve(guest, { ...completedCommand, id: 'beta_stale_unload' })).toMatchObject({ ok: false, code: 'NO_ACTIVE_JOB' });
    expect((await state(guest)).contracts.progression).toEqual(reward);
    expect((await state(guest)).contracts.recent.filter(item => item.instanceId === active.instanceId)).toHaveLength(1);
    await frames(host); await host.screenshot({ path: testInfo.outputPath('multiplayer-beta-shared-completion.png') });
    expect(errors.get(guest)).toEqual([]);
    await second.close();
    const lateContext = await browser.newContext({ viewport: { width: 400, height: 500 } });
    try {
      const late = await lateContext.newPage(); await load(late); await join(late, 'Beta Late Join', room);
      await expect(late.locator('#crew-dialog')).toBeHidden();
      await late.locator('#crew-open').click();
      await expect(late.locator('#crew-recap')).toContainText('100 shared credits');
      await expect(late.locator('#crew-recap')).toContainText('Clinic Restock · completed');
      expect((await state(late)).contracts.progression).toEqual(reward);
      expect((await state(late)).contracts.recent).toEqual((await state(host)).contracts.recent);
      await late.screenshot({ path: testInfo.outputPath('multiplayer-beta-late-join.png') });
      expect(errors.get(late)).toEqual([]);
    } finally { await lateContext.close(); }
    await testInfo.attach('multiplayer-beta-real-job.json', { body: JSON.stringify({ scope: 'Real independent browser contexts and WebSockets; physical walking/driving; no state fixtures, teleportation or clock changes.', stages, baseline, finalProgression: reward, outcome, resumedIdentity: true, duplicateAcceptedCommandDidNotRepay: true, remoteCommandRejected: true }, null, 2), contentType: 'application/json' });
    expect(errors.get(host)).toEqual([]);
  } catch (error) {
    const summary: Record<string, unknown> = {};
    for (const [name, page] of [['host', host], ['guest', guest]] as const) {
      const evidence = await entryEvidence(page).catch(() => null);
      await testInfo.attach(`van-${name}-failure.json`, { body: JSON.stringify(evidence, null, 2), contentType: 'application/json' });
      summary[name] = evidence && { tick: evidence.tick, time: evidence.time, seq: evidence.person.lastInputSeq, position: { x: evidence.person.x, z: evidence.person.z }, seat: evidence.person.seat, distance: evidence.distance, browser: evidence.browser, commands: evidence.commands?.slice(-4), results: evidence.results?.slice(-4) };
    }
    // GitHub annotations remain readable even if artifact downloads are blocked.
    throw new Error(`${error instanceof Error ? error.message : String(error)}\nVan diagnostic: ${JSON.stringify(summary)}`, { cause: error });
  } finally { await first.close(); await second.close(); }
});

test('mobile remapping preserves touch movement and full braking; larger dialogue survives reload', async ({ browser }, testInfo) => {
  test.setTimeout(150_000);
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const session = await context.newCDPSession(page);
  const touchStart = async (selector: string) => {
    const button = page.locator(selector); await expect(button).toBeInViewport();
    const box = (await button.boundingBox())!;
    await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: box.x + box.width / 2, y: box.y + box.height / 2, id: 1 }] });
  };
  const touchEnd = (cancel = false) => session.send('Input.dispatchTouchEvent', { type: cancel ? 'touchCancel' : 'touchEnd', touchPoints: [] });
  const speed = async () => (await state(page)).vehicles.find(vehicle => vehicle.id === 'compact-01')!.speed;
  try {
    await load(page); await page.locator('#play-story').click(); await page.locator('#interact').click();
    const initialFont = await page.locator('.dialogue-line p').first().evaluate(node => parseFloat(getComputedStyle(node).fontSize));
    await page.getByRole('button', { name: 'Close conversation' }).click();
    await page.keyboard.press('Escape'); await page.locator('#large-text').check(); await page.locator('#assist').check();
    await page.getByText('Rebind keyboard controls', { exact: true }).click();
    await page.locator('[data-binding="forward"]').click(); await page.keyboard.press('KeyI');
    await expect(page.locator('[data-binding="forward"]')).toHaveText('I');
    await page.locator('[data-binding="forward"]').click(); await page.keyboard.press('KeyS');
    await expect(page.locator('#binding-status')).toContainText('already controls');
    await page.keyboard.press('KeyJ'); await expect(page.locator('#binding-status')).toContainText('reserved');
    await page.keyboard.press('Space'); await expect(page.locator('#binding-status')).toContainText('reserved');
    await page.keyboard.press('Escape');
    await expect(page.locator('#settings-dialog')).toBeVisible();
    await expect(page.locator('[data-binding="forward"]')).toHaveText('I');
    await expect(page.locator('#binding-status')).toHaveText('Key change cancelled.');
    await page.locator('[data-binding="back"]').click();
    await page.getByRole('button', { name: 'Close settings' }).click();
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-binding="back"]')).toHaveText('S');
    await expect(page.locator('#binding-status')).toHaveText('Key change cancelled.');
    await page.locator('#return-title').click(); await page.reload(); await ready(page);
    await page.locator('#play-practice').click(); await page.locator('#touch-vehicle').click();
    await expect.poll(async () => (await player(page)).vehicleId).toBe('compact-01');
    await expect(page.locator('#world')).toBeFocused();
    const carHeading = (await state(page)).vehicles.find(vehicle => vehicle.id === 'compact-01')!.heading;
    await expect.poll(async () => {
      const yaw = await page.evaluate(() => window.__ANDOLAN.metrics().cameraYaw);
      return Math.abs(Math.atan2(Math.sin(yaw - carHeading), Math.cos(yaw - carHeading)));
    }).toBeLessThan(.2);
    await page.keyboard.down('KeyW'); await page.waitForTimeout(500); await page.keyboard.up('KeyW');
    expect(await speed()).toBe(0);
    await page.keyboard.down('KeyI');
    try { await expect.poll(speed).toBeGreaterThan(3); }
    finally { await page.keyboard.up('KeyI'); }
    await page.keyboard.down('Space');
    try {
      await expect.poll(speed).toBe(0); await page.waitForTimeout(400); expect(await speed()).toBe(0);
    } finally { await page.keyboard.up('Space'); }
    await touchStart('[data-touch-action="forward"]');
    try { await expect.poll(speed).toBeGreaterThan(3); }
    finally { await touchEnd(true); }
    await touchStart('[data-touch-action="brake"]');
    try {
      await expect.poll(speed).toBe(0); await page.waitForTimeout(400); expect(await speed()).toBe(0);
    } finally { await touchEnd(); }
    // A cancelled touch must not resume acceleration when the separate brake is released.
    await page.waitForTimeout(400); expect(await speed()).toBe(0);
    // Press immediately after close: a queued dialog close event must not erase
    // a new movement key. No frame barrier or repeat keydown masks that race.
    await page.keyboard.press('Escape'); await expect(page.locator('#settings-dialog')).toBeVisible();
    await page.getByRole('button', { name: 'Close settings' }).click();
    await page.keyboard.down('KeyI');
    try { await expect.poll(speed).toBeGreaterThan(2); }
    finally { await page.keyboard.up('KeyI'); }
    await page.keyboard.down('Space');
    try { await expect.poll(speed).toBe(0); }
    finally { await page.keyboard.up('Space'); }
    await page.locator('#touch-camera').click();
    const clearance = await page.evaluate(() => ({
      speedBottom: document.querySelector('#driving')!.getBoundingClientRect().bottom,
      actionTop: Math.min(document.querySelector('#touch-vehicle')!.getBoundingClientRect().top, document.querySelector('[data-touch-action="brake"]')!.getBoundingClientRect().top),
    }));
    expect(clearance.speedBottom).toBeLessThanOrEqual(clearance.actionTop);
    await frames(page); await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-mobile-controls.png') });
    await title(page); await page.reload(); await ready(page); await page.locator('#play-story').click();
    await page.locator('#interact').click();
    const restoredFont = await page.locator('.dialogue-line p').first().evaluate(node => parseFloat(getComputedStyle(node).fontSize));
    expect(restoredFont).toBeCloseTo(initialFont * 1.15, 1);
    await expect(page.locator('#dialog-continue')).toBeInViewport();
    await page.screenshot({ path: testInfo.outputPath('multiplayer-beta-large-dialogue.png') });
    await page.getByRole('button', { name: 'Close conversation' }).click(); await page.keyboard.press('Escape');
    await expect(page.locator('#large-text')).toBeChecked(); await expect(page.locator('#assist')).toBeChecked();
    await page.getByText('Rebind keyboard controls', { exact: true }).click();
    await expect(page.locator('[data-binding="forward"]')).toHaveText('I');
    await page.locator('#bindings-reset').click(); await expect(page.locator('[data-binding="forward"]')).toHaveText('W');
    await testInfo.attach('multiplayer-beta-controls.json', { body: JSON.stringify({ scope: 'Native keyboard and CDP touch input; no input/state hooks. Assisted driving retains sign-preserving full braking.', rejected: ['duplicate S', 'reserved J', 'reserved Space'], captureCancelledBy: ['Escape', 'closing settings'], touchSurvivesRemap: true, stationaryEntryCameraAligned: true, keyboardAndTouchBrakeRestedAtZero: true, initialFont, restoredFont }, null, 2), contentType: 'application/json' });
    expect(errors.get(page)).toEqual([]);
  } finally { await context.close(); }
});

test('two real clients publish the media correction through five physical job stages', async ({ browser }, testInfo) => {
  test.setTimeout(420_000);
  const first = await browser.newContext({ viewport: { width: 400, height: 500 } });
  const second = await browser.newContext({ viewport: { width: 400, height: 500 } });
  const host = await first.newPage(), guest = await second.newPage();
  const visited: string[] = [];
  try {
    await load(host); await join(host, 'Correction Driver');
    const room = (await state(host)).room;
    await load(guest); await join(guest, 'Correction Runner', room);
    await expect.poll(async () => (await state(host)).players.filter(person => person.connected).length).toBe(2);
    await chooseJob(host, 'media-correction');
    await expect(guest.locator('#jobs-dialog')).toBeHidden();
    const instanceId = (await state(host)).contracts.active!.instanceId;
    const stage = async (expected: string) => {
      for (const page of [host, guest]) await expect.poll(async () => (await state(page)).contracts.active?.stageId).toBe(expected);
      visited.push(expected);
    };
    await stage('brief'); await startIntent(host); await startIntent(guest);
    await walkOpenAvenue(host, landmark('board')!, 2.5); await host.keyboard.press('KeyE');
    await stage('archive-load');
    const compact = (await state(host)).vehicles.find(vehicle => vehicle.id === 'compact-01')!;
    await Promise.all([walkOpenAvenue(host, compact, 3), walkOpenAvenue(guest, compact, 3)]);
    await host.keyboard.press('KeyF'); await expect.poll(async () => (await player(host)).seat).toBe(0);
    await guest.keyboard.press('KeyF'); await expect.poll(async () => (await player(guest)).seat).toBe(1);
    await driveRoute(host, 'compact-01', [{ x: 48, z: 48 }, { x: 48, z: -64 }]);
    expect(distance(await player(host), landmark('archive')!)).toBeLessThan(8);
    await host.keyboard.press('KeyE'); await stage('clinic-check');
    expect((await state(host)).contracts.active).toMatchObject({ cargo: true, vehicleId: 'compact-01' });
    await driveRoute(host, 'compact-01', [{ x: 48, z: -48 }, { x: 52, z: -48 }]);
    await guest.keyboard.press('KeyF'); await expect.poll(async () => (await player(guest)).vehicleId).toBeNull();
    await frames(guest); await guest.screenshot({ path: testInfo.outputPath('multiplayer-beta-nearby-walk-objective.png') });
    await guest.keyboard.press('KeyE'); await stage('clinic-load');
    expect((await state(host)).contracts.active?.cargo).toBe(false);
    await host.keyboard.press('KeyE'); await stage('broadcast');
    expect((await state(host)).contracts.active).toMatchObject({ cargo: true, vehicleId: 'compact-01' });
    await guest.keyboard.press('KeyF'); await expect.poll(async () => (await player(guest)).seat).toBe(1);
    await driveRoute(host, 'compact-01', [{ x: 48, z: 0 }, { x: 64, z: 0 }]);
    await guest.keyboard.press('KeyF'); await expect.poll(async () => (await player(guest)).vehicleId).toBeNull();
    await guest.keyboard.press('KeyE');
    for (const page of [host, guest]) {
      await expect.poll(async () => (await state(page)).contracts.active).toBeNull();
      expect((await state(page)).contracts.progression).toEqual({ credits: 120, reputation: 2, project: 1, completed: 1 });
      expect((await state(page)).city.completedJobs).toEqual(['media-correction']);
      await expect(page.locator('#jobs-dialog')).toBeHidden();
    }
    const completion = commands.get(guest)!.filter(message => message.action === 'job_interact' && message.value === 'broadcast').at(-1)!;
    expect(await sendAndObserve(guest, completion, 2)).toMatchObject({ ok: true, code: 'JOB_COMPLETE' });
    expect((await state(guest)).contracts.progression.credits).toBe(120);
    await host.locator('#jobs-open').click();
    await selectJob(host, 'sector-energy'); await expect(host.locator('#job-start')).toBeEnabled();
    await host.locator('#city-tab-ledger').click();
    await expect(host.locator('[data-media-id="correction-corner"]')).toBeVisible();
    await expect(host.locator('#city-mandate-status')).toContainText('1/5 complete');
    await expect(host.locator('#city-route-capture')).toHaveCount(0);
    await host.locator('#city-receipts-toggle').click();
    await expect(host.locator('[data-receipt^="media-correction:"]')).toHaveCount(5);
    await frames(host); await host.screenshot({ path: testInfo.outputPath('multiplayer-beta-earned-media-ledger.png') });
    const final = await state(host);
    await testInfo.attach('multiplayer-beta-media-route.json', { body: JSON.stringify({ scope: 'Two real browser contexts and WebSockets; five stages earned by ordinary input, physical walking/driving and UI interactions. Sector completion and final mandate were not earned in this route.', instanceId, visited, progression: final.contracts.progression, city: final.city, outcome: final.contracts.recent[0], duplicateCompletionDidNotRepay: true, earnedReceiptCount: 5 }, null, 2), contentType: 'application/json' });
    expect(errors.get(host)).toEqual([]); expect(errors.get(guest)).toEqual([]);
  } catch (error) {
    for (const [name, page] of [['driver', host], ['runner', guest]] as const) await testInfo.attach(`media-${name}-failure.json`, { body: JSON.stringify(await state(page).catch(() => null)), contentType: 'application/json' });
    throw error;
  } finally { await first.close(); await second.close(); }
});

// Deliberately authored completed-case checkpoint. This exercises final-choice
// presentation and local persistence; it is not evidence of driving sector jobs.
function mandateCheckpoint() {
  const sim = new Simulation('CITY-PRACTICE', 'private', undefined, 'freeroam');
  const id = 'solo-player'; sim.addPlayer(id, 'Mandate Fixture');
  let serial = 0;
  const command = (action: CommandMessage['action'], target?: string, value?: string) => sim.command(id, { type: 'command', id: `mandate-fixture-${++serial}`, action, target, value });
  for (const job of CONTRACTS.filter(definition => definition.once)) {
    expect(command('job_start', job.id).ok).toBe(true);
    for (const stage of job.stages) {
      const active = sim.contracts.active!, person = sim.players.get(id)!;
      if (person.vehicleId) { sim.vehicles.get(person.vehicleId)!.speed = 0; expect(command('exit').ok).toBe(true); }
      const target = landmark(stage.targetId!)!; person.x = target.x; person.z = target.z;
      const vehicle = sim.vehicles.get(active.vehicleId ?? (stage.vehicle === 'van' ? 'van-01' : 'compact-01'))!;
      vehicle.x = target.x; vehicle.z = target.z; vehicle.speed = 0;
      if (stage.vehicle !== 'none') expect(command('enter', vehicle.id).ok).toBe(true);
      expect(command('job_interact', active.instanceId, active.stageId).ok).toBe(true);
    }
  }
  const person = sim.players.get(id)!, hall = landmark('civic')!;
  person.x = hall.x; person.z = hall.z;
  return sim.serialize();
}

test('both mandate outcomes disclose consequences and persist (labelled completed-case fixtures)', async ({ browser }, testInfo) => {
  test.setTimeout(120_000);
  const evidence: unknown[] = [];
  for (const route of ['reform', 'capture'] as const) {
    const context = await browser.newContext({ viewport: { width: 640, height: 600 } });
    try {
      const page = await context.newPage(), checkpoint = mandateCheckpoint();
      await page.addInitScript(saved => { if (!localStorage.getItem('andolan.city.v1')) localStorage.setItem('andolan.city.v1', JSON.stringify(saved)); }, checkpoint);
      await load(page); await page.locator('#play-practice').click();
      expect((await state(page)).city.completedJobs).toHaveLength(5);
      await page.locator('#jobs-open').click(); await page.locator('#city-tab-ledger').click();
      await expect(page.locator('#city-mandate-status')).toContainText('Ready to vote at Public Hearing');
      await expect(page.locator('#city-route-reform')).toContainText('+1 project point');
      await expect(page.locator('#city-route-capture')).toContainText('25% more crew credits');
      await expect(page.locator('#city-route-capture')).toContainText('zero project points');
      await page.locator(`#city-route-${route}`).click();
      await expect.poll(async () => (await state(page)).city.decision?.route).toBe(route);
      await expect(page.locator('#city-mandate-heading')).toHaveText(CITY_OUTCOMES[route].title);
      await expect(page.locator('#city-route-reform')).toHaveCount(0);
      await page.locator('#city-mandate-heading').scrollIntoViewIfNeeded();
      await frames(page); await page.screenshot({ path: testInfo.outputPath(`multiplayer-beta-${route}-fixture.png`) });
      await page.getByRole('button', { name: 'Close city jobs' }).click(); await title(page);
      await page.reload(); await ready(page); await page.locator('#play-practice').click();
      const resumed = await state(page);
      expect(resumed.city.decision?.route).toBe(route); expect(resumed.city.outcome).toEqual(CITY_OUTCOMES[route]);
      evidence.push({ route, outcome: resumed.city.outcome, persisted: true }); expect(errors.get(page)).toEqual([]);
    } finally { await context.close(); }
  }
  await testInfo.attach('multiplayer-beta-mandate-fixtures.json', { body: JSON.stringify({ scope: 'Explicit synthetic completed-case local checkpoints; final choice is made with the real UI and persisted by the real solo simulation. No claim of physical sector traversal or real multiplayer transport.', outcomes: evidence }, null, 2), contentType: 'application/json' });
});
