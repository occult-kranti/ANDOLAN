# Source-only transport-r2 preparation

The successor targets exact source `96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12`, held draft 416367666 and tag `yuga-desktop-finish-2026-10-18`. Its new branch is `transport/yuga-desktop-finish-2026-10-18-r2`; inputs will be the five sealed files under `/workspace/scratch/yuga-desktop-integrated-package-r4/build`.

The reviewed r1 generator, uploader and push trust checks are reused. The pending generator has an empty asset list and no checksum pin; it rejects both default and materialization modes before snapshot/Git/subprocess access. The existing 22 uploader and 10 mocked push checks are retained but have not yet run for r2. Five Python sources parse. No asset hash, payload manifest, uploader digest or completed preparation receipt is invented. The pending-source copy and fail-closed control remain historical when final pins arrive.

Root supplied the exact final draft API response; its ID/tag/source/draft/prerelease/empty-assets fields were checked and the raw response copied byte-for-byte. Root retains the earlier API correction history separately: a PATCH omitting tag_name unexpectedly changed the tag, then an explicit complete metadata PATCH restored the intended tag. Any later publication PATCH must explicitly include tag_name, target_commitish, name and body. This transport contains no publication operation.

Finalization waits for W6's exact export/package receipt and all five actual artifact hashes. Then verify source ancestry/manifests/SHA256SUMS, replace only pending pins, generate metadata in default prepare-only mode, and replay the retained 22+10 mocked guard suites. The strict two/three ZIP-part contract remains pending confirmation against actual sizes; it must fail rather than silently reinterpret a different layout. Independent review and actual package qualification remain separate gates before any future transport execution.

No Git object/ref/index creation, materialization, branch push, asset upload, publication, engine/export run or draft API mutation was performed by W5. Root owns draft metadata and later execution decisions. The sealed r1 packet and f8 artifacts remain unchanged.
