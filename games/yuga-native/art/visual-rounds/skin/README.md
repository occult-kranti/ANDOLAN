# R2-01: skin sampling candidate

Source pin: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.

Actual accepted day/night face originals still show fine dots on the ear and
neck; the final day gameplay anchor shows chest dots. The large shadow patches
had already improved under depth bias 0.2 / normal bias 0.35. The retained source
diagnosis measured a nearly flat normal map and passed the skin domains through
Mikk diagnostics. That weakens a normal-map explanation for large patches, but
does not establish the cause of all remaining stippling.

New inspection found that the 512x512 finish roughness map has high-frequency
grain (grayscale range 128–168) with mipmap generation disabled. Its original
skin input uses mipmaps. `roughness-mips` changes only that import parameter.
`sss-off-diagnostic` separately disables only the current skin scattering
feature to isolate its contribution. Neither is represented as a proven fix.
The accepted shadow baseline and every PNG/mesh byte remain unchanged.

From the repository root:

```bash
python3 games/yuga-native/art/visual-rounds/skin/stage_candidate.py --variant control --output /workspace/scratch/visual-round2/role-01/control
python3 games/yuga-native/art/visual-rounds/skin/stage_candidate.py --variant roughness-mips --output /workspace/scratch/visual-round2/role-01/roughness-mips
python3 games/yuga-native/art/visual-rounds/skin/stage_candidate.py --variant sss-off-diagnostic --output /workspace/scratch/visual-round2/role-01/sss-off-diagnostic
python3 games/yuga-native/art/visual-rounds/skin/test_candidates.py
```

The script refuses changed pinned inputs, repository-local output, symlink
escapes and reused output directories. It emits one-file overlays and unified
patches, never edits the input or runs imports. The renderer owns application to
an independent frozen scratch project and serial import. Apply exactly one
overlay to a fresh baseline copy, using the manifest's `edits[].path` values;
do not stack the two variants for causal review. For roughness mips the only
patch is `mipmaps/generate=false` → `mipmaps/generate=true` in
`assets/materials/rama-finish/skin-roughness.png.import`. Verify that generated
import metadata retains this setting after import and that the loaded texture
contains mip levels. For SSS the only patch is the `Rama warm skin` profile's
`subsurf_scatter_enabled` value from `true` to `false` in
`scripts/rama_surface_finish.gd`.

Run the existing `tests/rama_surface_finish_cases.gd` against the imported
candidate project, recording actual result and source hashes. Its preservation,
isolation, foreign-owner and rollback checks remain relevant. It cannot prove
pixel improvement. The capture owner must produce the fixed-camera comparison
listed in `material-profile.json`, including unchanged control, and report
original framebuffer hashes. Acceptance requires actual image review, not only
the source test. Root owns any eventual promotion and final content/package
identity updates. No production defaults are changed by this packet.
