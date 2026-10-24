import { ArenaSimulation } from '../shared/simulation.js';
import type { Actor, ArenaCommand, ArenaInput, ArenaSnapshot, CommandResult, Team } from '../shared/types.js';

/** The transport owns identity, input expiry and scheduling; the authority owns
 * game state. Factories are trusted, synchronous, server-side integrations, not
 * modules selected by a public client or an environment-supplied import path. */
export interface ArenaAuthority {
  readonly room: string;
  readonly phase: ArenaSnapshot['phase'];
  readonly actors: ReadonlyMap<string, Actor>;
  addPlayer(id: string, name: string, heroId: string, team?: Team): Actor;
  removePlayer(id: string): void;
  releasePlayer(id: string): void;
  input(id: string, input: ArenaInput): boolean;
  clearInput(id: string): void;
  command(id: string, command: ArenaCommand): CommandResult;
  step(dt: number): void;
  snapshot(): ArenaSnapshot;
}

export interface ArenaAuthorityOptions {
  readonly room: string;
  readonly seed: number;
  readonly duration?: number;
  readonly botsPerTeam?: number;
}

export type ArenaAuthorityFactory = (options: Readonly<ArenaAuthorityOptions>) => ArenaAuthority;

/** Existing browser simulation remains the default, including its clamps and
 * bot, combat, economy and match rules. Native authority is an explicit opt-in. */
export const createPlanarAuthority: ArenaAuthorityFactory = options => new ArenaSimulation(options);

export function resolveAuthorityFactory(factory: unknown): ArenaAuthorityFactory {
  if (factory === undefined) return createPlanarAuthority;
  if (typeof factory !== 'function') throw new TypeError('authorityFactory must be a synchronous function');
  return factory as ArenaAuthorityFactory;
}

/** Check the integration boundary before a new room becomes visible. This is
 * not a sandbox or a substitute for the adapter's state/protocol tests. */
export function instantiateAuthority(factory: ArenaAuthorityFactory, options: ArenaAuthorityOptions): ArenaAuthority {
  if (!/^[A-Z0-9-]{3,16}$/.test(options.room) || !Number.isSafeInteger(options.seed) || options.seed < 0 || options.seed > 0xffffffff) {
    throw new TypeError('Arena authority requires a valid room and uint32 seed');
  }
  const authority: unknown = factory(Object.freeze({ ...options }));
  // Consume a mistakenly returned rejecting Promise before refusing the async
  // contract. Otherwise a bad plugin can also cause an unhandled rejection.
  if (authority instanceof Promise) void authority.catch(() => {});
  if (authority === null || typeof authority !== 'object' || 'then' in authority) {
    throw new TypeError('authorityFactory must return a synchronous authority object');
  }
  const value = authority as Record<string, unknown>;
  if (value.room !== options.room) throw new TypeError('Arena authority room must match the transport room');
  if (value.phase !== 'playing' && value.phase !== 'finished') throw new TypeError('Arena authority phase is invalid');
  if (!(value.actors instanceof Map)) throw new TypeError('Arena authority actors must be a Map');
  for (const method of ['addPlayer', 'removePlayer', 'releasePlayer', 'input', 'clearInput', 'command', 'step', 'snapshot'] as const) {
    if (typeof value[method] !== 'function') throw new TypeError(`Arena authority is missing ${method}()`);
  }
  return authority as ArenaAuthority;
}
