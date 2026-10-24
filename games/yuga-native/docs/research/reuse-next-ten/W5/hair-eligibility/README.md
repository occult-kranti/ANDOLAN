# Isolated hair derivative — native motion eligibility

The corrected W3 r5 derivative passed a bounded headless comparison against its exact canonical ancestor. Both files were loaded with `GLTFDocument.append_from_file/generate_scene`, then configured with the unchanged accepted Rama controller and the same external 23-clip production library. No canonical GLB, LOD, manifest, material or roster was changed.

- Ancestor SHA: `db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e`.
- Isolated candidate SHA: `85c16967bdec0eeb6cf4c5b331fe07d236df114ebf3730937d97300e4dda0777`.
- Motion SHA: `6261a692308e84863dbac4ff049fb7855cc8c5ebf70d8ec844b1dfb2225e53c1`.
- Shared runtime library SHA: `1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8`.

[hair-runtime-r5.json](hair-runtime-r5.json) records **12/12 passing gates**, headless exit 0. Each of the 23 existing clips was sampled through the production controller's `_sample()` at normalized times 0, 0.5 and 1, producing 69 authored pose states. Every state compares all **193,951 protected body/weapon vertices** and **16,343 hair vertices** after skinning against the actual imported bind arrays. Protected posed positions differ by exactly 0 m. The maximum hair displacement is 0.019761266–0.019761311 m across these states; all are finite and stay inside the original 3 cm editor displacement budget.

Separately, 278 advancing 60 Hz frames cover primed aim, primary draw/hold/release, hit interrupt/recovery, death, respawn/recovery, piercing draw and cancellation. Both imports have exactly equal transforms for all 164 bones, the same action/stage/release state, and zero difference in five sockets and sampled actual bowstring/distal-finger skin. These are synchronous bare-stage comparisons; world collision and full gameplay input are not exercised.

[hair-runtime-stale-r4.json](hair-runtime-stale-r4.json) is the expected exit-1 negative: the earlier r4 candidate, whose positions and skin were otherwise the same, is rejected before import because it does not match the corrected r5 hash. This prevents the normal-bounds/tangent repair from being silently omitted. The positive and negative logs are retained here. The helper pins itself and rechecks all source bytes after assessment.

Run from `games/yuga-native` with a fresh output path after reconstructing W3's exact isolated candidate:

```sh
godot --headless --path . --script res://tools/hero-family-reuse/hair_runtime_eligibility.gd -- --candidate=/workspace/scratch/reuse-next-ten/W3/exact-glb-r5/rama-hair-sculpt-isolated.glb --output=/workspace/scratch/w5-hair-runtime-replay.json
```

This passes native rig/skin/clip eligibility for the isolated derivative. It does **not** measure hair-to-body penetration, shader/normal appearance, textured seams, ordinary-scale visual quality, secondary shader deformation, runtime LOD transitions, hardware performance or finished hero quality. W3's independently checked raw invariants and Blender clay views remain separate evidence. Actual textured native views and LOD gates are still required before any canonical art decision. The previously rejected generated-source bindings remain rejected.
