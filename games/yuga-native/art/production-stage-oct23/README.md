# Reuse-first Rama and Lanka art stage — 23 October 2026

This packet contains **actual Blender renders and editable-scene recipes**, plus a new GPU-generated 3D source candidate. It advances source intake and presentation. It does not replace the accepted gameplay hero, finish a map, close the hair/art gate or establish Deadlock-level graphics.

## Two distinct hero paths

| Path | Actual inputs and outputs | Acceptance scope |
| --- | --- | --- |
| Existing rigged avatar | The exact accepted Rama GLB, 164-bone rig and action named `idle` at frame 1; four fixed-camera views plus a small contextual Lanka/water/diya composition | Isolated source reuse and presentation. Hero geometry and canonical files are unchanged. No new animation or replacement groom was authored. |
| New concept-to-3D source | An original generated Rama concept → official TRELLIS.2 GPU generation/export → [exact GLB](hero-source/rama-generated.glb) → two independently lit Blender views | Unrigged source intake. Imported mesh has 93,214 vertices, 96,660 triangles, one material, two images, **zero armatures and zero animation actions**. Retopology, rigging and production acceptance remain open. |

[The GPU execution packet](../../docs/research/production-stage-oct23/gpu/README.md) records the actual remote requests, provider outputs, input identity, source/model limitations and quota behavior. The GLB SHA-256 is `0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b`.

## Actual renders

- [Current avatar front](existing-avatar/hero-front.png), [face](existing-avatar/hero-face.png), [profile](existing-avatar/hero-profile.png), [rear](existing-avatar/hero-rear.png).
- [Lanka court / water / diya composition](existing-avatar/lanka-water-court.png).
- [Generated source front three-quarter](hero-source/intake/generated-front-three-quarter.png) and [rear three-quarter](hero-source/intake/generated-rear-three-quarter.png).

All seven selected originals use Blender 4.3.2, Cycles CPU, **32 samples, two threads and no denoising**. The four current-avatar views are 640 × 800, share one pose and reuse the prior review-camera contracts; the context view is 960 × 640. The new-source views are 640 × 800. [The stage manifest](existing-avatar/stage-manifest.json) and [source-intake receipt](hero-source/intake/source-intake.json) bind exact source/output hashes, camera transforms, inventories and elapsed times. These are new presentation views, not a matched before/after art-quality comparison.

The stage reuses the existing full Lanka courtyard, lotus/rock nature meshes and generated diya. A single verified [CC0 sandstone source kit](../source-kits/production-reuse-oct23/sandstone-blocks-05/manifest.json) is linked into four paving materials with a physical 3 m UV tile, sRGB albedo, Non-Color OpenGL normal/roughness, normal strength 0.3 and no displacement. All canonical input hashes remained unchanged. The relocated court and local water patch are presentation set dressing; no gameplay routes or collision were changed or accepted.

## Review and defects

The art worker inspected all seven final originals. The accepted avatar still shows coarse facial expression, broad solid hair masses, stiff parallel cloth panels and angular body/garment transitions. The new source offers an ornate layered costume silhouette, but the rear view exposes pitted/melted hair reconstruction and smeared cape/ornament detail. Front facial/hand forms remain soft and are not suitable topology/deformation evidence. Noise remains visible in these bounded CPU captures. Neither source closes finished-hero quality.

The context render shows the reused column/gate base, sandstone paving, lotus water patch and diya together. It validates this small composition and material hookup, not the full map or a navigation/collision contract. The diya's flame remains opaque source geometry and needs separate effect authoring.

A first presentation attempt put the courtyard backdrop behind the camera because the existing generator maps game Z to authoring −Y. That failed composition and a thread-override verification failure are retained in scratch and summarized in [the failure receipt](retained-failure-r1.json). One correction removed the extra rotation and raised 16 to 32 samples. The final saved scene passed [10 reopened data checks](existing-avatar/reopened-verification-final.json). Blender commands use `--python-exit-code 1`; a normal Blender process exit alone is insufficient proof that a Python check passed.

## Editable sources and next owner

[Reproduction commands](../../tools/production-art-stage/README.md) rebuild the packed editable scenes from versioned GLBs, texture maps and scripts. [The retention map](editable-retention.json) records both actual saved `.blend` paths outside Git, avoiding redundant 43.8 MB and 4.77 MB copies. Their exact hashes and sizes are in the manifests. Preserve those working scenes until a verified replacement/recovery path exists; the versioned recipes do not claim fresh-task filesystem restoration.

Next art work is an artist-controlled principal hair/face/costume refinement or deliberate retopology/rigging of the new source, with original front/rear checks before further detail or roster duplication. Preserve the [existing four-view hair gate](../hero-finish/hair-sculpt-design/clay-grouped-r1/NEXT_ARTIST_TASK.md); this packet is not an automatic C9 groom candidate. Follow with continuous contact/deformation, LODs, collisions, gameplay-distance views and physical-GPU profiling. Runtime promotion and production-completion credit remain **false / zero**.
