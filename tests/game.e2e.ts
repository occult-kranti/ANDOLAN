import { test, expect, type Page, type Browser } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { Simulation } from '../packages/sim/src/index';
import { WORLD, isBlocked, landmark } from '../packages/sim/src/world';
import type { CommandAction, CommandMessage, InputMessage, Snapshot } from '../packages/protocol/src/index';
import type { GameAudio } from '../apps/client/src/audio';

type Intent = Omit<InputMessage, 'type' | 'seq'>;
interface DevHooks {
  snapshot(): Snapshot;
  playerId(): string;
  metrics(): { frameTimes: number[]; quality: string; cameraYaw: number };
  command(action: CommandAction, target?: string, value?: string): void;
  connection(): { input(message: InputMessage): void; command(message: CommandMessage): void };
  audio(): GameAudio['diagnostics'];
}
declare global {
  interface Window {
    __ANDOLAN: DevHooks;
    __qaIntent?: { axes: Intent; sequence: number; timer: number };
    __qaFrameSchedulerInstalled?: boolean;
  }
}
const rest: Intent = { moveX: 0, moveZ: 0, forward: 0, turn: 0, sprint: false };
const errors = new WeakMap<Page, string[]>();

async function load(page: Page) {
  const collected: string[] = []; errors.set(page, collected);
  page.on('pageerror', error => collected.push(error.message));
  if (process.env.CI || process.env.ANDOLAN_SOFTWARE_RENDERING === '1') {
    await page.addInitScript(() => {
      if (window.__qaFrameSchedulerInstalled) return;
      window.__qaFrameSchedulerInstalled = true;
      const nativeRequest = window.requestAnimationFrame.bind(window);
      const queued = new Map<number, FrameRequestCallback>();
      let nextHandle = 1;
      let timer: number | undefined;
      let nativeQueued = false;
      let dispatching = false;
      let finishedAt = performance.now() - 100;
      const schedule = () => {
        if (!queued.size || timer !== undefined || nativeQueued || dispatching) return;
        // Leave a 100 ms graphics cooldown even when one software frame is slow.
        // Input, networking and the original simulation timers remain untouched.
        timer = window.setTimeout(() => {
          timer = undefined;
          nativeQueued = true;
          nativeRequest(timestamp => {
            nativeQueued = false;
            dispatching = true;
            const batch = [...queued.keys()];
            for (const handle of batch) {
              const callback = queued.get(handle);
              queued.delete(handle);
              if (callback) {
                try { callback(timestamp); }
                catch (error) { window.setTimeout(() => { throw error; }, 0); }
              }
            }
            dispatching = false;
            finishedAt = performance.now();
            schedule();
          });
        }, Math.max(0, 100 - (performance.now() - finishedAt)));
      };
      window.requestAnimationFrame = callback => {
        const handle = nextHandle++;
        queued.set(handle, callback);
        schedule();
        return handle;
      };
      window.cancelAnimationFrame = handle => { queued.delete(handle); };
    });
  }
  await page.addInitScript(() => { if (!localStorage.getItem('andolan.settings')) localStorage.setItem('andolan.settings', JSON.stringify({ quality: 'low' })); });
  await page.goto('/');
  await page.waitForFunction(() => !!window.__ANDOLAN, undefined, { timeout: 90_000 });
  await expect(page.locator('#loading')).toBeHidden();
}
async function state(page: Page) {
  return page.evaluate(() => ({ snapshot: window.__ANDOLAN.snapshot(), id: window.__ANDOLAN.playerId() }));
}
async function me(page: Page) {
  const { snapshot, id } = await state(page);
  return snapshot.players.find(player => player.id === id)!;
}
async function stage(page: Page, expected: string) {
  await expect.poll(async () => (await state(page)).snapshot.mission.stage).toBe(expected);
}
async function pressFor(page: Page, key: string, milliseconds: number) {
  await page.keyboard.down(key);
  await page.waitForTimeout(milliseconds);
  await page.keyboard.up(key);
}
async function moveWithKey(page: Page, key: string, meters: number) {
  const before = await me(page);
  await page.keyboard.down(key);
  try {
    await expect.poll(async () => {
      const current = await me(page);
      return Math.hypot(current.x - before.x, current.z - before.z);
    }, { timeout: 30_000, intervals: [150] }).toBeGreaterThan(meters);
  } finally { await page.keyboard.up(key); }
  await expect.poll(async () => {
    const first = await me(page);
    await page.waitForTimeout(250);
    const second = await me(page);
    return Math.hypot(second.x - first.x, second.z - first.z);
  }, { timeout: 15_000 }).toBeLessThan(.001);
}
async function renderedFrames(page: Page) {
  await page.evaluate(() => new Promise<void>(resolve => {
    let frames = 0;
    const wait = () => { if (++frames >= 4) resolve(); else requestAnimationFrame(wait); };
    requestAnimationFrame(wait);
  }));
}
async function conversation(page: Page, choice?: string) {
  await expect(page.locator('#interact')).toBeVisible();
  await page.locator('#interact').click();
  await expect(page.locator('#mission-dialog')).toBeVisible();
  await expect(page.locator('#dialogue-lines')).not.toBeEmpty();
  const documents = (await state(page)).snapshot.mission.documents ?? [];
  if (documents.length) {
    await expect(page.locator('#dialogue-lines .paper')).toHaveCount(documents.length);
    for (const paper of await page.locator('#dialogue-lines .paper').all()) await expect(paper).toContainText('Source:');
  }
  if (choice) {
    const button = page.locator(`[data-choice="${choice}"]`);
    await expect(button).toBeVisible();
    await expect(button.locator('strong')).not.toBeEmpty();
    await button.click();
  }
  else await page.locator('#dialog-continue').click();
  await expect(page.locator('#mission-dialog')).toBeHidden();
}
async function confirmReplay(page: Page) {
  const confirmation = page.waitForEvent('dialog');
  const click = page.locator('#replay').click();
  const dialog = await confirmation;
  expect(dialog.type()).toBe('confirm');
  expect(dialog.message()).toContain('Start a new story?');
  await dialog.accept();
  await click;
}

