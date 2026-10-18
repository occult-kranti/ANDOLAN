# One-line pipeline-priority diagnostic build

The isolated source tree differs from public Godot 4.6.3 `35e80b3a8822a9df9be390814b62f44c0a9c69e8` in exactly one line: `PipelineCompilation` tasks use `false` for the `add_template_task` high-priority argument in `pipeline_hash_map_rd.h`. The retained original/proposed headers and exact unified diff bind the change. ShaderCompilation group priority, lock scope, resource lifetime/readiness, shader bodies, runtime/import features, and project files are unchanged.

All 13,847 expected source files match, with exactly one delta from the original inventory. The same template-debug flags and CPU0–3/four-job guarded build completed 18 compilation actions and relinked in 30.32 seconds according to SCons; the five-second wrapper observed completion at35.018 seconds. Ten post-build checks passed. The baseline binary and installed editor remain byte-identical to their earlier receipts.

The candidate is retained at `/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority`, 85,447,128 bytes, SHA-256 `e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e`. The unmodified binary remains separately retained; no installed engine or project runtime was replaced. This is an isolated diagnostic, not a promoted engine or release artifact.

The [cold baseline](../template-cold-baseline-r1/REVIEW.md) failed before its first image. [Independent native review](../W4-public463-native-review-r1/README.md) maps the exact compiled functions to the shader-version mutex and shader-group completion paths. Fresh mutex-owner/queue-memory equality was not captured. Low-priority tasks can be promoted cooperatively, other high-priority clients exist, and a single-worker pool has different constraints; one successful fixture would not prove universal deadlock prevention.

The unchanged cold eight-screen fixture and frozen runner are used for the next comparison, with fresh Godot and Mesa directories and identical rendering configuration. Build success alone does not establish first-draw success, visual quality, performance, or engine readiness.
