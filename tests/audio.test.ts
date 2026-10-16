import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { GameAudio } from '../apps/client/src/audio';

// This models lifecycle/resource ownership, not loudness or subjective mix quality.
class Param {
  value = 0;
  setTargetAtTime(value: number) { this.value = value; }
  setValueAtTime(value: number) { this.value = value; }
  linearRampToValueAtTime(value: number) { this.value = value; }
  exponentialRampToValueAtTime(value: number) { this.value = value; }
  cancelScheduledValues() {}
}
class Node {
  gain = new Param(); frequency = new Param(); detune = new Param(); Q = new Param();
  threshold = new Param(); knee = new Param(); ratio = new Param(); attack = new Param(); release = new Param();
  onended: (() => void) | null = null;
  disconnected = false;
  stops: (number | undefined)[] = [];
  loop = false;
  oscillator = false;
  waveformSample = 0;
  getFloatTimeDomainData(data: Float32Array) { data.fill(this.waveformSample); }
  connect() {}
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
  createGain = () => this.makeNode();
  createAnalyser = () => this.makeNode();
  createDynamicsCompressor = () => this.makeNode();
  createBiquadFilter = () => this.makeNode();
  createOscillator = () => { const node = this.makeNode(); node.oscillator = true; return node; };
  createBufferSource = () => this.makeNode();
  createBuffer(_channels: number, length: number) { return { getChannelData: () => new Float32Array(length) }; }
  private makeNode() { const node = new Node(); this.nodes.push(node); return node; }
}
class Document extends EventTarget { hidden = false; }
let document: Document;
let audio: GameAudio;
const settle = async () => { await vi.advanceTimersByTimeAsync(100); };
const toggleAudio = async () => { const changed = audio.toggle(); await settle(); return changed; };

beforeEach(() => {
  vi.useFakeTimers();
  Context.all = [];
  document = new Document();
  vi.stubGlobal('document', document); vi.stubGlobal('AudioContext', Context);
  audio = new GameAudio();
});
afterEach(async () => { await audio.destroy(); vi.unstubAllGlobals(); vi.useRealTimers(); });

