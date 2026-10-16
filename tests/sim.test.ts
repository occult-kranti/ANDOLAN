import { describe, it, expect } from 'vitest';
import { Simulation, WORLD, isBlocked } from '../packages/sim/src/index.js';
import { CAMPAIGN } from '../packages/content/src/index.js';
import { parseClientMessage, type CommandMessage, type InputMessage } from '../packages/protocol/src/index.js';

const input = (seq: number, overrides: Partial<InputMessage> = {}): InputMessage => ({ type: 'input', seq, moveX: 0, moveZ: 0, forward: 0, turn: 0, ...overrides });
const command = (id: string, action: CommandMessage['action'], extras: Partial<CommandMessage> = {}): CommandMessage => ({ type: 'command', id, action, ...extras });
const fresh = () => { const sim = new Simulation('TESTROOM'); sim.addPlayer('p1', 'Aadi'); return sim; };
function atTarget(sim: Simulation, playerId = 'p1') {
  const point = WORLD.landmarks.find(l => l.id === sim.mission.targetId)!;
  const player = sim.players.get(playerId)!;
  if (player.vehicleId) { const car = sim.vehicles.get(player.vehicleId)!; car.x = point.x; car.z = point.z; car.speed = 0; }
  player.x = point.x; player.z = point.z;
}
function atFirstChoice(sim: Simulation) {
  sim.command('p1', command('start-keys', 'interact'));
  sim.command('p1', command('start-car', 'enter'));
  atTarget(sim); sim.step(); sim.command('p1', command('start-exit', 'exit'));
  for (const player of sim.players.values()) atTarget(sim, player.id);
}

