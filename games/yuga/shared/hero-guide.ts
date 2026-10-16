/**
 * Original match guidance for the current arena kits, not canonical epic powers.
 * Literary associations and their limits live in docs/MYTHOLOGY_AND_ROSTER.md.
 * Suggested exercises are optional prose, not automatic mastery/completion claims.
 */
export interface HeroGuide {
  firstAction: string;
  positioning: string;
  /** One short note for each current Q/E/R slot, in order. */
  abilityNotes: readonly [string, string, string];
  /** Practical options for an opponent facing this hero, not guaranteed wins. */
  counterplay: string;
  upgrades: Readonly<Record<'power' | 'vitality' | 'tempo', string>>;
  optionalPracticeGoal: string;
}

export const HERO_GUIDE_CONTEXT = {
  invitation: 'All 14 heroes and all three skills are unlocked. Choose a playstyle you enjoy; a role is an emphasis, not a restriction.',
  matchGoal: 'Protect your wave, defeat two defending towers to expose the enemy core, then attack it. Camps are optional detours.',
  practice: 'Choose one small thing to try, or play freely. An observed action is progress to inspect, not a mastery grade.',
  weapons: 'Every basic weapon fires an aimed projectile, including maces, staffs and spears. Aim and cover still matter.',
  upgrades: 'Spend match gold while alive within 15 metres of your own spawn. Each upgrade has three ranks; the next rank costs more. A fresh match resets purchases.',
} as const;

export const UPGRADE_GUIDES = {
  power: {
    label: 'Power',
    effect: 'Each rank adds 17% of base primary damage and 12% of base ability damage, healing, shielding and summoned-shot damage.',
    prices: '120 / 240 / 360 gold',
    tradeoff: 'Stronger hits and support compete with health or firing rate. Range, movement distance, slow strength and durations stay the same.',
  },
  vitality: {
    label: 'Vitality',
    effect: 'Each rank adds 65 maximum health and restores up to 65 current health.',
    prices: '100 / 200 / 300 gold',
    tradeoff: 'A larger health reserve buys room for mistakes; it adds no damage, shield or resistance.',
  },
  tempo: {
    label: 'Tempo',
    effect: 'Each rank adds 12% of base primary firing rate: the interval is divided by 1 + 0.12 × rank.',
    prices: '140 / 280 / 420 gold',
    tradeoff: 'Useful when you can keep landing basic shots. It does not reduce skill cooldowns or speed up movement, projectiles or preparation.',
  },
} as const;

