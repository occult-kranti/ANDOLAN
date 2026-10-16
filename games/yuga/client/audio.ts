import { heroById } from '../shared/heroes';
import type { Actor, ArenaSnapshot, GameEvent, HeroDef, Vec } from '../shared/types';

type Bus = 'game' | 'preview';
interface Voice { source: AudioScheduledSourceNode; nodes: AudioNode[]; priority: number; bus: Bus }
interface Pending { timer: ReturnType<typeof setTimeout>; resolve: () => void }
interface Spatial { pan: number; gain: number }
const VOICE_LIMIT = 20;
const finite = (value: number, fallback = 0) => Number.isFinite(value) ? value : fallback;
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

/** Original synthesis only: no samples, speech, recordings, network audio or sacred chants. */
export class ArenaAudio {
  private context?: AudioContext;
  private master?: GainNode;
  private audition?: GainNode;
  private analyser?: AnalyserNode;
  private noise?: AudioBuffer;
  private nodes: AudioNode[] = [];
  private voices = new Set<Voice>();
  private waveform = new Float32Array(256);
  private muted = true;
  private active = false;
  private volume = .6;
  private rhythm = false;
  private unlocked = false;
  private destroyed = false;
  private previewing = false;
  private needsGesture = false;
  private revision = 0;
  private pendingFade?: Pending;
  private pendingPreview?: Pending;
  private baseline = true;
  private room = '';
  private listenerId = '';
  private matchSeed = 0;
  private snapshotTime = -1;
  private lastEvent = 0;
  private structureHealth = new Map<string, number>();
  private cooldowns = new Map<string, number>();
  private priorityUntil = 0;
  private nextBeat = 0;
  private beat = 0;

  constructor() { document.addEventListener('visibilitychange', this.visibilityChanged); }

  /** Root owns persistence. Neither this method nor a restored preference creates audio. */
  setVolume(value: number) {
    if (Number.isFinite(value)) this.volume = clamp(value, 0, 1);
    this.mix(.06);
  }
  setMuted(muted: boolean) {
    if (this.muted === muted || this.destroyed) return;
    this.muted = muted;
    void this.reconcile().catch(() => { this.needsGesture = true; });
  }
  setActive(active: boolean) {
    if (this.active === active || this.destroyed) return;
    this.active = active; this.baseline = true;
    void this.reconcile().catch(() => { this.needsGesture = true; });
  }
  /** Optional original light percussion; off until explicitly selected. */
  setRhythm(enabled: boolean) { this.rhythm = enabled; this.nextBeat = 0; }

  /** Invoke directly from Play/Enable click; unlock preserves the saved mute preference. */
  async unlock(): Promise<void> {
    if (this.destroyed || document.hidden) return;
    this.initialize();
    const revision = ++this.revision;
    this.cancelPending('fade'); this.cancelPreview();
    try {
      await this.context!.resume();
      if (this.destroyed) return;
      this.unlocked = true; this.needsGesture = false;
      if (revision !== this.revision) { this.mix(.14); await this.repairContext(); return; }
      await this.reconcile();
    } catch (error) { this.needsGesture = true; throw error; }
  }

