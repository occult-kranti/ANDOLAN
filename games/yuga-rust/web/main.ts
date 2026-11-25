import { makeScene } from './scene';
import { PracticeCoach } from './practice-coach';

const data = JSON.parse(document.querySelector('#payload')!.textContent!);
const byId = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const canvas = byId<HTMLCanvasElement>('arena');
const begin = byId<HTMLButtonElement>('begin');
const menu = byId('menu'),
  play = byId('play'),
  overlay = byId('overlay');
const credits = byId<HTMLDialogElement>('credits');
const keyNames = ['LMB', 'Q', 'E', 'C', 'X'];
const practiceCoach = new PracticeCoach();
const keys = new Set<string>();
const decoder = new TextDecoder();
const PERIOD = 0.05;
let mode: 'loading' | 'ready' | 'playing' | 'paused' | 'complete' | 'error' = 'loading';
let scene: Awaited<ReturnType<typeof makeScene>>;
let wasm: any;
let current: any, previous: any;
let playMode: 'drill' | 'match' | 'online' = 'drill';
let socket: WebSocket | null = null;
let sequence = 0,
  frameReceived = 0,
  networkInterval = 100,
  nextAutoCast = 0;
let primaryHeld = false;
const heroSelect = byId<HTMLSelectElement>('hero');
const roomCode = byId<HTMLInputElement>('room-code');
const roomSize = byId<HTMLSelectElement>('room-size');
let room: { code: string; seat: number; team: string; count: number; capacity: number } | null = null;
let elapsed = 0,
  last = 0,
  lastEvent = 0;
let pointer: [number, number] | null = null;
let lastGround: [number, number] | null = null;
let lastAim: [number, number] = [0, 1];
let armedSlot: number | null = null;
const aimMessages = ['Clear landing · Click to cast Mountain Pulse', 'Out of range · Bring the landing point closer',
  'Cover blocks this landing · Choose open ground', 'Land on clear ground before casting', 'Aim at the arena floor'];
let mountainAim: { code: number; ground: [number, number] | null; actorX: number; actorZ: number; height: number; ready: boolean } | null = null;
let messageUntil = 0;
let ctx: AudioContext | undefined;
let output: GainNode | undefined;
let mixBus: GainNode | undefined;
let wasmModule: WebAssembly.Module;
let mixerKind = 'inactive';
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
    playMode,
    room: room && { ...room },
    state: current ? structuredClone(current) : null,
    renderer: scene?.diagnostics(),
    input: { armedSlot, pointer: pointer?.slice() ?? null, ground: lastGround?.slice() ?? null,
      mountainAim: mountainAim && structuredClone(mountainAim) },
    period: PERIOD,
    mixer: mixerKind,
    audio: { state: ctx?.state ?? null, muted, gain: output?.gain.value ?? null },
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

