import { Simulation, type PersistedSimulation } from '../../../packages/sim/src/index';
import type { Snapshot, ServerMessage, JoinMessage, InputMessage, CommandMessage } from '../../../packages/protocol/src/index';

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
export const hasSave = () => { try { return !!localStorage.getItem(SAVE_KEY); } catch { return false; } };
export function connectSolo(name: string, callbacks: Callbacks, fresh = false): Connection {
  let restored: PersistedSimulation | undefined;
  if (!fresh) {
    try { const saved = localStorage.getItem(SAVE_KEY); if (saved) restored = JSON.parse(saved); }
    catch { callbacks.error('The previous save could not be read. Starting a new story.'); }
  }
  let sim: Simulation;
  try { sim = new Simulation('STORY', 'private', restored); }
  catch { sim = new Simulation('STORY', 'private'); callbacks.error('This save is incompatible. A new story has started.'); }
  const id = 'solo-player';
  if (sim.snapshot().players.some(p => p.id === id)) sim.connectPlayer(id); else sim.addPlayer(id, name);
  callbacks.welcome(id, 'On this device', true);
  callbacks.status('Story · saved on this device', true);
  callbacks.snapshot(sim.snapshot());
  let frames = 0;
  const save = () => {
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(sim.serialize())); }
    catch { callbacks.error('Browser storage is full or disabled. Keep this tab open to preserve progress.'); }
  };
  const timer = setInterval(() => {
    sim.step(0.05); callbacks.snapshot(sim.snapshot());
    if (++frames % 100 === 0) save();
  }, 50);
  return {
    input: input => { sim.input(id, input); },
    command: command => {
      const result = sim.command(id, command);
      if (!result.ok) callbacks.error(friendlyCode(result.code));
      callbacks.snapshot(sim.snapshot()); save();
    },
    close: () => { clearInterval(timer); sim.disconnectPlayer(id); save(); },
  };
}
export function connectOnline(join: JoinMessage, callbacks: Callbacks): Connection {
  let socket: WebSocket | undefined;
  let stopped = false, reconnectTimer = 0, failures = 0;
  let joined = false, stale = false, lastSnapshotAt = 0;
  let currentJoin = { ...join };
  const configured = import.meta.env.VITE_SERVER_URL as string | undefined;
  const url = configured || `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`;
  const send = (value: unknown) => { if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(value)); };
  const statusText = () => `${currentJoin.mode === 'private' ? 'Private crew' : 'City sandbox'} · ${currentJoin.room || 'connecting'}`;
  const freshnessTimer = window.setInterval(() => {
    if (joined && !stopped && !stale && Date.now() - lastSnapshotAt > 2000) {
      stale = true; callbacks.status('Waiting for fresh city state · controls paused', false);
    }
  }, 500);
  const start = () => {
    if (stopped) return;
    callbacks.status(failures ? 'Reconnecting to your room…' : 'Connecting to the city…', false);
    try { socket = new WebSocket(url); } catch { callbacks.error('Online rooms are unavailable in this copy. Return to the title to play Story on this device.'); return; }
    const attempt = socket;
    joined = false; stale = false;
    socket.addEventListener('open', () => { if (attempt === socket) send(currentJoin); });
    socket.addEventListener('message', event => {
      if (attempt !== socket) return;
      let message: ServerMessage;
      try { message = JSON.parse(String(event.data)); } catch { return; }
      if (message.type === 'welcome') {
        joined = true; stale = false; lastSnapshotAt = Date.now();
        failures = 0;
        currentJoin = { ...currentJoin, room: message.room, token: message.token };
        try { sessionStorage.setItem(`andolan.room.${message.room}`, message.token); } catch { /* Session remains usable. */ }
        callbacks.welcome(message.playerId, message.room, false);
        callbacks.status(`${message.mode === 'private' ? 'Private crew' : 'City sandbox'} · ${message.room}`, true);
        callbacks.snapshot(message.snapshot);
      } else if (message.type === 'snapshot') {
        lastSnapshotAt = Date.now();
        if (stale) { stale = false; callbacks.status(statusText(), true); }
        callbacks.snapshot(message);
      }
      else if (message.type === 'error') {
        callbacks.error(message.message);
        if (['ROOM_REQUIRED', 'ROOM_NOT_FOUND', 'ROOM_FULL', 'SERVER_FULL', 'INVALID_TOKEN'].includes(message.code)) {
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
        callbacks.error('The game server is unavailable. Return to the title to play Story on this device.'); return;
      }
      reconnectTimer = window.setTimeout(start, Math.min(8000, failures * 1500));
    });
  };
  if (join.room) {
    try { const token = sessionStorage.getItem(`andolan.room.${join.room}`); if (token) currentJoin.token = token; } catch { /* Optional persistence. */ }
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
    vehicle_moving: 'Stop the vehicle before getting out.', exit_blocked: 'Move to an open street before getting out.', vehicle_full: 'Every seat in this vehicle is occupied.', replay_unavailable: 'Replay is available after completion with one connected player.', moving: 'Stop the vehicle before getting out.', too_fast: 'Stop the vehicle before getting out.',
    wrong_stage: 'Follow the current objective first.', not_driver: 'Only the driver controls this vehicle.',
    blocked: 'There is no space to get out here. Move to an open street.', cooldown: 'Wait a moment and try again.',
    not_near_target: 'Move closer to the marked destination.', stale_revision: 'The crew has already moved on.',
  };
  return messages[code.toLowerCase()] || code.replaceAll('_', ' ').toLowerCase();
}