/** Presentation fixture only. This does not establish that gameplay can complete. */
function completedSimulation(room: string, playerId: string) {
  const initial = new Simulation(room, 'private');
  initial.addPlayer(playerId, 'QA Completed');
  const checkpoint = initial.serialize();
  Object.assign(checkpoint.mission, {
    chapterIndex: 6, stageIndex: 0, complete: true,
    metrics: { trust: 90, care: 90, accountability: 90 },
    history: [{ chapterId: 'last-delivery', stageId: 'receipt', choiceId: 'copy', label: 'Request an authorized copy' }],
  });
  const complete = new Simulation(room, 'private', checkpoint);
  complete.connectPlayer(playerId);
  return complete;
}

test('Story keyboard controls, dialogue, vehicle, checkpoint and settings', async ({ page }, testInfo) => {
  await load(page);
  await page.screenshot({ path: testInfo.outputPath('desktop-title.png') });
  await page.locator('#play-story').click();
  await stage(page, 'keys');
  await renderedFrames(page);
  await page.screenshot({ path: testInfo.outputPath('desktop-garage.png') });
  await page.keyboard.press('KeyE');
  await expect(page.locator('#mission-dialog')).toBeVisible();
  await expect(page.locator('#dialogue-lines')).toContainText('Yusuf');
  await page.locator('#dialog-continue').click();
  await stage(page, 'car');
  await page.keyboard.press('KeyF');
  await stage(page, 'clinic-drive');
  await expect.poll(async () => (await me(page)).seat).toBe(0);
  const before = await me(page);
  await moveWithKey(page, 'KeyW', 5);
  await expect.poll(async () => Math.hypot((await me(page)).x - before.x, (await me(page)).z - before.z)).toBeGreaterThan(5);
  await expect.poll(async () => Math.abs((await state(page)).snapshot.vehicles[0]!.speed)).toBeLessThan(1);
  await page.keyboard.press('Escape');
  await page.locator('#comfort').check();
  await page.getByRole('button', { name: 'Close settings' }).click();
  const beforeReverse = await me(page);
  const yawBefore = await page.evaluate(() => window.__ANDOLAN.metrics().cameraYaw);
  await moveWithKey(page, 'KeyS', 2);
  const afterReverse = await me(page);
  const yawAfter = await page.evaluate(() => window.__ANDOLAN.metrics().cameraYaw);
  const angleGap = (a: number, b: number) => Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b)));
  expect((afterReverse.x - beforeReverse.x) * Math.sin(beforeReverse.heading) + (afterReverse.z - beforeReverse.z) * Math.cos(beforeReverse.heading)).toBeLessThan(-1);
  expect(angleGap(yawAfter, afterReverse.heading)).toBeLessThanOrEqual(angleGap(yawBefore, beforeReverse.heading) + .05);
  await testInfo.attach('reverse-camera.json', { body: JSON.stringify({ comfort: true, beforeReverse, afterReverse, yawBefore, yawAfter }), contentType: 'application/json' });
  await page.keyboard.press('KeyF');
  await expect.poll(async () => (await me(page)).vehicleId).toBeNull();
  const parked = await me(page);
  await moveWithKey(page, 'ArrowUp', 1.2);
  const walked = await me(page);
  expect(Math.hypot(walked.x - parked.x, walked.z - parked.z)).toBeGreaterThan(1);
  await page.keyboard.press('KeyJ');
  await expect(page.locator('#journal-dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Close journal' }).click();
  await page.keyboard.press('Escape');
  await expect(page.locator('#settings-dialog')).toBeVisible();
  await page.locator('#comfort').check();
  await page.locator('#large-text').check();
  await page.locator('#assist').check();
  const paused = await me(page);
  await pressFor(page, 'KeyW', 400);
  expect((await me(page)).x).toBeCloseTo(paused.x, 3);
  expect((await me(page)).z).toBeCloseTo(paused.z, 3);
  await page.locator('#return-title').click();
  await expect(page.locator('#story-label')).toHaveText('Continue story');
  await page.reload();
  await page.waitForFunction(() => !!window.__ANDOLAN);
  await page.locator('#play-story').click();
  await stage(page, 'clinic-drive');
  expect((await me(page)).x).toBeCloseTo(paused.x, 2);
  expect((await me(page)).z).toBeCloseTo(paused.z, 2);
  await page.keyboard.press('Escape');
  await expect(page.locator('#comfort')).toBeChecked();
  await expect(page.locator('#large-text')).toBeChecked();
  await expect(page.locator('#assist')).toBeChecked();
  await page.getByRole('button', { name: 'Close settings' }).click();
  await page.screenshot({ path: testInfo.outputPath('story-driving-checkpoint.png') });
  expect(errors.get(page)).toEqual([]);
});

