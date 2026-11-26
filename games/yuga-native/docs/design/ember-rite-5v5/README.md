# Ember Rite · YUGA tactical objective direction

**Sound and counterplay.** An attacker can make an audible offer to kindle, release the hold and leave a defender guessing. Only confirmed ignition starts the public fire clock and its score. Rehearse this in the four offline districts, compare sounds around cover or audition both musical outcomes and the guide voices. [Play the listening exercise](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/rehearsal.html?map=mandala&exercise=explore&listen=1) · [Listening desk](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/audio/index.html) · [Audio bible and production roadmap](audio/README.md)

The vertical design study gives both sites in every district two shelter choices per entrance. Mandala also has measured flight, arrow and chakra paths, a 20-second mobile preparation phase, and a two-team rehearsal script. [Design fieldbook](atlas/vertical-play/README.md) · [All site entrances](atlas/vertical-play/door-register.md)

Ember Rite adapts the user's **“plant the fire”** brief into an original 5v5, two-site objective on the proposed Mandala Rift map. Attackers carry a protected ember and kindle a site; defenders interrupt or quench it. This is a **fictional ritual-inspired game mechanic**, not a description of an actual religious ceremony. Ten proposed hero concepts, a prologue and seasonal ideas supply the surrounding fiction.

- [Round rules, timing and authority contract](ROUND_AND_TECH.md)
- [Story, opening cinematic and voice script](STORY.md)
- [Ten hero roles, ability concepts and color research](HEROES_AND_COLOR.md)
- [Four-map atlas, measured blueprints and 3D blockouts](atlas/README.md) · [Ten-player encounter script](atlas/ENCOUNTERS.md)
- [Maps, modes and player progression](MODES_AND_MAPS.md)
- [Sources, corrections and implementation roadmap](SOURCES_AND_ROADMAP.md)
- [Five-hero animation, ability and VFX technical intake](../animation-tech-codex-2026/README.md)
- [New ember-vessel concept and provenance](../../../art/ember-rite-5v5/README.md) · [Existing five-hero art direction](../dharmic-heroes-key-visual-2026/README.md) · [Mandala Rift sketch and routes](../mandala-rift-5v5/README.md)

## What exists now

Open **Ember Rite map rehearsal** on the game title, launch `ember-rite.html` from the download, or play the standalone drill online. It follows the four drawn districts on foot. Private Confluence rooms still score hero knockouts. Hanuman and Rama received complementary ability additions in that Rust simulation. The other roster entries are design proposals or art studies. [Play rehearsal](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/rehearsal.html) · [Hero niches, counters and tests](HERO_BALANCE.md) · [Panel roadmap](atlas/PANEL_ROADMAP.md)

This update adds a standalone, deterministic [Rust rules experiment](../../../../yuga-rust/src/ritual.rs) and [boundary tests](../../../../yuga-rust/tests/ritual.rs). It can evaluate a complete round and a first-to-13 series **from trusted test observations**, but it is not connected to actual player movement, combat, online snapshots, rendering, animations or audio. Map geometry, spatial visibility, channel input, no-respawn enforcement and events require an authoritative adapter. The current camera is third person; first-person view is a separate experiment, not an existing mode.

The original round-rules milestone recorded 96 passing tests and two ignored cases. The new panel lists release checks for the revised map and hero builds separately. [Original Rust record](evidence/rust-tests.txt) · [Current panel and verification](atlas/PANEL_ROADMAP.md)

## Design choices

The vessel persists when dropped. Any attacker can recover it; any defender can use a personal water vessel to quench. There is no unavoidable fire damage or automatic speed bonus at the objective. Damage interrupts interactions, but the fire continues after all attackers are eliminated. First to 13 in regulation, paired side-swapped overtime at 12–12, and a bounded draw are specified separately. Costs, ability numbers, maps and accessibility remain playtest hypotheses, not measured balance or content already shipped.

Sun and Moon are player teams; **attack/defend changes at halftime without changing players' chosen heroes**. The Deva and Asura names in the user's brief inform fictional coalitions and conflicts, not a rule that a character's appearance defines a team or morality. Friendly/enemy markers are viewer-relative, include shape and text, and never rely on costume color. No lane or jungle minion waves are added.

Baseline: `47c458a55007b4096a7fc7646d3e48c578ad97b9`. The storyboard, palettes, abilities and three map variations are proposals; the rules experiment is tested separately from the current downloadable game. The known two-rendered-client software-rendering stall from the [Vanara Sena handoff](../vanara-sena-2026/README.md) remains an explicit multiplayer qualification gate.
