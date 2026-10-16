import { YUGA_PROTOCOL } from '../shared/types';
/** Bounded local measurements, not production-capacity claims. Run: npx tsx games/yuga/tools/stress.ts */
import assert from 'node:assert/strict';
import os from 'node:os';
import { createHash } from 'node:crypto';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { performance, monitorEventLoopDelay } from 'node:perf_hooks';
import { execFileSync } from 'node:child_process';
import { WebSocket } from 'ws';
import { ArenaSimulation, ARENA_RULES } from '../shared/simulation';
import { HEROES } from '../shared/heroes';
import { GOLD_RULES, JUNGLE_CAMPS } from '../shared/map';
import { createArenaServer } from '../server/server';
import type { ArenaSnapshot, ServerMessage } from '../shared/types';

const percentile=(values:number[],q:number)=>values.length?[...values].sort((a,b)=>a-b)[Math.min(values.length-1,Math.floor((values.length-1)*q))]!:0;
const summary=(values:number[])=>({samples:values.length,p50:percentile(values,.5),p95:percentile(values,.95),max:values.length?Math.max(...values):0});
const readOptional=async(path:string)=>{try{return(await readFile(path,'utf8')).trim();}catch{return'unavailable';}};
const cpu=()=>process.cpuUsage();
function resource(start:ReturnType<typeof cpu>,elapsedMs:number){const use=process.cpuUsage(start);return{cpuUserMs:use.user/1000,cpuSystemMs:use.system/1000,cpuPercentOfOneCore:(use.user+use.system)/1000/elapsedMs*100,rssBytes:process.memoryUsage().rss,heapUsedBytes:process.memoryUsage().heapUsed};}
function counts(snapshot:ArenaSnapshot){return{actors:snapshot.actors.length,heroes:snapshot.actors.filter(a=>a.kind==='hero').length,minions:snapshot.actors.filter(a=>a.kind==='minion').length,projectiles:snapshot.projectiles.length,zones:snapshot.zones.length,events:snapshot.events.length,neutrals:snapshot.neutrals.length,livingNeutrals:snapshot.neutrals.filter(n=>n.health>0).length,goldShards:snapshot.goldShards.length,soldiers:snapshot.actors.filter(a=>a.unitArchetype==='soldier').length,cityWatch:snapshot.actors.filter(a=>a.unitArchetype==='city-watch').length,ministers:snapshot.actors.filter(a=>a.unitArchetype==='minister').length,kings:snapshot.actors.filter(a=>a.unitArchetype==='king').length};}
function check(snapshot:ArenaSnapshot){
 assert.equal(snapshot.protocol,YUGA_PROTOCOL);assert(snapshot.actors.length<=ARENA_RULES.maxActors);assert(snapshot.projectiles.length<=ARENA_RULES.maxProjectiles);assert(snapshot.zones.length<=ARENA_RULES.maxZones);
 for(const actor of snapshot.actors)assert([actor.x,actor.z,actor.y,actor.health,actor.credits,...actor.cooldowns].every(Number.isFinite));
 assert.equal(snapshot.neutrals.length,JUNGLE_CAMPS.length);assert.equal(new Set(snapshot.neutrals.map(n=>n.id)).size,snapshot.neutrals.length);
 for(const neutral of snapshot.neutrals){assert([neutral.x,neutral.z,neutral.y,neutral.health,neutral.maxHealth,neutral.respawnAt].every(Number.isFinite));assert(neutral.health>=0&&neutral.health<=neutral.maxHealth);assert(Math.abs(neutral.x)<70&&Math.abs(neutral.z)<84);}
 assert(snapshot.goldShards.length<=GOLD_RULES.maxShards);assert.equal(new Set(snapshot.goldShards.map(g=>g.id)).size,snapshot.goldShards.length);
 for(const shard of snapshot.goldShards){assert([shard.x,shard.z,shard.y,shard.value,shard.createdAt,shard.expiresAt].every(Number.isFinite));assert(shard.value>0);assert(shard.expiresAt>snapshot.time);assert(Math.abs(shard.expiresAt-shard.createdAt-GOLD_RULES.lifetime)<1e-5);}
}
function maxima(target:ReturnType<typeof counts>,snapshot:ArenaSnapshot){const next=counts(snapshot);for(const k of Object.keys(target)as(keyof typeof target)[])target[k]=Math.max(target[k],next[k]);}
function simulationRun(seed:number,humans:boolean){
 const sim=new ArenaSimulation({room:`SIM-${seed}`,seed}),steps:number[]=[],serialize:number[]=[],peak=counts(sim.snapshot());
 if(humans)for(let n=0;n<6;n++)sim.addPlayer(`stress-${n}`,`Synthetic ${n}`,HEROES[n]!.id,n%2?'moon':'sun');
 const start=performance.now(),before=cpu();let bytes=0;const laneAdvance={sun:[0,0,0],moon:[0,0,0]};
 for(let tick=0;tick<9602&&sim.phase==='playing';tick++){
  if(humans)for(let n=0;n<6;n++){const actor=sim.actors.get(`stress-${n}`)!,sign=actor.team==='sun'?1:-1;sim.input(actor.id,{type:'input',seq:tick,moveX:Math.sin(tick/150+n)*.3,moveZ:sign,yaw:actor.team==='sun'?0:Math.PI,pitch:.01,fire:true,jump:tick%130===0});if(tick%140===0)sim.command(actor.id,{type:'command',id:`ability-${tick}-${n}`,action:'ability',slot:(Math.floor(tick/140)%3)as 0|1|2});}
  const t=performance.now();sim.step(.05);steps.push(performance.now()-t);
  if(tick%2===0){const t=performance.now(),snap=sim.snapshot();bytes+=Buffer.byteLength(JSON.stringify(snap));serialize.push(performance.now()-t);maxima(peak,snap);check(snap);for(const actor of snap.actors)laneAdvance[actor.team][actor.lane]=Math.max(laneAdvance[actor.team][actor.lane]!,actor.team==='sun'?actor.z+66:66-actor.z);}
 }
 const elapsedMs=performance.now()-start,snap=sim.snapshot();assert.equal(snap.phase,'finished');return{seed,mode:humans?'six synthetic human intents':'six simulation bots',wallMs:elapsedMs,simulatedSeconds:snap.time,winner:snap.winner,reason:snap.reason,scores:snap.scores,furthestInwardMetresByTeamLane:laneAdvance,finalStructures:snap.structures.map(s=>({id:s.id,health:s.health,shielded:s.shielded})),stepMs:summary(steps),snapshotAndJsonMs:summary(serialize),serializedBytes:bytes,peakEntities:peak,resources:resource(before,elapsedMs)};
}
interface Client{socket:WebSocket;id:string;team:'sun'|'moon';lastAt:number;lastTime:number;seq:number;messages:number;bytes:number;gaps:number[];simAdvance:number[];peak:ReturnType<typeof counts>}
async function websocketRun(roomCount:number,seconds:number){
 const server=await createArenaServer({host:'127.0.0.1',port:0}),address=server.address;assert(address&&typeof address!=='string');const url=`ws://127.0.0.1:${address.port}/ws`,clients:Client[]=[],failures:string[]=[],stepTimes:number[]=[],snapshotTimes:number[]=[];
 const lag=monitorEventLoopDelay({resolution:10});let inputTimer:ReturnType<typeof setInterval>|undefined,measureTimer:ReturnType<typeof setInterval>|undefined,peakRss=process.memoryUsage().rss,peakHeap=process.memoryUsage().heapUsed,inputMessages=0;
 try{
  for(let roomIndex=0;roomIndex<roomCount;roomIndex++){let room='';for(let i=0;i<6;i++)await new Promise<void>((resolve,reject)=>{
   const socket=new WebSocket(url);const timeout=setTimeout(()=>reject(new Error('Join timed out')),5000);let client:Client|undefined;
   socket.on('open',()=>socket.send(JSON.stringify({type:'join',protocol:YUGA_PROTOCOL,heroId:HEROES[(roomIndex*6+i)%HEROES.length]!.id,name:`Load ${roomIndex}-${i}`,...(room?{room}:{})})));
   socket.on('error',e=>{failures.push(e.message);reject(e);});socket.on('message',raw=>{const message=JSON.parse(String(raw))as ServerMessage;if(message.type==='error'){failures.push(message.message);return;}if(message.type==='welcome'){room=message.room;const actor=message.snapshot.actors.find(a=>a.id===message.id)!;client={socket,id:message.id,team:actor.team,lastAt:0,lastTime:message.snapshot.time,seq:0,messages:0,bytes:0,gaps:[],simAdvance:[],peak:counts(message.snapshot)};clients.push(client);clearTimeout(timeout);resolve();}if(message.type==='snapshot'&&client){const now=performance.now();if(client.lastAt){client.gaps.push(now-client.lastAt);client.simAdvance.push(message.snapshot.time-client.lastTime);}client.lastAt=now;client.lastTime=message.snapshot.time;client.messages++;client.bytes+=Buffer.byteLength(String(raw));maxima(client.peak,message.snapshot);check(message.snapshot);}});
  });}
  assert.equal(server.rooms.size,roomCount);assert.equal(clients.length,roomCount*6);
  for(const room of server.rooms.values()){const original=room.sim.step.bind(room.sim),snap=room.sim.snapshot.bind(room.sim);room.sim.step=dt=>{const t=performance.now();original(dt);stepTimes.push(performance.now()-t);};room.sim.snapshot=()=>{const t=performance.now(),value=snap();snapshotTimes.push(performance.now()-t);return value;};}
  const start=performance.now(),before=cpu();lag.enable();
  inputTimer=setInterval(()=>{for(const [n,c]of clients.entries()){if(c.socket.readyState!==WebSocket.OPEN)continue;const sign=c.team==='sun'?1:-1;c.socket.send(JSON.stringify({type:'input',seq:++c.seq,moveX:Math.sin(c.seq/100+n)*.3,moveZ:sign,yaw:c.team==='sun'?0:Math.PI,pitch:.01,fire:true,jump:c.seq%130===0}));inputMessages++;if(c.seq%140===0)c.socket.send(JSON.stringify({type:'command',id:`load-${c.seq}-${n}`,action:'ability',slot:Math.floor(c.seq/140)%3}));}},50);
  measureTimer=setInterval(()=>{peakRss=Math.max(peakRss,process.memoryUsage().rss);peakHeap=Math.max(peakHeap,process.memoryUsage().heapUsed);},250);
  await new Promise(resolve=>setTimeout(resolve,seconds*1000));clearInterval(inputTimer);clearInterval(measureTimer);lag.disable();const elapsedMs=performance.now()-start;assert.equal(clients.filter(c=>c.socket.readyState===WebSocket.OPEN).length,roomCount*6);assert.equal(failures.length,0,failures.join('; '));for(const c of clients)assert(c.messages>=seconds*7,`Too few snapshots for ${c.id}: ${c.messages}`);
  const allGaps=clients.flatMap(c=>c.gaps);return{scope:'Actual loopback sockets; server and synthetic clients share this Node process',rooms:roomCount,actualClients:clients.length,durationMs:elapsedMs,inputHzPerClient:inputMessages/clients.length/(elapsedMs/1000),inputMessages,snapshotMessages:clients.reduce((n,c)=>n+c.messages,0),snapshotBytes:clients.reduce((n,c)=>n+c.bytes,0),stepMs:summary(stepTimes),snapshotCloneMs:summary(snapshotTimes),clientSnapshotIntervalMs:summary(allGaps),snapshotSimulationAdvanceSeconds:summary(clients.flatMap(c=>c.simAdvance)),eventLoopDelayMs:{p50:lag.percentile(50)/1e6,p95:lag.percentile(95)/1e6,max:lag.max/1e6},peakEntitiesByClient:clients.map(c=>c.peak),resources:{...resource(before,elapsedMs),samplingIntervalMs:250,peakRssBytes:Math.max(peakRss,process.memoryUsage().rss),peakHeapUsedBytes:Math.max(peakHeap,process.memoryUsage().heapUsed)},errors:failures};
 }finally{if(inputTimer)clearInterval(inputTimer);if(measureTimer)clearInterval(measureTimer);lag.disable();for(const c of clients)c.socket.terminate();await server.close();}
}
const prefix=process.env.YUGA_EVIDENCE_PREFIX||'';assert(/^[a-z0-9-]*$/.test(prefix),'Evidence prefix must use lower-case letters, digits and hyphens');
const mode=process.env.YUGA_STRESS_MODE||'all';assert(['all','simulation','websocket'].includes(mode));const seconds=Number(process.env.YUGA_STRESS_SECONDS||20);assert(Number.isFinite(seconds)&&seconds>=10&&seconds<=45,'Run length must be10–45 seconds per WS scenario');
const report={protocol:YUGA_PROTOCOL,createdAt:new Date().toISOString(),source:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),workingTreeMayContainUncommittedYugaFiles:true,sourceSha256:Object.fromEntries(await Promise.all(['games/yuga/shared/simulation.ts','games/yuga/shared/types.ts','games/yuga/shared/map.ts','games/yuga/shared/heroes.ts','games/yuga/server/server.ts','games/yuga/tools/stress.ts'].map(async path=>[path,createHash('sha256').update(await readFile(path)).digest('hex')]))),limits:'Local bounded beta observations only. No public WSS, WAN latency, adversarial DDoS, multi-host or national capacity measurement.',machine:{node:process.version,platform:os.platform(),arch:os.arch(),cpuModel:os.cpus()[0]?.model,hostLogicalCpus:os.cpus().length,availableParallelism:os.availableParallelism(),hostTotalMemoryBytes:os.totalmem(),cgroupCpuMax:await readOptional('/sys/fs/cgroup/cpu.max'),cgroupMemoryMax:await readOptional('/sys/fs/cgroup/memory.max')},simulation:[]as ReturnType<typeof simulationRun>[],websocket:[]as Awaited<ReturnType<typeof websocketRun>>[]};
if(mode!=='websocket')for(const humans of[false,true])for(const seed of[7,41,20261016]){report.simulation.push(simulationRun(seed,humans));console.log(`Finished simulation seed${seed}, ${humans?'synthetic players':'bots'}`);}
if(mode!=='simulation')for(const roomCount of[1,2,4]){report.websocket.push(await websocketRun(roomCount,seconds));console.log(`Finished ${roomCount*6} actual sockets / ${roomCount} rooms`);}
const sourceSha256After=Object.fromEntries(await Promise.all(Object.keys(report.sourceSha256).map(async path=>[path,createHash('sha256').update(await readFile(path)).digest('hex')])));assert.deepEqual(sourceSha256After,report.sourceSha256,'Source changed during measurement; no final acceptance');
Object.assign(report,{sourceSha256After,sourceStable:true});
await mkdir('games/yuga/docs/evidence',{recursive:true});const output=`games/yuga/docs/evidence/${prefix}stress-${mode}.json`;await writeFile(output,JSON.stringify(report,null,2));console.log(output);
