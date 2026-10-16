import { YUGA_PROTOCOL } from '../shared/types';
import { test, expect, type Page, type TestInfo } from '@playwright/test';
import { HEROES } from '../shared/heroes';
import { ArenaSimulation } from '../shared/simulation';
import type { ArenaSnapshot } from '../shared/types';

const clips=['idle','run','fire','cast','jump','defeat','cast1','cast2','cast3'];
type Instance={id:string;heroId:string;url:string;loaded:boolean;fallback:boolean;skinned:boolean;skeletons:number[];bones:number;clips:string[];state:string;action:string;transitions:Record<string,number>;animationTime:number;pose:number[]};
type Assets={assets:{heroId:string;state:string;url:string;animations:string[];skinnedPrimitives:number;triangles:number;materials:number}[];instances:Instance[];fallback:{id:string;heroId:string}[]};
const assets=(page:Page)=>page.evaluate(()=>(window.__YUGA as unknown as {assets():Assets}).assets());
const local=(page:Page)=>page.evaluate(()=>(window.__YUGA as unknown as {assets():Assets}).assets().instances.find(i=>i.id===window.__YUGA.playerId())!);
async function setup(page:Page){
 if(process.env.CI||process.env.YUGA_SOFTWARE_RENDERING==='1')await page.addInitScript(()=>{
  if(window.__yugaQAFrameCap)return;window.__yugaQAFrameCap=true;const native=requestAnimationFrame.bind(window),queue=new Map<number,FrameRequestCallback>();let next=0,queued=false,dispatching=false,last=performance.now()-100,timer:number|undefined;
  const schedule=()=>{if(!queue.size||queued||dispatching||timer!==undefined)return;timer=window.setTimeout(()=>{timer=undefined;queued=true;native(time=>{queued=false;dispatching=true;for(const id of[...queue.keys()]){const callback=queue.get(id);queue.delete(id);if(callback)try{callback(time);}catch(error){window.setTimeout(()=>{throw error;},0);}}dispatching=false;last=performance.now();schedule();});},Math.max(0,100-performance.now()+last));};window.requestAnimationFrame=callback=>{const id=++next;queue.set(id,callback);schedule();return id;};window.cancelAnimationFrame=id=>{queue.delete(id);};
 });
 await page.goto('/');await page.waitForFunction(()=>!!window.__YUGA);await page.locator('#lobby-settings').click();await page.locator('#quality').selectOption('low');await page.locator('#resume-game').click();
}
async function observeStartupFailures(page:Page){
 await page.evaluate(()=>{
  const history:unknown[]=[];let previous='';
  const record=()=>{const element=document.getElementById('global-error');if(!element)return;const value=JSON.stringify({text:element.textContent,hidden:element.hidden});if(value===previous)return;previous=value;history.push({at:performance.now(),kind:'global-error',text:element.textContent,hidden:element.hidden});if(history.length>40)history.shift();};
  const observer=new MutationObserver(record);observer.observe(document.getElementById('global-error')!,{attributes:true,childList:true,subtree:true,characterData:true});record();
  const context=(event:Event)=>{history.push({at:performance.now(),kind:event.type,canvas:(event.target as HTMLElement)?.id});if(history.length>40)history.shift();};
  document.addEventListener('webglcontextlost',context,true);document.addEventListener('webglcontextrestored',context,true);
  Object.defineProperty(window,'__yugaStartupHistory',{configurable:true,value:()=>history.slice()});
  Object.defineProperty(window,'__yugaStopStartupHistory',{configurable:true,value:()=>{observer.disconnect();document.removeEventListener('webglcontextlost',context,true);document.removeEventListener('webglcontextrestored',context,true);return history.slice();}});
 });
}
async function startupFailureState(page:Page){
 return page.evaluate(()=>{
  const api=window.__YUGA as unknown as{snapshot():ArenaSnapshot|undefined;playerId():string;metrics():unknown;assets():Assets|undefined;showcase():unknown};
  const snapshot=api.snapshot(),id=api.playerId(),models=api.assets();
  const ui=Object.fromEntries(['global-error','status-line','loading','loading-copy','lobby','hud'].map(id=>{const e=document.getElementById(id)!;return[id,{hidden:e.hidden,inert:e.inert,text:['global-error','status-line','loading-copy'].includes(id)?e.textContent:undefined}];}));
  return{at:performance.now(),visibility:document.visibilityState,focus:document.activeElement?.id,dialogs:[...document.querySelectorAll('dialog[open]')].map(e=>e.id),ui,metrics:api.metrics(),playerId:id,snapshot:snapshot?{room:snapshot.room,tick:snapshot.tick,time:snapshot.time,phase:snapshot.phase,self:snapshot.actors.find(a=>a.id===id),actorIds:snapshot.actors.map(a=>a.id)}:null,models:models?{assets:models.assets.map(a=>({heroId:a.heroId,state:a.state,url:a.url,error:(a as typeof a&{error?:string}).error})),instances:models.instances.map(i=>({id:i.id,heroId:i.heroId,loaded:i.loaded,state:i.state,action:i.action})),fallback:models.fallback}:null,history:(window as unknown as{__yugaStartupHistory():unknown[]}).__yugaStartupHistory()};
 });
}
async function frame(page:Page){await page.evaluate(()=>new Promise<void>(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r()))));}
async function capture(page:Page,info:TestInfo,name:string){await frame(page);await page.screenshot({path:info.outputPath(`${name}.png`)});}
async function transition(page:Page,key:string,state:string){
 const before=await local(page),count=before.transitions[state]||0,slot=Number(state.at(-1))-1;
 const started=await page.evaluate(({slot})=>{
  const samples:unknown[]=[],events=new Map<number,unknown>();
  const observe=()=>{const snapshot=window.__YUGA.snapshot()!,actor=snapshot.actors.find(a=>a.id===window.__YUGA.playerId())!,metrics=window.__YUGA.metrics(),model=(window.__YUGA as unknown as{assets():Assets}).assets().instances.find(i=>i.id===actor.id)!;
   if(samples.length<400)samples.push({at:performance.now(),time:snapshot.time,tick:snapshot.tick,frames:metrics.frames,maxFrameMs:metrics.maxFrameMs,health:actor.health,cooldown:actor.cooldowns[slot],cast:actor.cast??null,state:model.state,action:model.action,transitions:{...model.transitions}});
   for(const event of snapshot.events)if(event.actorId===actor.id&&event.type==='ability')events.set(event.id,event);
  };
  observe();const watermark=Math.max(0,...snapshotEvents());
  function snapshotEvents(){return window.__YUGA.snapshot()!.events.map(event=>event.id);}
  const timer=window.setInterval(observe,50);Object.defineProperty(window,'__yugaCastObservation',{configurable:true,value:()=>{clearInterval(timer);observe();return{samples,events:[...events.values()]};}});
  return{watermark,time:window.__YUGA.snapshot()!.time,frames:window.__YUGA.metrics().frames};
 },{slot});
 let observation:unknown;
 try{
  await page.keyboard.press(key);
  await expect.poll(()=>page.evaluate(slot=>window.__YUGA.snapshot()!.actors.find(a=>a.id===window.__YUGA.playerId())!.cooldowns[slot]!,slot),{message:`${before.heroId} ${key} must be accepted by practice authority`}).toBeGreaterThan(0);
  await expect.poll(async()=>(await local(page)).transitions[state]||0,{message:`${before.heroId} ${key} must produce actual ${state} animation`}).toBeGreaterThan(count);
 }catch(error){observation=await page.evaluate(()=>(window as unknown as{__yugaCastObservation():unknown}).__yugaCastObservation());throw new Error(`Native animation failure ${before.heroId} ${key}/${state}: ${JSON.stringify({before:{state:before.state,action:before.action,transitions:before.transitions},after:await local(page),started,observation})}`,{cause:error});}
 finally{observation??=await page.evaluate(()=>(window as unknown as{__yugaCastObservation():unknown}).__yugaCastObservation());}
 return{key,state,started,observation,after:await local(page)};
}

