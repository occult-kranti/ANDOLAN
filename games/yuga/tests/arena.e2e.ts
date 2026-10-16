import { YUGA_PROTOCOL } from '../shared/types';
import { test, expect, type Page, type TestInfo } from '@playwright/test';
import { keyboardYaw, mouseAimAt, inputObservation } from './browser-harness';
import { HEROES } from '../shared/heroes';
import { ArenaSimulation } from '../shared/simulation';
import { createArenaServer } from '../server/server';
import type { Actor, ArenaSnapshot, ArenaCommand, CommandResult, GameEvent } from '../shared/types';

type AudioDiagnostics = {started:boolean;unlocked:boolean;muted:boolean;active:boolean;volume:number;previewing:boolean;contextState:string;outputRms:number;outputPeak:number};
declare global { interface Window { __YUGA:{snapshot():ArenaSnapshot|undefined;playerId():string;metrics():{ready:boolean;room:string;frames:number;meanFps:number;maxFrameMs:number;yaw:number;pitch:number;targetId:string|null};audio():AudioDiagnostics}; __yugaQAFrameCap?:boolean } }
type WireProbe={lastSnapshot?:{at:number;tick:number;time:number};closedAt?:number;errors:string[];results:{at:number;id:string;code:string}[]};
const wireProbes=new WeakMap<Page,WireProbe>();
const errors=new WeakMap<Page,string[]>(), commands=new WeakMap<Page,ArenaCommand[]>(), results=new WeakMap<Page,CommandResult[]>(), receivedEvents=new WeakMap<Page,Map<number,GameEvent>>();
const snapshot=(page:Page)=>page.evaluate(()=>window.__YUGA.snapshot()!);
const me=(page:Page)=>page.evaluate(()=>window.__YUGA.snapshot()!.actors.find(a=>a.id===window.__YUGA.playerId())!);
const audio=(page:Page)=>page.evaluate(()=>window.__YUGA.audio());
const length=(a:{x:number;z:number},b:{x:number;z:number})=>Math.hypot(a.x-b.x,a.z-b.z);
async function load(page:Page){
 errors.set(page,[]);commands.set(page,[]);results.set(page,[]);receivedEvents.set(page,new Map());wireProbes.set(page,{errors:[],results:[]});
 page.on('pageerror',e=>errors.get(page)!.push(e.stack||e.message));
 page.on('websocket',socket=>{
  if(!socket.url().endsWith('/ws'))return;
  socket.on('close',()=>{wireProbes.get(page)!.closedAt=Date.now();});socket.on('socketerror',error=>wireProbes.get(page)!.errors.push(error));
  socket.on('framesent',frame=>{try{const m=JSON.parse(String(frame.payload));if(m.type==='command')commands.get(page)!.push(m);}catch{/* No bearer join/welcome traffic retained. */}});
  socket.on('framereceived',frame=>{try{const m=JSON.parse(String(frame.payload));if(m.type==='result'){results.get(page)!.push(m);wireProbes.get(page)!.results.push({at:Date.now(),id:m.id,code:m.code});}if(m.type==='snapshot')wireProbes.get(page)!.lastSnapshot={at:Date.now(),tick:m.snapshot.tick,time:m.snapshot.time};if(m.type==='snapshot')for(const event of m.snapshot.events)receivedEvents.get(page)!.set(event.id,event);}catch{/* No bearer join/welcome traffic retained. */}});
 });
 await page.addInitScript(()=>{
  const probe={heartbeat:0,lastHeartbeat:0,lastDispatch:0,lastSnapshot:null as null|{tick:number;time:number},lastResult:null as null|{id:string;code:string},closedAt:0,errors:0};
  Object.defineProperty(window,'__yugaSocketProbe',{value:probe});
  window.setInterval(()=>{probe.heartbeat++;probe.lastHeartbeat=Date.now();},100);
  const NativeWebSocket=window.WebSocket;
  window.WebSocket=class extends NativeWebSocket{
   constructor(url:string|URL,protocols?:string|string[]){super(url,protocols);if(!String(url).endsWith('/ws'))return;
    this.addEventListener('message',event=>{let message;try{message=JSON.parse(String(event.data));}catch{return;}probe.lastDispatch=Date.now();if(message.type==='snapshot')probe.lastSnapshot={tick:message.snapshot.tick,time:message.snapshot.time};if(message.type==='result')probe.lastResult={id:message.id,code:message.code};});
    this.addEventListener('close',()=>{probe.closedAt=Date.now();});this.addEventListener('error',()=>probe.errors++);
   }
  };
 });
 if(process.env.CI||process.env.YUGA_SOFTWARE_RENDERING==='1')await page.addInitScript(()=>{
  if(window.__yugaQAFrameCap)return;window.__yugaQAFrameCap=true;
  const native=window.requestAnimationFrame.bind(window),queue=new Map<number,FrameRequestCallback>();let id=0,timer:number|undefined,nativeQueued=false,dispatching=false,finished=performance.now()-100;
  const schedule=()=>{if(!queue.size||timer!==undefined||nativeQueued||dispatching)return;timer=window.setTimeout(()=>{timer=undefined;nativeQueued=true;native(timestamp=>{nativeQueued=false;dispatching=true;for(const key of [...queue.keys()]){const callback=queue.get(key);queue.delete(key);if(callback)try{callback(timestamp);}catch(e){window.setTimeout(()=>{throw e;},0);}}dispatching=false;finished=performance.now();schedule();});},Math.max(0,100-(performance.now()-finished)));};
  window.requestAnimationFrame=callback=>{const key=++id;queue.set(key,callback);schedule();return key;};window.cancelAnimationFrame=key=>{queue.delete(key);};
 });
 await page.bringToFront();await page.goto('/');await page.waitForFunction(()=>!!window.__YUGA);await expect(page.locator('#lobby')).toBeVisible();
}
async function low(page:Page){await page.locator('#lobby-settings').click();await page.locator('#quality').selectOption('low');await page.locator('#resume-game').click();}
async function frames(page:Page){await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));}
async function capture(page:Page,info:TestInfo,name:string){await frames(page);await page.screenshot({path:info.outputPath(`${name}.png`),fullPage:true});}
async function ready(page:Page){await expect(page.locator('#loading')).toBeHidden({timeout:120_000});await expect.poll(()=>page.evaluate(()=>!!window.__YUGA.snapshot()&&(window.__YUGA.metrics().ready||window.__YUGA.snapshot()!.phase==='finished'))).toBe(true);}
async function practice(page:Page){await page.bringToFront();await page.locator('#practice-play').click();await ready(page);await expect.poll(async()=>(await snapshot(page)).room).toBe('PRACTICE');}
async function activate(page:Page){await page.bringToFront();if(await page.locator('#pause-dialog').isVisible())await page.locator('#resume-game').click();await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().ready)).toBe(true);}
async function park(page:Page){if(!await page.locator('#pause-dialog').isVisible())await page.keyboard.press('Escape');await expect(page.locator('#pause-dialog')).toBeVisible();}
async function join(page:Page,name:string,room=''){await page.bringToFront();await page.locator('#online-open').click();await page.locator('#player-name').fill(name);await page.locator('#room-code').fill(room);await page.locator('#join-room').click();await ready(page);if(room)await expect.poll(async()=>(await snapshot(page)).room).toBe(room);}
async function hold(page:Page,key:string,until:(actor:Actor)=>boolean,timeout=15_000){await page.keyboard.down(key);try{await expect.poll(async()=>until(await me(page)),{timeout,intervals:[60,100]}).toBe(true);}finally{await page.keyboard.up(key);}}
async function previewSamples(page:Page){await page.locator('#sound-preview').click();return page.evaluate(async()=>{let peak=0,rms=0,running=false,previewing=false;const end=performance.now()+450;while(performance.now()<end){const d=window.__YUGA.audio();peak=Math.max(peak,d.outputPeak);rms=Math.max(rms,d.outputRms);running ||= d.contextState==='running';previewing ||= d.previewing;await new Promise(r=>setTimeout(r,20));}return{peak,rms,running,previewing};});}
async function range(page:Page,id:string,value:number){await page.locator(id).fill(String(value));}
async function attach(page:Page,info:TestInfo,name:string,detail:unknown){await info.attach(name,{body:JSON.stringify({scope:name,detail,pageErrors:errors.get(page),commands:commands.get(page),results:results.get(page)},null,2),contentType:'application/json'});}
const nativeYaw=keyboardYaw;

