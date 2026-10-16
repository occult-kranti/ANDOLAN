import { Simulation, type PersistedSimulation } from '../../../packages/sim/src/index';
import { PROTOCOL_VERSION, type Snapshot, type ServerMessage, type JoinMessage, type InputMessage, type CommandMessage, type Gameplay } from '../../../packages/protocol/src/index';

export interface Connection {
  input(input: InputMessage): void;
  command(command: CommandMessage): void;
  reconnect?(): void;
  close(): void;
}
export interface Callbacks {
  snapshot(snapshot: Snapshot): void;
  welcome(id: string, room: string, local: boolean): void;
  status(message: string, connected: boolean): void;
  error(message: string): void;
}
const SAVE_KEY = 'andolan.story.v1';
const PRACTICE_KEY = 'andolan.city.v1';
export const hasSave = (gameplay: Gameplay = 'story') => { try { return !!localStorage.getItem(gameplay === 'story' ? SAVE_KEY : PRACTICE_KEY); } catch { return false; } };

/** A server address is public connection information, never an API key or room identity. */
export function validateServerUrl(value: string): string | undefined {
  try {
    const url = new URL(value.trim());
    if (url.username || url.password || url.hash || url.search) return;
    if (url.protocol === 'https:') url.protocol = 'wss:';
    if (url.protocol === 'http:') url.protocol = 'ws:';
    const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
    if (url.protocol !== 'wss:' && !(url.protocol === 'ws:' && loopback)) return;
    if (url.pathname === '/') url.pathname = '/ws';
    return url.toString();
  } catch { return; }
}
export function getServerUrl(): string | undefined {
  try { const stored = localStorage.getItem('andolan.server'); if (stored) return validateServerUrl(stored); } catch { /* Optional preference. */ }
  const configured = import.meta.env.VITE_SERVER_URL as string | undefined;
  if (configured) return validateServerUrl(configured);
  if (!['http:', 'https:'].includes(location.protocol) || location.hostname.endsWith('.github.io')) return;
  return `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`;
}
export function connectSolo(name: string, callbacks: Callbacks, fresh = false, gameplay: Gameplay = 'story'): Connection {
  const saveKey = gameplay === 'story' ? SAVE_KEY : PRACTICE_KEY;
  const room = gameplay === 'story' ? 'STORY' : 'CITY-PRACTICE';
  let restored: PersistedSimulation | undefined;
  if (!fresh) {
    try { const saved = localStorage.getItem(saveKey); if (saved) restored = JSON.parse(saved); }
    catch { callbacks.error('The previous save could not be read. Starting a new session.'); }
  }
  let sim: Simulation;
  try { sim = new Simulation(room, 'private', restored, gameplay); }
  catch { sim = new Simulation(room, 'private', undefined, gameplay); callbacks.error('This save is incompatible. A new session has started.'); }
  const id = 'solo-player';
  if (sim.snapshot().players.some(p => p.id === id)) sim.connectPlayer(id); else sim.addPlayer(id, name);
  callbacks.welcome(id, 'On this device', true);
  callbacks.status(gameplay === 'story' ? 'Story · saved on this device' : 'City practice · solo on this device', true);
  callbacks.snapshot(sim.snapshot());
  const stepMs = 50, maxCatchUpMs = 250, inputTimeoutMs = 350;
  let previousTime = performance.now(), lastInputTime = -Infinity, lastSaveTime = previousTime;
  let accumulator = 0, closed = false;
  const save = (now = performance.now()) => {
    try { localStorage.setItem(saveKey, JSON.stringify(sim.serialize())); }
    catch { callbacks.error('Browser storage is full or disabled. Keep this tab open to preserve progress.'); }
    lastSaveTime = now;
  };
  const advance = (now = performance.now()) => {
    if (closed) return;
    const elapsed = Math.max(0, now - previousTime); previousTime = now;
    if (document.hidden) { accumulator = 0; sim.clearInput(id); return; }
    // Discard excessive lag instead of replaying seconds of unattended movement.
    accumulator += Math.min(elapsed, maxCatchUpMs);
    if (now - lastInputTime > inputTimeoutMs) sim.clearInput(id);
    const steps = Math.floor((accumulator + 1e-6) / stepMs);
    accumulator = Math.max(0, accumulator - steps * stepMs);
    for (let i = 0; i < steps; i++) sim.step(stepMs / 1000);
    if (steps) callbacks.snapshot(sim.snapshot());
    if (now - lastSaveTime >= 5000) save(now);
  };
  const clearHeldInput = () => { sim.clearInput(id); lastInputTime = -Infinity; };
  const visibilityChanged = () => {
    previousTime = performance.now(); accumulator = 0; clearHeldInput();
    if (document.hidden) save(previousTime);
  };
  document.addEventListener('visibilitychange', visibilityChanged);
  window.addEventListener('blur', clearHeldInput);
  const timer = setInterval(advance, stepMs);
  return {
    input: input => {
      if (closed) return;
      const now = performance.now(); advance(now);
      // Finish elapsed time with the previous intent before accepting new controls.
      if (!document.hidden && sim.input(id, input)) lastInputTime = now;
    },
    command: command => {
      if (closed || document.hidden) return;
      advance();
      const result = sim.command(id, command);
      if (!result.ok) callbacks.error(friendlyCode(result.code));
      callbacks.snapshot(sim.snapshot()); save();
    },
    close: () => {
      if (closed) return;
      closed = true; clearInterval(timer);
      document.removeEventListener('visibilitychange', visibilityChanged);
      window.removeEventListener('blur', clearHeldInput);
      sim.disconnectPlayer(id); save();
    },
  };
}
export function connectOnline(join: JoinMessage, callbacks: Callbacks, serverUrl = getServerUrl()): Connection {
  let socket: WebSocket | undefined;
  let stopped = false, reconnectTimer = 0, failures = 0;
  let joined = false, stale = false, lastSnapshotAt = 0;
  let currentJoin = { ...join };
  const url = serverUrl || '';
  const identityKey = (room: string) => `andolan.room.${encodeURIComponent(url)}.${currentJoin.gameplay || 'story'}.${room}`;
  const send = (value: unknown) => { if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(value)); };
  const statusText = () => `${currentJoin.mode === 'private' ? 'Private crew' : 'Open city'} · ${currentJoin.room || 'connecting'}`;
  const freshnessTimer = window.setInterval(() => {
    if (joined && !stopped && !stale && Date.now() - lastSnapshotAt > 2000) {
      stale = true; callbacks.status('Waiting for fresh city state · controls paused', false);
    }
  }, 500);
  const start = () => {
    if (stopped) return;
    if (!url) { callbacks.status('Choose a game server to play online', false); callbacks.error('Add a server address in the lobby, or choose City practice to play on this device.'); return; }
    callbacks.status(failures ? 'Reconnecting to your room…' : 'Connecting to the city…', false);
    try { socket = new WebSocket(url); } catch { callbacks.error('This server address could not be opened. Return to the lobby to check it, or choose City practice.'); return; }
    const attempt = socket;
    joined = false; stale = false;
    socket.addEventListener('open', () => { if (attempt === socket) send(currentJoin); });
    socket.addEventListener('message', event => {
      if (attempt !== socket) return;
      let message: ServerMessage;
      try { message = JSON.parse(String(event.data)); } catch { return; }
      if (!message || typeof message !== 'object') return;
      const rejectVersion = () => {
        stopped = true; joined = false;
        const reason = 'This server needs the City Reform update. Ask its host to deploy the same version, or use City practice.';
        callbacks.status('Game server update required', false); callbacks.error(reason); socket?.close();
      };
      const compatible = (state: Snapshot | undefined) => state?.protocol === PROTOCOL_VERSION && !!state.contracts?.progression && Array.isArray(state.contracts?.recent) && !!state.city?.sectors && !!state.city?.votes && Array.isArray(state.city?.completedJobs);
      if (message.type === 'welcome') {
        if (message.protocol !== PROTOCOL_VERSION || !compatible(message.snapshot)) { rejectVersion(); return; }
        joined = true; stale = false; lastSnapshotAt = Date.now();
        failures = 0;
        currentJoin = { ...currentJoin, room: message.room, token: message.token };
        try { sessionStorage.setItem(identityKey(message.room), message.token); } catch { /* Session remains usable. */ }
        callbacks.welcome(message.playerId, message.room, false);
        callbacks.status(`${message.mode === 'private' ? 'Private crew' : 'Open city'} · ${message.room}`, true);
        callbacks.snapshot(message.snapshot);
      } else if (message.type === 'snapshot') {
        if (!joined) return;
        if (!compatible(message)) { rejectVersion(); return; }
        lastSnapshotAt = Date.now();
        if (stale) { stale = false; callbacks.status(statusText(), true); }
        callbacks.snapshot(message);
      }
      else if (message.type === 'error') {
        callbacks.error(message.message);
        if (['ROOM_REQUIRED', 'ROOM_NOT_FOUND', 'ROOM_FULL', 'SERVER_FULL', 'INVALID_TOKEN', 'GAMEPLAY_MISMATCH'].includes(message.code)) {
          stopped = true; callbacks.status(message.message, false); socket?.close();
        }
      }
      else if (message.type === 'result' && !message.ok) callbacks.error(friendlyCode(message.code));
    });
    socket.addEventListener('close', event => {
      if (attempt !== socket || stopped) return;
      joined = false;
      if (event.code === 4001) {
        stopped = true;
        callbacks.status('This identity is active in another tab', false);
        callbacks.error('Another tab resumed this crew member. Use Reconnect here only when you want to take control back.');
        return;
      }
      failures++;
      callbacks.status('Connection lost · your controls are paused', false);
      if (failures >= 4) {
        callbacks.error('The game server is unavailable. Your room identity is retained. Reconnect, change the server in the lobby, or try City practice.'); return;
      }
      reconnectTimer = window.setTimeout(start, Math.min(8000, failures * 1500));
    });
  };
  if (join.room) {
    try {
      let token = sessionStorage.getItem(identityKey(join.room));
      // Legacy identities belonged to this origin's Story server. Never send them to a new host.
      const sameOriginServer = url === `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`;
      if (!token && sameOriginServer && (!join.gameplay || join.gameplay === 'story')) token = sessionStorage.getItem(`andolan.room.${join.room}`);
      if (token) currentJoin.token = token;
    } catch { /* Optional persistence. */ }
  }
  start();
  return {
    input: input => { if (joined && !stale && !stopped) send(input); },
    command: command => { if (joined && !stale && !stopped) send(command); else callbacks.error('Wait for a fresh connection before taking an action.'); },
    reconnect: () => { stopped = true; clearTimeout(reconnectTimer); socket?.close(); failures = 0; stopped = false; start(); },
    close: () => { stopped = true; clearInterval(freshnessTimer); clearTimeout(reconnectTimer); socket?.close(); },
  };
}
export function friendlyCode(code: string) {
  const messages: Record<string, string> = {
    too_far: 'Move closer to interact.', occupied: 'That seat is already occupied.',
    vehicle_moving: 'Stop the vehicle before this action.', exit_blocked: 'Move to an open street before getting out.', vehicle_full: 'Every seat in this vehicle is occupied.', replay_unavailable: 'Replay is available after completion with one connected player.', moving: 'Stop the vehicle before this action.', too_fast: 'Stop the vehicle before this action.',
    wrong_stage: 'Follow the current objective first.', not_driver: 'Only the driver controls this vehicle.',
    blocked: 'There is no space to get out here. Move to an open street.', cooldown: 'Wait a moment and try again.',
    not_near_target: 'Move closer to the marked destination.', stale_revision: 'The crew has already moved on.',
    job_already_active: 'Your crew already has a job. Finish it or open City jobs to abandon it.',
    job_locked: 'Build more crew reputation to unlock this job.', job_cooldown: 'This job is getting its next load ready. Check the job board for the wait.',
    job_prerequisite: 'Complete The Nine O’Clock Correction to open the sector cases.', job_already_completed: 'This case is already filed. Choose another job or review the City ledger.',
    city_locked: 'Finish the media exposé and all four sector cases before the City Mandate.',
    city_already_decided: 'This city has already chosen its mandate. The decision remains in the City ledger.',
    city_job_active: 'Finish or abandon the current job before voting on the City Mandate.',
    city_invalid_choice: 'Choose one of the two routes shown in the City ledger.',
    job_owner_required: 'The crew member who accepted this job can abandon it. If they disconnect, contributing crew can recover it.',
    job_expired: 'Time ran out. No rewards were earned; choose a new run.', stale_job_stage: 'This step is already finished. Follow the new objective.',
    wrong_vehicle: 'Bring the vehicle required by this job.', cargo_missing: 'Load the supplies before continuing.',
    vehicle_required: 'Take the driver’s seat in the required vehicle.', wrong_bound_vehicle: 'Use the same vehicle that started this job.',
    driver_required: 'This step needs the driver of the required vehicle.', bound_vehicle_required: 'Use the same vehicle that started this job.',
    cargo_required: 'Collect the load before continuing.', cargo_too_far: 'Bring the loaded vehicle into this delivery area before unloading.',
    recovery_vehicle_occupied: 'Ask everyone to exit the stopped recovery car, then approach it on foot.',
    exit_vehicle_first: 'Step out of the vehicle to complete this handover.', no_active_job: 'Choose a job from City jobs first.',
    stale_job: 'That job has ended. Check your crew’s current objective.',
  };
  return messages[code.toLowerCase()] || code.replaceAll('_', ' ').toLowerCase();
}
