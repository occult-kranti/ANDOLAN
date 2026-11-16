# Rama combat panel — rounds 1 and 2

Task YUGA-HERO-6R, native desktop/offline. Source base
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`;
pre-existing studio changes are preserved. The parent owns integration and the
shared ledger. Skills: `yuga-motion-combat`, `yuga-hero-art`.

## Round 1 — audit the last actual hero

Read the current native handbook, active handoff, quality target, ability kit,
runtime/effects/motion source and relevant reuse/warm-entry evidence. Opened
three actual previous captures: studio `final-native/07-final-training-entered.png`,
`final-native/10-final-world.png`, and `forward-probe/04-qualified-world.png`.
They show the existing Rama, bow, ivory garment, blue drape and working HUD.
They are stills; this is not a new continuous-motion acceptance.

The current kit is already playable and authoritative within local practice:
Kodanda 28 damage, Piercing Dawn 70 damage/up to six recipients, Measured Step
4.5 m collision-limited movement with no invulnerability, Guardian Circle 5 m
fixed shielding/healing, and Dawn Volley three 82-damage arrows at 0/.1/.2 s
after accepted release. The army owns the 20 Hz clock. Effects/audio/motion
consume accepted events and cannot award damage or release attacks.

The concrete presentation defect is in `RamaAbilityEffects._animate`: every
projectile warning disappears when the first arrow releases. For Dawn Volley,
two locked lanes consequently lose their warnings before their own pulse.
Thin, single-tone projectile lines also lack the Guardian boundary's contrast
on pale paving. Existing warning strokes straddle the nominal sweep radius,
making the visible outer edge slightly too wide.

Baseline commands, all exit 0 with Godot 4.6.3 official:

```sh
godot --headless --path games/yuga-native --script res://tests/rama_ability_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/baseline/abilities.json
godot --headless --path games/yuga-native --script res://tests/rama_ability_visual_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/baseline/visual-structure.json
godot --headless --path games/yuga-native --script res://tests/rama_effect_adversarial_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/baseline/adversarial.json
```

Results: 85/85 ability checks, 74/74 presentation structure checks, 56/56
adversarial consumer checks. Source pins are beside these reports.

## Round 2 — agreed implementation contract

Exclusive files: `scripts/rama_ability_effects.gd`, new
`shaders/rama_projectile_warning.gdshader`, new
`tests/rama_volley_warning_cases.gd`, the legitimate shader expectation in
`tests/rama_ability_visual_cases.gd`, and this `combat/` report directory.
No kit/rule/rig/GLB/motion edits are authorized by this bounded contract.

Each pending Volley lane persists until its own accepted authority age reaches
the projectile delay. Interpolation cannot remove a warning. A two-tone dark
outline and warm core make the committed lanes readable without filled floors,
particles, screen flashes or new collision. Strokes sit inside their true sweep
radius. Ordinary primary shots continue without ground warnings. Reduced
effects/motion retain the same essential warnings. Pause, stale events, cancel,
reset and between-pulse interruption must preserve correct lifetime.

HUD coordination: `kit.report().casts` does not contain actual release age;
the UI owner must consume `runtime.combat_event`/accepted events for Volley
pulse counts. Emitted events contain `age_s`, actual `release_age_s` and
`geometry.projectiles[].delay_s`. Nominal JSON windup is not a substitute for
the accepted release tick.

Remaining art findings remain open: prior C1–C8 and three MPFB hair candidates
were rejected; copying their geometry into the game would not improve quality.
The warm-primary string-entry repair is already integrated. Later Piercing
Dawn entry and respawn/reaim contact residuals need separate localization.
