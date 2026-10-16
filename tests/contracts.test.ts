import { describe, expect, it } from 'vitest';
import { Simulation, WORLD } from '../packages/sim/src/index.js';
import { CONTRACTS } from '../packages/content/src/contracts.js';
import { parseClientMessage, type CommandAction, type CommandMessage } from '../packages/protocol/src/index.js';

const packet = (id: string, action: CommandAction, target?: string, value?: string): CommandMessage => ({ type: 'command', id, action, target, value });
let movementSerial = 0;
function free() { const sim = new Simulation('CONTRACTS', 'private', undefined, 'freeroam'); sim.addPlayer('a', 'Aadi'); sim.addPlayer('b', 'Noor'); return sim; }
function driveAt(sim: Simulation, who: string, vehicleId: string, targetId: string) {
  const actor = sim.players.get(who)!, vehicle = sim.vehicles.get(vehicleId)!, target = WORLD.landmarks.find(p => p.id === targetId)!;
  if (actor.vehicleId) { const current = sim.vehicles.get(actor.vehicleId)!; current.speed = 0; sim.command(who, packet(`fixture-exit-${++movementSerial}`, 'exit')); }
  vehicle.x = target.x; vehicle.z = target.z; vehicle.speed = 0;
  actor.x = target.x; actor.z = target.z;
  const entered = sim.command(who, packet(`fixture-enter-${++movementSerial}`, 'enter', vehicleId));
  expect(entered.ok).toBe(true);
}
function interact(sim: Simulation, who = 'a', id = `stage-${sim.contracts.revision}`) {
  const active = sim.contracts.active!;
  return sim.command(who, packet(id, 'job_interact', active.instanceId, active.stageId));
}
function at(sim: Simulation, who: string, targetId: string) { const target = WORLD.landmarks.find(p => p.id === targetId)!; const actor = sim.players.get(who)!; actor.x = target.x; actor.z = target.z; }
function loadedClinic() {
  const sim = free(); sim.command('a', packet('start', 'job_start', 'clinic-restock'));
  driveAt(sim, 'a', 'van-01', 'mill'); expect(interact(sim).ok).toBe(true); return sim;
}