test('roster, saved settings and native muted audio preview',async({page},info)=>{
 await load(page);await capture(page,info,'desktop-roster');await expect(page.locator('[data-hero]')).toHaveCount(14);
 for(const hero of HEROES){await page.locator(`[data-hero="${hero.id}"]`).click();await expect(page.locator('#hero-name')).toHaveText(hero.name);await expect(page.locator('#hero-kit > div')).toHaveCount(3);for(const ability of hero.abilities)await expect(page.locator('#hero-kit')).toContainText(ability.name);}
 await page.locator('[data-hero="rama"]').click();await page.locator('#lobby-settings').click();await page.locator('#mute').check();await page.locator('#quality').selectOption('low');await page.locator('#reduced-motion').check();await range(page,'#sensitivity',130);await range(page,'#volume',60);
 const audible=await previewSamples(page);expect(audible.previewing).toBe(true);expect(audible.running).toBe(true);expect(audible.rms).toBeGreaterThan(.00001);expect((await audio(page)).muted).toBe(true);
 await expect.poll(async()=>(await audio(page)).contextState).toBe('suspended');await range(page,'#volume',0);const zero=await previewSamples(page);expect(zero.running).toBe(true);expect(zero.peak).toBeLessThan(.000001);await expect.poll(async()=>(await audio(page)).contextState).toBe('suspended');
 await range(page,'#volume',60);await page.locator('#resume-game').click();await page.reload();await page.waitForFunction(()=>!!window.__YUGA);await page.locator('#lobby-settings').click();await expect(page.locator('#volume')).toHaveValue('60');await expect(page.locator('#sensitivity')).toHaveValue('130');await expect(page.locator('#quality')).toHaveValue('low');await expect(page.locator('#mute')).toBeChecked();await expect(page.locator('#reduced-motion')).toBeChecked();await capture(page,info,'desktop-settings');
 await attach(page,info,'native-audio-and-settings',{audible,zero,claim:'Native WebAudio samples and preferences, not hardware listening quality'});expect(errors.get(page)).toEqual([]);
});

