# R5 independent native hero visual review — provisional

Task YUGA-HERO-6R; native YUGA; baseline
`7162b5d0b666e4422b0bc73100e1fba947d3323f`. Original capture owner: root.
Independent reviewer: reference panel. Source capture:
`../../root/hero-capture-r1/rama-gameplay-review.json`, SHA256
`cd3b0b32b72580684fb58f2040f3188d7c8a4bb96633e2ca74c306ee0cbb6a60`.

**Do not mark the capture accepted yet.** Its inner Godot report says complete,
source unchanged and no failure, but root reports that the outer runner exited 1
on a stale HUD-notice validation condition. The combat owner is investigating.
This independent review describes the actual images; it does not bypass that gate.

The worker personally inspected all **363 consecutive rendered frame images**
using 23 derived contact sheets (18 ×16 plus 75 in five sheets), and all **25
original 1280×720 phase/low-angle/lifecycle stills** with `view_image`. All 388
original PNG SHA256 values were independently recomputed and matched the capture
metadata. Source images were not changed. This is five separate staged takes at
30 samples/s and 60Hz physics, not one fight or human OS input. Forward+ ran on
llvmpipe (LLVM20.1.2); 574.65s wall time is not physical-GPU gameplay performance.
No audio audition occurred. The old world is intentionally retained in this hero
checkpoint; the new Sangam district is a separate production/review lane.

| Scope | Direct visual and metadata finding | Decision |
| --- | --- | --- |
| Kodanda, frames0–44 | DRAWING→RECOVERING→ready appears with11/12 ammo; projectile contact is separate from warning; status text and new meter fit. | Provisional visual pass for the scoped feedback. |
| Piercing Dawn, frames45–98 | Long warning remains through draw, clears at release; three staged target contacts appear. Cooldown continues while other slots become ready. | Provisional visual pass. |
| Measured Step, frames99–119 | Hero and camera advance continuously, ribbons trail the path, recovery returns to ready; no damage receipt is falsely expected for movement. | Provisional visual pass for this unobstructed staged path. Cover interruption still requires its existing tests. |
| Guardian, frames120–287 | Dark-edged perimeter remains readable; petals do not fill the actor silhouette. Release grants+55 shield; health rises240→285; field-active label clears when authority ends. Reduced-effects replay retains boundary. | Provisional visual pass. The existing granted shield rule remains documented separately from area-bound healing. |
| Dawn Volley, frames288–362 | Three lanes during draw, two after first launch, one after second, zero after third; contacts remain separate. | The previously identified premature warning disappearance is visually corrected in these originals. |
| Lifecycle stills | Hit150/300, defeat0/300 with disabled actions/return timer, respawn300/300 and ready actions are readable. | State feedback clear. Defeated pose remains upright with raised arms and reads more like recoil; a remaining character-polish gap. |

The staggered release is also bounded by source state: frame316 has accepted
authority age0.95s, one arrow and warning visible; frame319 age1.05s has two
arrows and warning visible; frame322 age1.15s has three arrows and no warning.
At frame321 interpolated VFX age is1.15s but authority age is1.10s and warning
remains visible. This is useful counterevidence against interpolation dismissing
the final warning early. Merely inspecting the effect's smooth age would have
mischaracterized this behavior.

The three-segment HUD cue and thin timing strip are visible at1280×720, backed by
larger cooldown/phase text. Corner information panels occupy substantial screen
area; further hierarchy refinement remains an art/UX opportunity. This capture
does not establish small-screen accessibility, high-density team fights, full
map navigation, network play or a finished Deadlock-level visual product.

Sources pinned by the capture include:

- `rama_hero_hud.gd`: `fa4be323a08f3a5de5578817d2603d1373b8bd2396f88a5d2fcc8b5096464087`
- `rama_ability_effects.gd`: `c8579329c1eeae3e6d4bc9575dce29836a3490a7da5bdba8169b29ae8aae0cb8`
- `rama_motion.gd`: `09c4e72153ad5ca21e70e58c1ae691899041076bdacc8e7495870c9bd23f3301`
- `rama_ability_meter.gd`: `1aeffd0c91215faa5c019f3241808e8d73a2cc4e6283f14185bc032b010c4344`

Derived sheets used FFmpeg only to label/resize/tile originals; no simulation
or engine render was run by this worker. Exact successful command pattern:

```sh
ffmpeg -hide_banner -loglevel error -threads 2 -start_number 0 -i games/yuga-native/docs/research/hero-six-rounds/root/hero-capture-r1/frame-%05d.png -frames:v 18 -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='frame %{n}':x=8:y=340:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.8,scale=480:270,tile=4x4:padding=4:margin=4" games/yuga-native/docs/research/hero-six-rounds/reference/round5-hero/sheet-%02d.jpg
```

The volley uses `-start_number288`, five sheets and a `local frame n +288` label.
A prior attempted `select=between(...)` filter failed from unescaped commas
before writing sheets; it did not produce reviewed evidence. The corrected
whole-sequence command above produced the accepted review derivatives.

Next owners: combat/root resolve outer-runner status, root integrates the final
source capture decision, map owner supplies separate Sangam native visuals.