test('gallery rapid selection and close survives delayed real GLB loads',async({page},info)=>{
 test.setTimeout(180_000);const errors:string[]=[],consoleErrors:string[]=[];page.on('pageerror',e=>errors.push(e.stack||e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);let delayed=0,completed=0;
 await page.route(/\/heroes\/[^/?]+\.glb(?:\?.*)?$/,async route=>{if(route.request().resourceType()==='script'){await route.continue();return;}const wait=delayed<2;if(wait){delayed++;await held;}await route.continue();if(wait)completed++;});
 try{
  await setup(page);await page.locator('[data-hero="rama"]').click();await page.locator('#inspect-hero').click();await expect.poll(()=>delayed).toBe(1);await page.locator('#hero-next').click();await expect.poll(()=>delayed).toBe(2);await page.locator('#hero-next').click();await page.locator('#hero-dialog [data-close]').click();await expect(page.locator('#hero-dialog')).toBeHidden();release();await expect.poll(()=>completed).toBe(2);await frame(page);
  await page.locator('[data-hero="ulupi"]').click();await page.locator('#inspect-hero').click();await expect(page.locator('#showcase-status')).toContainText('Drag to rotate',{timeout:60_000});await page.locator('[data-clip="run"]').click();const diagnostic=()=>page.evaluate(()=>(window.__YUGA as unknown as {showcase():{hero:{heroId:string;state:string;loaded:boolean;fallback:boolean;pose:number[]}}}).showcase());await expect.poll(async()=>(await diagnostic()).hero.state).toBe('run');expect((await diagnostic()).hero).toMatchObject({heroId:'ulupi',loaded:true,fallback:false});await capture(page,info,'ulupi-gallery-run');await page.locator('#hero-dialog [data-close]').click();await frame(page);expect(errors).toEqual([]);expect(consoleErrors).toEqual([]);
  await info.attach('gallery-delayed-load-lifecycle',{body:JSON.stringify({scope:'Only two real GLB network requests were deliberately delayed; ordinary gallery clicks, actual assets/PlayCanvas, then close and reopen. No gameplay/state injection.',delayed,completed,errors,consoleErrors},null,2),contentType:'application/json'});
 }finally{release();}
});

test('cancel delayed actual match assets with Escape and Back, then restart cleanly',async({page},info)=>{
 test.setTimeout(180_000);const errors:string[]=[],consoleErrors:string[]=[];
 page.on('pageerror',error=>errors.push(error.stack||error.message));page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text());});
 type ColdSample={at:number;time:number;ready:boolean;loading:boolean;renderReady:boolean;warmFrames:number;hudInert:boolean};
 let coldSamples:ColdSample[]=[];
 let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);let delayed=0;
 await page.route(/\/heroes\/[^/?]+\.glb(?:\?.*)?$/,async route=>{
  if(route.request().resourceType()==='script'){await route.continue();return;}
  if(!delayed){delayed++;await gate;}await route.continue();
 });
 try{
  await setup(page);await page.locator('#practice-play').click();await expect.poll(()=>delayed).toBe(1);await expect(page.locator('#loading-back')).toBeFocused();
  await page.keyboard.press('Escape');await expect(page.locator('#lobby')).toBeVisible();await expect(page.locator('#loading')).toBeHidden();
  await page.locator('#practice-play').click();await expect(page.locator('#loading-back')).toBeFocused();await page.locator('#loading-back').click();await expect(page.locator('#lobby')).toBeVisible();
  release();await expect.poll(async()=>(await assets(page)).assets.filter(asset=>asset.state==='ready').length,{timeout:120_000}).toBe(14);await frame(page);
  expect(await page.evaluate(()=>window.__YUGA.snapshot())).toBeUndefined();await expect(page.locator('#hud')).toBeHidden();await expect(page.locator('#loading')).toBeHidden();await expect(page.locator('#lobby')).toBeVisible();
  await page.evaluate(()=>{
   const samples:ColdSample[]=[];const timer=window.setInterval(()=>{const state=window.__YUGA.snapshot();if(!state||samples.length>=300)return;const m=(window.__YUGA as unknown as{metrics():{ready:boolean;loading:boolean;renderReady:boolean;warmFrames:number}}).metrics();samples.push({at:performance.now(),time:state.time,...m,hudInert:document.getElementById('hud')!.inert});},10);
   Object.defineProperty(window,'__yugaColdObservation',{value:()=>{clearInterval(timer);return samples;}});
  });
  await page.locator('#practice-play').click();await expect(page.locator('#loading')).toBeHidden({timeout:120_000});await expect.poll(()=>page.evaluate(()=>window.__YUGA.snapshot()?.room)).toBe('PRACTICE');expect((await assets(page)).fallback).toEqual([]);
  coldSamples=await page.evaluate(()=>(window as unknown as{__yugaColdObservation():ColdSample[]}).__yugaColdObservation());
  const preparing=coldSamples.filter(sample=>sample.loading&&!sample.renderReady);
  expect(preparing.length,'Observe the actual scene before its two required renders').toBeGreaterThan(0);
  for(const sample of preparing){expect(sample.time).toBe(0);expect(sample.ready).toBe(false);expect(sample.hudInert).toBe(true);expect(sample.warmFrames).toBeLessThan(2);}
  const finalMetrics=await page.evaluate(()=>(window.__YUGA as unknown as{metrics():{ready:boolean;loading:boolean;renderReady:boolean;warmFrames:number}}).metrics());expect(finalMetrics).toMatchObject({ready:true,loading:false,renderReady:true,warmFrames:2});
  await page.keyboard.press('KeyQ');await expect.poll(()=>page.evaluate(()=>window.__YUGA.snapshot()!.actors.find(actor=>actor.id===window.__YUGA.playerId())!.cooldowns[0])).toBeGreaterThan(0);
  await capture(page,info,'cancelled-load-restart');expect(errors).toEqual([]);expect(consoleErrors).toEqual([]);
  await info.attach('delayed-match-load-cancellation',{body:JSON.stringify({scope:'A real binary GLB request was delayed. Native Escape and Back cancel two loading attempts; releasing the asset may populate cache but must not start either canceled match. A third native start enters ordinary practice. Read-only polling proves its first scene remains paused at time0 with controls inert until two actual postrenders; native Q then works. No simulation/input/clock mutation.',delayed,coldSamples,errors,consoleErrors},null,2),contentType:'application/json'});
 }finally{release();}
});

