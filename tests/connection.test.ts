import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { connectOnline, getServerUrl, validateServerUrl, type Callbacks, type Connection } from '../apps/client/src/connection';
import { Simulation } from '../packages/sim/src/index';
import { PROTOCOL_VERSION, type ClientMessage, type ServerMessage, type WelcomeMessage } from '../packages/protocol/src/index';

/** A controllable transport, so delayed close callbacks and silent links are reproducible. */
class FakeSocket extends EventTarget {
  static readonly OPEN = 1;
  static readonly instances: FakeSocket[] = [];
  readyState = 0;
  readonly sent: ClientMessage[] = [];
  constructor(readonly url: string) { super(); FakeSocket.instances.push(this); }
  send(data: string) {
    if (this.readyState !== FakeSocket.OPEN) throw new Error('Sending on a closed transport');
    this.sent.push(JSON.parse(data) as ClientMessage);
  }
  close() { this.readyState = 2; }
  open() { this.readyState = FakeSocket.OPEN; this.dispatchEvent(new Event('open')); }
  receive(message: ServerMessage) { this.dispatchEvent(new MessageEvent('message', { data: JSON.stringify(message) })); }
  finishClose(code: number) {
    this.readyState = 3;
    this.dispatchEvent(Object.assign(new Event('close'), { code }));
  }
}

const connections: Connection[] = [];
const room = 'CREW-TEST';
const playerId = 'player-a';
const token = 'a'.repeat(48);
function welcome(): WelcomeMessage {
  const sim = new Simulation(room, 'private'); sim.addPlayer(playerId, 'Aadi');
  return { type: 'welcome', protocol: PROTOCOL_VERSION, playerId, token, room, mode: 'private', gameplay: 'story', snapshot: sim.snapshot() };
}
function setup() {
  const callbacks = { snapshot: vi.fn(), welcome: vi.fn(), status: vi.fn(), error: vi.fn() } satisfies Callbacks;
  const connection = connectOnline({ type: 'join', mode: 'private', name: 'Aadi' }, callbacks);
  connections.push(connection);
  return { callbacks, connection, socket: FakeSocket.instances.at(-1)! };
}
function join() {
  const state = setup(); state.socket.open(); state.socket.receive(welcome()); return state;
}
const command = { type: 'command', id: 'choice-one', action: 'choice', value: 'supplies' } as const;
const input = { type: 'input', seq: 1, moveX: 1, moveZ: 0, forward: 0, turn: 0 } as const;

beforeEach(() => {
  vi.useFakeTimers(); vi.setSystemTime(new Date('2026-10-16T01:00:00Z'));
  FakeSocket.instances.length = 0;
  const storage = new Map<string, string>();
  vi.stubGlobal('WebSocket', FakeSocket);
  vi.stubGlobal('window', globalThis);
  vi.stubGlobal('location', new URL('https://andolan.example/'));
  const preferences = new Map<string, string>();
  vi.stubGlobal('localStorage', { getItem: (key: string) => preferences.get(key) ?? null, setItem: (key: string, value: string) => preferences.set(key, value) });
  vi.stubGlobal('sessionStorage', { getItem: (key: string) => storage.get(key) ?? null, setItem: (key: string, value: string) => storage.set(key, value) });
  vi.stubEnv('VITE_SERVER_URL', '');
});
afterEach(() => {
  for (const connection of connections.splice(0)) connection.close();
  vi.clearAllTimers(); vi.useRealTimers(); vi.unstubAllGlobals(); vi.unstubAllEnvs();
});