test('native practice movement, combat, three skills, upgrade and pause controls',async({page},info)=>{
 test.setTimeout(180_000);await load(page);await low(page);await practice(page);await capture(page,info,'practice-spawn');
 await page.keyboard.press('KeyB');await expect(page.locator('#upgrades-dialog')).toBeVisible();await page.locator('#buy-power').click();await expect.poll(async()=>(await me(page)).upgrades.power).toBe(1);expect((await me(page)).credits).toBe(60);await expect(page.locator('#buy-vitality')).toBeDisabled();await page.locator('#upgrades-dialog [data-close]').click();await expect(page.locator('#arena')).toBeFocused();
 for(const [slot,key]of ['KeyQ','KeyE','KeyR'].entries()){await page.keyboard.press(key);await expect.poll(async()=>(await me(page)).cooldowns[slot]!).toBeGreaterThan(0);}
 await hold(page,'Space',actor=>actor.y>.4);const before=await me(page);await hold(page,'KeyA',actor=>actor.x-before.x>4);await hold(page,'KeyW',actor=>actor.z>-47,30_000);
 // Stay behind our z=-37 tower, offset from its collider, and use ordinary
 // pointer aim promptly as the real enemy wave approaches. Keyboard rotation
 // has its own native timing gate; a slow aim loop here was dying in bot fire.
 const visibleRival=()=>page.evaluate(()=>{const state=window.__YUGA.snapshot()!,actor=state.actors.find(a=>a.id===window.__YUGA.playerId())!;return state.actors.filter(target=>target.team!==actor.team&&target.health>0&&Math.abs(target.x)<10&&Math.hypot(target.x-actor.x,target.z-actor.z)<31.5).sort((a,b)=>Math.hypot(a.x-actor.x,a.z-actor.z)-Math.hypot(b.x-actor.x,b.z-actor.z))[0];});
 await expect.poll(async()=>!!await visibleRival(),{timeout:30_000}).toBe(true);const pos=await me(page);expect(pos.health).toBeGreaterThan(0);const rival=await visibleRival();expect(rival).toBeDefined();const aim=await mouseAimAt(page,rival!.id,.08);await page.keyboard.press('KeyT');await hold(page,'KeyF',actor=>actor.damageDealt>pos.damageDealt,15_000);const afterAttack=await me(page);expect(afterAttack.health).toBeGreaterThan(0);await capture(page,info,'native-combat');
 await page.keyboard.press('KeyB');await expect(page.locator('#shop-status')).toContainText('Return to your spawn');await expect(page.locator('#buy-power')).toBeDisabled();await page.locator('#upgrades-dialog [data-close]').click();
 await page.keyboard.down('KeyW');await page.keyboard.down('KeyF');await page.keyboard.press('Escape');await expect(page.locator('#pause-dialog')).toBeVisible();const stopped=await snapshot(page),actor=await me(page);await page.keyboard.press('KeyQ');await page.waitForTimeout(700);expect((await snapshot(page)).time).toBe(stopped.time);expect(length(actor,await me(page))).toBe(0);await page.keyboard.up('KeyW');await page.keyboard.up('KeyF');await page.locator('#resume-game').click();await expect(page.locator('#arena')).toBeFocused();const resumed=await me(page);await hold(page,'KeyS',a=>length(a,resumed)>1);
 await attach(page,info,'native-practice',{before,combat:{rivalId:rival!.id,approach:pos,aim:{time:aim.state.time,yaw:aim.metrics.yaw,pitch:aim.metrics.pitch,health:aim.actor.health},afterAttack},after:await me(page),snapshotTime:(await snapshot(page)).time,claim:'Ordinary keyboard and pointer controls, unchanged bots/health/time and authority hit rules. Pointer correction into the target-lock cone avoids prolonged keyboard acquisition under bot fire. No command, position or clock injection.'});expect(errors.get(page)).toEqual([]);
});

test('mobile touch movement, aiming, firing and modal release',async({browser},info)=>{
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});const page=await context.newPage();try{
 await load(page);await capture(page,info,'mobile-roster');await low(page);await practice(page);await page.locator('#target-lock').tap();expect(await page.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();const cdp=await context.newCDPSession(page),pad=await page.locator('#touch-pad').boundingBox();expect(pad).not.toBeNull();const x=pad!.x+pad!.width/2,y=pad!.y+pad!.height/2,before=await me(page);
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y,id:1}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-35,id:1}]});await expect.poll(async()=>length(before,await me(page))).toBeGreaterThan(2);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 const look=await page.locator('#touch-look').boundingBox(),yaw=(await me(page)).yaw;expect(look).not.toBeNull();const lx=look!.x+look!.width*.45,ly=look!.y+look!.height*.5;await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:lx,y:ly,id:2}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:lx+50,y:ly,id:2}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await expect.poll(async()=>Math.abs((await me(page)).yaw-yaw)).toBeGreaterThan(.05);
 const fire=await page.locator('#shoot').boundingBox();await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:fire!.x+fire!.width/2,y:fire!.y+fire!.height/2,id:3}]});await expect.poll(async()=>(await snapshot(page)).events.some(e=>e.type==='shot'&&e.actorId===before.id)).toBe(true);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.locator('#ability-0').tap();await expect.poll(async()=>(await me(page)).cooldowns[0]!).toBeGreaterThan(0);await capture(page,info,'mobile-controls');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.locator('#pause-open').tap();await expect(page.locator('#pause-dialog')).toBeVisible();const time=(await snapshot(page)).time;await page.waitForTimeout(500);expect((await snapshot(page)).time).toBe(time);await page.locator('#resume-game').tap();await capture(page,info,'mobile-resumed');await attach(page,info,'native-mobile',{before,after:await me(page),viewport:{width:390,height:844},claim:'Chromium native touch emulation, not physical phone hardware'});expect(errors.get(page)).toEqual([]);
 }finally{await context.close();}
});