  /** A short settings audition, including when muted, without changing any preferences. */
  async preview(): Promise<void> {
    if (this.destroyed || document.hidden) return;
    this.initialize();
    const revision = ++this.revision;
    this.cancelPending('fade'); this.cancelPreview(); this.previewing = true;
    this.mix(.04);
    try {
      await this.context!.resume();
      if (revision !== this.revision || this.destroyed || document.hidden) { await this.repairContext(); return; }
      this.unlocked = true; this.needsGesture = false; this.mix(.04);
      this.tone(293.66, .22, .07, { pan: -.22, gain: 1 }, 3, 'preview', .04);
      this.tone(440, .33, .06, { pan: .22, gain: 1 }, 3, 'preview', .18);
      if (this.rhythm) this.tone(104, .12, .035, { pan: 0, gain: 1 }, 3, 'preview', .36, 51);
      await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(() => {
          this.pendingPreview = undefined;
          if (revision !== this.revision) { resolve(); return; }
          this.previewing = false;
          void this.reconcile().then(resolve, reject);
        }, 650);
        this.pendingPreview = { timer, resolve };
      });
    } catch (error) {
      if (revision === this.revision) { this.cancelPreview(); this.mix(0); await this.repairContext().catch(() => {}); }
      this.needsGesture = true; throw error;
    }
  }

  /** Sample authoritative events once. Input/button presses never claim a cast, hit or kill. */
  update(snapshot: ArenaSnapshot, playerId: string) {
    const listener = snapshot.actors.find(actor => actor.id === playerId);
    const newest = snapshot.events.reduce((id, event) => Math.max(id, event.id), 0);
    const reset = this.baseline || playerId !== this.listenerId || snapshot.room !== this.room || snapshot.seed !== this.matchSeed || snapshot.time < this.snapshotTime;
    this.listenerId = playerId; this.room = snapshot.room; this.matchSeed = snapshot.seed; this.snapshotTime = snapshot.time;
    if (reset || !listener || !this.canPlay || this.previewing) {
      this.lastEvent = newest; this.baseline = false;
      this.structureHealth = new Map(snapshot.structures.map(structure => [structure.id, structure.health]));
      if (reset) { this.cooldowns.clear(); this.priorityUntil = 0; this.nextBeat = 0; }
      return;
    }
    const fresh = snapshot.events.filter(event => event.id > this.lastEvent && snapshot.time - event.time <= .6 && event.time <= snapshot.time + .01);
    this.lastEvent = Math.max(this.lastEvent, newest);
    // Important outcomes precede nearby combat when a delayed frame contains many events.
    fresh.sort((a, b) => this.eventPriority(b, playerId) - this.eventPriority(a, playerId) || b.id - a.id);
    let cues = 0;
    for (const event of fresh) {
      if (cues >= 5) break;
      if (this.playEvent(event, snapshot, listener)) cues++;
    }
    for (const structure of snapshot.structures) {
      const previous = this.structureHealth.get(structure.id);
      this.structureHealth.set(structure.id, structure.health);
      if (snapshot.phase !== 'playing' || structure.team !== listener.team || previous === undefined || structure.health <= 0 || structure.health >= previous) continue;
      const nearby = Math.hypot(structure.x - listener.x, structure.z - listener.z) < 34;
      if ((structure.kind === 'core' || nearby) && this.allowed('under-attack', 6, true)) {
        this.tone(196, .16, .065, { pan: 0, gain: 1 }, 3);
        this.tone(146.83, .22, .055, { pan: 0, gain: 1 }, 3, 'game', .13);
      }
    }
    if (this.rhythm && snapshot.phase === 'playing' && listener.health > 0) this.rhythmBeat();
  }

  private eventPriority(event: GameEvent, playerId: string) {
    if (event.type === 'victory') return 5;
    if (event.type === 'defeat' && (event.actorId === playerId || event.targetId === playerId)) return 4;
    // A camp and its buff can arrive together. Play the combined camp cue first
    // so the paired reward does not become two overlapping notifications.
    if (event.type === 'camp' && event.actorId === playerId) return 3;
    if (event.type === 'tower' || event.type === 'core' || (event.type === 'hit' && event.targetId === playerId)) return 3;
    return event.actorId === playerId ? 2 : 1;
  }
  private spatial(origin: Vec, listener: Actor): Spatial {
    const dx = origin.x - listener.x, dz = origin.z - listener.z, distance = Math.hypot(dx, dz);
    return { pan: clamp((dx * Math.cos(listener.yaw) - dz * Math.sin(listener.yaw)) / Math.max(1, distance), -.85, .85), gain: distance > 42 ? 0 : 1 / (1 + Math.pow(distance / 15, 2)) };
  }
  private playEvent(event: GameEvent, snapshot: ArenaSnapshot, listener: Actor): boolean {
    const source = snapshot.actors.find(actor => actor.id === event.actorId);
    if (event.type !== 'victory' && this.context!.currentTime < this.priorityUntil) return false;
    const local = event.actorId === listener.id;
    const enemy = event.team !== listener.team;
    const spatial = local ? { pan: 0, gain: 1 } : this.spatial(event, listener);
    const priority = local ? 2 : 1;
    if (event.type === 'victory') {
      if (!this.allowed('outcome', 10, true)) return false;
      this.priorityUntil = this.context!.currentTime + 1;
      const notes = snapshot.winner === 'draw' ? [293.66, 329.63] : snapshot.winner === listener.team ? [293.66, 440, 587.33] : [293.66, 220, 146.83];
      notes.forEach((note, i) => this.tone(note, .5, .09 - i * .01, { pan: 0, gain: 1 }, 4, 'game', i * .18)); return true;
    }
    if (event.type === 'tower' || event.type === 'core') {
      if (!this.allowed('structure-fall', 1, true)) return false;
      const target = snapshot.structures.find(structure => structure.id === event.targetId);
      const friendlyLost = target?.team === listener.team;
      this.tone(friendlyLost ? 174.61 : 392, .3, .08, { pan: 0, gain: 1 }, 3);
      this.tone(friendlyLost ? 130.81 : 523.25, .38, .065, { pan: 0, gain: 1 }, 3, 'game', .18); return true;
    }
    if (event.type === 'defeat') {
      if (event.targetId === listener.id && this.allowed('death', 2, true)) {
        this.tone(146.83, .3, .085, { pan: 0, gain: 1 }, 4, 'game', 0, 73.42); return true;
      }
      const target = snapshot.actors.find(actor => actor.id === event.targetId);
      if (local && target?.kind === 'hero' && this.allowed('kill', .6, true)) {
        this.tone(523.25, .16, .06, { pan: -.08, gain: 1 }, 3);
        this.tone(659.25, .26, .06, { pan: .08, gain: 1 }, 3, 'game', .11); return true;
      }
      return false;
    }
    if (event.type === 'hit') {
      if (event.targetId === listener.id && this.allowed('hurt', .22, true)) {
        this.noiseHit(.075, .07, 650, this.spatial(source ?? snapshot.neutrals.find(neutral => neutral.id === event.actorId) ?? snapshot.structures.find(structure => structure.id === event.actorId) ?? event, listener), 3);
        this.tone(84, .1, .055, { pan: 0, gain: 1 }, 3, 'game', 0, 53); return true;
      }
      if (local && this.allowed('hit-confirm', .12)) { this.tone(930, .045, .028, { pan: 0, gain: 1 }, 2); return true; }
      return false;
    }
    if (event.type === 'gold') {
      if (!local || !Number.isFinite(event.amount) || event.amount! <= 0 || (event.reward !== 'secure' && event.reward !== 'steal') || !this.allowed('gold', .20)) return false;
      // A small, distinct interval communicates a steal without louder fanfare.
      // Credits, shard appearance and input presses never trigger these cues.
      const steal = event.reward === 'steal';
      this.tone(steal ? 659.25 : 587.33, .075, .032, spatial, 2);
      this.tone(steal ? 880 : 783.99, .13, .026, spatial, 2, 'game', .055);
      return true;
    }
    if (event.type === 'camp' || event.type === 'buff') {
      if (!local || !event.targetId) return false;
      if (event.type === 'camp' && (!Number.isFinite(event.amount) || event.amount! <= 0)) return false;
      if (event.type === 'buff' && !['vigor', 'haste', 'ward'].includes(event.buff ?? '')) return false;
      // Same-target pairing also works when the two authoritative events are
      // split across snapshots. All keys share the existing bounded cooldown map.
      if (!this.allowed(`camp-buff:${event.targetId}`, 1.2) || !this.allowed('camp-buff', .45)) return false;
      if (event.type === 'camp') {
        this.tone(349.23, .17, .046, spatial, 2);
        this.tone(523.25, .24, .038, spatial, 2, 'game', .10);
      } else {
        const pitch = event.buff === 'vigor' ? 293.66 : event.buff === 'haste' ? 440 : 349.23;
        this.tone(pitch, .21, .038, spatial, 2, 'game', 0, pitch * 1.5);
      }
      return true;
    }
    if ((event.type === 'pickup' || event.type === 'upgrade') && local && this.allowed('reward', .3)) {
      this.tone(440, .12, .05, spatial, 2); this.tone(587.33, .2, .045, spatial, 2, 'game', .1); return true;
    }
    if (!source || source.kind !== 'hero' || spatial.gain < .12 || snapshot.phase !== 'playing') return false;
    if (event.type === 'shot' && this.allowed(`shot:${source.id}`, Math.max(.09, heroById(source.heroId).fireInterval * .75))) {
      this.weapon(heroById(source.heroId).weapon, spatial, enemy, priority); return true;
    }
    if (event.type === 'ability' && this.allowed(`cast:${source.id}`, .3)) {
      const pitch = enemy ? 261.63 : 349.23;
      this.tone(pitch, .2, .065, spatial, priority, 'game', 0, enemy ? pitch * .8 : pitch * 1.35);
      this.noiseHit(.16, .035, 1700, spatial, priority); return true;
    }
    return false;
  }
  private weapon(weapon: HeroDef['weapon'], spatial: Spatial, enemy: boolean, priority: number) {
    const pitch = enemy ? .88 : 1;
    if (weapon === 'bow') {
      this.tone(390 * pitch, .13, .065, spatial, priority, 'game', 0, 145 * pitch, 'triangle');
      this.noiseHit(.045, .045, 2100, spatial, priority);
    } else if (weapon === 'mace') {
      this.tone(112 * pitch, .18, .09, spatial, priority, 'game', 0, 48, 'triangle');
      this.noiseHit(.11, .06, 750, spatial, priority);
    } else if (weapon === 'staff') {
      this.tone(330 * pitch, .2, .06, spatial, priority, 'game', 0, 510 * pitch);
      this.tone(660 * pitch, .14, .022, spatial, priority, 'game', .035);
    } else if (weapon === 'chakram') {
      this.tone(740 * pitch, .15, .036, spatial, priority, 'game', 0, 420 * pitch);
      this.tone(1115 * pitch, .11, .018, spatial, priority);
    } else {
      this.tone(265 * pitch, .1, .065, spatial, priority, 'game', 0, 120 * pitch, 'triangle');
      this.noiseHit(.065, .04, 1350, spatial, priority);
    }
  }
  private rhythmBeat() {
    const now = this.context!.currentTime;
    if (now < this.nextBeat || now < this.priorityUntil) return;
    this.nextBeat = now + .375;
    const accent = [1, 0, .35, 0, .65, 0, .35, 0][this.beat++ % 8];
    if (accent) this.tone(accent === 1 ? 112 : 190, .09, .018 * accent, { pan: accent === 1 ? -.12 : .12, gain: 1 }, 0, 'game', 0, accent === 1 ? 49 : 135, 'triangle');
  }
  private allowed(key: string, interval: number, important = false) {
    const now = this.context!.currentTime;
    if ((!important && now < this.priorityUntil) || now - (this.cooldowns.get(key) ?? -Infinity) < interval) return false;
    if (!this.cooldowns.has(key) && this.cooldowns.size >= 64) this.cooldowns.delete(this.cooldowns.keys().next().value!);
    this.cooldowns.set(key, now); return true;
  }

  get diagnostics() {
    let sum = 0, peak = 0;
    if (this.analyser && !this.destroyed) {
      this.analyser.getFloatTimeDomainData(this.waveform);
      for (const sample of this.waveform) { const value = clamp(finite(sample), -1, 1); sum += value * value; peak = Math.max(peak, Math.abs(value)); }
    }
    return { started: !!this.context, unlocked: this.unlocked, muted: this.muted, active: this.active, volume: this.volume, rhythm: this.rhythm, previewing: this.previewing, needsGesture: this.needsGesture, contextState: this.context?.state ?? 'uninitialized', contextTime: this.context?.currentTime ?? 0, activeVoices: this.voices.size, outputRms: Math.sqrt(sum / this.waveform.length), outputPeak: peak };
  }
  private get audible() { return this.unlocked && !this.muted && this.active && !document.hidden && !this.destroyed; }
  private get canPlay() { return this.audible && this.context?.state === 'running' && this.volume > 0; }
  private get shouldRun() { return !this.destroyed && !document.hidden && (this.audible || this.previewing); }
  private visibilityChanged = () => { this.baseline = true; void this.reconcile().catch(() => { this.needsGesture = true; }); };

  private initialize() {
    if (this.context) return;
    const context = this.context = new AudioContext();
    this.analyser = context.createAnalyser(); this.analyser.fftSize = 256; this.analyser.smoothingTimeConstant = 0;
    this.analyser.connect(context.destination);
    const compressor = context.createDynamicsCompressor(); compressor.threshold.value = -16; compressor.knee.value = 15; compressor.ratio.value = 5; compressor.attack.value = .006; compressor.release.value = .16;
    compressor.connect(this.analyser);
    this.master = context.createGain(); this.master.gain.value = 0; this.master.connect(compressor);
    this.audition = context.createGain(); this.audition.gain.value = 0; this.audition.connect(compressor);
    this.nodes.push(this.analyser, compressor, this.master, this.audition);
    this.noise = context.createBuffer(1, Math.round(context.sampleRate * .3), context.sampleRate);
    const data = this.noise.getChannelData(0); let seed = 5731;
    for (let i = 0; i < data.length; i++) { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; data[i] = seed / 2147483648 - 1; }
  }
  private ramp(param: AudioParam | undefined, value: number, duration: number) {
    if (!param || !this.context || this.context.state === 'closed') return;
    const now = this.context.currentTime;
    if (typeof param.cancelAndHoldAtTime === 'function') param.cancelAndHoldAtTime(now);
    else { const current = param.value; param.cancelScheduledValues(now); param.setValueAtTime(current, now); }
    if (duration) param.linearRampToValueAtTime(value, now + duration); else param.setValueAtTime(value, now);
  }
  private mix(duration = .08) {
    this.ramp(this.master?.gain, this.audible && !this.previewing ? this.volume * .65 : 0, duration);
    this.ramp(this.audition?.gain, this.previewing && !document.hidden ? this.volume * .65 : 0, .02);
  }
  private cancelPending(kind: 'fade' | 'preview') {
    const pending = kind === 'fade' ? this.pendingFade : this.pendingPreview;
    if (!pending) return;
    clearTimeout(pending.timer); pending.resolve();
    if (kind === 'fade') this.pendingFade = undefined; else this.pendingPreview = undefined;
  }
  private cancelPreview() { this.cancelPending('preview'); this.previewing = false; this.stopVoices('preview'); }
  private async repairContext() {
    const context = this.context;
    if (!context || this.destroyed || context.state === 'closed') return;
    if (this.shouldRun && context.state !== 'running') await context.resume();
    else if (!this.shouldRun && context.state === 'running') await context.suspend();
  }
  private async reconcile() {
    const revision = ++this.revision;
    this.cancelPending('fade'); this.cancelPreview();
    const context = this.context;
    if (!context || context.state === 'closed') return;
    if (this.audible) {
      if (context.state !== 'running') { this.ramp(this.master?.gain, 0, 0); await context.resume(); }
      if (revision !== this.revision) { await this.repairContext(); return; }
      this.mix(.14);
    } else {
      const fade = !document.hidden && context.state === 'running'; this.mix(fade ? .06 : 0);
      if (fade) await new Promise<void>(resolve => { const timer = setTimeout(() => { this.pendingFade = undefined; resolve(); }, 65); this.pendingFade = { timer, resolve }; });
      if (revision !== this.revision) return;
      this.stopVoices();
      if (context.state === 'running') await context.suspend();
      if (revision !== this.revision) await this.repairContext();
    }
  }
  private reserve(priority: number) {
    if (this.voices.size < VOICE_LIMIT) return true;
    const victim = [...this.voices].find(voice => voice.priority < priority);
    if (!victim) return false;
    this.stopVoice(victim); return true;
  }
  private register(source: AudioScheduledSourceNode, nodes: AudioNode[], end: number, priority: number, bus: Bus) {
    const voice: Voice = { source, nodes, priority, bus }; this.voices.add(voice);
    source.onended = () => { nodes.forEach(node => node.disconnect()); this.voices.delete(voice); };
    source.stop(end);
  }
  private tone(frequency: number, duration: number, level: number, spatial: Spatial, priority: number, bus: Bus = 'game', delay = 0, endFrequency = frequency, type: OscillatorType = 'sine') {
    if (!this.context || this.volume === 0 || !this.reserve(priority)) return;
    const start = this.context.currentTime + delay, oscillator = this.context.createOscillator(), gain = this.context.createGain(), pan = this.context.createStereoPanner();
    oscillator.type = type; oscillator.frequency.setValueAtTime(frequency, start); oscillator.frequency.exponentialRampToValueAtTime(endFrequency, start + duration);
    gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(level * spatial.gain, start + Math.min(.012, duration / 3)); gain.gain.exponentialRampToValueAtTime(.0001, start + duration);
    pan.pan.value = spatial.pan; oscillator.connect(gain); gain.connect(pan); pan.connect(bus === 'preview' ? this.audition! : this.master!); oscillator.start(start);
    this.register(oscillator, [oscillator, gain, pan], start + duration + .025, priority, bus);
  }
  private noiseHit(duration: number, level: number, frequency: number, spatial: Spatial, priority: number) {
    if (!this.context || this.volume === 0 || !this.reserve(priority)) return;
    const start = this.context.currentTime, source = this.context.createBufferSource(), filter = this.context.createBiquadFilter(), gain = this.context.createGain(), pan = this.context.createStereoPanner();
    source.buffer = this.noise!; filter.type = 'bandpass'; filter.frequency.value = frequency; filter.Q.value = .7;
    gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(level * spatial.gain, start + .008); gain.gain.exponentialRampToValueAtTime(.0001, start + duration);
    pan.pan.value = spatial.pan; source.connect(filter); filter.connect(gain); gain.connect(pan); pan.connect(this.master!); source.start(start);
    this.register(source, [source, filter, gain, pan], start + duration + .025, priority, 'game');
  }
  private stopVoice(voice: Voice) {
    voice.source.onended = null; try { voice.source.stop(); } catch { /* Already finished. */ }
    voice.nodes.forEach(node => node.disconnect()); this.voices.delete(voice);
  }
  private stopVoices(bus?: Bus) { for (const voice of this.voices) if (!bus || voice.bus === bus) this.stopVoice(voice); }
  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true; this.muted = true; this.revision++;
    document.removeEventListener('visibilitychange', this.visibilityChanged);
    this.cancelPending('fade'); this.cancelPreview(); this.stopVoices();
    this.nodes.forEach(node => node.disconnect()); this.nodes = []; this.analyser = undefined; this.waveform.fill(0);
    if (this.context && this.context.state !== 'closed') void this.context.close().catch(() => {});
  }
}
