# Play Hanuman in Confluence

Extract the Confluence ZIP, open `yuga-rust.html`, select **Hanuman · Gada**, and choose **Play lane match**. **Hanuman practice** opens a small courtyard with three enemies and one ally. A private room can seat two or six people. The same embedded skinned model plays the Sun and Moon heroes in each mode. [Download Confluence](../../../yuga-rust/downloads/yuga-rust-confluence.zip?raw=true) · [Room setup](../../../yuga-rust/README.md)

## Reading an encounter

Move with WASD and aim with the pointer. Hanuman can punish an enemy in front, protect a nearby ally, escape a lane through a gap, or catch someone pursuing him. His tail attack targets the space behind his facing direction. The table gives the elapsed time from input to the first effect on the 20 Hz authority. [Ability definitions](../../assets/design/hanuman-ability-kit.json) · [Combat rules](../../../yuga-rust/src/combat.rs)

| Input | Ability and animation | What happens |
| --- | --- | --- |
| LMB | Vajra Gada · `fire` | After 0.25 s the forward sweep deals 34 damage within 3.5 m. |
| Q | Vajra Kavacha · `cast2` | After 0.35 s the forward fan grants a 48-point shield for three seconds to Hanuman and qualifying allies within 5.5 m. Cover separates recipients. |
| E | Maruti Udayana · `cast1` | Leave after 0.20 s. Travel for up to 0.45 s over a maximum 8.5 m, shortening the route at solid cover. |
| C | Lanka Dahan · `tail_sweep` | After 0.45 s the rear sector deals 28 damage, then 8 damage per second to enemies staying in the embers for up to two seconds. |
| X | Mountain Pulse · `mountain_pulse` | Raise the mountain for 0.70 s. It lands 0.45 s later. The pulse deals 65 enemy damage or restores up to 45 allied HP in a seven-metre disk. Cooldown is 30 s. |

### Aim Mountain Pulse

Click **Mountain Pulse** in the action bar, then move the pointer over the floor. A gold center within the seven-metre ring means the target is eligible to cast. A crossed center marks an unavailable landing. The status line distinguishes excess range, cover, ground contact and an action already in progress. Point at a new location before committing. **Esc** cancels. **X** still quick-casts at the current aim point.

The aim center must be within 14 m of Hanuman. The render draws the footprint specified by the canonical kit. The local Wasm read-only query checks the same Rust method as the committed cast, using the player's most recent authoritative position. This preview is private. Once the room accepts the cast, all clients see the committed ground mark. Recipients may move out of the mark or behind cover before impact. The room decides whether each unit is hit or healed at landing. [Shared spatial check](../../../yuga-rust/src/combat.rs) · [Input and HUD](../../../yuga-rust/web/main.ts) · [Ground graphics](../../../yuga-rust/web/scene.ts)

### Practise with feedback

The practice counter tracks a damaging mace hit, an ally shield, a completed vault, a tail hit and a mountain impact that affects a target. They can be demonstrated in any order. Empty swings and self-only shielding leave their techniques available. At the end of a drill the result reports the number demonstrated. Restarting clears the count. [Practice coach](../../../yuga-rust/web/practice-coach.ts)

## Art and release lineage

The title uses an original image-generated Hanuman portrait. The illustrated eye, copper mane, gada and brushed tail set the look-development target. During play, the actor is a real-time joint-skinned GLB with embedded material maps. The match advances the mapped action against Rust release, contact and recovery markers. [Title illustration and prompt](design/PORTRAIT.md) · [Playable model](models/hanuman-enhanced.glb) · [Base rig and motion source](../four-hero-motion/models/hanuman.glb)

The finished actor adds one weighted guard-hair surface to the 17 base skin surfaces. Its 167 joints drive the muzzle, brows, copper mane, tail, gada and cloth through the 11 embedded actions. The playable model occupies 14,418,404 bytes. [Model build receipt](evidence/build.json) · [Sculpt and weights](design/SCULPT.md) · [Tail recoil](design/TAIL_MOTION.md)

The packager selects the finished model once for every local and remote Hanuman and preserves its embedded animation data. Older source trees without the finished file run the existing Rust exporter against the original model and Godot motion resource. The build rejects invalid GLB headers, missing skins and missing required actions. The release's `build.json` lists the chosen edition, clip names, cover MIME and asset hashes. The title retains a PNG fallback for older source trees. [Packager](../../../yuga-rust/tools/build_web.py)

## Reproduce the release check

From `games/yuga-rust`, with Node dependencies installed at the repository root, Rust's `wasm32-unknown-unknown` target and `unzip` on PATH, run:

```sh
cargo test --locked
python3 tools/build_web.py
node tools/test_hanuman_release.mjs --zip dist/yuga-rust-confluence.zip
node tools/test_practice_coach.mjs
node tools/test_hanuman_title.mjs
```

The release check opens the actual ZIP, decodes the playable HTML's model, title and Wasm, checks their digests, and exercises the identical room-worker module. Four modes cover 28 independent casts and 5,376 repeated previews. It tests the exact range boundary, blocked sight, airborne origin, invalid slots, nonfinite input and read-only aiming. Browser evidence covers the rendered model and physical input separately. [Release validator](../../../yuga-rust/tools/test_hanuman_release.mjs)

The final 30,698,613-byte ZIP has SHA-256 `91315c2c9ea866dafda4ef10732157b456e237c538c83b1aba614555776a7000`. A real packaged host ran a 3v3 match and a duel, reached nine concurrent connections across rooms, delivered all 144 commanded frames and returned to zero rooms after disconnect. Environment-specific frame intervals appear in the receipt. [Package and rules proof](evidence/packaged-game.json) · [Host stress test](evidence/packaged-rooms.json)

At 1280 × 720 and 390 × 844 the title displays the illustrated face and keeps the hero chooser and both launch buttons inside the viewport. The narrower image documents the title crop on a desktop browser at phone width. The playable controls target a keyboard and mouse. [Desktop title](media/title-1280.png) · [Narrow title](media/title-390.png) · [Chromium crop and control measurements](evidence/title-qa.json)
