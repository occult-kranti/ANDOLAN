import type { ArenaCommand, ArenaInput, ArenaSnapshot, CommandResult, Team } from '../shared/types.js';
import type { ControlPointSnapshot } from './objective.js';

export type ReferenceExperiment = 'lane-economy' | 'control-point';
export interface ReferenceOptions { experiment: ReferenceExperiment; heroId: string; seed?: number }
export type ReferenceCommand = ArenaCommand | { type: 'command'; id: string; action: 'reload' };
export type ReferenceInput = ArenaInput;
export type ReferenceResult = CommandResult;
export interface WeaponSnapshot { ammo: number; capacity: number; reloadRemaining: number; reloadSeconds: number }
export interface WalletSnapshot { balance: number; earned: number; spent: number }
export interface EconomyReceipt { id: number; epoch: number; time: number; actorId: string; amount: number; kind: 'income' | 'spend'; balance: number }
export interface ReferenceSnapshot {
  epoch: number; experiment: ReferenceExperiment; localId: string; paused: boolean;
  phase: 'playing' | 'finished'; winner: Team | 'draw' | null; reason: string; timeLeft: number;
  arena: ArenaSnapshot; objective: ControlPointSnapshot | null;
  weapons: Record<string, WeaponSnapshot>; botIds: string[];
  economy: { wallets: Record<string, WalletSnapshot>; receipts: EconomyReceipt[] };
}
