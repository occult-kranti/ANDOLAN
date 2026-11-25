// Compare the classic Rust combat lab against the actual TypeScript arena authority.
// Run with node games/yuga-rust/tools/test_classic_roster.mjs [--binary PATH] [--report PATH].
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { tsImport } from 'tsx/esm/api';

const crate = fileURLToPath(new URL('../', import.meta.url));
const simulationSource = '../../yuga/shared/simulation.ts';
const { ArenaSimulation } = await tsImport(simulationSource, import.meta.url);
const { HEROES } = await tsImport('../../yuga/shared/heroes.ts', import.meta.url);
const stepSeconds = 0.05;
const tolerance = 0.0001;

function fixture(hero) {
  const sim = new ArenaSimulation({ botsPerTeam: 0, seed: 7301, duration: 4800 });
  // Isolate role behavior from waves, towers, pickups and neutral camp respawns.
  sim.nextWave = Infinity;
  sim.structures = [];
  sim.neutrals = [];
  sim.pickups = [];
  const self = sim.addPlayer('self', 'Player', hero.id, 'sun');
  const ally = sim.addPlayer('ally', 'Ally', 'rama', 'sun');
  const enemy = sim.addPlayer('enemy', 'Enemy', 'ravana', 'moon');
  // The lab uses the classic middle lane for summons and respawns.
  for (const actor of [self, ally, enemy]) actor.lane = 1;
  Object.assign(self, { x: 0, z: 0, health: self.maxHealth - 70 });
  Object.assign(ally, { x: 1, z: 2, health: 230 });
  Object.assign(enemy, { x: 0, z: 3, health: 390 });
  return sim;
}

function submit(sim, command) {
  const actor = sim.actors.get(command.actor ?? 'self');
  const send = () =>
    assert.equal(
      sim.input(actor.id, {
        type: 'input',
        seq: actor.lastInputSeq + 1,
        moveX: command.movement?.[0] ?? 0,
        moveZ: command.movement?.[1] ?? 0,
        yaw: command.yaw ?? actor.yaw,
        pitch: command.pitch ?? 0,
        fire: command.fire ?? false,
        jump: command.jump ?? false
      }),
      true
    );
  let accepted = null;
  if (command.cast !== undefined) {
    send();
    accepted = sim.command(actor.id, {
      type: 'command',
      id: 'cast-' + actor.lastInputSeq,
      action: 'ability',
      slot: command.cast
    }).ok;
  }
  for (let t = 0; t < (command.ticks ?? 0); t++) {
    send();
    sim.step(stepSeconds);
  }
  return accepted;
}

function canonUnits(units) {
  const fixed = ['self', 'ally', 'enemy'].map((id) => {
    const actor = units.find((u) => u.id === id);
    assert.ok(actor, 'missing fixture actor ' + id);
    return actor;
  });
  const summons = units
    .filter((a) => !fixed.includes(a))
    .sort((a, b) => a.pos[0] - b.pos[0] || a.pos[1] - b.pos[1]);
  return [...fixed, ...summons].map((a, index) => ({
    id: index < 3 ? a.id : 'summon-' + (index - 2),
    kind: a.kind,
    team: a.team,
    pos: a.pos,
    y: a.y,
    hp: a.hp,
    shield: a.shield,
    slow: a.slow,
    ward: a.ward,
    cds: a.cds,
    fire_cd: a.fire_cd,
    respawn: a.respawn,
    expires_at: a.expires_at ?? null,
    cast: a.cast ?? null,
    max_hp: a.max_hp
  }));
}

function details(items, keys) {
  return items.map((v) => Object.fromEntries(keys.map((k) => [k, v[k] ?? null])));
}
const projectileFields = ['x', 'y', 'z', 'vx', 'vy', 'vz', 'damage', 'radius', 'life'];
const zoneFields = ['x', 'z', 'kind', 'radius', 'power', 'life', 'duration', 'mechanic'];

