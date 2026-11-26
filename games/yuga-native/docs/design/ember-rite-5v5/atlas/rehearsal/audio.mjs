/** Local rehearsal audio. Spatial inputs are authorized observations in atlas X/Z metres. */
export const REHEARSAL_CUE_RANGES = Object.freeze({
  footstep: 18, hanuman_leap: 20, kali_tandava: 25, kindle_start: 30, quench_start: 18
});

const CUE_DETAILS = Object.freeze({
  footstep:     {label: "Stone footstep",          priority: 0, interval: .10},
  hanuman_leap: {label: "Hanuman leap",            priority: 2, interval: .25},
  kali_tandava: {label: "Kali Tandava",            priority: 2, interval: .25},
  kindle_start: {label: "Kindle started",          priority: 2, interval: .09},
  quench_start: {label: "Quench started",          priority: 2, interval: .09},
  fold_start:   {label: "Fold opening",            priority: 1, interval: .09},
  fold:         {label: "Fold crossed",            priority: 1, interval: .09},
  drop:         {label: "Vessel dropped",          priority: 1, interval: .08},
  recover:      {label: "Vessel recovered",        priority: 1, interval: .08},
  cancel:       {label: "Hold interrupted",        priority: 2, interval: .09},
  handoff:      {label: "Defender took over",      priority: 2, interval: .15},
  kindled:      {label: "Ember kindled",           priority: 3, public: true},
  quenched:     {label: "Ember quenched",          priority: 3, public: true, terminal: true},
  burned:       {label: "Burn complete",           priority: 3, public: true, terminal: true},
  expired:      {label: "Approach expired",        priority: 3, public: true, terminal: true}
});

// The audio regression compares this portable playback score to the composer's score.json.
export const REHEARSAL_SCORE = Object.freeze({
  loopSeconds: 10, burnSeconds: 40, entryFadeSeconds: .012,
  stems: Object.freeze([
    {key: "drone", at: 0, pan: -.12}, {key: "low-drum", at: 10, pan: 0},
    {key: "hand-drum", at: 20, pan: .25}, {key: "reed", at: 30, pan: -.18}
  ].map(Object.freeze))
});
const {stems: SCORE_STEMS, loopSeconds: BAR_CYCLE} = REHEARSAL_SCORE;
export const REHEARSAL_DEFAULT_MIX = Object.freeze({
  enabled: false, master: .8, effects: 1, music: .65, mono: false, captions: true
});
const SURFACE_RATE = 24000;
const audioPoint = p => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
const audioClamp = (x, lo, hi) => Math.max(lo, Math.min(x, hi));

export function rehearsalCueInRange(type, metres) {
  // A legal diagonal may round a few machine epsilons above its radius.
  return Object.hasOwn(REHEARSAL_CUE_RANGES, type) && Number.isFinite(metres) &&
    metres >= 0 && metres - REHEARSAL_CUE_RANGES[type] <= 1e-10;
}

/** Length strictly inside a convex, counterclockwise registered polygon. Grazes are clear. */
function soundPathInside(a, b, ring) {
  let enter = 0, leave = 1;
  for (let i = 0; i < ring.length; i++) {
    const p = ring[i], q = ring[(i + 1) % ring.length];
    const dx = q[0] - p[0], dz = q[1] - p[1];
    const side = dx * (a[1] - p[1]) - dz * (a[0] - p[0]);
    const change = dx * (b[1] - a[1]) - dz * (b[0] - a[0]);
    const inset = 1e-5 * Math.hypot(dx, dz);
    if (Math.abs(change) < 1e-10) {
      if (side <= inset) return 0;
    } else {
      const t = (inset - side) / change;
      if (change > 0) enter = Math.max(enter, t);
      else leave = Math.min(leave, t);
      if (leave <= enter) return 0;
    }
  }
  return (leave - enter) * Math.hypot(b[0] - a[0], b[1] - a[1]);
}