test('native mouse chords preserve held fire and release through menus',async({page},info)=>{
 test.setTimeout(120_000);await load(page);await low(page);await practice(page);
 const actorId=(await me(page)).id;
 // The authority retains a bounded event window; an old shot being evicted is
 // not a reversal of the fire sequence. Preserve the largest observed receipt.
 let observedShot=0;
 const lastShot=async()=>observedShot=Math.max(observedShot,...(await snapshot(page)).events.filter(event=>event.type==='shot'&&event.actorId===actorId).map(event=>event.id));
 const observations:{step:string;shot:number;cooldown:number}[]=[];
 const record=async(step:string)=>observations.push({step,shot:await lastShot(),cooldown:(await me(page)).fireCooldown});
 const stopped=async()=>{await expect.poll(async()=>(await me(page)).fireCooldown).toBe(0);const shot=await lastShot();await page.waitForTimeout(450);expect(await lastShot()).toBe(shot);};
 await page.mouse.move(300,220);
 try{
  const before=await lastShot();await page.mouse.down({button:'left'});await expect.poll(lastShot).toBeGreaterThan(before);await record('left-down fires');
  await page.mouse.down({button:'right'});const both=await lastShot();await expect.poll(lastShot).toBeGreaterThan(both);await record('right-down while left held still fires');
  await page.mouse.up({button:'right'});const rightReleased=await lastShot();await expect.poll(lastShot).toBeGreaterThan(rightReleased);await record('right release preserves left fire');
  await page.mouse.up({button:'left'});await stopped();await record('left release stops');
  await page.mouse.down({button:'right'});const rightOnly=await lastShot();await page.waitForTimeout(450);expect(await lastShot()).toBe(rightOnly);
  await page.mouse.down({button:'left'});await expect.poll(lastShot).toBeGreaterThan(rightOnly);await record('left-down while right held starts fire');
  await page.mouse.up({button:'left'});await stopped();await record('left release stops while right held');await page.mouse.up({button:'right'});
  await page.mouse.down({button:'left'});const preMenu=await lastShot();await expect.poll(lastShot).toBeGreaterThan(preMenu);await page.keyboard.press('Escape');await expect(page.locator('#pause-dialog')).toBeVisible();
  const paused=await snapshot(page);await page.mouse.up({button:'left'});await page.locator('#resume-game').click();await stopped();expect((await snapshot(page)).time).toBeGreaterThan(paused.time);await record('menu and resume remain neutral');
  await capture(page,info,'native-mouse-chords');await attach(page,info,'native-mouse-chords',{scope:'Real practice authority and native mouse button chords. Authoritative own-shot events prove fire continuity and release; no input/command/state injection. This checks button semantics, not target acquisition at this empty spawn.',observations});expect(errors.get(page)).toEqual([]);
 }finally{await page.mouse.up({button:'left'});await page.mouse.up({button:'right'});}
});

