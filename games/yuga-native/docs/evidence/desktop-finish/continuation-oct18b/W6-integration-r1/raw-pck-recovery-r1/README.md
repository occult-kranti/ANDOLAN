# Exact old Linux raw-PCK recovery preparation

One selected candidate: `/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2/build/yuga-native-linux.pck`,70,594,852 logical bytes/70,602,752 allocated bytes, SHA256f2be4e20a0f3ea3915c5ab94e3896278ab4778991e80c6c8abaadc5209511a59, originalmode0644. It is inactive, regular, nlink1 and distinct from protected W1 actualPCK.

Recover exact bytes from retained publicLinuxZIP781d904d… member `yuga-native-linux-x86_64/yuga-native.pck`; restore recorded0644 mode. The guard hashes the entire retained ZIP against independently published/audited evidence, checks its exact46-member census and streams/hash/CRC-validates the70.6MB member against qualification and candidate. All five public files, W1 extracted PCK/runtime, build manifests, source/caches/evidence/user state remain protected and are rechecked.

Root/W1/W3/W6 explicit exact releases/custody are in owner-release.json.23 bounded controls and fresh1-file full local dryrun pass. No deletion yet. Accessible process refs are empty; inaccessible PIDs/limits remain in the raw map/check.

This guard imports only the previous bounded ZIP-alias helper after verifying exact b551cbd4 hash BEFORE Python import. Remote backup must include this new guard/map/owner and the imported old helper plus immutable public-audit/qualification receipts (old proofs already tracked). It admits no generic target selection or recursive cleanup. Atomic execution receipt records the only unlink.

Root must remotely back up/review before authorizing removal. Literal removal invocation, after substituting exact reviewed backup identities:

```sh
python3 -B games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/raw-pck-recovery-r1/raw-linux-pck.py --plan /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/raw-pck-recovery-r1/recovery-map.json --plan-sha256 ffff28c08ce59af530b98f76af1c7e33c087d22e0d3424090686aa458e2b367a --report /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/raw-pck-recovery-r1/execution.json --remove --backup-commit EXACT_REMOTE_COMMIT --backup-branch EXACT_BACKUP_BRANCH
```

GitHubCLI2.46 artifact download spools an entire outerZIP using os.CreateTemp("","gh-artifact.*.zip"), extracts innerZIP while outer remains, then removes outer. Explicit owned `/workspace` TMPDIR and peak outer+inner admission are required; default `/tmp` is unsuitable. CI39147837494 succeeded but artifact access is403 at an unapproved Azurehost pending user activation; no retry/alternatehost/proxy or artifact qualification claim.
