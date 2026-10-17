# Hero codex: fourteen distinct silhouettes and ultimates

This catalogue supplies fourteen complete art/animation briefs, fourteen primary presentations and all 42 Q/E/R slots. [hero-codex.json](../../assets/design/hero-codex.json) preserves the current browser definitions separately from proposed native-practice choreography. It does not establish new native hero models, animation, combat authority or production-art acceptance.

The direction is **mythic scale with readable combat**: a mountain procession, living courtyard, mirrored arrows, banner assemblies and braided water serpents. Large ornaments frame a clear actionable footprint; they do not hide targets, create terrain or multiply damage. Faces, anatomy, costume and motion distinguish individuals beyond palette swaps.

## Fourteen art cards

| Hero | Signature ultimate proposal | Visual identity |
| --- | --- | --- |
| [Rama](rama.md) | Mirrored-arrow eclipse | Calm vertical archer; crescent bow and split cobalt sash |
| [Ravana](ravana.md) | Ten-crown iris | Broad moving citadel; ten facets within one head silhouette |
| [Arjuna](arjuna.md) | Horizon needle | Quick diagonal archer; high quiver and silver mirror gates |
| [Duryodhana](duryodhana.md) | Iron crescent gate | Square grounded mace fighter; frontal bronze attack |
| [Hanuman](hanuman.md) | Mountain procession | Elastic leap, expressive face/tail, descending stone and rising herbs |
| [Karna](karna.md) | Sunwheel reversal | Heavy golden archer; shoulder discs and one close solar release |
| [Bhima](bhima.md) | Fault drum | Broad low stance; eight ground ribs and one weighted pulse |
| [Meghnad](meghnad.md) | Storm scroll | Forked crest, oblique footwork and transparent forward storm ribbons |
| [Sita](sita.md) | Living court of Mithila | Grounded protector; open branch arches and seed lanterns |
| [Draupadi](draupadi.md) | Fivefold assembly | Upright commander; five porous banners and one healing wave |
| [Subhadra](subhadra.md) | Twin banner procession | Field commander; exactly two temporary standard sentinels |
| [Hidimbi](hidimbi.md) | Walking grove pair | Powerful forest guardian; expressive face and two living grove forms |
| [Chitrangada](chitrangada.md) | Crossing oath | Agile spear duellist; crossed crescent plates becoming shields |
| [Ulupi](ulupi.md) | Naga river knot | Grounded water-staff guardian; two serpents framing one basin |

These are original fictional forms. [CREATIVE_HERO_SOURCES.md](../research/CREATIVE_HERO_SOURCES.md) separates retained literary motifs, existing rules and new invention. No new full book, Reddit corpus or commercial-game art/source extraction was undertaken here.

## Runtime contract

Load `res://assets/design/hero-codex.json`, require schema 1 and resolve an explicit known hero ID. Ultimate demonstrations use `heroes[].abilities` where `slot == "R"`.

| Field | Meaning |
| --- | --- |
| `id` / `native_demo.effect_id` | Stable `<hero>.r` / `<hero>.r.v1`; Q/E use corresponding lowercase suffixes |
| `browser_baseline` | Exact current unupgraded definition compared with `games/yuga/shared/heroes.ts` |
| `native_demo.shape`, `family`, `anchor` | Unique shape, semantic family and caster/aimed-forward/aimed-ground origin |
| `timing` / `timing_mode` | Seconds for preparation, nominal travel, active appearance and recovery; explicitly current or proposed |
| `payload_at_s` | Nominal presentation contact after preparation/travel, never permission to mutate gameplay |
| `range_m`, `radius_m`, `width_m`, `height_m` | Presentation envelope in metres, Y up/+Z forward; not replacement authority hit volumes |
| `telegraph` / `counterplay` | Advance warning or release/aftermath, readable boundary and opponent response |
| `projectile_count` / `summon_count` | Prevent phantom arrows or extra attackers; ornamental geometry carries no hitbox |
| `budget` | Instance, particle, light, voice, draw, triangle and lifetime ceilings |
| `applies_gameplay` | Always false for this design catalogue |
| `low_quality` / `reduced_motion` | Retain boundaries/expiry while dropping ornamental load; no screen flash or camera shake |

At most **four simultaneous demo casts** are proposed. Each cast is limited to 48 instances, 160 particles, one light, three voices, 16 draw calls, 18,000 triangles and 12 seconds. These are provisional engineering ceilings; no consumer GPU was measured. Share immutable meshes/materials, keep actor state separate and clear all effect state on replay/reset.

Only **Rama R, Hanuman R and Sita R** currently have authoritative preparation. Their 1.0/0.7/0.8-second windups remain; Hanuman's 0.45-second travel and Sita's six-second sanctuary remain. The other eleven R demonstrations propose visible preparation for offline study. Competitive adoption requires versioned server rules, tests, networking and balance review. The 28 Q/E slots remain immediate under their current shared kinds; aftermath must not masquerade as advance warning. Primary fire also cannot be delayed by an unapproved windup.

Rama still emits three arrows; Arjuna's line does not pierce walls. Subhadra/Hidimbi represent exactly two nine-second summons. Ulupi's serpents ornament one zone; Sita's forest is not solid terrain. Ordinary dashes/leaps add no damage or immunity. The native world has no complete hero-health/online receiver, so demonstrations must stay visibly separate from combat.

## Verification

From repository root after `npm ci`:

```sh
python3 games/yuga-native/tools/check-hero-codex.py --report /tmp/yuga-codex/check.json
python3 games/yuga-native/tests/hero_codex_cases.py --report /tmp/yuga-codex/cases.json
```

The validator uses a fixed Node/tsx roster import and pinned local sources; it preserves all fourteen identities/42 slots and checks finite geometry, timing, pool limits and proposal scope. JSON parsing rejects duplicate keys, nonfinite literals and files above 2 MiB. Catalogue data cannot supply executable code or source-import paths.

The current suite passes **71 checks**. Independent probes found and prompted repairs for huge-integer overflow, contradictory families, zero geometry/travel, misleading primary status, invalid palettes and booleans posing as numbers. The same eight malformed probes now reject without exceptions. Final reports and hashes are under [evidence](evidence/). They prove data contracts, not visual quality, animation contact, GPU performance or balance.

## Bounded handoff

This creative-intake packet covers current-source review → distinct concepts → validation/counterexamples → cards and source-pinned handoff. The next packet may build a native practice director, fourteen R effects, original cues and a clear selector. It must respect the catalogue, retain low-effects warnings, test pooled overlap/reset/invalid IDs and receive actual moving-render and input review. Batch 2 implementation has not been performed by this packet.

Production priorities remain one accepted hero and encounter: editable source, anatomy/face/hair/costume, hand/foot contact, continuous locomotion/aim/cast transitions and declared-hardware traces. Fourteen decorative ultimate demonstrations do not complete fourteen playable heroes. The canonical production roadmap retains its statuses.
