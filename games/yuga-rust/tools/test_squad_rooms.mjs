// Exercise actual WebSocket seating, play, input lifetimes and room isolation.
// Run with --binary /path/to/room, --wasm /path/to/yuga-rust.wasm or --package /extracted/dir.
import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { once } from 'node:events';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const here = path.dirname(fileURLToPath(import.meta.url));
const { values } = parseArgs({options:{
  binary:{type:'string'}, wasm:{type:'string'}, package:{type:'string'}, archive:{type:'string'}, report:{type:'string'},
}});
assert.ok([values.binary, values.wasm, values.package].filter(Boolean).length <= 1);
const packaged = values.package && path.resolve(values.package);
assert.ok(!values.archive || packaged, '--archive is checked against an extracted --package');
let archiveIdentity;
if (values.archive) {
  // Hash every runtime member directly out of the ZIP and compare with the exact
  // files about to be served/executed, including the HTML that embeds the browser.
  const archivePath=path.resolve(values.archive);
  const memberHashes=JSON.parse(execFileSync(process.env.PYTHON || 'python3',['-c',
    `import hashlib,json,sys,zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
 print(json.dumps({n:hashlib.sha256(z.read(n)).hexdigest() for n in ["serve_rooms.mjs","room-wasm.mjs","yuga-rust.wasm","yuga-rust.html"]}))`,
    archivePath],{encoding:'utf8'}));
  for(const [name,hash] of Object.entries(memberHashes)) {
    assert.equal(createHash('sha256').update(await readFile(path.join(packaged,name))).digest('hex'),hash,name);
  }
  archiveIdentity={filename:path.basename(archivePath),sha256:createHash('sha256').update(await readFile(archivePath)).digest('hex'),
    members:memberHashes};
}
const hostScript = path.join(packaged ?? here,'serve_rooms.mjs');
const worker = path.join(packaged ?? here,'room-wasm.mjs');
const native = path.resolve(values.binary ?? path.join(here,'../target/release',process.platform === 'win32' ? 'room.exe':'room'));
const wasm = values.wasm ? path.resolve(values.wasm) : (packaged && path.join(packaged,'yuga-rust.wasm'));
const authority = packaged ? [] : [wasm?'--wasm':'--binary',wasm ?? native,'--html',path.join(here,'../../yuga/index.html')];
const host = spawn(process.execPath,[hostScript,...authority,'--port','0'],{
  cwd: packaged || here, stdio:['ignore','pipe','pipe'], windowsHide:true,
});
const exited = once(host,'exit');
let log='';
for(const stream of [host.stdout,host.stderr]) stream.on('data',chunk=>{log=(log+chunk).slice(-32_000)});
const peers=[];
const sha=async f=>createHash('sha256').update(await readFile(f)).digest('hex');
async function until(label,fn,timeout=8000) {
  const end=Date.now()+timeout;
  while(Date.now()<end){
    const out=await fn(); if(out)return out;
    if(host.exitCode!==null || host.signalCode)throw Error(label+'; room host exited: '+log);
    await sleep(12);
  }
  throw Error('Timeout: '+label+'; host: '+log);
}
const port=await until('room host ready',()=>Number(/127\.0\.0\.1:(\d+)/.exec(log)?.[1]));
const base='http://127.0.0.1:'+port;
async function health(){const r=await fetch(base+'/health',{signal:AbortSignal.timeout(2000)});assert.equal(r.status,200);return r.json()}

