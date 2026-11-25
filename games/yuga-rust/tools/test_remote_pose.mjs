// Inspect the opponent actually presented by the Moon client on its animation frames.
import assert from 'node:assert/strict';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { digest, launchChromium, packageUnderTest } from './browser-package.mjs';

const root = fileURLToPath(new URL('../',import.meta.url));
const {values} = parseArgs({options:{
  origin:{type:'string',default:'http://127.0.0.1:8787'},
  input:{type:'string',default:path.join(root,'dist/yuga-rust.html')},
  report:{type:'string',default:path.join(root,'dist/remote-pose.json')},
  screenshot:{type:'string',default:path.join(root,'dist/remote-mountain.png')},
}});
const url = new URL('/yuga-rust.html',values.origin);
const game=await packageUnderTest(values.input);
const viewport={width:720,height:450};
const checks=[];
const report={scope:'Two independent Chromium processes, packaged room host, physical Sun casts and Moon presentation frames',
  checks,viewport,device_scale_factor:0.5,html_sha256:game.html_sha256,zip_sha256:game.zip_sha256,
  test_sha256:digest(await readFile(fileURLToPath(import.meta.url))),
  harness_sha256:digest(await readFile(new URL('./browser-package.mjs',import.meta.url))),errors:[],commands:{}};
const check=(ok,label)=>{assert.ok(ok,label);checks.push(label);console.log(label);};
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function seat(hero) {
  const browser=await launchChromium();
  const page=await browser.newPage({viewport,deviceScaleFactor:.5});
  page.on('pageerror',err=>report.errors.push(err.message));
  await page.goto(url.href,{waitUntil:'domcontentloaded',timeout:120_000});
  await page.waitForFunction(()=>window.yugaProbe?.().mode==='ready',undefined,{timeout:120_000});
  await page.locator('#hero').selectOption(hero);
  await page.locator('.rooms summary').click();
  return {browser,page};
}

async function cast(page,slot,id,key) {
  await page.waitForFunction(slot=>{
    const p=window.yugaProbe();
    return p.mode==='playing' && !p.state.active && p.state.actor.hp>0 && p.state.abilities[slot].cooldown_ticks===0;
  },slot,{timeout:60_000});
  const target=await page.evaluate(()=>{
    const p=window.yugaProbe();
    const spots=new Map(p.renderer.targetScreens.filter(s=>s.kind==='unit'&&s.inView&&s.alive).map(s=>[s.id,s]));
    const actor=p.state.actor.pos;
    for(const u of p.state.army.units) {
      const screen=spots.get(u.id);
      if(!screen || Math.hypot(u.xz[0]-actor[0],u.xz[1]-actor[1])>10 || screen.y<62 || screen.y>innerHeight-65) continue;
      if(document.elementFromPoint(screen.x,screen.y)?.id==='arena') return {x:screen.x,y:screen.y};
    }
    return {x:innerWidth*.52,y:innerHeight*.54};
  });
  await page.mouse.move(target.x,target.y);
  await page.keyboard.press(key);
  const lastCast=report.commands[id]?.at(-1)?.cast_id ?? 0;
  const event=await page.waitForFunction(({id,lastCast})=>window.yugaProbe().state.events.find(e=>e.id===id&&e.kind==='release'&&e.cast_id>lastCast),
    {id,lastCast},{timeout:40_000});
  const release=await event.jsonValue();
  (report.commands[id] ??= []).push({release_tick:release.tick,cast_id:release.cast_id,target:release.target});
}

