# Design lessons that change the Rama slice

Study date: **17 October 2026 UTC**. Native source baseline:
`a9dd94d8580e72cc109e8c271eb338a471611bfc`. The [source ledger](game-design-reuse-sources.json)
pins exact successful responses, read ranges, short excerpts and failures.
This packet contains original notes and proposed acceptance gates. **No runtime
code/assets were adopted, and no engine, render or gameplay test was run here.**

Read the existing [Rama study](RAMA_HERO_DESIGN_STUDY.md) for the bounded Deadlock
kit comparison and the [research brief](RESEARCH_BRIEF.md) for earlier feedback,
mythology and engine work. This packet adds component/update-order analysis and
an original open-game source example; it does not repeat the roster catalogue
or claim new commercial-client analysis.

## What was read

Robert Nystrom's *Game Programming Patterns*, at
[`898b1f2e…`](https://github.com/munificent/game-programming-patterns/tree/898b1f2e1818c80d7eed5eba98e9903ec13b7771),
supplied **selected sections from four chapters**, not four books or complete
chapter coverage:

| Chapter | Exact fresh reading | Why it matters here |
| --- | --- | --- |
| [Component](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/component.markdown#L184) | 184–246; 469–666: pattern, costs, construction and communication | Separate hero domains while retaining explicit ownership and update order. More components are not automatically faster or clearer. |
| [Object Pool](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/object-pool.markdown#L81) | 81–235: use, memory/capacity tradeoffs, initialization and retained references | Overflow and retirement are gameplay/readability decisions as well as allocation decisions. |
| [Game Loop](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/game-loop.markdown#L373) | 373–493: fixed catch-up and presentation between updates | Preserve a single rules clock; distinguish simulation granularity from visible FPS and extrapolation guesses. |
| [Update Method](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/update-method.markdown#L200) | 200–304; 520–570: sequential updates, collection mutation, dormant objects | Declare same-tick interaction rules and optimize active work without changing battle outcomes. |

Game Loop/Object Pool revisit earlier project reading. Component/Update Method
are new scoped reads in this packet. The book's
[license](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/LICENSE)
separates CC BY-NC-ND 4.0 prose/site files from MIT qualifying source-code files.
Full chapter bodies remain in scratch. The public ledger contains hashes,
section ranges and only 34 words of necessary book excerpts; these original
paraphrases are not a copied/adapted chapter or a blanket code/asset license.

The official Godot **Platformer 3D** example at
[`b761b4cd…`](https://github.com/godotengine/godot-demo-projects/tree/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/3d/platformer)
provides an original implementation that can be inspected without reconstructing
a commercial binary. The complete 202-line
[player](https://github.com/godotengine/godot-demo-projects/blob/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/3d/platformer/player/player.gd)
and 91-line
[camera](https://github.com/godotengine/godot-demo-projects/blob/b761b4cd5718a7118f2c95eb55f181d0a5f004f1/3d/platformer/player/follow_camera.gd)
scripts, short README, root MIT notice and project-header lines 1–19 were read.
The header declares **Godot 4.7**; YUGA uses **4.6.3**. Nothing was imported or
compiled, so this is a design/code study with untested version compatibility.
No demo models, maps, music, textures or touch add-on were downloaded/adopted.

Ordinary requests for the original MDA PDF, Riot's clarity article and Game AI
Pro index each stopped at **proxy tunnel 403**. Those bodies were not read and
support no findings below. One incorrect Nystrom README path returned 404; its
correct README and LICENSE paths are separately recorded. No blocked-host
retry, alternate route, subreddit crawl or video viewing occurred.

## Eight decisions and their acceptance gates

The book supplies architectural reasoning. The following combat/map/feel
consequences are **our design inferences**, to be checked in YUGA. Existing test
filenames identify useful harnesses; this reading task did not rerun them or
close a production gate.

| ID / source | YUGA decision and present subsystem | Testable acceptance / next owner |
| --- | --- | --- |
| **GD-R01 — Game Loop 373–493** | Keep the 20 Hz ability/army rules clock separate from 60 Hz physics and variable-rate presentation. A smooth arrow or fading Guardian decoration must not move damage, shield expiry or the active boundary. `rama_ability_kit`, `rama_vitals`, `rama_ability_effects`, `rama_hero_hud`. | **Combat + QA:** identical accepted command tape at 30/60/120 presentation rates produces the same releases, damage and expiry ticks. At the kit-defined field deadline, authority, boundary and displayed shield agree in that normal frame. Challenge both listener orders and a bounded hitch. Start with `rama_ability_cases`, `rama_hud_expiry_cases`, `rama_hero_integration_cases`; human smoothness and GPU frame time remain separate. |
| **GD-R02 — Component 184–246, 478–666** | Retain one owner for rules, skeleton motion, facial morphs, secondary offsets, material calibration and UI. Use typed/versioned events for cross-domain effects; avoid a new generic entity-system rewrite without a measured problem. `rama_hero_runtime`, `rama_motion`, `rama_action_buffer`, face/secondary/LOD components. | **Runtime + QA:** training, Confluence and any replica bind one live rig and one face writer, release one payload per accepted action and never accumulate listeners after reconfigure/reset. Missing components fail configuration explicitly. Extend `rama_quality_integration_cases`, `hero_lod_binding_cases` and replica fixtures where relevant. No second damage/movement authority may arise from rendering. |
| **GD-R03 — Update Method 200–304** | Treat simultaneous-looking minion combat as an explicit sequence. Declare whether same-tick trades resolve from a common snapshot, how ties earn gold and when new waves first act. Retain deferred cleanup/reset rather than mutating active iteration unpredictably. `lane_army`, siege attack collection and reward receipts. | **Army + economy:** replay the same stable IDs/commands through death, spawn and reset; get the same winner/core/gold and exactly one reward per kill. A new unit cannot receive an accidental extra attack from list placement. Mirror equal-team scenarios to expose first-list bias. Use `lane_army_cases`, `siege_army_cases`, `traversal_army_stress`; these are proposed explicit counterexamples, not new passing results. |
| **GD-R04 — Object Pool 117–169** | Define overflow by significance. Cosmetic flourishes may shrink/drop; authoritative damage and the imminent-damage/active-field contract cannot disappear because an effect slot is busy. Keep per-hero effect/contact caps and a separately measured full-fight budget. `rama_ability_effects`, `rama_action_audio`, army entity limits. | **VFX + audio + performance:** saturate cast/contact/voice pools. Damage, critical warning lifetime and status values remain correct; counters stay within declared capacity and record what was dropped/preempted. Check actual overlapping attacks with reduced effects. Existing `rama_vfx_quality_cases`/`rama_action_audio_cases` support the numeric half; threat recognition and a real populated GPU trace remain open. |
| **GD-R05 — Object Pool 199–235** | Reuse requires complete reset: generation, recipient links, opacity, pitch, cue IDs and external references must not leak into the next cast. Stopping a voice and mixer retirement are different lifetime stages. `rama_ability_effects`, `rama_action_audio`, scene/test teardown. | **VFX + audio + QA:** cancellation/death/F5/reconfigure followed by slot reuse shows no old warning, recipient, sound or delayed payload. Stale generation receipts cannot revive it. Inspect live/pooled counts and actual Dummy playback retirement, then separate human listening. Reuse existing action-audio/VFX/quality integration fixtures; a fixed simulated soak alone does not prove memory or audible quality. |
| **GD-R06 — Update Method 520–570 + Component 232–243** | Optimize visible work without making offscreen fights stop. LOD may change body/bow geometry; it must preserve the shared rig/face and must not suspend army/ability authority. Only introduce active/inactive collections where measured inactive work justifies their synchronization cost. `rama_visual_lod`, `rama_lod_binding`, `lane_army`. | **Art + performance:** same authoritative results with opponent visuals hidden/distant; one live rig and stable IDs across switches; source-matched near/selected pose pairs and continuous motion/camera checks. Keep the existing 182.3 px mid-level glint **LIMITED** until its forced-near comparison/material-frame work. Physical-GPU CPU/GPU/memory traces must justify further optimization; geometry reduction is not an FPS claim. |
| **GD-R07 — Godot camera 16–29, 32–91** | Adopt the camera-safety lesson, not the platformer's automatic steering. Exclude the controlled actor from collision; constrain near-wall distance and keep player aim deliberate. YUGA already has a sphere-shaped SpringArm with actor exclusion, so replacing it with demo rays is unnecessary. `player` camera rig; Confluence walls/arches/raised decks. | **Controls + world:** sweep approach/retreat/strafe beside a wall, column, arch and bridge; camera does not enter solid geometry or rotate the crosshair on its own. The first accepted shot agrees with the visible aim/cover contract. Preserve the actor exclusion through reset/respawn and remapping; compare actual input footage, not a fixed beauty camera. |
| **GD-R08 — Godot player 35–43, 63–68, 149–176** | Reuse the discontinuity and input-contract lessons, with original tuning. Clear velocity/interpolation history on teleport rather than blending across the map. Preserve Rama's deliberate LMB-repeat and Q/X edge/buffer rules; the platformer uses different shooting and movement normalization. `player`, `confluence_world.teleport_to`, action buffer, replica reset. | **Controls + motion + networking:** F5/death/teleport in each action stage cancels old inputs/effects and begins one new state without a camera/body streak or delayed queued shot. Confluence already resets interpolation; audit every other discontinuity before enabling broader interpolation. Compare key holds/edges/remaps with actual native input. Existing buffer/traversal/integration tests are starting points; a demo's constants and animation graph are not Rama's input spec. |

## Reuse choice for the next build

Continue the existing Godot/Blender/glTF pipeline. The open-game study gives
readable code for camera exclusions, movement intent, edge-triggered actions,
animation blends and teleport handling. It does not provide Deadlock-quality
characters or authorize another game's art. Copying the platformer's automatic
camera turn or normalized analog input would change shooter control semantics;
porting them merely because the code is available would be a regression risk.

The code-reuse worker separately audits TPS/Source SDK/ioquake/OpenMW/OpenRA with
file-level terms and counterexamples. These notes do not import GPL/restricted
game code into MIT runtime. If a future exact MIT component is adopted, retain
its notice, test its 4.6.3 compatibility in isolation and compare against the
current implementation before promotion. Source access and a reconstructed
engine remain distinct from commercial model, map, sound and animation rights.

The next practical design work is to select **one** still-open gate above, state
its command/scene fixture and counterexample, implement the smallest change,
and review it independently. For game feel/readability, the bounded book
sections cannot replace actual first-session observations, listening, dense
combat footage or hardware traces. No psychology, retention, balance or
commercial-art parity result follows from this reading packet.
