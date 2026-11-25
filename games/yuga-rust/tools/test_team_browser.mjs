// Two real desktop clients and four ordinary room-protocol peers use the shipped 3v3 host.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir,readFile,writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { WebSocket } from 'ws';
import { digest, launchChromium } from './browser-package.mjs';

const {values}=parseArgs({options:{url:{type:'string'},archive:{type:'string'},report:{type:'string'},screenshot:{type:'string'}}});
for(const field of ['url','archive','report','screenshot']) if(!values[field]) throw Error('Required --'+field);
const origin=new URL(values.url), entry=new URL('/yuga-rust.html',origin), socketURL=new URL('/rooms',origin);
socketURL.protocol=origin.protocol==='https:'?'wss:':'ws:';
const game=execFileSync('unzip',['-p',values.archive,'yuga-rust.html'],{maxBuffer:128*1024*1024});
const fetched=await fetch(entry);
assert.ok(fetched.ok&&Buffer.from(await fetched.arrayBuffer()).equals(game),'live host serves exact archived HTML');
const heroes=['hanuman','rama','hanuman','hanuman','rama','rama'];
const viewport={width:960,height:600};
const report={scope:'Packaged six-seat private team match with two independent Chromium processes and four room-protocol clients',
  zip_sha256:digest(await readFile(values.archive)),html_sha256:digest(game),
  test_sha256:digest(await readFile(fileURLToPath(import.meta.url))),
  harness_sha256:digest(await readFile(new URL('./browser-package.mjs',import.meta.url))),
  viewport,device_scale_factor:.5,checks:[],errors:[],unexpected_network:[],browser_sockets:0,casts:[]};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
const check=(ok,message)=>{assert.ok(ok,message);report.checks.push(message);console.log(message);};
const pages=[],browsers=[],peers=[];
async function poll(label,test,timeout=40_000) {
  const end=Date.now()+timeout;
  while(Date.now()<end){const value=await test();if(value)return value;await sleep(80);}
  throw Error(label+' timed out');
}
const read=page=>page.evaluate(()=>window.yugaProbe?.()??{mode:'loading'});
const health=async()=>{const r=await fetch(new URL('/health',origin));assert.ok(r.ok);return r.json();};

async function desktop(hero) {
  const browser=await launchChromium();browsers.push(browser);
  const page=await browser.newPage({viewport,deviceScaleFactor:.5});pages.push(page);
  page.on('pageerror',err=>report.errors.push(err.message));
  page.on('request',req=>{const u=new URL(req.url());if(/^https?:$/.test(u.protocol)&&u.href!==entry.href)report.unexpected_network.push(u.pathname);});
  page.on('websocket',ws=>{if(new URL(ws.url()).href===socketURL.href)report.browser_sockets++;else report.unexpected_network.push(ws.url());});
  await page.goto(entry.href,{waitUntil:'domcontentloaded',timeout:120_000});
  await page.waitForFunction(()=>window.yugaProbe?.().mode==='ready',undefined,{timeout:120_000});
  await page.locator('#hero').selectOption(hero);await page.locator('.rooms summary').click();
  return page;
}

async function joinPeer(hero,code) {
  const ws=new WebSocket(socketURL,{origin:origin.origin});
  const p={ws,seq:0,last:null,lobby:null,closed:false,deskErrors:[]};peers.push(p);
  ws.on('error',e=>p.deskErrors.push(e.message));
  ws.on('close',()=>{p.closed=true;});
  ws.on('message',data=>{
    const m=JSON.parse(data);
    if(m.type==='lobby')p.lobby=m;
    else if(m.type==='state')p.last=m.state;
    else if(m.type==='error')p.deskErrors.push(m.message);
  });
  await new Promise((resolve,reject)=>ws.once('open',resolve).once('error',reject));
  ws.send(JSON.stringify({type:'join',code,hero}));
  await poll('lobby acknowledgement for '+hero,()=>p.lobby);
  return p;
}
function move(p,delta) {
  p.ws.send(JSON.stringify({type:'input',seq:++p.seq,movement:delta,aim:[0,1]}));
}

