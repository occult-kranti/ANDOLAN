/** Capture baseline and scenic candidate using the released Rust/WASM snapshots. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../../..');
const zip = path.resolve(process.env.YUGA_BASE_GAME_ZIP ||
  path.join(root, 'games/yuga-rust/downloads/yuga-rust-confluence.zip'));
const out = path.resolve(process.argv[2] || '/tmp/yuga-ghat-candidate');
const digest = b => createHash('sha256').update(b).digest('hex');
const file = (zipPath, member) => execFileSync('unzip', ['-p', zipPath, member], { maxBuffer: 150 * 1024 * 1024 });
const wasm = file(zip, 'yuga-rust.wasm');
const { instance } = await WebAssembly.instantiate(wasm, {});
const authority = instance.exports;
assert.equal(authority.duel_start(0, 0), 1);
// Move both players to the ghat. Then take Sun to the clear strip between
// buildings and leave Moon outside the other building's camera footprint.
for (let i = 0; i < 216; i++) authority.duel_step(-1, 0, 0, 1, -1, 0, 0, -1);
for (let i = 0; i < 40; i++) authority.duel_step(-1, 0, 0, 1, 0, 0, 0, -1);
for (let i = 0; i < 32; i++) authority.duel_step(0, 1, 0, 1, 0, 0, 0, -1);
function snapshot(seat) {
  const offset = authority.duel_snapshot(seat);
  return JSON.parse(Buffer.from(authority.memory.buffer, offset, authority.duel_snapshot_len()));
}
const states = [snapshot(0), snapshot(1)];
assert.equal(states[0].actor.team, 'sun');
assert.equal(states[1].actor.team, 'moon');
const allPlans = [
  {label:'baseline-sun', path:zip, seat:0},
  {label:'candidate-sun', path:path.join(out, 'yuga-rust-confluence.zip'), seat:0},
  {label:'baseline-moon', path:zip, seat:1},
  {label:'candidate-moon', path:path.join(out, 'yuga-rust-confluence.zip'), seat:1},
];
const plans = process.env.YUGA_CAPTURE_ONLY
  ? allPlans.filter(plan => plan.label.startsWith(process.env.YUGA_CAPTURE_ONLY))
  : allPlans;
const candidateProps = Number(process.env.YUGA_EXPECTED_PROPS || 69);
assert.ok(Number.isInteger(candidateProps) && candidateProps > 0);
assert.ok(plans.length, 'No capture matched YUGA_CAPTURE_ONLY');
await mkdir(out, { recursive:true });
const browser = await chromium.launch({
  headless:true,
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium',
  args:['--no-sandbox', '--disable-dev-shm-usage', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
});
const screenshots = [];
try {
  for (const plan of plans) {
    console.error('Capturing',plan.label);
    const html = file(plan.path, 'yuga-rust.html');
    const context = await browser.newContext({viewport:{width:1280,height:800}});
    const page = await context.newPage();
    const faults = [];
    const external = [];
    page.on('pageerror', error => faults.push(String(error)));
    const pageUrl = 'http://127.0.0.1:8791/yuga-rust.html';
    await page.route('**/*', route => {
      if (route.request().url() === pageUrl) return route.fulfill({contentType:'text/html',body:html});
      external.push(route.request().url());
      return route.abort();
    });
    await page.routeWebSocket('**/rooms', socket => {
      socket.onMessage(text => {
        if (JSON.parse(text).type !== 'create') return;
        socket.send(JSON.stringify({type:'lobby',code:'GHAT',count:2,capacity:2,seat:plan.seat}));
        socket.send(JSON.stringify({type:'state',state:states[plan.seat],accepted:null}));
      });
    });
    await page.goto(pageUrl,{waitUntil:'domcontentloaded',timeout:120_000});
    await page.waitForFunction(() => window.yugaProbe?.().mode === 'ready',null,{timeout:120_000});
    await page.locator('#hero').selectOption('hanuman');
    await page.locator('.rooms summary').click();
    await page.locator('#create-room').click();
    await page.waitForFunction(({x,z,team}) => {
      const p = window.yugaProbe();
      return p?.mode === 'playing' && p.renderer?.frames > 6 && p.state?.actor?.team === team
        && Math.hypot(p.state.actor.pos[0]-x,p.state.actor.pos[1]-z) < .01;
    },{x:states[plan.seat].actor.pos[0],z:states[plan.seat].actor.pos[1],team:states[plan.seat].actor.team},{timeout:120_000});
    await page.locator('.slot[data-slot="4"]').click();
    await page.mouse.move(640, 550);
    await page.waitForFunction(() => window.yugaProbe()?.input?.mountainAim !== null,null,{timeout:60_000});
    await page.waitForTimeout(600);
    const snapshot = await page.evaluate(() => window.yugaProbe());
    const screenshot = await page.screenshot({path:path.join(out,plan.label+'.png')});
    assert.equal(snapshot.state.actor.team,plan.seat ? 'moon' : 'sun');
    assert.equal(snapshot.renderer.mapProps,plan.label.startsWith('candidate') ? candidateProps : 63);
    assert.equal(snapshot.renderer.lanes,3);
    assert.equal(snapshot.renderer.decks,8);
    assert.equal(snapshot.renderer.visualSolidIds.length,16);
    assert.equal(snapshot.renderer.heroBones,167);
    assert.deepEqual(faults,[]);
    assert.deepEqual(external,[]);
    screenshots.push({label:plan.label,html_sha256:digest(html),png_sha256:digest(screenshot),
      team:snapshot.state.actor.team, actor_pos:snapshot.state.actor.pos,
      map_props:snapshot.renderer.mapProps,solid_ids:snapshot.renderer.visualSolidIds,
      camera_forward:snapshot.renderer.cameraForward,aim:snapshot.input.mountainAim,
      viewport:[1280,800],file:plan.label+'.png',page_errors:faults,external_requests:external});
    await context.close();
  }
  const record = {method:'Offline served HTML with a staged room transport and exact local released-WASM duel snapshots; actors used the real authority movement for 288 ticks. Targeting uses the game UI and renderer. This is a camera/geometry probe, not a multiplayer transport test.',
    wasm_sha256:digest(wasm),chromium:browser.version(),screenshots};
  await writeFile(path.join(out,'browser-review.json'),JSON.stringify(record,null,2)+'\n');
  console.log(JSON.stringify(record,null,2));
} finally { await browser.close(); }
