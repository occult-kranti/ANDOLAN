# Vanara Sena · YUGA ability handoff

Vanara Sena adapts the user's image of Hanuman calling a coordinated company into a **brief, ground-targeted hero ability** for the Rust/PlayCanvas 5v5 prototype. Golden wind, petals and five spectral guardians give the action its identity; the authority owns one damage field, not five autonomous soldiers. The art and the mythology that inspire the ability do not establish its gameplay rules.

This packet separates the first competitive slice from proposed future independent companions and an original boss encounter. Soldier and jungle-creature waves remain paused. The separate Godot Hanuman trial continues to use its own five-action profile unless separately updated and tested.

- [Player-facing and animation script](ACTION_SCRIPT.md)
- [Original boss and future-companion proposals](BOSS_AND_NEXT.md)
- [Research, attribution and claim boundaries](SOURCES.md)
- [Generated ability concept sheet](../../../art/vanara-sena-concept-2026/concept.png), a visual reference rather than an in-game render or animation
- [Current Rust ability implementation](../../../../yuga-rust/assets/vanara-sena.json) and [Hanuman combat authority](../../../../yuga-rust/src/combat.rs)
- [Editable Blender motion study and preview](../../../art/vanara-sena-motion-2026/README.md) · [Original synthesized release cue](../../../art/vanara-sena-audio-2026/README.md)

## First competitive rule contract

| Rule | Initial tuning, subject to playtesting |
| --- | --- |
| Binding | Hanuman's sixth action, slot index `5`, **V**; Rama retains his existing five slots. |
| Placement | Fixed ground-targeted disk, radius **3 m**, up to **10 m** from Hanuman; the origin and destination must be valid and a clear route must exist between them. |
| Clock | **0.60 s** windup, then an immediate impact and **2.00 s** active field; body recovery is **0.40 s** after impact; **20 s** cooldown starts on accepted cast. Authority uses 20 ticks/s. |
| Enemy effect | **12 damage** at impact, then **8 damage/s** while eligible inside the field. The ideal uninterrupted 2 s exposure is **28 total damage**, before shields and other match interactions; it is not five separate hits multiplied by five guardians. |
| Counterplay | The caster is vulnerable. Opponents can interrupt by defeating Hanuman, leave the marked area, take cover, or move outside its supported height band. There are no invulnerability frames, roots, armor breaks or secret damage multipliers in this first rule. |
| Multiplayer | The server owns the accepted cast, tick, radius, cooldown and actual recipient receipts. Visual guardians are cues only: they have no independent health, collision, targeting, pathfinding or damage. No persistent lane or jungle minions are introduced. |

The numerical target is an initial design contract, not evidence that this is balanced. The playable caster reuses `cast2`; its five **painted, animated 2D spectral cards** and ground ring are presentation cues rather than skinned characters or independent combatants. The separate Blender scene explores a pluck-and-breath gesture using the actual Hanuman rig, but that authored motion is not in the game. The short in-game cue is original synthesized audio and contains no chant.

## Current prototype verification

- [Rust suite](evidence/rust-tests.txt): 86 tests passed, two ignored; eight focused cases exercise the new ability, counterplay, interruption, overlap and hero-specific slot rejection.
- [Ten local WebSocket peers](evidence/ten-peer-network.json) saw the same cast in all nine remote views, measured 28 total damage, rejected Rama's slot and a duplicate sequence, and spawned no waves. [Native/Wasm 5v5 replay](evidence/native-wasm-5v5.json) also matched with five simultaneous Vanara Sena casts; neither test renders ten browsers or proves internet performance.
- One [Chromium practice capture](evidence/browser-sena.json) checked the 3 m preview, a 12-damage hit, five visible spirits, expiry, V shortcut and six controls in a 390 × 844 viewport. [After contrast correction](evidence/browser-sena.png) · [Earlier lighter version](evidence/browser-before-contrast.png). This software-rendered check is not a human balance, listening or hardware-performance review.
- A [two-rendered-client loopback diagnostic](evidence/two-browser-diagnostic.json) of the initial build did **not** verify the defender's visual cue: the observer received the cast and took the expected damage, but its software renderer produced no new frame during the two-second field under that test load. This is a failed presentation/performance check, not proof of how a hardware GPU or real network behaves. The [first run](evidence/two-browser-initial-fixture-failure.json) also exposed an overly strict aim-drift assertion; the [subsequent run](evidence/two-browser-observer-timeout.json) retained the observer timeout after that fixture was corrected. The diagnostic's [exact test source](evidence/two-browser-diagnostic-test.mjs.gz) is archived compressed; the reusable test differs only by a final blank line.
- A follow-up [single-rendered-observer baseline](evidence/observer-diagnostic.json) with a lightweight WebSocket caster likewise received the cast and damage but did not observe the five guardians. Preallocating the bounded effect and merging its radial marks into one mesh produced a [later run](evidence/observer-v5-atomic.json) that observed five remote spirits in renderer state and the 12-damage impact. The earlier preallocation-only comparison is retained ([initial harness failure](evidence/observer-v4-diagnostic.json), [corrected atomic observation](evidence/observer-v4-atomic.json)); the [original comparison harness](evidence/observer-diagnostic-test.mjs.gz) is archived. The successful single-observer runs did not retain a qualifying image of the brief remote effect.
- A [two-rendered-client rerun of the optimized build](evidence/two-browser-v5-diagnostic.json) still **failed** to show the defender's cue: the observer received the cast and lost 28 HP, but its software renderer did not advance during the sampled cast. The single-observer result does not establish smooth frame pacing, and neither test establishes hardware-GPU behavior or WAN performance. Retest on actual target hardware before relying on the effect in competitive play.
- A separate [full practice run](evidence/browser-full-practice.json) passed 41 checks and demonstrated all six techniques through ordinary input. [Completion screen](evidence/browser-six-techniques.png).
- Tested ZIP SHA-256: `9f0a4f150cab90ebffe387bfb1e02ce492137cac1dde299fdfb82b1f17c508af`. [Build manifest](evidence/build.json) · [Package and embedded-rig check](evidence/release-check.json). Two independent builds produced this same ZIP hash. The existing standalone face-sculpt preview is an earlier five-action build.

## Follow-on priorities

1. Check actual V-key and mouse targeting, invalid/blocked/airborne casts, interruption, cooldown and the exact end of the field on both native and Wasm authority.
2. Resolve the two-client frame stall, then capture the action from both teams at ordinary gameplay distance: one hit, a clear escape, cover blocking, overlapping casts and a knockout. Confirm a visible, shape-coded radius even with reduced effects and audio muted.
3. Test competitive readability and impact in human 5v5 play before tuning damage. Profile match startup, ten visible heroes, the bounded cached effects and simultaneous fields on target hardware; compare real frame-time distributions rather than assuming fewer render objects guarantee smoother play.
4. If players want independently moving guardians or a co-op boss, develop them under the separate proposal in [BOSS_AND_NEXT.md](BOSS_AND_NEXT.md); they require authority, navigation and performance work and are not implied by the current visual effects.

The [source notes](SOURCES.md) record passages and limitations. Existing works inspired the broad design; the gameplay, script, artwork and fictional encounter here are original YUGA adaptations.
