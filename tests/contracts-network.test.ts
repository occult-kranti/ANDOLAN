import { afterEach, describe, expect, it } from 'vitest';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { WebSocket } from 'ws';
import { createGameServer } from '../apps/server/src/server.js';
import type { ResultMessage, ServerMessage, Snapshot, WelcomeMessage } from '../packages/protocol/src/index.js';

type Service = Awaited<ReturnType<typeof createGameServer>>;
const services: Service[] = [], directories: string[] = [], sockets: WebSocket[] = [];
async function start(dataDir?: string) {
  const directory = dataDir ?? await fs.mkdtemp('/tmp/andolan-contracts-');
  if (!directories.includes(directory)) directories.push(directory);
  const service = await createGameServer({ port: 0, host: '127.0.0.1', dataDir: directory }); services.push(service);
  const address = service.address;
  if (!address || typeof address === 'string') throw new Error('No server address');
  return { service, directory, url: `ws://127.0.0.1:${address.port}/ws` };
}
async function peer(url: string) {
  const socket = new WebSocket(url); sockets.push(socket);
  const queue: ServerMessage[] = [], checks = new Set<() => void>();
  socket.on('message', raw => { queue.push(JSON.parse(raw.toString())); for (const check of checks) check(); });
  await new Promise<void>((resolve, reject) => { socket.once('open', resolve); socket.once('error', reject); });
  return {
    socket, send: (message: unknown) => socket.send(JSON.stringify(message)),
    next<T extends ServerMessage>(predicate: (message: ServerMessage) => boolean): Promise<T> {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => { checks.delete(check); reject(new Error('No matching server response')); }, 3000);
        function check() { const index = queue.findIndex(predicate); if (index >= 0) { clearTimeout(timeout); checks.delete(check); resolve(queue.splice(index, 1)[0] as T); } }
        checks.add(check); check();
      });
    },
  };
}
afterEach(async () => {
  for (const socket of sockets.splice(0)) socket.terminate();
  for (const service of services.splice(0)) await service.close();
  for (const directory of directories.splice(0)) await fs.rm(directory, { recursive: true, force: true });
});

