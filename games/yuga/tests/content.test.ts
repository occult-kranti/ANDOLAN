import { describe, expect, it } from 'vitest';
import { HEROES, heroById } from '../shared/heroes.js';
import { blocked, distance } from '../shared/map.js';
import { ArenaSimulation } from '../shared/simulation.js';
import type { AbilityDef, AbilityKind, Actor, HeroDef } from '../shared/types.js';

// Positioned unit fixtures isolate authored effects. They are not browser travel,
// human balance testing, or evidence that every combination is equally strong.
function setup(hero: HeroDef) {
  const sim = new ArenaSimulation({ botsPerTeam: 0, seed: 7301 });
  const caster = sim.addPlayer('caster', 'Caster', hero.id, 'sun');
  const ally = sim.addPlayer('ally', 'Ally', 'sita', 'sun');
  const enemy = sim.addPlayer('enemy', 'Enemy', 'duryodhana', 'moon');
  Object.assign(caster, { x: 0, z: 0, yaw: 0 });
  Object.assign(ally, { x: 0, z: 2 });
  Object.assign(enemy, { x: 0, z: 6 });
  return { sim, caster, ally, enemy };
}

function advance(sim: ArenaSimulation, seconds: number) {
  let remaining = seconds;
  while (remaining > 1e-8) { const dt = Math.min(.05, remaining); sim.step(dt); remaining -= dt; }
}

function neutralAim(sim: ArenaSimulation, caster: Actor, pitch = 0) {
  expect(sim.input(caster.id, { type: 'input', seq: caster.lastInputSeq + 1, moveX: 0, moveZ: 0, yaw: caster.yaw, pitch, fire: false, jump: false })).toBe(true);
}

function cast(sim: ArenaSimulation, caster: Actor, slot: 0 | 1 | 2, ability: AbilityDef) {
  const command = { type: 'command', action: 'ability', id: 'first-cast', slot } as const;
  expect(sim.command(caster.id, command)).toMatchObject({ ok: true, code: 'ABILITY_CAST' });
  expect(caster.cooldowns[slot]).toBe(ability.cooldown);
  expect(sim.snapshot().events.some(event => event.type === 'ability' && event.actorId === caster.id && event.label === ability.name)).toBe(true);
  const once = sim.snapshot();
  expect(sim.command(caster.id, command)).toMatchObject({ ok: true, code: 'ABILITY_CAST' });
  expect(sim.snapshot()).toEqual(once);
  expect(sim.command(caster.id, { ...command, id: 'cooldown-cast' })).toMatchObject({ ok: false, code: ability.mechanic ? 'CAST_IN_PROGRESS' : 'ABILITY_COOLDOWN' });
  expect(sim.snapshot()).toEqual(once);
}

