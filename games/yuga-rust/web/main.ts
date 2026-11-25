import { makeScene } from './scene';

const data = JSON.parse(document.querySelector('#payload')!.textContent!);
const byId = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const canvas = byId<HTMLCanvasElement>('arena');
const begin = byId<HTMLButtonElement>('begin');
const menu = byId('menu'),
  play = byId('play'),
  overlay = byId('overlay');
const credits = byId<HTMLDialogElement>('credits');
const keyNames = ['LMB', 'Q', 'E', 'C', 'X'];
const keys = new Set<string>();
const decoder = new TextDecoder();
const PERIOD = 0.05;
let mode: 'loading' | 'ready' | 'playing' | 'paused' | 'complete' | 'error' = 'loading';
let scene: Awaited<ReturnType<typeof makeScene>>;
let wasm: any;
let current: any, previous: any;
let elapsed = 0,
  last = 0,
  lastEvent = 0;
let pointer: [number, number] | null = null;
let lastGround: [number, number] | null = null;
let lastAim: [number, number] = [0, 1];
let armedSlot: number | null = null;
let messageUntil = 0;
let ctx: AudioContext | undefined;
let output: GainNode | undefined;
let muted = false;
const voices = new Set<AudioBufferSourceNode>();
const sounds = new Map<string, AudioBuffer>();

function bytes(id: string) {
  const raw = atob(data.blobs[id]);
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}

function blob(id: string, type: string) {
  return URL.createObjectURL(new Blob([bytes(id)], { type }));
}

function readState() {
  const address = wasm.trial_snapshot();
  const size = wasm.trial_snapshot_len();
  return JSON.parse(decoder.decode(new Uint8Array(wasm.memory.buffer, address, size)));
}

function say(text: string) {
  byId('status').textContent = text;
  messageUntil = performance.now() + 1700;
}

function observe() {
  return {
    mode,
    state: current ? structuredClone(current) : null,
    renderer: scene?.diagnostics(),
    input: { armedSlot, pointer: pointer?.slice() ?? null, ground: lastGround?.slice() ?? null },
    period: PERIOD,
  };
}
Object.defineProperty(window, 'yugaProbe', { value: observe, writable: false });

function syncSound() {
  if (!ctx || !output) return;
  const audible = mode === 'playing' && !muted;
  output.gain.setValueAtTime(audible ? 1 : 0, ctx.currentTime);
  if (!audible) {
    for (const voice of voices) voice.stop();
    voices.clear();
  }
}

async function unlockSound() {
  try {
    if (!ctx) {
      ctx = new AudioContext();
      output = ctx.createGain();
      output.connect(ctx.destination);
      syncSound();
      const resume = ctx.state === 'suspended' ? ctx.resume() : Promise.resolve();
      await Promise.all([
        resume,
        ...Object.keys(data.blobs)
          .filter((k) => k.startsWith('audio/'))
          .map(async (id) => {
            sounds.set(id.slice(6), await ctx!.decodeAudioData(bytes(id).buffer));
          }),
      ]);
    } else if (ctx.state === 'suspended') {
      await ctx.resume();
    }
  } catch {
    byId('sound').textContent = 'Audio unavailable';
  }
}

function cue(id: string) {
  const buffer = sounds.get(id);
  if (mode !== 'playing' || muted || !ctx || !output || !buffer || ctx.state !== 'running') return;
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(output);
  source.onended = () => {
    voices.delete(source);
    source.disconnect();
  };
  voices.add(source);
  source.start();
}

function target(): [number, number] {
  if (pointer) {
    const ground = scene.ground(pointer[0], pointer[1]);
    if (ground && ground.every(Number.isFinite)) lastGround = ground;
  }
  if (lastGround) {
    const dx = lastGround[0] - current.actor.pos[0],
      dz = lastGround[1] - current.actor.pos[1];
    const length = Math.hypot(dx, dz);
    if (length > 0.05) lastAim = [dx / length, dz / length];
    return lastGround;
  }
  return [current.actor.pos[0] + lastAim[0] * 6, current.actor.pos[1] + lastAim[1] * 6];
}

function cast(slot: number) {
  if (mode !== 'playing') return false;
  const point = target();
  if (!wasm.trial_cast(slot, point[0], point[1], ...lastAim)) {
    const ability = current.abilities[slot];
    say(
      ability.cooldown_ticks
        ? ability.label + ' is cooling down'
        : current.active
          ? 'Finish the current invocation'
          : 'Choose a clear point within range',
    );
    return false;
  }
  current = readState();
  updateHud();
  return true;
}