async function joinedCrew(browser: Browser) {
  // Fixed narrow canvases avoid starving browser input timers on software GPUs.
  const first = await browser.newContext({ viewport: { width: 400, height: 500 } });
  const second = await browser.newContext({ viewport: { width: 400, height: 500 } });
  const host = await first.newPage(); const guest = await second.newPage();
  await load(host); await host.locator('#play-private').click();
  await host.locator('#gameplay').selectOption('story');
  await host.locator('#player-name').fill('QA Host');
  await host.getByRole('button', { name: 'Join the city' }).click();
  await expect.poll(async () => (await state(host)).snapshot.room).not.toBe('PREVIEW');
  const room = (await state(host)).snapshot.room;
  await load(guest); await guest.locator('#play-private').click();
  await guest.locator('#gameplay').selectOption('story');
  await guest.locator('#player-name').fill('QA Guest');
  await guest.locator('#room-input').fill(room);
  await guest.getByRole('button', { name: 'Join the city' }).click();
  for (const page of [host, guest]) {
    await expect.poll(async () => (await state(page)).snapshot.room).toBe(room);
    await expect.poll(async () => (await state(page)).snapshot.players.filter(p => p.connected).length).toBe(2);
    await expect(page.locator('#crew-count')).toHaveText('2 players in this room');
  }
  return { first, second, host, guest, room };
}

