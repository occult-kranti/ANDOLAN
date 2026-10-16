/** Original procedural audio. No recordings, third-party music, or network requests. */
export type SoundCue = 'ui' | 'job-start' | 'job-progress' | 'job-complete' | 'signal' | 'horn' | 'error';
export interface AudioSettings { volume: number; music: boolean }
export interface AudioMotion { walkSpeed?: number; interior?: boolean }
interface Voice { source: AudioScheduledSourceNode; nodes: AudioNode[]; bus: 'effects' | 'preview' }
const MAX_VOICES = 24;
const safeNumber = (value: number, fallback = 0) => Number.isFinite(value) ? value : fallback;
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

export class GameAudio {
  private context?: AudioContext;
  private master?: GainNode;
  private analyser?: AnalyserNode;
  private waveform = new Float32Array(256);
  private effects?: GainNode;
  private atmosphere?: GainNode;
  private musicGain?: GainNode;
  private previewGain?: GainNode;
  private engineGain?: GainNode;
  private roadGain?: GainNode;
  private engineFilter?: BiquadFilterNode;
  private engines: OscillatorNode[] = [];
  private musicNotes: OscillatorNode[] = [];
  private noise?: AudioBuffer;
  private loopSources: AudioScheduledSourceNode[] = [];
  private graph: AudioNode[] = [];
  private voices = new Set<Voice>();
  private lastCue = new Map<string, number>();
  private notificationUntil = 0;
  private priorityUntil = 0;
  private gear = 0;
  private transitionRevision = 0;
  private previewing = false;
  private pendingFade?: { timer: ReturnType<typeof setTimeout>; resolve: () => void };
  private pendingPreview?: { timer: ReturnType<typeof setTimeout>; resolve: () => void };
  private settings: AudioSettings = { volume: .65, music: false };
  private active = true;
  private destroyed = false;
  private driving = false;
  private lastUpdate = 0;
  private walked = 0;
  private nextChord = 0;
  private chord = 0;
  muted = true;

  constructor() {
    document.addEventListener('visibilitychange', this.visibilityChanged);
  }

  /** Read-only evidence for the development harness; no production global is installed. */
  get diagnostics() {
    // Read the post-master native buffer only on demand. A suspended context can retain
    // its final buffer: these measurements deliberately do not infer silence from labels.
    let squares = 0, outputPeak = 0;
    if (this.analyser && !this.destroyed) {
      this.analyser.getFloatTimeDomainData(this.waveform);
      for (const value of this.waveform) {
        const sample = clamp(safeNumber(value), -1, 1);
        squares += sample * sample; outputPeak = Math.max(outputPeak, Math.abs(sample));
      }
    }
    return {
      started: !!this.context, muted: this.muted, volume: this.settings.volume,
      music: this.settings.music, active: this.active, previewing: this.previewing,
      contextState: this.context?.state ?? 'uninitialized',
      contextTime: this.context?.currentTime ?? 0, activeVoices: this.voices.size,
      outputRms: Math.sqrt(squares / this.waveform.length), outputPeak,
    };
  }

  /** Preferences never create an AudioContext or opt the player into sound. */
  configure(settings: Partial<AudioSettings>) {
    if (typeof settings.volume === 'number' && Number.isFinite(settings.volume)) this.settings.volume = clamp(settings.volume, 0, 1);
    if (typeof settings.music === 'boolean') this.settings.music = settings.music;
    this.applyMix();
  }

  /** Call directly from a play/settings click, never from loading saved preferences. */
  async enable() {
    if (this.destroyed) return;
    this.initialize();
    this.muted = false;
    try { await this.reconcile(); }
    catch (error) { this.muted = true; this.applyMix(); throw error; }
  }

  async toggle() {
    if (this.muted) await this.enable();
    else {
      this.muted = true;
      await this.reconcile();
    }
    return this.muted;
  }

  /** Online simulation may continue while local audio is paused in a menu. */
  setActivity(active: boolean) {
    if (this.active === active || this.destroyed) return;
    this.active = active;
    this.resetMotion();
    void this.reconcile().catch(() => { /* A later explicit enable gesture can retry. */ });
  }

