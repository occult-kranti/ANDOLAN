# Published native screens and controls preview

[Download Linux or Windows](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-ui-2026-10-18). The prerelease became public on 18 October 2026 at 02:10:32 UTC, targeting source `9e81a7c849837dea477ddb5a8c93f43665774573`.

| Archive | Bytes | SHA-256 |
| --- | ---: | --- |
| Linux | 137812335 | `56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5` |
| Windows | 145813678 | `16f6e210fef90f26c1c725e503805fb5e9c4ee76d64e86cb2ff7b0788ea186c5` |

Both archives contain the exact qualified PCK `d387d34ad37fc959f974b9ced0107d5ad2a0e2505e55a090dd20fc583d62aa27`. The release also supplies `SHA256SUMS.txt`, `native-export-manifest.json` and `native-package-manifest.json`. Extract the whole archive and run `launch.sh` or `launch.bat`.

## Qualification

The five screen rounds and three integration rounds have completed their recorded scope. [Build provenance](../role06/REVIEW.md), [actual package execution](../role03/REVIEW.md), [navigation](../role01/REVIEW.md), [theme and glyphs](../role02/REVIEW.md), [HUD and outcomes](../role04/REVIEW.md) and [saved preferences](../role05/REVIEW.md) retain their exact inputs and limits. All 525 runtime inputs still equal the qualified source. [Native foundation CI](https://github.com/occult-kranti/ANDOLAN/actions/runs/39087210717) passed at that source.

Linux execution includes real native input, a same-save fresh-process relaunch and three clean Quit exits. Reviewers inspected the originals; all 57 PNGs and state records remain archived. The first process required two recorded capture-tool input recoveries. Relaunch and the separate staged result/respawn supplement required none. The staged supplement exercises actual rule methods but is not a naturally won match. The combined 43-check validator passes against repository archives after exact original log copies were restored.

## Publication route

Direct asset upload returned HTTP 401 even though Git and the GitHub API worked. A temporary isolated branch carried six bounded chunks of the already qualified ZIPs. [GitHub Actions run 39089069718](https://github.com/occult-kranti/ANDOLAN/actions/runs/39089069718) reconstructed and hash-verified those exact files, then uploaded them only to the fixed draft. It performed no rebuild or package execution and did not publish. Root separately verified all five API asset hashes and sizes, then published through the working API. The transport uses the runner's standard token; no credential was extracted or stored.

[Independent public-download verification](download-review.md) passed: all five fresh public downloads match the qualified local files and release digests; both ZIPs pass every member CRC and declared payload hash. Each PCK also passes all 519 internal entry checks. The public tag resolves to the exact qualified source. The [machine-readable receipt](download-verification.json) keeps the commands, URLs and results; no downloaded executable was started during that audit. The [transport archive](transport/README.md) preserves the upload recipe and exact-byte checks.

After that verification, the temporary transport branch was removed with exact expected-commit guards. The [cleanup receipt](transport-branch-cleanup.json) records unchanged production HEAD/branch and the recovery route from the published ZIPs. No Git object pruning or source deletion was performed.

## Remaining limits

This is an offline desktop preview. Windows is archive-validated but unexecuted. Software Vulkan and Dummy audio do not establish physical-GPU performance or listening quality. Compact HUD text is small. Foot contact, motion transitions, garment contact, world and soldier art, the full roster and native online matches remain open. The Deadlock-level visual target has not been reached. The earlier R4 motion tape has a different source and is not a recording of this package.

Follow the [current screen handoff](../../../../SCREEN_CAMPAIGN_HANDOFF.md) and [roadmap](../../../../ROADMAP_BACKLOG.json) for the next work. Later evidence/documentation commits retain this package's source identity; they do not relabel its bytes as a new build.
