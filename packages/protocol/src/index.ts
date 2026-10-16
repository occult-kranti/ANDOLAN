export const PROTOCOL_VERSION = 1;
export type Mode = 'private' | 'public';
export type Vec2 = { x: number; z: number };
export interface PlayerSnapshot extends Vec2 {
  id: string; name: string; heading: number; vehicleId: string | null;
  seat: number | null; connected: boolean; color: number; signal: string | null;
  signalUntil: number; lastInputSeq: number;
}
export interface VehicleSnapshot extends Vec2 {
  id: string; kind: 'car' | 'van'; heading: number; speed: number;
  occupants: (string | null)[];
}
export interface DialogueLine { speaker: string; text: string }
export interface Choice { id: string; label: string; description: string }
export interface Metrics { trust: number; care: number; accountability: number }
export interface HistoryEntry { chapterId: string; stageId: string; choiceId: string; label: string }
export interface MissionSnapshot {
  chapterIndex: number; chapterId: string; title: string; stageIndex: number; stage: string;
  objective: string; targetId: string | null; trigger: string;
  dialogue: DialogueLine[]; documents: string[]; choices: Choice[]; votes: Record<string, string>;
  evidence: string[]; metrics: Metrics; history: HistoryEntry[];
  revision: number; complete: boolean; ending: { id: string; title: string; description: string } | null;
}
export interface Snapshot {
  type: 'snapshot'; protocol: number; tick: number; time: number; room: string; mode: Mode;
  players: PlayerSnapshot[]; vehicles: VehicleSnapshot[]; mission: MissionSnapshot;
}
export interface JoinMessage { type: 'join'; mode: Mode; room?: string; name: string; token?: string }
export interface InputMessage {
  type: 'input'; seq: number; moveX: number; moveZ: number; forward: number; turn: number; sprint?: boolean;
}
export type CommandAction = 'enter' | 'exit' | 'take_wheel' | 'interact' | 'choice' | 'signal' | 'replay';
export interface CommandMessage { type: 'command'; id: string; action: CommandAction; target?: string; value?: string }
export type ClientMessage = JoinMessage | InputMessage | CommandMessage | { type: 'ping'; time: number };
export interface WelcomeMessage { type: 'welcome'; protocol: number; playerId: string; token: string; room: string; mode: Mode; snapshot: Snapshot }
export interface ResultMessage { type: 'result'; commandId: string; ok: boolean; code: string }
export type ServerMessage = Snapshot | WelcomeMessage | ResultMessage | { type: 'error'; code: string; message: string; commandId?: string } | { type: 'pong'; time: number; serverTime: number };

const finiteAxis = (x: unknown) => typeof x === 'number' && Number.isFinite(x) && Math.abs(x) <= 1;
const string = (x: unknown, max: number) => typeof x === 'string' && x.length > 0 && x.length <= max;
const onlyKeys = (value: Record<string, unknown>, keys: string[]) => Object.keys(value).every(k => keys.includes(k));
/** Reject unknown fields so browser claims about position, rewards or identity never become authority. */
export function parseClientMessage(raw: unknown): ClientMessage | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const m = raw as Record<string, unknown>;
  if (m.type === 'join' && onlyKeys(m, ['type', 'mode', 'room', 'name', 'token']) && (m.mode === 'private' || m.mode === 'public') && string(m.name, 24) && (m.room === undefined || (typeof m.room === 'string' && /^[A-Z0-9-]{3,16}$/.test(m.room))) && (m.token === undefined || (typeof m.token === 'string' && /^[a-f0-9]{48}$/.test(m.token)))) return m as unknown as JoinMessage;
  if (m.type === 'input' && onlyKeys(m, ['type', 'seq', 'moveX', 'moveZ', 'forward', 'turn', 'sprint']) && Number.isSafeInteger(m.seq) && (m.seq as number) >= 0 && finiteAxis(m.moveX) && finiteAxis(m.moveZ) && finiteAxis(m.forward) && finiteAxis(m.turn) && (m.sprint === undefined || typeof m.sprint === 'boolean')) return m as unknown as InputMessage;
  if (m.type === 'command' && onlyKeys(m, ['type', 'id', 'action', 'target', 'value']) && typeof m.id === 'string' && /^[a-zA-Z0-9_-]{1,64}$/.test(m.id) && ['enter', 'exit', 'take_wheel', 'interact', 'choice', 'signal', 'replay'].includes(m.action as string) && (m.target === undefined || string(m.target, 64)) && (m.value === undefined || string(m.value, 64))) return m as unknown as CommandMessage;
  if (m.type === 'ping' && onlyKeys(m, ['type', 'time']) && typeof m.time === 'number' && Number.isFinite(m.time)) return m as unknown as ClientMessage;
  return null;
}
