// Exercise the shipped single-file game with browser input and a read-only state probe.
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { digest as hash, packageUnderTest, launchChromium, openOffline } from './browser-package.mjs';
import { parseArgs } from 'node:util';

const gameRoot = fileURLToPath(new URL('../', import.meta.url));
const { values } = parseArgs({
  options: {
    input: { type: 'string', default: path.join(gameRoot, 'dist/yuga-rust.html') },
    report: { type: 'string', default: path.join(gameRoot, 'dist/browser-check.json') },
    screenshot: { type: 'string', default: path.join(gameRoot, 'dist/gameplay.png') },
    'coach-screenshot': { type: 'string' },
  },
});
const html = path.resolve(values.input);
const shot = path.resolve(values.screenshot);
const report = path.resolve(values.report);
const game = await packageUnderTest(html);
const viewport = { width: 1100, height: 720 };
const evidence = {
  scope: 'Packaged HTML, desktop browser controls after disconnection, read-only Rust state and PlayCanvas presentation',
  input_sha256: game.html_sha256, zip_sha256: game.zip_sha256,
  test_sha256: hash(await readFile(fileURLToPath(import.meta.url))),
  harness_sha256: hash(await readFile(new URL('./browser-package.mjs', import.meta.url))),
  viewport, checks: [], ability_results: {}, rendered_abilities: {}, external_requests: [], page_errors: [],
};
await Promise.all([mkdir(path.dirname(shot), { recursive: true }), mkdir(path.dirname(report), { recursive: true })]);
const browser = await launchChromium();
const context = await browser.newContext({ viewport, offline: true, deviceScaleFactor: 1 });
let page;
let initialDocument;
const read = () => page.evaluate(() => window.yugaProbe?.() ?? { mode: 'loading' });
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const check = (ok, label) => {
  assert.ok(ok, label);
  evidence.checks.push(label);
  if (process.env.YUGA_QA_TRACE) console.log(label);
};
const distance = (a,b) => Math.hypot(a[0]-b[0], a[1]-b[1]);

async function coachScore(expected, stage) {
  if (!values['coach-screenshot']) return;
  const hint = await page.locator('#match-detail').textContent();
  check(hint.startsWith(expected + '/5 techniques'), 'coach shows ' + expected + '/5 after ' + stage);
  (evidence.coach_steps ??= []).push({stage, count:expected, hint});
}

async function until(label, predicate, timeout = 45_000) {
  const end = Date.now() + timeout;
  let snap;
  do {
    snap = await read();
    if (snap.mode === 'error') throw new Error('Game reported error: ' + (await page.locator('#loading').textContent()));
    if (predicate(snap)) return snap;
    await pause(60);
  } while (Date.now() < end);
  throw new Error(label + ' timed out: ' + JSON.stringify({mode:snap?.mode, tick:snap?.state?.tick,
    actor:snap?.state?.actor, targets:snap?.state?.targets, last:snap?.state?.events?.slice(-3)}));
}

async function aim(id) {
  const snap = await read();
  const target = snap.renderer.targetScreens.find(t => t.id === id);
  assert.ok(target && Number.isFinite(target.x) && Number.isFinite(target.y), 'target projected into camera');
  const box = await page.locator('#arena').boundingBox();
  assert.ok(box && target.x >= box.x && target.x < box.x + box.width && target.y >= box.y && target.y < box.y + box.height,
    'target feet within viewport');
  await page.mouse.move(target.x, target.y);
}

async function cast(slot, input) {
  const before = await until('ready to cast slot ' + slot, p => p.mode === 'playing' && !p.state.active && p.state.abilities[slot].cooldown_ticks === 0);
  const prevSeq = before.state.events.at(-1)?.seq ?? 0;
  await input();
  const began = await until('begin slot ' + slot, p => p.state.events.some(e => e.slot === slot && e.seq > prevSeq && e.kind === 'begin'));
  const begin = began.state.events.find(e => e.slot === slot && e.seq > prevSeq && e.kind === 'begin');
  const action = before.state.abilities[slot];
  if (!evidence.rendered_abilities[action.id]) {
    const posed = await until('animated ' + action.id, p => p.state.active?.cast_id === begin.cast_id &&
      p.renderer.activeClip === action.motion && p.renderer.posePhase > 0 && p.renderer.poseTime > 0 &&
      p.renderer.heroPose.length >= 4 && p.renderer.visibleCasts.includes(action.id));
    evidence.rendered_abilities[action.id] = {
      clip: posed.renderer.activeClip, normalized_time: posed.renderer.posePhase,
      clip_seconds: posed.renderer.poseTime, sampled_joints: posed.renderer.heroPose.length / 4,
    };
  }
  return begin;
}