function acousticCover(plan, listener, source) {
  // The architectural solids are walking-height sections. A single conservative
  // obstruction treatment avoids stacking filters through nested masonry.
  let strength = 0;
  for (const piece of plan.masonry) {
    if (soundPathInside(listener, source, piece.ring) >= .12) {
      strength = .75;
      break;
    }
  }
  for (const {xz: [x, z], size: [w, d], height} of plan.data.cover) {
    const left = x - w / 2, right = x + w / 2, bottom = z - d / 2, top = z + d / 2;
    if (soundPathInside(listener, source, [[left,bottom],[right,bottom],[right,top],[left,top]]) >= .12)
      strength = Math.max(strength, height >= 1.6 ? 1 : .32);
  }
  return strength;
}

function inAcousticStudy(p, ring) {
  return ring.every((q, i) => {
    const a = ring[(i + ring.length - 1) % ring.length];
    return (q[0] - a[0]) * (p[1] - a[1]) - (q[1] - a[1]) * (p[0] - a[0]) >= 0;
  });
}

function cueBearing(side, front) {
  const sides = ["ahead", "ahead right", "right", "behind right", "behind", "behind left", "left", "ahead left"];
  return sides[(Math.round(Math.atan2(side, front) * 4 / Math.PI) + 8) % 8];
}

/** Sound and captions consume this same decision. Coordinates never enter the caption. */
export function resolveRehearsalCue(plan, position, facing, event) {
  if (typeof event?.type !== "string" || !Object.hasOwn(CUE_DETAILS, event.type)) return null;
  const type = event.type, descriptor = CUE_DETAILS[type];
  let text = descriptor.label;
  const receipt = {
    type, text, priority: descriptor.priority, preview: event.preview === true, direction: "",
    distance: 0, gain: 1, pan: 0, cutoff: 11500, occluded: false, surface: null, room: null
  };
  if (descriptor.public) {
    if (type === "kindled" && (event.site === "a" || event.site === "b"))
      receipt.text = "Site " + event.site.toUpperCase() + " kindled";
    return receipt;
  }
  if (!plan || !audioPoint(position) || !audioPoint(facing)) return null;
  const heading = Math.hypot(...facing);
  if (!heading || !Number.isFinite(heading)) return null;
  if (!Object.hasOwn(REHEARSAL_CUE_RANGES, type)) {
    // The local operator hears release, pickup and their own fold. A fold link
    // never transports another event to a second map coordinate.
    if (event.at !== undefined && (!audioPoint(event.at) || Math.hypot(
      position[0] - event.at[0], position[1] - event.at[1]) > .05)) return null;
    return receipt;
  }
  if (!audioPoint(event.at)) return null;
  const dx = event.at[0] - position[0], dz = event.at[1] - position[1];
  const length = Math.hypot(dx, dz), range = REHEARSAL_CUE_RANGES[type];
  if (!rehearsalCueInRange(type, length)) return null;
  const ratio = Math.min(1, length / range);
  const side = length ? (dx / length) * (facing[1] / heading) - (dz / length) * (facing[0] / heading) : 0;
  const front = length ? (dx / length) * (facing[0] / heading) + (dz / length) * (facing[1] / heading) : 1;
  const obstruction = length > .12 ? acousticCover(plan, position, event.at) : 0;
  const surface = plan.surface(event.at).kind === "water" ? "water" : "stone";
  if (type === "footstep" && surface === "water") text = "Water footstep";
  const direction = length >= 1 ? cueBearing(side, front) : "";
  if (direction) text += " · " + direction;
  if (ratio >= .7) text += " · distant";
  if (obstruction > 0) text += " · muffled";
  const outline = plan.data.building.outline;
  const room = inAcousticStudy(position, outline) && inAcousticStudy(event.at, outline)
    ? plan.data.architecture.name : null;
  return {...receipt, text, direction, distance: length, surface, room, occluded: obstruction > 0,
    gain: (.22 + .78 * (1 - ratio) ** 1.6) * (1 - .45 * obstruction),
    pan: .9 * side * Math.min(1, length / 1.5),
    cutoff: (11200 - 4100 * ratio) * (1 - .72 * obstruction) * (1 + .22 * Math.min(0, front))};
}