describe('online connection recovery', () => {
  it('rejects an older server with a recovery message before accepting identity or rendering', () => {
    const { callbacks, socket, connection } = setup(); socket.open();
    socket.receive({ ...welcome(), protocol: PROTOCOL_VERSION - 1 });
    connection.command(command); connection.input(input);
    socket.finishClose(1000); vi.advanceTimersByTime(30_000);
    expect(callbacks.welcome).not.toHaveBeenCalled(); expect(callbacks.snapshot).not.toHaveBeenCalled();
    expect(callbacks.error).toHaveBeenCalledWith(expect.stringMatching(/server needs the City Reform update/));
    expect(FakeSocket.instances).toHaveLength(1); expect(socket.sent).toHaveLength(1);
  });
  it('rejects missing city state and ignores snapshots before the welcome handshake', () => {
    const { callbacks, socket } = setup(); socket.open();
    socket.receive(welcome().snapshot); expect(callbacks.snapshot).not.toHaveBeenCalled();
    const malformed = welcome(); delete (malformed.snapshot as Partial<typeof malformed.snapshot>).city;
    socket.receive(malformed);
    expect(callbacks.error).toHaveBeenCalledWith(expect.stringMatching(/server needs the City Reform update/));
    expect(callbacks.welcome).not.toHaveBeenCalled(); expect(callbacks.snapshot).not.toHaveBeenCalled();
  });
  it('leaves a superseded identity paused without automatically reclaiming it', () => {
    const { callbacks, connection, socket } = join();
    socket.finishClose(4001);
    const sentBefore = socket.sent.length;
    connection.command(command); connection.input(input);
    vi.advanceTimersByTime(30_000);
    expect(FakeSocket.instances).toHaveLength(1);
    expect(socket.sent).toHaveLength(sentBefore);
    expect(callbacks.status).toHaveBeenLastCalledWith(expect.stringMatching(/another tab/i), false);
    connection.reconnect!();
    const resumed = FakeSocket.instances[1]!; resumed.open();
    expect(resumed.sent[0]).toMatchObject({ type: 'join', room, token });
    resumed.receive(welcome());
    expect(callbacks.welcome).toHaveBeenLastCalledWith(playerId, room, false);
  });

  it('ignores delayed close and message events from the previous connection attempt', () => {
    const { callbacks, connection, socket } = join();
    connection.reconnect!();
    const replacement = FakeSocket.instances[1]!; replacement.open(); replacement.receive(welcome());
    const welcomes = callbacks.welcome.mock.calls.length;
    socket.finishClose(1000);
    socket.receive({ ...welcome(), playerId: 'obsolete-player' });
    vi.advanceTimersByTime(1_600);
    expect(FakeSocket.instances).toHaveLength(2);
    expect(callbacks.welcome).toHaveBeenCalledTimes(welcomes);
    expect(callbacks.welcome).toHaveBeenLastCalledWith(playerId, room, false);
    connection.command(command);
    expect(replacement.sent.at(-1)).toEqual(command);
  });

  it('pauses both input and commands during silent state loss and resumes the same identity on a fresh snapshot', () => {
    const { callbacks, connection, socket } = join();
    connection.input(input); connection.command(command);
    const sentBefore = socket.sent.length;
    vi.advanceTimersByTime(2_500);
    expect(callbacks.status.mock.calls.at(-1)?.[1]).toBe(false);
    connection.input({ ...input, seq: 2 }); connection.command({ ...command, id: 'stale-choice' });
    expect(socket.sent).toHaveLength(sentBefore);
    const fresh = welcome().snapshot; fresh.tick += 50;
    socket.receive(fresh);
    expect(callbacks.status.mock.calls.at(-1)?.[1]).toBe(true);
    expect(callbacks.snapshot).toHaveBeenLastCalledWith(fresh);
    expect(callbacks.welcome).toHaveBeenCalledTimes(1);
    expect(callbacks.welcome).toHaveBeenLastCalledWith(playerId, room, false);
    connection.command({ ...command, id: 'fresh-choice' });
    expect(socket.sent.at(-1)).toMatchObject({ type: 'command', id: 'fresh-choice' });
    expect(socket.sent.filter(message => message.type === 'command' && message.id === 'stale-choice')).toHaveLength(0);
  });

  it.each(['ROOM_REQUIRED', 'ROOM_NOT_FOUND', 'ROOM_FULL', 'SERVER_FULL', 'INVALID_TOKEN', 'GAMEPLAY_MISMATCH'])('stops automatic retry after %s', code => {
    const { callbacks, socket } = setup(); socket.open();
    socket.receive({ type: 'error', code, message: 'This room cannot be joined.' });
    socket.finishClose(1008);
    vi.advanceTimersByTime(30_000);
    expect(FakeSocket.instances).toHaveLength(1);
    expect(callbacks.error).toHaveBeenCalledWith('This room cannot be joined.');
    expect(callbacks.status.mock.calls.at(-1)?.[1]).toBe(false);
    expect(callbacks.welcome).not.toHaveBeenCalled();
  });

  it('retries an unexpected drop using the accepted room and identity', () => {
    const { callbacks, socket } = join(); socket.finishClose(1006);
    vi.advanceTimersByTime(1_500);
    expect(FakeSocket.instances).toHaveLength(2);
    const resumed = FakeSocket.instances[1]!; resumed.open();
    expect(resumed.sent[0]).toEqual({ type: 'join', mode: 'private', name: 'Aadi', room, token });
    resumed.receive(welcome());
    expect(callbacks.welcome).toHaveBeenLastCalledWith(playerId, room, false);
    expect(callbacks.status.mock.calls.at(-1)?.[1]).toBe(true);
  });
});