test('two independent browsers share movement, seats and driver handover', async ({ browser }, testInfo) => {
  test.setTimeout(150_000);
  const { first, second, host, guest } = await joinedCrew(browser);
  try {
    const hostId = (await state(host)).id;
    await host.bringToFront();
    await conversation(host); await stage(host, 'car');
    const before = await me(host);
    await moveWithKey(host, 'KeyW', 1.3);
    const after = await me(host);
    expect(Math.hypot(after.x - before.x, after.z - before.z)).toBeGreaterThan(1);
    await expect.poll(async () => (await state(guest)).snapshot.players.find(p => p.id === hostId)!.x).toBeCloseTo(after.x, 1);
    await expect.poll(async () => (await state(guest)).snapshot.players.find(p => p.id === hostId)!.z).toBeCloseTo(after.z, 1);
    await moveWithKey(host, 'KeyS', Math.hypot(after.x - before.x, after.z - before.z) - .3);
    await host.keyboard.press('KeyF');
    await expect.poll(async () => (await me(host)).seat).toBe(0);
    await guest.bringToFront(); await guest.keyboard.press('KeyF');
    await expect.poll(async () => (await me(guest)).seat).toBe(1);
    await expect.poll(async () => (await state(host)).snapshot.vehicles[0]!.occupants.filter(Boolean).length).toBe(2);
    const beforePassenger = (await state(guest)).snapshot.vehicles[0]!;
    await pressFor(guest, 'KeyW', 600);
    const afterPassenger = (await state(guest)).snapshot.vehicles[0]!;
    expect(afterPassenger.x).toBeCloseTo(beforePassenger.x, 3);
    expect(afterPassenger.z).toBeCloseTo(beforePassenger.z, 3);
    await guest.screenshot({ path: testInfo.outputPath('private-crew-seats.png') });
    await host.bringToFront(); await host.keyboard.press('KeyF');
    await expect.poll(async () => (await me(host)).vehicleId).toBeNull();
    await guest.bringToFront();
    await expect(guest.locator('#interact-text')).toHaveText('Take the wheel');
    await guest.keyboard.press('KeyE');
    await expect.poll(async () => (await me(guest)).seat).toBe(0);
    await guest.keyboard.press('KeyF');
    await expect.poll(async () => (await me(guest)).vehicleId).toBeNull();
    await expect.poll(async () => (await state(host)).snapshot.vehicles[0]!.occupants.filter(Boolean).length).toBe(0);
    expect(errors.get(host)).toEqual([]); expect(errors.get(guest)).toEqual([]);
  } finally { await first.close(); await second.close(); }
});