test('two actual browser clients share movement, upgrades and reconnect identity',async({browser},info)=>{
 test.setTimeout(180_000);const a=await browser.newContext({viewport:{width:480,height:400}}),b=await browser.newContext({viewport:{width:480,height:400}});const host=await a.newPage(),guest=await b.newPage();try{
 await load(host);await low(host);await join(host,'Sun QA');const code=(await snapshot(host)).room;await park(host);await load(guest);await low(guest);await pageHero(guest,'arjuna');await join(guest,'Moon QA',code);await park(guest);const hostBefore=await me(host),guestBefore=await me(guest);expect(hostBefore.id).not.toBe(guestBefore.id);expect(hostBefore.team).not.toBe(guestBefore.team);await expect.poll(async()=>(await snapshot(host)).actors.filter(a=>a.kind==='hero'&&!a.bot).length).toBe(2);expect((await snapshot(host)).actors.filter(a=>a.kind==='hero')).toHaveLength(6);
 await activate(host);await host.keyboard.press('KeyB');await host.locator('#buy-power').click();await expect.poll(async()=>(await me(host)).upgrades.power).toBe(1);await host.locator('#upgrades-dialog [data-close]').click();await hold(host,'KeyA',actor=>length(actor,hostBefore)>3);await expect.poll(async()=>length((await snapshot(guest)).actors.find(a=>a.id===hostBefore.id)!,await me(host))).toBeLessThan(.6);
 await park(host);await activate(guest);const peerEventWatermark=Math.max(0,...receivedEvents.get(host)!.keys()),priorGuestCommands=commands.get(guest)!.length;await guest.keyboard.press('KeyQ');await expect.poll(()=>commands.get(guest)!.length).toBeGreaterThan(priorGuestCommands);const castCommand=commands.get(guest)!.at(-1)!;await expect.poll(()=>results.get(guest)!.find(result=>result.id===castCommand.id)?.code).toBe('ABILITY_CAST');await expect.poll(()=>[...receivedEvents.get(host)!.values()].some(e=>e.id>peerEventWatermark&&e.type==='ability'&&e.actorId===guestBefore.id)).toBe(true);await park(guest);await activate(host);await host.keyboard.press('Escape');const pausedPosition=await me(host),clock=(await snapshot(host)).time;await host.keyboard.press('KeyW');await expect.poll(async()=>(await snapshot(host)).time).toBeGreaterThan(clock+.8);expect(length(pausedPosition,await me(host))).toBeLessThan(.05);await host.locator('#resume-game').click();
 await host.keyboard.press('KeyQ');await expect.poll(async()=>(await me(host)).cooldowns[0]!).toBeGreaterThan(0);await host.keyboard.press('Escape');await host.locator('#leave-game').click();await join(host,'Sun QA',code);await activate(host);await host.keyboard.press('KeyE');await expect.poll(async()=>(await me(host)).cooldowns[1]!).toBeGreaterThan(0);expect((await me(host)).id).toBe(hostBefore.id);
 const beforeReconnect=await me(host);await host.goto('/');await expect.poll(async()=>(await snapshot(guest)).actors.find(a=>a.id===hostBefore.id)!.bot).toBe(true);await host.waitForFunction(()=>!!window.__YUGA);await join(host,'Sun QA',code);const afterReconnect=await me(host);expect(afterReconnect.id).toBe(hostBefore.id);expect(afterReconnect.heroId).toBe(beforeReconnect.heroId);expect(afterReconnect.team).toBe(beforeReconnect.team);expect(afterReconnect.upgrades).toEqual(beforeReconnect.upgrades);expect((await snapshot(host)).actors.filter(a=>a.id===hostBefore.id)).toHaveLength(1);await expect.poll(async()=>(await snapshot(guest)).actors.find(a=>a.id===hostBefore.id)!.bot).toBe(false);
 await capture(host,info,'two-client-host');await park(host);await activate(guest);await capture(guest,info,'two-client-guest');await attach(host,info,'real-two-client',{room:code,hostId:hostBefore.id,guestId:guestBefore.id,beforeReconnect,afterReconnect,claim:'Two independent480x400 browser contexts and actual local WebSockets. Inactive peer stays in native Settings while receiving shared authority updates; world captures are sequential. This functional software-render budget does not establish simultaneous rendering performance or public hosting.'});expect(errors.get(host)).toEqual([]);expect(errors.get(guest)).toEqual([]);expect(results.get(host)!.some(r=>r.ok&&r.code==='UPGRADED')).toBe(true);
 }finally{await info.attach('two-client-command-and-state-diagnostics',{body:JSON.stringify({host:{observation:await inputObservation(host).catch(()=>null),browserDispatch:await host.evaluate(()=>({now:Date.now(),probe:(window as unknown as{__yugaSocketProbe:unknown}).__yugaSocketProbe})).catch(()=>null),wire:wireProbes.get(host),pageErrors:errors.get(host),commands:commands.get(host),results:results.get(host)},guest:{observation:await inputObservation(guest).catch(()=>null),browserDispatch:await guest.evaluate(()=>({now:Date.now(),probe:(window as unknown as{__yugaSocketProbe:unknown}).__yugaSocketProbe})).catch(()=>null),wire:wireProbes.get(guest),pageErrors:errors.get(guest),commands:commands.get(guest),results:results.get(guest)},receivedPeerAbilities:[...(receivedEvents.get(host)?.values()??[])].filter(event=>event.type==='ability')},null,2),contentType:'application/json'});await a.close();await b.close();}
});
async function pageHero(page:Page,id:string){await page.locator(`[data-hero="${id}"]`).click();}

test('labelled finished-state socket fixture renders results and fresh replay',async({page},info)=>{
 let connections=0;await page.routeWebSocket('**/ws',socket=>{const serial=++connections;socket.onMessage(raw=>{const message=JSON.parse(String(raw));if(message.type!=='join')return;const sim=new ArenaSimulation({room:`FIXTURE-${serial}`,seed:5,duration:serial===1?1:480});sim.addPlayer('fixture-player','Fixture hero',message.heroId,'sun');if(serial===1)for(let i=0;i<21;i++)sim.step(.05);socket.send(JSON.stringify({type:'welcome',protocol:YUGA_PROTOCOL,id:'fixture-player',room:sim.room,token:'a'.repeat(48),snapshot:sim.snapshot()}));});});
 await load(page);await low(page);await join(page,'Fixture hero');await expect(page.locator('#result-dialog')).toBeVisible();await expect(page.locator('#scoreboard .score-row')).toHaveCount(7);await capture(page,info,'fixture-result');await page.locator('#play-again').click();await ready(page);await expect(page.locator('#result-dialog')).toBeHidden();expect((await snapshot(page)).phase).toBe('playing');expect((await snapshot(page)).room).toBe('FIXTURE-2');expect((await me(page)).upgrades).toEqual({power:0,vitality:0,tempo:0});expect((await me(page)).credits).toBe(180);expect(connections).toBe(2);await attach(page,info,'labelled-result-fixture',{claim:'Mocked WebSocket and shortened simulation fixture verifies result/replay presentation only; no native match victory or real server claim'});expect(errors.get(page)).toEqual([]);
});