async function beat(begin, kind) {
  const current = await until(kind + ' slot ' + begin.slot, p => p.state.events.some(e => e.cast_id === begin.cast_id && e.kind === kind));
  return { event: current.state.events.find(e => e.cast_id === begin.cast_id && e.kind === kind), current };
}

async function reset(mode) {
  const before = await read();
  await page.locator('#reset').click();
  const p = await until('reset from ' + mode, p => p.mode === 'playing' &&
    p.state.generation === before.state.generation + 1 &&
    p.state.defeated === 0 && p.state.actor.hp === 275 && p.state.abilities.every(a=>!a.cooldown_ticks) &&
    p.state.targets.every(t=>t.hp === t.max_hp));
  check(p.state.events.length === 0 && p.state.actor.shield === 0 && !p.state.active, mode + ' reset clears targets, timers, shields and event history');
}

const requests = {};
context.on('request', req => {
  const u = new URL(req.url());
  requests[u.protocol] = (requests[u.protocol] ?? 0) + 1;
  if (req.url() === initialDocument && req.isNavigationRequest()) return;
  if (['http:', 'https:', 'ws:', 'wss:'].includes(u.protocol)) evidence.external_requests.push(u.origin);
});
context.on('page', tab => {
  tab.on('websocket', socket => evidence.external_requests.push(new URL(socket.url()).origin));
  tab.on('pageerror', err => evidence.page_errors.push(err.message.slice(0, 400)));
});
try {
  evidence.browser = browser.version();
  const launched = await openOffline(context, game, url => { initialDocument = url; });
  page = launched.tab;
  evidence.entry = launched.entry;
  await page.locator('#begin').waitFor({ timeout: 120_000 });
  await until('offline startup', p => p.mode === 'ready', 120_000);
  await page.locator('#credits-button').click();
  check(await page.locator('#credits').isVisible() && (await page.locator('#notices').textContent()).trim().length > 100,
    'credits dialog exposes the bundled asset and engine notices');
  await page.locator('#close-credits').click();
  await page.locator('#begin').click();
  const first = await until('start drill', p => p.mode === 'playing' && p.state?.targets?.length === 4 && p.renderer?.frames > 0);
  check(first.period === 0.05 && first.state.abilities.length === 5 && first.state.enemies === 3,
    'offline play starts the 20 Hz trial with five actions, three enemies and an ally');
  const { heroClips, heroBones, mapProps, lanes, waters, decks, visualSolidIds, soldierCount } = first.renderer;
  check(heroBones===167 && ['fire','cast2','cast1','tail_sweep','mountain_pulse'].every(name=>heroClips.includes(name)),
    'renderer loaded the source skin and named clips for every ability');
  check(mapProps===63 && lanes===3 && waters===3 && decks===8 && new Set(visualSolidIds).size===16 && soldierCount===4,
    'renderer displays all map placements, three lanes, water, 16 authority solids and four native practice units');
  evidence.renderer_at_start = { heroClips, heroBones, mapProps, lanes, waters, decks, visualSolidIds, soldierCount };
  evidence.graphics_device = await page.locator('#arena').evaluate(canvas => {
    const gl = canvas.getContext('webgl2');
    const debug = gl.getExtension('WEBGL_debug_renderer_info');
    return {api: gl.getParameter(gl.VERSION), renderer: gl.getParameter(debug ? debug.UNMASKED_RENDERER_WEBGL : gl.RENDERER)};
  });
  await page.locator('#sound').click();
  check(await page.locator('#sound').getAttribute('aria-pressed') === 'true', 'audio mute is reflected in the player control');
  await page.locator('#sound').click();

  // Move and interrupt a pending attack before measuring the clean combat run.
  await coachScore(0, 'starting the drill');
  const start = first.state.actor.pos;
  await page.keyboard.down('w');
  try { await until('forward movement', p=>distance(start,p.state.actor.pos) >= .6); }
  finally { await page.keyboard.up('w'); }
  const moved = await read();
  check(moved.state.actor.pos[1] > start[1], 'W moves Hanuman up the central lane');
  await until('stationary camera after movement', p => p.state.tick >= moved.state.tick + 6);
  await page.locator('button[data-slot="3"]').click();
  await until('arm a lane ability', p => p.mode === 'playing' && p.input.armedSlot === 3);
  await page.keyboard.press('Escape');
  const cancelled = await until('cancel selection', p => p.mode === 'playing' && p.input.armedSlot === null);
  check(cancelled.state.events.length === moved.state.events.length, 'Escape cancels targeting before pause without spending a cast');
  await coachScore(0, 'cancelling an armed cast');
  await page.locator('button[data-slot="4"]').click();
  const selected = await until('select Mountain', p => p.input.armedSlot === 4);
  check(selected.state.events.length === moved.state.events.length, 'clicking a ready HUD ability arms it without casting');
  await aim(3);
  const projected = (await read()).input.ground;
  const pending = await cast(4, async () => { await page.mouse.down(); await page.mouse.up(); });
  const intended = moved.state.targets.find(target=>target.id===3).pos;
  evidence.toolbar_target = {intended, projected, actual:pending.target, error_m:distance(pending.target,intended)};
  check(evidence.toolbar_target.error_m < .08 && distance(projected,pending.target) < .08 && (await read()).input.armedSlot === null,
    'clicking the guard after selecting Mountain casts at its projected feet and clears the selection');
  await page.keyboard.press('Escape');
  const frozen = await until('pause with Escape', p=>p.mode==='paused');
  await pause(600);
  const again = await read();
  check(frozen.state.tick === again.state.tick && again.state.events.length === frozen.state.events.length,
    'pause freezes the authority tick and all combat events');
  for (let i=0; i<5; i++) {
    await page.keyboard.press('Tab');
    assert.ok(await page.evaluate(()=>['resume','reset','back'].includes(document.activeElement?.id)));
  }
  check(true,'keyboard focus stays in the pause dialog');
  await page.locator('#resume').click();
  await until('resume',p=>p.mode==='playing' && p.state.tick>again.state.tick);
  check(pending.slot === 4 && await page.locator('#arena').evaluate(el=>el === document.activeElement),
    'resume restores gameplay focus and advances the same drill');
  await page.locator('#pause').click();
  await until('pause button',p=>p.mode==='paused');
  await reset('paused');
  await coachScore(0, 'resetting the paused drill');

  // An unobstructed forward strike, frontal ally ward, rear sweep and delayed disk.
  await aim(1);
  const gada = await cast(0, ()=>page.mouse.down());
  await page.mouse.up();
  const gadaImpact = await beat(gada,'impact');
  const enemy = gadaImpact.current.state.targets.find(t=>t.id===1);
  check(enemy.hp === 56, 'primary strike deals 34 HP to the pointed enemy');
  await coachScore(1, 'the frontal gada hit');
  evidence.ability_results.gada = {begin:gada.tick, impact:gadaImpact.event.tick, hp:enemy.hp};
  await aim(1);
  const ward = await cast(1, ()=>page.keyboard.press('q'));
  const wardImpact = await beat(ward,'impact');
  const ally = wardImpact.current.state.targets.find(t=>t.team==='sun');
  check(wardImpact.current.state.actor.shield === 48 && ally.shield === 48, 'ward applies 48 shield to Hanuman and his forward ally');
  await page.keyboard.press('q');
  await beat(ward,'end');
  await page.locator('button[data-slot="1"]').click();
  const cooldown = await read();
  check(cooldown.input.armedSlot === null && cooldown.state.abilities[1].cooldown_ticks > 0 && cooldown.state.events.filter(e=>e.kind==='begin'&&e.slot===1).length===1,
    'keyboard and action-bar repeats during the ward lock and cooldown start no second cast');
  check((await page.locator('#status').textContent()).includes('cooling down'), 'HUD explains the rejected ward input');
  await coachScore(2, 'shielding the ally and rejecting both cooldown repeats');
  evidence.ability_results.ward = {impact:wardImpact.event.tick, shield:ally.shield};

  await aim(1);
  const tail = await cast(3, ()=>page.keyboard.press('c'));
  const burn = await beat(tail,'impact');
  check(burn.event.receipts.some(r=>r.damage===28), 'tail impact deals 28 damage behind the hero');
  const lingering = await beat(tail,'tick');
  check(lingering.event.tick > burn.event.tick, 'the tail field deals exposure damage after the sweep');
  await coachScore(3, 'sweeping the rear guard and applying the following exposure tick');
  evidence.ability_results.tail = {impact:burn.event.tick, first_exposure:lingering.event.tick};

  // Save a genuine running state; the canvas alone must contain visibly varied 3D imagery.
  await page.screenshot({ path: shot, animations:'allow', timeout:90_000 });
  const shotBytes = await readFile(shot);
  const bins = await page.evaluate(async b64 => {
    const image = new Image(); image.src='data:image/png;base64,'+b64; await image.decode();
    const canvas=document.createElement('canvas'); canvas.width=48; canvas.height=28;
    const ctx=canvas.getContext('2d');ctx.drawImage(image,image.width*.15,image.height*.19,image.width*.70,image.height*.58,0,0,48,28);
    const pixels=ctx.getImageData(0,0,48,28).data;const colors=new Set();
    for(let i=0;i<pixels.length;i+=4)colors.add((pixels[i]>>4)*256+(pixels[i+1]>>4)*16+(pixels[i+2]>>4));
    return colors.size;
  }, shotBytes.toString('base64'));
  check(bins>20, 'captured playfield has varied rasterized imagery in the central camera region');
  evidence.gameplay_png_sha256 = hash(shotBytes);
  evidence.central_color_bins = bins;

  await aim(1);
  const mountain = await cast(4, ()=>page.keyboard.press('x'));
  const {event:release} = await beat(mountain,'release');
  const {event:slammed,current:afterSlam} = await beat(mountain,'impact');
  check(slammed.tick-release.tick===9 && afterSlam.state.actor.hp===300 && afterSlam.state.defeated===2,
    'Mountain heals the actor and eliminates two targets nine ticks after release');
  await coachScore(4, 'landing Mountain Pulse on the guards');
  evidence.ability_results.mountain = {release:release.tick, impact:slammed.tick, kills:afterSlam.state.defeated, actor_hp:afterSlam.state.actor.hp};

  // The remaining target is seven metres forward. Vault into range, then finish it.
  await aim(3);
  const takeoff = await cast(2, ()=>page.keyboard.press('e'));
  const apex = await until('actual airborne vault',p=>p.state.actor.y>.05);
  const ground = await beat(takeoff,'recovery');
  check(ground.current.state.actor.y<.001 && distance(apex.state.actor.pos,ground.current.state.actor.pos)>0,
    'vault moves the actor through the air and lands on the court');
  const last = ground.current.state.targets.find(t=>t.id===3);
  check(last.hp === 25 && distance(ground.current.state.actor.pos,last.pos)<3.5, 'the remaining target is within physical strike reach after vault');
  await coachScore(5, 'landing the vault');
  evidence.ability_results.vault = {release_tick:(await beat(takeoff,'release')).event.tick, air_y:apex.state.actor.y, landed:ground.current.state.actor.pos};

  await aim(3);
  await cast(0, async ()=>{ await page.mouse.down(); await page.mouse.up(); });
  const won = await until('drill complete',p=>p.mode==='complete');
  check(won.state.defeated===3 && await page.locator('#result').isVisible(), 'all three neutralizations show the completion dialog');
  if (values['coach-screenshot']) {
    evidence.coach_completion = await page.locator('#summary').innerText();
    check(evidence.coach_completion.includes('5/5 techniques demonstrated'), 'the completion dialog preserves all five demonstrated techniques');
    const coachShot = path.resolve(values['coach-screenshot']);
    await mkdir(path.dirname(coachShot), {recursive:true});
    evidence.coach_png_sha256 = hash(await page.screenshot({path:coachShot,timeout:90_000}));
  }
  await reset('complete');
  await coachScore(0, 'starting over after victory');
  await page.setViewportSize({width:820,height:600});
  await until('resized renderer still ticks',p=>p.mode==='playing'&&p.state.tick>2);
  check(await page.locator('#arena').isVisible() && await page.locator('#pause').isVisible(), 'resized trial keeps its viewport and pause control');
  const unsupported = await launchChromium(false);
  try {
    const noGraphics = await unsupported.newContext({offline: true});
    const {tab:fallback} = await openOffline(noGraphics, game);
    await fallback.waitForFunction(() => window.yugaProbe?.().mode === 'error', undefined, {timeout: 45_000});
    check(await fallback.locator('#begin').isDisabled() && (await fallback.locator('#loading').textContent()).includes('WebGL'),
      'a desktop with WebGL disabled receives an actionable graphics requirement');
  } finally {
    await unsupported.close();
  }
  check(!evidence.external_requests.length, 'gameplay requested no external HTTP or WebSocket resources');
  check(!evidence.page_errors.length, 'no uncaught browser errors during normal play');
  evidence.transport_requests=requests;
  evidence.passed=true;
} catch (error) {
  evidence.passed=false;
  evidence.failure=String(error).slice(0,1400);
  if (page) await page.screenshot({path:shot.replace(/\.png$/,'-failure.png'),timeout:15000}).catch(()=>{});
  console.error(error);
  process.exitCode=1;
} finally {
  await writeFile(report, JSON.stringify(evidence,null,2)+'\n');
  await browser.close();
}