const slots: HTMLButtonElement[] = [];
function arm(slot: number | null) {
  armedSlot = slot;
  slots.forEach((button, index) => button.setAttribute('aria-pressed', String(index === slot)));
  canvas.classList.toggle('targeting', slot !== null);
  if (slot === null) byId('status').textContent = '';
  else say(current.abilities[slot].label + ' · Click in the arena to cast. Esc to cancel.');
}

function buildHud() {
  for (const ability of current.abilities) {
    const b = document.createElement('button');
    b.className = 'slot';
    b.dataset.slot = String(ability.slot);
    b.title = ability.description + ' · Select, then click the arena.';
    b.setAttribute('aria-label', ability.label);
    b.setAttribute('aria-pressed', 'false');
    const key = document.createElement('kbd');
    key.textContent = keyNames[ability.slot];
    const name = document.createElement('span');
    name.textContent = ability.label;
    b.append(key, name);
    b.addEventListener('click', () => {
      if (mode !== 'playing') return;
      if (current.abilities[ability.slot].cooldown_ticks > 0) {
        arm(null);
        say(ability.label + ' is cooling down');
      } else {
        arm(armedSlot === ability.slot ? null : ability.slot);
      }
    });
    byId('actions').append(b);
    slots.push(b);
  }
}

function updateHud() {
  byId('objective').textContent = 'Moon guard · ' + current.defeated + ' / ' + current.enemies;
  const a = current.actor;
  byId('vital-text').textContent =
    Math.ceil(a.hp) + ' / ' + a.max_hp + (a.shield ? '   +' + Math.ceil(a.shield) + ' shield' : '');
  byId('hp').style.width = Math.max(0, (100 * a.hp) / a.max_hp) + '%';
  for (const ability of current.abilities) {
    const b = slots[ability.slot];
    if (!b) continue;
    b.classList.toggle('cool', ability.cooldown_ticks > 0);
    b.firstElementChild!.textContent =
      keyNames[ability.slot] +
      (ability.cooldown_ticks ? ' · ' + (ability.cooldown_ticks * PERIOD).toFixed(1) + 's' : '');
  }
  for (const ev of current.events) {
    if (ev.seq <= lastEvent) continue;
    lastEvent = ev.seq;
    if (ev.kind === 'release') cue(ev.id);
    if (ev.kind === 'impact') {
      if (ev.id === 'mountain_pulse') cue('mountain_impact');
      if (ev.receipts?.length)
        say(current.abilities[ev.slot].label + ' · ' + ev.receipts.length + ' affected');
    }
  }
}

function start(restart: boolean) {
  if (restart) wasm.trial_reset();
  current = readState();
  previous = current;
  lastEvent = 0;
  elapsed = 0;
  last = performance.now();
  keys.clear();
  pointer = null;
  lastGround = null;
  lastAim = [0, 1];
  arm(null);
  byId('status').textContent = '';
  byId('resume').hidden = false;
  byId('summary').textContent = '';
  menu.hidden = true;
  overlay.hidden = true;
  play.hidden = false;
  mode = 'playing';
  canvas.inert = play.inert = false;
  syncSound();
  updateHud();
  canvas.focus({ preventScroll: true });
  void unlockSound();
}

function pause(complete = false) {
  if (mode !== 'playing') return;
  arm(null);
  mode = complete ? 'complete' : 'paused';
  keys.clear();
  elapsed = 0;
  overlay.hidden = false;
  canvas.inert = play.inert = true;
  syncSound();
  byId('result').textContent = complete ? 'Avenue secured' : 'Practice paused';
  byId('summary').textContent = complete ? 'All three Moon guards are down.' : 'The drill clock is stopped.';
  byId('resume').hidden = complete;
  byId(complete ? 'reset' : 'resume').focus();
}

function resume() {
  if (mode !== 'paused') return;
  overlay.hidden = true;
  mode = 'playing';
  last = performance.now();
  elapsed = 0;
  previous = current;
  canvas.inert = play.inert = false;
  syncSound();
  canvas.focus();
  void unlockSound();
}

