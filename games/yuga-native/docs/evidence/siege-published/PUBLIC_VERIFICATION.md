# Public siege release verification

Release: https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-siege

Exact source: `35b20429d2b34f06f2907d5739cf4877aac597ab`.

Both native workflows succeeded: foundation `39011346033`, prerelease `39011346041`. Public metadata reported 62 uploaded assets. All 62 were independently downloaded and hashed; the exact remote inventory, manifest and SHA256SUMS agreed. The annotated tag resolved to the expected commit.

The public export inventory's 227 source files match the tagged Git blobs. Linux and Windows ZIPs each contain 18 verified members, including 226 checked PCK resources. ZIP CRCs, all payload hashes, PCK stored MD5 and SHA-256 entries, internal package manifests and public export manifests agree. No game was executed by this verifier.

## Exact downloaded Linux handoff

`/workspace/scratch/yuga-siege/public/extracted-linux/yuga-native-linux-x86_64/launch.sh`

All 17 extracted payloads were rehashed against PACKAGE-MANIFEST.json and archive modes preserved. Parent owns the actual public-package window test. Windows execution and physical-GPU performance remain untested.

## Difference from the local package

The local and public packages have the same runtime source inventory and 226 resource paths. 217 resource payloads are byte-identical; nine generated `.scn` resources differ. This comparison alone does not prove semantic equivalence. Exact path/hash/length details are in `local-public-entry-comparison.json`; the parent will exercise the downloaded build.

## Evidence

- `public-verification.json`: complete public download/source/ZIP/PCK result.
- `remote-release.json`, `remote-assets.json`, `remote-tag-ref.json`: actual remote metadata.
- `downloaded-asset-hashes.json`: exact public file bytes and SHA-256.
- `release-verify.stdout.txt`: committed release validator result.
- `linux-extraction.json`: post-extraction payload verification.
- `workflow-snapshots/`: timestamped API observations through successful publication.
- `verification-tools/`: exact executed verifier and committed package/release helpers.

No GitHub mutation, credential extraction, runtime change or commit was performed by this verification task.
