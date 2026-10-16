import { describe, expect, it } from 'vitest';
import { CITY_OUTCOMES, CONTRACTS, getEffectiveJobReward } from '../packages/content/src/contracts.js';
import { PROTOCOL_VERSION, parseClientMessage, type Mode } from '../packages/protocol/src/index.js';
import { Simulation } from '../packages/sim/src/index.js';
import { command, completeCity, completeJob, walkAt } from './city-fixtures.js';

function free(mode: Mode = 'private') {
  const sim = new Simulation('CITY-TEST', mode, undefined, 'freeroam');
  sim.addPlayer('a', 'Aadi'); sim.addPlayer('b', 'Noor'); return sim;
}
function ready(mode: Mode = 'private') { const sim = free(mode); completeCity(sim, 'a'); walkAt(sim, 'a', 'civic'); walkAt(sim, 'b', 'civic'); return sim; }
const ballot = (route: string) => command('city_choice', 'city-mandate', route);

describe('authoritative city reform and capture', () => {
  it('rounds disclosed capture rewards down, keeps reputation and never changes authored rewards', () => {
    const base = Object.freeze({ credits: 170, reputation: 3, project: 1 });
    expect(getEffectiveJobReward(base, 'capture')).toEqual({ credits: 212, reputation: 3, project: 0 });
    expect(getEffectiveJobReward(base, 'reform')).toEqual({ credits: 170, reputation: 3, project: 2 });
    expect(getEffectiveJobReward({ ...base, project: 0 }, 'reform').project).toBe(0);
    expect(getEffectiveJobReward(base, null)).toEqual(base); expect(base.project).toBe(1);
  });

  it('keeps the original repeatables, gates sectors behind the expose and awards each once', () => {
    const sim = free();
    expect(CONTRACTS.filter(job => !job.once)).toHaveLength(5);
    expect(sim.command('a', command('job_start', 'sector-energy')).code).toBe('JOB_PREREQUISITE');
    const finish = completeJob(sim, 'a', 'media-correction');
    const before = sim.snapshot();
    expect(sim.city.completedJobs).toEqual(['media-correction']);
    expect(sim.command('a', finish).code).toBe('JOB_COMPLETE');
    expect(sim.snapshot()).toEqual(before);
    expect(sim.command('b', command('job_start', 'media-correction')).code).toBe('JOB_ALREADY_COMPLETED');
    completeJob(sim, 'a', 'sector-energy');
    expect(sim.city.sectors).toEqual({ energy: 1, welfare: 0, resources: 0, procurement: 0 });
    expect(sim.command('b', command('job_start', 'sector-energy')).code).toBe('JOB_ALREADY_COMPLETED');
  });

  it('does not grant city progress for remote actions or cancelled work', () => {
    const sim = free(); sim.command('a', command('job_start', 'media-correction'));
    walkAt(sim, 'a', 'river');
    const active = sim.contracts.active!;
    expect(sim.command('a', command('job_interact', active.instanceId, active.stageId)).code).toBe('TOO_FAR');
    expect(sim.command('a', command('job_cancel', active.instanceId)).code).toBe('JOB_CANCELLED');
    expect(sim.city.completedJobs).toEqual([]); expect(sim.contracts.progression.completed).toBe(0);
  });

  it('keeps one-shot completion durable after the recent outcome window rolls over', () => {
    const sim = free(); completeJob(sim, 'a', 'media-correction');
    for (let i = 0; i < 21; i++) {
      expect(sim.command('a', command('job_start', 'clinic-restock')).ok).toBe(true);
      expect(sim.command('a', command('job_cancel', sim.contracts.active!.instanceId)).ok).toBe(true);
      for (let tick = 0; tick < 101; tick++) sim.step();
    }
    expect(sim.contracts.recent).toHaveLength(20);
    expect(sim.contracts.recent.some(outcome => outcome.jobId === 'media-correction')).toBe(false);
    const restored = new Simulation('CITY-TEST', 'private', sim.serialize()); restored.connectPlayer('a');
    expect(restored.city.completedJobs).toEqual(['media-correction']);
    expect(restored.command('a', command('job_start', 'media-correction')).code).toBe('JOB_ALREADY_COMPLETED');
    expect(restored.contracts.progression.completed).toBe(1);
  });

  it('requires unlocked, in-person on-foot explicit choices and rejects forged authority fields', () => {
    const locked = free(); expect(locked.command('a', ballot('reform')).code).toBe('CITY_LOCKED');
    const story = new Simulation('STORY'); story.addPlayer('a', 'Aadi');
    expect(story.command('a', ballot('reform')).code).toBe('FREEROAM_REQUIRED');
    const sim = ready(); walkAt(sim, 'a', 'garage');
    expect(sim.command('a', ballot('reform')).code).toBe('TOO_FAR');
    walkAt(sim, 'a', 'civic');
    const car = sim.vehicles.get('compact-01')!, player = sim.players.get('a')!;
    car.x = player.x; car.z = player.z; car.speed = 0;
    expect(sim.command('a', command('enter', car.id)).ok).toBe(true);
    expect(sim.command('a', ballot('reform')).code).toBe('EXIT_VEHICLE_FIRST');
    walkAt(sim, 'a', 'civic');
    expect(sim.command('a', ballot('invented')).code).toBe('CITY_INVALID_CHOICE');
    expect(sim.command('a', command('city_choice', 'wrong', 'reform')).code).toBe('WRONG_TARGET');
    expect(parseClientMessage({ ...ballot('capture'), sectors: { energy: 99 } })).toBeNull();
    expect(sim.city.decision).toBeNull();
  });

  it.each(['private', 'public'] as const)('requires a connected crew majority in %s rooms and consumes the decision once', mode => {
    const sim = ready(mode);
    expect(sim.command('a', ballot('capture')).code).toBe('CITY_VOTE_RECORDED');
    expect(sim.city.decision).toBeNull();
    expect(sim.command('b', ballot('reform')).code).toBe('CITY_VOTE_RECORDED');
    expect(sim.city.decision).toBeNull();
    const decisive = ballot('capture'); const result = sim.command('b', decisive);
    expect(result.code).toBe('CITY_DECIDED'); expect(sim.city.decision?.route).toBe('capture');
    expect(sim.city.outcome).toEqual(CITY_OUTCOMES.capture); expect(sim.city.votes).toEqual({});
    const before = sim.snapshot(); expect(sim.command('b', decisive)).toEqual(result);
    expect(sim.snapshot()).toEqual(before);
    expect(sim.command('a', ballot('reform')).code).toBe('CITY_ALREADY_DECIDED');
  });

  it('prunes disconnected ballots without silently deciding and requires an explicit fresh vote', () => {
    const sim = ready(); sim.command('a', ballot('reform')); sim.command('b', ballot('capture'));
    sim.disconnectPlayer('b');
    expect(sim.city.votes).toEqual({ a: 'reform' }); expect(sim.city.decision).toBeNull();
    sim.step(); expect(sim.city.decision).toBeNull();
    const restored = new Simulation('CITY-TEST', 'private', sim.serialize());
    expect(restored.city.votes).toEqual({}); expect(restored.city.decision).toBeNull();
    restored.connectPlayer('a'); walkAt(restored, 'a', 'civic');
    expect(restored.command('a', ballot('reform')).code).toBe('CITY_DECIDED');
  });

  it('clears pending ballots when new work interrupts the hearing and blocks votes during work', () => {
    const sim = ready(); sim.command('a', ballot('reform'));
    expect(sim.command('b', command('job_start', 'clinic-restock')).code).toBe('JOB_STARTED');
    expect(sim.city.votes).toEqual({});
    expect(sim.command('a', ballot('capture')).code).toBe('CITY_JOB_ACTIVE');
  });

  it.each(['reform', 'capture'] as const)('persists the %s route and applies its disclosed future payout', route => {
    const sim = ready(); sim.command('a', ballot(route)); sim.command('b', ballot(route));
    const restored = new Simulation('CITY-TEST', 'private', sim.serialize()); restored.connectPlayer('a');
    expect(restored.city.decision?.route).toBe(route); expect(restored.city.outcome).toEqual(CITY_OUTCOMES[route]);
    const before = { ...restored.contracts.progression };
    completeJob(restored, 'a', 'clinic-restock');
    expect(restored.contracts.progression.credits - before.credits).toBe(route === 'capture' ? 125 : 100);
    expect(restored.contracts.progression.project - before.project).toBe(route === 'capture' ? 0 : 2);
    expect(restored.contracts.recent[0]).toMatchObject({ credits: route === 'capture' ? 125 : 100, project: route === 'capture' ? 0 : 2 });
    expect(restored.city.completedJobs).toHaveLength(5);
  });

  it('migrates a schema-two current job and reward history without inventing sector progress', () => {
    const sim = free(); completeJob(sim, 'a', 'clinic-restock');
    sim.command('a', command('job_start', 'pool-car-recall'));
    const old = sim.serialize(); old.schema = 2; delete old.city; Object.assign(old, { protocol: 1 });
    const before = JSON.stringify(old);
    const restored = new Simulation('CITY-TEST', 'private', old);
    expect(restored.contracts).toEqual(old.contracts); expect(restored.city.completedJobs).toEqual([]);
    expect(Object.values(restored.city.sectors)).toEqual([0, 0, 0, 0]);
    expect(restored.serialize().schema).toBe(3); expect(JSON.stringify(old)).toBe(before);
    expect(restored.snapshot().protocol).toBe(PROTOCOL_VERSION); expect(PROTOCOL_VERSION).toBe(2);
  });

  it('rejects inconsistent city ledgers, prerequisites, decisions and schema downgrades', () => {
    const sim = ready(), valid = sim.serialize();
    const corruptions = [
      (save: typeof valid) => { delete save.city; },
      (save: typeof valid) => { save.city!.sectors.energy = 99; },
      (save: typeof valid) => { save.city!.completedJobs.push('media-correction'); },
      (save: typeof valid) => { save.city!.completedJobs.shift(); },
      (save: typeof valid) => { save.city!.completedJobs[0] = 'unknown-job'; },
      (save: typeof valid) => { save.city!.votes = { stranger: 'capture' }; },
      (save: typeof valid) => { save.city!.decision = { route: 'capture', decidedAt: save.time + 1 }; save.city!.outcome = CITY_OUTCOMES.capture; },
      (save: typeof valid) => { save.schema = 2; },
    ];
    for (const corrupt of corruptions) {
      const save = structuredClone(valid); corrupt(save);
      expect(() => new Simulation('CITY-TEST', 'private', save)).toThrow('INVALID_CHECKPOINT');
    }
    const story = structuredClone(valid); story.gameplay = 'story';
    expect(() => new Simulation('CITY-TEST', 'private', story)).toThrow('INVALID_CHECKPOINT');
  });
});
