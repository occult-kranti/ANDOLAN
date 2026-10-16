/** Bounded AI comparison, never a claim of human/ranked balance. Run: npx tsx games/yuga/tools/balance.ts */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import os from 'node:os';
import { ArenaSimulation, ARENA_RULES } from '../shared/simulation.js';
import { HEROES, heroById } from '../shared/heroes.js';
import { distance, GOLD_RULES, JUNGLE_CAMPS, SPAWNS } from '../shared/map.js';
import { YUGA_PROTOCOL } from '../shared/types.js';
import type { Actor, Lane, Team } from '../shared/types.js';

const seeds = [17, 20261016], lanes: Lane[] = [0, 1, 2], sides: Team[] = ['sun', 'moon'];
const benchmark = ['rama', 'bhima', 'sita'];
const snapshotActor = (actor: Actor) => ({ health: actor.health, shield: actor.shield, respawn: actor.respawn, x: actor.x, z: actor.z, cooldowns: [...actor.cooldowns] });
function run(heroId: string, lane: Lane, team: Team, seed: number) {
  const sim = new ArenaSimulation({ seed, botsPerTeam: 0 });
  let focal: Actor | undefined;
  for (const side of sides) for (const slot of lanes) {
    const id = side === team && slot === lane ? 'focal' : `${side}-${slot}`;
    const actor = sim.addPlayer(id, id, id === 'focal' ? heroId : benchmark[slot]!, side); sim.removePlayer(id);
    if (id === 'focal') focal = actor;
  }
  assert(focal); assert.equal(focal.lane, lane);
  let supportCastStarts = 0, observedTeamHealing = 0, observedTeamShieldAdded = 0, peakActors = sim.actors.size, peakGoldShards = 0, peakLivingNeutrals = 0;
  const start = performance.now();
  for (let tick = 0; tick < 9602 && sim.phase === 'playing'; tick++) {
    const before = new Map([...sim.actors.values()].filter(actor => actor.kind === 'hero').map(actor => [actor.id, snapshotActor(actor)]));
    sim.step(.05); peakActors = Math.max(peakActors, sim.actors.size);
    peakGoldShards = Math.max(peakGoldShards, sim.goldShards.length); peakLivingNeutrals = Math.max(peakLivingNeutrals, sim.neutrals.filter(neutral => neutral.health > 0).length);
    assert.equal(sim.neutrals.length, JUNGLE_CAMPS.length); assert(sim.goldShards.length <= GOLD_RULES.maxShards);
    assert(sim.actors.size <= ARENA_RULES.maxActors); assert(sim.projectiles.length <= ARENA_RULES.maxProjectiles);
    for (const actor of sim.actors.values()) {
      assert([actor.x, actor.y, actor.z, actor.health, actor.credits].every(Number.isFinite));
      if (actor.kind !== 'hero') continue;
      const previous = before.get(actor.id); if (!previous) continue;
      if (actor.id === 'focal') for (const slot of lanes) {
        const ability = heroById(heroId).abilities[slot];
        if (actor.cooldowns[slot]! > previous.cooldowns[slot]! + .1 && (ability.kind === 'heal' || ability.kind === 'ward' || ability.mechanic === 'mountain-descent')) supportCastStarts++;
      }
      if (actor.team === team && previous.health > 0 && actor.health > 0 && previous.respawn === 0 && actor.respawn === 0 && distance(actor, SPAWNS[team]) >= 12 && distance(previous, SPAWNS[team]) >= 12) {
        observedTeamHealing += Math.max(0, actor.health - previous.health);
        observedTeamShieldAdded += Math.max(0, actor.shield - previous.shield);
      }
    }
  }
  assert.equal(sim.phase, 'finished');
  const enemy = team === 'sun' ? 'moon' : 'sun';
  return { heroId, lane, team, seed, simulatedSeconds: sim.time, wallMs: performance.now() - start, winner: sim.winner, won: sim.winner === team, draw: sim.winner === 'draw', reason: sim.reason, damage: focal.damageDealt, kills: focal.kills, deaths: focal.deaths, assists: focal.assists, creditsEarned: focal.credits - 180, supportCastStarts, observedTeamHealingOutsideBase: observedTeamHealing, observedTeamShieldAddedOutsideBase: observedTeamShieldAdded, teamScore: sim.scores[team], opponentScore: sim.scores[enemy], towersDestroyed: sim.structures.filter(s => s.team === enemy && s.kind === 'tower' && s.health <= 0).length, damageToEnemyCore: 1400 - sim.structures.find(s => s.id === `${enemy}-core`)!.health, peakActors, peakGoldShards, peakLivingNeutrals };
}

