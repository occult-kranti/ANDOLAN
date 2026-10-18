# Distinct desktop polish release: source-only transport plan

Proposed tag: `yuga-desktop-polish-2026-10-18`. Final source commit, draft release ID, package output directory, exact five asset sizes/digests, package warm/cold acceptance, workflow run and transport commit are **pending**. The prior public `yuga-desktop-finish-2026-10-18` release (ID416367666/source96d5) is immutable and must not be a successor destination. No request, draft, Git object/ref/index write, materialization, upload or publication was performed for this plan.

Reuse the reviewed machinery under `published/transport-r2` and `published/release-r4/publish.py`. Keep their sealed bytes unchanged. The proposed new packet paths are `published/transport-polish-r1/` and `published/release-polish-r1/`; this plan does not create either executable packet.

## Minimal successor substitutions

| File in new packet | Required change after exact inputs exist |
|---|---|
| `generate.py` | Bind final source HEAD and existing approved repository path, qualified output directory, new draft ID/tag, fresh branch `transport/yuga-desktop-polish-2026-10-18-r1`, exact four asset tuples and SHA256SUMS digest. Preserve default hashing-only generation and explicit `--materialize`. Generate fixed workflow identity from the same values. |
| `upload_template.py` | Bind that same new draft/tag/source/branch. Recompute exact per-asset part counts from sealed sizes with unchanged48MiB maximum; derive the exact total paths/tree census. Do not assume old2Linux+3Windows chunks remain correct. Preserve five names, byte reconstruction, no-clobber, exact-existing skip and unexpected-asset rejection. |
| `push.py` | Replace fixed branch/API ID and exact census; keep current generator/uploader/workflow/manifest/test hash binding, recomputed entries, parentless commit and exact tree, HEAD/index invariants and explicit `--push-fixed-draft`. |
| `test_guards.py`, `test_push_guards.py` | Rebind fixture identities and exact part census. Preserve all22 uploader and10 local push guard cases, including wrong branch/source/receipt/tool/tree and public/wrong release rejection. Mocks must not call network or mutate Git. |
| generated manifest/uploader/workflow/receipts | Regenerate from the five existing exported files; no rebuild or repack. Retain commit-pinned checkout, no persisted credentials/LFS/submodules, verification without token, upload with builtin token only. |
| new `release-polish-r1/publish.py` | Bind final W1 warm/cold and independent review receipts, W6 export/package identity, source, new draft ID/tag, manifest, upload run/commit and release notes. Preserve exact five API size/digest/state checks. Publication PATCH must explicitly contain tag_name, target_commitish, name and body alongside draft=false, prerelease=true and make_latest=false. |

All pending identities must fail closed; use no old asset digest, release ID or source literal as a placeholder. Existing generator's exact HEAD/source branch gate must still hold at execution. If HEAD has advanced, root must explicitly select an already-owned exact-source checkout and reseal its path/origin/HEAD/index; do not weaken the check or silently switch sources.

## Execution and approval sequence

1. W6 supplies final export/package qualification and five exact files; W1 and independent reviewer qualify the same archive/runtime. Root creates a new held draft only after authorizing that external action. Capture its exact ID, tag, target, prerelease/draft=true and initially empty assets. Current network upload availability is untested by this plan.
2. Default generator reads those exact files, computes chunk/blob identities without object/ref/index writes, then22+10 mocked guards and independent source review freeze the packet. Root authorizes later operations against that concrete result. Direct upload, if used, must preserve the same exact-output/fixed-draft/no-clobber checks. A401 is retained and triggers the already-reviewed Git transport fallback; it never triggers export again.
3. Explicit materialization streams existing files into Git blobs, reconstructs/validates exact bytes from blobs, builds a private index and parentless commit, and proves normal HEAD/index unchanged. No binary chunk copies are retained. Explicit push first validates the complete local trust chain and an empty new remote branch/fixed draft; upload workflow only attaches files and does not publish.
4. Root separately publishes only after actual package acceptance and exact successful upload identity/API digests. W5 independently downloads/verifies all five public bytes, new tag/source, both ZIP payload/PCK/proofs; no new gameplay claim. Stream one ZIP at a time, retain small metadata/audit and avoid another extraction.
5. After public verification, remove only the temporary branch using remote `--force-with-lease=<exact-ref>:<exact-transport-commit>` and local compare-and-delete. Verify remote/local absence and normal HEAD/index. Never delete the public tag/source branch or prune objects as part of this operation.

## Storage admission

Let A be the sum of the five **new qualified** file sizes. Default preparation retains small source/JSON only (plan allowance4MiB), reads chunks in1MiB blocks and does not copy ZIPs. Materialization/push should reserve **2A+64MiB additional free space** for new compressed Git objects and a transient pack/metadata, plus the separately protected **500MiB actual reserve**. This is a conservative planning bound, not measured next-run allocation; compression/dedup savings are not assumed. The existing five exported files are already allocated and excluded from this incremental amount. Check the actual filesystem holding Git objects and its fresh free space immediately before materialization. Preserve one process/threaded pack controls and avoid unrelated backup/export overlap.

Historical r4A=244,440,031B (233.116MiB), giving555,988,926B additional transport allowance and1,080,276,926B free-space admission including500MiB reserve. Read-only observation during this plan found1,396,895,744B free on/workspace; forthcoming export and other workers can consume it, so this is **not** current transport clearance. A GitHub runner should budget roughly3A+64MiB for checkout Git objects, chunk worktree and reconstructed files (historical800,428,957B), separately from runner overhead. Public verification needs at most the larger qualified ZIP plus small metadata/audit and500MiB reserve. Recalculate all values from final receipts; if insufficient, request exact inactive/recoverable-file cleanup, not cache or broad directory deletion.

## Scope

This is a source review and proposed change map only. No new code, engine, network request, mock replay or payload hashing was executed. Existing published receipts are historical examples, not qualification of the successor. Windows execution, physical-GPU performance, human game feel and full art completion remain separate.
