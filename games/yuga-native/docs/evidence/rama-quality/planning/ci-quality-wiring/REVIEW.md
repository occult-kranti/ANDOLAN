# New Rama quality CI/setup gates

Role 15 bounded packet. [Wiring review](review.json) pins the edited workflow,
setup script, shared runner and current squad/quality documents. All previous
workflow and setup lines remain in order; the changes add one shared-runner
invocation to each and retain the existing gates/artifact paths.

The shared runner catalogs **sixteen suites: fourteen Godot and two Python**.
These cover LOD interchange/selector/one-rig binding, lighting, action audio,
input buffer and its actual offline integration, actual-asset facial binding,
QA's actual-world quality admission/lifecycle, materials, isolated practice
brain, pose-only remote replica, screens, secondary motion and VFX. The second
Python command runs the deterministic fifteen-cue generator in `--check` mode.
The ordinary project import remains outside this runner.

Every Godot invocation receives distinct temporary `XDG_DATA_HOME`,
`XDG_CONFIG_HOME` and `XDG_CACHE_HOME`. Execution is sequential, headless and uses
Dummy audio. It does not force fixed-fps timing onto the audio mix fixture.
The runner retains JSON reports/logs, checks nonempty passing results and exit
codes, rejects engine errors, and compares runtime plus checked-source hashes
before/after. Python executable symlinks retain their venv path, preserving the
already-pinned NumPy dependency used by LOD tests.

The workflow calls the runner after its existing traversal-tools venv is
prepared. Cloud setup uses its existing native Python venv. CI retains the
runner summary, source manifests, `reports/` and `logs/` even on failure; user
cache directories are not uploaded.

## Executed here

The [source-bound actual subset](summary.json) passes six suites on the current
runner: LOD interchange **19**, selector **27**, one-rig binding **33**, material
component **38**, secondary component **42**, and deterministic checks of all
**fifteen PCM files**. Their [reports](reports/) and [logs](logs/) are retained.
Runtime and checked-source hashes were unchanged during that run. This is an
executed subset, not a claim that all sixteen suites or full setup/CI passed.

Four [orchestration counterexamples](negative-orchestration/review.json) use a
clearly labeled fake engine to challenge empty reports, contradictory checks,
nonzero exit with a claimed pass, and an engine-error log. All eight fake
invocations are rejected and distinct XDG directories are verified. These
fixtures test wrapper behavior; they execute no Godot/gameplay and do not add
game acceptance counts. Bash syntax, Python compilation, installed-PyYAML
workflow parsing, the sixteen-entry catalog and additive preservation checks
also pass.

## Still required

Run the entire catalog after the accepted face/LOD/runtime source and imports
are frozen. The actual-asset facial and actual-world quality gates stay enabled:
the old R7 asset is expected to fail the new-feature admission before its
accepted replacement is staged. Do not bypass those gates to make CI green.

Root coordinates final source pins, schema-2 NOTICE/asset promotion, complete
foundation CI and actual rendered/package/input qualification. No contract-pin
refresh was performed in this packet. Isolated brain/replica checks do not mean
AI or native online play is integrated. Headless passing counts do not accept
visual quality, OS input, listening, human feel, Windows or physical-GPU cost.