export const HERO_GUIDES = {
  rama: {
    firstAction: 'Follow your wave and use Steady Arrow through a clear firing lane.',
    positioning: 'Keep space to turn and use Measured Step toward an escape route. Prepare Dawn Volley only when you can commit to its locked angle.',
    abilityNotes: ['Steady Arrow: one aimed, cover-blocked projectile.', 'Measured Step: a forward reposition of up to 10 metres.', 'Dawn Volley: brace for 1 second, then fire three separate arrows.'],
    counterplay: 'Move sideways or behind cover during the volley preparation. Pressure him after his reposition is spent.',
    upgrades: { power: 'Reward accurate primary shots and both arrow skills.', vitality: 'Add a buffer while learning when to brace or retreat.', tempo: 'Favor repeated basic shots; Dawn Volley still has its full cooldown.' },
    optionalPracticeGoal: 'Land one aimed shot before trying a longer volley.',
  },
  ravana: {
    firstAction: 'Move with an ally and use Tenfold Guard before taking a close exchange.',
    positioning: 'Commanding Circle acts at the aimed point; Crownfire acts around you. Close the gap deliberately instead of expecting the pull to bring everyone to your feet.',
    abilityNotes: ['Tenfold Guard: shield yourself and allies within 4 metres.', 'Commanding Circle: damage and pull around the aimed circle.', 'Crownfire: damage visible enemies within 7 metres of you.'],
    counterplay: 'Keep outside Crownfire range, spread away from the pull circle and use cover. His shield is temporary.',
    upgrades: { power: 'Increase shield strength as well as pull, blast and basic damage.', vitality: 'Support a sustained approach, without adding movement speed.', tempo: 'Improve repeated chakram shots when closing is unsafe.' },
    optionalPracticeGoal: 'Place one Commanding Circle on a visible enemy.',
  },
  arjuna: {
    firstAction: 'Stay behind your wave and try Converging Volley against enemies in front of you.',
    positioning: 'Use New Angle to change a firing lane, keeping a route out. Your 275 starting health makes exposed trades costly.',
    abilityNotes: ['Converging Volley: a forward fan reaching 18 metres.', 'New Angle: dash forward up to 12 metres; walls stop you.', 'One Clear Line: a fast aimed projectile, blocked by cover.'],
    counterplay: 'Use cover against the heavy shot and pressure him after his dash. Avoid standing in the forward fan.',
    upgrades: { power: 'Make landed fan, line and primary hits stronger.', vitality: 'Increase the roster’s smallest starting health reserve.', tempo: 'Build on frequent basic shots, without refreshing New Angle sooner.' },
    optionalPracticeGoal: 'Use New Angle once with a clear destination.',
  },
  duryodhana: {
    firstAction: 'Advance with the wave and use Mace Shock when an opponent enters your short forward reach.',
    positioning: 'Hold the Ground protects allies close to you. Keep enemies in front for Iron Crescent; your mace’s basic shot still needs aim.',
    abilityNotes: ['Mace Shock: strike the forward area within 10 metres.', 'Hold the Ground: a 4-second shield for yourself and close allies.', 'Iron Crescent: a heavy forward cone reaching 12 metres.'],
    counterplay: 'Keep distance or move around his forward attacks. Wait out the shield rather than treating high health as invulnerability.',
    upgrades: { power: 'Increase both forward attacks, primary damage and allied shielding.', vitality: 'Extend an already large health reserve for close pressure.', tempo: 'Favor more basic mace projectiles when enemies stay outside your skills.' },
    optionalPracticeGoal: 'Aim one Mace Shock while keeping a retreat route open.',
  },
  hanuman: {
    firstAction: 'Stay near your wave and use Bring Them Home when you or a nearby ally have lost health.',
    positioning: 'Windward Leap can reposition you without damage. Aim Mountain Pulse at a place where its landing can help allies as well as threaten enemies.',
    abilityNotes: ['Windward Leap: move forward up to 14 metres, respecting walls.', 'Bring Them Home: heal yourself and allies within 5 metres.', 'Mountain Pulse: prepare 0.7 seconds, travel 0.45 seconds, then damage and heal around the landing.'],
    counterplay: 'Leave the marked landing area or use cover. Ordinary damage does not interrupt the preparation, and the leap grants no invulnerability.',
    upgrades: { power: 'Strengthen healing, landing damage and primary hits.', vitality: 'Give a committed landing more health to work with.', tempo: 'Add primary pressure between heals; neither leap recovers sooner.' },
    optionalPracticeGoal: 'Use Bring Them Home after taking some damage.',
  },
  karna: {
    firstAction: 'Find a clear angle beside your wave and aim Sunshaft at a visible target.',
    positioning: 'Borrowed Dawn gives nearby allies a brief shield. Keep Solar Reprisal for enemies who enter its 6-metre circle.',
    abilityNotes: ['Sunshaft: one fast projectile reaching 27 metres.', 'Borrowed Dawn: shield yourself and close allies for 3 seconds.', 'Solar Reprisal: a damaging circle centred on you.'],
    counterplay: 'Break the firing lane with cover and avoid chasing into his close blast. His slower basic shot rhythm leaves gaps between releases.',
    upgrades: { power: 'Favor heavy accurate shots, blast damage and shield strength.', vitality: 'Make holding an angle less fragile when the shield ends.', tempo: 'Shorten primary-shot intervals, without changing Sunshaft’s cooldown.' },
    optionalPracticeGoal: 'Land one Sunshaft from a clear firing lane.',
  },
  bhima: {
    firstAction: 'Move with the wave, then use Heavy Sweep when a target enters your forward reach.',
    positioning: 'Closing Stride commits you toward your aim. Check the landing space before using Thunder at Your Feet around your new position.',
    abilityNotes: ['Heavy Sweep: a forward cone reaching 10 metres.', 'Closing Stride: leap forward up to 12 metres; no landing damage.', 'Thunder at Your Feet: damage visible enemies within 8 metres.'],
    counterplay: 'Keep space, use cover and move away from the landing. Bhima has no shield or heal skill to repair a poor commitment.',
    upgrades: { power: 'Increase sweep, blast and primary damage; the leap remains movement.', vitality: 'Support close exchanges when your escape route is uncertain.', tempo: 'Help repeated basic shots when you cannot enter blast range.' },
    optionalPracticeGoal: 'Use Closing Stride toward open ground once.',
  },
  meghnad: {
    firstAction: 'Aim Cloud Snare at an approach an opponent is using, then continue firing from outside the danger.',
    positioning: 'Use Storm Step to change angle. Gathered Squall hits in front of you, so turn toward the target before casting.',
    abilityNotes: ['Cloud Snare: a visible ground zone with damage and slow.', 'Storm Step: dash forward up to 13 metres; cover stops movement.', 'Gathered Squall: a forward fan reaching 22 metres.'],
    counterplay: 'Leave the cloud to limit its ongoing damage, spread from the fan and pressure his small health reserve after the dash.',
    upgrades: { power: 'Increase zone, fan and primary damage, not slow strength.', vitality: 'Reduce the cost of a failed flank with more health.', tempo: 'Favor basic shots between zone placements; it does not refresh the cloud.' },
    optionalPracticeGoal: 'Place one Cloud Snare on an enemy approach.',
  },
  sita: {
    firstAction: 'Stay close to your wave and use Grove Renewal when nearby allies or you need health.',
    positioning: 'Rooted Path shapes an approach. Put Shelter of Mithila where allies can stay: it is fixed in place and leaves you preparing for 0.8 seconds.',
    abilityNotes: ['Grove Renewal: heal yourself and allies within 5 metres.', 'Rooted Path: damage and slow within the aimed ground zone.', 'Shelter of Mithila: shield nearby allies once, then heal occupants of the 6-second sanctuary.'],
    counterplay: 'Take another approach or leave the zone. Pressure from outside her support circle; damage alone does not cancel a preparing sanctuary.',
    upgrades: { power: 'Increase heals, shields, zone damage and primary hits.', vitality: 'Help you survive while staying close enough to support allies.', tempo: 'Add primary pressure; it does not shorten either healing cooldown.' },
    optionalPracticeGoal: 'Use Grove Renewal after you or a nearby ally lose health.',
  },
  draupadi: {
    firstAction: 'Move with allies and use Circle of Resolve before a nearby exchange.',
    positioning: 'Aim Stand Accountable at a clear enemy group. Save Unbroken Assembly for injured allies within 8 metres; keep a walking route out.',
    abilityNotes: ['Circle of Resolve: a temporary shield for nearby allies and you.', 'Stand Accountable: damage and pull in an aimed circle.', 'Unbroken Assembly: a large immediate heal around you.'],
    counterplay: 'Spread out from the pull, use cover and keep pressure outside the healing group. She has no dash or leap.',
    upgrades: { power: 'Improve group shielding/healing and damaging attacks.', vitality: 'Keep the support centre alive without granting an escape skill.', tempo: 'Favor staff fire between support casts; heal cooldowns stay fixed.' },
    optionalPracticeGoal: 'Cast Circle of Resolve near an ally.',
  },
  subhadra: {
    firstAction: 'Follow an ally and open with an aimed Signal Lance.',
    positioning: 'Rally Close has a small 4-metre radius. Call Twin Standards near a useful lane position rather than expecting its sentinels to last the whole fight.',
    abilityNotes: ['Signal Lance: an aimed projectile reaching 24 metres.', 'Rally Close: heal yourself and nearby allies.', 'Twin Standards: call two allied sentinels for 9 seconds.'],
    counterplay: 'Break her projectile lane and separate her from injured allies. Summons expire; defeating them grants no gold or team score.',
    upgrades: { power: 'Strengthen the heal, lance, primary hits and summoned shots.', vitality: 'Help you stay close enough for the small healing circle.', tempo: 'Increase your own basic firing rate, not the sentinels’ rate.' },
    optionalPracticeGoal: 'Try Signal Lance once at a visible target.',
  },
  hidimbi: {
    firstAction: 'Place Forest Boundary across an approach, then stay close enough to shield your wave with Canopy Guard.',
    positioning: 'Protect a useful position without standing alone in it. Grove Watch supplies temporary help, not a permanent defence.',
    abilityNotes: ['Forest Boundary: an aimed damaging and slowing zone.', 'Canopy Guard: shield yourself and allies within 5 metres.', 'Grove Watch: call two allied sentinels for 9 seconds.'],
    counterplay: 'Use another approach, let the zone expire, and pressure from outside the shield group. Summons award no gold or team score.',
    upgrades: { power: 'Improve zone damage, shields, primary hits and summoned shots.', vitality: 'Support holding ground while allies arrive.', tempo: 'Favor your basic spear shots; it adds no summon lifetime or firing rate.' },
    optionalPracticeGoal: 'Place Forest Boundary across one visible approach.',
  },
  chitrangada: {
    firstAction: 'Follow your wave and use Spear Arc when a target reaches the short forward cone.',
    positioning: 'Crossing Step can enter or leave an angle. Gather allies within 6 metres before Defender’s Vow; a dash does not make you immune to damage.',
    abilityNotes: ['Crossing Step: dash forward up to 12 metres.', 'Spear Arc: a forward damaging cone reaching 11 metres.', 'Defender’s Vow: a strong 4-second shield for you and nearby allies.'],
    counterplay: 'Avoid her forward arc, keep space after the dash and wait out the shield. Her starting health is lower than the heavier Vanguards’.',
    upgrades: { power: 'Increase the arc, primary damage and allied shield strength.', vitality: 'Give a mobile approach a larger health reserve.', tempo: 'Favor repeated spear projectiles; Crossing Step keeps its cooldown.' },
    optionalPracticeGoal: 'Use Crossing Step toward an open retreat route.',
  },
  ulupi: {
    firstAction: 'Aim River Draw at a visible target, keeping injured allies close for Cooling Current.',
    positioning: 'Naga Basin controls a chosen ground circle, not the whole lane. Aim down to place it closer and leave yourself a clear retreat.',
    abilityNotes: ['River Draw: damage and pull enemies toward an aimed centre.', 'Cooling Current: heal yourself and allies within 5 metres.', 'Naga Basin: a broad damaging and slowing zone lasting up to 6 seconds.'],
    counterplay: 'Leave the basin, spread away from the pull and use a different approach. Her heal reaches allies only within 5 metres.',
    upgrades: { power: 'Strengthen pull/zone damage, healing and basic attacks.', vitality: 'Help a Keeper with no movement skill survive pressure.', tempo: 'Improve staff fire between casts; the basin’s duration and slow stay fixed.' },
    optionalPracticeGoal: 'Place one Naga Basin where you intend, using ground aim.',
  },
} satisfies Record<string, HeroGuide>;

export type HeroGuideId = keyof typeof HERO_GUIDES;

/** Unknown IDs remain unknown; guidance must not silently describe another hero. */
export function heroGuideById(id: string): HeroGuide | undefined {
  return Object.hasOwn(HERO_GUIDES, id) ? HERO_GUIDES[id as HeroGuideId] : undefined;
}