// Original 24 kHz one-shots. Pitched membranes decay and fall in pitch, while the
// independent band-limited noise layer identifies friction, stone, water and air.
const SIGNAL_LENGTHS = {
  footstep: .23, water_step: .33, hanuman_leap: .39, kali_tandava: .62,
  kindle_start: .52, quench_start: .53, fold_start: .37, fold: .34, cancel: .21,
  drop: .32, recover: .34, handoff: .31, kindled: .54, quenched: .42, burned: .45, expired: .39
};

function createSignal(context, key, variation) {
  const duration = SIGNAL_LENGTHS[key], rate = SURFACE_RATE, tau = 2 * Math.PI;
  const samples = context.createBuffer(1, Math.ceil((duration + .025) * rate), rate);
  const out = samples.getChannelData(0);
  let seed = 0x73e3 + Object.keys(SIGNAL_LENGTHS).indexOf(key) * 1301 + 31 * variation;
  const pitch = [1, .955, 1.045][variation % 3];
  const random = () => {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return seed / 2147483648 - 1;
  };
  function note(start, length, freq, endFreq, amplitude, decay, overtone = .22) {
    const begin = Math.round(start * rate), count = Math.min(Math.round(length * rate), out.length - begin);
    for (let i = 0; i < count; i++) {
      const t = i / rate, phase = tau * (freq * t + (endFreq - freq) * t * t / (2 * length));
      const envelope = Math.min(1, t / .003, (count - 1 - i) / (rate * .017)) * Math.exp(-decay * t);
      out[begin + i] += amplitude * envelope * (Math.sin(phase) + overtone * Math.sin(2.13 * phase));
    }
  }
  function brush(start, length, amplitude, bright, attack, decay) {
    const begin = Math.round(start * rate), count = Math.min(Math.round(length * rate), out.length - begin);
    let smooth = 0, body = 0;
    for (let i = 0; i < count; i++) {
      const t = i / rate;
      smooth += bright * (random() - smooth);
      body += .035 * (smooth - body);
      const envelope = Math.min(1, t / attack, (count - 1 - i) / (rate * .02)) * Math.exp(-decay * t);
      out[begin + i] += amplitude * envelope * (smooth - body);
    }
  }
  switch (key) {
    case "footstep":
      note(0, .16, 153 * pitch, 77 * pitch, .85, 27, .35);
      brush(.006, .088, .56, .8, .002, 40);
      brush(.054, .125, .38, .46, .009, 28);
      break;
    case "water_step":
      note(0, .17, 112 * pitch, 73, .54, 23);
      brush(.002, .214, .99, .71, .017, 12);
      note(.065, .10, 540 * pitch, 1080, .13, 25, .01);
      note(.143, .105, 702 * pitch, 419, .11, 20, .02);
      brush(.11, .20, .53, .38, .014, 15);
      break;
    case "hanuman_leap":
      // Same takeoff signature as the native Maruti Udayana: a 140 Hz
      // membrane under rising air and the 177 Hz upward sweep.
      note(0, .22, 140, 78, .43, 14);
      note(0, .39, 177, 668, .35, 5);
      brush(0, .39, 1.1, .25, .12, 3);
      break;
    case "kali_tandava":
      for (const [start, f, a] of [[0, 156, .72],[.151, 198, .55],[.238, 115, .92]]) {
        note(start, .25, f, f * .60, a, 16, .42);
        brush(start, .065, .55, .82, .002, 47);
      }
      note(.246, .36, 584, 577, .23, 9, .53);
      break;
    case "kindle_start":
      brush(0, .178, .9, .90, .011, 15);
      note(.059, .19, 294, 355, .38, 12);
      note(.137, .36, 440, 441, .63, 8, .33);
      break;
    case "quench_start":
      note(0, .18, 588, 384, .54, 13);
      brush(.076, .36, .86, .70, .027, 7);
      note(.11, .31, 262, 224, .42, 8, .09);
      break;
    case "fold_start":
      note(0, .17, 310, 299, .53, 17);
      note(.085, .27, 462, 600, .52, 10);
      break;
    case "fold":
      note(0, .19, 616, 452, .47, 16);
      note(.075, .25, 312, 309, .77, 12, .34);
      break;
    case "cancel":
      note(0, .082, 612, 445, .43, 14);
      note(.079, .115, 287, 210, .44, 19);
      break;
    case "drop":
      note(0, .23, 162, 117, .85, 17, .4);
      note(.106, .17, 278, 260, .37, 19);
      break;
    case "recover":
      note(0, .19, 288, 297, .57, 12);
      note(.09, .23, 432, 430, .54, 12);
      break;
    case "handoff":
      note(0, .11, 294, 294, .56, 16);
      note(.112, .19, 392, 392, .60, 12);
      break;
    case "kindled":
      note(0, .29, 440, 440, .55, 9);
      note(.104, .40, 660, 660, .68, 7, .32);
      break;
    case "quenched":
      note(0, .19, 495, 465, .57, 14);
      note(.092, .30, 294, 280, .54, 9);
      break;
    case "burned":
      note(0, .21, 330, 335, .61, 13);
      note(.085, .34, 494, 495, .65, 8);
      break;
    case "expired":
      note(0, .18, 247, 239, .64, 15);
      note(.13, .24, 147, 142, .54, 11);
      break;
  }
  let peak = 0;
  for (const sample of out) peak = Math.max(peak, Math.abs(sample));
  const limit = key === "footstep" || key === "water_step" ? .30 : .36;
  for (let i = 0; i < out.length; i++) out[i] *= limit / peak;
  return samples;
}