const actual=await fetch(url);
assert.ok(actual.ok && Buffer.from(await actual.arrayBuffer()).equals(game.bytes),'host serves verified release HTML');
await Promise.all([mkdir(path.dirname(values.report),{recursive:true}),mkdir(path.dirname(values.screenshot),{recursive:true})]);
let sun,moon;
try {
  [sun,moon]=await Promise.all([seat('hanuman'),seat('rama')]);
  await sun.page.locator('#create-room').click();
  await sun.page.waitForFunction(()=>document.querySelector('#room-code').value.length>=4);
  const code=await sun.page.locator('#room-code').inputValue();
  await moon.page.locator('#room-code').fill(code);
  await moon.page.locator('#join-room').click();
  await Promise.all([sun.page,moon.page].map(page=>page.waitForFunction(()=>{
    const p=window.yugaProbe();
    return p.mode==='playing' && p.renderer.opponentHero && p.renderer.frames>0;
  },undefined,{timeout:90_000})));
  report.browser=sun.browser.version();

  // Read the already-rendered rig, not just the received action packet. Capturing here
  // also preserves the exact frame before Chromium composites and clears its backbuffer.
  const observer=await moon.page.evaluateHandle(()=>{
    const trace={frames:0,last_frame:-1,sweep:[],mountain:[],timeline:[],image:null};
    function sample() {
      const p=window.yugaProbe();
      if(p.mode!=='playing') {requestAnimationFrame(sample);return;}
      const r=p.renderer;
      if(r.frames!==trace.last_frame) {
        trace.last_frame=r.frames;trace.frames++;
        const foot=r.targetScreens.find(s=>s.kind==='hero'&&s.team==='sun');
        const active=p.state.opponent?.active;
        const row={frame:r.frames,tick:p.state.army.tick,clip:r.opponentClip,active:active?.id??null,
          effects:[...r.opponentCasts],in_view:foot?.inView??false,screen:foot?[Math.round(foot.x),Math.round(foot.y)]:null};
        if(trace.timeline.length<100) trace.timeline.push(row);
        const list=r.opponentClip==='tail_sweep'?trace.sweep:r.opponentClip==='mountain_pulse'?trace.mountain:null;
        if(list && r.opponentHero==='hanuman' && foot?.inView && list.length<18) {
          const sample={frame:r.frames,authority_tick:p.state.army.tick,clip:r.opponentClip,
            cast:active?.id??null,phase:active?.phase??null,normalized_phase:active?.motion_phase_normalized??null,
            visible_effects:[...r.opponentCasts],screen_foot:[Math.round(foot.x),Math.round(foot.y)]};
          list.push(sample);
          if(list===trace.mountain && !trace.image && active?.id==='mountain_pulse') {
            trace.image=document.querySelector('#arena').toDataURL('image/png');
          }
        }
      }
      requestAnimationFrame(sample);
    }
    requestAnimationFrame(sample);
    return trace;
  });
  const started=Date.now();
  while(await observer.evaluate(t=>t.frames)<3) {
    if(Date.now()-started>40_000) throw Error('Moon client did not render three observation frames');
    await delay(80);
  }
  check(true,'Moon presented three independent frames before the Sun casts');
  await cast(sun.page,3,'lanka_dahan','c');
  let recorded;
  for(let attempt=0;attempt<3;attempt++) {
    await cast(sun.page,4,'mountain_pulse','x');
    const deadline=Date.now()+3300;
    do {
      recorded=await observer.evaluate(({frames,sweep,mountain,timeline})=>({frames,sweep,mountain,timeline}));
      if(recorded.mountain.length>=2) break;
      await delay(120);
    } while(Date.now()<deadline);
    if(recorded.mountain.some(s=>s.cast==='mountain_pulse'&&s.visible_effects.includes('mountain_pulse'))) break;
  }
  Object.assign(report,recorded);
  const mountain=recorded.mountain.filter(s=>s.cast==='mountain_pulse' && s.visible_effects.includes('mountain_pulse'));
  check(mountain.length>0,'Moon rendered the in-view Hanuman rig in mountain_pulse with its matching live effect');
  const phases=new Set(mountain.map(s=>s.normalized_phase));
  report.distinct_mountain_phases=phases.size;
  const captured=await observer.evaluate(t=>t.image);
  if(captured) {
    const pixels=await moon.page.evaluate(async data=>{
      const img=new Image();img.src=data;await img.decode();
      const c=document.createElement('canvas');c.width=60;c.height=40;const ctx=c.getContext('2d');ctx.drawImage(img,0,0,60,40);
      const p=ctx.getImageData(0,0,60,40).data;const bins=new Set();
      for(let i=0;i<p.length;i+=4) bins.add((p[i]>>4)*256+(p[i+1]>>4)*16+(p[i+2]>>4));
      return bins.size;
    },captured);
    report.frame_color_bins=pixels;
    if(pixels>20) {
      const bytes=Buffer.from(captured.split(',')[1],'base64');
      await writeFile(values.screenshot,bytes);
      report.screenshot_sha256=digest(bytes);
    }
  }
  check(report.errors.length===0,'both Chromium processes completed the cast sequence without an uncaught page error');
  report.passed=true;
} catch(error) {
  report.passed=false;
  report.failure=String(error);
  console.error(error);
  process.exitCode=1;
} finally {
  await Promise.all([sun?.browser.close(),moon?.browser.close()]);
  await writeFile(values.report,JSON.stringify(report,null,2)+'\n');
}
