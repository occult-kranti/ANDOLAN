# Round 2 code build — N4 shared Lanka texture palette

15 November 2026. Product: YUGA native desktop. Baseline `7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`. Root assigned the first resource-reuse part of N4 after a source-bound proposal. This packet does not close coherent district art, native multiplayer or full-game production.

## Change and preserved contract

Added `scripts/lanka_texture_palette.gd`, and called it once per verified cached scene from `lanka_lane_gate.gd` and `lanka_water_garden.gd`. The pool compares embedded ImageTexture content by texture size, source-image dimensions/format/mipmap state and SHA-256 of all decoded pixel bytes. Only albedo, normal, roughness and metallic texture references are eligible. Null channels, empty ImageTextures and other texture implementations stay untouched. A stale-key guard rechecks a canonical image before aliasing it.

The validated gate and garden keep their existing mesh/material resources; only an exact equivalent texture reference is shared. Scene/cache instance sharing and private gate collider ownership remain as before. The process-lifetime pool retains canonical immutable textures. No binary scene, original source pack, authored artwork, source manifest, map, army footprint, collision/deck/anchor rule or accepted asset hash was modified. No sampler/material scalar/color/feature setting changes.

This executes the concrete duplication reduction requested in [N4](../../games/yuga-native/docs/research/reuse-production-continuation/NEXT_TEN.md): both self-contained caches originally contained twelve images of identical content. It avoids a binary migration or a new runtime art dependency.

## Observed result

| Census | Before | After | Difference |
| --- | ---: | ---: | ---: |
| Texture resources referenced by the two instantiated source modules | 24 | 12 | 12 fewer |
| Distinct source-image contents | 12 | 12 | Exact preserved set |
| Decoded source-image bytes including mips, counted once per actual resource | 18,874,368 | 9,437,184 | 9,437,184 bytes / 9 MiB fewer |

Weak-reference checks confirm all twelve replaced original garden texture objects are released while the cached scene and its materials stay alive. The before/after census covers these two modules, not total process memory or physical GPU VRAM. No frame-time, draw-call, upload timing or package-size gain is claimed. The serialized self-contained scene assets are intentionally unchanged.

## Executed checks and evidence

Godot `4.6.3.stable.official.7d41c59c4`, headless dummy backend, `LP_NUM_THREADS=2`:

```sh
godot --headless --path games/yuga-native \
  --script tests/lanka_texture_palette_cases.gd -- \
  --report=/workspaces/ANDOLAN/docs/research/evidence/studio/n4-resource-reuse/cases-freeze.json

godot --headless --path games/yuga-native \
  --script tools/lanka-water-garden/test_integrated.gd -- \
  --output=/workspaces/ANDOLAN/docs/research/evidence/studio/n4-resource-reuse/integrated-final.json
```

The focused resource suite checks actual Texture2D identity, weak-reference release, full geometry arrays/transforms, stored material properties/pixel contents, garden collision, exact gate collision metadata, repeated mesh/material identity, private gate colliders, cache reload, source-derived footprints, null/empty/other texture types, mipmaps, size overrides, source immutability and new-content non-aliasing. The final `cases-freeze.json` suite passed **20 checks**, process exit 0; its log and source pins are retained. The existing actual-world integration suite passed **31 checks**, including default opt-in/opt-out, source bodies, army copy isolation and blocked/open lane/wet-crossing routes; process exit 0. `git diff --check` passed.

A mutable-canonical adverse case remains **UNRUN** in headless mode: this backend did not expose ImageTexture pixel replacement to readback, so it could not establish the test's mutation precondition. The test records this limit, rather than reporting the guard as exercised. Production source-cache textures are immutable; rendered-backend mutation coverage is separate. Runtime code does recheck the canonical key before reuse.

Meaningful failed receipts are retained in the same evidence directory. `cases-r1.json` failed a fixture's comparison of stored float32 roughness to a float64 literal; it was corrected to compare the exact stored before/after value, with no material-code change. The later `cases-final.json`, `cases-adverse-r1.json` and `cases-accepted.json` retain the unsupported image-replacement precondition failures. Their numeric/resource/collision checks passed. The final fixture declares that adverse case unrun instead of treating backend readback as a code defect or weakening pixel equivalence.

No actual rendered before/after images or ordinary input were captured by this owner. The build owner is checking the combined candidate and may provide independent real-view/route evidence. Exact pixel/material/geometry/physics equality is the scope of this packet; visual quality, hardware profiling and package acceptance remain separate.

## Immutable sources and handoff

Both unchanged scene hashes still equal their existing runtime constants:

- Gate `assets/world/lanka-lane-gate.scn`: `e895e0aaef172901e445aa1e782b7ecbfbdf6b021cf13f1c311db3c60cae7d25`.
- Garden `assets/world/lanka-water-garden-candidate.scn`: `69cebe64d18b6acadc16c5b43c2d4fd4ae069793590a909f2b636ba81cc64dd0`.

Changed runtime hashes at freeze:

- `scripts/lanka_texture_palette.gd`: `eb01e36c99f64b57f519aaf8bc60cf74fa794f7b1f8af4941822442aff42e5db`.
- `scripts/lanka_lane_gate.gd`: `6e7e5b91c6ca4fed2b8372224ea010bf5af0ac46232c9ddffb66222372a18556`.
- `scripts/lanka_water_garden.gd`: `e2214cfb1c3ece2836cf05d9d5ca20f97fe0c2e9a2a2798b2bc85250677461d4`.

The focused receipt pins its final test/runtime sources. Next owners: root incorporates the focused test in its chosen verification scope; build reviewer checks the frozen combined candidate. Further N4 traversal-area expansion, serialized texture externalization, package-byte reduction and physical-GPU measurements require their own concrete assignments and evidence.