function defaultAudioContext() {
  const Context = globalThis.AudioContext || globalThis.webkitAudioContext;
  return Context ? new Context({latencyHint: "interactive"}) : null;
}

function fromBase64(encoded) {
  const raw = globalThis.atob(encoded.slice(encoded.indexOf(",") + 1));
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return bytes.buffer;
}

function changeLevel(param, value, now, seconds = .012) {
  if (typeof param.cancelAndHoldAtTime === "function") param.cancelAndHoldAtTime(now);
  else {
    const old = param.value;
    param.cancelScheduledValues(now);
    param.setValueAtTime(old, now);
  }
  if (seconds) param.linearRampToValueAtTime(value, now + seconds);
  else param.setValueAtTime(value, now);
}

export class RehearsalAudio {
  constructor({onCaption = () => {}, onStatus = () => {}, createContext = defaultAudioContext,
    score = {}, now = () => performance.now() / 1000} = {}) {
    this.onCaption = onCaption;
    this.onStatus = onStatus;
    this.createContext = createContext;
    this.score = score && typeof score === "object" ? score : {};
    this.now = now;
    this.mix = {...REHEARSAL_DEFAULT_MIX};
    this.status = "off";
    this.context = null;
    this.graph = null;
    this.requested = false;
    this.disposed = false;
    this.assets = new Map();
    this.failedAssets = new Set();
    this.assetPromise = null;
    this.signals = new Map();
    this.voices = new Set();
    this.layers = new Map();
    this.ids = new Set();
    this.lastCue = new Map();
    this.stateChanged = () => this.contextState();
    this.reset();
  }

  listen(plan, position, facing) {
    if (this.plan && this.plan !== plan) this.reset();
    this.plan = plan;
    this.position = audioPoint(position) ? [...position] : null;
    this.facing = audioPoint(facing) ? [...facing] : null;
  }

  setStatus(value) {
    if (this.status === value) return;
    this.status = value;
    this.onStatus(value);
  }

  contextState() {
    if (this.disposed || !this.mix.enabled) return;
    if (!this.requested || this.context?.state !== "running") {
      this.stopAll();
      if (this.context || this.status !== "unavailable") this.setStatus("blocked");
      return;
    }
    this.setStatus("ready");
    this.loadAssets();
    this.refreshScore();
  }

