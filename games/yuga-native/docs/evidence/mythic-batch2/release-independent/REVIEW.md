# Independent mythic release-gate review

**Accepted for this bounded review:** eight focused regression probes pass on release validator `62e5865352b833845f9aa2a1dd2efed52363797ad7dafe4747f927c097eac0f9`. Five routing predicates and the exact producer/publication fixed-source comparison also pass. The release owner separately reports 151 synthetic gate cases; this reviewer did not rerun that unchanged suite.

This review compared the real capture producers with publication validation, then used synthetic counterexamples. It did not render, import, build, publish or certify visual quality. The reviewer changed only this evidence directory; the release owner repaired the validator and its fixtures. Runtime and capture sources remained unchanged by this review.

## Findings and verified repairs

| Finding | Repaired gate | Independent evidence |
| --- | --- | --- |
| The full capture report has no `preview` field; the old fixture concealed this mismatch. | Absence is accepted under the existing exact full-take constraints. A present value must be exact `false`. | Actual-schema probe accepts. The owner suite separately tests invalid present values. |
| The producer pins five fixed sources, but the gate pinned three. | Canonical `art/world/confluence-map.json` and `tools/run-traversal-capture.py` are included alongside the other three paths. | `producer-schema-r1.json` preserves the mismatch; R2 and the source-set acceptance probe pass. |
| Top-level `passed:true` allowed stale source hashes and empty gameplay results. | Typed mandatory mythic reports require meaningful successful checks and current source/export provenance, with explicit handling of the real catalogue, physics, audio and effect schemas. | Both stale-success and empty-success probes reject before staging media. |
| Missing events, reversed frame-phase chronology and zero-age warning stills passed. | The existing ten-event Rama/Sita ledger is checked against per-cast sequence, timings, frame phases and cleanup; still ages are positive and persistent-zone cancellation is required. | All three malformed probes reject with the intended reason. |

`probes-r1.json` retains the initial seven cases: the baseline passed and six desired-contract checks failed. `probes-r2.json` retains eight passing cases, including the added producer-source-set acceptance case. Their exact scripts and logs are beside them. The scripts use the owner's synthetic fixture for setup and mock Git/decoder calls; independent mutations and expected outcomes are the review contribution. They do not decode media or execute a packaged game.

The final source and fixture hashes are recorded in `source-sha256.json`. The final probe command was:

```sh
python3 /workspace/scratch/yuga-mythic-release-independent/probes-r2.py
```

The archived `.py.txt` is that exact script. To repeat it in this workspace, copy it back to that path; it uses the current checkout's fixture. Preserve previous output before rerunning. This is an inspection companion, not a new CI test target.

## Routing and scope

The workflow and helper agree on exact `-mythic` routing. Mythic tags require the fresh mythic traversal archive and the new ultimate archive. Older tags retain their historical routing. A duel tag, a nonterminal suffix and a newline cannot select the mythic path. `routing-review.json` records the five pure predicates; no workflow was executed by this reviewer.

The actual film contract covers fourteen static warning/motif studies, a representative Rama lifecycle, and Sita onset/sustain explicitly cancelled at take end. It does not show fourteen complete rendered lifecycles. Gameplay outcomes remain separate session/integration checks.

A source-pinned structural gate does not independently prove artistic quality, pixel-to-event correspondence, or realtime performance. Imported Godot resource bytes may differ across build environments. Actual captured-frame review, media checks and downloaded executable tests remain separate release evidence. No remaining blocker was found in these focused probes; this is not a blanket security or production-game certification.
