# Native art and reuse review

This pass improves an original native render/animation test scene. The full
competitive game and requested commercial visual standard remain unfinished.
The [task board](PRODUCTION_TASK_BOARD.md) records four rounds per subgoal and
the [roadmap](NATIVE_PRODUCTION_ROADMAP.md) keeps the wider dependencies open.

## Implemented and verified

- Rama v4: original cobalt/ivory costume, hair and material revision on the
  preserved 164-bone rig and nine animation curves. Actual renders exposed and
  guided repairs for bow-grip placement, cape decoration, accidental hand shells
  and ten omitted calf garment polygons. Final model SHA-256:
  `6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`.
- Courtyard v2: quieter paving, deeper gate, restrained brass, warmer side light,
  darker recesses, moonlight and a fragment-based water surface. Model SHA-256:
  `1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33`.
- Closer shoulder camera framing; the offset is applied to the spring arm,
  which controls its camera child's position.
- Projectile expiry now checks its final valid travel segment and stops at its
  remaining range. Three reproduced failures pass after the correction;
  seven focused collision/range checks pass without weakening assertions.
- Final [native acceptance](../tests/evidence/native-acceptance-production-v4.json)
  passes 18 cases, including 7,380 finite/non-singular bone samples and stable
  hashes for all 12 selected runtime/source files. This is scripted headless QA.

## Actual rendered evidence

The [final studio report](evidence/art-production-v4/hero-render-review.json)
pins all 13 PNGs, the imported scene and source GLB. Forward+ ran through Vulkan
on llvmpipe, a software renderer. Representative views:

- [Three-quarter idle](evidence/art-production-v4/04-three-quarter-idle.png)
- [Run pose](evidence/art-production-v4/13-pose-run.png)
- [Defeat pose](evidence/art-production-v4/09-pose-defeat.png)

These are explicitly staged static poses. They do not prove continuous animation,
transition quality, cloth contact in every frame or physical-GPU frame rate.
The [art director's review](../art/production/ART_DIRECTION.md) accepts the bounded
defect corrections and records unresolved anatomy, rigid cloth/floating jewelry
and insufficiently distinct action poses.

The earlier v3 package's actual X11 input history is preserved separately in
[window-production-v3](evidence/window-production-v3/input-review.json).
`native-menu.png` actually shows training; `title-ready.png` is a startup splash.
Held fire visibly changed ammunition from 12 to 10; no target-hit proof is
claimed from those frames. Settings and the saved moonlight toggle were viewed.
Synthetic absolute pointer warps produced an unsuitable camera jump, so the
aimed-night capture is not evidence of smooth normal mouse aiming. Runtime code
was unchanged between this input review and the v4 model correction.

The final v4 exported PCK is
`16fc5d53c3bd1706d3b628a115e4f887d559687db31b68fd906fb9fb7cf44592`.
Its own [native-window record](evidence/window-production-v4/input-review.json)
includes the viewed [title](evidence/window-production-v4/native-title.png),
[training](evidence/window-production-v4/training-final.png) and
[held-fire result](evidence/window-production-v4/fire-final.png). The final
ammunition display changes from 12 to 10 without a synthetic pointer warp;
no target hit or smooth physical-mouse claim is made. `title-screen.png` is an
earlier startup splash and is preserved as such. The game log has no errors or
warnings. Archive checks and renderer execution are separate from Windows
execution, which has not been performed on this Linux worker.

## Research translated into usable decisions

The [systems study](research/REUSABLE_GAME_SYSTEMS.md) covers eight project groups,
three REA forks and selected sections of *Game Programming Patterns*. The sampled
forks added no demonstrated native capability; the configured upstream REA/Ghidra
lane remains appropriate. Dota replay parsers expose recorded events and support
typed, attributed event-receipt design; they are not game-engine implementations.

The [character audit](research/CHARACTER_REUSE_AUDIT.md) examines OpenLara, OpenMW,
DevilutionX, Red Eclipse and Xonotic. The chosen immediate asset is the explicitly
CC-BY 3.0 official Godot TPS character. Its [isolated import report](research/REFERENCE_CHARACTER_IMPORT.md)
records 145 bones, 56 resources including helper clips, and a real duplicate-name
import failure corrected by preserving authored names. The 21 semantic bone-map
candidates are not applied retargeting. Transferring one suitable locomotion clip
with contact/root-motion review is the next measurable reuse subgoal.

The [physics/graphics notes](research/PHYSICS_GRAPHICS_STUDY.md) record actual
Godot, LearnOpenGL and Jolt source reads and distinguish blocked/unread material.
No claim of reading every book, subreddit or commercial game's internals follows
from this bounded study. No commercial character extraction was performed.