  buildGraph(ctx) {
    const master = ctx.createGain(), effects = ctx.createGain(), music = ctx.createGain();
    const duck = ctx.createGain();
    effects.connect(master);
    duck.connect(music);
    music.connect(master);
    // Request actual speaker downmixing at the terminal bus for stereo result recordings too.
    master.channelCountMode = "explicit";
    master.channelInterpretation = "speakers";
    let limiter = null;
    if (ctx.createDynamicsCompressor) {
      limiter = ctx.createDynamicsCompressor();
      limiter.threshold.value = -5;
      limiter.knee.value = 5;
      limiter.ratio.value = 12;
      limiter.attack.value = .002;
      limiter.release.value = .10;
      master.connect(limiter);
      limiter.connect(ctx.destination);
    } else master.connect(ctx.destination);
    this.graph = {master, effects, music, duck, limiter};
    this.applyLevels(0);
  }

  applyLevels(ramp = .012) {
    if (!this.graph) return;
    const t = this.context.currentTime;
    const {enabled, master, effects, music, mono} = this.mix;
    this.graph.master.channelCount = mono ? 1 : 2;
    changeLevel(this.graph.master.gain, enabled ? master : 0, t, ramp);
    changeLevel(this.graph.effects.gain, effects, t, ramp);
    changeLevel(this.graph.music.gain, music, t, ramp);
    for (const voice of this.voices) {
      if (voice.panner) changeLevel(voice.panner.pan, mono ? 0 : voice.pan, t, ramp);
    }
  }

  /** Call directly from a user gesture. A denied attempt never queues old cue playback. */
  async unlock() {
    if (this.disposed || !this.mix.enabled) return false;
    let ctx = this.context;
    try {
      if (!ctx || ctx.state === "closed") {
        if (ctx) this.releaseContext();
        ctx = this.createContext();
        if (!ctx) {
          this.setStatus("unavailable");
          return false;
        }
        this.context = ctx;
        this.buildGraph(ctx);
        ctx.addEventListener("statechange", this.stateChanged);
      }
      this.requested = true;
      if (ctx.state !== "running") {
        // Some browsers leave resume pending until another gesture. Leave the
        // controls usable, and also observe a later real statechange.
        let timer;
        try {
          await Promise.race([ctx.resume(), new Promise(resolve => { timer = setTimeout(resolve, 800); })]);
        } finally { clearTimeout(timer); }
      }
    } catch {
      if (this.context && !this.graph) {
        this.releaseContext();
        ctx.close?.()?.catch(() => {});
      }
      if (this.mix.enabled) this.setStatus(this.context ? "blocked" : "unavailable");
      return false;
    }
    if (ctx !== this.context || this.disposed || !this.mix.enabled) return false;
    this.contextState();
    if (ctx.state !== "running") return false;
    return true;
  }

  loadAssets() {
    if (this.assetPromise || !this.context) return;
    const ctx = this.context;
    const keys = [...SCORE_STEMS.map(stem => stem.key), "quench", "expiry", "maruti-udayana"];
    this.assetPromise = Promise.all(keys.filter(k => typeof this.score[k] === "string").map(async key => {
      try {
        const buffer = await ctx.decodeAudioData(fromBase64(this.score[key]));
        if (ctx !== this.context || this.disposed) return;
        if (!buffer || !Number.isFinite(buffer.duration)) throw new Error("Invalid audio buffer");
        if (SCORE_STEMS.some(s => s.key === key) && Math.abs(buffer.duration - BAR_CYCLE) > .001)
          throw new Error("Unexpected stem duration");
        this.assets.set(key, buffer);
        this.refreshScore();
      } catch {
        if (ctx === this.context) this.failedAssets.add(key);
      }
    }));
  }

  whenAssetsReady() { return this.assetPromise || Promise.resolve(); }