describe('procedural audio lifecycle', () => {
  it('never starts from restored preferences, snapshots, or queued UI cues', async () => {
    audio.configure({ volume: .4, music: true });
    audio.setActivity(false); audio.setActivity(true);
    audio.update(30, true, { walkSpeed: 7 }); audio.cue('job-complete');
    expect(Context.all).toHaveLength(0);
    expect(audio.diagnostics).toMatchObject({ started: false, muted: true });
    await audio.enable(); await audio.enable();
    expect(Context.all).toHaveLength(1);
    expect(audio.diagnostics).toMatchObject({ started: true, muted: false, contextState: 'running', volume: .4, music: true });
  });

  it('suspends in hidden tabs and menus without queuing missed footsteps or cues', async () => {
    await audio.enable();
    const context = Context.all[0];
    audio.cue('job-start'); expect(audio.diagnostics.activeVoices).toBe(2);
    document.hidden = true; document.dispatchEvent(new Event('visibilitychange')); await settle();
    expect(context.state).toBe('suspended'); expect(audio.diagnostics.activeVoices).toBe(0);
    const nodes = context.nodes.length;
    context.currentTime += 60; audio.update(0, false, { walkSpeed: 12 }); audio.cue('signal');
    expect(context.nodes).toHaveLength(nodes);
    document.hidden = false; document.dispatchEvent(new Event('visibilitychange')); await settle();
    expect(context.state).toBe('running');
    audio.update(0, false, { walkSpeed: 12 });
    expect(audio.diagnostics.activeVoices).toBe(0);
    audio.setActivity(false); await settle(); expect(context.state).toBe('suspended');
    audio.setActivity(true); await settle(); expect(context.state).toBe('running');
  });

  it('keeps explicit mute across focus changes and safely validates volume', async () => {
    await audio.enable();
    const context = Context.all[0];
    audio.configure({ volume: 2 }); expect(audio.diagnostics.volume).toBe(1);
    audio.configure({ volume: Number.NaN }); expect(audio.diagnostics.volume).toBe(1);
    audio.configure({ volume: -1 }); expect(audio.diagnostics.volume).toBe(0);
    expect(context.nodes[0].gain.value).toBe(0);
    audio.cue('job-complete'); expect(audio.diagnostics.activeVoices).toBe(0);
    await toggleAudio();
    document.hidden = true; document.dispatchEvent(new Event('visibilitychange')); await settle();
    document.hidden = false; document.dispatchEvent(new Event('visibilitychange')); await settle();
    expect(audio.diagnostics).toMatchObject({ muted: true, contextState: 'suspended' });
    expect(context.resume).toHaveBeenCalledTimes(1);
  });

  it('bounds one-shot voices and disconnects ended or interrupted graphs', async () => {
    await audio.enable();
    const context = Context.all[0];
    const loops = context.nodes.length;
    for (let i = 0; i < 100; i++) { context.currentTime++; audio.cue('job-complete'); }
    expect(audio.diagnostics.activeVoices).toBe(24);
    expect(context.nodes.length - loops).toBe(48); // 24 oscillator + envelope pairs.
    const ended = context.nodes.slice(loops).filter(node => node.onended)[0];
    ended.onended!(); expect(ended.disconnected).toBe(true);
    expect(audio.diagnostics.activeVoices).toBe(23);
    audio.setActivity(false); await settle();
    expect(audio.diagnostics.activeVoices).toBe(0);
    expect(context.nodes.slice(loops).every(node => node.disconnected)).toBe(true);
  });

  it('uses measured movement for footsteps and bounds delayed frame catch-up', async () => {
    await audio.enable();
    const context = Context.all[0];
    context.currentTime += .2; audio.update(0, false, { walkSpeed: 0 });
    expect(audio.diagnostics.activeVoices).toBe(0);
    context.currentTime += 90; audio.update(0, false, { walkSpeed: 12 });
    expect(audio.diagnostics.activeVoices).toBe(2);
    context.currentTime += .1; audio.update(Number.NaN, true, { walkSpeed: 12 });
    expect(audio.diagnostics.activeVoices).toBe(4); // One enter sound, no walking while driving.
    expect(context.nodes.every(node => Number.isFinite(node.frequency.value))).toBe(true);
  });

  it('recovers from browser refusal without claiming sound is enabled', async () => {
    // Create a paused context through an explicit gesture while inactive, then refuse resume.
    audio.setActivity(false); await audio.enable();
    const context = Context.all[0];
    context.resume.mockRejectedValueOnce(new Error('gesture required'));
    audio.setActivity(true); await settle();
    context.resume.mockRejectedValueOnce(new Error('gesture required'));
    await expect(audio.enable()).rejects.toThrow('gesture required');
    expect(audio.diagnostics.muted).toBe(true);
    await audio.enable(); expect(audio.diagnostics.contextState).toBe('running');
  });

  it('samples the native post-master buffer on demand without substituting mute labels', async () => {
    expect(audio.diagnostics).toMatchObject({ outputRms: 0, outputPeak: 0 });
    await audio.enable();
    const analyser = Context.all[0].nodes[1];
    analyser.waveformSample = .25;
    expect(audio.diagnostics).toMatchObject({ outputRms: .25, outputPeak: .25 });
    await toggleAudio();
    // Native analysers retain a last buffer while suspended. Do not fabricate mute evidence.
    expect(audio.diagnostics).toMatchObject({ muted: true, outputRms: .25, outputPeak: .25 });
    analyser.waveformSample = Number.NaN;
    expect(audio.diagnostics).toMatchObject({ outputRms: 0, outputPeak: 0 });
    analyser.waveformSample = 2;
    expect(audio.diagnostics).toMatchObject({ outputRms: 1, outputPeak: 1 });
    await audio.destroy();
    expect(audio.diagnostics).toMatchObject({ outputRms: 0, outputPeak: 0 });
  });

  it('allows a mute fade to finish, and cancels a stale fade when re-enabled', async () => {
    await audio.enable();
    const context = Context.all[0];
    const muting = audio.toggle();
    await vi.advanceTimersByTimeAsync(30);
    expect(context.state).toBe('running'); expect(context.suspend).not.toHaveBeenCalled();
    await audio.toggle(); await settle(); await muting;
    expect(context.state).toBe('running'); expect(context.suspend).not.toHaveBeenCalled();
    const finalMute = audio.toggle();
    await vi.advanceTimersByTimeAsync(80); await finalMute;
    expect(context.state).toBe('suspended'); expect(audio.diagnostics.muted).toBe(true);
  });

  it('repairs a late suspend completion after a newer enable request', async () => {
    await audio.enable();
    const context = Context.all[0];
    let finishSuspend: (() => void) | undefined;
    context.suspend.mockImplementationOnce(() => new Promise<void>(resolve => {
      finishSuspend = () => { context.state = 'suspended'; resolve(); };
    }));
    const muting = audio.toggle(); await settle();
    expect(finishSuspend).toBeDefined();
    await audio.toggle(); finishSuspend!(); await muting;
    expect(audio.diagnostics).toMatchObject({ muted: false, contextState: 'running' });
  });

  it('auditions settings while muted and paused, then restores the previous state', async () => {
    audio.setActivity(false); audio.configure({ volume: .3, music: true });
    const audition = audio.preview(); await settle();
    expect(audio.diagnostics).toMatchObject({ muted: true, active: false, previewing: true, contextState: 'running', volume: .3, music: true, activeVoices: 4 });
    await vi.advanceTimersByTimeAsync(800); await audition;
    expect(audio.diagnostics).toMatchObject({ muted: true, active: false, previewing: false, contextState: 'suspended', volume: .3, music: true, activeVoices: 0 });
    expect(vi.getTimerCount()).toBe(0);
  });

  it('returns an audition to enabled gameplay without suspending or changing preferences', async () => {
    await audio.enable(); audio.configure({ volume: .42, music: false });
    const audition = audio.preview(); await settle();
    expect(audio.diagnostics).toMatchObject({ previewing: true, muted: false, active: true });
    await vi.advanceTimersByTimeAsync(800); await audition;
    expect(audio.diagnostics).toMatchObject({ previewing: false, muted: false, active: true, contextState: 'running', volume: .42, music: false });
    expect(Context.all[0].suspend).not.toHaveBeenCalled();
    expect(vi.getTimerCount()).toBe(0);
  });

  it('obeys zero audition volume, replaces overlapping previews, and never restarts after hiding', async () => {
    audio.configure({ volume: 0 });
    const silent = audio.preview(); await settle();
    expect(audio.diagnostics.activeVoices).toBe(0);
    audio.configure({ volume: .4 });
    const heard = audio.preview(); await settle(); await silent;
    expect(audio.diagnostics.activeVoices).toBe(2);
    document.hidden = true; document.dispatchEvent(new Event('visibilitychange')); await settle(); await heard;
    expect(audio.diagnostics).toMatchObject({ muted: true, previewing: false, contextState: 'suspended', activeVoices: 0 });
    await vi.advanceTimersByTimeAsync(3000);
    expect(Context.all[0].resume).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('cancels an audition on explicit mute and destroys pending audition work', async () => {
    await audio.enable(); audio.setActivity(false); await settle();
    const audition = audio.preview(); await settle();
    await toggleAudio(); await audition;
    expect(audio.diagnostics).toMatchObject({ muted: true, previewing: false, contextState: 'suspended', activeVoices: 0 });
    const another = audio.preview(); await settle();
    await audio.destroy(); await another;
    expect(audio.diagnostics).toMatchObject({ muted: true, previewing: false, contextState: 'closed', activeVoices: 0 });
    expect(vi.getTimerCount()).toBe(0);
  });

  it('coalesces routine notifications and lets completion take priority without a cue backlog', async () => {
    await audio.enable();
    const context = Context.all[0];
    audio.cue('signal'); expect(audio.diagnostics.activeVoices).toBe(2);
    audio.cue('error'); audio.cue('ui'); audio.cue('job-progress');
    expect(audio.diagnostics.activeVoices).toBe(2);
    audio.cue('job-complete'); expect(audio.diagnostics.activeVoices).toBe(5);
    context.currentTime += .3; audio.cue('job-progress');
    expect(audio.diagnostics.activeVoices).toBe(5);
    context.currentTime += .5; audio.cue('job-progress');
    expect(audio.diagnostics.activeVoices).toBe(7);
  });

  it('keeps engine pitch stable when speed jitters around a gear threshold', async () => {
    await audio.enable();
    const engine = Context.all[0].nodes.filter(node => node.oscillator)[2];
    const pitches = [8.9, 9.1, 8.95, 9.2].map(speed => { audio.update(speed, true); return engine.frequency.value; });
    expect(Math.max(...pitches) - Math.min(...pitches)).toBeLessThan(1);
    audio.update(10, true); expect(engine.frequency.value).toBeCloseTo(58);
    audio.update(9, true); expect(engine.frequency.value).toBeCloseTo(55.3);
    audio.update(8, true); expect(engine.frequency.value).toBeCloseTo(64.6);
  });

  it('closes every loop and prevents reactivation after shutdown', async () => {
    await audio.enable(); audio.cue('horn');
    const context = Context.all[0];
    await audio.destroy(); await audio.destroy();
    expect(context.close).toHaveBeenCalledTimes(1);
    expect(context.nodes.every(node => node.disconnected)).toBe(true);
    const resumes = context.resume.mock.calls.length;
    document.dispatchEvent(new Event('visibilitychange'));
    await audio.enable(); audio.setActivity(true); await settle();
    expect(context.resume).toHaveBeenCalledTimes(resumes);
    expect(Context.all).toHaveLength(1);
    expect(audio.diagnostics).toMatchObject({ contextState: 'closed', muted: true, activeVoices: 0 });
  });
});