describe('authoritative original simulation', () => {
  it('strictly rejects client coordinates, forged identity and non-finite input', () => {
    expect(parseClientMessage({ ...input(1), x: 90 })).toBeNull();
    expect(parseClientMessage({ ...input(1), moveX: Infinity })).toBeNull();
    expect(parseClientMessage({ ...command('x', 'enter'), playerId: 'victim' })).toBeNull();
    expect(parseClientMessage({ ...input(1), moveX: 1 })).not.toBeNull();
  });

  it('bounds movement, expires stale intent and rejects input sequence replay', () => {
    const sim = fresh(), player = sim.players.get('p1')!;
    const initial = player.x;
    expect(sim.input('p1', input(2, { moveX: 1 }))).toBe(true);
    expect(sim.input('p1', input(1, { moveX: -1 }))).toBe(false);
    for (let i = 0; i < 100; i++) sim.step();
    expect(player.x).toBeGreaterThan(initial);
    expect(player.x - initial).toBeLessThan(1.6);
    player.x = 99.4; player.z = 48;
    for (let i = 3; i < 30; i++) { sim.input('p1', input(i, { moveX: 1 })); sim.step(); }
    expect(player.x).toBeLessThanOrEqual(99.5);
    expect(isBlocked(player.x, player.z)).toBe(false);
  });

  it('resolves simultaneous vehicle requests to unique seats and idempotently returns duplicates', () => {
    const sim = fresh(); sim.addPlayer('p2', 'Noor');
    const first = sim.command('p1', command('enter-a', 'enter', { target: 'compact-01' }));
    const duplicate = sim.command('p1', command('enter-a', 'exit'));
    const second = sim.command('p2', command('enter-b', 'enter', { target: 'compact-01' }));
    expect(first.ok).toBe(true); expect(duplicate).toEqual(first); expect(second.ok).toBe(true);
    expect(sim.vehicles.get('compact-01')!.occupants.slice(0, 2)).toEqual(['p1', 'p2']);
    expect(sim.players.get('p1')!.seat).toBe(0); expect(sim.players.get('p2')!.seat).toBe(1);
    sim.input('p2', input(1, { forward: 1 })); sim.step();
    expect(sim.vehicles.get('compact-01')!.speed).toBe(0);
    sim.input('p1', input(1, { forward: 1 })); sim.step();
    expect(sim.vehicles.get('compact-01')!.speed).toBeGreaterThan(0);
  });

  it('disconnect releases the driver, stops the vehicle and reconnect creates no duplicated occupancy', () => {
    const sim = fresh(); sim.command('p1', command('e', 'enter'));
    sim.input('p1', input(1, { forward: 1 })); sim.step(); sim.disconnectPlayer('p1');
    const car = sim.vehicles.get('compact-01')!;
    expect(car.occupants).toEqual([null, null, null, null]); expect(car.speed).toBe(0);
    expect(sim.players.get('p1')!.vehicleId).toBeNull();
    sim.connectPlayer('p1');
    expect(sim.command('p1', command('new-enter', 'enter')).ok).toBe(true);
    expect(car.occupants.filter(id => id === 'p1')).toHaveLength(1);
  });

  it('lets a passenger explicitly take a vacant wheel once, with competing claims and no inherited throttle', () => {
    const sim = fresh(); sim.addPlayer('p2', 'Noor'); sim.addPlayer('p3', 'Kavya');
    for (const player of sim.players.values()) { player.x = -52; player.z = 49; sim.command(player.id, command(`enter-${player.id}`, 'enter')); }
    expect(sim.command('p2', command('occupied', 'take_wheel')).code).toBe('DRIVER_OCCUPIED');
    sim.input('p2', input(1, { forward: 1 }));
    sim.disconnectPlayer('p1');
    const car = sim.vehicles.get('compact-01')!;
    expect(sim.players.get('p2')!.seat).toBe(1);
    const accepted = sim.command('p2', command('take-a', 'take_wheel'));
    expect(accepted.code).toBe('DRIVER_CLAIMED');
    expect(sim.command('p3', command('take-b', 'take_wheel')).code).toBe('DRIVER_OCCUPIED');
    expect(sim.command('p2', command('take-a', 'take_wheel'))).toEqual(accepted);
    expect(car.occupants).toEqual(['p2', null, 'p3', null]);
    sim.step(); expect(car.speed).toBe(0);
    sim.input('p2', input(2, { forward: 1 })); sim.step(); expect(car.speed).toBeGreaterThan(0);
  });

  it('rejects taking the wheel while moving or while on foot', () => {
    const sim = fresh(); sim.addPlayer('p2', 'Noor');
    expect(sim.command('p1', command('foot', 'take_wheel')).code).toBe('NOT_SEATED');
    sim.command('p1', command('driver', 'enter')); sim.command('p2', command('passenger', 'enter'));
    sim.disconnectPlayer('p1'); sim.vehicles.get('compact-01')!.speed = 2;
    expect(sim.command('p2', command('moving', 'take_wheel')).code).toBe('VEHICLE_MOVING');
  });

  it('choice prerequisites reject remote and out-of-order attempts', () => {
    const sim = fresh();
    expect(sim.command('p1', command('early', 'choice', { value: 'copy' })).code).toBe('CHOICE_UNAVAILABLE');
    sim.players.get('p1')!.x = 80;
    expect(sim.command('p1', command('far', 'interact', { target: 'garage' })).code).toBe('TOO_FAR');
    expect(sim.mission.stage).toBe('keys');
  });

  it('requires a private crew majority and keeps canonical modes separate', () => {
    const sim = fresh(); sim.addPlayer('p2', 'Noor');
    atTarget(sim); sim.command('p1', command('keys', 'interact'));
    sim.players.get('p1')!.x = -52;
    sim.command('p1', command('car', 'enter'));
    atTarget(sim); sim.step(); sim.command('p1', command('leave', 'exit'));
    atTarget(sim, 'p1'); atTarget(sim, 'p2');
    expect(sim.mission.trigger).toBe('choice');
    expect(sim.command('p1', command('vote1', 'choice', { value: 'copy' })).code).toBe('VOTE_RECORDED');
    expect(sim.mission.history).toHaveLength(0);
    expect(sim.command('p2', command('vote2', 'choice', { value: 'copy' })).code).toBe('CHOICE_ACCEPTED');
    expect(sim.mission.history).toHaveLength(1);
    expect(new Simulation('PUBLIC', 'public').mission.history).toHaveLength(0);
  });

  it('resolves an existing majority on disconnect exactly once and allows changing a ballot', () => {
    const sim = fresh(); sim.addPlayer('p2', 'Noor'); atFirstChoice(sim);
    expect(sim.command('p1', command('vote-a', 'choice', { value: 'ask' })).code).toBe('VOTE_RECORDED');
    expect(sim.command('p1', command('vote-copy', 'choice', { value: 'copy' })).code).toBe('VOTE_RECORDED');
    expect(sim.mission.votes).toEqual({ p1: 'copy' });
    sim.disconnectPlayer('p2');
    expect(sim.mission.history).toHaveLength(1); expect(sim.mission.history[0]!.choiceId).toBe('copy');
    expect(sim.mission.metrics.accountability).toBe(60);
    sim.disconnectPlayer('p2');
    expect(sim.mission.history).toHaveLength(1); expect(sim.mission.metrics.accountability).toBe(60);
  });

  it('does not canonize a vote when the server deliberately shuts down', () => {
    const sim = fresh(); sim.addPlayer('p2', 'Noor'); atFirstChoice(sim);
    sim.command('p1', command('vote-a', 'choice', { value: 'copy' }));
    sim.disconnectPlayer('p2', false); sim.disconnectPlayer('p1', false);
    expect(sim.mission.history).toHaveLength(0); expect(sim.mission.stage).toBe('receipt');
    const resumed = new Simulation('TESTROOM', 'private', sim.serialize());
    expect(resumed.mission.votes).toEqual({}); expect(resumed.mission.history).toHaveLength(0);
  });

  it('completes every authored stage and preserves final choice in its ending', () => {
    const sim = fresh(); let id = 0;
    const total = CAMPAIGN.reduce((n, chapter) => n + chapter.stages.length, 0);
    for (let guard = 0; !sim.mission.complete && guard < 100; guard++) {
      atTarget(sim);
      if (sim.mission.trigger === 'arrive') sim.step();
      else if (sim.mission.trigger === 'enter_vehicle') {
        const p = sim.players.get('p1')!, car = sim.vehicles.get('compact-01')!; car.x = p.x; car.z = p.z;
        expect(sim.command('p1', command(`c${++id}`, 'enter')).ok).toBe(true);
      } else {
        if (sim.players.get('p1')!.vehicleId) sim.command('p1', command(`c${++id}`, 'exit'));
        atTarget(sim);
        const choose = sim.mission.stage === 'hearing-choice' ? 'settlement' : sim.mission.choices[0]?.id;
        expect(sim.command('p1', command(`c${++id}`, sim.mission.trigger === 'choice' ? 'choice' : 'interact', { value: choose })).ok).toBe(true);
      }
    }
    expect(sim.mission.complete).toBe(true); expect(sim.mission.revision).toBe(total);
    expect(sim.mission.ending?.id).toBe('bargain');
    expect(new Set(sim.mission.evidence).size).toBe(sim.mission.evidence.length);
    const last = sim.mission.revision;
    expect(sim.command('p1', command('again', 'interact')).code).toBe('CAMPAIGN_COMPLETE');
    expect(sim.mission.revision).toBe(last);
  });

  it('restores checkpoints without occupancy or command duplication and rejects corrupt data', () => {
    const sim = fresh(); sim.command('p1', command('key', 'interact')); sim.command('p1', command('seat', 'enter'));
    const state = sim.serialize();
    const restored = new Simulation('TESTROOM', 'private', state);
    expect(restored.mission).toEqual(sim.mission);
    expect(restored.players.get('p1')!.connected).toBe(false);
    expect(restored.players.get('p1')!.vehicleId).toBeNull();
    restored.connectPlayer('p1');
    expect(restored.command('p1', command('key', 'interact')).code).toBe('STAGE_COMPLETE');
    expect(restored.mission.revision).toBe(sim.mission.revision);
    state.players[0]!.x = NaN;
    expect(() => new Simulation('TESTROOM', 'private', state)).toThrow('INVALID_CHECKPOINT');
  });

  it('retains command replay protection when a disconnected seat expires and rejoins after restart', () => {
    const sim = fresh();
    expect(sim.command('p1', command('persisted-key', 'interact')).ok).toBe(true);
    sim.removePlayer('p1');
    const restored = new Simulation('TESTROOM', 'private', sim.serialize());
    restored.addPlayer('p1', 'Aadi');
    const revision = restored.mission.revision;
    expect(restored.command('p1', command('persisted-key', 'enter')).code).toBe('STAGE_COMPLETE');
    expect(restored.mission.revision).toBe(revision);
    expect(restored.players.get('p1')!.vehicleId).toBeNull();
  });

  it('rejects partial metrics and unknown evidence, and restores authored presentation', () => {
    const sim = fresh();
    const partial = sim.serialize();
    delete (partial.mission.metrics as Partial<typeof partial.mission.metrics>).care;
    expect(() => new Simulation('TESTROOM', 'private', partial)).toThrow('INVALID_CHECKPOINT');
    const unknown = sim.serialize(); unknown.mission.evidence.push('__proto__');
    expect(() => new Simulation('TESTROOM', 'private', unknown)).toThrow('INVALID_CHECKPOINT');
    const presentation = sim.serialize(); presentation.mission.title = 'A forged title';
    expect(new Simulation('TESTROOM', 'private', presentation).mission.title).toBe(CAMPAIGN[0]!.title);
  });

  it('is deterministic for the same input stream and static collisions remain finite', () => {
    const a = fresh(), b = fresh();
    for (let tick = 0; tick < 400; tick++) {
      const packet = input(tick, { moveX: Math.sin(tick / 13), moveZ: Math.cos(tick / 17), sprint: tick % 5 === 0 });
      for (const sim of [a, b]) { sim.input('p1', packet); sim.step(); }
    }
    expect(a.snapshot()).toEqual(b.snapshot());
    const player = a.players.get('p1')!;
    expect(isBlocked(player.x, player.z)).toBe(false);
  });
});