function observe(sim, accepted) {
  const s = sim.snapshot();
  return {
    tick: s.tick,
    accepted,
    units: canonUnits(
      s.actors.map((a) => ({
        id: a.id,
        kind: a.kind,
        team: a.team,
        pos: [a.x, a.z],
        y: a.y,
        hp: a.health,
        shield: a.shield,
        slow: a.effects.slow,
        ward: a.effects.ward,
        cds: a.cooldowns,
        fire_cd: a.fireCooldown,
        max_hp: a.maxHealth,
        expires_at: a.expiresAt,
        respawn: a.respawn,
        cast: a.cast
          ? {
              slot: a.cast.slot,
              mechanic: a.cast.mechanic,
              phase: a.cast.phase,
              origin: [a.cast.origin.x, a.cast.origin.z],
              target: [a.cast.target.x, a.cast.target.z],
              yaw: a.cast.yaw,
              pitch: a.cast.pitch,
              release: a.cast.releaseAt,
              end: a.cast.endsAt
            }
          : null
      }))
    ),
    projectiles: details(s.projectiles, projectileFields),
    zones: details(s.zones, zoneFields)
  };
}

const stationary = (ticks) => ({ ticks });
function abilityCommands(slot, ability) {
  // Aim ground circles slightly past the defender for measurable pull displacement.
  // Primary arrows and volleys use a level trajectory through the defender.
  const ground = ['pull', 'slow'].includes(ability.kind) || ability.mechanic === 'mountain-descent';
  const cast = { cast: slot, pitch: ground ? -0.25 : 0 };
  const checkpoints = [1, 4, 14, 16, 20, 23, 30, 61, 121];
  if (ability.kind === 'summon') checkpoints.push(181, 182);
  checkpoints.push(Math.ceil(ability.cooldown / stepSeconds) + 1);
  let previous = 0;
  return [
    cast,
    { ...cast },
    ...checkpoints.map((t) => {
      const c = stationary(t - previous);
      previous = t;
      return c;
    }),
    { ...cast }
  ];
}

function checkReference(caseName, hero, ability, frames) {
  // After the last timer check, each ability is cast again to exercise cooldown completion.
  const start = frames[0].units,
    end = (ability ? frames.at(-2) : frames.at(-1)).units;
  const playerFrames = frames.map((f) => f.units[0]);
  const enemyFrames = frames.map((f) => f.units[2]);
  if (caseName === 'primary') {
    assert.equal(frames[1].units[0].fire_cd, hero.fireInterval);
    assert.equal(end[2].hp, start[2].hp - hero.damage);
    assert.equal(end[1].hp, start[1].hp);
    return;
  }
  if (caseName === 'movement') {
    assert.ok(playerFrames.some((u) => u.y > 0) && end[0].y === 0, 'jump and land');
    assert.ok(end[0].pos[0] > 0 && end[0].pos[1] < 0, 'diagonal displacement');
    assert.ok(
      frames.some((f) => f.projectiles.length > 0),
      'missed primary travels in space'
    );
    return;
  }
  assert.equal(frames[1].accepted, true);
  assert.equal(frames[2].accepted, false);
  assert.equal(frames.at(-2).units[0].cds[hero.abilities.indexOf(ability)], 0);
  assert.equal(frames.at(-1).accepted, true);
  assert.equal(frames[1].units[0].cds[hero.abilities.indexOf(ability)], ability.cooldown);
  if (ability.mechanic === 'mithila-sanctuary') {
    assert.ok(frames.some((f) => f.units[1].shield > 0) && frames.some((f) => f.units[1].hp > start[1].hp));
  } else if (ability.kind === 'heal') {
    assert.ok(end[0].hp > start[0].hp && end[1].hp > start[1].hp);
  } else if (ability.kind === 'ward') {
    assert.ok(frames.some((f) => f.units[0].shield > 0 && f.units[1].shield > 0));
  } else if (['dash', 'leap'].includes(ability.kind) && !ability.mechanic) {
    assert.ok(end[0].pos[1] > start[0].pos[1]);
    if (ability.kind === 'leap') assert.ok(playerFrames.some((u) => u.y > 0));
  } else {
    assert.ok(
      enemyFrames.some((u) => u.hp < start[2].hp),
      'enemy takes damage'
    );
    if (ability.kind === 'pull')
      assert.ok(
        enemyFrames.some((u) => u.pos[1] !== start[2].pos[1]),
        'pull displacement'
      );
    if (ability.kind === 'slow')
      assert.ok(
        enemyFrames.some((u) => u.slow > 0),
        'slow applied'
      );
    if (ability.kind === 'summon')
      assert.ok(
        frames.some((f) => f.units.length === 5) && end.length === 3,
        'two sentinels spawn and expire'
      );
  }
}

