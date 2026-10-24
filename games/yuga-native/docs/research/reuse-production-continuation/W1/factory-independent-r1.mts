/** Independent boundary/transport probes. Does not alter the authority source. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { WebSocket } from 'ws';
import { createArenaServer, parseArenaMessage } from '../../../yuga/server/server.js';
import { ArenaSimulation } from '../../../yuga/shared/simulation.js';
import { instantiateAuthority, resolveAuthorityFactory } from '../../../yuga/server/authority-factory.js';

const output = process.argv[2];
if (!output || !path.isAbsolute(output) || fs.existsSync(output)) throw Error('Provide fresh absolute report filename');
const files = ['games/yuga/server/server.ts', 'games/yuga/server/authority-factory.ts', 'games/yuga-native/tools/arena-bridge-pilot/vertical_simulation.ts'];
const pins = files.map(file => ({ file, sha256: createHash('sha256').update(fs.readFileSync(file)).digest('hex') }));
const checks: { id: string; pass: boolean; detail?: string }[] = [];
const check = async (id: string, run: () => unknown | Promise<unknown>) => {
  try { await run(); checks.push({ id, pass: true }); }
  catch (error) { checks.push({ id, pass: false, detail: String(error) }); }
};
const join = { type: 'join', protocol: 2, name: 'Independent', heroId: 'rama' };
async function peer(port: number) {
  const socket = new WebSocket(`ws://127.0.0.1:${port}/ws`);
  const queue: any[] = [];
  socket.on('message', data => queue.push(JSON.parse(String(data))));
  await new Promise<void>((resolve, reject) => { socket.once('open', resolve); socket.once('error', reject); });
  async function next(type: string) {
    const deadline = Date.now() + 2000;
    while (Date.now() < deadline) {
      const index = queue.findIndex(value => value.type === type);
      if (index >= 0) return queue.splice(index, 1)[0];
      await new Promise(resolve => setTimeout(resolve, 5));
    }
    throw Error(`Missing ${type} response`);
  }
  return { socket, next, send: (data: unknown) => socket.send(JSON.stringify(data)) };
}

await check('default-factory-is-existing-planar-engine', () => {
  const authority = instantiateAuthority(resolveAuthorityFactory(undefined), { room: 'BOUNDARY', seed: 31, botsPerTeam: 0 });
  assert(authority instanceof ArenaSimulation);
  assert.equal(authority.room, 'BOUNDARY');
  assert.equal(authority.snapshot().structures.length, 14);
});
await check('caller-option-mutation-cannot-change-factory-options', () => {
  const options = { room: 'FROZEN', seed: 55, botsPerTeam: 0 };
  instantiateAuthority(value => {
    assert(Object.isFrozen(value));
    assert.notEqual(value, options);
    assert.throws(() => { (value as any).room = 'CHANGED'; });
    return new ArenaSimulation(value);
  }, options);
  assert.equal(options.room, 'FROZEN');
});
for (const bad of [null, 4, {}, 'native', Promise.resolve(() => {})]) {
  await check(`invalid-factory-${typeof bad}-${String(bad)}`, async () => {
    await assert.rejects(createArenaServer({ port: 0, host: '127.0.0.1', authorityFactory: bad as any }), /authorityFactory/);
  });
}
await check('bad-identity-is-rejected-before-factory-is-called', () => {
  let calls = 0;
  const factory = (value: any) => { calls++; return new ArenaSimulation(value); };
  for (const options of [{ room: 'x', seed: 1 }, { room: 'HAS SPACES', seed: 1 }, { room: 'VALID', seed: -1 }, { room: 'VALID', seed: 2 ** 32 }, { room: 'VALID', seed: 1.1 }]) {
    assert.throws(() => instantiateAuthority(factory, options), /valid room/);
  }
  assert.equal(calls, 0);
});
const factories: [string, (value: any) => any][] = [
  ['throw', () => { throw Error('private adapter detail'); }],
  ['null', () => null],
  ['async-reject', () => Promise.reject(Error('private rejected adapter detail'))],
  ['thenable', () => ({ then() { throw Error('thenable must not be invoked'); } })],
  ['wrong-room', value => new ArenaSimulation({ ...value, room: 'WRONG' })],
  ['missing-step', value => Object.assign(new ArenaSimulation(value), { step: undefined })],
  ['bad-actors', value => Object.assign(new ArenaSimulation(value), { actors: {} })],
  ['throw-on-add', value => Object.assign(new ArenaSimulation(value), { addPlayer() { throw Error('private add error'); } })],
];
for (const [name, invalid] of factories) {
  await check(`real-transport-${name}-recovers-without-room-leak`, async () => {
    let healthy = false;
    const server = await createArenaServer({ port: 0, host: '127.0.0.1', simulation: { botsPerTeam: 0 }, authorityFactory: value => healthy ? new ArenaSimulation(value) : invalid(value) });
    const address = server.address;
    if (!address || typeof address === 'string') throw Error('Missing port');
    const client = await peer(address.port);
    try {
      client.send(join);
      const failure = await client.next('error');
      assert(!failure.message.includes('private'));
      assert.equal(server.rooms.size, 0);
      healthy = true;
      client.send(join);
      const welcome = await client.next('welcome');
      assert.equal(server.rooms.size, 1);
      assert.equal(server.rooms.get(welcome.room)!.identities.size, 1);
      assert.equal(welcome.snapshot.room, welcome.room);
    } finally { client.socket.terminate(); await server.close(); }
  });
}
await check('transport-generated-identity-overrides-untyped-simulation-options', async () => {
  let seen: any;
  const server = await createArenaServer({ port: 0, host: '127.0.0.1', simulation: { room: 'FORGED', seed: 7, botsPerTeam: 0 } as any, authorityFactory: value => { seen = value; return new ArenaSimulation(value); } });
  const address = server.address;
  if (!address || typeof address === 'string') throw Error('Missing port');
  const client = await peer(address.port);
  try {
    client.send(join); const welcome = await client.next('welcome');
    assert.notEqual(welcome.room, 'FORGED'); assert.equal(seen.room, welcome.room);
    assert.equal(welcome.snapshot.room, welcome.room); assert(Object.isFrozen(seen));
  } finally { client.socket.terminate(); await server.close(); }
});
await check('public-message-cannot-select-factory-or-module', () => {
  for (const key of ['authorityFactory', 'module', 'authority']) assert.equal(parseArenaMessage({ ...join, [key]: 'native' }), null);
});
await check('reviewed-source-stayed-frozen', () => {
  for (const pin of pins) assert.equal(createHash('sha256').update(fs.readFileSync(pin.file)).digest('hex'), pin.sha256);
});
const report = { kind: 'independent-authority-factory-boundary', source: pins, checks, passed: checks.every(row => row.pass), scope: 'Typed boundary and actual loopback WebSocket failures/recovery; no rendered native clients, full match, service benchmark or untrusted-plugin sandbox.' };
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ passed: report.passed, checks: checks.length, failures: checks.filter(row => !row.pass) }));
if (!report.passed) process.exitCode = 1;
