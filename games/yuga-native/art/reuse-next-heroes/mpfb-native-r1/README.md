# MPFB cards: actual native pipeline, rejected first appearance

This packet **executes the existing MPFB card and atlas tools**, bakes real donor coverage, exports a skinned hair asset and attaches it to Rama's existing native skeleton. The new appearance is **not accepted for the game**. Both sparse-card takes and the final opaque-underlayer comparison are retained; the canonical hero stays unchanged.

The input is the [previously accepted editable donor direction](../../../docs/research/reuse-next-ten/reuse-advisor-hero/README.md), master `8cd254da…`. This is a source refinement of the existing Rama with the CC0 `straight_hair_to_shoulder` donor by Tomáš Klecer. It contains no commercial-game geometry or leaked code. [Notice and exact upstream code](NOTICE.md).

## Actual reuse and outputs

| Input / existing tool | Executed result |
| --- | --- |
| MPFB `haircardservice.py`, pinned `b1a2dc98776da9d1eea751b159d42cf61778fe2e` | Existing k-means and arc-length average → 72 cluster ribbons, 2,304 vertices, 2,160 triangles, one surface. |
| MPFB `hairbakeservice.py` | Exact atlas-grid and ray-portal helpers → actual 1024×1024 donor coverage bake, 24 Cycles samples, two CPU threads, 134.89 seconds. |
| Existing refined 14,744-curve / 899,384-point donor | No original guide changes, body/crown edits or replacement skeleton. The image contains measured coverage plus explicitly authored warm-black albedo, **not a bake of the donor's original BSDF/color**. |
| Existing 164-bone Rama + 23 external clips | Hair-only GLB has unit weight on `head`; the native adapter discards the duplicate carrier's inverse binds and derives them from the canonical native rig. No second animation owner. |
| Existing nine-nape source mask / original-byte carry method | Exactly 7,344 nape triangles suppressed in a scratch comparison body. All 34,977,924 original binary payload bytes stay exact; only a filtered index accessor is appended. No duplicate 36 MB body is committed. |
| Existing R1 opaque sculpt `85c16967…` + Blender PROJECT Shrinkwrap | One separate layered comparison. Only the audited 3,996-vertex / 7,344-triangle target participates; 82 card vertices move at most 27.54 mm, 2,222 stay unchanged. Zero inverted/collapsed triangles, maximum edge ratio 2.50; UVs and weights exact. |

[Portable cards](candidate/mpfb-nape-cards-near.glb) are `a7add6b73b690f9fd8e5c88d7d0eaa36e248ad3368a1bdbc2a06d5d73bd038d9`, 1,202,280 bytes. [Coverage/albedo atlas](candidate/mpfb-nape-albedo-alpha.png) has byte-exact R1 measured alpha and RGB `(29,22,18)` encoding the intended linear `(0.012,0.008,0.006)`. [Layered cards](candidate/mpfb-nape-layered-cards.glb) are `570c884c20327e01b4a90729f4209be047da6d2a1747a6678a3d8471b6dd02ae`, 1,202,284 bytes. Both remain inactive candidates.

## What was actually reviewed

Fourteen **original native** 960×540 images use the qualified X11 Forward+ software raster runtime and fixed cameras/light:

1. [Eight matched baseline/candidate views](views/native-r1/) cover rear/profile at ordinary and close distance. Root and W1 rejected the sparse, stippled curtain and exposed nape.
2. [Three material-correction views](views/native-r2/) keep the same geometry/atlas and replace alpha hash with alpha-scissor + MSAA alpha-to-coverage. Coverage and root/fringe defects remain; rejected again.
3. [Three layered views](views/native-layered-r1/) combine the retained R1 opaque source with the projected cards. Ordinary silhouette returns, but broad leaf-like masses dominate and sparse card strands remain near the neck/root. W1 independently rejects promotion; additional geometry/overdraw has no accepted visual gain.

No 120-frame rendered motion take was run: the visible defects stopped that gate. The driver is prepared, but **zero rendered animation frames** belong to this packet. Native headless eligibility separately sampled 23 clips at five times (115 states) and 300 advancing draw/release/interruption/run/turn/death/recovery steps. These prove finite skin behavior, not neck/collar/cape contact or beautiful motion. No new mid/far LOD, game-camera integration, ordinary input, physical-GPU performance or complete-hero acceptance is claimed.

[Current 10-control eligibility](evidence/native-r4-current-eligibility.json) and [separate layered 10-control eligibility](evidence/layered-native-probe-r1.json) belong to their own source hashes. W5's independent 32-control review is separate and applies to the unprojected cards/adapter it pinned; it must not be borrowed for the projected geometry. W1's raw audit is linked from the [worker handoff](../../../docs/research/reuse-production-continuation/W3/README.md).

## Meaningful failed runs retained

- R1 wrote intended linear albedo into a Non-Color byte texture. W1 caught native sRGB darkening. Changing metadata alone in R2 retained wrong `(3,2,2)` pixels; R3 explicitly encodes sRGB and externally verifies `(29,22,18)` with unchanged alpha. No coverage rebake was needed.
- The first native carrier gate rejected 3.61 μm position / 2.01e-5 basis round-trip drift. The repair **uses canonical inverse binds**, instead of calling re-exported values exact. Source carrier identity has an explicit 0.1 mm / 1e-4 tolerance; actual canonical rest reprojection is checked below 1 μm.
- W5 found attaching to a pre-positioned hero left hair in source/world coordinates. The adapter now places the temporary carrier in the model's current world frame before reparenting. Independent pre-positioned and attach-then-move covariance pass; the wrong-head negative is rejected.
- The first layer-fit finished geometry/export but its receipt failed on a NumPy boolean. The sole correction converts that field to a Python boolean. The first failure log remains; the corrected run produced the same GLB geometry.
- Generic fixture labels originally said “masked” even for the explicitly pinned opaque R1 layered body. [The context correction](evidence/context-correction.json) names the actual source. Original receipts are retained, not silently rewritten; future driver labels are corrected.

The first exporter reports unavailable optional Draco (compression was not requested) and a same-image sampler warning. Neither is hidden or presented as a clean warning-free export. Native raster captures themselves completed with exit 0 and no script/engine errors.

## Next art change

Use this pipeline and its failure witnesses. The accepted dense editable donor remains the source direction. An artist must solve card orientation/coverage and a coherent root-to-nape volume in the same ordinary-camera view; copying the old broad panels under the sparse cards does not finish that work. Inspect donor card placement, coverage per UV cell and silhouette before more material tuning. A revised source must then pass native continuous head/neck/cape contact, 23-clip behavior and separate LOD/popping review. Preserve the body, crown, rig and existing action timing.

See [reproduction](REPRODUCE.md), [tool code](../../../tools/hero-donor-groom/mpfb_native/) and [manifest](manifest.json). Derived `.blend` masters remain in scratch and are reproducible from the already archived source plus these exact tools; no new unique hand-edited data is omitted.
