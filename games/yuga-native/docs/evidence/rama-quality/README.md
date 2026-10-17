# Rama quality-pass evidence

This archive supports the fifteen rotating specialist work packets on
`game/yuga-native-production`, starting at `1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`.
Read [the handoff](../../RAMA_QUALITY_MILESTONE.md) and
[independent acceptance](../../RAMA_QUALITY_ACCEPTANCE.md) first.

- [Final complete component/offline run](integration/full-suite-r3/summary.json):
  sixteen suites, 777 assertions plus fifteen deterministic PCM files; unchanged
  runtime/tested sources and zero engine warnings/errors in the complete logs.
  The prior runner rejection and subsequent two-warning run are preserved.
- [Actual imported-world cases](qa/positive-r4/summary.json): 31 checks covering
  the native face, one 164-bone rig, three LOD levels, real camera selection,
  pause/focus/death/respawn and 100 resets. Earlier failed fixtures are retained.
- [Final content/provenance freeze](planning/final-native-contracts/README.md):
  native content revision 4, fifteen authoritative source pins, 42 source checks,
  242 pure Godot contracts, 118 provenance counterexamples and 23 authoring records.
- [Matched actual-world capture R2](lookdev/capture-r2/capture-run.json): twelve
  unaltered framebuffer PNGs. Its original shutdown warning is retained; no
  warning-free capture claim. Both comparison halves use the corrected flat-ground
  shadow policy. The separate eight-image floor probe isolates that policy.
- [Independent lookdev review](qa/lookdev-r2-review/review.json), followed by the
  [mandatory label correction](qa/lookdev-r2-review/label-correction-2026-10-17.json):
  actual PNG text pixels are identical. Initial image-preview diagnoses were wrong;
  the original reviews remain historical and explicitly superseded on that point.
- [Actual five-action capture](gameplay/capture-r1/capture-run.json): 363 sequential
  frames, 25 separate stills and a checked MP4; unchanged pins, natural expiry for
  every action, and zero engine warnings/errors. Separate takes and lifecycle
  stills are not one uninterrupted match or a continuous defeat/return sequence.
- [Actual LOD capture](lod/native-capture-r1/capture-run.json): six matched pairs
  at three projected sizes, plus all thirty frozen-pose camera frames and checked
  video; unchanged source/import/state identities, one rig and clean engine log.
  These establish bounded appearance evidence, not moving-pose or GPU acceptance.
- [Material-frame finding](lod/source-tangent-finding/nonorthogonal-material-frame.json):
  7,797 nonorthogonal source tangent records still require controlled rebaking and
  matched appearance review. The separate three-zero-tangent repair preserves
  the exact reviewed face payload; it does not fix all material frames.

`archive-manifest.json` pins the retained files. The repository evidence checker
validates their exact bytes, including historical failures; it does not turn
those failures into passes or compare every historical source against current art.
Capture reports pin their own runtime/import/camera/pose identities. R1 precedes
later audio and ground-policy changes and is historical, even where its earlier
catalog-only bridge was valid at creation.

Art remains LIMITED and the overall quality gate OPEN. Fixed-rate software-Vulkan
capture is not measured consumer-GPU performance. Native online/AI components
are not integrated matches/bots; human listening/feel, exact new-package OS input,
Windows execution, hardware and full-roster production remain unqualified.

Final independent render decisions:
[gameplay sampled review](qa/gameplay-r1-review/review.json) covers all 25 stills
and 54 individually opened adjacent frames; all 363 raw-frame hashes were checked.
[LOD review](qa/lod-r1-review/review.json) covers all six pairs and every camera
frame. Both results remain LIMITED. The verified glint in LOD frames 9/20 at
182.3 projected pixels needs a controlled near/mid comparison; detailed continuous
motion/contact and lifecycle observations remain incomplete. No final art gate
was closed by this checkpoint.
