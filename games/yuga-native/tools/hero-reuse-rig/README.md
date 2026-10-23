# Existing-rig transfer investigation

This pipeline reuses the accepted Rama skeleton and nine actions on the generated Rama source. It uses Blender's polygon-interpolated weight transfer and strongest-four normalization, following the existing `art/hero-finish/s5-shoulder-armour/articulated-r5/skinning_trials.py` study. It does not generate a new skeleton. Both completed candidates are rejected for production; see the [evidence handoff](../../art/ten-rounds-oct23/rig/README.md).

Run from the repository root with Blender 4.3.2 and one CPU thread. Output directories must be new. Rendering needs the coordinator's resource lane; no tools replace runtime files.

```bash
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-reuse-rig/inspect_inputs.py -- --output /workspace/scratch/ten-rounds-oct23/rig/input-inspection.json

# Baseline nearest-face binding; known rejected anatomy. --export is optional.
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-reuse-rig/build_transfer.py -- --output /workspace/scratch/rig-baseline-reproduction --export

# One completed experimental anatomy-gated correction; also rejected.
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-reuse-rig/build_transfer.py -- --output /workspace/scratch/rig-anatomy-reproduction --anatomy-gated

blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-reuse-rig/analyze_deformation.py -- --scene /workspace/scratch/rig-anatomy-reproduction/skin-transfer.blend --output /workspace/scratch/rig-anatomy-reproduction/deformation-localization.json

blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-reuse-rig/audit_repose.py -- --transfer /workspace/scratch/rig-anatomy-reproduction/transfer.json --output /workspace/scratch/rig-anatomy-reproduction/repose-audit.json
```

`build_transfer.py` verifies the original source hash, explicitly resets imported animation state to REST, records the source-to-donor matrix, saves a separate `.blend`, and samples 18 actual action frames. The current script also fixes glTF armature parenting and records its launch hash. The frozen R1 code predates those packaging fixes; its original warning and artifacts remain preserved. Frozen scripts are provenance snapshots whose root discovery assumes their original `tools/hero-reuse-rig/` location; do not execute them directly from the art folder.

`anatomy_gate.py` is the rejected R2 experiment, not an accepted automatic-rigging solution. Its original source→reposed REST damage must be assessed separately from the action→REST strain statistics. Its mirrored landmarks do not fit the source asymmetry, and zero filtered-prefix weight sums are not proof of anatomical correctness. Do not run parameter sweeps without first fixing the measured source correspondence.

```bash
# Data-only integrity validation of a real exported GLB.
python3 games/yuga-native/tools/hero-reuse-rig/validate_export.py --candidate /workspace/scratch/rig-baseline-reproduction/rama-skin-transfer.glb --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb --donor games/yuga-native/assets/heroes/rama-hero.glb --output /workspace/scratch/rig-baseline-reproduction/export-integrity.json

# Actual five-pose witness set, Cycles CPU / 16 samples / 1 thread / 480 px.
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-reuse-rig/render_poses.py -- --scene /workspace/scratch/rig-baseline-reproduction/skin-transfer.blend --output /workspace/scratch/rig-baseline-reproduction/views

# Rebuild only the bounded evidence packet from this session's retained data.
python3 games/yuga-native/tools/hero-reuse-rig/package_evidence.py --scratch /workspace/scratch/ten-rounds-oct23/rig --output games/yuga-native/art/ten-rounds-oct23/rig
```

Positive markers establish that a named operation finished, never production acceptance: `RIG_INPUT_INSPECTION_PASS`, `RIG_TRANSFER_MECHANICS_PASS`, `RIG_DEFORMATION_LOCALIZATION_PASS`, `RIG_REPOSE_AUDIT_PASS`, `RIG_GLB_INTEGRITY_PASS`, `RIG_POSE_VIEWS_PASS`, `RIG_EVIDENCE_PACKAGE_PASS`. Read each report's explicit `quality_accepted`, `runtime_promoted` and scope fields. No new runtime hero has been accepted.