async function connect(){
  const ws=new WebSocket('ws://127.0.0.1:'+port+'/rooms');
  const bag={ws,events:[],frames:0,bytes:0,max:0,closed:false,
    send(packet){ws.send(JSON.stringify(packet));},
    wait(label,test,after=0){return until(label,()=>bag.events.slice(after).find(test));},
  };
  peers.push(bag);
  ws.addEventListener('close',()=>{bag.closed=true;});
  ws.addEventListener('message',message=>{
    const packet=JSON.parse(message.data);
    if(packet.type!=='state'){bag.events.push(packet);return;}
    const s=packet.state, bytes=Buffer.byteLength(message.data);
    bag.frames++;bag.bytes+=bytes;bag.max=Math.max(bag.max,bytes);
    // Store the fields being checked; release full JSON arrays between frames.
    const pose=p=>({id:p.actor.id,team:p.actor.team,pos:p.actor.pos,hero:p.hero});
    bag.events.push({type:'state',seq:packet.seq,accepted:packet.accepted,seat:s.seat,tick:s.tick,
      local:pose(s),others:s.roster?.map(p=>({seat:p.seat,...pose(p)})),active:s.active?.id,
      score:s.army.cores,bytes,arrival:performance.now()});
  });
  await until('open socket',()=>ws.readyState===WebSocket.OPEN);
  return bag;
}
const heroes=['hanuman','rama','rama','hanuman','hanuman','rama'];
const direction=i=>[0,i%2===0?1:-1];
const team=i=>i%2===0?'sun':'moon';
function input(i,seq,movement=[0,0],cast){
  return {type:'input',seq,movement,aim:direction(i),...(cast?{cast}:{})};
}
const durations=[];
const checks=[];
try{
  const squad=[await connect()];
  const invalid=squad[0];
  for(const n of [0,2,'3',null]){
    const cursor=invalid.events.length;invalid.send({type:'create',hero:heroes[0],teamSize:n});
    await invalid.wait('reject invalid squad size',m=>m.type==='error',cursor);
  }
  assert.equal((await health()).rooms,0);
  squad[0].send({type:'create',hero:heroes[0],teamSize:3});
  const opened=await squad[0].wait('create squad',m=>m.type==='lobby');
  assert.equal(opened.capacity,6);assert.equal(opened.count,1);assert.equal(opened.seat,0);
  const code=opened.code;
  for(let i=1;i<5;i++){
    const p=await connect();squad.push(p);
    p.send({type:'join',hero:heroes[i],code});
    for(let j=0;j<=i;j++){
      const lobby=await squad[j].wait('broadcast seats before launch',m=>m.type==='lobby'&&m.count===i+1);
      assert.equal(lobby.seat,j);assert.equal(lobby.team,team(j));assert.equal(lobby.capacity,6);
    }
  }
  const pre=await health();
  assert.equal(pre.rooms,1);assert.equal(pre.running,0);
  assert.ok(squad.every(p=>p.frames===0));
  squad[0].send(input(0,0));
  await squad[0].wait('reject pre-match movement',m=>m.type==='error'&&/not running/i.test(m.message));

  // A separate two-seat room can start while five players are still in this lobby.
  const duel=[await connect(),await connect()];duel[0].send({type:'create',hero:'rama'});
  const pair=await duel[0].wait('create default duel',m=>m.type==='lobby');
  assert.notEqual(pair.code,code);assert.equal(pair.capacity,2);
  duel[1].send({type:'join',code:pair.code,hero:'hanuman'});
  await Promise.all(duel.map(p=>p.wait('default duel starts',m=>m.type==='state')));
  assert.equal((await health()).running,1);
  checks.push('Invalid team sizes rejected; all five waiting seats receive each count while the separate default duel starts.');

  squad.push(await connect());squad[5].send({type:'join',code,hero:heroes[5]});
  const start=await Promise.all(squad.map((p,i)=>p.wait('six-seat initial state '+i,m=>m.type==='state')));
  assert.ok(start.every(s=>s.tick===start[0].tick));
  const ids=start.map(e=>e.local.id);assert.equal(new Set(ids).size,6);
  for(let i=0;i<6;i++){
    const lobby=await squad[i].wait('final lobby',m=>m.type==='lobby'&&m.count===6);
    assert.equal(lobby.seat,i);assert.equal(lobby.team,team(i));assert.equal(lobby.capacity,6);
    assert.equal(start[i].seat,i);assert.equal(start[i].local.team,team(i));assert.equal(start[i].local.hero,heroes[i]);
    const remoteSeats=[0,1,2,3,4,5].filter(seat=>seat!==i);
    assert.deepEqual(start[i].others.map(r=>r.seat),remoteSeats);
    for(const r of start[i].others){
      assert.equal(r.id,ids[r.seat]);assert.equal(r.team,team(r.seat));assert.deepEqual(r.pos,start[r.seat].local.pos);
    }
  }
  assert.equal((await health()).running,2);
  const excess=await connect();excess.send({type:'join',hero:'rama',code});
  await excess.wait('reject seventh entrant',m=>m.type==='error'&&/full/i.test(m.message));
  const spoof={...input(0,1),seat:4};
  squad[0].send(spoof);await squad[0].wait('reject seat spoof',m=>m.type==='error'&&/invalid input/i.test(m.message));
  const cursors=squad.map(p=>p.events.length);
  const started=performance.now();
  for(let seq=1;seq<=24;seq++){
    for(let i=0;i<6;i++){
      const cast=seq===2?{slot:0,ground:[0,0],aim:direction(i)}:null;
      squad[i].send(input(i,seq,[0.45,0],cast));
    }
    await sleep(50);
  }
  const last=await Promise.all(squad.map((p,i)=>p.wait('ack latest input for seat '+i,m=>m.type==='state'&&m.seq===24,cursors[i])));
  for(let i=0;i<6;i++){
    assert.ok(squad[i].events.slice(cursors[i]).some(m=>m.type==='state'&&m.accepted===true),'accepted ability seat '+i);
    assert.ok(last[i].local.pos[0]>start[i].local.pos[0]+0.5,'movement applied to seat '+i);
    const frames=squad[i].events.slice(cursors[i]).filter(m=>m.type==='state');
    assert.ok(frames.length>=2);
    for(let j=1;j<frames.length;j++){
      assert.ok(frames[j].tick>frames[j-1].tick);
      durations.push(frames[j].arrival-frames[j-1].arrival);
    }
  }
  const elapsed=performance.now()-started;
  for(const bad of [input(5,24),{...input(5,25),cast:{slot:6,ground:[0,0],aim:[0,-1]}}]){
    const cursor=squad[5].events.length;squad[5].send(bad);
    await squad[5].wait('reject stale sequence or invalid slot',m=>m.type==='error',cursor);
  }
  squad[5].send(input(5,25,[0.45,0]));
  await squad[5].wait('recover with unchanged seq after invalid input',m=>m.type==='state'&&m.seq===25);
  await sleep(1400);
  const movementCursor=squad[5].events.length;
  const pauseA=await squad[5].wait('first expired movement pose',m=>m.type==='state',movementCursor);
  const pauseB=await squad[5].wait('second expired movement pose',m=>m.type==='state'&&m.tick>=pauseA.tick+4,movementCursor);
  assert.deepEqual(pauseA.local.pos,pauseB.local.pos);
  const standstill=duel[0].events.filter(m=>m.type==='state');
  assert.ok(standstill.length>=2);assert.deepEqual(standstill.at(-1).local.pos,standstill[0].local.pos);
  checks.push('Every seat received its local authority view plus five ordered remote players; seventh join and seat spoof were refused.');
  checks.push('Six seats moved, cast, advanced monotonically and acknowledged 144 inputs; stale movement expired and an invalid cast consumed no sequence.');

  const cursor=duel[0].events.length;
  squad[2].ws.close(1000,'player left');
  await until('all six squad sockets close',()=>squad.every(p=>p.closed));
  for(let i=0;i<6;i++)if(i!==2)assert.ok(squad[i].events.some(m=>m.type==='closed'));
  await duel[0].wait('unrelated duel continues',m=>m.type==='state',cursor);
  const remaining=await until('only the duel remains',async()=>{const s=await health();return s.rooms===1&&s.running===1&&s;});
  assert.equal(remaining.clients,3); // Two duel players plus the unseated entrant.
  excess.ws.close();duel[0].ws.close();
  const clean=await until('room cleanup',async()=>{const s=await health();return s.rooms===0&&s.running===0&&s.clients===0&&s;});
  checks.push('A squad departure closed precisely its room and its six seats; the other room continued, then released its sockets and authority.');
  const ordered=durations.sort((a,b)=>a-b);
  const report={result:'pass',transport:'loopback WebSocket, real host, one Rust authority per active room',
    authority:wasm?'portable Rust WebAssembly worker':'native Rust executable',squad_seats:6,other_room_seats:2,
    peak_connected_sockets:9,peak_running_rooms:2,initial_tick:start[0].tick,
    command_frames:6*24,load_elapsed_ms:Math.round(elapsed),total_squad_frames:squad.reduce((n,p)=>n+p.frames,0),
    max_snapshot_bytes:Math.max(...squad.map(p=>p.max)),squad_network_bytes:squad.reduce((n,p)=>n+p.bytes,0),
    observed_frame_interval_p50_ms:Math.round(ordered[Math.floor(ordered.length/2)]),
    observed_frame_interval_p95_ms:Math.round(ordered[Math.floor(ordered.length*0.95)]),
    final_health:clean,checks,...(archiveIdentity?{archive:archiveIdentity}:{}),hashes:{host:await sha(hostScript),authority:await sha(wasm??native),
      ...(wasm?{worker:await sha(worker)}:{}),test:await sha(fileURLToPath(import.meta.url))}};
  console.log(JSON.stringify(report,null,2));
  if(values.report){await mkdir(path.dirname(path.resolve(values.report)),{recursive:true});await writeFile(values.report,JSON.stringify(report,null,2)+'\n');}
}finally{
  for(const p of peers)if(p.ws.readyState===WebSocket.OPEN)p.ws.close();
  host.kill('SIGTERM');
  await Promise.race([exited,sleep(2000).then(()=>{if(host.exitCode===null&&!host.signalCode)host.kill('SIGKILL');})]);
}