async function installMixer(context: AudioContext, bus: GainNode, master: GainNode) {
  const compressor = context.createDynamicsCompressor();
  compressor.threshold.value = -1;
  compressor.knee.value = 1;
  compressor.ratio.value = 20;
  bus.connect(compressor);
  compressor.connect(master);
  mixerKind = 'browser-compressor';
  if (!context.audioWorklet || !wasmModule) return;
  const url = URL.createObjectURL(new Blob([data.mixWorklet], { type: 'text/javascript' }));
  try {
    await context.audioWorklet.addModule(url);
    const node = new AudioWorkletNode(context, 'yuga-limiter', {
      numberOfInputs: 1,
      numberOfOutputs: 1,
      outputChannelCount: [2],
      processorOptions: { module: wasmModule },
    });
    node.port.onmessage = (event) => {
      if (event.data?.type !== 'ready' || mixerKind === 'openbf-rust') return;
      bus.disconnect(compressor);
      compressor.disconnect();
      bus.connect(node);
      node.connect(master);
      mixerKind = 'openbf-rust';
    };
    node.onprocessorerror = () => {
      if (mixerKind === 'openbf-rust') {
        bus.disconnect(node);
        node.disconnect();
        bus.connect(compressor);
        compressor.connect(master);
        mixerKind = 'browser-compressor';
      }
    };
  } catch {
    /* The compressor remains connected on browsers without worklet support. */
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function unlockSound() {
  try {
    if (!ctx) {
      ctx = new AudioContext();
      output = ctx.createGain();
      output.connect(ctx.destination);
      mixBus = ctx.createGain();
      void installMixer(ctx, mixBus, output);
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
  if (
    mode !== 'playing' ||
    muted ||
    !ctx ||
    !mixBus ||
    !buffer ||
    ctx.state !== 'running' ||
    voices.size >= 16
  )
    return;
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(mixBus);
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

// The local Wasm uses the same spatial rules as the room host. Cooldown and all
// hits still resolve on the authoritative tick when the pointer is committed.
function updateGroundAim() {
  if (mode !== 'playing' || armedSlot === null || current.abilities[armedSlot]?.id !== 'mountain_pulse') {
    if (mountainAim) scene.showGroundAim(null);
    mountainAim = null;
    return;
  }
  const at = pointer && scene.ground(...pointer);
  const actor = current.actor;
  const sameLanding = at && mountainAim?.ground && at[0] === mountainAim.ground[0] && at[1] === mountainAim.ground[1]
    && actor.pos[0] === mountainAim.actorX && actor.pos[1] === mountainAim.actorZ && actor.y === mountainAim.height;
  const code = !at ? 4 : sameLanding ? mountainAim!.code : wasm.trial_ground_aim(armedSlot, ...actor.pos, actor.y, ...at);
  const ready = code === 0 && !current.respawn_ticks && !current.active && !current.abilities[armedSlot].cooldown_ticks;
  if (!sameLanding || mountainAim?.ready !== ready) scene.showGroundAim(at, ready);
  mountainAim = { code, ground: at, actorX: actor.pos[0], actorZ: actor.pos[1], height: actor.y, ready };
  let message = aimMessages[code] ?? aimMessages[4];
  if (current.respawn_ticks) message = 'Wait for respawn';
  else if (current.active) message = 'Finish the current invocation';
  else if (current.abilities[armedSlot].cooldown_ticks) message = 'Mountain Pulse is cooling down';
  if (byId('status').textContent !== message) byId('status').textContent = message;
}

function cast(slot: number) {
  if (mode !== 'playing') return false;
  if (armedSlot === slot && current.abilities[slot].id === 'mountain_pulse') {
    updateGroundAim();
    if (!mountainAim?.ready) return false;
  }
  const point = target();
  if (playMode === 'online') {
    if (!socket || socket.readyState !== WebSocket.OPEN || current.respawn_ticks) return false;
    sendInput({ slot, ground: point, aim: lastAim });
    return true;
  }
  if (!wasm.trial_cast(slot, point[0], point[1], ...lastAim)) {
    const ability = current.abilities[slot];
    say(
      current.hero === 'rama' && (current.reload_ticks || (slot === 0 && current.ammo === 0))
        ? 'Reloading the bow'
        : ability.cooldown_ticks
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
  updateGroundAim();
}

function buildHud() {
  byId('actions').replaceChildren();
  slots.length = 0;
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
  const army = current.army;
  const hero = current.hero === 'rama' ? 'Rama' : 'Hanuman';
  byId('hero-name').textContent = hero;
  byId('overlay-label').textContent = hero + ' · Confluence';
  if (army && current.ruleset === 'hero_skirmish') {
    const seconds = Math.ceil(current.remaining_ticks * PERIOD);
    byId('location').textContent = current.solo_exploration
      ? 'Solo exploration'
      : (current.actor.team === 'moon' ? 'Moon' : 'Sun') + ' · Hero skirmish' +
        (playMode === 'online' && room ? ' · Seat ' + (room.seat + 1) + '/' + room.capacity : '');
    byId('objective').textContent = current.solo_exploration
      ? 'No AI opponents in this mode'
      : 'Sun ' + current.score.sun + '  /  Moon ' + current.score.moon + ' · First to ' + current.score.target;
    byId('match-detail').textContent = Math.floor(seconds / 60) + ':' +
      String(seconds % 60).padStart(2, '0') +
      (current.respawn_ticks ? '   ·   Respawn in ' + (current.respawn_ticks * PERIOD).toFixed(1) + 's' : '');
  } else if (army) {
    const seconds = Math.ceil(current.remaining_ticks * PERIOD);
    const moon = current.actor.team === 'moon';
    byId('location').textContent = (moon ? 'Moon' : 'Sun') + ' army · Wave ' + army.wave +
      (playMode === 'online' && room ? ' · Seat ' + (room.seat + 1) + '/' + room.capacity : '');
    byId('objective').textContent =
      'Sun core ' + Math.ceil(army.cores.sun) + '  /  Moon core ' + Math.ceil(army.cores.moon);
    byId('match-detail').textContent =
      Math.floor(seconds / 60) +
      ':' +
      String(seconds % 60).padStart(2, '0') +
      '   ·   ' +
      (moon ? army.moon_gold : army.gold) +
      ' gold' +
      (current.respawn_ticks ? '   ·   Respawn in ' + (current.respawn_ticks * PERIOD).toFixed(1) + 's' : '');
  } else {
    byId('location').textContent = 'Temple avenue';
    byId('objective').textContent = 'Moon guard · ' + current.defeated + ' / ' + current.enemies;
  }
  const a = current.actor;
  byId('vital-text').textContent =
    Math.ceil(a.hp) +
    ' / ' +
    a.max_hp +
    (a.shield ? '   +' + Math.ceil(a.shield) + ' shield' : '') +
    (current.hero === 'rama'
      ? '   ·   ' +
        (current.reload_ticks ? 'Reloading' : current.ammo + '/' + current.max_ammo + ' arrows · R')
      : '');
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
    if (playMode === 'drill') practiceCoach.observe(ev);
    if (current.hero === 'rama') {
      if (ev.kind === 'begin') cue('rama/draw_' + ev.id);
      if (ev.kind === 'release') cue('rama/release_' + ev.id);
      if (ev.kind === 'impact' && ev.receipts?.length) cue('rama/contact');
    } else if (ev.kind === 'release') cue(ev.id);
    if (ev.kind === 'impact') {
      if (ev.id === 'mountain_pulse') cue('mountain_impact');
      if (ev.receipts?.length)
        say(current.abilities[ev.slot].label + ' · ' + ev.receipts.length + ' affected');
    }
  }
  if (playMode === 'drill') byId('match-detail').textContent = practiceCoach.hint(keyNames);
}

function start(restart: boolean, networkState?: any) {
  practiceCoach.reset();
  if (restart) wasm.trial_reset();
  current = networkState || readState();
  buildHud();
  primaryHeld = false;
  nextAutoCast = 0;
  lastAim = [0, current.actor.team === 'moon' ? -1 : 1];
  previous = current;
  lastEvent = 0;
  elapsed = 0;
  last = performance.now();
  keys.clear();
  pointer = null;
  lastGround = null;
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
  if (mode !== 'playing' && !(complete && mode === 'paused')) return;
  primaryHeld = false;
  arm(null);
  if (playMode === 'online' && !complete) sendInput(undefined, false, true);
  mode = complete ? 'complete' : 'paused';
  keys.clear();
  elapsed = 0;
  overlay.hidden = false;
  canvas.inert = play.inert = true;
  syncSound();
  const playingArmy = !!current.army;
  byId('result').textContent = complete
    ? playingArmy
      ? current.winner === 'draw'
        ? 'Match drawn'
        : current.winner === current.actor.team
          ? 'Victory'
          : 'Defeat'
      : 'Avenue secured'
    : playMode === 'online'
      ? 'Match menu'
      : playingArmy
        ? 'Match paused'
        : 'Practice paused';
  byId('summary').textContent = complete
    ? playingArmy
      ? current.ruleset === 'hero_skirmish'
        ? 'Final score · Sun ' + current.score.sun + ' / Moon ' + current.score.moon
        : 'Final cores · Sun ' +
          Math.ceil(current.army.cores.sun) +
          ' / Moon ' +
          Math.ceil(current.army.cores.moon)
      : 'All three Moon guards are down. ' + practiceCoach.score + ' demonstrated.'
    : playMode === 'online'
      ? 'The room continues while this menu is open.'
      : 'The simulation clock is stopped.';
  byId('reset').hidden = playMode === 'online';
  byId('reset').textContent = playingArmy ? 'Restart match' : 'Restart drill';
  byId('resume').hidden = complete;
  byId(complete ? (playMode === 'online' ? 'back' : 'reset') : 'resume').focus();
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

function startLocal(selection: number) {
  if (mode !== 'ready') return;
  leaveRoom();
  playMode = selection === 0 ? 'drill' : 'match';
  if (!wasm.trial_select(selection)) {
    byId('loading').textContent = 'Could not load match data.';
    return;
  }
  byId('reset').hidden = false;
  start(false);
}
begin.addEventListener('click', () => startLocal(0));
byId('match').onclick = () => startLocal(heroSelect.value === 'rama' ? 2 : 1);
byId('pause').onclick = () => pause();
byId('resume').onclick = resume;
byId('reset').onclick = () => start(true);
function title() {
  primaryHeld = false;
  mode = 'ready';
  keys.clear();
  overlay.hidden = play.hidden = true;
  menu.hidden = false;
  canvas.inert = play.inert = true;
  syncSound();
  begin.focus();
}
byId('back').onclick = () => {
  leaveRoom();
  title();
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
      primaryHeld = current.hero === 'rama';
      nextAutoCast = performance.now() + 400;
      cast(0);
    } else if (scene.ground(...pointer) === null) {
      say('Choose a point on the arena floor');
    } else if (cast(armedSlot)) {
      arm(null);
    }
  }
};
window.addEventListener('pointerup', () => {
  primaryHeld = false;
});
window.addEventListener('pointercancel', () => {
  primaryHeld = false;
});
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
  if (e.code === 'KeyR' && !e.repeat && current.hero === 'rama') {
    e.preventDefault();
    if (playMode === 'online') sendInput(undefined, true);
    else {
      wasm.trial_reload();
      current = readState();
      updateHud();
    }
    return;
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

function move() {
  const down = (...k: string[]) => Number(k.some((code) => keys.has(code)));
  const sign = current.actor.team === 'moon' ? -1 : 1;
  return [
    sign * (down('KeyA', 'ArrowLeft') - down('KeyD', 'ArrowRight')),
    sign * (down('KeyW', 'ArrowUp') - down('KeyS', 'ArrowDown')),
  ];
}

function frame(now: number) {
  if (mode === 'playing') {
    elapsed += Math.min((now - last) / 1000, 0.25);
    if (
      primaryHeld &&
      !current.active &&
      !current.reload_ticks &&
      !current.abilities[0].cooldown_ticks &&
      now >= nextAutoCast
    ) {
      nextAutoCast = now + 400;
      cast(0);
    }
    if (playMode === 'online') {
      if (elapsed >= PERIOD) {
        target();
        sendInput();
        elapsed %= PERIOD;
      }
    } else {
      while (elapsed >= PERIOD && mode === 'playing') {
        previous = current;
        target();
        wasm.trial_tick(...move(), ...lastAim);
        current = readState();
        elapsed -= PERIOD;
        updateHud();
        if (current.army ? current.winner : current.enemies > 0 && current.defeated === current.enemies)
          pause(true);
      }
    }
    if (armedSlot === null && now > messageUntil) byId('status').textContent = '';
    if (armedSlot !== null) updateGroundAim();
  }
  if (!menu.hidden || !current) {
    last = now;
    requestAnimationFrame(frame);
    return;
  }
  scene.render(
    current,
    previous,
    mode === 'playing'
      ? playMode === 'online'
        ? Math.min(1, (now - frameReceived) / networkInterval)
        : elapsed / PERIOD
      : 1,
    mode === 'playing' ? Math.min(0.1, (now - last) / 1000) : 0,
  );
  last = now;
  requestAnimationFrame(frame);
}

function roomMessage(message: string) {
  byId('room-status').textContent = message;
}
function enableRooms() {
  const supported = location.protocol === 'http:' || location.protocol === 'https:';
  for (const id of ['create-room', 'join-room'])
    byId<HTMLButtonElement>(id).disabled = !supported || !!socket;
  byId('cancel-room').hidden = !socket;
  roomCode.readOnly = !!socket;
  roomSize.disabled = !supported || !!socket;
  heroSelect.disabled = !!socket;
  if (!supported) roomMessage('Open the game from its room server for online play.');
}
function leaveRoom() {
  const old = socket;
  socket = null;
  room = null;
  if (old) {
    old.onclose = null;
    old.onerror = null;
    old.onmessage = null;
    old.close();
  }
  roomMessage('');
  enableRooms();
}
function sendInput(castIntent?: any, reload = false, neutral = false) {
  if (!socket || socket.readyState !== WebSocket.OPEN || !current || socket.bufferedAmount > 32768) return;
  socket.send(
    JSON.stringify({
      type: 'input',
      seq: ++sequence,
      movement: neutral ? [0, 0] : move(),
      aim: lastAim,
      ...(castIntent ? { cast: castIntent } : {}),
      ...(reload ? { reload: true } : {}),
    }),
  );
}
function connect(create: boolean) {
  if (mode !== 'ready' || socket) return;
  const code = roomCode.value.trim().toUpperCase();
  if (!create && !code) {
    roomMessage('Enter the code from the room host.');
    roomCode.focus();
    return;
  }
  const url = new URL('/rooms', location.href);
  url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(url);
  socket = ws;
  enableRooms();
  sequence = 0;
  roomMessage('Connecting…');
  ws.onopen = () =>
    ws.send(
      JSON.stringify({
        type: create ? 'create' : 'join',
        hero: heroSelect.value,
        ...(create ? { teamSize: Number(roomSize.value) } : { code }),
      }),
    );
  function closed(reason: string) {
    if (socket !== ws) return;
    const wasPlaying = playMode === 'online' && mode !== 'ready';
    const finished = wasPlaying && mode === 'complete';
    leaveRoom();
    if (wasPlaying && !finished) title();
    roomMessage(reason);
  }
  ws.onerror = () => closed('Could not reach the room server. Open its game URL and try again.');
  ws.onclose = () => closed('Room closed. Create or join another match.');
  ws.onmessage = (event) => {
    let message;
    try {
      message = JSON.parse(event.data);
    } catch {
      closed('Invalid server reply.');
      return;
    }
    if (message.type === 'lobby') {
      const team = message.team ?? (message.seat % 2 ? 'moon' : 'sun');
      const capacity = message.capacity ?? 2, count = message.count ?? 1;
      room = { code: message.code, seat: message.seat, team, count, capacity };
      roomCode.value = message.code;
      const teamLabel = team === 'sun' ? 'Sun' : 'Moon';
      roomMessage('Share ' + room.code + ' · ' + count + '/' + capacity + ' players · ' +
        teamLabel + ' seat ' + (room.seat + 1) + '. ' +
        (count === capacity ? 'Starting match…' : 'Waiting for ' + (capacity - count) + ' more.'));
    } else if (message.type === 'state') {
      if (mode === 'ready') {
        playMode = 'online';
        if (room) room.count = room.capacity;
        frameReceived = performance.now();
        networkInterval = 100;
        start(false, message.state);
      } else if (playMode === 'online') {
        previous = current;
        current = message.state;
        const timestamp = performance.now();
        networkInterval = Math.max(50, Math.min(200, timestamp - frameReceived));
        frameReceived = timestamp;
        updateHud();
        if (message.accepted === false) say('Cast unavailable. Check range and cooldown.');
      }
      if (current.winner && mode !== 'complete') pause(true);
    } else if (message.type === 'error' && mode !== 'ready') {
      say(message.message || 'Input unavailable.');
    } else if (message.type === 'error' || message.type === 'closed') {
      closed(message.message || 'Room unavailable.');
    }
  };
}
byId('create-room').onclick = () => connect(true);
byId('join-room').onclick = () => connect(false);
byId('cancel-room').onclick = () => leaveRoom();

async function init() {
  document.querySelector<HTMLElement>('.cover')!.style.backgroundImage =
    'url(' + blob('cover', data.coverMime ?? 'image/png') + ')';
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
  wasmModule = engine.module;
  if (!wasm.trial_start()) throw new Error('The Rust rules or map could not be loaded.');
  current = readState();
  previous = current;
  const asset = (id: string) => blob(id, 'model/gltf-binary');
  scene = await makeScene(
    canvas,
    {
      hero: asset('hero'),
      rama: asset('rama'),
      vehicles: asset('vehicles'),
      soldier: asset('soldier'),
      architecture: asset('architecture'),
      nature: asset('nature'),
      mountain: data.blobs['mountain-rock'] ? asset('mountain-rock') : undefined,
    },
    data.map,
    data.kit,
    data.ramaKit,
  );
  window.addEventListener('resize', () => scene.resize());
  scene.resize();
  buildHud();
  mode = 'ready';
  begin.textContent = 'Hanuman practice';
  byId<HTMLButtonElement>('match').disabled = false;
  enableRooms();
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
