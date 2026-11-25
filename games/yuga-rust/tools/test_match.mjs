// Drive hero-only exploration and 1v1 room controls using the public diagnostic snapshot.
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { digest, packageUnderTest, launchChromium, openOffline } from './browser-package.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const {values} = parseArgs({options: {
  input: {type: 'string', default: path.join(root, 'dist/yuga-rust.html')},
  origin: {type: 'string'}, // When supplied, test two browsers against the real room server.
  report: {type: 'string'}, screenshot: {type: 'string'},
}});
const kind = values.origin ? 'room' : 'match';
const report = path.resolve(values.report || path.join(root, 'dist', kind + '-check.json'));
const screenshot = path.resolve(values.screenshot || path.join(root, 'dist', kind + '-gameplay.png'));
const game = await packageUnderTest(values.input);
const viewport = {width: 1100, height: 720};
const evidence = {
  scope: values.origin ? 'Two isolated Chromium sessions and an authoritative room host' : 'Local hero-only arena exploration',
  html_sha256: game.html_sha256, zip_sha256: game.zip_sha256,
  test_sha256: digest(await readFile(fileURLToPath(import.meta.url))),
  harness_sha256: digest(await readFile(new URL('./browser-package.mjs', import.meta.url))),
  checks: [], renderers: {}, requests: {documents: 0, room_sockets: 0, unexpected: []}, page_errors: [],
};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const distance = (a,b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const read = page => page.evaluate(() => window.yugaProbe?.() ?? {mode:'loading'});
const check = (test, description) => {
  assert.ok(test, description);
  evidence.checks.push(description);
  if (process.env.YUGA_QA_TRACE) console.log(description);
};

async function until(page, description, predicate, timeout = 60_000) {
  const deadline = Date.now() + timeout;
  let last;
  while (Date.now() < deadline) {
    last = await read(page);
    if (last.mode === 'error') throw Error('Game startup error: ' + await page.locator('#loading').textContent());
    if (predicate(last)) return last;
    await sleep(40);
  }
  throw Error(description + ' timed out. Last state ' + JSON.stringify({mode:last?.mode,hero:last?.state?.hero,
    tick:last?.state?.army?.tick, actor:last?.state?.actor?.pos, opponent:last?.state?.opponent?.actor?.pos, winner:last?.state?.winner, active:last?.state?.active?.id, clip:last?.renderer?.activeClip,
    events:last?.state?.events?.slice(-2), room:await page.locator('#room-status').textContent(), status:await page.locator('#status').textContent()}));
}

function track(context, allowedDocument, roomUrl, packets) {
  context.on('request', request => {
    const url = new URL(request.url());
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
    if (request.isNavigationRequest() && request.url() === allowedDocument()) evidence.requests.documents++;
    else evidence.requests.unexpected.push(url.origin + url.pathname);
  });
  context.on('page', page => {
    page.on('pageerror', error => evidence.page_errors.push(error.message.slice(0,400)));
    page.on('websocket', socket => {
      const url = new URL(socket.url());
      if (roomUrl && url.host === roomUrl.host && url.pathname === '/rooms') {
        evidence.requests.room_sockets++;
        socket.on('framereceived', ({payload}) => {
          if (typeof payload==='string' && packets && payload.startsWith('{"type":"state"')) {
            const {state} = JSON.parse(payload);
            for (const c of state.opponent?.casts ?? []) {
              if (!packets.has(c.id)) packets.set(c.id,{owner:state.opponent.hero, tick:state.army.tick, clip:c.motion});
            }
          }
          if (typeof payload==='string' && /^\{"type":"(closed|error)"/.test(payload)) {
            (evidence.room_messages ??= []).push(JSON.parse(payload));
          }
        });
      }
      else evidence.requests.unexpected.push(url.origin + url.pathname);
    });
  });
}

async function awaitMatch(page, hero) {
  const snap = await until(page, 'enter match as ' + hero,
    p => p.mode === 'playing' && p.state?.mode === 'match' && p.state.hero === hero &&
      p.renderer.heroId === hero && p.state.ruleset === 'hero_skirmish' && p.renderer.armyVisible === 0 && p.renderer.frames > 0);
  const {heroBones,heroClips,armyVisible,armyNear,armyRoles,objectiveCount,lanes} = snap.renderer;
  assert.ok(heroBones > 10 && heroClips.length >= 5 && lanes === 3);
  assert.equal(armyVisible, 0);
  assert.equal(snap.state.abilities.length,5);
  assert.equal(snap.state.army.waves_enabled, false);
  evidence.renderers[hero] = {heroBones,heroClips,armyVisible,armyNear,armyRoles,objectiveCount,lanes};
  return snap;
}

async function motion(page) {
  const initial = await read(page);
  await page.keyboard.down('w');
  try {
    return await until(page, 'W movement', p=>distance(p.state.actor.pos,initial.state.actor.pos) > .5);
  } finally {
    await page.keyboard.up('w');
  }
}

async function aimAtEnemy(page) {
  const p = await read(page);
  const bounds = page.viewportSize();
  const screens = new Map(p.renderer.targetScreens.map(t=>[t.id,t]));
  const candidates = p.state.army.units.filter(u => u.alive && u.team !== p.state.actor.team);
  candidates.sort((a,b)=>distance(a.xz,p.state.actor.pos)-distance(b.xz,p.state.actor.pos));
  for (const unit of candidates) {
    const target = screens.get(unit.id);
    if (!target || target.x < 16 || target.x > bounds.width-16 || target.y < 74 || target.y > bounds.height-80) continue;
    const unobstructed = await page.evaluate(({x,y}) => document.elementFromPoint(x,y)?.id === 'arena', target);
    if (!unobstructed) continue;
    await page.mouse.move(target.x,target.y);
    return {unit:unit.id, world:unit.xz};
  }
  // Exploration has no enemies. Aiming at clear ground is sufficient to exercise a cast.
  await page.mouse.move(bounds.width * .5, bounds.height * .47);
  return {unit:null};
}

async function testCast(page, slot) {
  const before = await until(page,'available action',p=>p.mode==='playing' && !p.state.active && p.state.actor.hp>0 &&
    p.state.abilities[slot].cooldown_ticks===0);
  const action = before.state.abilities[slot];
  const last = before.state.events.at(-1)?.seq ?? 0;
  const point = await aimAtEnemy(page);
  // Observe rendered frames before sending the input. Short draw/release clips can
  // finish before a desktop automation round-trip on a software GPU.
  const watch = await page.evaluateHandle(({id,last}) => {
    const deadline = performance.now() + 30_000;
    return {pose: new Promise(resolve => {
      function frame() {
        const p = window.yugaProbe();
        const ours = p.state?.events?.some(e=>e.seq>last && e.id===id && e.kind==='begin');
        const fx = p.renderer;
        if (ours && fx.activeClip!=='idle' && fx.poseTime>0 &&
            (fx.visibleCasts.includes(id) || fx.nocked || fx.projectiles>0)) {
          resolve({clip:fx.activeClip, seconds:fx.poseTime, arrows:fx.projectiles, nocked:fx.nocked});return;
        }
        if (performance.now()>=deadline) {resolve(null);return;}
        requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    })};
  },{id:action.id,last});
  if (slot===0) {await page.mouse.down();await page.mouse.up();}
  else await page.keyboard.press(['','q','e','c','x'][slot]);
  const observed = await until(page,'cast in live formation',p=>p.state.events.some(e=>e.seq>last&&e.id===action.id&&e.kind==='begin'));
  const begin = observed.state.events.find(e=>e.seq>last&&e.id===action.id&&e.kind==='begin');
  const visible = await watch.evaluate(holder=>holder.pose);
  await watch.dispose();
  assert.ok(visible,'a committed '+action.id+' cast presents an animated pose and visible effect');
  const release = await until(page,'release in lane',p=>p.state.events.some(e=>e.cast_id===begin.cast_id&&e.kind==='release'));
  return {id:action.id, clip:visible.clip, pose_seconds:visible.seconds, arrows:visible.arrows, nocked:visible.nocked, aim:point,
    begin_tick:begin.tick, release_tick:release.state.events.find(e=>e.cast_id===begin.cast_id&&e.kind==='release').tick};
}

async function localMatch(browser) {
  const context = await browser.newContext({viewport,offline:true});
  let url;
  track(context,()=>url);
  const opened = await openOffline(context,game,address=>{url=address;});
  const page = opened.tab;
  evidence.entry = opened.entry;
  await until(page,'ready',p=>p.mode==='ready',120_000);
  for (const hero of ['hanuman','rama']) {
    await page.locator('#hero').selectOption(hero);
    await page.locator('#match').click();
    const start = await awaitMatch(page,hero);
    const army = start.state.army;
    check(start.state.solo_exploration && army.units.length === 0 && !army.waves_enabled,
      hero+' enters solo exploration without wave units or AI opponents');
    const progressed = await until(page,'advancing clock',p=>p.state.army.tick >= army.tick+4);
    check(progressed.state.remaining_ticks < start.state.remaining_ticks,
      hero+' sees a running match clock');
    if (hero==='hanuman') {
      const supported = await page.evaluate(()=>isSecureContext && 'AudioWorkletNode' in window);
      if (supported) {
        const audio = await until(page,'Rust stereo limiter',p=>p.mixer==='openbf-rust');
        evidence.audio_mixer = audio.mixer;
        check(audio.mixer==='openbf-rust' && audio.audio.state==='running' && audio.audio.gain===1,
          'localhost Chromium activated the packaged openbf Rust stereo limiter and a live unity-gain output');
        await page.locator('#sound').click();
        const muted = await until(page,'mute audio quantum',p=>p.audio.muted && p.audio.gain===0);
        check(muted.audio.muted && muted.audio.gain===0 && muted.mixer==='openbf-rust',
          'muting drives the active audio output to zero');
        await page.locator('#sound').click();
        const audible = await until(page,'unmute audio quantum',p=>!p.audio.muted && p.audio.gain===1);
        check(!audible.audio.muted && audible.audio.gain===1,'unmuting restores the active audio output');
      }
    }
    const moved = await motion(page);
    check(moved.state.actor.pos[1] > start.state.actor.pos[1], hero+' moves forward with WASD');
    const cast = await testCast(page,hero==='hanuman'?1:4);
    evidence[hero+'_cast'] = cast;
    check(cast.release_tick > cast.begin_tick,hero+' commits an animated ability with a visible effect through live input');
    if (hero==='rama') {
      await page.screenshot({path:screenshot,timeout:90_000});
      evidence.screenshot_sha256 = digest(await readFile(screenshot));
    }
    await page.keyboard.press('Escape');
    const frozen = await until(page,'pause match',p=>p.mode==='paused');
    await sleep(350);
    const silent = await until(page,'paused audio quantum',p=>p.mode==='paused' && p.audio.gain===0);
    evidence[hero+'_pause'] = {before:frozen.state.army.tick,after:silent.state.army.tick,gain:silent.audio.gain};
    check(silent.state.army.tick===frozen.state.army.tick,hero+' pause freezes the lane authority and silences the mixer');
    await page.locator('#reset').click();
    const fresh = await awaitMatch(page,hero);
    check(fresh.state.army.tick < frozen.state.army.tick && fresh.state.events.length===0 &&
      fresh.state.army.gold===0 && fresh.state.abilities.every(a=>!a.cooldown_ticks),
      hero+' restart clears previous casts and restores the exploration state');
    await page.keyboard.press('Escape');
    await until(page,'second pause',p=>p.mode==='paused');
    await page.locator('#back').click();
    await until(page,'return to hero selection',p=>p.mode==='ready');
  }
  check(evidence.renderers.rama.heroClips.includes('draw') && evidence.renderers.hanuman.heroClips.includes('tail_sweep'),
    'hero selection switches between the imported bow and gada animation libraries');
  await context.close();
}

async function verifyRoomCast(sender,receiver,hero,slot) {
  const before = await until(sender.page,'ready network hero',
    p=>p.mode==='playing' && p.state.actor.hp>0 && !p.state.active && p.state.abilities[slot].cooldown_ticks===0);
  const id = before.state.abilities[slot].id;
  const last = before.state.events.at(-1)?.seq ?? 0;
  // Capture the best rival render actually presented. The received authoritative
  // activation is checked separately from frame presentation under SwiftShader.
  const remoteProbe = await receiver.page.evaluateHandle(id=>{
    const trace = {frames:0, effect:false, clip:null};
    const until = performance.now()+15_000;
    function frame() {
      const r=window.yugaProbe().renderer;
      trace.frames++;
      if(r.opponentCasts.includes(id)||r.opponentProjectiles>0) {trace.effect=true;trace.clip=r.opponentClip;return;}
      if(performance.now()<until) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    return trace;
  },id);
  await aimAtEnemy(sender.page);
  await sender.page.keyboard.press(['','q','e','c','x'][slot]);
  const released=await until(sender.page,'network release '+id,
    p=>p.state.events.some(e=>e.seq>last&&e.id===id&&e.kind==='release'));
  const event=released.state.events.find(e=>e.seq>last&&e.id===id&&e.kind==='release');
  await until(receiver.page,'room authority replicates '+id,p=>p.mode==='playing' && p.renderer.opponentHero===hero && receiver.packets.has(id));
  const rendered=await remoteProbe.evaluate(tr=>({...tr}));
  await remoteProbe.dispose();
  return {id,owner:hero,local_release_tick:event.tick,remote:receiver.packets.get(id),remote_render:rendered};
}

async function onlineRoom(browser) {
  const origin = new URL(values.origin);
  const url = new URL('/yuga-rust.html',origin).href;
  const received = await fetch(url);
  const actual = Buffer.from(await received.arrayBuffer());
  assert.ok(received.ok && actual.equals(game.bytes),'room host serves the exact tested release');
  // Two SwiftShader windows share one software GPU. Keep both active inside a
  // compact desktop viewport, while the single-player capture exercises 1100×720.
  evidence.seat_viewport = {width:760,height:480};
  async function seat(hero) {
    const context = await browser.newContext({viewport:evidence.seat_viewport});
    const packets = new Map();
    track(context,()=>url,origin,packets);
    const page = await context.newPage();
    await page.goto(url,{waitUntil:'domcontentloaded',timeout:120_000});
    await until(page,'room menu as '+hero,p=>p.mode==='ready',120_000);
    await page.locator('#hero').selectOption(hero);
    await page.locator('.rooms summary').click();
    return {context,page,packets};
  }
  const host = await seat('hanuman');
  const guest = await seat('rama');
  try {
    await host.page.locator('#room-size').selectOption('1');
    await host.page.locator('#create-room').click();
    await host.page.waitForFunction(()=>document.querySelector('#room-code').value.length>=4, undefined, {timeout:30_000});
    const code = await host.page.locator('#room-code').inputValue();
    await guest.page.locator('#room-code').fill(code);
    await guest.page.locator('#join-room').click();
    const [sun,moon] = await Promise.all([awaitMatch(host.page,'hanuman'),awaitMatch(guest.page,'rama')]);
    check(sun.state.actor.team==='sun' && moon.state.actor.team==='moon' && sun.renderer.opponentHero==='rama' &&
      moon.renderer.opponentHero==='hanuman','room assigns distinct teams and renders the selected rival rig in both browsers');
    check(sun.renderer.cameraForward===1 && moon.renderer.cameraForward===-1,'the Moon camera faces the opposing lane direction');
    const moved = await motion(host.page);
    const released = await read(host.page);
    const final = await until(host.page,'neutral input accepted',p=>p.state.army.tick>=released.state.army.tick+24);
    const seen = await until(guest.page,'opponent movement replication',p=>p.mode==='playing' &&
      distance(p.state.opponent.actor.pos,final.state.actor.pos)<.15 &&
      distance(p.state.opponent.actor.pos,sun.state.actor.pos)>.2);
    check(distance(seen.state.opponent.actor.pos,final.state.actor.pos)<.15,
      'guest sees Hanuman move to the position accepted by the room host');
    evidence.replicated_movement = {from:sun.state.actor.pos, during:moved.state.actor.pos, to:final.state.actor.pos,
      guest_observed:seen.state.opponent.actor.pos};
    const sweep = await verifyRoomCast(host,guest,'hanuman',3);
    check(sweep.remote.owner==='hanuman','Rama’s browser receives Hanuman’s committed rear sweep');
    const volley = await verifyRoomCast(guest,host,'rama',4);
    check(volley.remote.owner==='rama','Hanuman’s browser receives the rival bow volley from Rama');
    evidence.synchronized_casts = [sweep,volley];
    await guest.page.screenshot({path:screenshot,timeout:90_000});
    evidence.screenshot_sha256 = digest(await readFile(screenshot));
    check(evidence.requests.room_sockets===2,'each browser used one same-origin room socket');
    await guest.context.close();
    // A departing seat ends the room. The remaining player must be able to reach hero selection.
    await until(host.page,'opponent departure',p=>['ready','complete','paused'].includes(p.mode));
    const left = await read(host.page);
    if (left.mode!=='ready') await host.page.locator('#back').click();
    await until(host.page,'recover room menu',p=>p.mode==='ready');
    check(await host.page.locator('#match').isEnabled(),'host can return to a local match after the opponent leaves');
  } finally {
    await guest.context.close();
    await host.context.close();
  }
}

await Promise.all([mkdir(path.dirname(report),{recursive:true}),mkdir(path.dirname(screenshot),{recursive:true})]);
const browser = await launchChromium();
try {
  evidence.browser = browser.version();
  if (values.origin) await onlineRoom(browser);
  else await localMatch(browser);
  check(evidence.requests.unexpected.length===0,'all game assets were embedded and no external requests occurred');
  check(evidence.page_errors.length===0,'no uncaught browser errors');
  evidence.passed = true;
} catch (err) {
  evidence.passed = false;
  evidence.failure = String(err);
  console.error(err);
  process.exitCode = 1;
} finally {
  await writeFile(report,JSON.stringify(evidence,null,2)+'\n');
  await browser.close();
}
