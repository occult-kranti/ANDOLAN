import { test, expect } from '@playwright/test';
import { createArenaServer } from '../server/server';
import { ArenaSimulation } from '../shared/simulation';
import { JUNGLE_RULES, NEUTRAL_STATS } from '../shared/map';
import { YUGA_PROTOCOL, type ArenaSnapshot, type GameEvent } from '../shared/types';
import { boot, arenaState, localActor, waitReady, imageEvidence, nativeWalk, keyboardYaw, rendered } from './browser-harness';

test('native camp approach, leash, clear, gold shard, temporary power and respawn',async({page},info)=>{
 test.setTimeout(240_000);
 const server=await createArenaServer({port:0,host:'127.0.0.1',simulation:{botsPerTeam:0}}),address=server.address;
 if(!address||typeof address==='string')throw new Error('No arena listener');
 const events=new Map<number,GameEvent>(),states:{time:number;state:string;health:number;x:number;z:number}[]=[],shards=new Map<string,{sourceId:string;value:number}>();
 let campId='';
 page.on('websocket',socket=>socket.on('framereceived',frame=>{
  let message:{type:string;snapshot?:ArenaSnapshot};try{message=JSON.parse(String(frame.payload));}catch{return;}
  if(message.type!=='snapshot'||!message.snapshot)return;
  for(const event of message.snapshot.events)if(['camp','gold','buff'].includes(event.type))events.set(event.id,event);
  for(const shard of message.snapshot.goldShards)shards.set(shard.id,{sourceId:shard.sourceId,value:shard.value});
  const neutral=message.snapshot.neutrals.find(n=>n.campId==='stone-grove');if(neutral){campId=neutral.id;const prior=states.at(-1);if(!prior||prior.state!==neutral.state)states.push({time:message.snapshot.time,state:neutral.state,health:neutral.health,x:neutral.x,z:neutral.z});}
 }));
 try{
  const diagnostics=await boot(page);await page.locator('#online-open').click();await page.locator('#server-address').fill(`http://127.0.0.1:${address.port}`);await page.locator('#player-name').fill('Native grove visitor');await page.locator('#join-room').click();await waitReady(page);
  const actorId=(await localActor(page)).id;await imageEvidence(page,info,'jungle-no-interaction-spawn');
  await page.keyboard.press('KeyB');await page.locator('#buy-power').click();await expect.poll(async()=>(await localActor(page)).upgrades.power).toBe(1);await page.locator('#upgrades-dialog [data-close]').click();
  // The real server's first human starts at x=-3, clearing the central tower.
  await nativeWalk(page,'KeyW',actor=>actor.z>-2,35_000);await nativeWalk(page,'KeyD',actor=>actor.x<-14);
  const neutral=async()=>(await arenaState(page)).neutrals.find(n=>n.campId==='stone-grove')!;
  await expect(page.locator('#camp-status')).toContainText('Stone Grove');
  await expect.poll(async()=>(await neutral()).state,{timeout:45_000}).toBe('aggro');expect((await neutral()).targetId).toBe(actorId);await imageEvidence(page,info,'native-yaksha-aggro');
  await nativeWalk(page,'KeyA',actor=>actor.x>-3);await expect.poll(()=>states.some(state=>state.state==='returning')).toBe(true);await expect.poll(async()=>(await neutral()).state).toBe('idle');expect((await neutral()).health).toBe((await neutral()).maxHealth);
  await nativeWalk(page,'KeyD',actor=>actor.x<-14);await expect.poll(async()=>(await neutral()).state).toBe('aggro');
  const before=await localActor(page),target=await neutral();await keyboardYaw(page,Math.atan2(target.x-before.x,target.z-before.z));await page.keyboard.press('KeyT');await expect.poll(()=>page.evaluate(()=>window.__YUGA.metrics().targetId)).toBe(campId);
  await page.keyboard.down('KeyF');
  try{
   await expect.poll(async()=>(await neutral()).state,{timeout:25_000,intervals:[50,100]}).toBe('dead');
   await expect.poll(()=>[...events.values()].some(event=>event.type==='gold'&&event.actorId===actorId&&event.amount===JUNGLE_RULES.shardGold&&event.time>=[...events.values()].find(e=>e.type==='camp'&&e.targetId===campId)!.time),{timeout:8_000,intervals:[30,50]}).toBe(true);
  }finally{await page.keyboard.up('KeyF');}
  const killed=await neutral(),after=await localActor(page),earned=[...events.values()].filter(event=>event.actorId===actorId&&event.targetId===campId),gold=[...events.values()].filter(event=>event.type==='gold'&&event.actorId===actorId&&event.amount===JUNGLE_RULES.shardGold&&event.time>=[...events.values()].find(e=>e.type==='camp'&&e.targetId===campId)!.time);
  expect(earned.filter(event=>event.type==='camp')).toHaveLength(1);expect(earned.filter(event=>event.type==='buff')).toHaveLength(1);expect(gold).toHaveLength(1);expect(gold[0]!.amount).toBe(JUNGLE_RULES.shardGold);expect(gold[0]!.reward).toBe('secure');
  expect(after.credits-before.credits).toBeGreaterThanOrEqual(JUNGLE_RULES.sharedGold+JUNGLE_RULES.shardGold);expect(after.effects.vigor).toBeGreaterThan(0);
  await expect(page.locator('#buff-status [data-buff="vigor"]')).toBeVisible();await expect(page.locator('#gold-feedback')).toContainText('Secured');await expect(page.locator('#camp-status')).toContainText('Returns in');await imageEvidence(page,info,'native-camp-reward');
  // Return along the open central route behind the friendly tower while the
  // normal respawn clock runs; staying beside the camp would invite lane combat.
  await keyboardYaw(page,0);await nativeWalk(page,'KeyA',actor=>actor.x>-4);await nativeWalk(page,'KeyS',actor=>actor.z<-50,25_000);
  await expect.poll(async()=>(await localActor(page)).effects.vigor||0,{timeout:20_000}).toBe(0);expect((await localActor(page)).health).toBeGreaterThan(0);await expect(page.locator('#buff-status [data-buff="vigor"]')).toHaveCount(0);
  await expect.poll(async()=>(await neutral()).state,{timeout:50_000}).toBe('idle');const respawned=await neutral();expect(respawned.health).toBe(respawned.maxHealth);expect((await arenaState(page)).time).toBeGreaterThanOrEqual(killed.respawnAt);expect([...events.values()].filter(event=>event.type==='gold'&&event.targetId===gold[0]!.targetId)).toHaveLength(1);
  expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);
  await info.attach('native-jungle-loop',{body:JSON.stringify({scope:'Actual local WebSocket server without hero bots; ordinary movement, target lock and primary fire. Lane waves and normal camp/buff/respawn clocks remain active. No positional, reward, health or timer setup.',states,before,after,killed,respawned,earned,gold,observedShard:shards.get(gold[0]!.targetId!)??'Shard was collected between snapshots; durable gold receipt is authoritative evidence, not a visual shard claim.',errors:diagnostics},null,2),contentType:'application/json'});
 }finally{await page.keyboard.up('KeyF');await server.close();}
});

