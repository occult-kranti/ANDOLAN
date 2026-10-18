# Exact-byte asset transport

GitHub Actions [run 39089069718](https://github.com/occult-kranti/ANDOLAN/actions/runs/39089069718) completed successfully on 18 October 2026. It reconstructed and uploaded the five reviewed package-r3 files to existing draft release `416177473`, leaving that release a draft. The release owner subsequently published it at `2026-10-18T02:10:32Z`. Public download verification belongs to the separate receipts in the parent directory.

The release owner had observed HTTP 401 from direct asset upload to `uploads.github.com`, while existing release API operations and Git push worked. This approved transport used a GitHub-hosted runner's built-in `github.token` with job-scoped `contents: write`. It required no additional credential, build, export, import, archive repacking or package execution.

| Identity | Value |
| --- | --- |
| Reviewed package source | `9e81a7c849837dea477ddb5a8c93f43665774573` |
| Isolated transport branch | `release/yuga-native-ui-2026-10-18-assets` |
| Orphan transport commit | `b2ea3a72627394c00ce829700d6361475dc08cdb` |
| Transport tree | `cd89ef202877eae49380810715e3e0e550021e1b` |
| Transport manifest SHA-256 | `a97acb51d76c9c404d0cf6f72c4aba320ef5a8bebb69e8947a02b05306b0aa3f` |
| Uploader SHA-256 | `75bcdadb004fa41dcff38356578ddcc6ab18042f7a0fbd415ad5e0b3595f792b` |

The two original ZIPs were streamed into six Git blobs, with four chunks of 50,331,648 bytes and final chunks of 37,149,039 and 45,150,382 bytes. The manifest pins each chunk's length, SHA-256 and Git object identity, plus all five assembled asset identities. The original export manifest, package manifest and checksum file were the other three payload files. No local chunk files were retained. Only this small evidence directory enters the production branch; the 283,626,013 binary ZIP bytes lived on the isolated orphan branch.

`generate.py` used Git plumbing and a private `GIT_INDEX_FILE`, then streamed all Git blobs back through the same verifier used by the runner. Its thirteen-file tree includes only the payload, manifest, verifier, pinned workflow and exact `.gitattributes` content. Both generation and push receipts prove that the normal branch, HEAD and index remained unchanged. `push.py` checked the live release identity and empty asset set before creating and pushing the separate branch. It never switched the checkout.

The workflow pins the repository's existing `actions/checkout` revision, disables persisted credentials, and accepts only creation of the exact transport branch. The verifier hashes every chunk and assembled file before the token-bearing upload step; that step rehashes the output files. Before every upload it checks the fixed release ID, draft status, tag, source commit and prerelease status. Unexpected, duplicate, incomplete or mismatched existing assets fail closed. An exact existing asset is skipped only when its uploaded state, size and GitHub SHA-256 digest match. Every POST targets the fixed release ID. The workflow contains no publish, delete or clobber action.

`guard-tests.json` records 20/20 local checks with an in-memory API and zero network mutations: pinned manifest, modified/truncated/oversized chunks, independent assembled hash, altered reconstructed bytes, five release identity/state failures, conflicting existing assets, five exact uploads and exact rerun skips. `action-run.json` records the successful actual runner; `action-upload-receipt.json` records all five uploaded asset IDs and digests while the release remained a draft. The filtered application-step log preserves the actual reconstruction and upload results. `asset-api-receipt.json` independently confirms those identities after the release owner published.

The scripts are retained as exact historical execution sources. Their original absolute workspace paths describe that run; do not rerun the push/upload scripts against the published release. To recover the transport payload, obtain and verify the five public files against `manifest.json`, split the ZIPs at the listed lengths, and verify each listed Git blob identity. `transport-tree.txt`, `transport-commit.txt`, the exact workflow/verifier and `gitattributes.txt` preserve the rest of the tree and original commit metadata. This allows recovery without keeping the binary chunks in production history. Remote branch cleanup requires a separate authorization after public-byte verification.
