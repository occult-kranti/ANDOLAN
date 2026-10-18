Runtime commit proposal against `0412db42f0a3da8afa1c30b33be6239d04f7afe8`: **112 exact files, 7,501,116 bytes**. No staging or source edits performed. Normal CI must run; do not add a skip-CI marker. Root owns the commit/push and later CI observation.

The first ten selected paths are the eight W4/W6 production/test files plus final WORLD-LANE-FRONTAGE.md and ASSET-NOTICE.md. Their exact owner/current notice hashes are in scope.json. The explicit runtime UID sidecar is included; unrelated generated UID and __pycache__ outputs are excluded. Remaining 102 paths are unique sealed R2 source, W1 actual R2, W4 production and W6 package proof artifacts. No broad directory add is needed.

manifest.json records every path/SHA256/Git blob ID/size/physical and Git mode. allowlist.paths0 is the exact NUL-separated add list. Mode counts: {'100644': 111, '100755': 1}. 8 explicitly selected sealed artifacts are normally ignored, including raw logs; parent should use the exact list with forced inclusion rather than broad directories. No file exceeds 95 MiB. Eight duplicates recover from another selected path and nine from exact committed 0412 blobs; recovery-map.json records all 17 aliases. Runtime paths take priority over identical historical source copies so the shipping JSON and module/test files cannot be omitted through deduplication.

All 128 receipt artifact checks passed. This does not close W4 route checks, W1 production integration capture or a new exported package. Accepted R2 component art retains its stated limits; independent package witness proves only its bounded synthetic source-binding checks. Remaining clay/motion/cleanup/general Backup C payloads and parent changing docs are outside this list.

Suggested parent staging form, after rechecking all manifest bytes/modes:

    git add -f --pathspec-from-file=/workspace/scratch/yuga-frontage-runtime-commit-plan-r1/allowlist.paths0 --pathspec-file-nul

The command above was not executed by this worker. Preserve manifest/recovery-map/receipt metadata alongside the payloads under a new evidence prefix; metadata files are not counted in the 112 payload files. HEAD/index stayed exact during inventory. Root may add its own commit metadata deliberately; do not implicitly include unrelated working changes.
