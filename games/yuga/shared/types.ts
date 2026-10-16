export type Team = 'sun' | 'moon';
export type CombatTeam = Team | 'neutral';
export type UnitArchetype = 'soldier' | 'city-watch' | 'minister' | 'king' | 'summon';
export type NeutralSpecies = 'yaksha' | 'naga' | 'sky-sentinel';
export type BuffKind = 'vigor' | 'haste' | 'ward';
export type Lane = 0 | 1 | 2;
export type AbilityKind = 'bolt' | 'burst' | 'dash' | 'heal' | 'ward' | 'nova' | 'slow' | 'line' | 'leap' | 'summon' | 'pull' | 'cone';
export interface Vec { x: number; z: number }
export type AbilityMechanic = 'dawn-volley' | 'mountain-descent' | 'mithila-sanctuary';
export interface CastState { slot: 0 | 1 | 2; mechanic: AbilityMechanic; phase: 'windup' | 'travel'; startedAt: number; releaseAt: number; endsAt: number; origin: Vec; target: Vec; yaw: number; pitch: number }
export interface AbilityDef { name: string; kind: AbilityKind; description: string; cooldown: number; power: number; range: number; radius: number; duration: number; color: string; mechanic?: AbilityMechanic; windup?: number }
export interface HeroDef { id: string; name: string; epithet: string; origin: string; role: 'Vanguard' | 'Striker' | 'Keeper'; description: string; silhouette: string; color: string; accent: string; health: number; speed: number; damage: number; fireInterval: number; projectileSpeed: number; weapon: 'bow' | 'mace' | 'staff' | 'chakram' | 'spear'; abilities: [AbilityDef, AbilityDef, AbilityDef]; difficulty: 1 | 2 | 3 }
export interface Actor extends Vec { id: string; kind: 'hero' | 'minion'; team: Team; heroId: string; name: string; bot: boolean; connected: boolean; lane: Lane; y: number; yaw: number; health: number; maxHealth: number; shield: number; respawn: number; cooldowns: number[]; fireCooldown: number; credits: number; level: number; kills: number; deaths: number; assists: number; damageDealt: number; upgrades: { power: number; vitality: number; tempo: number }; effects: { haste: number; slow: number; ward: number; vigor?: number }; lastInputSeq: number; cast?: CastState; minionRole?: 'escort' | 'siege' | 'summon'; unitArchetype?: UnitArchetype; summonerId?: string; expiresAt?: number }
export interface Neutral extends Vec { id: string; kind: 'neutral'; team: 'neutral'; species: NeutralSpecies; campId: string; name: string; y: number; yaw: number; health: number; maxHealth: number; state: 'idle' | 'aggro' | 'returning' | 'dead'; targetId: string | null; respawnAt: number; slow: number }
export interface GoldShard extends Vec { id: string; y: number; value: number; sourceId: string; originTeam: Team; createdAt: number; expiresAt: number }
export interface Structure extends Vec { id: string; kind: 'tower' | 'core'; team: Team; lane: Lane; health: number; maxHealth: number; shielded: boolean }
export interface Projectile extends Vec { id: string; owner: string; team: CombatTeam; y: number; vx: number; vy: number; vz: number; damage: number; radius: number; life: number; color: string; structureDamage?: number; canSecureGold?: boolean }
export interface Zone extends Vec { id: string; owner: string; team: Team; kind: AbilityKind; radius: number; life: number; duration: number; power: number; color: string; mechanic?: AbilityMechanic; yaw?: number }
export interface Pickup extends Vec { id: string; kind: 'vigor' | 'haste' | 'ward'; readyAt: number }
export interface GameEvent extends Vec { id: number; type: 'shot' | 'hit' | 'ability' | 'defeat' | 'tower' | 'core' | 'pickup' | 'upgrade' | 'victory' | 'gold' | 'camp' | 'buff'; team: CombatTeam; actorId: string; targetId?: string; label: string; color: string; time: number; amount?: number; reward?: 'secure' | 'steal'; buff?: BuffKind; sharedAwards?: { actorId: string; amount: number }[] }
export interface ArenaSnapshot { protocol: 2; room: string; tick: number; time: number; duration: number; phase: 'playing' | 'finished'; winner: Team | 'draw' | null; reason: string; actors: Actor[]; neutrals: Neutral[]; goldShards: GoldShard[]; structures: Structure[]; projectiles: Projectile[]; zones: Zone[]; pickups: Pickup[]; events: GameEvent[]; scores: Record<Team, number>; seed: number }
export interface ArenaInput { type: 'input'; seq: number; moveX: number; moveZ: number; yaw: number; pitch: number; fire: boolean; jump: boolean }
export type ArenaCommand = { type: 'command'; id: string; action: 'ability'; slot: 0 | 1 | 2 } | { type: 'command'; id: string; action: 'upgrade'; upgrade: 'power' | 'vitality' | 'tempo' };
export interface CommandResult { type: 'result'; id: string; ok: boolean; code: string }
export interface ArenaJoin { type: 'join'; protocol: 2; room?: string; heroId: string; name: string; token?: string }
export type ServerMessage = { type: 'welcome'; protocol: 2; id: string; room: string; token: string; snapshot: ArenaSnapshot } | { type: 'snapshot'; snapshot: ArenaSnapshot } | CommandResult | { type: 'error'; message: string };
export const YUGA_PROTOCOL = 2;
