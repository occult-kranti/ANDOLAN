# Round 2 · accepted UI contract

Lead accepted exclusive ownership of `scripts/rama_hero_hud.gd`, `scripts/rama_hero_panel.gd`, new `scripts/rama_ability_meter.gd`, new `tests/rama_hero_feedback_cases.gd`, and this report directory. No shared theme, fixed JSON stats, input bindings, runtime combat, world or imported assets are edited.

The HUD keeps its existing public `slots`, `slot_cards`, `slot_glyphs`, vitals, text/status and remap semantics, supported compact footprint and opaque surfaces. Cooldown strips read real remaining cooldown divided by the current kit's fixed duration. Casting feedback uses live cast snapshots. Dawn Volley's three lane markers appear during the active action and use actual `release` event time plus each existing projectile delay; they are not charge stacks, hit confirmations or an extra resource. Unavailable, paused, cancelled, reset and detached states cannot retain ready meters.

Combat owner confirmed `kit.report().casts` lacks actual `release_age_s`; emitted `runtime.combat_event` includes it. Never infer paced launch time from nominal JSON windup. The UI listens to the existing immutable event signal and stores bounded cast receipts; rendering never changes simulation.

The guide adds contextual tactical instruction, calculated damage/defense summaries from existing JSON, and explicit cover/counterplay. Preserve existing rule description verbatim, current binding labels, focus/scroll behavior and read-only operation. Root separately owns the training progress card in `courtyard.gd`; no duplicate overlay.

R3 validation commands will use `godot --headless --path games/yuga-native --script res://tests/<suite>.gd -- --report=<fresh-absolute-json>` with process-specific isolated user-data directories. Engine imports, native captures and exports remain serialized by root. Existing regression suites cover layout, compact remaps, availability/reload, real action pause/reset, glyph identity and guide scales; new lifecycle assertions cover new meter semantics. Actual images/input remain R5 evidence.
