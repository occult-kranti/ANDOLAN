import assert from 'node:assert/strict';
import test from 'node:test';
import { once } from 'node:events';
import { WebSocket } from 'ws';
import { ArenaSimulation } from '../../../yuga/shared/simulation.js';
import { YUGA_PROTOCOL } from '../../../yuga/shared/types.js';
import type { ServerMessage } from '../../../yuga/shared/types.js';
import { createArenaServer, parseArenaMessage } from '../../../yuga/server/server.js';
import { instantiateAuthority, resolveAuthorityFactory } from '../../../yuga/server/authority-factory.js';
import type { ArenaAuthorityFactory, ArenaAuthorityOptions } from '../../../yuga/server/authority-factory.js';
import { createNativePilotAuthority } from './vertical_simulation.js';

const options = { room: 'FIXTURE', seed: 17, duration: 30, botsPerTeam: 0 };
const join = { type: 'join', protocol: YUGA_PROTOCOL, heroId: 'rama', name: 'Factory probe' };
type Server = Awaited<ReturnType<typeof createArenaServer>>;
const unsafeFactory = (factory: unknown) => factory as ArenaAuthorityFactory;

async function peer(server: Server) {
  assert.ok(server.address && typeof server.address !== 'string');
  const socket = new WebSocket(`ws://127.0.0.1:${server.address.port}/ws`);
  const queued: ServerMessage[] = [];
  socket.on('message', data => queued.push(JSON.parse(data.toString())));
  await once(socket, 'open');
  async function next<K extends ServerMessage['type']>(type: K): Promise<Extract<ServerMessage, { type: K }>> {
    const deadline = Date.now() + 1200;
    while (Date.now() < deadline) {
      const index = queued.findIndex(row => row.type === type);
      if (index >= 0) return queued.splice(index, 1)[0] as Extract<ServerMessage, { type: K }>;
      await new Promise(resolve => setTimeout(resolve, 5));
    }
    throw Error(`missing ${type} from real server`);
  }
  return { socket, next, send: (message: unknown) => socket.send(JSON.stringify(message)) };
}

test('default factory preserves the exact existing planar constructor snapshot', () => {
  const actual = instantiateAuthority(resolveAuthorityFactory(undefined), options);
  assert.ok(actual instanceof ArenaSimulation);
  assert.deepEqual(actual.snapshot(), new ArenaSimulation(options).snapshot());
});

test('server factory receives a frozen config; room/seed remain transport-owned', () => {
  let received: Readonly<ArenaAuthorityOptions> | undefined;
  instantiateAuthority(value => { received = value; return new ArenaSimulation(value); }, options);
  assert.ok(Object.isFrozen(received));
  assert.deepEqual(received, options);
  assert.notEqual(received, options);
});

for (const value of [null, 'native', {}, 12]) {
  test(`non-callable factory ${JSON.stringify(value)} rejects before server listen`, async () => {
    await assert.rejects(createArenaServer({ port: 0, host: '127.0.0.1', authorityFactory: unsafeFactory(value) }), /authorityFactory must be a synchronous function/);
  });
}

for (const [name, patch] of Object.entries({
  invalid_room: { room: '../outside' },
  negative_seed: { seed: -1 },
  noninteger_seed: { seed: 1.1 },
  oversized_seed: { seed: 0x100000000 },
})) test(`invalid authority config ${name} is refused before calling plugin`, () => {
  let called = false;
  assert.throws(() => instantiateAuthority(value => { called = true; return new ArenaSimulation(value); }, { ...options, ...patch }), /valid room and uint32 seed/);
  assert.equal(called, false);
});

const invalid: Record<string, unknown> = {
  throws: () => { throw Error('private backend detail'); },
  undefined: () => undefined,
  resolved_promise: async (value: ArenaAuthorityOptions) => new ArenaSimulation(value),
  rejected_promise: async () => { throw Error('private rejected backend'); },
  wrong_room: (value: ArenaAuthorityOptions) => new ArenaSimulation({ ...value, room: 'OTHER' }),
  wrong_phase: (value: ArenaAuthorityOptions) => Object.assign(new ArenaSimulation(value), { phase: 'invalid' }),
  non_map_actors: (value: ArenaAuthorityOptions) => Object.assign(new ArenaSimulation(value), { actors: [] }),
  missing_step: (value: ArenaAuthorityOptions) => Object.assign(new ArenaSimulation(value), { step: null }),
};

