# Independent environment review

**Result: the corrected courtyard is a useful presentation improvement; the environment quality target remains LIMITED.** This review covers eight baseline/R1 pairs and nine standard R2 views, plus an independent headless run on the actual courtyard. It does not accept Deadlock-level fidelity, the Confluence map, continuous motion, or physical-GPU performance.

The source baseline is `38d11148fe69b184e981164c8a71387c91dc64c5`. The current working changes have their exact source hashes in the receipts below. All images were viewed through the image tool as their original PNGs.

## Visible findings and corrections

| Finding | R1 observation | R2 observation / current status |
| --- | --- | --- |
| Floating architecture | In the title and both hero portraits, planter, column and diya feet hang beyond the old floor edge. | The new terrace visibly supports the shown feet. The correction is visible in the title and both near portraits. Closed within these fixed views. |
| Sky horizon discontinuity | A straight darker horizontal strip cuts across title/portrait backgrounds and the overview horizon. | Matching upper/lower sky energy removes that strip in the inspected day/night portraits and overviews. The water edge remains a real separate surface. Closed within these views. |
| Surface orientation | Independent helper probes found all 32 lintel faces, all 64 sampled arch front/back faces and all 32 southern rosette faces facing inward. Double-sided materials hid missing-face symptoms. | The district owner corrected only local triangle order. All sampled faces now point outward; all 43,008 actual mesh triangles agree with their shading normals. See retained reproduction and corrected numerical receipts. |
| Play-space readability | Added arches improve title framing. Northern ornament stays on existing piers; all five turquoise training targets remain visible in day/night gameplay views. | No added target obstruction is visible in R2. Actual physics checks establish the added presentation does not change the existing movement or collision objects. This is not a complete navigation/playtest result. |
| Night practicals | The new diya flames read as bright dots without a convincing local warm pool on their bases. | R2 still shows this limitation. A later four-light implementation passes the independent numerical budget/lifecycle checks, but is **not present in the R2 images**. Its separate rendered trial remains required. |
| Remaining fidelity | Large uniform paving, repeated roof beams and trim, a stepped block skyline and broad empty background planes make the arena read as a developing game space. | These remain visible in R2. More repeated decoration alone will not establish the requested target: material scale, silhouette variation, inhabited depth and lighting hierarchy need authored treatment and matching review. |

The title background is more composed than baseline, and the seam/floating corrections make it coherent. Night remains readable, with clear targets and a visible hero silhouette. There is no basis here for approving final environment art or the entire game.

## Independent numerical evidence

The durable suite is [hero_environment_adversarial_cases.gd](../../../../tests/hero_environment_adversarial_cases.gd). Its final source hash is `a0d5406e594973e4906596813d2d402503a7f601d6eb342e8a3c2555b90c18a2`.

The [latest actual-scene run](numerical-r4/report.json) passes **27/27 assertions**, Godot 4.6.3 exits 0, and the captured log has no warnings or errors. Source snapshots are retained alongside the receipt. The previous 23- and 24-assertion cuts remain historical evidence of the geometry correction and added pier-back checks, respectively.

- Every sampled lintel, arch, south/north rosette and cylinder normal points outward. No emitted triangle has opposite mean shading normal, nonfinite data or zero area.
- New presentation stays south of the playable boundary, below the paving overlap, or on occupied northern piers. All **48 northern relief centres** ray-hit existing authored solid pier geometry.
- The actual courtyard contains **38 collision/shape records**. Their identities, transforms and collision settings remain exact through **12 day/night settings cycles**, district removal and rebuild. The actual southern boundary raycast remains exact.
- Repeated configuration preserves the visual owner. Removing and rebuilding it preserves the generated mesh bytes. No collision, navigation region/link or per-frame callback was added by the district.
- Opaque materials retain normal depth testing. This detects depth-disabled presentation, but does not replace a camera-motion or overdraw review.
- The later four-practical version keeps exactly **four** finite, outboard, unshadowed lights with range at most **3.4 m**. All four identities persist across phase changes; daylight has zero energy and hidden lights, while night energy is positive and at most **1.05**.
- Mesh geometry is unchanged by that light addition: **43,008 triangles**, vertex/normal digest `ed8fca450c6cb39898c3771c211180818212e4bb388dc2b4ebedf402cadc4bb2`.
- Scene teardown rejects further atmosphere writes and releases controller references with explicit missing-object reporting.

The final numerical sources are district `09c6447f36a9eba2d0898f3db846fedb45693b9c9d56f3212bc2ec537de56431`, atmosphere `174c02b7fd0733eae17be9cff45713b79feaf2e6f7814e43c27f0206680708fe`, and courtyard `0a904ebe3de420c80ad436aabf074da159251ed051048c7488c37cd7d0af1128`.

## Inputs and retained limits

[R1 input verification](r1-input-verification.json) checks all 31 archived files across the baseline/candidate capture archives, all sixteen image hashes, successful producer receipts and eight exact camera/player/phase/resolution pairs. Multiple rendering variables intentionally differ, so this is not a controlled single-variable material experiment.

[R2 viewed inputs](r2-viewed-inputs.json) pins the nine original standard frames actually inspected and the frozen source project. These frames use district `02d2665c7a88dbbeeecfe4718689609f816b5ba09d5c87550203350c658eb913`, with the corrected terrace/winding but **zero new practical lights**. The full producer was still capturing ability/motion views when this visual inspection occurred; this review does not invent a terminal-completion result. The parent capture archive supplies that separate receipt when finished. The ninth night-title frame has no R1 matching frame.

The original inward-face reproductions remain in [r1-defects](r1-defects/). Those small diagnostic programs intentionally print observed counts and exit 0; they are reproduction data, not passing outward-orientation tests. The later durable test asserts the correct orientation and passes on the corrected source.

Next owner: the renderer and independent art reviewer should inspect the later four-practical day/night captures for restrained warm pools, light leakage, target readability and unchanged daytime appearance. The roadmap should retain broader environment art and hardware profiling as open gates.