test('real crew walking, split votes, agreement and late-join recap', async ({ browser }, testInfo) => {
  test.setTimeout(360_000);
  const { first, second, host, guest, room } = await joinedCrew(browser);
  try {
    await host.bringToFront(); await conversation(host); await stage(host, 'car');
    await host.keyboard.press('KeyF'); await stage(host, 'clinic-drive');
    await host.keyboard.press('KeyF');
    await expect.poll(async () => (await me(host)).vehicleId).toBeNull();
    await startIntent(host); await startIntent(guest);
    // Arrival is reachable on foot after collecting the car. Both players physically
    // traverse the collision map; no checkpoints or mission edits enter this test.
    await Promise.all([
      walkTo(host, { x: 49, z: -48 }, 2),
      walkTo(guest, { x: 52, z: -46 }, 2),
    ]);
    await stage(host, 'receipt'); await stage(guest, 'receipt');
    await host.bringToFront(); await host.keyboard.press('KeyE');
    await expect(host.locator('#vote-note')).toContainText('2 matching votes needed');
    await host.locator('[data-choice="copy"]').click();
    await expect(host.locator('[data-choice="copy"]')).toHaveAttribute('aria-pressed', 'true');
    await expect(host.locator('[data-choice="copy"]')).toContainText('1 vote');
    await expect(guest.locator('#vote-status')).toContainText('Press E or use Interact to vote.');
    await expect(guest.locator('#vote-status')).not.toContainText('exit');
    await guest.bringToFront(); await guest.keyboard.press('KeyE');
    await guest.locator('[data-choice="ask"]').click();
    await stage(guest, 'receipt');
    await expect(guest.locator('[data-choice="ask"]')).toContainText('1 vote');
    await expect(guest.locator('[data-choice="copy"]')).toContainText('1 vote');
    await guest.screenshot({ path: testInfo.outputPath('private-crew-vote-tie.png') });
    await guest.getByRole('button', { name: 'Close conversation' }).click();
    await expect(guest.locator('#vote-status')).toBeVisible();
    await expect(guest.locator('#vote-status')).toContainText('2/2 voted');
    await expect(guest.locator('#vote-status')).toContainText('2 matching needed');
    await guest.keyboard.press('KeyE');
    await guest.locator('[data-choice="copy"]').click();
    await stage(host, 'river-return'); await stage(guest, 'river-return');
    await expect(guest.locator('#vote-status')).toBeHidden();
    expect((await state(host)).snapshot.mission.history).toHaveLength(1);
    await guest.screenshot({ path: testInfo.outputPath('private-crew.png') });
    expect(errors.get(host)).toEqual([]); expect(errors.get(guest)).toEqual([]);
    await second.close();
    const lateContext = await browser.newContext({ viewport: { width: 400, height: 500 } });
    const late = await lateContext.newPage();
    try {
      await load(late); await late.locator('#play-private').click();
      await late.locator('#gameplay').selectOption('story');
      await late.locator('#player-name').fill('QA Late Arrival'); await late.locator('#room-input').fill(room);
      await late.getByRole('button', { name: 'Join the city' }).click();
      await expect(late.locator('#crew-dialog')).toBeVisible();
      await expect(late.locator('#crew-recap .recap-line')).toHaveCount(1);
      const lateState = (await state(late)).snapshot;
      expect(lateState.mission.stage).toBe('river-return');
      await expect(late.locator('#crew-recap')).toContainText(lateState.mission.objective);
      await expect(late.locator('#crew-list')).toContainText('QA Late Arrival (you) · here · on foot');
      expect(lateState.mission.history[0]!.choiceId).toBe('copy');
      await late.screenshot({ path: testInfo.outputPath('late-join-recap.png') });
      await late.getByRole('button', { name: 'Close crew' }).click();
      await renderedFrames(late);
      await expect(late.locator('#crew-dialog')).toBeHidden();
      expect(errors.get(late)).toEqual([]);
    } finally { await lateContext.close(); }
  } catch (error) {
    for (const [name, page] of [['host', host], ['guest', guest]] as const) {
      await testInfo.attach(`${name}-failure-state.json`, { body: JSON.stringify(await state(page).catch(() => null)), contentType: 'application/json' });
    }
    throw error;
  } finally { await first.close(); await second.close(); }
});

test('mobile title, garage and dialogue layout remain usable', async ({ browser }, testInfo) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });
  const page = await context.newPage();
  try {
    await load(page);
    await expect(page.locator('#play-story')).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath('mobile-title.png') });
    await page.locator('#play-story').click(); await stage(page, 'keys');
    await renderedFrames(page);
    await expect(page.locator('#interact')).toBeInViewport();
    await page.screenshot({ path: testInfo.outputPath('mobile-garage.png') });
    await page.locator('#interact').click();
    await expect(page.locator('#mission-dialog')).toBeVisible();
    await expect(page.locator('#dialog-continue')).toBeInViewport();
    await page.locator('#dialog-continue').click(); await stage(page, 'car');
    expect(errors.get(page)).toEqual([]);
  } finally { await context.close(); }
});

