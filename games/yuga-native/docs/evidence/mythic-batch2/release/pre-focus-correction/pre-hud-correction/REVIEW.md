# Mythic release and CI gates

The new `yuga-traversal-armies-2026-10-17-mythic` route requires16 new mythic test reports, a fresh180-frame traversal capture, and source-matched original ultimate VFX studies. Historical film evidence and old traversal/siege/Triad routes remain separate. Generic capture-directory constants were not reassigned.

Owner checks pass:154 new synthetic release cases;169 existing traversal,78 siege and106 Triad counterexamples. Official actions remain pinned to exact40-hex revisions. The older action-name allowlist received only the new official setup-node name; its rejected run is preserved. Workflows parse and setup shell syntax passes. An actual Node22.14.0 execution passes48 physics reference tests with explicit --experimental-strip-types.

Required mythic reports must contain successful nonempty check arrays or their specific measured validation schema. Declared required runtime/tool source pins must match the checkout and shared export source records. A stale successful report, empty successful report and missing source pins reject. The physics and original audio builder have typed provenance handling rather than invented generic fields.

The ultimate validator checks120 frames/240 physics ticks, all14 themed stills, three reduced-effects/reduced-motion/overlap views, six retained take frames, renderer counters, exact source/export inventory, import proof, movie hashes and fresh decoded dimensions/count/rate/duration. It checks the actual ten-event Rama/Sita ledger, per-cast sequence, projectile contact indexes, ordered rendered phases and disclosed early cancellation of the persistent Sita study. Positive still ages are required. The producer has no preview mode; absent preview is accepted only with all exact full-take constraints, while any present value must be literal false.

Independent review found the initially missing source-map dependency, optional-preview producer mismatch, insufficient report provenance and unvalidated event chronology. All were corrected without altering the frozen rendering helpers. Eight focused independent closure probes pass in the sibling independent review archive.

The actual accepted ultimate archive passes this validator with a fresh ffprobe decode:120 frames,14 hero studies,3 variants,6 retained frames and293 source pins. All16 actual mythic reports pass source-provenance checks. These two local validations use the current packager.source_state snapshot; they are explicitly not PCK/package validation. Root must repeat against the final native-export-manifest.json after its final traversal capture and export.

No commit, import, heavy render, package export, tag or publication was performed by this worker. Root owns those actions and the top-level evidence manifest.

## Reproduction

```sh
python3 games/yuga-native/tests/release_mythic_cases.py --report=/tmp/mythic-release-cases.json
python3 games/yuga-native/tests/release_traversal_cases.py --report=/tmp/traversal-release-cases.json
python3 games/yuga-native/tests/release_siege_cases.py --report=/tmp/siege-release-cases.json
python3 games/yuga-native/tests/release_triad_cases.py --report=/tmp/triad-release-cases.json
bash -n tools/cloud/setup-native.sh
```

`bash tools/cloud/setup-native.sh` performs a full import and prepared-environment test pass; coordinate the import with any active renderer. No import should run during frozen capture.

## Root release sequence

1. Finish the180-frame capture in `docs/evidence/mythic-traversal-render-r1`; both captures must match frozen runtime and final exported sources. Mythic traversal validation sets require_shaders=True; historical validation keeps its existing default.
2. Finish owner/fullsetup checks and commit all runtime, helpers, captures, manifests and tests. Keep failed evidence with its own pinned sources.
3. Build Linux/Windows packages at the intended immutable commit using `tools/package-native.py`. Validate both captures against that build's native-export-manifest.json; the fresh capture validation must decode the movies. Windows execution remains a separate claim.
4. Create the new tag only at the verified commit. Push the authorized branch/tag to run the pinned prerelease workflow. It imports/tests/packages, validates source-bound captures, assembles assets and verifies downloads before publication.
5. If staging locally, provide all CHECKS, TRAVERSAL_CHECKS and MYTHIC_CHECKS JSONs with the exact filenames used by yuga-native-release.yml, plus existing engine download and package manifests. `release-native.py stage --build BUILD --engines ENGINES --checks CHECKS --output EMPTY_OUTPUT --tag yuga-traversal-armies-2026-10-17-mythic --commit COMMIT` verifies tag/checkout/build identity and committed archive/source status before staging.
6. `release-native.py verify --directory OUTPUT --tag TAG --commit COMMIT` checks the staged set; root may then use the existing publish command/workflow. This worker has not published anything.