  private visibilityChanged = () => {
    this.resetMotion();
    void this.reconcile().catch(() => { /* Browsers may require a fresh enable gesture. */ });
  };

  private get audible() {
    return !this.muted && this.active && !document.hidden && !this.destroyed;
  }

  private get shouldRun() { return !this.destroyed && !document.hidden && (this.audible || this.previewing); }

  private cancelFade() {
    if (!this.pendingFade) return;
    clearTimeout(this.pendingFade.timer); this.pendingFade.resolve(); this.pendingFade = undefined;
  }
  private cancelPreview() {
    if (this.pendingPreview) {
      clearTimeout(this.pendingPreview.timer); this.pendingPreview.resolve(); this.pendingPreview = undefined;
    }
    this.previewing = false; this.stopVoices('preview');
    if (this.previewGain && this.context) this.ramp(this.previewGain.gain, 0, .015);
  }
  private fadeDelay() {
    return new Promise<void>(resolve => {
      const timer = setTimeout(() => { this.pendingFade = undefined; resolve(); }, 75);
      this.pendingFade = { timer, resolve };
    });
  }

  /** Explicit settings audition; preserves mute, volume, music and gameplay activity. */
  async preview(): Promise<void> {
    if (this.destroyed || document.hidden) return;
    this.initialize();
    const revision = ++this.transitionRevision;
    this.cancelFade(); this.cancelPreview(); this.previewing = true;
    const context = this.context!;
    this.applyMix(.04);
    try {
      if (context.state !== 'running') await context.resume();
      if (revision !== this.transitionRevision || !this.shouldRun) { await this.repairContextRace(context); return; }
      this.applyMix(.04);
      // The same volume control feeds this isolated bus, including an intentional zero.
      this.tone(293.66, .28, .065, .045, 'sine', 293.66, 'preview');
      this.tone(440, .38, .055, .19, 'sine', 440, 'preview');
      if (this.settings.music) {
        this.tone(146.83, .56, .025, .045, 'sine', 146.83, 'preview');
        this.tone(174.61, .56, .02, .045, 'sine', 174.61, 'preview');
      }
      await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(() => {
          this.pendingPreview = undefined;
          if (revision !== this.transitionRevision) { resolve(); return; }
          this.previewing = false;
          void this.reconcile().then(resolve, reject);
        }, 750);
        this.pendingPreview = { timer, resolve };
      });
    } catch (error) {
      if (revision === this.transitionRevision) {
        this.cancelPreview(); this.applyMix();
        await this.repairContextRace(context).catch(() => {});
      }
      throw error;
    }
  }

  private async repairContextRace(context: AudioContext) {
    if (this.destroyed || context.state === 'closed') return;
    if (this.shouldRun && context.state !== 'running') await context.resume();
    else if (!this.shouldRun && context.state === 'running') await context.suspend();
  }

  private async reconcile() {
    const revision = ++this.transitionRevision;
    this.cancelFade(); this.cancelPreview();
    const context = this.context;
    if (!context || context.state === 'closed') return;
    if (this.audible) {
      if (context.state !== 'running') {
        // A suspended gain can retain its previous value; start the new audible period at zero.
        this.ramp(this.master?.gain, 0, 0);
        await context.resume();
      }
      if (revision !== this.transitionRevision) { await this.repairContextRace(context); return; }
      this.applyMix(.16);
    } else {
      const canFade = !document.hidden && context.state === 'running';
      this.applyMix(canFade ? .07 : 0);
      if (canFade) await this.fadeDelay();
      if (revision !== this.transitionRevision) return;
      this.stopVoices();
      if (context.state === 'running') await context.suspend();
      if (revision !== this.transitionRevision) await this.repairContextRace(context);
    }
    this.lastUpdate = context.currentTime;
  }

  private node<T extends AudioNode>(node: T): T { this.graph.push(node); return node; }
  private gain(value: number, destination: AudioNode) {
    const node = this.node(this.context!.createGain());
    node.gain.value = value; node.connect(destination); return node;
  }
  private loopTone(frequency: number, type: OscillatorType, destination: AudioNode) {
    const source = this.node(this.context!.createOscillator());
    source.type = type; source.frequency.value = frequency; source.connect(destination);
    source.start(); this.loopSources.push(source); return source;
  }
  private loopNoise(frequency: number, type: BiquadFilterType, destination: AudioNode) {
    const filter = this.node(this.context!.createBiquadFilter());
    filter.type = type; filter.frequency.value = frequency; filter.Q.value = .6; filter.connect(destination);
    const source = this.node(this.context!.createBufferSource());
    source.buffer = this.noise!; source.loop = true; source.connect(filter); source.start(); this.loopSources.push(source);
  }

  private initialize() {
    if (this.context) return;
    const context = this.context = new AudioContext();
    this.lastUpdate = context.currentTime;
    this.master = this.node(context.createGain()); this.master.gain.value = 0;
    this.analyser = this.node(context.createAnalyser());
    this.analyser.fftSize = this.waveform.length; this.analyser.smoothingTimeConstant = 0;
    this.master.connect(this.analyser); this.analyser.connect(context.destination);
    this.previewGain = this.gain(0, this.analyser);
    const compressor = this.node(context.createDynamicsCompressor());
    compressor.threshold.value = -18; compressor.knee.value = 16; compressor.ratio.value = 4;
    compressor.attack.value = .006; compressor.release.value = .22; compressor.connect(this.master);
    this.effects = this.gain(.7, compressor);
    this.atmosphere = this.gain(.055, compressor);
    this.musicGain = this.gain(0, compressor);

    // Seeded soft noise with a loop seam blend keeps the city bed repeatable and click-free.
    this.noise = context.createBuffer(1, Math.round(context.sampleRate * 3), context.sampleRate);
    const data = this.noise.getChannelData(0);
    let seed = 173, smooth = 0;
    for (let i = 0; i < data.length; i++) {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      smooth = .94 * smooth + .06 * (seed / 2147483648 - 1);
      data[i] = smooth * 3;
    }
    const seam = Math.min(2048, Math.floor(data.length / 4));
    for (let i = 0; i < seam; i++) {
      const weight = i / (seam - 1);
      data[data.length - seam + i] = data[data.length - seam + i] * (1 - weight) + data[0] * weight;
    }
    this.loopNoise(850, 'lowpass', this.atmosphere);
    const farTraffic = this.gain(.13, this.atmosphere);
    this.loopTone(73.42, 'sine', farTraffic);
    this.loopTone(110.06, 'sine', farTraffic);

    this.engineGain = this.gain(0, this.effects);
    this.engineFilter = this.node(context.createBiquadFilter());
    this.engineFilter.type = 'lowpass'; this.engineFilter.frequency.value = 330; this.engineFilter.Q.value = .55;
    this.engineFilter.connect(this.engineGain);
    const body = this.gain(.68, this.engineFilter), mechanical = this.gain(.11, this.engineFilter);
    this.engines = [this.loopTone(43, 'triangle', body), this.loopTone(86.8, 'sawtooth', mechanical)];
    this.roadGain = this.gain(0, this.effects); this.loopNoise(1300, 'bandpass', this.roadGain);

    // Original restrained Dm9 / Cmaj9 / Gm9 / Dm9 pad; opt-in and no recognizable borrowed melody.
    this.musicNotes = [146.83, 174.61, 220, 329.63].map((note, index) => {
      const level = this.gain(index === 0 ? .32 : .18, this.musicGain!);
      const oscillator = this.loopTone(note, 'sine', level); oscillator.detune.value = index % 2 ? 3 : -3; return oscillator;
    });
  }

  private target(param: AudioParam | undefined, value: number, time = .08) {
    if (!param || !this.context || this.context.state === 'closed') return;
    // Cancel superseded ramps so long sessions never accumulate automation events.
    param.cancelScheduledValues(this.context.currentTime);
    param.setTargetAtTime(value, this.context.currentTime, time);
  }
  private ramp(param: AudioParam | undefined, value: number, duration: number) {
    if (!param || !this.context || this.context.state === 'closed') return;
    const now = this.context.currentTime;
    if (typeof param.cancelAndHoldAtTime === 'function') param.cancelAndHoldAtTime(now);
    else { const current = param.value; param.cancelScheduledValues(now); param.setValueAtTime(current, now); }
    if (duration <= 0) param.setValueAtTime(value, now);
    else param.linearRampToValueAtTime(value, now + duration);
  }
  private applyMix(duration = .08) {
    this.ramp(this.master?.gain, this.audible && !this.previewing ? this.settings.volume * .7 : 0, duration);
    this.ramp(this.previewGain?.gain, this.previewing && !document.hidden ? this.settings.volume * .7 : 0, .025);
    this.target(this.musicGain?.gain, this.settings.music ? .05 : 0, .5);
  }
  private resetMotion() {
    this.walked = 0; this.lastUpdate = this.context?.currentTime ?? 0;
    this.target(this.engineGain?.gain, 0); this.target(this.roadGain?.gain, 0);
  }

  /** Speed is metres/second. Feed measured on-foot motion, not pressed keys, for footsteps. */
  update(speed: number, driving: boolean, motion: AudioMotion = {}) {
    const context = this.context;
    const previousDriving = this.driving;
    this.driving = driving;
    if (!context || !this.audible || this.previewing || context.state !== 'running') { this.resetMotion(); return; }
    const now = context.currentTime, dt = clamp(now - this.lastUpdate, 0, .2);
    this.lastUpdate = now;
    speed = clamp(Math.abs(safeNumber(speed)), 0, 45);
    const roadSpeed = speed / 45;
    // Virtual gear changes keep acceleration from becoming a single rising electronic whistle.
    // A speed near a gear boundary must not repeatedly jump between two engine pitches.
    while (this.gear < 4 && speed > (this.gear + 1) * 9 + .8) this.gear++;
    while (this.gear > 0 && speed < this.gear * 9 - .8) this.gear--;
    const revs = 43 + speed * 2.7 - this.gear * 12;
    this.target(this.engines[0]?.frequency, revs, .12);
    this.target(this.engines[1]?.frequency, revs * 2.015, .12);
    this.target(this.engineFilter?.frequency, 240 + roadSpeed * 650, .12);
    this.target(this.engineGain?.gain, driving ? .13 + roadSpeed * .08 : 0, .12);
    this.target(this.roadGain?.gain, driving ? Math.pow(roadSpeed, .8) * .16 : 0, .15);
    this.target(this.atmosphere?.gain, motion.interior ? .018 : driving ? .032 : .055, .3);
    if (driving !== previousDriving) {
      this.tone(driving ? 76 : 60, .15, .15, 0, 'sine', 34);
      this.noiseHit(.08, .12, driving ? 440 : 650);
    }
    const walking = driving ? 0 : clamp(Math.abs(safeNumber(motion.walkSpeed ?? 0)), 0, 12);
    if (walking < .3) this.walked = 0;
    else {
      this.walked += walking * dt;
      if (this.walked >= 1.35) {
        this.walked %= 1.35;
        this.tone(motion.interior ? 105 : 75, .07, .11, 0, 'sine', 40);
        this.noiseHit(.045, .13, motion.interior ? 950 : 1800);
      }
    }
    if (this.settings.music && now >= this.nextChord) {
      const chords = [[146.83, 174.61, 220, 329.63], [130.81, 164.81, 196, 293.66], [98, 146.83, 174.61, 220], [146.83, 174.61, 220, 329.63]];
      const notes = chords[this.chord++ % chords.length];
      this.musicNotes.forEach((note, i) => this.target(note.frequency, notes[i], 1.8));
      this.nextChord = now + 12;
    }
  }

  cue(cue: SoundCue) {
    if (!this.context || !this.audible || this.previewing || this.context.state !== 'running' || this.settings.volume === 0) return;
    const now = this.context.currentTime;
    const cooldown = { horn: .8, ui: .14, 'job-start': .6, 'job-progress': .45, 'job-complete': 1, signal: .7, error: 1.1 }[cue];
    if (now - (this.lastCue.get(cue) ?? -Infinity) < cooldown) return;
    if (cue !== 'horn' && cue !== 'job-complete' && (now < this.notificationUntil || now < this.priorityUntil)) return;
    this.lastCue.set(cue, now);
    if (cue === 'job-complete') this.priorityUntil = now + .7;
    if (cue !== 'horn') this.notificationUntil = now + .24;
    if (cue === 'ui') this.tone(660, .085, .038);
    else if (cue === 'job-start') { this.tone(293.66, .17, .1); this.tone(440, .22, .09, .12); }
    else if (cue === 'job-progress') { this.tone(440, .12, .06); this.tone(587.33, .19, .055, .1); }
    else if (cue === 'job-complete') { this.tone(293.66, .3, .12); this.tone(440, .32, .1, .12); this.tone(587.33, .5, .1, .25); }
    else if (cue === 'signal') { this.tone(523.25, .15, .05); this.tone(659.25, .19, .045, .14); }
    else if (cue === 'error') { this.tone(220, .17, .055); this.tone(174.61, .23, .045, .13); }
    else if (cue === 'horn') { this.tone(349.23, .32, .045, 0, 'triangle'); this.tone(440, .32, .035, 0, 'triangle'); }
  }

  private register(source: AudioScheduledSourceNode, nodes: AudioNode[], end: number, bus: 'effects' | 'preview' = 'effects') {
    const voice: Voice = { source, nodes, bus }; this.voices.add(voice);
    source.onended = () => { for (const node of voice.nodes) node.disconnect(); this.voices.delete(voice); };
    source.stop(end);
  }
  private tone(frequency: number, duration: number, level: number, delay = 0, type: OscillatorType = 'sine', endFrequency = frequency, bus: 'effects' | 'preview' = 'effects') {
    if (!this.context || !this.effects || this.settings.volume === 0 || this.voices.size >= MAX_VOICES) return;
    const start = this.context.currentTime + delay;
    const oscillator = this.context.createOscillator(), gain = this.context.createGain();
    oscillator.type = type; oscillator.frequency.setValueAtTime(frequency, start);
    oscillator.frequency.exponentialRampToValueAtTime(endFrequency, start + duration);
    gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(level, start + .016);
    gain.gain.exponentialRampToValueAtTime(.0001, start + duration);
    oscillator.connect(gain); gain.connect(bus === 'preview' ? this.previewGain! : this.effects); oscillator.start(start);
    this.register(oscillator, [oscillator, gain], start + duration + .025, bus);
  }
  private noiseHit(duration: number, level: number, frequency: number) {
    if (!this.context || !this.effects || !this.noise || this.settings.volume === 0 || this.voices.size >= MAX_VOICES) return;
    const start = this.context.currentTime;
    const source = this.context.createBufferSource(), filter = this.context.createBiquadFilter(), gain = this.context.createGain();
    source.buffer = this.noise; filter.type = 'highpass'; filter.frequency.value = frequency;
    gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(level, start + .004);
    gain.gain.exponentialRampToValueAtTime(.0001, start + duration);
    source.connect(filter); filter.connect(gain); gain.connect(this.effects); source.start(start);
    this.register(source, [source, filter, gain], start + duration + .02);
  }
  private stopVoices(bus?: 'effects' | 'preview') {
    for (const voice of this.voices) {
      if (bus && voice.bus !== bus) continue;
      voice.source.onended = null;
      try { voice.source.stop(); } catch { /* It may already have ended. */ }
      for (const node of voice.nodes) node.disconnect();
      this.voices.delete(voice);
    }
  }
  async destroy() {
    if (this.destroyed) return;
    this.destroyed = true; this.muted = true; this.transitionRevision++;
    this.cancelFade(); this.cancelPreview();
    document.removeEventListener('visibilitychange', this.visibilityChanged);
    this.stopVoices();
    for (const source of this.loopSources) { try { source.stop(); } catch { /* Already stopped. */ } }
    for (const node of this.graph) node.disconnect();
    this.loopSources = []; this.graph = []; this.engines = []; this.musicNotes = [];
    this.analyser = undefined; this.waveform.fill(0);
    if (this.context && this.context.state !== 'closed') await this.context.close();
  }
}
