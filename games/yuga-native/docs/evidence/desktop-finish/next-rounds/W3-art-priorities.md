# W3: next art priorities from accepted component originals

I opened these five original framebuffers, without running an engine or geometry
test: [day title100](../D01/W1-title-fill-day-r1/candidate/originals/00-title.png)
(`a81b65985ba2…`), [night title100](../D01/W1-title-fill-night-200-r1/candidate/originals/00-title-night-100.png)
(`4e3096c457ca…`), [day title200](../D01/W1-title-fill-night-200-r1/candidate/originals/01-title-day-200.png)
(`f45e8bac3f51…`), [overview100](../world-overview-composition/W1-native-r1/candidate/00-overview-100.png)
(`e9b637b2ef63…`) and [overview200](../world-overview-composition/W1-native-r1/candidate/02-overview-200.png)
(`a1de571206a0…`). Hashes shown are SHA256 prefixes; full source/image identities
are retained in the linked packets' receipts and capture sidecars.

These accepted **component** images all use hero `8b6cf0f4…`, motion `8c3771a3…`
and finish `6eb51ce8…`. They demonstrate the title fill and overview composition,
but predate combined smooth-crown, sash-UV and roof work. Check those accepted
changes in the next combined image before treating an old symptom as a new edit.

1. **The hero's head and upper-body silhouette need coherent sculpted masses.**
   At day/night100, the dark hair cap, bright fine strands and top ornament read
   as separate pieces. The face and upper chest remain broad, smooth planes;
   tiny chains and gold lines carry more definition than the anatomy.

   **Task:** finish the existing narrow knot-bridge and compact shoulder image
   gates first, retaining the rig/palette. If the integrated front still reads flat,
   author one bounded cheek/jaw-to-neck/clavicle form pass with clear three-quarter
   planes and retained identity. Avoid adding more ornament.

   **Art acceptance:** identical front/profile/rear rest views and one fixed cast
   must show continuous hair attachment, a legible crown, and a shoulder that looks
   attached. Day/night title100 and day200 must retain the face without hotter gold,
   an enlarged black cap, detached bridge or exposed shoulder hole. Source packets:
   [knot bridge](../../../../art/hero-finish/hair-knot-bridge-r5/SHAPE_BRIEF.md),
   [compact shoulder](../../../../art/hero-finish/s5-shoulder-armour/compact-r6/README.md).

2. **The garment silhouette still reads as thin decorated sheets.**
   The blue flank drape and long pale front panel have large straight spans;
   repeated gold motifs supply much of the richness. At title scale the cloth
   does not yet show convincing gathers, edge thickness and layered weight.
   Carry forward the separately accepted sash UV proportions.

   **Task:** revise one front-wrap/waist-to-flank junction, using the original
   [cloth authoring](../../../../art/hero-rama/build_hero.py) and current bindings.
   Add a small number of broad folds that emerge from the actual belt/gather,
   a rolled edge and a clear overlap shadow; preserve the accepted UV density.

   **Art acceptance:** matched title and three-quarter close originals must show
   folds through light and silhouette, not extra painted stripes. Keep motifs
   readable and the leg/hand outline clear. Reject a thicker rigid slab or folds
   that terminate arbitrarily. Fixed cast views assess the visible overlap;
   W5 owns motion/integration separately.

3. **The world still reads as a repeated modular board rather than a built place.**
   Overview100/200 exposes a large flat rectangular ground plane, broad uniform
   approaches and repeated blue blocks outlined by dense gold grids. The temple
   spires offer some hierarchy; the plain perimeter, dark void and exposed board
   edge still reinforce the prototype impression.

   **Task:** make one existing lane-side building a finished original module:
   deeper wall recesses, a readable entry/loggia, a substantial base and a deliberate
   connection to the paving. Carry the accepted roof forward; work on its facade
   and ground relationship. Reduce repetitive gold divisions where they obscure
   the larger volumes. Then derive two restrained silhouette variants before
   repeating them. Give this district a retaining edge or shoreline transition.
   Integration entry points are the existing architecture presets and
   [`_build_props`](../../../../scripts/confluence_world.gd); the accepted
   [roof packet](../../../../art/world-finish/roof-loggia-r1/) remains distinct.

   **Art acceptance:** the same overview100/200 and one fixed ground-level lane
   view must distinguish entry, wall, roof and base without relying on bright
   outline noise. Preserve open route/relay silhouettes and accepted overview
   framing. Improve this local module before expanding its repetition.

No flow/motion/release work is duplicated here. These stills do not establish
continuous material stability, hardware performance or Deadlock-level finish.
No asset or runtime file changed.