async function watchMoon(page) {
  return page.evaluateHandle(()=>{
    const log={samples:[],frames:0,last:-1};
    function frame() {
      const p=window.yugaProbe();
      if(p.mode==='playing'&&p.renderer.frames!==log.last) {
        log.last=p.renderer.frames;log.frames++;
        const h=p.renderer.remoteHeroes.find(h=>h.seat===0);
        const sibling=p.renderer.remoteHeroes.find(h=>h.seat===2);
        const foot=p.renderer.targetScreens.find(s=>s.kind==='hero'&&s.seat===0);
        if(h?.clip==='mountain_pulse' && h.casts.includes('mountain_pulse') && foot?.inView && log.samples.length<16)
          log.samples.push({frame:p.renderer.frames,tick:p.state.army.tick,seat:h.seat,id:h.id,hero:h.hero,team:h.team,
            color:h.color,clip:h.clip,casts:h.casts,x:Math.round(foot.x),y:Math.round(foot.y),
            other_hanuman:{seat:sibling.seat,id:sibling.id,clip:sibling.clip,casts:sibling.casts}});
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);return log;
  });
}

async function physicalMountain(sun,moonWatch) {
  for(let attempt=0;attempt<3;attempt++) {
    await poll('Hanuman ready to cast',async()=>{
      const p=await read(sun);return p.mode==='playing'&&p.state.actor.hp>0&&!p.state.active&&!p.state.abilities[4].cooldown_ticks;
    },65_000);
    const aim=await sun.evaluate(()=>{
      const p=window.yugaProbe(),a=p.state.actor.pos;
      const spots=new Map(p.renderer.targetScreens.filter(s=>s.kind==='unit'&&s.inView&&s.alive).map(s=>[s.id,s]));
      for(const u of p.state.army.units) {
        const s=spots.get(u.id);
        if(s&&Math.hypot(u.xz[0]-a[0],u.xz[1]-a[1])<10&&s.y>80&&s.y<innerHeight-75&&
          document.elementFromPoint(s.x,s.y)?.id==='arena')return {x:s.x,y:s.y};
      }
      return {x:innerWidth*.52,y:innerHeight*.54};
    });
    const previous=report.casts.at(-1)?.cast_id??0;
    await sun.mouse.move(aim.x,aim.y);await sun.keyboard.press('x');
    const release=await poll('physical Sun Mountain release',async()=>{
      const {state}=await read(sun);return state.events.find(e=>e.id==='mountain_pulse'&&e.kind==='release'&&e.cast_id>previous);
    });
    report.casts.push({cast_id:release.cast_id,tick:release.tick,target:release.target});
    await sleep(1100);
    const samples=await moonWatch.evaluate(t=>t.samples);
    if(samples.length)return samples;
  }
  return moonWatch.evaluate(t=>t.samples);
}

await Promise.all([mkdir(path.dirname(values.report),{recursive:true}),mkdir(path.dirname(values.screenshot),{recursive:true})]);
try {
  const [sun,moon]=await Promise.all([desktop(heroes[0]),desktop(heroes[1])]);
  await sun.locator('#room-size').selectOption('3');
  await sun.locator('#create-room').click();
  const code=await poll('private team code',()=>sun.locator('#room-code').inputValue());
  await moon.locator('#room-code').fill(code);await moon.locator('#join-room').click();
  await poll('first guest enters lobby',async()=>/2\s*(?:\/|of)\s*6/i.test(await sun.locator('#room-status').textContent()));
  for(let i=2;i<5;i++)await joinPeer(heroes[i],code);
  report.five_seat_lobby=await poll('five of six',async()=>{const t=await sun.locator('#room-status').textContent();return /5\s*(?:\/|of)\s*6/i.test(t)?t:null;});
  check((await read(sun)).mode==='ready' && (await read(moon)).mode==='ready','the public 3v3 lobby waits for the sixth player');
  await joinPeer(heroes[5],code);
  await Promise.all(peers.map(p=>poll('peer authority',()=>p.last)));
  await Promise.all([sun,moon].map(page=>poll('graphical team roster',async()=>{const p=await read(page);return p.mode==='playing'&&p.renderer.remoteHeroes?.length===5;},120_000)));
  const [a,b]=await Promise.all([read(sun),read(moon)]);
  report.browser=browsers[0].version();
  report.hud_labels=await Promise.all([sun,moon].map(p=>p.locator('#location').textContent()));
  check(/Sun army.*Seat 1\/6/i.test(report.hud_labels[0]) && /Moon army.*Seat 2\/6/i.test(report.hud_labels[1]),
    'both HUDs identify their army and assigned team-match seat');
  report.views=[a,b].map(p=>({hero:p.state.hero,team:p.state.actor.team,local_tick:p.state.army.tick,
    remotes:p.renderer.remoteHeroes.map(({id,seat,hero,team,color,clip,pos})=>({id,seat,hero,team,color,clip,pos})).sort((x,y)=>x.seat-y.seat)}));
  for(const [local,p] of [a,b].entries()){
    assert.equal(p.state.actor.team,local?'moon':'sun');
    assert.equal(p.state.roster.length,5);
    const rivals=p.renderer.remoteHeroes;
    assert.equal(new Set(rivals.map(h=>h.id)).size,5);
    assert.equal(new Set(rivals.map(h=>h.seat)).size,5);
    const colors=new Map();
    for(const h of rivals) {
      assert.notEqual(h.seat,local);assert.equal(h.hero,heroes[h.seat]);assert.equal(h.team,h.seat%2?'moon':'sun');
      if(colors.has(h.team))assert.equal(h.color,colors.get(h.team));else colors.set(h.team,h.color);
    }
    assert.equal(colors.size,2);assert.notEqual(colors.get('sun'),colors.get('moon'));
  }
  check(true,'both viewports instantiate five identified teammate/enemy hero rigs with the assigned team colors');
  const watcher=await watchMoon(moon);
  const duplicate=peers[0];
  const initial=[...duplicate.last.actor.pos];
  const unmoved=[...b.renderer.remoteHeroes.find(h=>h.seat===0).pos];
  for(let i=0;i<12&&distance(initial,duplicate.last.actor.pos)<1.25;i++){move(duplicate,[1,0]);await sleep(130);}
  move(duplicate,[0,0]);await sleep(1400);
  const placed=[...duplicate.last.actor.pos];
  assert.ok(distance(initial,placed)>.6,'seat 2 moved');
  const sync=await poll('moon sees the independent duplicate',async()=>{
    const p=await read(moon),h=p.renderer.remoteHeroes?.find(h=>h.seat===2),same=p.renderer.remoteHeroes?.find(h=>h.seat===0);
    return h&&same&&distance(h.pos,placed)<.2&&distance(same.pos,unmoved)<.2?{moving:h.pos,still:same.pos,id:h.id,still_id:same.id}:null;
  });
  const sunCopy=await poll('Sun sees its teammate move',async()=>{
    const mate=(await read(sun)).renderer.remoteHeroes?.find(h=>h.seat===2);
    return mate&&distance(mate.pos,placed)<.2?mate.pos:null;
  });
  report.independent_hanumans={initial,placed,moon_observed:sync,sun_observed:sunCopy};
  check(sync.id!==sync.still_id,'both viewports track the independently moved Hanuman while his duplicate stays put');
  const samples=await physicalMountain(sun,watcher);
  report.moon_presented_cast=samples;
  check(samples.some(s=>s.seat===0&&s.other_hanuman.seat===2&&s.other_hanuman.id!==s.id&&!s.other_hanuman.casts.includes('mountain_pulse')),
    'Moon renders the correct Sun Hanuman’s Mountain pose and effect while his teammate stays independent');
  await moon.screenshot({path:values.screenshot,scale:'css',timeout:120_000});
  report.screenshot_sha256=digest(await readFile(values.screenshot));
  check(report.browser_sockets===2 && !report.unexpected_network.length && !report.errors.length,
    'the graphical clients use two same-origin room sockets and no external assets');
  peers.at(-1).ws.close();
  await Promise.all([sun,moon].map(p=>poll('return to title after player departure',async()=>(await read(p)).mode==='ready')));
  await poll('release match worker',async()=>{const state=await health();return state.rooms===0&&state.running===0;});
  check(true,'a departing seat closes the match and both public clients return to hero selection');
  report.passed=true;
} catch(error) {
  report.passed=false;report.failure=String(error);console.error(error);process.exitCode=1;
  report.last_views=await Promise.all(pages.map(async p=>{try{const x=await read(p);return {mode:x.mode,room:await p.locator('#room-status').textContent(),seat:x.state?.seat,tick:x.state?.army?.tick};}catch{return {};}}));
} finally {
  for(const p of peers)p.ws.close();
  await Promise.all(browsers.map(b=>b.close()));
  report.health_after_cleanup=await health().catch(()=>null);
  await writeFile(values.report,JSON.stringify(report,null,2)+'\n');
}