test('labelled synchronous gallery-close and practice-start UI lifecycle keeps the owning arena app',async({page},info)=>{
 test.setTimeout(180_000);const errors:string[]=[];page.on('pageerror',error=>errors.push(error.stack||error.message));
 await page.setViewportSize({width:480,height:400});await setup(page);await observeStartupFailures(page);
 try{
  await page.locator('#practice-play').click();await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().ready),{timeout:120_000}).toBe(true);
  await page.keyboard.press('Escape');await page.locator('#leave-game').click();await expect(page.locator('#lobby')).toBeVisible();
  await page.locator('[data-hero="arjuna"]').click();await page.locator('#inspect-hero').click();await expect(page.locator('#showcase-status')).toContainText('Drag to rotate',{timeout:60_000});
  // Deliberately run the real handlers within one task so no arena RAF can
  // repair ambient engine ownership between gallery disposal and startup.
  await page.evaluate(()=>{document.querySelector<HTMLButtonElement>('#hero-dialog [data-close]')!.click();document.querySelector<HTMLButtonElement>('#practice-play')!.click();});
  await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().ready),{timeout:30_000}).toBe(true);
  await expect.poll(async()=>(await local(page))?.heroId).toBe('arjuna');
  expect(await page.evaluate(()=>window.__YUGA.snapshot()!.actors.find(a=>a.id===window.__YUGA.playerId())!.heroId)).toBe('arjuna');
  expect((await local(page)).loaded).toBe(true);expect((await assets(page)).fallback).toEqual([]);expect(errors).toEqual([]);
 }catch(error){throw new Error(`Synchronous gallery/start lifecycle failed: ${JSON.stringify({state:await startupFailureState(page),errors})}`,{cause:error});}
 finally{
  const state=await startupFailureState(page);await page.evaluate(()=>(window as unknown as{__yugaStopStartupHistory():unknown[]}).__yugaStopStartupHistory());
  await info.attach('synchronous-gallery-start-lifecycle',{body:JSON.stringify({scope:'Labelled synchronous UI lifecycle fixture: ordinary Practice and gallery preparation, then two real DOM button click handlers in one JS task. This fixes event ordering only; no engine/global/authority/clock/position mutation and no native-gameplay timing claim.',state,errors},null,2),contentType:'application/json'});
 }
});