begin.addEventListener('click', () => {
  if (mode === 'ready') start(true);
});
byId('pause').onclick = () => pause();
byId('resume').onclick = resume;
byId('reset').onclick = () => start(true);
byId('back').onclick = () => {
  mode = 'ready';
  keys.clear();
  overlay.hidden = play.hidden = true;
  menu.hidden = false;
  canvas.inert = play.inert = true;
  syncSound();
  begin.focus();
};
byId('credits-button').onclick = () => credits.showModal();
byId('close-credits').onclick = () => credits.close();
byId('sound').onclick = () => {
  muted = !muted;
  syncSound();
  byId('sound').setAttribute('aria-pressed', String(muted));
  byId('sound').setAttribute('aria-label', muted ? 'Unmute sound' : 'Mute sound');
  byId('sound').textContent = muted ? 'Sound off' : 'Sound on';
  if (!muted) void unlockSound();
};
canvas.onpointermove = (e) => {
  if (mode === 'playing') {
    pointer = [e.clientX, e.clientY];
    target();
  }
};
canvas.onpointerdown = (e) => {
  if (mode === 'playing' && e.button === 0) {
    canvas.focus();
    pointer = [e.clientX, e.clientY];
    if (armedSlot === null) {
      cast(0);
    } else if (scene.ground(...pointer) === null) {
      say('Choose a point on the arena floor');
    } else if (cast(armedSlot)) {
      arm(null);
    }
  }
};
canvas.onpointerleave = () => {
  pointer = null;
};
overlay.addEventListener('keydown', (e) => {
  if (e.key !== 'Tab') return;
  const buttons = overlay.querySelectorAll<HTMLButtonElement>('button:not([hidden])');
  const first = buttons[0],
    last = buttons[buttons.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
});
window.addEventListener('keydown', (e) => {
  if (credits.open || e.altKey || e.ctrlKey || e.metaKey) return;
  if (e.code === 'Escape' && !e.repeat) {
    if (mode === 'playing') {
      e.preventDefault();
      if (armedSlot !== null) arm(null);
      else pause();
    } else if (mode === 'paused') {
      e.preventDefault();
      resume();
    }
    return;
  }
  if (mode !== 'playing') return;
  if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowLeft', 'ArrowDown', 'ArrowRight'].includes(e.code)) {
    e.preventDefault();
    keys.add(e.code);
  }
  const slot = ['', 'KeyQ', 'KeyE', 'KeyC', 'KeyX'].indexOf(e.code);
  if (slot > 0 && !e.repeat) {
    e.preventDefault();
    arm(null);
    cast(slot);
  }
});
window.addEventListener('keyup', (e) => keys.delete(e.code));
window.addEventListener('blur', () => {
  keys.clear();
  pause();
});
document.addEventListener('visibilitychange', () => {
  if (document.hidden) pause();
});

function frame(now: number) {
  if (mode === 'playing') {
    elapsed += Math.min((now - last) / 1000, 0.25);
    while (elapsed >= PERIOD && mode === 'playing') {
      previous = current;
      target();
      const down = (...k: string[]) => Number(k.some((code) => keys.has(code)));
      wasm.trial_tick(
        down('KeyA', 'ArrowLeft') - down('KeyD', 'ArrowRight'),
        down('KeyW', 'ArrowUp') - down('KeyS', 'ArrowDown'),
        ...lastAim,
      );
      current = readState();
      elapsed -= PERIOD;
      updateHud();
      if (current.enemies > 0 && current.defeated === current.enemies) pause(true);
    }
    if (armedSlot === null && now > messageUntil) byId('status').textContent = '';
  }
  if (!menu.hidden || !current) {
    last = now;
    requestAnimationFrame(frame);
    return;
  }
  scene.render(
    current,
    previous,
    mode === 'playing' ? elapsed / PERIOD : 1,
    mode === 'playing' ? Math.min(0.1, (now - last) / 1000) : 0,
  );
  last = now;
  requestAnimationFrame(frame);
}

async function init() {
  document.querySelector<HTMLElement>('.cover')!.style.backgroundImage =
    'url(' + blob('cover', 'image/png') + ')';
  byId('notices').textContent = data.notices;
  for (const [family, id] of [
    ['BC', 'display-font'],
    ['DM', 'body-font'],
  ]) {
    const font = new FontFace(family, bytes(id).buffer);
    document.fonts.add(await font.load());
  }
  const engine = await WebAssembly.instantiate(bytes('wasm'), {});
  wasm = engine.instance.exports;
  if (!wasm.trial_start()) throw new Error('The Rust rules or map could not be loaded.');
  current = readState();
  previous = current;
  const asset = (id: string) => blob(id, 'model/gltf-binary');
  scene = await makeScene(
    canvas,
    {
      hero: asset('hero'),
      soldier: asset('soldier'),
      architecture: asset('architecture'),
      nature: asset('nature'),
    },
    data.map,
    data.kit,
  );
  window.addEventListener('resize', () => scene.resize());
  scene.resize();
  buildHud();
  mode = 'ready';
  begin.textContent = 'Begin practice';
  begin.disabled = false;
  byId('loading').textContent = '';
  requestAnimationFrame(frame);
}
init().catch((e) => {
  mode = 'error';
  byId('loading').textContent =
    'Unable to start. Enable WebGL 2 and WebAssembly in your desktop browser, then reload.';
  begin.textContent = 'Arena unavailable';
  console.error(e);
});
