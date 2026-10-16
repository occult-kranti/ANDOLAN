import { describe, expect, it } from 'vitest';
import { ReferenceLab } from '../reference/controller.js';
import type { ReferenceSnapshot } from '../reference/types.js';
import type { ArenaInput } from '../shared/types.js';

const input = (seq: number, fields: Partial<ArenaInput> = {}): ArenaInput => ({ type: 'input', seq, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire: false, jump: false, ...fields });
const local = (state: ReferenceSnapshot) => state.arena.actors.find(actor => actor.id === state.localId)!;
function advance(lab: ReferenceLab, seconds: number) {
  for (let step = 0; step < Math.round(seconds / .05); step++) lab.step(.05);
}

describe('original reference controller through its public API', () => {
  it('uses genuine arena participants, rejects invalid input/epochs and isolates returned state', () => {
    const lab = new ReferenceLab({ experiment: 'control-point', heroId: 'rama', seed: 7301 });
    const state = lab.snapshot();
    expect(state.botIds).toHaveLength(5);
    expect(state.arena.actors.filter(actor => actor.kind === 'hero')).toHaveLength(6);
    expect(state.botIds.every(id => state.arena.actors.some(actor => actor.id === id && actor.connected && actor.health > 0))).toBe(true);
    expect(lab.input(input(1, { moveX: NaN }), lab.epoch)).toBe(false);
    expect(lab.input(input(1, { moveZ: 1 }), lab.epoch - 1)).toBe(false);
    expect(lab.input(input(1, { moveX: 1 }), lab.epoch)).toBe(true);
    expect(lab.input(input(1, { moveX: -1 }), lab.epoch)).toBe(false);
    lab.step(.05);
    expect(local(lab.snapshot()).x).toBeGreaterThan(local(state).x);
    state.weapons[state.localId]!.ammo = 900;
    state.economy.wallets[state.localId]!.balance = 900;
    state.arena.actors[0]!.health = 0;
    state.objective!.scores.sun = 60;
    expect(lab.snapshot().weapons[state.localId]!.ammo).toBe(12);
    expect(lab.snapshot().economy.wallets[state.localId]!.balance).toBe(180);
    expect(local(lab.snapshot()).health).toBeGreaterThan(0);
    expect(lab.snapshot().objective!.scores.sun).toBe(0);
    lab.dispose();
  });

  it('caps elapsed work, pauses without hidden accrual and clears held input on resume', () => {
    const lab = new ReferenceLab({ experiment: 'lane-economy', heroId: 'rama' });
    lab.step(.04);
    expect(lab.snapshot().arena.time).toBe(0);
    lab.input(input(1, { moveX: 1, fire: true }), lab.epoch);
    lab.pause(true);
    const paused = lab.snapshot();
    lab.step(100);
    expect(lab.snapshot()).toEqual(paused);
    expect(lab.input(input(2, { moveX: 1 }), lab.epoch)).toBe(false);
    expect(lab.command({ type: 'command', id: 'paused-q', action: 'ability', slot: 0 }, lab.epoch).code).toBe('PAUSED');
    lab.pause(false); lab.step(.01);
    expect(lab.snapshot().arena.time).toBe(0);
    lab.step(100);
    const resumed = lab.snapshot();
    expect(resumed.arena.time).toBeCloseTo(.25, 10);
    expect(local(resumed).x).toBe(local(paused).x);
    expect(resumed.weapons[resumed.localId]!.ammo).toBe(12);
    for (const elapsed of [NaN, Infinity, 0, -1]) lab.step(elapsed);
    expect(lab.snapshot()).toEqual(resumed);
    lab.dispose();
  });

  it('permits one real base purchase while paused without advancing reload, objective or combat', () => {
    const lab = new ReferenceLab({ experiment: 'control-point', heroId: 'rama', seed: 91 });
    lab.input(input(1, { fire: true, pitch: .7 }), lab.epoch); lab.step(.05);
    expect(lab.command({ type: 'command', id: 'start-reload', action: 'reload' }, lab.epoch).ok).toBe(true);
    lab.pause(true);
    const before = lab.snapshot();
    const purchase = { type: 'command', id: 'paused-purchase', action: 'upgrade', upgrade: 'power' } as const;
    expect(lab.command(purchase, lab.epoch).code).toBe('UPGRADED');
    const after = lab.snapshot();
    expect(local(after).upgrades.power).toBe(1);
    expect(local(before).credits - local(after).credits).toBe(120);
    expect(after.arena.time).toBe(before.arena.time);
    expect(after.weapons).toEqual(before.weapons);
    expect(after.objective).toEqual(before.objective);
    expect(lab.command(purchase, lab.epoch).code).toBe('UPGRADED');
    expect(lab.command({ type: 'command', id: 'paused-cast', action: 'ability', slot: 0 }, lab.epoch).code).toBe('PAUSED');
    expect(lab.command({ type: 'command', id: 'paused-reload', action: 'reload' }, lab.epoch).code).toBe('PAUSED');
    lab.step(10);
    expect(lab.snapshot()).toEqual(after);
    expect(after.economy.receipts.filter(receipt => receipt.actorId === lab.localId)).toHaveLength(1);
    lab.dispose();
  });

  it('spends one round per actual primary shot, blocks an empty magazine and reloads only once', () => {
    const lab = new ReferenceLab({ experiment: 'lane-economy', heroId: 'rama', seed: 21 });
    const shots = new Set<number>(); let sequence = 0;
    for (let step = 0; step < 240 && lab.snapshot().weapons[lab.localId]!.ammo > 0; step++) {
      lab.input(input(++sequence, { fire: true, pitch: .7 }), lab.epoch); lab.step(.05);
      for (const event of lab.snapshot().arena.events) if (event.actorId === lab.localId && event.type === 'shot') shots.add(event.id);
    }
    expect(lab.snapshot().weapons[lab.localId]!.ammo).toBe(0);
    expect(shots.size).toBe(12);
    const watermark = lab.snapshot().arena.events.at(-1)?.id ?? 0;
    for (let step = 0; step < 40; step++) { lab.input(input(++sequence, { fire: true }), lab.epoch); lab.step(.05); }
    expect(lab.snapshot().arena.events.some(event => event.id > watermark && event.actorId === lab.localId && event.type === 'shot')).toBe(false);
    lab.input(input(++sequence), lab.epoch);
    const reload = { type: 'command', id: 'reload-once', action: 'reload' } as const;
    expect(lab.command(reload, lab.epoch).code).toBe('RELOAD_STARTED');
    advance(lab, .8);
    const halfway = lab.snapshot().weapons[lab.localId]!.reloadRemaining;
    expect(halfway).toBeCloseTo(.8, 10);
    expect(lab.command(reload, lab.epoch).code).toBe('RELOAD_STARTED');
    expect(lab.snapshot().weapons[lab.localId]!.reloadRemaining).toBe(halfway);
    lab.pause(true); lab.step(10);
    expect(lab.snapshot().weapons[lab.localId]!.reloadRemaining).toBe(halfway);
    lab.pause(false); advance(lab, .75);
    expect(lab.snapshot().weapons[lab.localId]!.ammo).toBe(0);
    lab.step(.05);
    expect(lab.snapshot().weapons[lab.localId]!).toMatchObject({ ammo: 12, reloadRemaining: 0 });
    expect(lab.command({ ...reload, id: 'already-full' }, lab.epoch).code).toBe('MAGAZINE_FULL');
    lab.dispose();
  });

  it('does not charge primary ammunition for immediate or delayed ability projectiles', () => {
    const lab = new ReferenceLab({ experiment: 'lane-economy', heroId: 'rama', seed: 32 });
    lab.input(input(1, { pitch: .6 }), lab.epoch);
    expect(lab.command({ type: 'command', id: 'q', action: 'ability', slot: 0 }, lab.epoch).ok).toBe(true);
    expect(lab.command({ type: 'command', id: 'r', action: 'ability', slot: 2 }, lab.epoch).ok).toBe(true);
    const localShots = new Set<number>();
    for (let step = 0; step < 50; step++) {
      lab.step(.05);
      const state = lab.snapshot();
      for (const event of state.arena.events) if (event.actorId === lab.localId && event.type === 'shot') localShots.add(event.id);
      expect(state.weapons[lab.localId]!.ammo).toBe(12);
    }
    expect(localShots.size).toBeGreaterThan(1);
    expect(local(lab.snapshot()).cast).toBeUndefined();
    lab.dispose();
  });

  it('deduplicates actual purchases and resets mode, wallet, reload, input and command identity into a fresh epoch', () => {
    const lab = new ReferenceLab({ experiment: 'lane-economy', heroId: 'rama', seed: 77 });
    const purchase = { type: 'command', id: 'reusable-after-reset', action: 'upgrade', upgrade: 'power' } as const;
    expect(lab.command(purchase, lab.epoch).code).toBe('UPGRADED');
    const purchased = lab.snapshot();
    expect(local(purchased).upgrades.power).toBe(1);
    expect(purchased.economy.receipts.filter(receipt => receipt.actorId === lab.localId)).toMatchObject([{ amount: 120, kind: 'spend', balance: 60 }]);
    expect(lab.command(purchase, lab.epoch).code).toBe('UPGRADED');
    expect(lab.snapshot()).toEqual(purchased);
    lab.input(input(1, { fire: true, moveX: 1 }), lab.epoch); lab.step(.05);
    expect(lab.command({ type: 'command', id: 'reload', action: 'reload' }, lab.epoch).ok).toBe(true);
    lab.pause(true);
    const oldEpoch = lab.epoch;
    const reset = lab.reset({ experiment: 'control-point', heroId: 'sita', seed: 31 });
    expect(reset).toMatchObject({ epoch: oldEpoch + 1, experiment: 'control-point', paused: false, phase: 'playing', winner: null, reason: '', timeLeft: 240 });
    expect(reset.arena.time).toBe(0); expect(local(reset).heroId).toBe('sita');
    expect(reset.economy.receipts).toEqual([]);
    expect(reset.economy.wallets[lab.localId]).toEqual({ balance: 180, earned: 0, spent: 0 });
    expect(reset.weapons[lab.localId]).toMatchObject({ ammo: 12, reloadRemaining: 0 });
    expect(reset.objective).toMatchObject({ owner: null, progress: 0, scores: { sun: 0, moon: 0 } });
    expect(lab.input(input(999, { fire: true }), oldEpoch)).toBe(false);
    expect(lab.command(purchase, oldEpoch).code).toBe('STALE_EPOCH');
    expect(lab.command(purchase, lab.epoch).code).toBe('UPGRADED');
    expect(local(lab.snapshot()).upgrades.power).toBe(1);
    expect(lab.snapshot().economy.receipts).toHaveLength(1);
    lab.step(.05);
    expect(lab.snapshot().weapons[lab.localId]!.ammo).toBe(12);
    expect(lab.reset({ experiment: 'lane-economy' }).objective).toBeNull();
    lab.dispose();
  });

  it('reconciles every observed wallet delta through a normal bot match and freezes its real result', () => {
    const lab = new ReferenceLab({ experiment: 'control-point', heroId: 'rama', seed: 7301 });
    const balances = Object.fromEntries(Object.entries(lab.snapshot().economy.wallets).map(([id, wallet]) => [id, wallet.balance]));
    let receiptId = 0, lastReceiptTime = 0, income = 0, contested = false, occupied = false;
    const seen = new Set<number>();
    for (let step = 0; step < 961 && lab.snapshot().phase === 'playing'; step++) {
      lab.step(.25);
      const state = lab.snapshot();
      contested ||= !!state.objective?.contested;
      occupied ||= !!state.objective && state.objective.occupants.sun + state.objective.occupants.moon > 0;
      for (const receipt of state.economy.receipts.filter(value => value.id > receiptId)) {
        expect(seen.has(receipt.id)).toBe(false); seen.add(receipt.id);
        expect(receipt.epoch).toBe(lab.epoch);
        expect(receipt.time).toBeGreaterThanOrEqual(lastReceiptTime);
        expect(receipt.amount).toBeGreaterThan(0);
        balances[receipt.actorId]! += receipt.kind === 'income' ? receipt.amount : -receipt.amount;
        expect(receipt.balance).toBe(balances[receipt.actorId]);
        if (receipt.kind === 'income') income += receipt.amount;
        receiptId = receipt.id; lastReceiptTime = receipt.time;
      }
      for (const [id, wallet] of Object.entries(state.economy.wallets)) {
        expect(wallet.balance).toBe(balances[id]);
        expect(wallet.balance).toBe(180 + wallet.earned - wallet.spent);
        expect(state.arena.actors.find(actor => actor.id === id)!.credits).toBe(wallet.balance);
      }
      expect(state.economy.receipts.length).toBeLessThanOrEqual(128);
    }
    const finished = lab.snapshot();
    expect(occupied).toBe(true); expect(contested).toBe(true); expect(income).toBeGreaterThan(0);
    expect(finished.phase).toBe('finished'); expect(finished.winner).not.toBeNull(); expect(finished.reason).not.toBe('');
    expect(finished.arena.time).toBeLessThanOrEqual(240.000001);
    lab.step(10);
    expect(lab.input(input(10000, { fire: true }), lab.epoch)).toBe(false);
    expect(lab.command({ type: 'command', id: 'finished-q', action: 'ability', slot: 0 }, lab.epoch).code).toBe('MATCH_FINISHED');
    expect(lab.snapshot()).toEqual(finished);
    lab.dispose();
  });

  it('retains the lane arena result and has no hidden control objective or scoring', () => {
    const lab = new ReferenceLab({ experiment: 'lane-economy', heroId: 'rama', seed: 7301 });
    for (let step = 0; step < 1921 && lab.snapshot().phase === 'playing'; step++) lab.step(.25);
    const finished = lab.snapshot();
    expect(finished.objective).toBeNull();
    expect(finished.phase).toBe('finished');
    expect(finished.arena.phase).toBe('finished');
    expect(finished.winner).toBe(finished.arena.winner);
    expect(finished.reason).toBe(`Arena result: ${finished.arena.reason}`);
    expect(finished.arena.time).toBeLessThanOrEqual(480.000001);
    lab.step(.25);
    expect(lab.snapshot()).toEqual(finished);
    lab.dispose();
  });
});
