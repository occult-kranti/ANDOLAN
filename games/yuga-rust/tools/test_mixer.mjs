// Verify the shipped Wasm ABI and real AudioWorklet using the original Hanuman WAVs.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { performance } from 'node:perf_hooks';
import { chromium } from 'playwright';

const project = fileURLToPath(new URL('../', import.meta.url));
const { values } = parseArgs({ options: {
  wasm: { type: 'string', default: resolve(project, 'target/wasm32-unknown-unknown/release/yuga_rust.wasm') },
  report: { type: 'string' }
} });
const hash = data => createHash('sha256').update(data).digest('hex');
const wasm = await readFile(values.wasm);
const worklet = await readFile(resolve(project, 'web/mix-worklet.js'));
const module = await WebAssembly.compile(wasm);
const api = new WebAssembly.Instance(module, {}).exports;
const fixtures = resolve(project, '../yuga-native/assets/audio/hanuman-trial');
function wavPcm(data) {
  assert.equal(data.toString('ascii', 0, 4), 'RIFF');
  assert.equal(data.toString('ascii', 8, 12), 'WAVE');
  let format, samples;
  for (let p = 12; p + 8 <= data.length;) {
    const name = data.toString('ascii', p, p+4), n = data.readUInt32LE(p+4);
    const start = p + 8, end = start + n;
    assert.ok(end <= data.length);
    if (name === 'fmt ') format = [data.readUInt16LE(start), data.readUInt16LE(start+2),
      data.readUInt32LE(start+4), data.readUInt16LE(start+14)];
    if (name === 'data') samples = Array.from({length: n / 2}, (_, i) => data.readInt16LE(start+i*2) / 32768);
    p = end + (n & 1);
  }
  assert.deepEqual(format, [1, 1, 24000, 16]); assert.ok(samples?.length); return samples;
}
const waves = [];
for (const name of (await readdir(fixtures)).filter(n=>n.endsWith('.wav')).sort()) {
  const data = await readFile(resolve(fixtures,name));
  waves.push({ name, sha256:hash(data), samples:wavPcm(data) });
}
assert.equal(waves.length, 6);
const stack = Array.from({length: Math.max(...waves.map(w=>w.samples.length))}, (_,i) =>
  waves.reduce((s,w)=>s + (w.samples[i] ?? 0) * 2, 0));
const inputPeak = Math.max(...stack.map(Math.abs));
assert.ok(inputPeak>1);

function benchmark(sampleRate) {
  const block = 128, blocks = Math.ceil(sampleRate*2/block), passes=[], cpuPasses=[];
  const left = Float32Array.from({length:block},(_,i)=>Math.sin(i*.17)*1.7);
  const right = left.map(v => -.5*v);
  for(let run=0; run<4; run++) {
    assert.ok(api.mix_init(sampleRate)>=block);
    const l= new Float32Array(api.memory.buffer, api.mix_left_ptr(), block);
    const r= new Float32Array(api.memory.buffer, api.mix_right_ptr(), block);
    const t=performance.now(), cpuStart=process.cpuUsage();
    for(let i=0;i<blocks;i++) {l.set(left);r.set(right);api.mix_process(block);}
    const ms=performance.now()-t;
    const cpu=process.cpuUsage(cpuStart);
    if(run){passes.push(ms);cpuPasses.push((cpu.user+cpu.system)/1000);}
  }
  const median=[...passes].sort((a,b)=>a-b)[1];
  return {sample_rate:sampleRate,block_frames:block,timed_blocks:blocks,audio_seconds:blocks*block/sampleRate,
    cpu_ms:cpuPasses.map(v=>Number(v.toFixed(3))),
    median_cpu_percent_realtime:Number(([...cpuPasses].sort((a,b)=>a-b)[1]*sampleRate/(10*blocks*block)).toFixed(3)),
    elapsed_ms:passes.map(v=>Number(v.toFixed(3))),median_percent_realtime:Number((median*sampleRate/(10*blocks*block)).toFixed(3))};
}
const cpu = [24000,44100,48000,96000,192000].map(benchmark);
const server=createServer((req,res)=>{
  if(req.url==='/module.wasm') res.writeHead(200,{'Content-Type':'application/wasm'}).end(wasm);
  else if(req.url==='/worklet.js') res.writeHead(200,{'Content-Type':'text/javascript'}).end(worklet);
  else if(req.url==='/') res.writeHead(200,{'Content-Type':'text/html'}).end('<title>YUGA audio test</title>');
  else res.writeHead(404).end();
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try {
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ||
    (existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox']});
  const page=await browser.newPage();
  await page.goto('http://127.0.0.1:'+server.address().port+'/');
  const measured=await page.evaluate(async stack=>{
    const rate=24000, delay=48;
    const module=await WebAssembly.compileStreaming(fetch('/module.wasm'));
    async function mix(level) {
      const context=new OfflineAudioContext(2,stack.length+delay,rate);
      await context.audioWorklet.addModule('/worklet.js');
      const node=new AudioWorkletNode(context,'yuga-limiter',{numberOfInputs:1,numberOfOutputs:1,
        outputChannelCount:[2],channelCount:2,channelCountMode:'explicit',processorOptions:{module}});
      const ready=new Promise((resolve,reject)=>{
        node.port.onmessage=e=>resolve(e.data);
        node.onprocessorerror=()=>reject(new Error('Processor failed'));
      });
      const source=context.createBufferSource();
      const input=context.createBuffer(2,stack.length,rate);
      const left=Float32Array.from(stack,x=>x*level);
      input.copyToChannel(left,0);input.copyToChannel(left.map(x=>-0.5*x),1);
      source.buffer=input;source.connect(node);node.connect(context.destination);source.start(0);
      const [audio,status]=await Promise.all([context.startRendering(),ready]);
      const l=audio.getChannelData(0),r=audio.getChannelData(1);
      let max=0,stereoError=0,quietError=0;
      for(let i=0;i<l.length;i++) {
        max=Math.max(max,Math.abs(l[i]),Math.abs(r[i]));stereoError=Math.max(stereoError,Math.abs(r[i]+l[i]*.5));
        quietError=Math.max(quietError,Math.abs(l[i]-(i<delay?0:left[i-delay])));
      }
      return {status,output_peak:max,stereo_max_error:stereoError,initial_silence:l.subarray(0,delay).every(x=>x===0),
        quiet_after_delay_max_error:level<1?quietError:null};
    }
    return {stack:await mix(1),quiet:await mix(.08)};
  },stack);
  assert.equal(measured.stack.status.type,'ready');
  assert.equal(measured.stack.status.latencyFrames,48);
  assert.ok(measured.stack.output_peak>.95 && measured.stack.output_peak<=1.000001);
  assert.equal(measured.stack.stereo_max_error,0);
  assert.equal(measured.quiet.quiet_after_delay_max_error,0);
  assert.ok(measured.stack.initial_silence && measured.quiet.initial_silence);
  const report={wasm_sha256:hash(wasm),worklet_sha256:hash(worklet),node:process.version,browser:browser.version(),
    fixture_sha256:Object.fromEntries(waves.map(w=>[w.name,w.sha256])),input_peak:inputPeak,worklet:measured,wasm_benchmarks:cpu};
  const text=JSON.stringify(report,null,2)+'\n';if(values.report)await writeFile(values.report,text);process.stdout.write(text);
} finally {if(browser)await browser.close();server.close();server.closeAllConnections();}