  setMix(settings = {}) {
    for (const key of ["enabled", "mono", "captions"]) {
      if (typeof settings[key] === "boolean") this.mix[key] = settings[key];
    }
    for (const key of ["master", "effects", "music"]) {
      if (Number.isFinite(settings[key])) this.mix[key] = audioClamp(settings[key], 0, 1);
    }
    if (!this.mix.enabled) {
      this.requested = false;
      this.stopAll();
      this.setStatus("off");
    } else if (!this.mix.master) this.stopAll();
    else {
      if (!this.mix.effects) this.stopGroup("effects");
      if (!this.mix.music) {
        this.stopGroup("music");
        this.stopGroup("sting");
        this.origin = null;
      }
    }
    this.applyLevels();
    if (this.mix.enabled) this.contextState();
  }

  mayPlay(bus) {
    return !this.disposed && !this.paused && this.requested && this.mix.enabled && this.mix.master > 0 &&
      this.mix[bus] > 0 && this.context?.state === "running" && this.graph;
  }

  setPaused(value) {
    if (this.paused === Boolean(value)) return;
    this.paused = Boolean(value);
    if (this.paused) this.stopAll();
    else this.refreshScore();
  }

  reset() {
    this.stopAll();
    this.plan = null;
    this.position = null;
    this.facing = null;
    this.burn = null;
    this.origin = null;
    this.paused = false;
    this.final = null;
    this.ignited = false;
    this.stepIndex = 0;
    this.ids.clear();
    this.lastCue.clear();
  }

  emit(event) {
    if (this.disposed || this.paused || this.final) return null;
    const receipt = resolveRehearsalCue(this.plan, this.position, this.facing, event);
    if (!receipt) return null;
    const descriptor = CUE_DETAILS[receipt.type];
    const hasId = (typeof event.id === "string" && event.id.length > 0 && event.id.length <= 150) ||
      Number.isSafeInteger(event.id);
    if ((hasId && this.ids.has(event.id)) || (receipt.type === "kindled" && this.ignited)) return null;
    const clock = this.now(), rateKey = (receipt.preview ? "preview-" : "") + receipt.type;
    if (clock - (this.lastCue.get(rateKey) ?? -Infinity) < (descriptor.interval ?? 0)) return null;
    this.lastCue.set(rateKey, clock);
    if (hasId) {
      this.ids.add(event.id);
      if (this.ids.size > 128) this.ids.delete(this.ids.values().next().value);
    }
    if (descriptor.terminal) {
      this.final = receipt.type;
      this.syncBurn(null);
    }
    if (receipt.type === "kindled") this.ignited = true;
    if (["cancel", "fold", "kindled", "quenched", "burned", "expired"].includes(receipt.type)) {
      for (const voice of this.voices) {
        if (voice.localHold && !voice.retiring) this.stopVoice(voice, true);
      }
    }
    if (this.mix.captions) {
      const {type, text, direction, priority, preview} = receipt;
      this.onCaption({type, text, direction, priority, preview});
    }
    if (this.mayPlay("effects")) this.playEffect(receipt, event.localHold);
    if (descriptor.terminal && this.mayPlay("music")) {
      const key = {burned: "expiry", quenched: "quench"}[receipt.type];
      if (this.assets.has(key))
        this.startVoice(this.assets.get(key), {group: "sting", key, priority: 3});
    }
    return receipt;
  }

  playEffect(receipt, operatorHold) {
    const active = [...this.voices].filter(v => v.group === "effects");
    const cap = receipt.priority < 2 ? 4 : 6;
    if (active.length >= cap) {
      const least = active.reduce((low, v) => v.priority < low.priority ? v : low);
      if (least.priority > receipt.priority) return;
      this.stopVoice(least);
    }
    const key = receipt.type === "footstep" && receipt.surface === "water" ? "water_step" : receipt.type;
    const variation = receipt.type === "footstep" ? this.stepIndex++ % 3 : 0;
    let buffer = key === "hanuman_leap" ? this.assets.get("maruti-udayana") : null;
    if (!buffer) {
      const cacheKey = key + variation;
      if (!this.signals.has(cacheKey)) this.signals.set(cacheKey, createSignal(this.context, key, variation));
      buffer = this.signals.get(cacheKey);
    }
    // A defender can operate up to 1.5 m from the vessel that emits the pour.
    const localHold = !receipt.preview && (operatorHold === true || receipt.distance <= .05) &&
      ["kindle_start", "quench_start", "fold_start"].includes(receipt.type);
    this.startVoice(buffer, {...receipt, group: "effects", key, localHold});
    if (receipt.priority >= 2) this.duckFor(Math.min(.8, buffer.duration), receipt.priority);
  }