test('completed-room welcome preserves the ending (presentation fixture)', async ({ page }, testInfo) => {
  const fixture = completedSimulation('QA-END', 'fixture-player').snapshot();
  await page.routeWebSocket('**/ws', route => {
    route.onMessage(raw => {
      const message = JSON.parse(String(raw)) as { type: string };
      if (message.type === 'join') route.send(JSON.stringify({
        type: 'welcome', protocol: fixture.protocol, playerId: 'fixture-player',
        token: '0'.repeat(48), room: fixture.room, mode: fixture.mode, snapshot: fixture,
      }));
      else if (message.type === 'input') route.send(JSON.stringify(fixture));
    });
  });
  await load(page); await page.locator('#play-private').click();
  await page.locator('#gameplay').selectOption('story');
  await page.locator('#room-input').fill('QA-END');
  await page.getByRole('button', { name: 'Join the city' }).click();
  await renderedFrames(page);
  await expect(page.locator('#ending-dialog')).toBeVisible();
  await expect(page.locator('#ending-title')).toHaveText('Open Windows');
  await expect(page.locator('#crew-dialog')).toBeHidden();
  await page.screenshot({ path: testInfo.outputPath('completed-room-ending-fixture.png') });
  await page.getByRole('button', { name: 'Keep exploring' }).click();
  await page.locator('#crew-open').click();
  await expect(page.locator('#crew-dialog')).toBeVisible();
  await expect(page.locator('#crew-recap .recap-line')).toHaveCount(1);
  expect(errors.get(page)).toEqual([]);
});

test('confirmed replay from a completed checkpoint (labelled setup)', async ({ page }, testInfo) => {
  const checkpoint = completedSimulation('STORY', 'solo-player').serialize();
  let provenance = 'Synthetic completed checkpoint fixture; not campaign completion evidence.';
  if (process.env.ANDOLAN_EARNED_CAMPAIGN) {
    const earned = JSON.parse(readFileSync(process.env.ANDOLAN_EARNED_CAMPAIGN, 'utf8')) as {
      visited: string[]; mission: Snapshot['mission']; player: Snapshot['players'][number];
    };
    expect(earned.visited).toHaveLength(22);
    expect(earned.mission.complete).toBe(true);
    expect(earned.mission.history).toHaveLength(7);
    checkpoint.mission = earned.mission;
    checkpoint.players = [earned.player];
    provenance = 'Reconstructed checkpoint using earned mission and player from the physical campaign; vehicles and command ledger use default unoccupied fixture state.';
  }
  testInfo.annotations.push({ type: 'setup', description: provenance });
  writeFileSync(testInfo.outputPath('replay-checkpoint.json'), JSON.stringify(checkpoint, null, 2));
  await testInfo.attach('checkpoint-provenance.txt', { body: provenance, contentType: 'text/plain' });
  await page.addInitScript(saved => localStorage.setItem('andolan.story.v1', JSON.stringify(saved)), checkpoint);
  await load(page); await page.locator('#play-story').click();
  await stage(page, 'complete');
  await expect(page.locator('#ending-dialog')).toBeVisible();
  await confirmReplay(page);
  await stage(page, 'keys');
  expect((await state(page)).snapshot.mission.history).toHaveLength(0);
  await expect(page.locator('#ending-dialog')).toBeHidden();
  expect(errors.get(page)).toEqual([]);
});

