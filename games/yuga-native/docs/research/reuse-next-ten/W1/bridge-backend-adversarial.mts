/** Actual isolated bridge TCP intake; public client parser is a separate boundary. */
import net from 'node:net';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';

const source=process.argv[2], output=process.argv[3];
const sha=(path:string)=>createHash('sha256').update(fs.readFileSync(path)).digest('hex');
const before=sha(source);
const bridge=await import(pathToFileURL(source).href);
const simulation=new bridge.ArenaSimulation({room:'W1-FIXTURE',seed:1,botsPerTeam:0,duration:30});
simulation.addPlayer('a'.repeat(16),'W1 A','rama');
simulation.addPlayer('b'.repeat(16),'W1 B','rama');
const pause=(ms:number)=>new Promise(resolve=>setTimeout(resolve,ms));
let peer:net.Socket|undefined;
const server=net.createServer(socket=>{peer=socket});
await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));
const address=server.address();
if(!address||typeof address==='string')throw Error('missing ephemeral listener');
const fixture='f'.repeat(64),contract='c'.repeat(64);
await bridge.connectNative(address.port,fixture,contract);
await pause(10);
const trials:Array<object>=[];
const mutations:Array<[string,boolean,(packet:any)=>void]>=[
 ['valid ordinary backend state',true,()=>{}],
 ['duplicate actor slots',false,p=>{p.actors[1].bridgeSlot=0}],
 ['grounded string',false,p=>{p.actors[0].grounded='false'}],
 ['empty velocity vector',false,p=>{p.actors[0].velocity=[]}],
 ['actor tick differs from envelope',false,p=>{p.actors[0].nativeTick+=100}],
 ['actor epoch differs from envelope',false,p=>{p.actors[0].bridgeEpoch+=1}],
 ['fractional negative acknowledgement',false,p=>{p.actors[0].bridgeAckSeq=-.5}],
 ['positive after rejected controls',true,()=>{}],
];
for(let index=0;index<mutations.length;index++){
 const [label,expected,mutate]=mutations[index],tick=index+1;
 const actor=(slot:number)=>({id:slot?'b'.repeat(16):'a'.repeat(16),x:12,y:3.21,z:1,yaw:0,pitch:0,bridgeAckSeq:-1,bridgeInputTick:-1000,bridgeSlot:slot,bridgeEpoch:0,nativeTick:tick,grounded:true,support:'fixture',shot:{},velocity:[0,0,0]});
 const packet={schema:1,fixtureHash:fixture,contractHash:contract,nativeTick:tick,nativeTime:tick/60,stage:'stacked',stageTime:tick/60,epoch:0,done:false,revision:tick,actors:[actor(0),actor(1)],rejectedPackets:0};
 mutate(packet);
 const count=bridge.bridgeStats.nativePackets;
 peer!.write(JSON.stringify(packet)+'\n');
 await pause(30);
 const accepted=bridge.bridgeStats.nativePackets===count+1;
 trials.push({label,expected_accepted:expected,accepted,passed:accepted===expected});
}
bridge.closeNative();peer?.destroy();
await new Promise<void>(resolve=>server.close(()=>resolve()));
const unchanged=before===sha(source);
const report={schema:1,scope:'Fake private native backend sends actual JSON over real loopback TCP into unchanged bridge module. This challenges its stated two-actor/versioned-state boundary; it is not a public client exploit or full match.',source_sha256:before,source_unchanged:unchanged,checks:trials,passed:unchanged&&trials.every((row:any)=>row.passed)};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
process.exitCode=report.passed?0:1;