describe('server-owned repeatable city contracts', () => {
  it('accepts a short preset horn and rejects arbitrary communication signals', () => {
    const sim = free();
    expect(sim.command('a', packet('horn', 'signal', undefined, 'horn')).code).toBe('SIGNAL_SENT');
    expect(sim.players.get('a')!.signalUntil).toBe(5);
    expect(sim.command('a', packet('free-text', 'signal', undefined, 'arbitrary-message')).code).toBe('UNKNOWN_SIGNAL');
    for (let i = 0; i < 101; i++) sim.step();
    expect(sim.players.get('a')!.signal).toBeNull();
  });

  it('separates gameplay from visibility and does not advance story in free roam', () => {
    const sim = free(); const before = sim.mission;
    expect(sim.command('a', packet('story', 'interact', 'garage')).code).toBe('STORY_REQUIRED');
    sim.step(); expect(sim.mission).toEqual(before);
    const story = new Simulation('STORY'); story.addPlayer('a', 'Aadi');
    expect(story.command('a', packet('free', 'job_start', 'clinic-restock')).code).toBe('FREEROAM_REQUIRED');
    expect(parseClientMessage({ type: 'join', mode: 'public', gameplay: 'freeroam', name: 'Aadi' })).not.toBeNull();
    expect(parseClientMessage({ ...packet('forged', 'job_start', 'clinic-restock'), credits: 10000 })).toBeNull();
  });

  it('starts a single shared job, rejects replacement and enforces reputation unlocks', () => {
    const sim = free();
    expect(sim.command('a', packet('locked', 'job_start', 'print-run')).code).toBe('JOB_LOCKED');
    const accepted = sim.command('a', packet('start', 'job_start', 'clinic-restock'));
    expect(accepted.code).toBe('JOB_STARTED');
    expect(sim.command('a', packet('start', 'job_start', 'district-circuit'))).toEqual(accepted);
    expect(sim.command('b', packet('replace', 'job_start', 'district-circuit')).code).toBe('JOB_ALREADY_ACTIVE');
    expect(sim.contracts.active!.jobId).toBe('clinic-restock'); expect(sim.contracts.nextInstance).toBe(2);
  });

  it('rejects remote pickup, wrong vehicle, passenger claims, motion and stale stage commands', () => {
    const sim = free(); sim.command('a', packet('start', 'job_start', 'clinic-restock'));
    expect(interact(sim, 'a', 'far').code).toBe('TOO_FAR');
    driveAt(sim, 'a', 'compact-01', 'mill'); expect(interact(sim, 'a', 'wrong').code).toBe('WRONG_VEHICLE');
    driveAt(sim, 'a', 'van-01', 'mill');
    at(sim, 'b', 'mill'); sim.command('b', packet('passenger', 'enter', 'van-01'));
    expect(interact(sim, 'b', 'passenger-load').code).toBe('DRIVER_REQUIRED');
    sim.vehicles.get('van-01')!.speed = 2;
    expect(interact(sim, 'a', 'moving').code).toBe('VEHICLE_MOVING'); sim.vehicles.get('van-01')!.speed = 0;
    expect(sim.command('a', packet('stale', 'job_interact', 'job-1', 'unload')).code).toBe('STALE_JOB_STAGE');
    expect(sim.contracts.active!.cargo).toBe(false); expect(sim.contracts.progression.credits).toBe(0);
  });

  it('keeps cargo in its actual vehicle and permits another player to unload exactly once', () => {
    const sim = loadedClinic(), van = sim.vehicles.get('van-01')!;
    const active = sim.contracts.active!;
    expect(active.vehicleId).toBe('van-01'); expect(active.cargo).toBe(true);
    at(sim, 'b', 'clinic');
    expect(interact(sim, 'b', 'remote-finish').code).toBe('CHECKPOINT_REQUIRED');
    sim.step(); expect(sim.contracts.active!.stageId).toBe('drive');
    van.x = 52; van.z = -48; sim.step(); expect(sim.contracts.active!.stageId).toBe('unload');
    van.x = -48; van.z = -68;
    expect(interact(sim, 'b', 'cargo-remote').code).toBe('CARGO_TOO_FAR');
    van.x = 52; van.z = -48;
    const completed = interact(sim, 'b', 'final-handover'); expect(completed.code).toBe('JOB_COMPLETE');
    expect(sim.contracts.active).toBeNull();
    expect(sim.contracts.progression).toEqual({ credits: 100, reputation: 2, project: 1, completed: 1 });
    expect(sim.contracts.recent[0]!.participants).toEqual(['a', 'b']);
    expect(sim.command('b', packet('final-handover', 'job_interact', active.instanceId, 'unload'))).toEqual(completed);
    expect(sim.command('a', packet('new-id-repeat', 'job_interact', active.instanceId, 'unload')).code).toBe('NO_ACTIVE_JOB');
    expect(sim.contracts.progression.credits).toBe(100);
    expect(sim.command('a', packet('cooldown', 'job_start', 'clinic-restock')).code).toBe('JOB_COOLDOWN');
  });

  it('refuses replacing the bound cargo carrier with a different vehicle', () => {
    const sim = loadedClinic();
    sim.command('a', packet('exit-loaded', 'exit'));
    driveAt(sim, 'a', 'compact-01', 'clinic'); sim.step();
    expect(sim.contracts.active!.stageId).toBe('drive');
    expect(sim.contracts.active!.vehicleId).toBe('van-01'); expect(sim.contracts.progression.completed).toBe(0);
  });

  it('claims a physically present empty recovery vehicle and requires an actual return route', () => {
    const sim = free(), car = sim.vehicles.get('compact-01')!;
    car.x = 82; car.z = 48;
    sim.command('a', packet('recovery', 'job_start', 'pool-car-recall'));
    expect(sim.contracts.active!.targetPosition).toEqual({ x: 82, z: 48 });
    expect(interact(sim, 'a', 'remote').code).toBe('TOO_FAR');
    at(sim, 'b', 'river'); sim.command('b', packet('occupy', 'enter', car.id)); at(sim, 'a', 'river');
    expect(interact(sim, 'a', 'occupied').code).toBe('RECOVERY_VEHICLE_OCCUPIED');
    sim.command('b', packet('leave', 'exit')); expect(interact(sim, 'a', 'claim').ok).toBe(true);
    expect(sim.contracts.active!.vehicleId).toBe(car.id); expect(sim.contracts.active!.stageId).toBe('check');
    driveAt(sim, 'a', car.id, 'garage'); sim.step(); expect(sim.contracts.active!.stageId).toBe('check');
    driveAt(sim, 'a', car.id, 'mill'); sim.step(); expect(sim.contracts.active!.stageId).toBe('return');
    driveAt(sim, 'a', car.id, 'garage'); expect(interact(sim, 'a', 'returned').code).toBe('JOB_COMPLETE');
    expect(sim.contracts.progression.credits).toBe(120);
  });

  it('orders timed checkpoints and grants no reward when the timer expires', () => {
    const sim = free(); sim.command('a', packet('start', 'job_start', 'district-circuit'));
    driveAt(sim, 'a', 'compact-01', 'garage'); expect(interact(sim).ok).toBe(true);
    driveAt(sim, 'a', 'compact-01', 'archive'); sim.step(); expect(sim.contracts.active!.stageId).toBe('mill');
    driveAt(sim, 'a', 'compact-01', 'mill'); sim.step(); expect(sim.contracts.active!.stageId).toBe('records');
    for (let i = 0; i < 3601; i++) sim.step();
    expect(sim.contracts.active).toBeNull(); expect(sim.contracts.recent[0]!.status).toBe('failed');
    expect(sim.contracts.progression).toEqual({ credits: 0, reputation: 0, completed: 0, project: 0 });
  });

  it('restricts cancellation, then permits a late join to recover an orphaned job', () => {
    const sim = free(); sim.command('a', packet('start', 'job_start', 'clinic-restock'));
    const instance = sim.contracts.active!.instanceId;
    expect(sim.command('b', packet('grief', 'job_cancel', instance)).code).toBe('JOB_OWNER_REQUIRED');
    sim.disconnectPlayer('a'); sim.step();
    expect(sim.command('b', packet('early', 'job_cancel', instance)).code).toBe('JOB_OWNER_REQUIRED');
    for (let i = 0; i < 601; i++) sim.step();
    expect(sim.command('b', packet('recover', 'job_cancel', instance)).code).toBe('JOB_CANCELLED');
    expect(sim.contracts.progression.credits).toBe(0); expect(sim.contracts.recent[0]!.status).toBe('cancelled');
  });

  it('preserves loaded cargo and contributions across reconnect/checkpoint restart', () => {
    const sim = loadedClinic(); sim.disconnectPlayer('a');
    const restored = new Simulation('CONTRACTS', 'private', sim.serialize());
    expect(restored.gameplay).toBe('freeroam'); expect(restored.contracts.active!.cargo).toBe(true);
    expect(restored.contracts.active!.vehicleId).toBe('van-01'); expect(restored.contracts.active!.participants).toEqual(['a']);
    restored.connectPlayer('b'); driveAt(restored, 'b', 'van-01', 'clinic'); restored.step();
    restored.command('b', packet('unseat', 'exit')); at(restored, 'b', 'clinic');
    expect(interact(restored, 'b', 'completed-after-restart').code).toBe('JOB_COMPLETE');
    const again = new Simulation('CONTRACTS', 'private', restored.serialize());
    again.connectPlayer('b');
    expect(again.command('b', packet('completed-after-restart', 'job_interact', 'job-1', 'unload')).code).toBe('JOB_COMPLETE');
    expect(again.contracts.progression.completed).toBe(1); expect(again.contracts.progression.credits).toBe(100);
  });

  it('rejects corrupted contract clocks, sequence counters and gameplay identities', () => {
    const sim = free(); sim.command('a', packet('circuit', 'job_start', 'district-circuit'));
    const missingDeadline = sim.serialize(); missingDeadline.contracts!.active!.deadlineAt = null;
    expect(() => new Simulation('CONTRACTS', 'private', missingDeadline)).toThrow('INVALID_CHECKPOINT');
    const movedDeadline = sim.serialize(); movedDeadline.contracts!.active!.deadlineAt = 1000;
    expect(() => new Simulation('CONTRACTS', 'private', movedDeadline)).toThrow('INVALID_CHECKPOINT');
    const reusedId = sim.serialize(); reusedId.contracts!.nextInstance = 1;
    expect(() => new Simulation('CONTRACTS', 'private', reusedId)).toThrow('INVALID_CHECKPOINT');
    const missingGameplay = sim.serialize(); delete missingGameplay.gameplay;
    expect(() => new Simulation('CONTRACTS', 'private', missingGameplay)).toThrow('INVALID_CHECKPOINT');
    const invalidGameplay = sim.serialize(); (invalidGameplay as unknown as { gameplay: string }).gameplay = 'broken';
    expect(() => new Simulation('CONTRACTS', 'private', invalidGameplay)).toThrow('INVALID_CHECKPOINT');
    const crossedGameplay = sim.serialize(); crossedGameplay.gameplay = 'story';
    expect(() => new Simulation('CONTRACTS', 'private', crossedGameplay)).toThrow('INVALID_CHECKPOINT');
    sim.command('a', packet('cancel', 'job_cancel', sim.contracts.active!.instanceId));
    const reusedOutcome = sim.serialize(); reusedOutcome.contracts!.nextInstance = 1;
    expect(() => new Simulation('CONTRACTS', 'private', reusedOutcome)).toThrow('INVALID_CHECKPOINT');
  });

  it('rejects cargo bindings incompatible with completed stages while preserving a valid second load', () => {
    const loaded = loadedClinic();
    const wrongVehicle = loaded.serialize(); wrongVehicle.contracts!.active!.vehicleId = 'compact-01';
    expect(() => new Simulation('CONTRACTS', 'private', wrongVehicle)).toThrow('INVALID_CHECKPOINT');
    const missingCargo = loaded.serialize(); missingCargo.contracts!.active!.cargo = false;
    expect(() => new Simulation('CONTRACTS', 'private', missingCargo)).toThrow('INVALID_CHECKPOINT');
    const print = free(); print.contracts.progression.reputation = 4;
    print.command('a', packet('print', 'job_start', 'print-run'));
    driveAt(print, 'a', 'compact-01', 'radio'); expect(interact(print).ok).toBe(true);
    const car = print.vehicles.get('compact-01')!; car.x = -68; car.z = 43;
    at(print, 'b', 'board'); expect(interact(print, 'b', 'first-delivery').ok).toBe(true);
    expect(print.contracts.active).toMatchObject({ stageId: 'load-notices', cargo: false, vehicleId: 'compact-01' });
    const restored = new Simulation('CONTRACTS', 'private', print.serialize());
    expect(restored.contracts.active).toMatchObject({ stageId: 'load-notices', cargo: false, vehicleId: 'compact-01' });
  });

  it('migrates schema-one Story saves without changing decisions, evidence or accumulated metrics', () => {
    const original = new Simulation('LEGACY'); original.addPlayer('a', 'Aadi');
    original.command('a', packet('keys', 'interact', 'garage'));
    const saved = original.serialize(); saved.schema = 1; saved.contentVersion = '0.4.0'; delete saved.gameplay; delete saved.contracts;
    saved.mission.metrics = { trust: 71, care: 67, accountability: 64 };
    saved.mission.evidence = ['delivery'];
    const before = JSON.stringify(saved);
    const migrated = new Simulation('LEGACY', 'private', saved);
    expect(migrated.gameplay).toBe('story'); expect(migrated.mission.stage).toBe('car');
    expect(migrated.mission.metrics).toEqual(saved.mission.metrics); expect(migrated.mission.evidence).toEqual(saved.mission.evidence);
    expect(migrated.serialize().schema).toBe(3); expect(migrated.contracts).toEqual({ active: null, progression: { credits: 0, reputation: 0, completed: 0, project: 0 }, cooldowns: {}, recent: [], nextInstance: 1, revision: 0 });
    expect(JSON.stringify(saved)).toBe(before);
    expect(() => new Simulation('LEGACY', 'private', saved, 'freeroam')).toThrow('INVALID_CHECKPOINT');
  });

  it('completes all five declarative jobs through their validated stage requirements', () => {
    for (const definition of CONTRACTS.filter(job => !job.once)) {
      const sim = free(); sim.contracts.progression.reputation = 4;
      expect(sim.command('a', packet('start', 'job_start', definition.id)).ok).toBe(true);
      for (let guard = 0; sim.contracts.active && guard < 20; guard++) {
        const active = sim.contracts.active, stage = definition.stages[active.stageIndex]!;
        if (stage.targetVehicleId) {
          const car = sim.vehicles.get(stage.targetVehicleId)!; const actor = sim.players.get('a')!;
          actor.x = car.x; actor.z = car.z;
        } else if ((stage.vehicle ?? 'none') !== 'none') driveAt(sim, 'a', active.vehicleId ?? (stage.vehicle === 'van' ? 'van-01' : 'compact-01'), stage.targetId);
        else {
          const carrier = active.vehicleId ? sim.vehicles.get(active.vehicleId)! : null;
          if (carrier) { const target = WORLD.landmarks.find(p => p.id === stage.targetId)!; carrier.x = target.x; carrier.z = target.z; carrier.speed = 0; }
          if (sim.players.get('a')!.vehicleId) sim.command('a', packet(`exit-${active.stageIndex}`, 'exit'));
          at(sim, 'a', stage.targetId);
        }
        if (stage.action === 'checkpoint') sim.step();
        else expect(interact(sim, 'a', `stage-${active.stageIndex}`).ok).toBe(true);
      }
      expect(sim.contracts.active).toBeNull(); expect(sim.contracts.progression.completed).toBe(1);
      expect(sim.contracts.progression.credits).toBe(definition.reward.credits);
    }
  });
});
