// Isolation test: one rendered Rama observer, one lightweight WebSocket Hanuman.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
import { WebSocket } from 'ws';
import { launchChromium } from './browser-package.mjs';

const [folder, reportFile, screenshotFile] = process.argv.slice(2);
if (!folder || !reportFile || !screenshotFile)
  throw Error('Usage: node test_vanara_observer.mjs extracted-dir report.json screenshot.png');
const root = path.resolve(folder);
const host = spawn(process.execPath, [path.join(root, 'serve_rooms.mjs'), '--port', '0'],
  { cwd: root, stdio: ['ignore','pipe','pipe'] });
let hostOutput = '';
for (const stream of [host.stdout,host.stderr]) stream.on('data', c => { hostOutput += c; });
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const errors = [], unexpected = [], wire = [];
const evidence = {result:'running', scope:'one rendered Chromium/SwiftShader observer and one WebSocket caster on loopback Wasm host; not two rendered clients or WAN',
  checks:[], page_errors:errors, unexpected_requests:unexpected};
const check = (condition,label) => {assert.ok(condition,label);evidence.checks.push(label);};
async function until(label, fn, timeout = 90000) {
  const deadline=Date.now()+timeout;
  while(Date.now()<deadline) {
    const result=await fn();if(result)return result;
    if(host.exitCode!==null || host.signalCode!==null) throw Error(label+': host exited: '+hostOutput.slice(-1000));
    await delay(30);
  }
  throw Error('Timeout waiting for '+label+': '+hostOutput.slice(-1000));
}
const read = page => page.evaluate(() => window.yugaProbe?.() ?? {mode:'loading'});
const distance = (a,b) => Math.hypot(a[0]-b[0],a[1]-b[1]);
let browser, owner, page;
try {
  await Promise.all([mkdir(path.dirname(path.resolve(reportFile)),{recursive:true}), mkdir(path.dirname(path.resolve(screenshotFile)),{recursive:true})]);
  const port=await until('host start',()=>Number(/127\.0\.0\.1:(\d+)/.exec(hostOutput)?.[1]));
  const origin=`http://127.0.0.1:${port}`, documentUrl=`${origin}/yuga-rust.html`;
  const [html,wasm,testSource]=await Promise.all([
    readFile(path.join(root,'yuga-rust.html')),readFile(path.join(root,'yuga-rust.wasm')),readFile(fileURLToPath(import.meta.url))
  ]);
  const response=await fetch(documentUrl);
  assert.ok(response.ok && Buffer.from(await response.arrayBuffer()).equals(html),'host must serve extracted HTML');
  Object.assign(evidence,{html_sha256:sha(html),wasm_sha256:sha(wasm),test_sha256:sha(testSource)});
  owner=new WebSocket(`ws://127.0.0.1:${port}/rooms`);
  const sender={messages:[],state:null,replies:[],seq:0};
  owner.on('message',data=>{
    const m=JSON.parse(data.toString());
    if(m.type==='state') {sender.state=m.state;if(m.accepted!==null)sender.replies.push(m);}
    else sender.messages.push(m);
  });
  owner.on('error',()=>{});
  await until('caster socket',()=>owner.readyState===WebSocket.OPEN);
  owner.send(JSON.stringify({type:'create',hero:'hanuman',teamSize:1}));
  const lobby=await until('caster lobby',()=>sender.messages.find(m=>m.type==='lobby'));
  browser=await launchChromium();
  evidence.browser=browser.version();
  evidence.viewport={width:760,height:480};
  const context=await browser.newContext({viewport:evidence.viewport});
  page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',req=>{const u=new URL(req.url());if(['http:','https:'].includes(u.protocol)&&
    (u.origin!==origin||u.pathname!=='/yuga-rust.html'))unexpected.push(u.origin+u.pathname);});
  page.on('websocket',socket=>{
    const u=new URL(socket.url());
    if(u.host!==`127.0.0.1:${port}`||u.pathname!=='/rooms'){unexpected.push(u.origin+u.pathname);return;}
    socket.on('framereceived',({payload})=>{
      try {
        const p=JSON.parse(typeof payload==='string'?payload:payload.toString());
        const c=p.state?.opponent?.casts?.find(c=>c.id==='vanara_sena');
        if(c&&wire.length<80)wire.push({tick:p.state.tick,age:c.age_ticks,target:c.target,hp:p.state.actor.hp});
      } catch { /* Ignore non-JSON frames. */ }
    });
  });
  const loadStarted=Date.now();
  await page.goto(documentUrl,{waitUntil:'domcontentloaded',timeout:120000});
  await page.waitForFunction(()=>window.yugaProbe?.().mode==='ready',null,{timeout:120000});
  const readyWallMs=Date.now()-loadStarted;
  await page.locator('#hero').selectOption('rama');
  await page.locator('.rooms summary').click();
  await page.locator('#room-code').fill(lobby.code);
  const joinStarted=Date.now();
  await page.locator('#join-room').click();
  await page.waitForFunction(()=>{
    const p=window.yugaProbe?.();return p?.mode==='playing'&&p.state?.hero==='rama'&&
      p.renderer?.remoteHeroes?.some(r=>r.hero==='hanuman')&&p.renderer.frames>3;
  },null,{timeout:120000});
  evidence.startup_wall_ms={page_to_ready:readyWallMs,join_to_remote_render:Date.now()-joinStarted};
  await until('caster authority state',()=>sender.state?.opponent?.actor?.pos);
  let observer=await read(page);
  check(observer.state.army.units.length===0,'room contains no wave units');
  const firstFrames=observer.renderer.frames;
  const sendMotion=(movement,cast)=>{
    const seq=++sender.seq;
    owner.send(JSON.stringify({type:'input',seq,movement,aim:[0,1],...(cast?{cast}: {})}));
    return seq;
  };
  const timer=setInterval(()=>sendMotion([0,1]),250);
  try {
    await until('caster approaches',()=>sender.state && distance(sender.state.actor.pos,sender.state.opponent.actor.pos)<7,20000);
  } finally {clearInterval(timer);}
  sendMotion([0,0]);
  const stopped=sender.state.tick;
  await until('neutral motion processed',()=>sender.state?.tick>=stopped+4);
  observer=await read(page);
  const enemyPos=sender.state.opponent.actor.pos.slice(), hpBefore=observer.state.actor.hp;
  const startFrames=observer.renderer.frames;
  const traceHandle=await page.evaluateHandle(()=>{
    const trace={samples:0,frames:[],maxSpirits:0,modes:{}};
    const sample=()=>{
      const p=window.yugaProbe?.();if(!p)return;
      trace.samples++;trace.modes[p.mode]=(trace.modes[p.mode]??0)+1;
      const remote=p.renderer?.remoteHeroes?.find(r=>r.hero==='hanuman');
      const c=p.state?.opponent?.casts?.find(c=>c.id==='vanara_sena');
      trace.maxSpirits=Math.max(trace.maxSpirits,remote?.senaSpirits??0);
      if(remote?.senaSpirits===5&&!trace.canvasCapture){
        try {
          const canvas=document.querySelector('#arena');
          const sample=document.createElement('canvas');sample.width=32;sample.height=32;
          const ctx=sample.getContext('2d');ctx.drawImage(canvas,0,0,32,32);
          const rgba=ctx.getImageData(0,0,32,32).data, colors=new Set();
          for(let i=0;i<rgba.length;i+=4)colors.add(`${rgba[i]>>4},${rgba[i+1]>>4},${rgba[i+2]>>4}`);
          trace.canvasCapture={data:canvas.toDataURL('image/png'),colorBins:colors.size,tick:p.state.tick,
            frames:p.renderer.frames,spirits:remote.senaSpirits};
        }catch(error){trace.canvasCapture={error:String(error)};}
      }
      if(c&&trace.frames.length<60)trace.frames.push({tick:p.state.tick,age:c.age_ticks,renderedFrames:p.renderer.frames,
        spirits:remote?.senaSpirits??0,mode:p.mode,visible:document.visibilityState,focused:document.hasFocus()});
    };
    sample();trace.timer=setInterval(sample,50);return trace;
  });
  const ready=page.waitForFunction(()=>{
    const p=window.yugaProbe?.(), remote=p?.renderer?.remoteHeroes?.find(r=>r.hero==='hanuman');
    return p?.mode==='playing'&&remote?.senaSpirits===5&&remote.casts.includes('vanara_sena')
      ? {tick:p.state.tick,frames:p.renderer.frames,spirits:remote.senaSpirits,casts:remote.casts} : false;
  },null,{timeout:25000}).then(async handle=>{const sample=await handle.jsonValue();await handle.dispose();return {sample};},error=>({error}));
  const seq=sendMotion([0,0],{slot:5,ground:enemyPos,aim:[0,1]});
  const accepted=await until('authoritative cast accepted',()=>sender.replies.find(m=>m.seq===seq));
  check(accepted.accepted===true,'host accepts WebSocket Hanuman cast');
  const actualCast=accepted.state.casts.find(c=>c.id==='vanara_sena');
  assert.ok(actualCast);check(distance(actualCast.target,enemyPos)<0.01,'authority target matches the observer position');
  const readyResult=await ready;
  let shotBytes=null,afterShot=null;
  if(readyResult.sample){
    shotBytes=await page.screenshot({timeout:90000});
    afterShot=await read(page);
  }
  const trace=await traceHandle.evaluate(trace=>{clearInterval(trace.timer);delete trace.timer;return trace;});
  await traceHandle.dispose();
  const canvasCapture=trace.canvasCapture;delete trace.canvasCapture;
  if(canvasCapture?.data&&canvasCapture.colorBins>3){
    const png=Buffer.from(canvasCapture.data.split(',')[1],'base64');
    const canvasPath=path.resolve(screenshotFile).replace(/\.png$/i,'')+'-canvas.png';
    await writeFile(canvasPath,png);
    evidence.canvas_capture={path:canvasPath,sha256:sha(png),color_bins:canvasCapture.colorBins,
      tick:canvasCapture.tick,frames:canvasCapture.frames,spirits:canvasCapture.spirits};
  } else if(canvasCapture) evidence.canvas_capture={error:canvasCapture.error??'blank or insufficient canvas color variation',color_bins:canvasCapture.colorBins};
  evidence.observer_trace=trace;
  evidence.observer_wire=wire;
  if(readyResult.error)throw readyResult.error;
  const sample=readyResult.sample;
  check(sample.spirits===5&&sample.casts.includes('vanara_sena'),'observer renders five replicated spirit cues');
  const afterRemote=afterShot.renderer.remoteHeroes.find(r=>r.hero==='hanuman');
  if(afterRemote?.senaSpirits===5){await writeFile(screenshotFile,shotBytes);evidence.screenshot_sha256=sha(shotBytes);}
  const impact=await until('caster damage receipt',()=>sender.state?.events?.find(e=>e.id==='vanara_sena'&&
    e.cast_id===actualCast.cast_id&&e.kind==='impact'&&e.receipts?.some(r=>r.damage>0)));
  const hpAfter=await until('observer damage',async()=>{const p=await read(page);return p.state?.actor?.hp<hpBefore?p.state.actor.hp:null;});
  check(hpAfter<hpBefore,'observer receives authoritative damage');
  check(errors.length===0,'no uncaught page errors');
  check(unexpected.length===0,'no unexpected external requests');
  Object.assign(evidence,{result:'pass',caster:'WebSocket protocol client',observer:'rendered Chromium Rama',
    target:actualCast.target,observer_position_at_cast:enemyPos,cast_id:actualCast.cast_id,
    observer_frames:{initial:firstFrames,before_cast:startFrames,at_effect:sample.frames,after_screenshot:afterShot.renderer.frames},
    visible_spirits:sample.spirits,visible_after_screenshot:afterRemote?.senaSpirits??0,
    hp_before:hpBefore,hp_after:hpAfter,impact_receipts:impact.receipts});
  console.log(JSON.stringify(evidence,null,2));
} catch(error) {
  evidence.result='fail';evidence.failure=String(error);
  console.error(error);process.exitCode=1;
} finally {
  await writeFile(reportFile,JSON.stringify(evidence,null,2)+'\n');
  owner?.terminate(); if(browser)await browser.close();host.kill('SIGTERM');
}