describe('real multiplayer contract transactions', () => {
  it('shares pickup, late-join contribution and one reward across two independent clients', async () => {
    const running = await start(), driver = await peer(running.url);
    driver.send({ type: 'join', mode: 'private', gameplay: 'freeroam', name: 'Driver' });
    const welcome = await driver.next<WelcomeMessage>(m => m.type === 'welcome');
    driver.send({ type: 'command', id: 'start-load', action: 'job_start', target: 'clinic-restock' });
    expect((await driver.next<ResultMessage>(m => m.type === 'result')).code).toBe('JOB_STARTED');
    const runner = await peer(running.url);
    runner.send({ type: 'join', mode: 'private', gameplay: 'freeroam', room: welcome.room, name: 'Runner' });
    const other = await runner.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(other.snapshot.contracts.active!.jobId).toBe('clinic-restock');
    const sim = running.service.rooms.get(welcome.room)!.sim;
    // These fixtures position the authoritative server, not browser coordinates. Browser QA covers the driven route.
    const van = sim.vehicles.get('van-01')!, actor = sim.players.get(welcome.playerId)!;
    van.x = -48; van.z = -68; actor.x = -48; actor.z = -68;
    driver.send({ type: 'command', id: 'enter-van', action: 'enter', target: van.id });
    expect((await driver.next<ResultMessage>(m => m.type === 'result')).ok).toBe(true);
    const instanceId = sim.contracts.active!.instanceId;
    driver.send({ type: 'command', id: 'load', action: 'job_interact', target: instanceId, value: 'load' });
    expect((await driver.next<ResultMessage>(m => m.type === 'result')).code).toBe('JOB_STAGE_COMPLETE');
    await runner.next<Snapshot>(m => m.type === 'snapshot' && m.contracts.active?.cargo === true);
    const helper = sim.players.get(other.playerId)!; helper.x = 52; helper.z = -48;
    runner.send({ type: 'command', id: 'remote-unload', action: 'job_interact', target: instanceId, value: 'unload' });
    expect((await runner.next<ResultMessage>(m => m.type === 'result')).code).toBe('STALE_JOB_STAGE');
    expect(sim.contracts.progression.credits).toBe(0);
    van.x = 52; van.z = -48;
    await runner.next<Snapshot>(m => m.type === 'snapshot' && m.contracts.active?.stageId === 'unload');
    const finish = { type: 'command', id: 'unload-once', action: 'job_interact', target: instanceId, value: 'unload' };
    runner.send(finish); const result = await runner.next<ResultMessage>(m => m.type === 'result'); expect(result.code).toBe('JOB_COMPLETE');
    const a = await driver.next<Snapshot>(m => m.type === 'snapshot' && m.contracts.progression.completed === 1);
    const b = await runner.next<Snapshot>(m => m.type === 'snapshot' && m.tick === a.tick);
    expect(a.contracts).toEqual(b.contracts); expect(a.contracts.progression.credits).toBe(100);
    expect(new Set(a.contracts.recent[0]!.participants)).toEqual(new Set([welcome.playerId, other.playerId]));
    runner.send(finish); expect(await runner.next<ResultMessage>(m => m.type === 'result')).toEqual(result);
    expect(sim.contracts.progression.completed).toBe(1);
  });

  it('persists public free-roam cargo and the same bearer identity through a server restart', async () => {
    const running = await start(), client = await peer(running.url);
    client.send({ type: 'join', mode: 'public', gameplay: 'freeroam', name: 'Aadi' });
    const welcome = await client.next<WelcomeMessage>(m => m.type === 'welcome');
    const sim = running.service.rooms.get(welcome.room)!.sim;
    const van = sim.vehicles.get('van-01')!, player = sim.players.get(welcome.playerId)!;
    van.x = player.x = -48; van.z = player.z = -68;
    for (const message of [
      { type: 'command', id: 'job', action: 'job_start', target: 'clinic-restock' },
      { type: 'command', id: 'seat', action: 'enter', target: 'van-01' },
      { type: 'command', id: 'load', action: 'job_interact', target: 'job-1', value: 'load' },
    ]) { client.send(message); expect((await client.next<ResultMessage>(m => m.type === 'result')).ok).toBe(true); }
    services.splice(services.indexOf(running.service), 1); await running.service.close();
    const file = await fs.readFile(path.join(running.directory, `${welcome.room}.json`), 'utf8');
    expect(file).not.toContain(welcome.token);
    const restored = await start(running.directory), returning = await peer(restored.url);
    returning.send({ type: 'join', mode: 'public', gameplay: 'freeroam', room: welcome.room, token: welcome.token, name: 'Aadi' });
    const resumed = await returning.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(resumed.playerId).toBe(welcome.playerId); expect(resumed.gameplay).toBe('freeroam');
    expect(resumed.snapshot.contracts.active).toMatchObject({ jobId: 'clinic-restock', stageId: 'drive', cargo: true, vehicleId: 'van-01' });
    expect(resumed.snapshot.vehicles.find(v => v.id === 'van-01')!.occupants).toEqual([null, null, null, null]);
    returning.send({ type: 'command', id: 'load', action: 'job_interact', target: 'job-1', value: 'load' });
    expect((await returning.next<ResultMessage>(m => m.type === 'result')).code).toBe('JOB_STAGE_COMPLETE');
    expect(restored.service.rooms.get(welcome.room)!.sim.contracts.active!.stageId).toBe('drive');
  });

  it('isolates public Story from public free roam and rejects gameplay mismatches without allocation', async () => {
    const running = await start(), story = await peer(running.url), roam = await peer(running.url);
    story.send({ type: 'join', mode: 'public', name: 'Story' });
    const first = await story.next<WelcomeMessage>(m => m.type === 'welcome');
    roam.send({ type: 'join', mode: 'public', gameplay: 'freeroam', room: first.room, name: 'Roam' });
    const error = await roam.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error');
    expect(error.code).toBe('GAMEPLAY_MISMATCH'); expect(running.service.rooms.size).toBe(1);
    roam.send({ type: 'join', mode: 'public', gameplay: 'freeroam', name: 'Roam' });
    const next = await roam.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(next.room).not.toBe(first.room); expect(first.snapshot.gameplay).toBe('story');
    roam.send({ type: 'command', id: 'forged-reward', action: 'job_start', target: 'clinic-restock', reward: 1000 });
    expect((await roam.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error')).code).toBe('INVALID_MESSAGE');
    expect(running.service.rooms.get(next.room)!.sim.contracts.progression.credits).toBe(0);
  });

  it('loads a legacy schema-one Story room with its original identity and progress', async () => {
    const running = await start(), client = await peer(running.url);
    client.send({ type: 'join', mode: 'private', name: 'Aadi' });
    const welcome = await client.next<WelcomeMessage>(m => m.type === 'welcome');
    client.send({ type: 'command', id: 'keys', action: 'interact', target: 'garage' });
    expect((await client.next<ResultMessage>(m => m.type === 'result')).ok).toBe(true);
    services.splice(services.indexOf(running.service), 1); await running.service.close();
    const filename = path.join(running.directory, `${welcome.room}.json`);
    const legacy = JSON.parse(await fs.readFile(filename, 'utf8'));
    legacy.simulation.schema = 1; legacy.simulation.contentVersion = '0.4.0';
    delete legacy.simulation.gameplay; delete legacy.simulation.contracts;
    await fs.writeFile(filename, JSON.stringify(legacy));
    const restarted = await start(running.directory), returning = await peer(restarted.url);
    returning.send({ type: 'join', mode: 'private', room: welcome.room, token: welcome.token, name: 'Aadi' });
    const resumed = await returning.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(resumed.playerId).toBe(welcome.playerId); expect(resumed.gameplay).toBe('story');
    expect(resumed.snapshot.mission.stage).toBe('car'); expect(resumed.snapshot.mission.revision).toBe(1);
    expect(resumed.snapshot.contracts.progression.completed).toBe(0);
    expect(JSON.parse(await fs.readFile(`${filename}.legacy-v1.bak`, 'utf8'))).toEqual(legacy);
  });
});
