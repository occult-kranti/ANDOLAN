import type { AbilityDef, AbilityKind, HeroDef } from './types.js';

// Original arena kits. Epic associations inform names/silhouettes, not claims about canonical powers.
function ability(kind: AbilityKind, name: string, description: string, cooldown: number, power: number, range: number, radius: number, duration: number, color: string): AbilityDef {
  return { kind, name, description, cooldown, power, range, radius, duration, color };
}

/** Every hero and every ability is available at the start; team choice is independent of epic allegiance. */
export const HEROES: HeroDef[] = [
  {
    id: 'rama', name: 'Rama', epithet: 'The Steady Bow', origin: 'Ramayana · original arena adaptation',
    role: 'Striker', description: 'A measured archer who keeps a clear firing lane and steps away from pressure. Strong aimed shots reward patient positioning.',
    silhouette: 'Tall curved bow, swept sash, narrow crest', color: '#3cb8df', accent: '#ffdf85',
    health: 300, speed: 7.2, damage: 27, fireInterval: 0.48, projectileSpeed: 46, weapon: 'bow', difficulty: 1,
    abilities: [
      ability('bolt', 'Steady Arrow', 'Fire a powerful aimed projectile. Cover blocks the shot.', 9, 54, 26, 3, 2, '#87e4ff'),
      ability('dash', 'Measured Step', 'Dash forward up to 10 metres. Walls stop the movement.', 12, 25, 10, 3, 2, '#ffe39a'),
      { ...ability('line', 'Dawn Volley', 'Brace in place for 1 second, then release three arrows along the locked firing angle. Each arrow can hit separately; cover blocks them.', 44, 32, 28, 3, 2, '#fff0b7'), mechanic: 'dawn-volley', windup: 1 },
    ],
  },
  {
    id: 'ravana', name: 'Ravana', epithet: 'The Tenfold Strategist', origin: 'Ramayana · original arena adaptation',
    role: 'Vanguard', description: 'A deliberate frontline controller. Gather enemies around a chosen point, then close the distance before releasing a nearby blast.',
    silhouette: 'Ten-faceted crown, broad mantle, ring blade', color: '#ad71e8', accent: '#fbc86d',
    health: 390, speed: 6.4, damage: 26, fireInterval: 0.52, projectileSpeed: 34, weapon: 'chakram', difficulty: 3,
    abilities: [
      ability('ward', 'Tenfold Guard', 'Grant a temporary shield to yourself and nearby allies.', 11, 48, 8, 4, 4, '#d1a0ff'),
      ability('pull', 'Commanding Circle', 'Damage enemies in the aimed circle and pull them toward its centre. Solid cover limits displacement.', 16, 35, 20, 5, 2, '#e1a6ff'),
      ability('nova', 'Crownfire', 'Blast enemies around you in a broad circle.', 48, 90, 8, 7, 2, '#ffce80'),
    ],
  },
  {
    id: 'arjuna', name: 'Arjuna', epithet: 'The Focused Archer', origin: 'Mahabharata · original arena adaptation',
    role: 'Striker', description: 'A quick archer who changes angles between volleys. High mobility comes with the roster’s smallest health reserve.',
    silhouette: 'Long bow, split shoulder scarf, high quiver', color: '#6599fa', accent: '#f5e7bd',
    health: 275, speed: 7.7, damage: 20, fireInterval: 0.35, projectileSpeed: 48, weapon: 'bow', difficulty: 2,
    abilities: [
      ability('burst', 'Converging Volley', 'Strike enemies in a forward fan within 18 metres.', 8, 38, 18, 5, 2, '#a5c8ff'),
      ability('dash', 'New Angle', 'Dash forward up to 12 metres to change your firing position.', 11, 25, 12, 3, 2, '#d5e3ff'),
      ability('line', 'One Clear Line', 'Fire a fast, heavy projectile along your aim.', 42, 88, 28, 3, 2, '#edf4ff'),
    ],
  },
  {
    id: 'duryodhana', name: 'Duryodhana', epithet: 'The Unyielding Mace', origin: 'Mahabharata · original arena adaptation',
    role: 'Vanguard', description: 'A durable close-pressure fighter. Hold a position with a small allied shield, then punish enemies who remain in front of you.',
    silhouette: 'Square shoulder guards, low crown, heavy mace', color: '#c58b48', accent: '#ffe2a5',
    health: 410, speed: 6.2, damage: 29, fireInterval: 0.55, projectileSpeed: 26, weapon: 'mace', difficulty: 1,
    abilities: [
      ability('burst', 'Mace Shock', 'Strike enemies in the short area in front of you.', 10, 48, 10, 5, 2, '#ffd18c'),
      ability('ward', 'Hold the Ground', 'Shield yourself and close allies for a brief defensive stand.', 15, 55, 8, 4, 4, '#ffe7bc'),
      ability('cone', 'Iron Crescent', 'Sweep a heavy wave through enemies in a broad forward cone.', 46, 92, 12, 8, 2, '#fff0cd'),
    ],
  },
  {
    id: 'hanuman', name: 'Hanuman', epithet: 'The Returning Leap', origin: 'Ramayana · original arena adaptation',
    role: 'Keeper', description: 'A mobile ally who leaps between skirmishes and restores nearby teammates. His final pulse rewards reaching a crowded frontline.',
    silhouette: 'Curved tail, flowing scarf, rounded mace', color: '#e79c61', accent: '#fff3bd',
    health: 350, speed: 7.6, damage: 23, fireInterval: 0.46, projectileSpeed: 29, weapon: 'mace', difficulty: 2,
    abilities: [
      ability('leap', 'Windward Leap', 'Leap forward up to 14 metres. Solid obstacles stop your advance.', 9, 28, 14, 3, 2, '#ffe1a6'),
      ability('heal', 'Bring Them Home', 'Restore health to yourself and allies close to you.', 14, 48, 8, 5, 3, '#a9f0c9'),
      { ...ability('nova', 'Mountain Pulse', 'Brace for 0.7 seconds, then leap to the aimed ground point. On landing, damage nearby enemies and heal nearby allies. Cover limits travel.', 45, 65, 14, 7, 2, '#fff0be'), mechanic: 'mountain-descent', windup: .7 },
    ],
  },
  {
    id: 'karna', name: 'Karna', epithet: 'The Sunlit Challenger', origin: 'Mahabharata · original arena adaptation',
    role: 'Striker', description: 'A slower marksman with heavy basic shots. A brief guard lets him hold an angle; his close-range final burst answers an enemy rush.',
    silhouette: 'Radiant shoulder discs, crescent bow, long sash', color: '#e5ac35', accent: '#fff5cb',
    health: 315, speed: 6.8, damage: 30, fireInterval: 0.55, projectileSpeed: 43, weapon: 'bow', difficulty: 2,
    abilities: [
      ability('line', 'Sunshaft', 'Fire a fast aimed projectile through a clear firing lane.', 11, 62, 27, 3, 2, '#ffe399'),
      ability('ward', 'Borrowed Dawn', 'Give yourself and nearby allies a short-lived shield.', 16, 42, 8, 4, 3, '#fff0b9'),
      ability('nova', 'Solar Reprisal', 'Strike enemies immediately around you with a bright area blast.', 50, 95, 8, 6, 2, '#fff4d5'),
    ],
  },
  {
    id: 'bhima', name: 'Bhima', epithet: 'The Forward Storm', origin: 'Mahabharata · original arena adaptation',
    role: 'Vanguard', description: 'A forceful close-range fighter who commits to a lane. Leap into reach, pressure the forward arc and save the broad blast for a contested objective.',
    silhouette: 'Broad torso, crossed straps, long-headed mace', color: '#62b88d', accent: '#eaf4bc',
    health: 400, speed: 6.4, damage: 28, fireInterval: 0.55, projectileSpeed: 27, weapon: 'mace', difficulty: 1,
    abilities: [
      ability('cone', 'Heavy Sweep', 'Strike enemies in a close forward cone.', 10, 52, 10, 5, 2, '#b2efba'),
      ability('leap', 'Closing Stride', 'Leap forward up to 12 metres. Walls stop the advance.', 15, 32, 12, 3, 2, '#d6f2bb'),
      ability('nova', 'Thunder at Your Feet', 'Damage enemies in a wide circle around you.', 48, 92, 8, 8, 2, '#efffcf'),
    ],
  },
  {
    id: 'meghnad', name: 'Meghnad', epithet: 'The Cloudline Archer', origin: 'Ramayana · Indrajit/Meghnad traditions; original arena kit',
    role: 'Striker', description: 'A swift disruptor who places slowing pressure before changing angle. Catch a lane in the cloud zone, then turn a flank into a forward burst.',
    silhouette: 'Forked crest, compact bow, layered cloud scarf', color: '#857ee0', accent: '#bce9ff',
    health: 285, speed: 7.8, damage: 22, fireInterval: 0.4, projectileSpeed: 42, weapon: 'bow', difficulty: 3,
    abilities: [
      ability('slow', 'Cloud Snare', 'Place an aimed zone that damages and slows enemies who remain inside.', 12, 28, 22, 4, 3, '#a8b2ff'),
      ability('dash', 'Storm Step', 'Dash forward up to 13 metres, stopping at solid cover.', 12, 25, 13, 3, 2, '#b5dcff'),
      ability('burst', 'Gathered Squall', 'Strike enemies in a long forward fan.', 43, 78, 22, 7, 2, '#dce7ff'),
    ],
  },
  {
    id: 'sita', name: 'Sita', epithet: 'The Patient Grove', origin: 'Ramayana · original protective arena adaptation',
    role: 'Keeper', description: 'A resilient protector. Restore nearby allies, shape the approach with a slowing zone and shield a gathered team.',
    silhouette: 'Leaf-tipped staff, long mantle, seed-shaped crest', color: '#69c8a2', accent: '#ffe3b1',
    health: 330, speed: 6.8, damage: 19, fireInterval: 0.45, projectileSpeed: 32, weapon: 'staff', difficulty: 1,
    abilities: [
      ability('heal', 'Grove Renewal', 'Restore health to yourself and allies within the nearby circle.', 10, 50, 8, 5, 3, '#b3f3d0'),
      ability('slow', 'Rooted Path', 'Place an aimed zone that damages and slows enemies crossing it.', 15, 25, 18, 5, 4, '#9be2b7'),
      { ...ability('ward', 'Shelter of Mithila', 'Prepare in place for 0.8 seconds, then raise a fixed sanctuary for 6 seconds. Nearby allies gain a shield; allies who remain inside steadily recover health.', 46, 70, 8, 8, 6, '#f1eab3'), mechanic: 'mithila-sanctuary', windup: .8 },
    ],
  },
  {
    id: 'draupadi', name: 'Draupadi', epithet: 'The Unbroken Voice', origin: 'Mahabharata · original protective arena adaptation',
    role: 'Keeper', description: 'A resolute guardian. Shield allies, gather approaching enemies into a clear target area and restore a team holding its ground.',
    silhouette: 'Five-point mantle clasp, flame staff, upright crown', color: '#d4759b', accent: '#ffe1a8',
    health: 340, speed: 6.5, damage: 20, fireInterval: 0.48, projectileSpeed: 33, weapon: 'staff', difficulty: 2,
    abilities: [
      ability('ward', 'Circle of Resolve', 'Give yourself and close allies a temporary shield.', 10, 46, 8, 5, 4, '#f1aed1'),
      ability('pull', 'Stand Accountable', 'Damage enemies in the aimed circle and pull them toward its centre; solid cover limits movement.', 17, 30, 19, 5, 2, '#ffd0df'),
      ability('heal', 'Unbroken Assembly', 'Restore a large amount of health to yourself and allies in a broad nearby circle.', 48, 95, 8, 8, 4, '#ffe5b8'),
    ],
  },
  {
    id: 'subhadra', name: 'Subhadra', epithet: 'The Rallying Standard', origin: 'Mahabharata · original commander arena adaptation',
    role: 'Keeper', description: 'A mobile field commander. An aimed opening shot and a small recovery circle support teammates; temporary allied sentinels reinforce a contested lane.',
    silhouette: 'Spear pennant, rounded shoulder guards, side braid', color: '#64bbc5', accent: '#ffe8a4',
    health: 315, speed: 7.2, damage: 22, fireInterval: 0.45, projectileSpeed: 38, weapon: 'spear', difficulty: 2,
    abilities: [
      ability('bolt', 'Signal Lance', 'Fire an aimed energy projectile toward the opposing line.', 9, 44, 24, 3, 2, '#a9edf1'),
      ability('heal', 'Rally Close', 'Restore health to yourself and allies close to your position.', 13, 42, 8, 4, 3, '#cff7d4'),
      ability('summon', 'Twin Standards', 'Call two temporary allied sentinels beside you for 9 seconds.', 48, 28, 10, 4, 3, '#ffebac'),
    ],
  },
  {
    id: 'hidimbi', name: 'Hidimbi', epithet: 'The Forest Sentinel', origin: 'Mahabharata · original forest-guardian arena adaptation',
    role: 'Vanguard', description: 'A guardian with a strong presence around objectives. Control an approach, protect close allies and reinforce the lane with temporary sentinels.',
    silhouette: 'Broad leaf mantle, braided crest, forked spear', color: '#7da96e', accent: '#f1d6a3',
    health: 375, speed: 6.8, damage: 24, fireInterval: 0.5, projectileSpeed: 31, weapon: 'spear', difficulty: 2,
    abilities: [
      ability('slow', 'Forest Boundary', 'Place a nearby aimed zone that damages and slows enemies inside it.', 12, 27, 16, 5, 4, '#b9dc96'),
      ability('ward', 'Canopy Guard', 'Shield yourself and allies standing close to you.', 16, 50, 8, 5, 4, '#d5eab2'),
      ability('summon', 'Grove Watch', 'Call two temporary allied sentinels beside you for 9 seconds.', 52, 32, 10, 4, 3, '#f2dfac'),
    ],
  },
  {
    id: 'chitrangada', name: 'Chitrangada', epithet: 'The Crossing Spear', origin: 'Mahabharata · original duelist arena adaptation',
    role: 'Vanguard', description: 'An agile defender who crosses a firing lane, answers with a spear arc and protects nearby allies. Her speed trades away the heavier vanguards’ health.',
    silhouette: 'Short segmented mantle, braided knot, crescent spear', color: '#ca785d', accent: '#ffe0a5',
    health: 350, speed: 7.5, damage: 24, fireInterval: .46, projectileSpeed: 37, weapon: 'spear', difficulty: 2,
    abilities: [
      ability('dash', 'Crossing Step', 'Dash forward up to 12 metres to cross or leave a firing lane. Solid obstacles stop movement.', 9, 25, 12, 3, 2, '#f1bb94'),
      ability('cone', 'Spear Arc', 'Strike enemies in a close forward cone with a sweeping energy blade.', 12, 44, 11, 4, 2, '#ffdcaf'),
      ability('ward', 'Defender’s Vow', 'Grant a strong temporary shield to yourself and nearby allies. Gather close before committing to the fight.', 44, 80, 8, 6, 4, '#fff0c7'),
    ],
  },
  {
    id: 'ulupi', name: 'Ulupi', epithet: 'The Riverward Keeper', origin: 'Mahabharata · original naga-inspired arena adaptation',
    role: 'Keeper', description: 'A guardian who gathers opponents into a clear target area and restores nearby allies. Her broad slowing zone controls an approach while leaving other routes open.',
    silhouette: 'Wave crest, scale-edged collar, water-ring staff', color: '#4cb3c0', accent: '#d6f6e4',
    health: 320, speed: 7, damage: 20, fireInterval: .46, projectileSpeed: 35, weapon: 'staff', difficulty: 3,
    abilities: [
      ability('pull', 'River Draw', 'Damage enemies in the aimed circle and draw them toward its centre. Solid cover limits displacement.', 12, 28, 19, 4, 2, '#9be5eb'),
      ability('heal', 'Cooling Current', 'Restore health to yourself and allies standing nearby.', 14, 44, 8, 5, 3, '#bff4df'),
      ability('slow', 'Naga Basin', 'Place a broad aimed zone that damages and slows enemies remaining inside for up to 6 seconds.', 46, 72, 23, 7, 6, '#a4e7dd'),
    ],
  },
];

/** Rendering/internal fallback only. Network joins must separately reject unknown IDs. */
export function heroById(id: string): HeroDef {
  return HEROES.find(hero => hero.id === id) ?? HEROES[0]!;
}
