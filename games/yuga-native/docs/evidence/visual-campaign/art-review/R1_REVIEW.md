# Independent art-direction review — first candidate

Reviewer: `/root/visual_art_review`, AI specialist role 15. This is an AI visual
review, not a human player study or a commercial-game comparison experiment.
Source base: `38d11148fe69b184e981164c8a71387c91dc64c5`; candidate is the
per-file-pinned working-tree snapshot in `capture-candidate-r1/candidate-origin.json`.

**Decision: retain the visible improvements as work in progress; reject R1 as a
finished hero or environment and do not claim Deadlock-level quality.**
This first review is retained even after the forthcoming corrected capture.

## Evidence actually inspected

All eight original baseline PNGs and all eight corresponding R1 candidate PNGs
were individually opened with `view_image`, at their original 1280 × 960
resolution. No contact sheet or generated concept image substituted for a raw
frame. The renderer records Godot Forward+ on llvmpipe, successful exits and
no capture warnings. The same-camera comparison establishes equal camera,
player transform, lighting phase and resolution, not a single-variable
material experiment: scene, lighting and material changes coexist.

`R1_inputs.json` records every inspected file, hash, bytes and archive match.
The original capture reports and comparison remain in the sibling capture
directories. One released Q frame cannot qualify continuous motion, timing,
impact anticipation, audio or team-fight readability.

## Visible findings

| Area / actual views | Observation | Decision and observable acceptance condition |
| --- | --- | --- |
| Title, `01` | New arch, plants and lamp stands give Rama a setting. The left menu remains clearly separated; the hero and bow retain their readable silhouette. Several rear bases and stands visibly end above the floor/horizon band. | Keep the composition direction; reject floating bases. Corrected front and oblique views must show every visible base meeting a believable supporting surface without a background-colored gap. |
| Hero, `02–03` | Indigo/gold costume identity survives. Bright broad sheen is reduced; bare torso is calmer. Face remains comparatively smooth and neutral, with little plane/expression detail. Hair still reads as thick, evenly grouped ropes; cloth folds retain a heavy sculpted appearance. | Surface polish is a bounded improvement. Hero quality stays open until close front/three-quarter face views show coherent eyelids, lip/chin planes and expression, and moving hair/cloth preserve a designed silhouette rather than a solid curtain. A still cannot establish deformation quality. |
| Back view, `04–05` | The prominent white bands across the back sash are reduced, helping the cloth separate from gold and bare skin. The blue drape remains recognisable. | Accept reduced glare only for these inspected views. Require orbit and motion checks for seam glints, fold collapse, self-intersection and material changes across LOD boundaries. |
| Architecture, `01–07` | Arches and ornament strengthen the setting, and added border motifs enrich the main gate. The existing stepped background towers, blunt flat horizon band, repeated roof beams and nearly uniform paving still read as a test arena. | Reject a finished-world claim. Next environment pass needs a layered skyline, grounded structure and authored edge/wear variation; the approach route and target silhouettes must remain clear. More repeated ornament alone will not meet that condition. |
| Day light, `02/04/06` | Cooler sky and softer-looking floor shadow are visible. The courtyard is legible, but pale paving occupies most of the frame with little material/shape hierarchy. | Preserve navigation contrast while developing near/mid/far light hierarchy. Do not hide unfinished silhouettes in fog or bloom. |
| Night light, `03/05/07` | Blue ambient fill keeps targets and major geometry readable. Practical lights are small points; they do not yet create a convincing chain of warm pools or reveal the hero's facial planes. | Readable but unfinished. Require discernible warm pools around visible lamps, a readable hero face and clear dark-background separation without lifting the whole scene to daylight values. |
| UI, `01/04/05/08` | Title hierarchy and primary action are readable. Training HUD retains clear pause, objective, health and five action slots. The ability strip is text-heavy; small target health labels compete with their discs, and the broad flat health strip has limited hierarchy. | No visible regression in these desktop frames. Final UI remains open: distinctive ability glyphs, cooldown/disabled states, hit/aim feedback, remapping and smaller-screen inspection are still needed. This review did not test interactive focus or input. |
| Q release, `08` | Candidate adds larger gold crescent strokes around the archer and shot path; target and HUD remain visible in this single quiet scene. | Improved release silhouette is visible. Windup, travel, hit, recovery, all other abilities, reduced-effects options and overlapping combat need separate captures before effect clarity is accepted. |

## Highest-impact production work still open

1. Finish hero sculpt and surface art together: expressive face planes, authored
   hair masses/strands, convincing fabric thickness/folds, and controlled gold
   highlights. Keep the existing costume identity as the anchor.
2. Replace the horizon/tower test silhouettes with a coherent layered district;
   ground all architectural and decorative elements and make material scale
   consistent between paving, columns, roofs and plants.
3. Author a lighting hierarchy for the hero and combat path in both phases;
   preserve threat visibility while giving lamps, shadows and atmosphere a
   spatial purpose.
4. Review actual movement, shooting and all ability sequences; static screenshots
   cannot demonstrate the responsiveness and animation finish of the target.
5. Establish a small set of licensed reference frames and matched presentation
   conditions before any specific quality comparison. This review inspected
   YUGA only; no asset count or test assertion is a visual parity measurement.

Known corrective work on backdrop foundations, horizon and generated-surface
winding is reported by the implementation team. It is **not accepted by this
R1 review**; the corrected pixels must be inspected separately.