for (const [name, authorityFactory] of Object.entries(invalid)) test(`real join safely refuses ${name} with no leaked room`, async () => {
  const server = await createArenaServer({ port: 0, host: '127.0.0.1', authorityFactory: unsafeFactory(authorityFactory) });
  try {
    const client = await peer(server); client.send(join);
    assert.deepEqual(await client.next('error'), { type: 'error', message: 'Arena authority unavailable. Create a new match.' });
    assert.equal(server.rooms.size, 0);
    assert.equal(client.socket.readyState, WebSocket.OPEN);
    // A malformed authority must not break the shared parser/transport either.
    client.send({ ...join, authority: 'file:///untrusted.ts' });
    assert.equal((await client.next('error')).message, 'Invalid arena message');
  } finally { await server.close(); }
});

test('a failed first player does not publish an empty room', async () => {
  const server = await createArenaServer({ port: 0, host: '127.0.0.1', authorityFactory: value => {
    const sim = new ArenaSimulation(value); sim.addPlayer = () => { throw Error('failed'); }; return sim;
  } });
  try {
    const client = await peer(server); client.send(join);
    assert.equal((await client.next('error')).message, 'Could not join this match');
    assert.equal(server.rooms.size, 0);
  } finally { await server.close(); }
});

test('one explicit instance serves both peers, reconnects and normal transport dispatch', async () => {
  const created: ArenaSimulation[] = [];
  let steps = 0, inputs = 0, commands = 0;
  const server = await createArenaServer({ port: 0, host: '127.0.0.1', simulation: { botsPerTeam: 0 }, authorityFactory: value => {
    const sim = new ArenaSimulation(value); created.push(sim);
    const step = sim.step.bind(sim), input = sim.input.bind(sim), command = sim.command.bind(sim);
    sim.step = dt => { steps++; step(dt); };
    sim.input = (id, intent) => { inputs++; return input(id, intent); };
    sim.command = (id, intent) => { commands++; return command(id, intent); };
    return sim;
  } });
  try {
    const host = await peer(server); host.send(join); const welcome = await host.next('welcome');
    const guest = await peer(server); guest.send({ ...join, room: welcome.room }); await guest.next('welcome');
    assert.equal(created.length, 1);
    assert.equal(server.rooms.get(welcome.room)?.sim, created[0]);
    host.send({ type: 'input', seq: 1, moveX: 0, moveZ: 1, yaw: 0, pitch: 0, fire: false, jump: false });
    host.send({ type: 'command', id: 'probe', action: 'upgrade', upgrade: 'vitality' });
    assert.equal((await host.next('result')).ok, true);
    await host.next('snapshot');
    assert.ok(steps > 0 && inputs === 1 && commands === 1);
    const closed = once(host.socket, 'close'); host.socket.close(); await closed;
    const reconnect = await peer(server); reconnect.send({ ...join, room: welcome.room, token: welcome.token });
    assert.equal((await reconnect.next('welcome')).id, welcome.id);
    assert.equal(created.length, 1);
  } finally { await server.close(); }
});

test('returning a previous room authority cannot alias another room', async () => {
  let shared: ArenaSimulation | undefined;
  const server = await createArenaServer({ port: 0, host: '127.0.0.1', simulation: { botsPerTeam: 0 }, authorityFactory: value => shared ??= new ArenaSimulation(value) });
  try {
    const first = await peer(server); first.send(join); const welcome = await first.next('welcome');
    const second = await peer(server); second.send(join);
    assert.equal((await second.next('error')).message, 'Arena authority unavailable. Create a new match.');
    assert.equal(server.rooms.size, 1);
    assert.equal(server.rooms.get(welcome.room)?.sim.room, welcome.room);
    assert.equal(server.rooms.get(welcome.room)?.sim.actors.size, 1);
  } finally { await server.close(); }
});

test('a public join cannot pick an authority or module', () => {
  assert.equal(parseArenaMessage({ ...join, authorityFactory: 'native' }), null);
  assert.equal(parseArenaMessage({ ...join, module: 'file:///plugin.ts' }), null);
});

test('native pilot factory refuses an unconnected backend', () => {
  assert.throws(() => createNativePilotAuthority(options), /must connect before creating a room/);
});