test('native complete eight-minute practice and fresh replay [release soak]',async({page},info)=>{
 test.skip(process.env.YUGA_FULL_MATCH!=='1','Explicit bounded release soak; routine native combat and result fixture run separately.');
 test.setTimeout(720_000);await load(page);await low(page);await practice(page);
 const began=Date.now(),initial=await snapshot(page);
 // Use the same conservative approach distance as the accepted native combat
 // case. The full authority clock remains unchanged, including death/respawn.
 await hold(page,'KeyA',actor=>actor.x>4);await hold(page,'KeyW',actor=>actor.z>-35,30_000);
 const roles=new Set<string>(),archetypes=new Set<string>(),castMechanics=new Set<string>(),campStates=new Set<string>();
 const peaks={actors:0,neutrals:0,livingCamps:0,shards:0};await page.keyboard.down('KeyF');
 try{
  await expect.poll(async()=>{
   const state=await snapshot(page);
   for(const actor of state.actors){if(actor.minionRole)roles.add(actor.minionRole);if(actor.unitArchetype)archetypes.add(actor.unitArchetype);if(actor.cast)castMechanics.add(actor.cast.mechanic);}
   for(const neutral of state.neutrals)campStates.add(`${neutral.campId}:${neutral.state}`);
   peaks.actors=Math.max(peaks.actors,state.actors.length);peaks.neutrals=Math.max(peaks.neutrals,state.neutrals.length);peaks.livingCamps=Math.max(peaks.livingCamps,state.neutrals.filter(neutral=>neutral.health>0).length);peaks.shards=Math.max(peaks.shards,state.goldShards.length);
   return state.phase;
  },{timeout:640_000,intervals:[1000]}).toBe('finished');
  await expect(page.locator('#result-dialog')).toBeVisible();
 }finally{await page.keyboard.up('KeyF');}
 expect(roles.has('siege')).toBe(true);for(const archetype of ['soldier','city-watch','minister','king'])expect(archetypes.has(archetype)).toBe(true);expect(peaks.livingCamps).toBe(4);
 const final=await snapshot(page),finishedAfterMs=Date.now()-began;expect(final.phase).toBe('finished');await capture(page,info,'native-complete-match');
 await page.locator('#play-again').click();await ready(page);expect((await snapshot(page)).phase).toBe('playing');expect((await snapshot(page)).time).toBeLessThan(5);expect((await me(page)).upgrades).toEqual({power:0,vitality:0,tempo:0});
 const replayRig=()=>page.evaluate(()=>(window.__YUGA as unknown as {assets():{instances:{id:string;transitions:Record<string,number>}[]}}).assets().instances.find(i=>i.id===window.__YUGA.playerId())!);
 await page.keyboard.down('KeyF');try{await expect.poll(async()=>(await replayRig()).transitions.fire||0).toBeGreaterThan(0);}finally{await page.keyboard.up('KeyF');}
 await page.keyboard.press('KeyQ');await expect.poll(async()=>(await replayRig()).transitions.cast1||0).toBeGreaterThan(0);
 await attach(page,info,'native-full-match',{initialTime:initial.time,finishedAfterMs,elapsedIncludingReplayMs:Date.now()-began,observedMinionRoles:[...roles],observedUnitArchetypes:[...archetypes],observedCastMechanics:[...castMechanics],observedCampStates:[...campStates],observedEntityPeaks:peaks,final,claim:'Normal wall-clock practice simulation from fresh roster; native approach and held fire, no timer/position/command injection. Read-only counts are functional coverage, not a performance/capacity measurement.'});
 expect(errors.get(page)).toEqual([]);
});


