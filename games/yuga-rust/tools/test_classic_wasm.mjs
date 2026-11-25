// Compare native and standalone Wasm for the actual 14-hero lab command fixtures.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { referenceCases } from './test_classic_roster.mjs';

const project = fileURLToPath(new URL('../', import.meta.url));
const { values } = parseArgs({options:{wasm:{type:'string',default:resolve(project,'../yuga/client/assets/classic-roster.wasm')},binary:{type:'string'},report:{type:'string'}}});
const hash = b => createHash('sha256').update(b).digest('hex');
function run(exe,args,input) {
  const p=spawnSync(exe,args,{cwd:project,encoding:'utf8',input,maxBuffer:12*1024*1024});
  if(p.error)throw p.error;
  assert.equal(p.status,0,p.stderr);return p.stdout;
}
const native = values.binary ? resolve(values.binary) : run('cargo',['build','--locked','--bin','roster','--message-format=json']).trim().split('\n').map(x=>JSON.parse(x)).find(x=>x.target?.name==='roster' && x.executable)?.executable;
assert.ok(native,'Missing native binary');
const bytes=await readFile(values.wasm), compiled=await WebAssembly.compile(bytes);
assert.equal(WebAssembly.Module.imports(compiled).length,0);
function instance() {
  const w=new WebAssembly.Instance(compiled,{}).exports;
  function input(text,fn) {
    const raw=typeof text==='string'?new TextEncoder().encode(text):text;
    assert.ok(raw.length<=w.roster_input_capacity());
    new Uint8Array(w.memory.buffer,w.roster_input_ptr(),raw.length).set(raw);
    return fn(raw.length);
  }
  function copy(ptr,len) {return new TextDecoder('utf-8',{fatal:true}).decode(new Uint8Array(w.memory.buffer,ptr,len));}
  return {w,reset:id=>input(id,w.roster_reset), command:s=>input(typeof s==='string'?s:JSON.stringify(s),w.roster_command),
    snapshot:()=>copy(w.roster_snapshot_ptr(),w.roster_snapshot_len()),error:()=>copy(w.roster_error_ptr(),w.roster_error_len()),input};
}
const target=instance(), {w}=target;
const checks=[];
function check(test,label) {assert.ok(test,label);checks.push(label);}
check(w.roster_snapshot_len()===0 && !target.command({ticks:1}), 'Commands before hero selection preserve an empty session');
check(target.reset('sita')===1,'Valid hero initializes a fresh snapshot');
const initial=target.snapshot();
for(const [label,callback] of [
  ['empty input',()=>w.roster_command(0)],['oversized length',()=>w.roster_command(w.roster_input_capacity()+1)],
  ['u32 boundary',()=>w.roster_reset(0xffffffff)],['malformed UTF-8',()=>target.input(Uint8Array.from([0xff]),w.roster_reset)],
  ['unknown hero',()=>target.reset('not-a-hero')],['syntax error',()=>target.command('{')],
  ['unknown field',()=>target.command({health:500})],['invalid actor',()=>target.command({actor:'unknown unit',ticks:1})],
  ['excessive step count',()=>target.command({ticks:3601})],['invalid ability',()=>target.command({cast:42})],
  ['nonfinite number',()=>target.command('{"pitch":1e309,"ticks":1}')],['excessive nesting',()=>target.command('['.repeat(1000))],
]) check(!callback() && target.error().length>0 && target.snapshot()===initial,label+' preserves the last accepted world');
w.memory.grow(1);
check(target.command({ticks:1})===1 && !target.error() && JSON.parse(target.snapshot()).tick===1,'ABI works after Wasm memory growth and clears old errors');
const separate=instance();
check(separate.reset('ulupi')===1 && JSON.parse(separate.snapshot()).units[0].hero==='ulupi' && JSON.parse(target.snapshot()).units[0].hero==='sita','Independent Wasm instances keep different heroes and clocks');

check(target.reset('arjuna')===1 && target.command({cast:0})===1, 'Authority accepts an authentic area ability');
let state=JSON.parse(target.snapshot());
check(state.events.some(e=>e.kind==='hit' && e.actor==='self' && e.target==='enemy' && e.slot===0 && e.amount===38) &&
  state.zones.some(z=>z.owner==='self' && z.slot===0 && Number.isSafeInteger(z.id)), 'Damage and zone records carry stable authoritative identity');
target.command({fire:true,ticks:1500});
state=JSON.parse(target.snapshot());
check(state.events.length===64 && state.events[0].id>1 && state.events.every((e,i,all)=>!i || e.id>all[i-1].id),
  'Long play keeps a chronological bounded event ring');
let comparisons=0, numbers=0, largestError=0;
const tolerance=1e-7;
function equal(expected,actual,path) {
  if(typeof expected==='number'){
    const delta=Math.abs(expected-actual);
    assert.ok(typeof actual==='number' && Number.isFinite(actual) && delta<=tolerance,path+' numeric mismatch: '+expected+' vs '+actual);
    largestError=Math.max(largestError,delta);numbers++;return;
  }
  if(expected && typeof expected==='object'){
    assert.ok(actual && typeof actual==='object',path);
    assert.deepEqual(Object.keys(expected).sort(),Object.keys(actual).sort(),path+' shape');
    for(const k of Object.keys(expected))equal(expected[k],actual[k],path+'.'+k);
  } else assert.equal(actual,expected,path);
}
const cases=referenceCases();
for(const c of cases){
  const frames=run(native,[c.hero],c.commands.map(v=>JSON.stringify(v)).join('\n')+'\n').trim().split('\n').map(v=>JSON.parse(v));
  assert.equal(frames.length,c.commands.length+1);
  assert.ok(target.reset(c.hero),target.error());
  for(let i=0;i<frames.length;i++){
    if(i) assert.ok(target.command(c.commands[i-1]),target.error());
    equal(frames[i],JSON.parse(target.snapshot()),c.hero+'/'+c.name+'/'+i);
    comparisons++;
  }
}
const report={heroes:new Set(cases.map(c=>c.hero)).size,cases:cases.length,stateComparisons:comparisons,numericComparisons:numbers,
  maxAbsoluteError:largestError,absoluteTolerance:tolerance,wasmBytes:bytes.length,wasmSha256:hash(bytes),nativeSha256:hash(await readFile(native)),
  inputCapacity:w.roster_input_capacity(),wasmImports:WebAssembly.Module.imports(compiled),edgeChecks:checks};
const output=JSON.stringify(report,null,2)+'\n';
if(values.report)await writeFile(values.report,output);
process.stdout.write(output);
