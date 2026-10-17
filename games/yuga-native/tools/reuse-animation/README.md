# Offline animation key audit

This tool uses a small [MIT-attributed ValveResourceFormat algorithm](NOTICE.md)
to propose fewer keys for the existing original Rama animation library. Godot
reads the actual resource; Python compares quaternion SLERP and normalized LERP,
positions and retained endpoints. Output is external JSON, never a runtime
resource. The current library and motion controller stay authoritative.

From the repository root, use a fresh external output directory:

```sh
mkdir -p /workspace/scratch/rama-key-study-new
taskset -c 0,1 godot --headless --path games/yuga-native \
  --script res://tools/reuse-animation/export-library.gd -- \
  --input=/workspace/ANDOLAN/games/yuga-native/assets/animations/rama_hero_motion.tres \
  --output=/workspace/scratch/rama-key-study-new/library.json
python3 games/yuga-native/tools/reuse-animation/audit.py \
  --input /workspace/scratch/rama-key-study-new/library.json \
  --output /workspace/scratch/rama-key-study-new/proposal
taskset -c 0,1 godot --headless --path games/yuga-native \
  --script res://tools/reuse-animation/verify-candidate.gd -- \
  --input=/workspace/ANDOLAN/games/yuga-native/assets/animations/rama_hero_motion.tres \
  --candidate=/workspace/scratch/rama-key-study-new/proposal/candidate.json
python3 -m unittest discover -s games/yuga-native/tools/reuse-animation -p 'test_*.py' -v
```

The extractor requires `--path games/yuga-native` and refuses existing outputs,
output symlink components and JSON paths inside the checkout. Python resolves
its output path and requires a new directory outside the checkout. No importer,
renderer, shared export or asset replacement is performed. The verifier builds
candidate animations in memory and prints its result; it saves no resource.

Default acceptance budgets are 0.01 degrees and 0.01 mm. Selection starts at
half those budgets, then restores neighboring original keys if dense probes
detect an excursion. Eight subdivisions per original interval include original
key times and intermediate times. These finite probes are **not a continuous
error proof**. The Godot comparison adds probes on both sides of loop boundaries.

The tool admits only enabled linear rotation/position tracks with unit key
transitions and finite, increasing times. Multiple-key channels must cover
the full clip; a single constant key is retained. Unsupported method/events,
scale, cubic interpolation, partial spans and malformed quaternions are refused.
It preserves clip names, duration, loop mode, track paths and existing endpoints.

Numerical reduction is an authoring/storage experiment. It does not establish
file-size savings for a future `.tres`, frame-time gains, smoother motion,
correct skinned soles/bow contact or unchanged gameplay event timing. Any
future runtime promotion needs the actual rig's hand/string/foot comparisons,
authoritative release receipts, continuous locomotion/action footage and an
independent review. The current motion library already prunes constant tracks;
the new capability is bounded reduction of nonconstant tracks.
