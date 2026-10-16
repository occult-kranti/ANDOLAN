import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ArenaAudio } from '../client/audio';
import { HEROES } from '../shared/heroes';
import type { Actor, ArenaSnapshot, GameEvent } from '../shared/types';

// Resource/lifecycle model only. Native synthesis and perceived balance need browser/hardware checks.
class Param {
  value = 0;
  setTargetAtTime(value: number) { this.value = value; }
  setValueAtTime(value: number) { this.value = value; }
  linearRampToValueAtTime(value: number) { this.value = value; }
  exponentialRampToValueAtTime(value: number) { this.value = value; }
  cancelScheduledValues() {}
}
class Node {
  gain = new Param(); frequency = new Param(); pan = new Param(); Q = new Param();
  threshold = new Param(); knee = new Param(); ratio = new Param(); attack = new Param(); release = new Param();
  onended: (() => void) | null = null;
  disconnected = false;
  waveformSample = 0;
  stops: (number | undefined)[] = [];
  connections: Node[] = [];
  constructor(readonly kind = 'node') {}
  getFloatTimeDomainData(data: Float32Array) { data.fill(this.waveformSample); }
  connect(node: Node) { this.connections.push(node); }
  disconnect() { this.disconnected = true; }
  start() {}
  stop(time?: number) { this.stops.push(time); }
}
class Context {
  static all: Context[] = [];
  currentTime = 0;
  sampleRate = 8000;
  state = 'suspended';
  destination = new Node();
  nodes: Node[] = [];
  resume = vi.fn(async () => { this.state = 'running'; });
  suspend = vi.fn(async () => { this.state = 'suspended'; });
  close = vi.fn(async () => { this.state = 'closed'; });
  constructor() { Context.all.push(this); }
  createGain = () => this.node('gain');
  createAnalyser = () => this.node('analyser');
  createDynamicsCompressor = () => this.node('compressor');
  createBiquadFilter = () => this.node('filter');
  createOscillator = () => this.node('oscillator');
  createStereoPanner = () => this.node('pan');
  createBufferSource = () => this.node('noise');
  createBuffer(_channels: number, length: number) { return { getChannelData: () => new Float32Array(length) }; }
  private node(kind: string) { const node = new Node(kind); this.nodes.push(node); return node; }
}
class Document extends EventTarget { hidden = false; }
const actor = (id: string, extra: Partial<Actor> = {}): Actor => ({
  id, kind: 'hero', team: id === 'me' ? 'sun' : 'moon', heroId: HEROES.find(hero => hero.weapon === 'bow')!.id,
  name: id, bot: false, connected: true, lane: 1, x: 0, z: 0, y: 0, yaw: 0, health: 100,
  maxHealth: 100, shield: 0, respawn: 0, cooldowns: [0, 0, 0], fireCooldown: 0, credits: 0,
  level: 1, kills: 0, deaths: 0, assists: 0, damageDealt: 0, upgrades: { power: 0, vitality: 0, tempo: 0 },
  effects: { haste: 0, slow: 0, ward: 0 }, lastInputSeq: -1, ...extra,
});
const event = (id: number, extra: Partial<GameEvent> = {}): GameEvent => ({ id, type: 'shot', team: 'sun', actorId: 'me', label: '', color: '#fff', time: 1, x: 0, z: 0, ...extra });
const snapshot = (events: GameEvent[] = [], extra: Partial<ArenaSnapshot> = {}): ArenaSnapshot => ({
  protocol: 1, room: 'ARENA', tick: 20, time: 1, duration: 480, phase: 'playing', winner: null, reason: '',
  actors: [actor('me'), actor('other', { x: 10 })], structures: [], projectiles: [], zones: [], pickups: [],
  events, scores: { sun: 0, moon: 0 }, seed: 5, ...extra,
});
let document: Document;
let audio: ArenaAudio;
const settle = async () => { await vi.advanceTimersByTimeAsync(100); };
async function start() { audio.setMuted(false); audio.setActive(true); await audio.unlock(); audio.update(snapshot(), 'me'); }

beforeEach(() => {
  vi.useFakeTimers(); Context.all = []; document = new Document();
  vi.stubGlobal('document', document); vi.stubGlobal('AudioContext', Context); audio = new ArenaAudio();
});
afterEach(async () => { audio.destroy(); await Promise.resolve(); vi.unstubAllGlobals(); vi.useRealTimers(); });

