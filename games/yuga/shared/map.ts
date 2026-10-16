import type { Lane, Team, Vec } from './types.js';
export const ARENA = { width: 140, depth: 170, spawnZ: 69, duration: 480, name: 'Sangam City', lanes: ['Ghat promenade', 'Temple avenue', 'Metro gardens'] } as const;
export const LANE_X = [-40, 0, 40] as const;
export const LANES: Record<Lane, Vec[]> = { 0: [{ x: 0, z: -66 }, { x: -40, z: -48 }, { x: -40, z: 48 }, { x: 0, z: 66 }], 1: [{ x: 0, z: -66 }, { x: 0, z: 66 }], 2: [{ x: 0, z: -66 }, { x: 40, z: -48 }, { x: 40, z: 48 }, { x: 0, z: 66 }] };
export interface Solid { x: number; z: number; w: number; d: number; height: number; style: 'sandstone' | 'modern' | 'garden' }
export const SOLIDS: Solid[] = [
  { x: -20, z: -28, w: 18, d: 18, height: 10, style: 'sandstone' }, { x: -20, z: 28, w: 18, d: 18, height: 12, style: 'sandstone' },
  { x: 20, z: -28, w: 18, d: 18, height: 15, style: 'modern' }, { x: 20, z: 28, w: 18, d: 18, height: 18, style: 'modern' },
  { x: -63, z: -18, w: 12, d: 20, height: 8, style: 'sandstone' }, { x: -63, z: 22, w: 12, d: 20, height: 9, style: 'sandstone' },
  { x: 63, z: -18, w: 12, d: 20, height: 20, style: 'modern' }, { x: 63, z: 22, w: 12, d: 20, height: 16, style: 'modern' },
];
export const SPAWNS: Record<Team, Vec> = { sun: { x: 0, z: -69 }, moon: { x: 0, z: 69 } };
export function blocked(x: number, z: number, radius = .65) { return Math.abs(x) > 68 - radius || Math.abs(z) > 82 - radius || SOLIDS.some(s => Math.abs(x - s.x) < s.w / 2 + radius && Math.abs(z - s.z) < s.d / 2 + radius); }
export function distance(a: Vec, b: Vec) { return Math.hypot(a.x - b.x, a.z - b.z); }
export function lineClear(a: Vec, b: Vec) { const d = distance(a,b); for (let i=1;i<Math.ceil(d/.8);i++) { const t=i/Math.ceil(d/.8); if(blocked(a.x+(b.x-a.x)*t,a.z+(b.z-a.z)*t,0)) return false; } return true; }
