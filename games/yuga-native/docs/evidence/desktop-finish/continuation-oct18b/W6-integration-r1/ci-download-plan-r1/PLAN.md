# CI-only candidate delivery: future bounded local route

Source/code checkpoint1741de3c96b0f8c4d9948a040e85257f154a5c88; candidate workflow39147837494 succeeded. Root-reported API artifact sizes: Linux97,906,137B, Windows146,203,047B, evidence201,950B. These are artifact transport sizes, not independently downloaded package pins. Current artifact access is403 at the unapproved productionresultssa6.blob.core.windows.net host; root’s exact-host configuration draft still requires user Save/Publish. No retries, alternate host/proxy/tunnel, artifact downloads or new local qualification have occurred.

The installed CLI reports2.46.0 (Debian2.46.0-3). Upstream v2.46.0 download/http.go (retained here, SHA65d77306…f0b52) uses os.CreateTemp("","gh-artifact.*.zip"), copies the whole outer artifact ZIP, extracts while it remains, then removes it. Go’s default temp is affected by TMPDIR; never allow bulk default/tmp spooling. This is a source inspection for the reported upstream version, not a runtime trace of the Debian executable.

Root approved the smaller alternative: retain the one Linux outer artifact in bounded RAM, avoiding CLI download temp behavior entirely. About98MB is small against the32GiB machine; enforce the exact response-size/digest cap anyway. No new downloader framework is needed while access is blocked.

Future API commands (NOT executed; artifact IDs and digests must first be bound to this exact source/run/name):

```sh
gh api repos/occult-kranti/ANDOLAN/actions/runs/39147837494/artifacts
gh api repos/occult-kranti/ANDOLAN/actions/artifacts/EXACT_EVIDENCE_ARTIFACT_ID/zip
gh api repos/occult-kranti/ANDOLAN/actions/artifacts/EXACT_LINUX_ARTIFACT_ID/zip
```

The ZIP responses must be captured by a bounded byte reader, not printed, redirected through an opaque disk temp, or parsed as JSON. No --cache/--include options. Signed redirect URLs/credentials must not be recorded; retain HTTP status/host and sanitized diagnostics.

Admission/execution sequence:

1. After host activation, require completed successful exact-source build run and exact separate Linux/evidence artifact identities, unexpired status, sizes and outerSHA256. Retrieve the small evidence artifact first with hard byte/uncompressed-total caps. Verify safe unique regular members and bind its CI final proof, source inventories, installer/runtime/manifest/log records and inner LinuxZIP bytes/SHA. FoundationCI remains a separate acceptance gate.
2. Before the Linux transfer, refresh free space and agree the renderer lane. Admit innerZIP size +exact private extraction size +bounded wrappers/cache/captures while preserving the500MiB actual floor. Account for partial files and runtime-output growth. Stop before starting if the sum fails. The archive identity/pins must come from the exact new CI proof, not old79e5 receipts.
3. Read gh-api stdout into BytesIO in1MiB chunks, rejecting any byte beyond the exact outer artifact cap and requiring exact final size/digest plus successful subprocess exit. Parse its full central directory; require exactly the expected regular inner LinuxZIP filename, no duplicates/symlinks/traversal, and the exact pinned inner size. Stream that member to a fresh owned workspace file with CRC/SHA/size validation; rename only after success. Keep bounded failure evidence and account for retained partial bytes.
4. Independently qualify the inner ZIP/member manifest, actual PCK/provenance/fonts/source closure against source1741 and the exact CI run/tool pins. Validate the new archive’s godot member85,447,128B/SHAe69af4f6…6d54e and0755 BEFORE considering reuse. No prior package source identity is transferred to the new artifact.
5. Reuse only W1 protected extracted `/workspace/scratch/yuga-continuation-W1-r1/package-r2-extracted/godot` after explicit owner immutable-use agreement, fresh exact hash/mode/dev/inode checks and new archive member equality. It is already0755. The installed tooling engine is0700 and must not be hardlinked then chmodded. Link only the verified engine into a fresh extraction; copy/extract the other45 members privately. Never chmod/write either engine alias; record the admitted link-count/ctime change and verify bytes/mode before/after actual execution. If that immutable-use contract cannot hold, use a private engine copy only after admitting the extra85.45MB. Preserve W1 old PCK/cache and all public evidence.
6. Actual extraction/member validation, native route/clock/input evidence and publication remain distinct later gates; CI success or transport metadata alone qualifies none of these.

Capacity observations: after the separately backed one-PCK cleanup free space was797,126,656B. Prior private extraction excluding engine was71,237,211B. Conservative ordinary disk-outer peak using2×new artifact bound plus500MiB+64MiB allowance is787,209,138B, leaving only9,917,518B before other writes. Approved RAM-outer route projects97,906,137+71,237,211+524,288,000+67,108,864=760,540,212B, leaving36,586,444B at that observation. These are estimates until new inner/member pins are read. Root expects~65MB additional motion output: if all persists, the same conservative admission would FAIL by~28.4MB. Reaudit after the actual queue; do not reduce reserves or start downloads on this old measurement.