const sources = ['games/yuga/shared/simulation.ts', 'games/yuga/shared/heroes.ts', 'games/yuga/shared/map.ts', 'games/yuga/shared/types.ts', 'games/yuga/tools/balance.ts'];
const sourceHashes = async () => Object.fromEntries(await Promise.all(sources.map(async path => [path, createHash('sha256').update(await readFile(path)).digest('hex')])));
const sourceSha256 = await sourceHashes();
const startedAt = new Date().toISOString(), all: ReturnType<typeof run>[] = [];
for (const hero of HEROES) {
  for (const seed of seeds) for (const lane of lanes) for (const team of sides) all.push(run(hero.id, lane, team, seed));
  console.log(`Finished ${hero.name}: ${seeds.length * lanes.length * sides.length} mirrored lane/seed cases`);
}
const round = (value: number) => Math.round(value * 100) / 100;
const summary = HEROES.map(hero => {
  const rows = all.filter(row => row.heroId === hero.id);
  const mean = (key: 'damage' | 'kills' | 'deaths' | 'assists' | 'creditsEarned' | 'supportCastStarts' | 'observedTeamHealingOutsideBase' | 'observedTeamShieldAddedOutsideBase' | 'towersDestroyed' | 'damageToEnemyCore') => round(rows.reduce((sum, row) => sum + row[key], 0) / rows.length);
  return { heroId: hero.id, role: hero.role, matches: rows.length, wins: rows.filter(row => row.won).length, draws: rows.filter(row => row.draw).length, meanDamage: mean('damage'), meanKills: mean('kills'), meanDeaths: mean('deaths'), meanAssists: mean('assists'), meanCreditsEarned: mean('creditsEarned'), meanSupportCastStarts: mean('supportCastStarts'), meanTeamHealingOutsideBase: mean('observedTeamHealingOutsideBase'), meanTeamShieldAddedOutsideBase: mean('observedTeamShieldAddedOutsideBase'), meanTowersDestroyed: mean('towersDestroyed'), meanEnemyCoreDamage: mean('damageToEnemyCore') };
});
const rankedWins = [...summary].sort((a, b) => b.wins - a.wins), rankedDamage = [...summary].sort((a, b) => b.meanDamage - a.meanDamage);
assert.deepEqual(await sourceHashes(), sourceSha256, 'Authoritative source changed during the matrix; rerun against a stable build.');
const report = { startedAt, completedAt: new Date().toISOString(), scope: 'Deterministic AI-only comparison with actual authoritative rules; not a human win-rate or ranked-balance estimate.', design: { focalHeroes: HEROES.map(hero => hero.id), seeds, lanes, mirroredTeams: sides, benchmark, matches: all.length, durationLimit: 480, fixedStepSeconds: .05, upgrades: 'Bots do not purchase upgrades. All actors start at base rank.' }, limitations: ['Two seeds and a fixed three-hero benchmark cannot establish matchup fairness or human skill ceilings.', 'Mirrored sides and all three lanes reduce position bias but do not eliminate bot targeting or kit-use bias.', 'Damage measures actual health removed from actors and structures; it excludes shield absorption.', 'Support cast starts count accepted cooldown starts, including interrupted windups; they do not measure effective support.', 'Observed team healing is positive net health change outside bases, excludes respawn, and can undercount concurrent damage. It is not attributed to the focal hero.', 'Observed shield additions outside bases include abilities and neutral pickups and exclude respawn. They are not attributed to the focal hero.', 'Object destruction and core damage are team outcomes, not individual credit. No automatic tuning is performed from this report.'], sourceSha256, machine: { node: process.version, platform: os.platform(), cpu: os.cpus()[0]?.model, availableParallelism: os.availableParallelism() }, disparitiesForReview: { mostWins: rankedWins[0], fewestWins: rankedWins.at(-1), mostDamage: rankedDamage[0], leastDamage: rankedDamage.at(-1), interpretation: 'Inspect these as bot-policy and tuning leads. Do not label heroes overpowered or fair from this small scripted matrix.' }, summary, matches: all };
await mkdir('games/yuga/docs/evidence', { recursive: true });
const prefix = process.env.YUGA_EVIDENCE_PREFIX ?? ''; assert(/^[a-z0-9-]*$/.test(prefix));
Object.assign(report, { protocol: YUGA_PROTOCOL, sourceStable: true, neutralCampCount: JUNGLE_CAMPS.length });
const filename = `games/yuga/docs/evidence/${prefix}balance-matrix.json`;
await writeFile(filename, JSON.stringify(report, null, 2));
console.log(filename);