describe('ArenaAudio authoritative cues and lifecycle', () => {
  it('does not create audio from preferences or snapshots and keeps explicit mute through unlock', async () => {
    audio.setVolume(.4); audio.setRhythm(true); audio.setActive(true); audio.update(snapshot([event(1)]), 'me');
    expect(Context.all).toHaveLength(0);
    const unlocking = audio.unlock(); await settle(); await unlocking;
    expect(audio.diagnostics).toMatchObject({ unlocked: true, muted: true, contextState: 'suspended', volume: .4, rhythm: true });
    audio.setVolume(Number.NaN); expect(audio.diagnostics.volume).toBe(.4);
    audio.setVolume(2); expect(audio.diagnostics.volume).toBe(1);
    audio.setVolume(-2); expect(audio.diagnostics.volume).toBe(0);
  });

  it('plays each authoritative event once, with no join, menu or stale-event backlog', async () => {
    audio.setMuted(false); audio.setActive(true); await audio.unlock();
    audio.update(snapshot([event(1)]), 'me'); expect(audio.diagnostics.activeVoices).toBe(0);
    audio.update(snapshot([event(1), event(2)]), 'me'); expect(audio.diagnostics.activeVoices).toBe(2);
    audio.update(snapshot([event(1), event(2)]), 'me'); expect(audio.diagnostics.activeVoices).toBe(2);
    audio.setActive(false); await settle(); expect(audio.diagnostics.activeVoices).toBe(0);
    audio.update(snapshot([event(3)]), 'me'); audio.setActive(true); await settle();
    audio.update(snapshot([event(4)]), 'me'); expect(audio.diagnostics.activeVoices).toBe(0);
    Context.all[0].currentTime = 2;
    audio.update(snapshot([event(5, { time: 0 })]), 'me'); expect(audio.diagnostics.activeVoices).toBe(0);
    audio.update(snapshot([event(6)]), 'me'); expect(audio.diagnostics.activeVoices).toBe(2);
  });

  it('uses directional pan and range attenuation for nearby heroes, while suppressing minion shot noise', async () => {
    await start(); const context = Context.all[0];
    audio.update(snapshot([event(1, { actorId: 'other', team: 'moon', x: 10 })]), 'me');
    expect(context.nodes.filter(node => node.kind === 'pan').every(node => node.pan.value > 0)).toBe(true);
    expect(audio.diagnostics.activeVoices).toBe(2);
    context.currentTime = 1;
    audio.update(snapshot([event(2, { actorId: 'other', x: 100 })], { actors: [actor('me'), actor('other', { x: 100 })] }), 'me');
    expect(audio.diagnostics.activeVoices).toBe(2);
    audio.update(snapshot([event(3, { actorId: 'minion' })], { actors: [actor('me'), actor('minion', { kind: 'minion' })] }), 'me');
    expect(audio.diagnostics.activeVoices).toBe(2);
  });

  it('does not claim damage or casts from cooldown/UI changes, and reserves kill cues for hero defeats', async () => {
    await start();
    audio.update(snapshot([], { actors: [actor('me', { fireCooldown: 1, cooldowns: [8, 0, 0] })] }), 'me');
    expect(audio.diagnostics.activeVoices).toBe(0);
    audio.update(snapshot([event(1, { type: 'ability' })]), 'me'); expect(audio.diagnostics.activeVoices).toBe(2);
    audio.update(snapshot([event(2, { type: 'defeat', targetId: 'minion' })], { actors: [actor('me'), actor('minion', { kind: 'minion' })] }), 'me');
    expect(audio.diagnostics.activeVoices).toBe(2);
    audio.update(snapshot([event(3, { type: 'defeat', targetId: 'other' })]), 'me'); expect(audio.diagnostics.activeVoices).toBe(4);
  });

  it('caps sources at20 and prioritizes a match outcome over old low-priority combat', async () => {
    await start(); const context = Context.all[0];
    for (let id = 1; id <= 50; id++) { context.currentTime = id; audio.update(snapshot([event(id)]), 'me'); }
    expect(audio.diagnostics.activeVoices).toBe(20);
    const removedBefore = context.nodes.filter(node => node.disconnected).length;
    audio.update(snapshot([event(51, { type: 'victory' })], { phase: 'finished', winner: 'sun' }), 'me');
    expect(audio.diagnostics.activeVoices).toBe(20);
    expect(context.nodes.filter(node => node.disconnected).length).toBeGreaterThan(removedBefore);
    audio.setActive(false); await settle(); expect(audio.diagnostics.activeVoices).toBe(0);
    expect(context.nodes.filter(node => ['oscillator', 'noise', 'pan'].includes(node.kind)).every(node => node.disconnected)).toBe(true);
  });

  it('throttles structure-under-attack alerts and does not warn on initial snapshot damage', async () => {
    await start();
    const structure = { id: 'sun-core', kind: 'core' as const, team: 'sun' as const, lane: 1 as const, x: 0, z: -69, health: 500, maxHealth: 1000, shielded: false };
    audio.update(snapshot([], { structures: [structure] }), 'me'); expect(audio.diagnostics.activeVoices).toBe(0);
    audio.update(snapshot([], { structures: [{ ...structure, health: 490 }] }), 'me'); expect(audio.diagnostics.activeVoices).toBe(2);
    Context.all[0].currentTime += 1;
    audio.update(snapshot([], { structures: [{ ...structure, health: 480 }] }), 'me'); expect(audio.diagnostics.activeVoices).toBe(2);
  });

  it('auditions while muted and paused without changing preferences, then restores silence', async () => {
    audio.setVolume(.3); audio.setRhythm(true);
    const preview = audio.preview(); await settle();
    expect(audio.diagnostics).toMatchObject({ muted: true, active: false, previewing: true, contextState: 'running', activeVoices: 3, volume: .3 });
    await vi.advanceTimersByTimeAsync(750); await preview;
    expect(audio.diagnostics).toMatchObject({ muted: true, active: false, previewing: false, contextState: 'suspended', activeVoices: 0, volume: .3 });
    expect(vi.getTimerCount()).toBe(0);
  });

  it('keeps volume-zero previews silent and cancels overlapping auditions on visibility loss', async () => {
    audio.setVolume(0); const first = audio.preview(); await settle(); expect(audio.diagnostics.activeVoices).toBe(0);
    audio.setVolume(.4); const second = audio.preview(); await settle(); await first;
    expect(audio.diagnostics.activeVoices).toBe(2);
    document.hidden = true; document.dispatchEvent(new Event('visibilitychange')); await settle(); await second;
    expect(audio.diagnostics).toMatchObject({ previewing: false, contextState: 'suspended', activeVoices: 0, muted: true });
    await vi.advanceTimersByTimeAsync(3000); expect(vi.getTimerCount()).toBe(0);
  });

  it('cancels stale mute fades and repairs a suspend that finishes after a newer unmute', async () => {
    await start(); const context = Context.all[0];
    audio.setMuted(true); await vi.advanceTimersByTimeAsync(25); audio.setMuted(false); await settle();
    expect(context.state).toBe('running'); expect(context.suspend).not.toHaveBeenCalled();
    let finish: (() => void) | undefined;
    context.suspend.mockImplementationOnce(() => new Promise<void>(resolve => { finish = () => { context.state = 'suspended'; resolve(); }; }));
    audio.setMuted(true); await settle(); audio.setMuted(false); finish!(); await settle();
    expect(audio.diagnostics).toMatchObject({ muted: false, contextState: 'running' });
  });

  it('does not let an older unlock completion cancel a newer settings preview', async () => {
    await start(); const context = Context.all[0];
    let finish: (() => void) | undefined;
    context.resume.mockImplementationOnce(() => new Promise<void>(resolve => { finish = resolve; }));
    const unlocking = audio.unlock(); const preview = audio.preview(); await settle();
    expect(audio.diagnostics.previewing).toBe(true);
    finish!(); await unlocking;
    expect(audio.diagnostics.previewing).toBe(true);
    await vi.advanceTimersByTimeAsync(750); await preview;
    expect(audio.diagnostics).toMatchObject({ previewing: false, contextState: 'running', muted: false });
  });

  it('samples native diagnostics without fabricating silence from mute labels', async () => {
    const preview = audio.preview(); await settle();
    const analyser = Context.all[0].nodes.find(node => node.kind === 'analyser')!;
    analyser.waveformSample = .2;
    expect(audio.diagnostics.outputRms).toBeCloseTo(.2);
    expect(audio.diagnostics.muted).toBe(true);
    analyser.waveformSample = Number.NaN; expect(audio.diagnostics.outputPeak).toBe(0);
    audio.destroy(); await preview; expect(audio.diagnostics.outputRms).toBe(0);
  });

  it('never creates rhythmic voices until the optional texture is selected', async () => {
    await start(); audio.update(snapshot(), 'me'); expect(audio.diagnostics.activeVoices).toBe(0);
    audio.setRhythm(true); audio.update(snapshot(), 'me'); expect(audio.diagnostics.activeVoices).toBe(1);
    audio.update(snapshot(), 'me'); expect(audio.diagnostics.activeVoices).toBe(1);
    audio.setRhythm(false); Context.all[0].currentTime += 10; audio.update(snapshot(), 'me');
    expect(audio.diagnostics.activeVoices).toBe(1);
  });

  it('stops every source/timer/listener on destruction and cannot restart', async () => {
    const preview = audio.preview(); await settle(); const context = Context.all[0];
    audio.destroy(); audio.destroy(); await preview; await settle();
    expect(context.close).toHaveBeenCalledTimes(1); expect(context.nodes.every(node => node.disconnected)).toBe(true);
    const resumes = context.resume.mock.calls.length;
    document.dispatchEvent(new Event('visibilitychange')); await audio.unlock(); await audio.preview();
    expect(context.resume).toHaveBeenCalledTimes(resumes); expect(vi.getTimerCount()).toBe(0);
  });
});
