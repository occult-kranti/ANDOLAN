# Historical workspace backup

The manifest names 773 exact historical source, art, evidence, log, design-note and UID files preserved on `backup/yuga-workspace-2026-10-18`. This is a recovery snapshot, not an accepted game build. Use `game/yuga-native-production` and its active handoff for implementation.

The snapshot uses a separate Git index; the current branch, working files and normal index remain intact. No files are deleted. Cache archives, font caches, private Git indexes, dependencies, exports and local private state are excluded. The manifest records path, size, mode and SHA-256 for every selected original.

Recover individual paths with `git show backup/yuga-workspace-2026-10-18:PATH` into a fresh file and verify its recorded SHA-256. Preserve existing local files; do not reset or wholesale merge this historical snapshot into the game branch. The main handoff records the remotely verified backup commit.

Verified remote snapshot: [`cd3180e1de00eccfc335587ba6283585236019c0`](https://github.com/occult-kranti/ANDOLAN/tree/cd3180e1de00eccfc335587ba6283585236019c0). [Push receipt](push-receipt.json) and [exact file manifest](file-manifest.json) are retained on the production branch.