test('all fourteen real GLBs spawn and respond to native movement, fire, three casts and jump',async({page},info)=>{
 test.setTimeout(600_000);const errors:string[]=[],consoleErrors:string[]=[],failed:string[]=[],requests=new Set<string>();page.on('pageerror',e=>errors.push(e.stack||e.message));page.on('console',message=>{if(message.type()==='error'&&consoleErrors.length<100)consoleErrors.push(message.text());});page.on('requestfailed',r=>{if(failed.length<100)failed.push(`${new URL(r.url()).pathname}: ${r.failure()?.errorText}`);});page.on('response',r=>{if(/\.glb(?:\?|$)/.test(r.url())){requests.add(r.url());if(!r.ok())failed.push(`${r.status()} ${new URL(r.url()).pathname}`);}});
 // A bounded software-rendering viewport keeps the one-second authoritative
 // windup observable. It does not change its clock or replay an expired cast.
 await page.setViewportSize({width:480,height:400});
 await setup(page);await observeStartupFailures(page);expect(HEROES).toHaveLength(14);await expect(page.locator('[data-hero]')).toHaveCount(14);const evidence:unknown[]=[];
 try{for(const hero of HEROES){
  try{
   await page.locator(`[data-hero="${hero.id}"]`).click();await page.locator('#inspect-hero').click();await expect(page.locator('#showcase-status')).toContainText('Drag to rotate',{timeout:60_000});await capture(page,info,`hero-${hero.id}-gallery`);await page.locator('#hero-dialog [data-close]').click();await page.locator('#practice-play').click();await expect(page.locator('#loading')).toBeHidden({timeout:120_000});await expect.poll(async()=>(await local(page))?.heroId,{timeout:30_000}).toBe(hero.id);
  }catch(error){
   const diagnostic={heroId:hero.id,completedHeroes:evidence.length,state:await startupFailureState(page),errors,consoleErrors,failed};
   await info.attach('native-start-failure',{body:JSON.stringify(diagnostic,null,2),contentType:'application/json'});
   throw new Error(`Native start failed: ${JSON.stringify(diagnostic)}`,{cause:error});
  }
  const diagnostic=await assets(page);expect(diagnostic.assets).toHaveLength(14);expect(diagnostic.assets.every(a=>a.state==='ready'&&a.skinnedPrimitives>0&&clips.every(c=>a.animations.includes(c)))).toBe(true);expect(diagnostic.fallback).toEqual([]);const model=await local(page);expect(model).toMatchObject({loaded:true,fallback:false,skinned:true});expect(model.bones).toBeGreaterThan(5);expect(model.skeletons.length).toBeGreaterThan(0);expect(model.url).toContain('.glb');await capture(page,info,`hero-${hero.id}-spawn`);
  await page.keyboard.down('KeyW');try{await expect.poll(async()=>(await local(page)).state).toBe('run');await expect.poll(async()=>(await local(page)).pose.some((v,i)=>Math.abs(v-(model.pose[i]||0))>.0001)).toBe(true);}finally{await page.keyboard.up('KeyW');}await expect.poll(async()=>(await local(page)).state).toBe('idle');const shot=(await local(page)).transitions.fire||0;await page.keyboard.down('KeyF');try{await expect.poll(async()=>(await local(page)).transitions.fire||0).toBeGreaterThan(shot);}finally{await page.keyboard.up('KeyF');}
  const casts=[];for(const [slot,key]of ['KeyQ','KeyE','KeyR'].entries()){casts.push(await transition(page,key,`cast${slot+1}`));await expect.poll(()=>page.evaluate(()=>!window.__YUGA.snapshot()!.actors.find(a=>a.id===window.__YUGA.playerId())!.cast)).toBe(true);}
  const jumps=(await local(page)).transitions.jump||0;await page.keyboard.down('Space');try{await expect.poll(async()=>(await local(page)).transitions.jump||0).toBeGreaterThan(jumps);}finally{await page.keyboard.up('Space');}await capture(page,info,`hero-${hero.id}-action`);const after=await local(page);for(const state of['idle','run','fire','cast1','cast2','cast3','jump'])expect(after.transitions[state]).toBeGreaterThan(0);evidence.push({heroId:hero.id,before:model,casts,after});await page.keyboard.press('Escape');await page.locator('#leave-game').click();await expect(page.locator('#lobby')).toBeVisible();
 }
 expect(failed).toEqual([]);expect(requests.size).toBeGreaterThanOrEqual(14);expect(errors).toEqual([]);
 }finally{
  const startupHistory=await page.evaluate(()=>(window as unknown as{__yugaStopStartupHistory():unknown[]}).__yugaStopStartupHistory());
  await info.attach('fourteen-native-asset-instances',{body:JSON.stringify({scope:'Native fresh practice for each hero at480x400 with existing maximum10fps software-render scheduling. This is a functional render budget, not a performance fix/certification. All native commands must be accepted and produce actual model transitions; read-only frame/authority-clock samples retain timing. No health/time/position mutation. Larger960x640 earlier passes and later missed1s-cast failure remain separate historical evidence. Samples do not establish every animation frame or visual approval.',requests:[...requests],errors,consoleErrors,failed,startupHistory,evidence},null,2),contentType:'application/json'});
 }
});

