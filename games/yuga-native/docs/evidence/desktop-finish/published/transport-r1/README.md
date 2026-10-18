# Exact desktop package transport preparation

This is the bounded successor of the [published I3 transport](../../../ui-campaign/I3/published/transport/README.md). It reuses the five already qualified r3 files; it does not export, rebuild, execute or publish the game. The normal source branch remains at `f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1`.

Root created draft `416367666`, tag `yuga-desktop-finish-2026-10-18`, targeting that exact source with prerelease enabled. Root reported a fresh direct SHA256SUMS upload HTTP 401 and confirmed zero assets. The historical I3 HTTP 401 is not the trigger for this attempt. The exact [current HTTP failure](direct-upload-failure.json) and [draft API response](draft-api.json) are retained; no credentials were copied.

The [manifest](manifest.json) pins Linux ZIP `913e2b82…`, Windows ZIP `ee8026ca…`, export manifest `c472ef52…`, package manifest `6df86cc2…`, and SHA256SUMS `3b437f1a…`. All bytes were rehashed from `/tmp/yuga-desktop-integrated-package-r3/build`. Linux is two parts and Windows three, each at most 48 MiB; the other three assets remain whole. The resulting orphan tree has 12 entries. Binary parts are streamed to Git only after explicit materialization, not copied into this evidence directory.

Preparation ran `python generate.py` and `python test_guards.py`: five real asset hashes and 22 local uploader guard cases and 10 mocked local receipt/tree cases pass. Default generation computes Git blob IDs without writing Git objects; it checks normal HEAD, branch and index before/after. No Git objects, refs, normal index, network or release assets were mutated. Tests replace the API with in-memory fixtures. The [preparation receipt](preparation-receipt.json), [uploader guard receipt](guard-tests.json) and [push guard receipt](push-guard-tests.json) retain exact identities.

After root has reviewed the scripts and the current warm/cold/CI evidence, the exact later commands from this directory are:

```bash
python generate.py --materialize
python test_guards.py
python test_push_guards.py
python push.py --push-fixed-draft
```

These commands are provided for root execution; they have not run. Materialization creates a private index, verifies all chunk and assembled bytes from the Git blobs, and writes one parentless commit without moving the normal branch. Push validates source/branch/current tool pins and all 12 tree entries against the exact parentless commit before any remote/API/ref operation. It requires the explicit --push-fixed-draft flag and that exact prepush receipt, unchanged normal checkout/index, a new local/remote transport branch, and the existing empty fixed draft. It pushes only `transport/yuga-desktop-finish-2026-10-18-r1`.

The workflow uses the repository's exact checkout pin and disables persisted credentials, LFS and submodules. Verification has no token. Only the upload step receives GitHub's supplied token. Upload verifies all reconstructed bytes before API access and checks ID, source, tag, draft/prerelease, allowed names, size, state and SHA-256 digest before each addition. Exact existing files are skipped; mismatched or unexpected files abort. No delete, replacement, release creation, release publication, credential extraction or new secret is implemented. Root must independently inspect the action result and all five downloaded bytes before separately publishing the release.

The default Linux package uses the explicitly selected unmodified public `dce0422d…` runtime, exported by official `f64d4ed1…`. The earlier official-runtime warm failure and skipped cold run remain separate; transport success establishes only delivery of the exact r3 bytes.

**Current disposition: HOLD.** The exact public-runtime package passed the warm journey but its separate fresh-cache cold run stalled. Root has withheld materialization, upload and publication pending cold qualification. No transport action is implied by these prepared files.

Independent [W5 review](../W5-transport-review-r1/REVIEW.md) accepted the repaired preparation. The [original mutable-branch counterexample](independent-review/branch-counterexample.json) and exact old push source are retained; the [repair replay](independent-review/branch-repair-replay.json) rejects before any Git/snapshot/subprocess call. The independent22 uploader cases and10 push cases use blocked/mocked subprocesses.