interface Point { x: number; z: number }
const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.z - b.z);
function clearLine(a: Point, b: Point) {
  const slices = Math.ceil(distance(a, b) / .35);
  for (let n = 0; n <= slices; n++) if (isBlocked(a.x + (b.x - a.x) * n / Math.max(1, slices), a.z + (b.z - a.z) * n / Math.max(1, slices), .7)) return false;
  return true;
}
/** A* uses public world geometry. It produces ordinary movement intent, never state edits. */
function walkingRoute(from: Point, to: Point): Point[] {
  const key = (p: Point) => `${p.x},${p.z}`;
  const start = { x: Math.round(from.x / 2) * 2, z: Math.round(from.z / 2) * 2 };
  const goal = { x: Math.round(to.x / 2) * 2, z: Math.round(to.z / 2) * 2 };
  const open = [start]; const costs = new Map([[key(start), 0]]); const previous = new Map<string, Point>(); const closed = new Set<string>();
  while (open.length) {
    open.sort((a, b) => (costs.get(key(a))! + distance(a, goal)) - (costs.get(key(b))! + distance(b, goal)));
    const current = open.shift()!;
    if (key(current) === key(goal)) {
      const path = [to]; let node = current;
      while (key(node) !== key(start)) { path.unshift(node); node = previous.get(key(node))!; }
      path.unshift(from); const compact: Point[] = []; let index = 0;
      while (index < path.length - 1) {
        let next = path.length - 1;
        while (next > index + 1 && !clearLine(path[index]!, path[next]!)) next--;
        compact.push(path[next]!); index = next;
      }
      return compact;
    }
    if (closed.has(key(current))) continue; closed.add(key(current));
    for (const [dx, dz] of [[2, 0], [-2, 0], [0, 2], [0, -2], [2, 2], [2, -2], [-2, 2], [-2, -2]]) {
      const next = { x: current.x + dx!, z: current.z + dz! };
      if (closed.has(key(next)) || !clearLine(current, next)) continue;
      const cost = costs.get(key(current))! + Math.hypot(dx!, dz!);
      if (cost < (costs.get(key(next)) ?? Infinity)) { costs.set(key(next), cost); previous.set(key(next), current); open.push(next); }
    }
  }
  throw new Error(`No walking route from ${key(from)} to ${key(to)}`);
}
async function startIntent(page: Page) {
  await page.evaluate(axes => {
    const controller = { axes, sequence: 8_000_000_000_000_000, timer: 0 };
    // The normal simulation still runs at real time. A high input sequence avoids keyboard
    // polling replacing test intent; the page is isolated and disposed after this test.
    controller.timer = window.setInterval(() => window.__ANDOLAN.connection().input({ type: 'input', seq: ++controller.sequence, ...controller.axes }), 35);
    window.__qaIntent = controller;
  }, rest);
}
async function intent(page: Page, axes: Partial<Intent>) {
  await page.evaluate(axes => { window.__qaIntent!.axes = axes; }, { ...rest, ...axes });
}
async function walkTo(page: Page, target: Point, radius = 2) {
  const route = walkingRoute(await me(page), target);
  const deadline = Date.now() + 140_000;
  for (let i = 0; i < route.length; i++) {
    const point = route[i]!; const tolerance = i === route.length - 1 ? radius : .7;
    while (distance(await me(page), point) > tolerance) {
      if (Date.now() > deadline) throw new Error(`Walking timed out at ${JSON.stringify(await me(page))} toward ${JSON.stringify(point)}`);
      const player = await me(page); const length = distance(player, point);
      const scale = Math.min(1, length / 2);
      await intent(page, { moveX: (point.x - player.x) / length * scale, moveZ: (point.z - player.z) / length * scale, sprint: true });
      await page.waitForTimeout(85);
    }
  }
  await intent(page, rest);
}
async function driveToClinic(page: Page) {
  const route = [{ x: 48, z: 48 }, { x: 48, z: -48 }, { x: 52, z: -48 }];
  const deadline = Date.now() + 180_000;
  for (const point of route) {
    while (true) {
      const vehicle = (await state(page)).snapshot.vehicles[0]!;
      const remaining = distance(vehicle, point);
      if (remaining < 4) break;
      if (Date.now() > deadline) throw new Error(`Driving timed out at ${JSON.stringify(vehicle)} toward ${JSON.stringify(point)}`);
      const desired = Math.atan2(point.x - vehicle.x, point.z - vehicle.z);
      const error = Math.atan2(Math.sin(desired - vehicle.heading), Math.cos(desired - vehicle.heading));
      const targetSpeed = Math.abs(error) > .5 ? 3.5 : Math.min(9, Math.max(3.5, remaining * .8));
      await intent(page, { forward: Math.max(-1, Math.min(1, (targetSpeed - vehicle.speed) / 8)), turn: Math.max(-1, Math.min(1, error * 1.8)) });
      await page.waitForTimeout(85);
    }
  }
  await intent(page, rest);
  await expect.poll(async () => Math.abs((await state(page)).snapshot.vehicles[0]!.speed)).toBeLessThan(1);
  await page.keyboard.press('KeyF');
  await expect.poll(async () => (await me(page)).vehicleId).toBeNull();
}

