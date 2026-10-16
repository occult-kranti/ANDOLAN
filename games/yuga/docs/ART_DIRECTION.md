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
| `art/pipeline/`, `art/textures/`, `client/assets/heroes/*.glb` | Blender pipeline fits original proportions, hair, costumes, armour, weapons and materials to that foundation and authors nine motion clips. | Fourteen actual exports match `art/hero-assets.json`; numeric skin/pose/clip, native all-roster action and labelled clone/defeat checks passed within their documented scope. This does not establish finished character quality. |
| `client/hero-models.ts`, `world.ts`, `cast-effects.ts`, `render-kit.ts` | Original GLB loader/instance lifecycle, animation integration, gameplay overlays, minion/objective geometry and ability effects. | Runtime GLB characters and original scene/FX; each model instance needs independent bones. A fallback does not count as passing art evidence. |
| `client/assets/units/*.glb`, `art/unit-assets.json` | Seven separately authored soldier/watch/minister/king and neutral-guardian models with four clips each. Source/build/contact records are in the unit asset ledger. | Actual assets passed numeric checks and labelled idle/run/fire/defeat browser snapshots. A real camp encounter is separate native evidence. |
| `art/references/` | Generated original full-body concept sheets, with the fourteen-hero design in `art/HERO_ART_BIBLE.md`. | Reference/selection art, not gameplay screenshots or rigged model files. |
| `client/audio.ts` | Original WebAudio synthesis, no recordings or sampled music. | Gesture-enabled runtime cues. |
| DM Sans, Barlow Condensed and PlayCanvas | Existing pinned dependencies; notices embedded in production HTML. | Fonts and rendering engine. |

The key illustration is an aspirational reference. The current replacement pass addresses the shared sphere/capsule bodies with continuous anatomy, faces, layered clothing and actual skeletons. The fourteen-entry manifest records 47,648–52,548 triangles, 9–10 material sections, nine clips and approximately 3.2–3.6 MB per GLB; all fourteen file sizes/hashes matched when checked for this pass. Those values exceed the initial 15–30k/six-material integration targets. They are exported-asset counts, not proof of acceptable mobile performance. Consult the manifest for each current file and hash because exports may be revised after validation.

The current pipeline records no LOD system, facial blendshape system, cloth simulation or Draco compression. Nine clips and finite skinning establish a technical asset, not polished grips/deformation or visual parity with the illustration. Later actual-WebGL evidence covers all fourteen real models and their native actions, with separate labelled clone/defeat fixtures; the seven unit assets also have four-state presentation captures. The real camp, two-client counterplay and native 480-second finish/replay checks passed on the jungle baseline. [QA](QA.md) records exact methods and limits. These replace reliance on the earlier three-model exploratory gallery without implying every pose or human readability question is resolved.

The [hero art bible](../art/HERO_ART_BIBLE.md) supplies fourteen distinct identities and forty-two ability presentation briefs. Rama's held three-arrow release, Hanuman's real flight/landing and Sita's fixed sanctuary must follow authoritative preparation/travel/expiry state. Escort, siege and summoned units need distinct readable roles. Optional target lock adds a labelled target cue; it must retain visibility/range checks and release on manual aim rather than hiding opponents behind a large opaque marker.

These GLBs are emitted as external hashed assets. The production artifact is the entire static directory, not one self-contained HTML download. Missing asset URLs, wrong paths or a fallback model fail the art delivery gate even if the HTML loads.

Public-source research and licensing are recorded in the [pipeline evaluation](../art/PIPELINE_EVALUATION.md), [source manifest](../art/sources/makehuman/manifest.json) and [Deadlock tooling study](../art/DEADLOCK_VIDEO_AND_TOOLING.md). Public Deadlock video requests were blocked, so no footage was watched and no timestamped visual comparison is claimed. No proprietary character/animation assets were extracted.

## Day/night and civic-space revision

The new environmental pass implements original fictional Sangam City work: five circular flat plaza inlays, route markings, 26 lanterns and 24 diyas with a dawn/day/dusk/night/predawn progression tied to the 480-second match clock. These are source counts; actual construction diagnostics and screenshots remain the next browser gate. The default is a cycle, with saved Fixed day and Fixed night options. Phase and illumination are presentation only: the three lanes, eight shared solid-building definitions, target eligibility and combat rules remain authoritative and unchanged.

The implementation reuses two directional lights, cached materials/sky tint and emissive lamp surfaces, with zero point lights at either quality. Night retains ambient/fill floors; low quality and reduced motion suppress flame flicker. Raised decoration stays inside existing solid footprints or beyond the playable boundary; flat circles add no collidable rings, capture points or collectible lights. Independent source review and eight pure-cycle tests passed, including bounded values over 4,801 samples, fixed modes and the clock seam. Palette/intensity interpolation is continuous; sun, moon and star visibility uses discrete thresholds. This does not establish live night readability or renderer performance.

The [environment research](ENVIRONMENT_MYTHOLOGY_RESEARCH.md) records the selected lamp, woven night/day and courtyard/water passages actually read. The lamp passage concerns proposed consecration preparations, not proof of Diwali’s origin; the circular paving is not an authenticated sacred diagram. Contemporary Reddit discussion is separate opinion, not literary or historical authority.

The [new three-round review](NEXT_PHASE_PANEL.md) separates source integration from actual day/night, low/high and touch inspection. No deity-specific night power, darkness-based concealment or map reconstruction is claimed. The [art production plan](ART_PRODUCTION_PLAN.md) maps all fourteen heroes, seven units and forty-two ability treatments; concept images and a planned video are not implemented geometry or watched footage.

## Next art gates

1. Preserve the passed export/hash/skin/clip baseline while improving front/profile/back and combat silhouettes at actual play scale, low resolution and against every lighting phase.
2. Review authored locomotion/fire/cast/jump/defeat in-engine, weapon grips, cloth coverage and independent duplicate-hero animation. Extend aim offsets, recovery/hit/respawn and effect polish where the actual captures show gaps.
3. Measure the complete scene on supported hardware and address material/LOD/texture costs. Test readability with human players; keep ally/enemy distinctions available through labels and shapes, not colour alone. Automated source and geometry checks do not establish this result.
4. Add original music, voice and environmental sound only with provenance and integration checks. No imported commercial assets are required for this build.
