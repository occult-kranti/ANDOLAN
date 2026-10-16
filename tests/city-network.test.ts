import { afterEach, describe, expect, it } from 'vitest';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { WebSocket } from 'ws';
import { createGameServer } from '../apps/server/src/server.js';
import type { ResultMessage, ServerMessage, Snapshot, WelcomeMessage } from '../packages/protocol/src/index.js';
import { command, completeCity, walkAt } from './city-fixtures.js';

type Service = Awaited<ReturnType<typeof createGameServer>>;
const services: Service[] = [], directories: string[] = [], sockets: WebSocket[] = [];
async function start(dataDir?: string) {
  const directory = dataDir ?? await fs.mkdtemp('/tmp/andolan-city-');
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

describe('real multiplayer city mandate', () => {
  it.each(['private', 'public'] as const)('shares one in-person majority outcome, replay receipt and late join in %s rooms', async mode => {
    const running = await start(), a = await peer(running.url);
    a.send({ type: 'join', mode, gameplay: 'freeroam', name: 'Aadi' });
    const first = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    const b = await peer(running.url); b.send({ type: 'join', mode, gameplay: 'freeroam', room: first.room, name: 'Noor' });
    const second = await b.next<WelcomeMessage>(m => m.type === 'welcome');
    const sim = running.service.rooms.get(first.room)!.sim;
    // Fixtures establish the completed routes; browser QA separately uses actual movement.
    completeCity(sim, first.playerId); walkAt(sim, first.playerId, 'civic');
    a.send(command('city_choice', 'city-mandate', 'capture'));
    expect((await a.next<ResultMessage>(m => m.type === 'result')).code).toBe('CITY_VOTE_RECORDED');
    expect(sim.city.decision).toBeNull();
    b.send(command('city_choice', 'city-mandate', 'capture'));
    expect((await b.next<ResultMessage>(m => m.type === 'result')).code).toBe('TOO_FAR');
    walkAt(sim, second.playerId, 'civic');
    const decisive = command('city_choice', 'city-mandate', 'capture'); b.send(decisive);
    const receipt = await b.next<ResultMessage>(m => m.type === 'result'); expect(receipt.code).toBe('CITY_DECIDED');
    const seenA = await a.next<Snapshot>(m => m.type === 'snapshot' && m.city.decision?.route === 'capture');
    const seenB = await b.next<Snapshot>(m => m.type === 'snapshot' && m.tick === seenA.tick);
    expect(seenA.city).toEqual(seenB.city);
    const revision = sim.city.revision;
    b.send(decisive); expect(await b.next<ResultMessage>(m => m.type === 'result')).toEqual(receipt);
    expect(sim.city.revision).toBe(revision);
    const late = await peer(running.url); late.send({ type: 'join', mode, gameplay: 'freeroam', room: first.room, name: 'Late Crew' });
    const joined = await late.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(joined.snapshot.city).toEqual(seenA.city);
    if (mode === 'public') {
      services.splice(services.indexOf(running.service), 1); await running.service.close();
      const restarted = await start(running.directory), returning = await peer(restarted.url);
      returning.send({ type: 'join', mode, gameplay: 'freeroam', room: first.room, token: first.token, name: 'Aadi' });
      const resumed = await returning.next<WelcomeMessage>(m => m.type === 'welcome');
      expect(resumed.playerId).toBe(first.playerId); expect(resumed.snapshot.city).toEqual(seenA.city);
      returning.send(command('city_choice', 'city-mandate', 'reform'));
      expect((await returning.next<ResultMessage>(m => m.type === 'result')).code).toBe('CITY_ALREADY_DECIDED');
    }
  });

  it('prunes a disconnected ballot and never chooses a route during shutdown or restart', async () => {
    const running = await start(), a = await peer(running.url), b = await peer(running.url);
    a.send({ type: 'join', mode: 'public', gameplay: 'freeroam', name: 'Aadi' });
    const first = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    b.send({ type: 'join', mode: 'public', gameplay: 'freeroam', room: first.room, name: 'Noor' });
    const second = await b.next<WelcomeMessage>(m => m.type === 'welcome');
    const sim = running.service.rooms.get(first.room)!.sim;
    completeCity(sim, first.playerId); walkAt(sim, first.playerId, 'civic'); walkAt(sim, second.playerId, 'civic');
    a.send(command('city_choice', 'city-mandate', 'reform'));
    expect((await a.next<ResultMessage>(m => m.type === 'result')).code).toBe('CITY_VOTE_RECORDED');
    b.send(command('city_choice', 'city-mandate', 'capture'));
    expect((await b.next<ResultMessage>(m => m.type === 'result')).code).toBe('CITY_VOTE_RECORDED');
    b.socket.terminate();
    const pruned = await a.next<Snapshot>(m => m.type === 'snapshot' && m.city.votes[first.playerId] === 'reform' && !m.city.votes[second.playerId] && !m.players.find(p => p.id === second.playerId)!.connected);
    expect(pruned.city.decision).toBeNull();
    services.splice(services.indexOf(running.service), 1); await running.service.close();
    const restarted = await start(running.directory), returning = await peer(restarted.url);
    returning.send({ type: 'join', mode: 'public', gameplay: 'freeroam', room: first.room, token: first.token, name: 'Aadi' });
    const resumed = await returning.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(resumed.playerId).toBe(first.playerId); expect(resumed.snapshot.city.votes).toEqual({}); expect(resumed.snapshot.city.decision).toBeNull();
    returning.send(command('city_choice', 'city-mandate', 'reform'));
    expect((await returning.next<ResultMessage>(m => m.type === 'result')).code).toBe('CITY_DECIDED');
  });

  it('backs up a schema-two room while preserving its bearer identity and loaded cargo', async () => {
    const running = await start(), a = await peer(running.url);
    a.send({ type: 'join', mode: 'private', gameplay: 'freeroam', name: 'Aadi' });
    const first = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    const sim = running.service.rooms.get(first.room)!.sim, player = sim.players.get(first.playerId)!, van = sim.vehicles.get('van-01')!;
    van.x = player.x = -48; van.z = player.z = -68;
    for (const message of [command('job_start', 'clinic-restock'), command('enter', van.id), command('job_interact', 'job-1', 'load')]) {
      a.send(message); expect((await a.next<ResultMessage>(m => m.type === 'result')).ok).toBe(true);
    }
    services.splice(services.indexOf(running.service), 1); await running.service.close();
    const filename = path.join(running.directory, `${first.room}.json`);
    const legacy = JSON.parse(await fs.readFile(filename, 'utf8'));
    legacy.simulation.schema = 2; delete legacy.simulation.city;
    const original = JSON.stringify(legacy); await fs.writeFile(filename, original);
    const restarted = await start(running.directory), returning = await peer(restarted.url);
    returning.send({ type: 'join', mode: 'private', gameplay: 'freeroam', room: first.room, token: first.token, name: 'Aadi' });
    const resumed = await returning.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(resumed.playerId).toBe(first.playerId);
    expect(resumed.snapshot.contracts.active).toMatchObject({ jobId: 'clinic-restock', cargo: true, vehicleId: 'van-01', stageId: 'drive' });
    expect(resumed.snapshot.city.completedJobs).toEqual([]);
    expect(await fs.readFile(`${filename}.legacy-v2.bak`, 'utf8')).toBe(original);
  });
});
