# Ember Rite · YUGA tactical objective direction

Ember Rite adapts the user's **“plant the fire”** brief into an original 5v5, two-site objective on the proposed Mandala Rift map. Attackers carry a protected ember and kindle a site; defenders interrupt or quench it. This is a **fictional ritual-inspired game mechanic**, not a description of an actual religious ceremony. Ten proposed hero concepts, a prologue and seasonal ideas supply the surrounding fiction.

- [Round rules, timing and authority contract](ROUND_AND_TECH.md)
- [Story, opening cinematic and voice script](STORY.md)
- [Ten hero roles, ability concepts and color research](HEROES_AND_COLOR.md)
- [Maps, modes and player progression](MODES_AND_MAPS.md)
- [Sources, corrections and implementation roadmap](SOURCES_AND_ROADMAP.md)
- [New ember-vessel concept and provenance](../../../art/ember-rite-5v5/README.md) · [Existing five-hero art direction](../dharmic-heroes-key-visual-2026/README.md) · [Mandala Rift sketch and routes](../mandala-rift-5v5/README.md)

## What exists now

The current Rust/PlayCanvas download is still a **hero-only knockout skirmish** with playable Hanuman and Rama, private 1v1/3v3/5v5 rooms and no wave minions. The proposed two-site map and objective are **not in that match, its UI, server protocol or published ZIP**. Krishna has a development rig and Arjuna has designs in a separate older roster; the other proposed heroes are not new Rust-match integrations. The earlier [Rift Seal](../mandala-rift-5v5/MATCH_SCRIPT.md) script is retained as a historical proposal; Ember Rite is the new objective direction.

This update adds a standalone, deterministic [Rust rules experiment](../../../../yuga-rust/src/ritual.rs) and [boundary tests](../../../../yuga-rust/tests/ritual.rs). It can evaluate a complete round and a first-to-13 series **from trusted test observations**, but it is not connected to actual player movement, combat, online snapshots, rendering, animations or audio. Map geometry, spatial visibility, channel input, no-respawn enforcement and events require an authoritative adapter. The current camera is third person; first-person view is a separate experiment, not an existing mode.

The full Rust suite passed **96 tests with two ignored**, including ten focused objective tests. A separate `wasm32-unknown-unknown` release build compiled successfully with Rust 1.88.0; that compilation does not expose or test an online mode. [Test log](evidence/rust-tests.txt) · [Wasm build log](evidence/wasm-build.txt)

## Design choices

The vessel persists when dropped. Any attacker can recover it; any defender can use a personal water vessel to quench. There is no unavoidable fire damage or automatic speed bonus at the objective. Damage interrupts interactions, but the fire continues after all attackers are eliminated. First to 13 in regulation, paired side-swapped overtime at 12–12, and a bounded draw are specified separately. Costs, ability numbers, maps and accessibility remain playtest hypotheses, not measured balance or content already shipped.

Sun and Moon are player teams; **attack/defend changes at halftime without changing players' chosen heroes**. The Deva and Asura names in the user's brief inform fictional coalitions and conflicts, not a rule that a character's appearance defines a team or morality. Friendly/enemy markers are viewer-relative, include shape and text, and never rely on costume color. No lane or jungle minion waves are added.

Baseline: `47c458a55007b4096a7fc7646d3e48c578ad97b9`. The storyboard, palettes, abilities and three map variations are proposals; the rules experiment is tested separately from the current downloadable game. The known two-rendered-client software-rendering stall from the [Vanara Sena handoff](../vanara-sena-2026/README.md) remains an explicit multiplayer qualification gate.