  duckFor(duration, priority) {
    const t = this.context.currentTime, fresh = t >= this.duckUntil;
    const target = priority === 3 ? .34 : .56;
    this.duckLevel = fresh ? target : Math.min(this.duckLevel, target);
    this.duckUntil = Math.max(this.duckUntil, t + duration);
    const param = this.graph.duck.gain;
    changeLevel(param, this.duckLevel, t, .012);
    param.setValueAtTime(this.duckLevel, this.duckUntil);
    param.linearRampToValueAtTime(1, this.duckUntil + .16);
  }

  /** Called by fixed simulation ticks. Only an explicit confirmed result plays a sting. */
  syncBurn(remainingSeconds, totalSeconds = REHEARSAL_SCORE.burnSeconds) {
    if (this.final || !Number.isFinite(remainingSeconds) || remainingSeconds <= 0 ||
        !Number.isFinite(totalSeconds) || totalSeconds <= 0 || remainingSeconds > totalSeconds) {
      this.burn = null;
      this.origin = null;
      this.stopGroup("music", true);
      return;
    }
    const elapsed = totalSeconds - remainingSeconds;
    // A discontinuity (seek, throttled simulation or rejoin) gets a new common
    // origin; ordinary 20 Hz delivery jitter never restarts an existing layer.
    if (this.origin !== null && (this.burn?.total !== totalSeconds || elapsed < this.burn.elapsed - 1e-7 ||
        Math.abs(this.context.currentTime - this.origin - elapsed) > .20)) {
      this.stopGroup("music", true);
      this.origin = null;
    }
    this.burn = {elapsed, total: totalSeconds};
    this.refreshScore();
  }

  refreshScore() {
    if (!this.burn || !this.mayPlay("music")) return;
    const now = this.context.currentTime, lead = .006;
    if (this.origin === null) this.origin = now + lead - this.burn.elapsed;
    const end = this.origin + this.burn.total;
    for (const stem of SCORE_STEMS) {
      if (stem.at > this.burn.elapsed || this.layers.has(stem.key) || !this.assets.has(stem.key)) continue;
      const when = Math.max(now + lead, this.origin + stem.at);
      if (when >= end) continue;
      const offset = ((when - this.origin) % BAR_CYCLE + BAR_CYCLE) % BAR_CYCLE;
      this.startVoice(this.assets.get(stem.key), {group: "music", key: stem.key, pan: stem.pan,
        when, offset, end, fade: REHEARSAL_SCORE.entryFadeSeconds});
    }
  }

