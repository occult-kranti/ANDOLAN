# Sangam City: visual direction and asset ledger

## Direction

A confluence of old civic space and a near-future Indian metropolis: sandstone arcades, temple-inspired stepped roofs and ghat water on one route; a ceremonial central avenue; glass towers, metro silhouettes, trees and garden courtyards on the other. Gold and cyan team markings coexist with hero-specific cloth, crests and weapons. Ancient and modern references are a fictional composition, not a surveyed reconstruction of any particular sacred site.

The lobby uses peacock-dark surfaces, warm ivory text, brass accents and a large illustration. Hero selection exposes all fourteen choices, with role, difficulty, health, weapon and three complete ability descriptions. The 3D inspection view must show the selected actual model, separately from the concept sheets. In combat the hierarchy is objective/clock, aiming space, health/abilities and upgrades. Menus use native modal dialogs and visible keyboard focus; motion and graphics quality are independent preferences.

## Asset origins and implementation

| Asset | Origin | Runtime status |
| --- | --- | --- |
| `client/assets/confluence-keyart.png` | OpenAI image generation in this task; original archer, many-rayed strategist and mace bearer above the fictional city. No commercial-game image supplied as input. | Lobby illustration, explicitly labelled concept art; not a gameplay screenshot. |
| `client/scenery.ts` | Original procedural geometry and authored palettes: shared-map solids, architecture, skyline and lane decoration. | Actual rendered city. |
| `art/sources/makehuman/` | Pinned MakeHuman bundled CC0 anatomical mesh, adult morphs, native rig and weights; source URLs/hashes/licences in its manifest. No MakeHuman application code is included. | Licensed foundation for authored hero GLBs; it is not original anatomy or a commercial-game extraction. |
| `art/pipeline/`, `art/textures/`, `client/assets/heroes/*.glb` | Blender pipeline fits original proportions, hair, costumes, armour, weapons and materials to that foundation and authors nine motion clips. | Fourteen actual exports have file sizes/hashes matching `art/hero-assets.json`. Full skin/pose/clip verification and final browser acceptance remain separate gates. |
| `client/hero-models.ts`, `world.ts`, `cast-effects.ts`, `render-kit.ts` | Original GLB loader/instance lifecycle, animation integration, gameplay overlays, minion/objective geometry and ability effects. | Runtime GLB characters and original scene/FX; each model instance needs independent bones. A fallback does not count as passing art evidence. |
| `art/references/` | Generated original full-body concept sheets, with the fourteen-hero design in `art/HERO_ART_BIBLE.md`. | Reference/selection art, not gameplay screenshots or rigged model files. |
| `client/audio.ts` | Original WebAudio synthesis, no recordings or sampled music. | Gesture-enabled runtime cues. |
| DM Sans, Barlow Condensed and PlayCanvas | Existing pinned dependencies; notices embedded in production HTML. | Fonts and rendering engine. |

The key illustration is an aspirational reference. The current replacement pass addresses the shared sphere/capsule bodies with continuous anatomy, faces, layered clothing and actual skeletons. The fourteen-entry manifest records 47,648–52,548 triangles, 9–10 material sections, nine clips and approximately 3.2–3.6 MB per GLB; all fourteen file sizes/hashes matched when checked for this pass. Those values exceed the initial 15–30k/six-material integration targets. They are exported-asset counts, not proof of acceptable mobile performance. Consult the manifest for each current file and hash because exports may be revised after validation.

The current pipeline records no LOD system, facial blendshape system, cloth simulation or Draco compression. Nine clips and finite skinning establish a technical asset, not polished grips/deformation or visual parity with the illustration. Exploratory actual-WebGL captures exist for Rama, Hanuman and Sita in `docs/evidence/exploratory-priority-*`; their scope is a gallery of three models, not final all-roster gameplay acceptance. [QA](QA.md) tracks the full asset, native-motion, clone-isolation and final-combat gates.

The [hero art bible](../art/HERO_ART_BIBLE.md) supplies fourteen distinct identities and forty-two ability presentation briefs. Rama's held three-arrow release, Hanuman's real flight/landing and Sita's fixed sanctuary must follow authoritative preparation/travel/expiry state. Escort, siege and summoned units need distinct readable roles. Optional target lock adds a labelled target cue; it must retain visibility/range checks and release on manual aim rather than hiding opponents behind a large opaque marker.

These GLBs are emitted as external hashed assets. The production artifact is the entire static directory, not one self-contained HTML download. Missing asset URLs, wrong paths or a fallback model fail the art delivery gate even if the HTML loads.

Public-source research and licensing are recorded in the [pipeline evaluation](../art/PIPELINE_EVALUATION.md), [source manifest](../art/sources/makehuman/manifest.json) and [Deadlock tooling study](../art/DEADLOCK_VIDEO_AND_TOOLING.md). Public Deadlock video requests were blocked, so no footage was watched and no timestamped visual comparison is claimed. No proprietary character/animation assets were extracted.

## Next art gates

1. Complete the fourteen-entry export/hash/skin/clip verification and inspect actual front/profile/back and combat silhouettes, including at low resolution and against each district's background.
2. Review authored locomotion/fire/cast/jump/defeat in-engine, weapon grips, cloth coverage and independent duplicate-hero animation. Extend aim offsets, recovery/hit/respawn and effect polish where the actual captures show gaps.
3. Measure the complete scene on supported hardware and address material/LOD/texture costs. Test readability with human players; keep ally/enemy distinctions available through labels and shapes, not colour alone. Automated source and geometry checks do not establish this result.
4. Add original music, voice and environmental sound only with provenance and integration checks. No imported commercial assets are required for this build.