test('complete six chapters through real-time movement, driving and visible choices', async ({ page }, testInfo) => {
  test.setTimeout(900_000);
  await load(page); await page.locator('#play-story').click();
  await conversation(page); await stage(page, 'car');
  await page.keyboard.press('KeyF'); await stage(page, 'clinic-drive');
  await startIntent(page);
  await driveToClinic(page); await stage(page, 'receipt');
  const decisions: Record<string, string> = {
    receipt: 'copy', compare: 'narrow', shipping: 'supplies',
    edition: 'correct', 'friendly-ledger': 'disclose',
    voices: 'share', 'hearing-choice': 'open-record',
  };
  const visited = new Set<string>(['keys', 'car', 'clinic-drive']);
  for (let guard = 0; guard < 30; guard++) {
    const mission = (await state(page)).snapshot.mission;
    if (mission.complete) break;
    visited.add(mission.stage);
    const target = landmark(mission.targetId!); expect(target).toBeTruthy();
    await walkTo(page, target!, Math.max(1, target!.radius - 2));
    if (mission.stage === 'clinic-restored') {
      await expect(page.locator('#subtitle')).toBeVisible();
      await expect(page.locator('#subtitle-speaker')).toHaveText('Meera');
      await expect(page.locator('#subtitle-line')).toContainText('reserve van came early');
    }
    if (mission.trigger === 'arrive') await expect.poll(async () => (await state(page)).snapshot.mission.stage).not.toBe(mission.stage);
    else {
      await conversation(page, decisions[mission.stage]);
      await expect.poll(async () => (await state(page)).snapshot.mission.stage).not.toBe(mission.stage);
      if (mission.stage === 'shipping') {
        await renderedFrames(page);
        await expect(page.locator('#subtitle')).toBeHidden();
        const current = await me(page);
        expect(distance(current, landmark('clinic')!)).toBeGreaterThan(80);
      }
    }
    console.log(`Campaign stage completed: ${mission.stage}`);
  }
  const final = (await state(page)).snapshot;
  expect(final.mission.complete).toBe(true);
  expect(final.mission.ending?.id).toBe('open-windows');
  expect(final.mission.history).toHaveLength(7);
  expect(final.mission.evidence).toContain('hearing');
  await expect(page.locator('#ending-dialog')).toBeVisible();
  await expect(page.locator('#ending-title')).toHaveText('Open Windows');
  await testInfo.attach('campaign-evidence.json', { body: JSON.stringify({ visited: [...visited], mission: final.mission, player: await me(page), worldBounds: WORLD.bounds }, null, 2), contentType: 'application/json' });
  await testInfo.attach('completed-checkpoint.json', { body: await page.evaluate(() => localStorage.getItem('andolan.story.v1')!), contentType: 'application/json' });
  await page.screenshot({ path: testInfo.outputPath('campaign-ending.png') });
  await confirmReplay(page);
  await stage(page, 'keys');
  expect((await state(page)).snapshot.mission.history).toHaveLength(0);
  expect(errors.get(page)).toEqual([]);
});