describe('authored roster contract', () => {
  it('has fourteen unlocked, distinct kits within the agreed initial tuning bounds', () => {
    expect(HEROES).toHaveLength(14);
    expect(new Set(HEROES.map(hero => hero.id)).size).toBe(14);
    expect(new Set(HEROES.map(hero => hero.abilities.map(ability => ability.kind).join('/'))).size).toBe(14);
    for (const [role, count] of [['Vanguard', 5], ['Striker', 4], ['Keeper', 5]] as const) expect(HEROES.filter(hero => hero.role === role)).toHaveLength(count);
    const supported: AbilityKind[] = ['bolt', 'burst', 'dash', 'heal', 'ward', 'nova', 'slow', 'line', 'leap', 'summon', 'pull', 'cone'];
    expect([...new Set(HEROES.flatMap(hero => hero.abilities.map(ability => ability.kind)))].sort()).toEqual(supported.sort());
    for (const hero of HEROES) {
      for (const [value, min, max] of [[hero.health, 260, 420], [hero.speed, 6, 8], [hero.damage, 18, 32], [hero.fireInterval, .25, .65]]) {
        expect(value).toBeGreaterThanOrEqual(min!); expect(value).toBeLessThanOrEqual(max!);
      }
      expect(heroById(hero.id)).toBe(hero);
      expect(hero.abilities).toHaveLength(3);
      for (const colour of [hero.color, hero.accent]) expect(colour).toMatch(/^#[a-f\d]{6}$/i);
      for (const [slot, ability] of hero.abilities.entries()) {
        expect(ability.name.length).toBeGreaterThan(0); expect(ability.description.length).toBeGreaterThan(0);
        const cooldowns = [[7, 14], [10, 18], [35, 55]][slot]!;
        for (const [value, min, max] of [[ability.cooldown, ...cooldowns], [ability.power, 25, 100], [ability.range, 8, 28], [ability.radius, 3, 9], [ability.duration, 2, 6]]) {
          expect(value).toBeGreaterThanOrEqual(min!); expect(value).toBeLessThanOrEqual(max!);
        }
      }
    }
  });

  it('keeps the internal fallback separate from joining an unknown hero', () => {
    expect(heroById('unknown')).toBe(HEROES[0]);
    expect(() => new ArenaSimulation({ botsPerTeam: 0 }).addPlayer('human', 'Human', 'unknown')).toThrow('UNKNOWN_HERO');
  });

  it.each(HEROES)('$name basic fire uses its authored damage and ignores an allied body', hero => {
    const { sim, caster, ally, enemy } = setup(hero);
    expect(caster.health).toBe(hero.health);
    const enemyHealth = enemy.health, allyHealth = ally.health;
    expect(sim.input(caster.id, { type: 'input', seq: 0, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire: true, jump: false })).toBe(true);
    sim.step(.01);
    expect(sim.projectiles.find(projectile => projectile.owner === caster.id)?.damage).toBe(hero.damage);
    expect(caster.fireCooldown).toBe(hero.fireInterval);
    neutralAim(sim, caster);
    advance(sim, .3);
    expect(enemy.health).toBeCloseTo(enemyHealth - hero.damage);
    expect(ally.health).toBe(allyHealth);
  });
});

for (const hero of HEROES) {
  describe(`${hero.name}: effects promised by its three authored ability slots`, () => {
    for (const [index, ability] of hero.abilities.entries()) {
      const slot = index as 0 | 1 | 2;
      it(`${['Q', 'E', 'R'][slot]} ${ability.name} (${ability.kind}) works at match start with one receipt and cooldown`, () => {
        const { sim, caster, ally, enemy } = setup(hero);
        neutralAim(sim, caster);
        const allyHealth = ally.health;

        if (ability.mechanic === 'dawn-volley') {
          const before = enemy.health;
          cast(sim, caster, slot, ability);
          expect(caster.cast).toMatchObject({ mechanic: 'dawn-volley', phase: 'windup', releaseAt: 1 });
          advance(sim, .95);
          expect(sim.projectiles.filter(projectile => projectile.owner === caster.id)).toHaveLength(0);
          expect(enemy.health).toBe(before);
          advance(sim, .05);
          expect(sim.projectiles.filter(projectile => projectile.owner === caster.id)).toHaveLength(3);
          advance(sim, .15);
          expect(enemy.health).toBe(before - 3 * ability.power);
          expect(ally.health).toBe(allyHealth);
          expect(caster.cast).toBeUndefined();
          return;
        }

        if (ability.mechanic === 'mountain-descent') {
          Object.assign(enemy, { x: 0, z: 15 }); Object.assign(ally, { x: 1, z: 14, health: 100 });
          caster.health = caster.maxHealth - 70;
          const before = enemy.health;
          cast(sim, caster, slot, ability);
          advance(sim, .69);
          expect(caster.z).toBe(0); expect(enemy.health).toBe(before); expect(ally.health).toBe(100);
          advance(sim, .22);
          expect(caster.cast?.phase).toBe('travel'); expect(caster.y).toBeGreaterThan(0);
          expect(caster.z).toBeGreaterThan(0); expect(caster.z).toBeLessThan(14);
          expect(enemy.health).toBe(before); expect(ally.health).toBe(100);
          advance(sim, .25);
          expect(caster.cast).toBeUndefined(); expect(caster.y).toBe(0); expect(caster.z).toBeCloseTo(14);
          expect(enemy.health).toBe(before - ability.power); expect(ally.health).toBe(145);
          expect(caster.health).toBe(caster.maxHealth - 25);
          return;
        }

        if (ability.mechanic === 'mithila-sanctuary') {
          caster.health = 100; ally.health = 100; enemy.health = 100;
          cast(sim, caster, slot, ability);
          advance(sim, .79);
          expect(ally.shield).toBe(0); expect(ally.health).toBe(100);
          advance(sim, .01);
          expect(ally.shield).toBe(ability.power); expect(caster.shield).toBe(ability.power);
          const zone = sim.snapshot().zones.find(value => value.mechanic === 'mithila-sanctuary')!;
          expect(zone).toMatchObject({ x: 0, z: 0, radius: 8 });
          const healedAtRelease = ally.health;
          advance(sim, 1);
          expect(ally.health).toBeCloseTo(healedAtRelease + 9);
          Object.assign(ally, { x: 10, z: 0 }); const beforeLeaving = ally.health;
          advance(sim, .5);
          expect(ally.health).toBe(beforeLeaving);
          expect(enemy.health).toBe(100); expect(enemy.shield).toBe(0);
          advance(sim, 4.7);
          expect(sim.snapshot().zones.some(value => value.id === zone.id)).toBe(false);
          expect(caster.shield).toBe(0);
          return;
        }

        if (ability.kind === 'bolt' || ability.kind === 'line') {
          const before = enemy.health;
          cast(sim, caster, slot, ability);
          expect(sim.projectiles.filter(projectile => projectile.owner === caster.id)).toHaveLength(1);
          advance(sim, .3);
          expect(enemy.health).toBeCloseTo(before - ability.power);
          expect(ally.health).toBe(allyHealth);
          return;
        }

        if (ability.kind === 'burst' || ability.kind === 'cone' || ability.kind === 'nova') {
          enemy.z = ability.kind === 'nova' ? ability.radius - .5 : Math.min(6, ability.range - .5);
          const rear = sim.addPlayer('rear', 'Rear', 'rama', 'moon'); Object.assign(rear, { x: 0, z: -enemy.z });
          const far = sim.addPlayer('far', 'Far', 'rama', 'moon'); Object.assign(far, { x: 0, z: (ability.kind === 'nova' ? ability.radius : ability.range) + 1 });
          const before = enemy.health, rearBefore = rear.health, farBefore = far.health;
          cast(sim, caster, slot, ability);
          expect(enemy.health).toBeCloseTo(before - ability.power);
          expect(rear.health).toBeCloseTo(rearBefore - (ability.kind === 'nova' ? ability.power : 0));
          expect(far.health).toBe(farBefore); expect(ally.health).toBe(allyHealth);
          return;
        }

        if (ability.kind === 'heal' || ability.kind === 'ward') {
          const far = sim.addPlayer('far-ally', 'Far ally', 'rama', 'sun'); Object.assign(far, { x: ability.radius + 1, z: 0, health: 100 });
          caster.health = caster.maxHealth - 10; ally.health = 100; enemy.health = 100;
          cast(sim, caster, slot, ability);
          if (ability.kind === 'heal') {
            expect(caster.health).toBe(caster.maxHealth); expect(ally.health).toBe(100 + ability.power);
          } else {
            expect(caster.shield).toBe(ability.power); expect(ally.shield).toBe(ability.power);
            expect(caster.effects.ward).toBe(ability.duration);
            expect(enemy.shield).toBe(0); expect(far.shield).toBe(0);
            advance(sim, ability.duration + .1);
            expect(caster.shield).toBe(0); expect(ally.shield).toBe(0);
          }
          expect(enemy.health).toBe(100); expect(far.health).toBe(100);
          return;
        }

        if (ability.kind === 'dash' || ability.kind === 'leap') {
          Object.assign(enemy, { x: 0, z: ability.range + 1 });
          const enemyHealth = enemy.health;
          cast(sim, caster, slot, ability);
          expect(caster.x).toBeCloseTo(0); expect(caster.z).toBeCloseTo(ability.range);
          expect(blocked(caster.x, caster.z)).toBe(false);
          expect(caster.effects.haste).toBe(0);
          expect(enemy.health).toBe(enemyHealth);
          sim.step(.05);
          if (ability.kind === 'leap') expect(caster.y).toBeGreaterThan(0);
          else expect(caster.y).toBe(0);
          expect(ally.health).toBe(allyHealth);
          return;
        }

        if (ability.kind === 'slow') {
          Object.assign(enemy, { x: 0, z: ability.range });
          Object.assign(ally, { x: 0, z: ability.range });
          const before = enemy.health;
          cast(sim, caster, slot, ability);
          const zone = sim.snapshot().zones.find(value => value.owner === caster.id && value.kind === 'slow')!;
          expect(zone).toMatchObject({ x: 0, z: ability.range, radius: ability.radius, life: ability.duration });
          sim.step(.1);
          expect(enemy.health).toBeLessThan(before); expect(enemy.effects.slow).toBeGreaterThan(0);
          expect(ally.health).toBe(allyHealth); expect(ally.effects.slow).toBe(0);
          advance(sim, ability.duration + .1);
          expect(sim.snapshot().zones.some(value => value.id === zone.id)).toBe(false);
          return;
        }

        if (ability.kind === 'pull') {
          const centre = { x: 0, z: ability.range };
          Object.assign(enemy, { x: 3, z: ability.range });
          Object.assign(ally, { x: 2, z: ability.range });
          const before = distance(enemy, centre), enemyHealth = enemy.health, allyPosition = { x: ally.x, z: ally.z };
          cast(sim, caster, slot, ability);
          expect(distance(enemy, centre)).toBeLessThan(before);
          expect(enemy.health).toBe(enemyHealth - ability.power);
          expect(blocked(enemy.x, enemy.z)).toBe(false);
          expect({ x: ally.x, z: ally.z }).toEqual(allyPosition); expect(ally.health).toBe(allyHealth);
          return;
        }

        if (ability.kind === 'summon') {
          cast(sim, caster, slot, ability);
          const summons = sim.snapshot().actors.filter(actor => actor.kind === 'minion');
          expect(summons).toHaveLength(2);
          expect(summons.every(actor => actor.team === caster.team && distance(actor, caster) < 2)).toBe(true);
          const before = enemy.health;
          advance(sim, .5);
          expect(enemy.health).toBeLessThan(before);
          expect(sim.snapshot().events.some(event => event.type === 'hit' && summons.some(summon => summon.id === event.actorId))).toBe(true);
          expect(ally.health).toBe(allyHealth);
          return;
        }

        const unsupported: never = ability.kind;
        throw new Error(`Untested ability kind ${unsupported}`);
      });
    }
  });
}

const movements = HEROES.flatMap(hero => hero.abilities.flatMap((ability, slot) => ability.kind === 'dash' || ability.kind === 'leap' ? [{ hero, ability, slot: slot as 0 | 1 | 2 }] : []));
const aimedShots = HEROES.flatMap(hero => hero.abilities.flatMap((ability, slot) => ability.kind === 'bolt' || ability.kind === 'line' ? [{ hero, ability, slot: slot as 0 | 1 | 2 }] : []));
describe('movement and summon descriptions have enforceable physical limits', () => {
  it.each(aimedShots)('$hero.name / $ability.name is stopped by solid cover', ({ hero, ability, slot }) => {
    const { sim, caster, ally, enemy } = setup(hero);
    // This fixture isolates a building hit from the nearby lane tower's damage.
    for (const structure of sim.structures) if (structure.kind === 'tower') structure.health = 0;
    Object.assign(caster, { x: -32, z: -28, yaw: Math.PI / 2 });
    Object.assign(enemy, { x: -8, z: -28 });
    Object.assign(ally, { x: -32, z: -26 });
    const health = enemy.health;
    expect(distance(caster, enemy)).toBeLessThanOrEqual(ability.range);
    neutralAim(sim, caster);
    cast(sim, caster, slot, ability);
    advance(sim, (ability.windup ?? 0) + .75);
    expect(enemy.health).toBe(health);
    expect(sim.projectiles.some(projectile => projectile.owner === caster.id)).toBe(false);
  });

  it.each(movements)('$hero.name / $ability.name cannot pass through a solid building', ({ hero, ability, slot }) => {
    const { sim, caster } = setup(hero);
    Object.assign(caster, { x: -20, z: -45, yaw: 0 });
    neutralAim(sim, caster);
    cast(sim, caster, slot, ability);
    expect(caster.z).toBeGreaterThan(-45);
    expect(caster.z).toBeLessThan(-37);
    expect(caster.z + 45).toBeLessThan(ability.range);
    expect(blocked(caster.x, caster.z)).toBe(false);
  });

  it.each(HEROES.filter(hero => hero.abilities.some(ability => ability.kind === 'summon')))('$name sentinels expire at the promised nine seconds', hero => {
    const { sim, caster, enemy } = setup(hero);
    Object.assign(enemy, { x: 60, z: 0 });
    const slot = hero.abilities.findIndex(ability => ability.kind === 'summon') as 0 | 1 | 2;
    const ability = hero.abilities[slot];
    cast(sim, caster, slot, ability);
    const ids = sim.snapshot().actors.filter(actor => actor.kind === 'minion').map(actor => actor.id);
    expect(ability.description).toContain('9 seconds');
    advance(sim, 8.9);
    expect(ids.every(id => sim.actors.has(id))).toBe(true);
    advance(sim, .2);
    expect(ids.every(id => !sim.actors.has(id))).toBe(true);
  });
});