test('labelled reward and camp HUD snapshots show first receipts, shared versus stolen, and expiry',async({browser},info)=>{
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true}),page=await context.newPage();
 let fixture:ArenaSimulation|undefined,send:(()=>void)|undefined,timer:ReturnType<typeof setInterval>|undefined;const fixtureEvents:GameEvent[]=[];
 await page.routeWebSocket('**/ws',socket=>socket.onMessage(raw=>{
  const message=JSON.parse(String(raw));if(message.type!=='join')return;
  fixture=new ArenaSimulation({room:'HUD-FIXTURE',botsPerTeam:0});const actor=fixture.addPlayer('hud-local','HUD fixture','rama','sun');actor.x=-14;actor.z=0;
  const camp=fixture.neutrals.find(n=>n.campId==='stone-grove')!;camp.state='idle';camp.health=camp.maxHealth;camp.respawnAt=0;
  send=()=>{fixture!.tick++;socket.send(JSON.stringify({type:'snapshot',snapshot:{...fixture!.snapshot(),events:fixtureEvents}}));};
  socket.send(JSON.stringify({type:'welcome',protocol:YUGA_PROTOCOL,id:actor.id,room:fixture.room,token:'d'.repeat(48),snapshot:fixture.snapshot()}));timer=setInterval(()=>send?.(),100);
 }));
 try{
  const diagnostics=await boot(page);await page.locator('#online-open').click();await page.locator('#player-name').fill('HUD fixture');await page.locator('#join-room').click();await waitReady(page);await expect(page.locator('#camp-status')).toContainText(NEUTRAL_STATS.yaksha.health.toString());await imageEvidence(page,info,'fixture-mobile-camp-idle');
  const actor=fixture!.actors.get('hud-local')!,camp=fixture!.neutrals.find(n=>n.campId==='stone-grove')!;actor.effects={ward:9,vigor:8,haste:7,slow:0};actor.shield=60;
  fixtureEvents.push({id:1,type:'camp',team:'sun',actorId:actor.id,targetId:camp.id,label:'Fixture camp cleared',color:'#fff',time:0,x:actor.x,z:actor.z,amount:30,sharedAwards:[{actorId:actor.id,amount:30}]},{id:2,type:'gold',team:'sun',actorId:actor.id,targetId:'gold-fixture',label:'Fixture contested gold',color:'#fff',time:0,x:actor.x,z:actor.z,amount:8,reward:'steal'});actor.credits+=38;camp.health=0;camp.state='dead';camp.respawnAt=40;send!();
  await expect(page.locator('#gold-feedback')).toContainText('Shared +30');await expect(page.locator('#gold-feedback')).toContainText('Contested +8');await expect(page.locator('#gold-feedback')).toHaveAttribute('data-kind','steal');await expect(page.locator('#buff-status [data-buff]')).toHaveCount(3);await expect(page.locator('#camp-status')).toContainText('Returns in 40s');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await imageEvidence(page,info,'fixture-mobile-reward-components');
  actor.shield=0;send!();await expect(page.locator('#buff-status [data-buff="ward"]')).toHaveCount(0);
  await expect(page.locator('#gold-feedback')).toBeHidden({timeout:5_000});send!();await rendered(page);await expect(page.locator('#gold-feedback')).toBeHidden();
  actor.effects={ward:0,vigor:0,haste:0,slow:0};fixture!.time=12;send!();await expect(page.locator('#buff-status [data-buff]')).toHaveCount(0);await expect(page.locator('#camp-status')).toContainText('Returns in 28s');
  expect(diagnostics.errors).toEqual([]);expect(diagnostics.consoleErrors).toEqual([]);
  await info.attach('labelled-jungle-hud-fixture',{body:JSON.stringify({scope:'Mocked WebSocket and explicit actor/camp/reward/time snapshots validate HUD presentation and deduplication only. No camp was physically cleared and no contested gold was earned in this fixture.',errors:diagnostics},null,2),contentType:'application/json'});
 }finally{if(timer)clearInterval(timer);await context.close();}
});