describe('server selection and identity isolation', () => {
  it('normalizes secure game addresses and allows only loopback insecure development', () => {
    expect(validateServerUrl('https://crew.example')).toBe('wss://crew.example/ws');
    expect(validateServerUrl('wss://crew.example/socket')).toBe('wss://crew.example/socket');
    expect(validateServerUrl('http://localhost:3001')).toBe('ws://localhost:3001/ws');
    for (const value of ['ws://crew.example/ws', 'https://user:secret@crew.example', 'https://crew.example/?token=secret', 'https://crew.example/#secret', 'javascript:alert(1)', 'invalid']) expect(validateServerUrl(value)).toBeUndefined();
  });

  it('does not attempt a fake same-origin server on the public static site', () => {
    vi.stubGlobal('location', new URL('https://occult-kranti.github.io/ANDOLAN/'));
    expect(getServerUrl()).toBeUndefined();
    const { callbacks } = setup();
    expect(FakeSocket.instances).toHaveLength(0);
    expect(callbacks.status).toHaveBeenLastCalledWith(expect.stringMatching(/choose a game server/i), false);
  });

  it('uses a validated runtime server on the static site without rebuilding the client', () => {
    vi.stubGlobal('location', new URL('https://occult-kranti.github.io/ANDOLAN/'));
    localStorage.setItem('andolan.server', 'https://crew.example');
    const { socket } = setup();
    expect(socket.url).toBe('wss://crew.example/ws');
  });

  it('retains identity on the same server/gameplay while withholding it from another server or mode', () => {
    join();
    const callbacks = { snapshot: vi.fn(), welcome: vi.fn(), status: vi.fn(), error: vi.fn() };
    for (const [server, gameplay, expectedToken] of [
      ['wss://andolan.example/ws', 'story', token],
      ['wss://another.example/ws', 'story', undefined],
      ['wss://andolan.example/ws', 'freeroam', undefined],
    ] as const) {
      const connection = connectOnline({ type: 'join', mode: 'private', gameplay, room, name: 'Aadi' }, callbacks, server);
      connections.push(connection);
      const socket = FakeSocket.instances.at(-1)!; socket.open();
      expect((socket.sent[0] as { token?: string }).token).toBe(expectedToken);
    }
  });

  it('migrates a legacy Story token only to its same-origin Story server', () => {
    sessionStorage.setItem(`andolan.room.${room}`, token);
    const callbacks = { snapshot: vi.fn(), welcome: vi.fn(), status: vi.fn(), error: vi.fn() };
    const external = connectOnline({ type: 'join', mode: 'private', room, name: 'Aadi' }, callbacks, 'wss://another.example/ws'); connections.push(external);
    let socket = FakeSocket.instances.at(-1)!; socket.open(); expect((socket.sent[0] as { token?: string }).token).toBeUndefined();
    const local = connectOnline({ type: 'join', mode: 'private', room, name: 'Aadi' }, callbacks); connections.push(local);
    socket = FakeSocket.instances.at(-1)!; socket.open(); expect((socket.sent[0] as { token?: string }).token).toBe(token);
  });
});