test('native two-player Dawn Volley received windup and lateral movement evades it',async({browser},info)=>{
 test.setTimeout(240_000);
 const server=await createArenaServer({port:0,host:'127.0.0.1',simulation:{botsPerTeam:0}});
 const address=server.address;if(!address||typeof address==='string')throw new Error('Test listener unavailable');
 const endpoint=`http://127.0.0.1:${address.port}`;
 const a=await browser.newContext({viewport:{width:480,height:400}}),b=await browser.newContext({viewport:{width:480,height:400}});
 const host=await a.newPage(),guest=await b.newPage();
 const observedHits=new Map<number,{id:number;actorId:string;targetId?:string;time:number}>();
 let casterId='',dodgerId='',armed=false,baselineX=0;
 let castReceipt:{snapshotTime:number;cast:NonNullable<Actor['cast']>}|undefined;
 let firstDodgeMovement:{time:number;x:number;phase:string|undefined}|undefined;
 let nativeDodge:Promise<void>|undefined,nativeDodgeError:string|undefined;
 const dodgePath:{time:number;x:number;z:number;lateralClearance:number;projectiles:number}[]=[];
 try{
  await load(host);await low(host);await practice(host);await host.keyboard.press('Escape');await host.locator('#leave-game').click();
  await load(guest);await low(guest);await practice(guest);await guest.keyboard.press('Escape');await guest.locator('#leave-game').click();
  await host.locator('#online-open').click();await host.locator('#server-address').fill(endpoint);await host.locator('#player-name').fill('Native caster');await host.locator('#join-room').click();await ready(host);
  const code=(await snapshot(host)).room;casterId=(await me(host)).id;
  guest.on('websocket',socket=>socket.on('framereceived',frame=>{
   let message:{type:string;snapshot?:ArenaSnapshot};try{message=JSON.parse(String(frame.payload));}catch{return;}
   if(message.type!=='snapshot'||!message.snapshot)return;
   const state=message.snapshot;
   for(const event of state.events)if(event.type==='hit')observedHits.set(event.id,{id:event.id,actorId:event.actorId,targetId:event.targetId,time:event.time});
   const caster=state.actors.find(actor=>actor.id===casterId),dodger=state.actors.find(actor=>actor.id===dodgerId);
   if(armed&&!castReceipt&&caster?.cast?.mechanic==='dawn-volley'&&caster.cast.phase==='windup'){
    castReceipt={snapshotTime:state.time,cast:{...caster.cast}};
    // React with an ordinary browser key to the peer's received windup. Retaining the packet
    // avoids falsely requiring a one-second phase to remain current after sequential polls.
    nativeDodge=guest.keyboard.down('KeyA').catch(error=>{nativeDodgeError=String(error);});
   }
   if(castReceipt&&dodger)dodgePath.push({time:state.time,x:dodger.x,z:dodger.z,lateralClearance:Math.abs(Math.cos(castReceipt.cast.yaw)*(dodger.x-castReceipt.cast.origin.x)-Math.sin(castReceipt.cast.yaw)*(dodger.z-castReceipt.cast.origin.z)),projectiles:state.projectiles.filter(p=>p.owner===casterId).length});
   if(castReceipt&&!firstDodgeMovement&&dodger&&baselineX-dodger.x>.15)firstDodgeMovement={time:state.time,x:dodger.x,phase:caster?.cast?.phase};
  }));
  await guest.locator('#online-open').click();await guest.locator('#server-address').fill(endpoint);await guest.locator('#room-code').fill(code);await guest.locator('#player-name').fill('Native dodger');await guest.locator('#join-room').click();await ready(guest);
  const initialHost=await me(host),initialGuest=await me(guest);dodgerId=initialGuest.id;
  expect(initialHost.team).toBe('sun');expect(initialGuest.team).toBe('moon');
  // Natural x=-3 spawn clears the central tower; no latency-sensitive lateral detour.
  await park(guest);await activate(host);await hold(host,'KeyW',p=>p.z>-12,40_000);
  await park(host);await activate(guest);await hold(guest,'KeyW',p=>p.z<12,40_000);await park(guest);
  await activate(host);const caster=await me(host),target=await me(guest);
  expect(caster.health).toBeGreaterThan(0);expect(target.health).toBeGreaterThan(0);
  await nativeYaw(host,Math.atan2(target.x-caster.x,target.z-caster.z));
  await host.keyboard.press('KeyT');await expect.poll(()=>host.evaluate(()=>window.__YUGA.metrics().targetId)).toBe(target.id);
  await expect(host.locator('#target-label')).toContainText('Native dodger');
  await host.keyboard.press('Escape');expect(await host.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();
  await host.locator('#resume-game').click();await host.keyboard.press('KeyT');await expect.poll(()=>host.evaluate(()=>window.__YUGA.metrics().targetId)).toBe(target.id);
  await host.keyboard.press('KeyJ');expect(await host.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();
  await nativeYaw(host,Math.atan2(target.x-caster.x,target.z-caster.z));
  await activate(guest);const beforeDodge=await me(guest);baselineX=beforeDodge.x;armed=true;
  const startTime=(await snapshot(host)).time;await host.keyboard.press('KeyR');
  await expect.poll(()=>!!castReceipt,{intervals:[30,50]}).toBe(true);await nativeDodge;
  expect(nativeDodgeError).toBeUndefined();
  // Keep dodging across the complete three-arrow envelope. Four metres can
  // still lie inside the outer arrow plus the combined actor/projectile radii.
  const volleyRange=HEROES.find(hero=>hero.id==='rama')!.abilities[2].range;
  try{await expect.poll(async()=>(await snapshot(guest)).time,{timeout:8_000,intervals:[50,100]}).toBeGreaterThan(castReceipt!.cast.releaseAt+volleyRange/62);expect(beforeDodge.x-(await me(guest)).x).toBeGreaterThan(4);}finally{await guest.keyboard.up('KeyA');}
  await expect.poll(()=>!!firstDodgeMovement,{intervals:[50,100]}).toBe(true);
  expect(firstDodgeMovement!.time).toBeLessThan(castReceipt!.cast.releaseAt);
  expect(firstDodgeMovement!.phase).toBe('windup');
  await expect.poll(async()=>(await snapshot(host)).time,{intervals:[50,100]}).toBeGreaterThan(castReceipt!.cast.releaseAt+1);
  const afterDodge=await me(guest);
  expect([...observedHits.values()].filter(event=>event.time>=startTime&&event.actorId===caster.id&&event.targetId===target.id)).toEqual([]);
  expect(results.get(host)!.some(result=>result.ok&&result.code==='ABILITY_CAST')).toBe(true);
  await capture(guest,info,'native-volley-evade');
  await attach(host,info,'native-windup-evade',{scope:'Two real browser clients and real local server without hero bots; lane waves run. Native movement/aim/R; native dodge key reacts to the peer received windup. First authoritative lateral movement must precede release. No actor-position/health/time injection. Snapshot timing does not itself verify every telegraph pixel or human reaction speed.',initialHost,initialGuest,caster,target,castReceipt,firstDodgeMovement,beforeDodge,afterDodge,dodgePath,observedTargetHits:[...observedHits.values()].filter(event=>event.actorId===caster.id&&event.targetId===target.id)});
  expect(errors.get(host)).toEqual([]);expect(errors.get(guest)).toEqual([]);
 }finally{await info.attach('native-dodge-diagnostics',{body:JSON.stringify({castReceipt,firstDodgeMovement,dodgePath,observedHits:[...observedHits.values()],hostResults:results.get(host),guestObservation:await inputObservation(guest).catch(()=>null)},null,2),contentType:'application/json'});armed=false;await nativeDodge;await guest.keyboard.up('KeyA').catch(()=>{});await a.close();await b.close();await server.close();}
});

test('labelled target fixture verifies native lock, manual release, settings and cover rejection',async({page},info)=>{
 test.setTimeout(180_000);let fixture:ArenaSimulation|undefined,send:(()=>void)|undefined,timer:ReturnType<typeof setInterval>|undefined;const inputs:{time:number;yaw:number;fire:boolean}[]=[];
 await page.routeWebSocket('**/ws',socket=>socket.onMessage(raw=>{const message=JSON.parse(String(raw));if(message.type==='join'){
  fixture=new ArenaSimulation({room:'LOCK-FIXTURE',seed:1,botsPerTeam:0});const actor=fixture.addPlayer('lock-local','Lock fixture','rama','sun'),target=fixture.addPlayer('lock-rival','Visible rival','rama','moon');actor.x=5;actor.z=-28;target.x=5;target.z=-10;
  send=()=>{fixture!.tick++;socket.send(JSON.stringify({type:'snapshot',snapshot:fixture!.snapshot()}));};socket.send(JSON.stringify({type:'welcome',protocol:YUGA_PROTOCOL,id:actor.id,room:fixture.room,token:'c'.repeat(48),snapshot:fixture.snapshot()}));timer=setInterval(()=>send?.(),100);
 }else if(message.type==='input'&&fixture){const actor=fixture.actors.get('lock-local')!;actor.yaw=message.yaw;actor.lastInputSeq=message.seq;inputs.push({time:Date.now(),yaw:message.yaw,fire:message.fire});}}));
 try{
  await load(page);await low(page);await join(page,'Lock fixture');await page.keyboard.press('KeyT');await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().targetId)).toBe('lock-rival');await expect(page.locator('#target-label')).toContainText('Visible rival');await capture(page,info,'fixture-visible-target-lock');
  await page.keyboard.press('Escape');expect(await page.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();await expect(page.locator('#target-label')).toBeHidden();await page.locator('#target-assist').uncheck();await page.locator('#resume-game').click();await page.keyboard.press('KeyT');expect(await page.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();await page.keyboard.press('Escape');await page.locator('#target-assist').check();await page.locator('#resume-game').click();
  await page.locator('#arena').click({button:'right',position:{x:400,y:220}});await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().targetId)).toBe('lock-rival');expect(inputs.every(i=>!i.fire)).toBe(true);await page.keyboard.press('KeyJ');expect(await page.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();await nativeYaw(page,0);await page.keyboard.press('KeyT');await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().targetId)).toBe('lock-rival');
  fixture!.actors.get('lock-rival')!.x=35;fixture!.actors.get('lock-rival')!.z=-28;send!();await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();await nativeYaw(page,Math.PI/2);await page.keyboard.press('KeyT');expect(await page.evaluate(()=>window.__YUGA.metrics().targetId)).toBeNull();await expect(page.locator('#target-label')).toBeHidden();await capture(page,info,'fixture-target-behind-cover');
  await attach(page,info,'labelled-target-cover-fixture',{scope:'Mocked WebSocket and explicit actor positions isolate UI targeting through the real map building at x20,z-28. Native T/right-click/manual aim/settings; no real movement, combat or multiplayer authority claim.',inputs,cover:{actor:{x:5,z:-28},target:{x:35,z:-28},distance:30},fireWasNeverRequested:inputs.every(i=>!i.fire)});expect(errors.get(page)).toEqual([]);
 }finally{if(timer)clearInterval(timer);}
});
