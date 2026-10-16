import { expect, test, type Page } from '@playwright/test';

interface AimSample { at: number; yaw: number; pitch: number; frames: number; gameTime: number }
interface KeySample extends AimSample { type: string; code: string }
interface AimProbe { read(): { keys: KeySample[]; samples: AimSample[] }; stop(): void }
type ProbeWindow = Window & { __yugaAimProbe: AimProbe };
const readAim = (page: Page) => page.evaluate(() => {
  const metrics = (window.__YUGA as unknown as { metrics(): { yaw: number; pitch: number; frames: number } }).metrics();
  return { at: performance.now(), yaw: metrics.yaw, pitch: metrics.pitch, frames: metrics.frames, gameTime: window.__YUGA.snapshot()!.time };
});

test('native keyboard aim keeps its input-clock rate with a five-FPS renderer and clears across pause', async ({ page }, info) => {
  test.setTimeout(180_000); await page.setViewportSize({ width: 480, height: 400 });
  const errors: string[] = [], consoleErrors: string[] = [];
  page.on('pageerror', error => errors.push(error.stack || error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  // Deliberately slow presentation scheduling only. No simulation clock, actor,
  // command, input payload or application-owned state is replaced by this test.
  await page.addInitScript(() => {
    window.__yugaQAFrameCap = true;
    const native = requestAnimationFrame.bind(window), queue = new Map<number, FrameRequestCallback>();
    let next = 0, queued = false, dispatching = false, last = performance.now() - 200, timer: number | undefined;
    const schedule = () => {
      if (!queue.size || queued || dispatching || timer !== undefined) return;
      timer = window.setTimeout(() => {
        timer = undefined; queued = true;
        native(time => {
          queued = false; dispatching = true;
          for (const id of [...queue.keys()]) { const callback = queue.get(id); queue.delete(id); if (callback) callback(time); }
          dispatching = false; last = performance.now(); schedule();
        });
      }, Math.max(0, 200 - performance.now() + last));
    };
    window.requestAnimationFrame = callback => { const id = ++next; queue.set(id, callback); schedule(); return id; };
    window.cancelAnimationFrame = id => { queue.delete(id); };
  });
  await page.goto('/'); await page.waitForFunction(() => !!window.__YUGA);
  await page.locator('#lobby-settings').click(); await page.locator('#quality').selectOption('low'); await page.locator('#resume-game').click();
  await page.locator('#practice-play').click(); await expect(page.locator('#loading')).toBeHidden({ timeout: 120_000 });
  await expect.poll(() => page.evaluate(() => window.__YUGA.metrics().ready)).toBe(true);
  await expect(page.locator('#arena')).toBeFocused();
  await page.evaluate(() => {
    const keys: KeySample[] = [], samples: AimSample[] = [], active = new Set<string>();
    const sample = (): AimSample => {
      const metrics = (window.__YUGA as unknown as { metrics(): { yaw: number; pitch: number; frames: number } }).metrics();
      return { at: performance.now(), yaw: metrics.yaw, pitch: metrics.pitch, frames: metrics.frames, gameTime: window.__YUGA.snapshot()!.time };
    };
    const observe = (event: KeyboardEvent) => {
      if (!['KeyJ', 'KeyI'].includes(event.code) || event.repeat) return;
      keys.push({ ...sample(), type: event.type, code: event.code });
      if (event.type === 'keydown') active.add(event.code); else active.delete(event.code);
    };
    window.addEventListener('keydown', observe, true); window.addEventListener('keyup', observe, true);
    const timer = window.setInterval(() => { if (active.size && samples.length < 1000) samples.push(sample()); }, 20);
    (window as unknown as ProbeWindow).__yugaAimProbe = {
      read: () => structuredClone({ keys, samples }),
      stop: () => { clearInterval(timer); window.removeEventListener('keydown', observe, true); window.removeEventListener('keyup', observe, true); },
    };
  });
  let evidence: unknown;
  try {
    await page.keyboard.down('KeyJ'); await page.waitForTimeout(1800); await page.keyboard.up('KeyJ');
    const observed = await page.evaluate(() => (window as unknown as ProbeWindow).__yugaAimProbe.read());
    const down = observed.keys.find(event => event.type === 'keydown' && event.code === 'KeyJ')!;
    const up = observed.keys.find(event => event.type === 'keyup' && event.code === 'KeyJ')!;
    const seconds = (up.at - down.at) / 1000, turnRate = (up.yaw - down.yaw) / seconds;
    const changesBetweenFrames = observed.samples.filter((sample, index) => index > 0 && sample.frames === observed.samples[index - 1]!.frames && Math.abs(sample.yaw - observed.samples[index - 1]!.yaw) > .01).length;
    expect(seconds).toBeGreaterThan(1.5); expect(turnRate).toBeGreaterThan(1.25); expect(turnRate).toBeLessThan(1.85);
    expect((up.frames - down.frames) / seconds).toBeLessThanOrEqual(5.5);
    expect(changesBetweenFrames, 'Aim must advance between renderer frames').toBeGreaterThan(2);
    const released = await readAim(page); await page.waitForTimeout(350); expect((await readAim(page)).yaw).toBeCloseTo(released.yaw, 6);

    await page.keyboard.down('KeyJ'); await page.waitForTimeout(100); await page.keyboard.press('Escape');
    await expect(page.locator('#pause-dialog')).toBeVisible(); const paused = await readAim(page);
    await page.waitForTimeout(800); const stillPaused = await readAim(page);
    expect(stillPaused.yaw).toBeCloseTo(paused.yaw, 6); expect(stillPaused.gameTime).toBe(paused.gameTime);
    await page.keyboard.up('KeyJ'); await page.locator('#resume-game').click();
    await page.waitForTimeout(300); const resumed = await readAim(page); expect(resumed.yaw).toBeCloseTo(paused.yaw, 6);
    await page.keyboard.down('KeyI'); await page.waitForTimeout(180); await page.keyboard.up('KeyI');
    const final = await readAim(page), finalProbe = await page.evaluate(() => (window as unknown as ProbeWindow).__yugaAimProbe.read());
    const pitchDown = finalProbe.keys.find(event => event.type === 'keydown' && event.code === 'KeyI')!, pitchUp = finalProbe.keys.find(event => event.type === 'keyup' && event.code === 'KeyI')!;
    const pitchSeconds = (pitchUp.at - pitchDown.at) / 1000;
    expect(final.pitch - resumed.pitch).toBeGreaterThan(.03);
    expect(final.pitch - resumed.pitch).toBeLessThanOrEqual(1.3 * pitchSeconds + .06);
    evidence = { scope: 'Actual Practice simulation and native keyboard controls; only requestAnimationFrame is capped at five FPS. Read-only diagnostic sampling; no game-state, clock or input-payload injection. This verifies input/presentation independence, not consumer hardware performance.', turnRate, seconds, renderedFrames: up.frames - down.frames, changesBetweenFrames, down, up, paused, stillPaused, resumed, final, pitchSeconds, pageErrors: errors, consoleErrors };
    expect(errors).toEqual([]); expect(consoleErrors).toEqual([]);
  } finally {
    await page.keyboard.up('KeyJ'); await page.keyboard.up('KeyI');
    const observations = await page.evaluate(() => { const probe = (window as unknown as ProbeWindow).__yugaAimProbe; const value = probe.read(); probe.stop(); return value; });
    await info.attach('native-five-fps-input-timing', { body: JSON.stringify({ evidence, observations }, null, 2), contentType: 'application/json' });
  }
});