// Exported for a source-fixture check without substituting an oracle for the Rust executable.
export function referenceCases() {
  assert.equal(HEROES.length, 14);
  assert.equal(new Set(HEROES.map((h) => h.id)).size, 14);
  const cases = [];
  for (const hero of HEROES) {
    const add = (name, commands, ability) => {
      const sim = fixture(hero);
      const frames = [observe(sim, null), ...commands.map((c) => observe(sim, submit(sim, c)))];
      try {
        checkReference(name, hero, ability, frames);
      } catch (err) {
        throw new Error(hero.id + '/' + name + ' TypeScript fixture: ' + err.message);
      }
      cases.push({ hero: hero.id, name, commands, frames });
    };
    hero.abilities.forEach((a, slot) => add(a.name, abilityCommands(slot, a), a));
    add('primary', [{ ticks: 1, fire: true }, { ticks: 4 }]);
    add('movement', [
      { ticks: 1, movement: [1, -1], jump: true, fire: true, yaw: 1.3, pitch: 0.2 },
      { ticks: 3, movement: [1, -1] },
      { ticks: 22 }
    ]);
  }
  return cases;
}

function compare(expected, actual, key) {
  if (typeof expected === 'number') {
    assert.ok(
      Number.isFinite(actual) && Math.abs(actual - expected) <= tolerance,
      key + ' Rust=' + JSON.stringify(actual) + ' TypeScript=' + expected
    );
    return;
  }
  if (expected && typeof expected === 'object') {
    assert.ok(actual && typeof actual === 'object', key + ' absent');
    if (Array.isArray(expected)) assert.equal(actual.length, expected.length, key + '.length');
    for (const [name, value] of Object.entries(expected)) compare(value, actual[name], key + '.' + name);
    return;
  }
  assert.equal(actual, expected, key);
}

async function run() {
  const { values } = parseArgs({ options: { binary: { type: 'string' }, report: { type: 'string' } } });
  let binary = values.binary;
  if (!binary) {
    const build = spawnSync('cargo', ['build', '--locked', '--bin', 'roster', '--message-format=json'], {
      cwd: crate,
      encoding: 'utf8'
    });
    if (build.error) throw build.error;
    assert.equal(build.status, 0, build.stderr);
    const artifacts = build.stdout
      .trim()
      .split('\n')
      .filter(Boolean)
      .map((line) => JSON.parse(line));
    binary = artifacts.find((record) => record.target?.name === 'roster' && record.executable)?.executable;
    assert.ok(binary, 'Cargo did not report a roster executable');
  }
  binary = path.resolve(binary);
  const cases = referenceCases(),
    failures = [];
  let snapshots = 0;
  for (const c of cases) {
    const result = spawnSync(binary, [c.hero], {
      input: c.commands.map((v) => JSON.stringify(v)).join('\n') + '\n',
      encoding: 'utf8',
      maxBuffer: 8 * 1024 * 1024
    });
    if (result.error) throw result.error;
    try {
      assert.equal(result.status, 0, result.stderr);
      const frames = result.stdout
        .trim()
        .split('\n')
        .filter(Boolean)
        .map((line) => JSON.parse(line));
      assert.equal(frames.length, c.frames.length, 'snapshot count');
      for (let i = 0; i < frames.length; i++) {
        const raw = frames[i],
          observed = {
            tick: raw.tick,
            accepted: raw.accepted,
            units: canonUnits(raw.units),
            projectiles: details(raw.projectiles, projectileFields),
            zones: details(raw.zones, zoneFields)
          };
        compare(c.frames[i], observed, c.hero + '/' + c.name + ' command ' + i + ' tick ' + c.frames[i].tick);
        snapshots++;
      }
    } catch (err) {
      failures.push(c.hero + '/' + c.name + ' ' + err.message);
    }
  }
  const report = {
    heroes: HEROES.length,
    abilityCases: 42,
    primaryCases: 14,
    movementCases: 14,
    cases: cases.length,
    passingCases: cases.length - failures.length,
    matchingSnapshots: snapshots,
    floatTolerance: tolerance,
    binarySha256: createHash('sha256')
      .update(await readFile(binary))
      .digest('hex'),
    typeScriptSha256: createHash('sha256')
      .update(await readFile(new URL(simulationSource, import.meta.url)))
      .digest('hex'),
    failures
  };
  if (values.report) await writeFile(values.report, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
  if (failures.length) process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await run();