  startVoice(buffer, {group, key, priority = 0, gain = 1, pan = 0, cutoff, room, fade = 0, localHold = false,
    when = this.context.currentTime, offset = 0, end} = {}) {
    const ctx = this.context;
    const source = ctx.createBufferSource();
    const level = ctx.createGain();
    const voice = {group, key, priority, source, level, pan, localHold, panner: null, nodes: [source, level],
      when, offset, retiring: false};
    try {
      source.buffer = buffer;
      let signal = source;
      if (cutoff && ctx.createBiquadFilter) {
        const lowpass = ctx.createBiquadFilter();
        voice.nodes.push(lowpass);
        lowpass.type = "lowpass";
        lowpass.Q.value = .707;
        lowpass.frequency.value = Math.min(cutoff, ctx.sampleRate * .48);
        signal.connect(lowpass);
        signal = lowpass;
      }
      signal.connect(level);
      if (room && ctx.createDelay) {
        // One quiet early reflection in the registered building's footprint.
        const delay = ctx.createDelay(.05), bounce = ctx.createGain();
        voice.nodes.push(delay, bounce);
        delay.delayTime.value = .021;
        bounce.gain.value = .12;
        signal.connect(delay);
        delay.connect(bounce);
        bounce.connect(level);
      }
      level.gain.setValueAtTime(fade ? 0 : gain, when);
      if (fade) level.gain.linearRampToValueAtTime(gain, when + fade);
      let output = level;
      // The musical stings already have a stereo image. Centre mono effects and
      // mono stems using equal-power panning relative to the listener's facing.
      if (group !== "sting" && ctx.createStereoPanner) {
        voice.panner = ctx.createStereoPanner();
        voice.nodes.push(voice.panner);
        voice.panner.pan.value = this.mix.mono ? 0 : pan;
        level.connect(voice.panner);
        output = voice.panner;
      }
      const bus = group === "music" ? this.graph.duck : group === "sting" ? this.graph.music : this.graph.effects;
      output.connect(bus);
      source.onended = () => this.finishVoice(voice);
      if (group === "music") {
        source.loop = true;
        source.loopStart = 0;
        source.loopEnd = BAR_CYCLE;
      }
      this.voices.add(voice);
      if (group === "music") this.layers.set(key, voice);
      source.start(when, offset);
      if (Number.isFinite(end)) {
        level.gain.setValueAtTime(gain, end);
        level.gain.linearRampToValueAtTime(0, end + .012);
        source.stop(end + .012);
      }
      return voice;
    } catch {
      this.stopVoice(voice);
      return null;
    }
  }

  finishVoice(voice) {
    voice.source.onended = null;
    for (const node of voice.nodes) node.disconnect();
    this.voices.delete(voice);
    if (this.layers.get(voice.key) === voice) this.layers.delete(voice.key);
  }

  stopVoice(voice, fade = false) {
    const t = this.context.currentTime;
    if (fade && t >= voice.when && !voice.retiring && this.context.state === "running") {
      voice.retiring = true;
      if (this.layers.get(voice.key) === voice) this.layers.delete(voice.key);
      changeLevel(voice.level.gain, 0, t, .012);
      voice.source.stop(t + .012);
      return;
    }
    try { voice.source.stop(t); } catch {}
    this.finishVoice(voice);
  }

  stopGroup(group, fade = false) {
    for (const voice of this.voices) {
      if (voice.group === group && !(fade && voice.retiring)) this.stopVoice(voice, fade);
    }
  }

  stopAll() {
    for (const voice of this.voices) this.stopVoice(voice);
    this.origin = null;
    this.duckUntil = -Infinity;
    this.duckLevel = 1;
    if (this.graph) changeLevel(this.graph.duck.gain, 1, this.context.currentTime, 0);
  }

  inspect() {
    const live = [...this.voices];
    return {status: this.status, paused: this.paused, mix: {...this.mix}, sourceCount: live.length,
      effects: live.filter(v => v.group === "effects").length,
      stings: live.filter(v => v.group === "sting").map(v => v.key),
      layers: [...this.layers.keys()], origin: this.origin, elapsed: this.burn?.elapsed ?? null,
      stemStarts: [...this.layers.values()].map(({key, when, offset}) => ({key, when, offset})),
      decoded: [...this.assets.keys()], failedAssets: [...this.failedAssets]};
  }

  releaseContext() {
    this.stopAll();
    this.context?.removeEventListener("statechange", this.stateChanged);
    if (this.graph) for (const node of Object.values(this.graph)) node?.disconnect();
    this.graph = null;
    this.context = null;
    this.assetPromise = null;
    this.assets.clear();
    this.failedAssets.clear();
    this.signals.clear();
  }

  dispose() {
    this.disposed = true;
    this.reset();
    const ctx = this.context;
    this.releaseContext();
    this.setStatus("off");
    if (ctx && ctx.state !== "closed") return ctx.close();
  }
}
