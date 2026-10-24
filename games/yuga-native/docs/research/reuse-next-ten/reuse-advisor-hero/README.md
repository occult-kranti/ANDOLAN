# Reusable hero hair: actual licensed donor and authoring trial

**Adopt the licensed authoring foundation; do not treat the preview as native hair integration.** The official MPFB Hair editor pack supplies a usable `straight_hair_to_shoulder` curves template and procedural material. It directly addresses the broad, disconnected ribbon shapes seen in Rama's rejected sculpt studies. Root accepted the refined black, denser fit as a **usable editable source candidate** after viewing both actuals. The rear is still uniformly dark, the lower fringe feathered/sparse, and crown flow unfinished. [Exact review](ROOT_REVIEW.json). The first sparse brown fit remains explicitly rejected. Body, crown, canonical GLB and the existing 164-bone/23-clip contract remain unchanged.

This checkpoint actually downloaded the selected source, read it with auto-execution disabled, fitted an isolated rear-guide subset, exercised the evaluated mask with an empty/recovery counterexample, and captured textured comparisons. It did not install the addon, analyze commercial client files, export a new hero GLB, bind the new hair to Rama, or qualify runtime LOD/performance.

## The one concrete source

| Item | Pinned evidence and actual result |
| --- | --- |
| Asset | Tomáš Klecer's `hair.blend`, official Hair editor functional pack. SHA-256 **`93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5`**, 19,608,264 bytes; Blender 4.4 file header. |
| Asset permission | [Official catalog](evidence/official-functional-pack-catalog.md), lines 141–146, explicitly says functional-pack assets are **CC0** and lists Hair editor. [Asset page](evidence/official-hair-pack.md) identifies Klecer and `hair.blend`/`fur.blend`. Website commit **`1f877f13e0259e83ea54615763ad40a4f18274d6`**. Full [CC0 text](licenses/CC0-1.0.txt) and [notice](NOTICE.md) retained. |
| Bounded retrieval | Normal public HTTPS Range request for only the selected ZIP member: **5,527,938 bytes in 4.28 s**, excluding unrelated fur. Local-header/member name, central-directory CRC and decompressed size verified. This is not a full-ZIP SHA claim. [Exact receipt](evidence/download-selected-member.json). |
| Actual template | **252 guide curves / 4,032 points**, source object `straight_hair_to_shoulder`, with reusable profile, curl, noise, frizz, roll and clump modifiers and material. The source contains other named short hair, brows, beard, moustache and pigtail assets; none is counted as a new finished hero. |
| Tool source | [MPFB 2.0.18](https://github.com/makehumancommunity/mpfb2/tree/b1a2dc98776da9d1eea751b159d42cf61778fe2e), commit **`b1a2dc98776da9d1eea751b159d42cf61778fe2e`**. Program code **GPL-3.0-or-later**, graphical assets/output terms separately **CC0**. No MPFB program logic was ported into the game. |
| Compatibility | Extension manifest permits Blender ≥4.2. Actual intake used **Blender 4.3.2**, read the 4.4 source with **34 node groups and zero undefined nodes**, and then evaluated/rendered the selected stack. This qualifies the exercised datablock path, not every addon operator. |
| Version mismatch found | Current addon menu requests `hair_to_shoulder`/`short_hedgehog`, while this pack contains `straight_hair_to_shoulder`/`hedgehog`. The trial uses the actual datablock directly. Do not claim that installing this rolling pack makes the current menu work unchanged. |

[UPSTREAM_SOURCES.json](UPSTREAM_SOURCES.json) records exact source revisions, read scope, URLs, hashes, failures and licensing distinctions. [Recovery and replay](REPRODUCE.md) preserves the immutable donor and final editable source separately from new captures.

## What the actual fit changes

The approved Rama comes from existing MakeHuman CC0 anatomy and the original project costume/hair/rig. The current source library already contains the precise source anatomy/rig, an editable clean hair master, original grouped-hair maps and a separately imported CC BY Godot TPS reference. The TPS character is a 145-bone robot with unapplied retarget candidates; it is useful architecture reference, not a suitable Rama hair donor. The unrigged generated Rama has rejected pitted-hair/segmentation evidence. Neither source is reclassified as finished art here.

The trial reuses **122 posterior guides** from the actual curves template. A saved editable transform scales the donor's measured 1.69455 m Human to the authored 1.85 m Rama: uniform scale **1.0917349376570533**, translation **(0, 0.033, 0.029626976444468208) m**. Root eligibility is explicitly `Y ≥ −0.015 m` and `Z ≥ 1.51 m` in donor space. The original 4,032 guide positions stay exact; this is not another generated lock mesh.

On a duplicate preview actor only, a non-applied MASK modifier hides the previously audited nine closed nape components: **3,996 original hair vertices**, all faces belonging to **Swept black hair**, with **zero mixed protected faces**. All original mesh positions/topology, UVs, crown, body and skin data remain present and unchanged. The canonical GLB stays byte-identical. The source helper Human supplies the existing curve surface; **the donor is not yet bound to Rama's animated head/neck**, so this is an authoring view, not a motion-ready replacement.

The first fit evaluates to **4,873 curves / 297,253 points**. Its four retained actuals show strands but an unacceptable sparse brown/gold veil. Root rejected that exact runtime look. The single permitted refinement changes existing profile density **0.2 → 0.6**, preserves every guide point, and adjusts existing material controls: dark warm-black colors, dielectric metallic 0 and restrained roughness/specular response. It adds no new geometry algorithm or shader implementation.

The refined stack evaluates to **14,744 curves / 899,384 finite points**, below the explicit **20,000-curve / 1,300,000-point** preview caps. Its bounds are X[−0.12848, 0.13016], Y[−0.02540, 0.12365], Z[1.47823, 1.84103] m. Setting every guide mask value false produces **zero actual curves/points**; restoring it recovers the identical evaluated position digest. [Seven actual checks and counterexample](evidence/refined-evaluated-probe.json). This is numerical eligibility, not hair/body collision or visual approval.

## Actual views and limitations

Retained original baseline: [profile](views/profile-baseline.png), [rear](views/rear-baseline.png). Rejected first fit: [profile](views/initial-profile-candidate.png), [rear](views/initial-rear-candidate.png). Refined actuals: [profile](views/profile-candidate.png), [rear](views/rear-candidate.png), with [positive capture receipt](evidence/refined-render.json) (two frames, exit 0, 179.13 s) and [root review](ROOT_REVIEW.json); no concept image is presented as engine footage.

All views use the frozen same cameras, lights, exposure and source body/crown. The baseline/first fit used 32 samples; the final two candidate frames use 64 samples, so noise reduction alone is not an artistic gain. They are **Cycles CPU authoring renders**, not native Godot skin/LOD captures or physical-GPU performance. The first take includes a disclosed suspension after one baseline to run the evaluated readiness gate; its 210.90 s wall time is not a benchmark. The final renderer requires the actual gate before any frame.

## Integration cost and next owners

This is a **contained authoring reuse**, not an engine replacement. The existing MakeHuman source and the protected Rama contract reduce fitting uncertainty. The remaining cost is three explicit work packets:

1. **Artist/material owner:** accept the final actual look or retain it only as a donor; establish a coherent scalp-to-nape mass, crown/root transition, tapered secondary strands and shoulder/cape clearance. Reuse the MPFB card-generation and bake pipeline rather than hand-writing another groom generator. Its shader/curves are not a direct glTF hair material; bake color/alpha and the supported data maps, with correct color spaces and tested strand direction.
2. **Rig/runtime owner:** convert a chosen baked/card result to an isolated mesh, bind it to the existing head/neck/upper-body contract, and retain all 164 existing bones/binds and all 23 clips. Re-run actual protected body/weapon skin/socket comparisons, 69 clip states and advancing action/interrupt/respawn sequences. The prior R1 motion result does not qualify new donor hair or collisions.
3. **Rendering/quality owner:** inspect actual textured ordinary-camera poses and matching near/mid/far LODs in Godot. Measure alpha overdraw, aliasing and memory on a physical GPU; do not ship the 899k-point authoring curves as if they were already a suitable game asset. Review all joins and readability independently before any canonical promotion.

MakeClothes' current MIT standalone source was read at `35d22919…`; its README is tested with Blender 4.5 and its custom-base workflow requires compatible base metadata/vertex groups. It is not needed for this successful direct donor-curves intake and was not installed. Adding another framework now would not resolve the actual density, material, binding or LOD gates.

## Authentic public game-inspection tools

These are useful for studying formats when a supplied readable client/package is available. They are not usable hair-asset grants or complete game engines.

| Public source actually read | Supported conclusion | This checkpoint's decision |
| --- | --- | --- |
| [overtools/OWLib](https://github.com/overtools/OWLib/tree/546efa19516d7df7ba138802d221c73ad886df28), commit `546efa19…`, MIT code | README documents DataTool against an installed Overwatch directory and the separate Blender importer. | Authentic inspection tooling; no client input, extraction or execution occurred. No Overwatch asset license was established. |
| [FabianFG/CUE4Parse](https://github.com/FabianFG/CUE4Parse/tree/990d4d7d4e0340a75a14323436d55568f1415e00), commit `990d4d7…`, Apache-2.0 code | README describes Unreal package parsing; actual `EGame.cs` distinguishes Valorant, PRE_11_2 and ValorantSource formats. | Authentic parser reference; no Valorant package, keys, extracted asset or parser execution was used. It contributes no permissively reusable character mesh here. |

Existing [REA source/fork study](../../REA_REUSE_REFRESH.md) remains the source for its tool capabilities and execution limits. A public parser license does not turn commercial game graphics or leaked source into a reusable asset library. The concrete reused art in this checkpoint is the explicitly CC0 MPFB source.
