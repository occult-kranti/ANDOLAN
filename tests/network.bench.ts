/** Bounded local development measurement. This is not an Internet/device capacity certification. */
import { promises as fs } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { monitorEventLoopDelay } from 'node:perf_hooks';
import { WebSocket } from 'ws';
import { createGameServer } from '../apps/server/src/server.js';

const directory = await fs.mkdtemp(path.join(tmpdir(), 'andolan-probe-'));
const service = await createGameServer({ port: 0, host: '127.0.0.1', dataDir: directory });
const address = service.address;
if (!address || typeof address === 'string') throw new Error('No listening port');
const sockets: WebSocket[] = [];
const intervals: number[] = [], sizes: number[] = [];
let snapshots = 0;
try {
  await Promise.all(Array.from({ length: 16 }, (_, index) => new Promise<void>((resolve, reject) => {
    const ws = new WebSocket(`ws://127.0.0.1:${address.port}/ws`); sockets.push(ws);
    let previous = 0;
    ws.once('error', reject);
    ws.on('open', () => ws.send(JSON.stringify({ type: 'join', mode: 'public', name: `Probe ${index}` })));
    ws.on('message', raw => {
      const message = JSON.parse(raw.toString());
      if (message.type === 'welcome') resolve();
      if (message.type === 'snapshot') {
        const now = performance.now();
        if (previous) intervals.push(now - previous);
        previous = now; snapshots++; sizes.push(Buffer.byteLength(raw.toString()));
      }
    });
  })));
  const loop = monitorEventLoopDelay({ resolution: 10 }); loop.enable();
  const cpu = process.cpuUsage(), started = performance.now();
  let sequence = 0;
  const inputTimer = setInterval(() => {
    sequence++;
    sockets.forEach((socket, index) => socket.send(JSON.stringify({ type: 'input', seq: sequence, moveX: Math.sin(sequence / 15 + index), moveZ: Math.cos(sequence / 17 + index), forward: 0, turn: 0, sprint: index % 2 === 0 })));
  }, 50);
  await new Promise(resolve => setTimeout(resolve, 5000));
  clearInterval(inputTimer); loop.disable();
  const elapsed = performance.now() - started, usage = process.cpuUsage(cpu);
  const percentile = (values: number[], p: number) => [...values].sort((a, b) => a - b)[Math.min(values.length - 1, Math.floor(values.length * p))] ?? 0;
  const round = (n: number) => Math.round(n * 100) / 100;
  const report = {
    measuredAt: new Date().toISOString(), scope: 'One local Node process hosting server and 16 synthetic WebSocket clients. Five-second development probe; no rendering, WAN, regional, device or sustained-load claims.',
    node: process.version, clients: sockets.length, rooms: service.rooms.size,
    elapsedMs: round(elapsed), inputMessagesSent: sequence * sockets.length, snapshotsReceived: snapshots,
    aggregateSnapshotsPerSecond: round(snapshots / elapsed * 1000), perClientSnapshotsPerSecond: round(snapshots / elapsed * 1000 / sockets.length),
    snapshotBytesMedian: percentile(sizes, .5), snapshotBytesP95: percentile(sizes, .95),
    snapshotInterarrivalMsMedian: round(percentile(intervals, .5)), snapshotInterarrivalMsP95: round(percentile(intervals, .95)),
    processCpuMs: round((usage.user + usage.system) / 1000), processOneCorePercent: round((usage.user + usage.system) / elapsed / 10),
    processRssMiB: round(process.memoryUsage().rss / 1024 / 1024), eventLoopDelayMsP95: round(loop.percentile(95) / 1e6),
  };
  await fs.writeFile('tests/network-benchmark.json', JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  for (const socket of sockets) socket.terminate();
  await service.close();
  await fs.rm(directory, { recursive: true, force: true });
}