test('labelled animation snapshot fixtures exercise defeat, recovery and independent duplicate-hero skins',async({page},info)=>{
 test.setTimeout(300_000);const errors:string[]=[];page.on('pageerror',e=>errors.push(e.stack||e.message));let deliver:((snapshot:ArenaSnapshot)=>void)|undefined,fixture:ArenaSimulation|undefined,serial=0;
 await page.routeWebSocket('**/ws',socket=>{socket.onMessage(raw=>{const message=JSON.parse(String(raw));if(message.type!=='join')return;fixture=new ArenaSimulation({room:`ART-${++serial}`,seed:4});const self=fixture.addPlayer('fixture-local','Fixture local',message.heroId,'sun'),peer=fixture.addPlayer('fixture-peer','Fixture peer',message.heroId,'moon');peer.z=self.z+4;peer.x=self.x+3;deliver=snapshot=>socket.send(JSON.stringify({type:'snapshot',snapshot}));socket.send(JSON.stringify({type:'welcome',protocol:YUGA_PROTOCOL,id:'fixture-local',room:fixture.room,token:'b'.repeat(48),snapshot:fixture.snapshot()}));});});
 await setup(page);const records:unknown[]=[];
 for(const hero of HEROES){await page.locator(`[data-hero="${hero.id}"]`).click();await page.locator('#online-open').click();await page.locator('#player-name').fill('Animation fixture');await page.locator('#join-room').click();await expect(page.locator('#loading')).toBeHidden({timeout:120_000});await expect.poll(async()=>(await assets(page)).instances.filter(i=>i.heroId===hero.id).length).toBeGreaterThanOrEqual(2);
  const me=fixture!.actors.get('fixture-local')!,peer=fixture!.actors.get('fixture-peer')!;await frame(page);const models=await assets(page),self=models.instances.find(i=>i.id===me.id)!,other=models.instances.find(i=>i.id===peer.id)!;expect(self.skeletons.some(id=>other.skeletons.includes(id))).toBe(false);expect(models.fallback).toEqual([]);
  me.health=0;me.respawn=9;fixture!.tick++;deliver!(fixture!.snapshot());await expect.poll(async()=>(await local(page)).state).toBe('defeat');await expect.poll(async()=>(await assets(page)).instances.find(i=>i.id===peer.id)!.state).toBe('idle');await expect.poll(async()=>(await local(page)).animationTime).toBeGreaterThan(.55);await page.screenshot({path:info.outputPath(`fixture-${hero.id}-defeat.png`)});const dead=await local(page);me.health=me.maxHealth;me.respawn=0;fixture!.tick++;deliver!(fixture!.snapshot());await expect.poll(async()=>(await local(page)).state).toBe('idle');records.push({heroId:hero.id,independentSkeletons:[self.skeletons,other.skeletons],defeat:dead,recovered:await local(page)});await page.keyboard.press('Escape');await page.locator('#leave-game').click();}
 expect(errors).toEqual([]);await info.attach('labelled-render-state-fixtures',{body:JSON.stringify({scope:'Mocked WebSocket snapshots and positional/health setup solely test visible animation-state isolation and defeat/recovery. No native defeat, combat win or realnetwork claim.',records,errors},null,2),contentType:'application/json'});
});
