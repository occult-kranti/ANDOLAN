# Bounded storage recovery and integration

The storage proposal selects **182 inactive asset copies**, totaling **1,034,369,742 logical bytes / 1,034,743,808 allocated bytes** (986.8 MiB). Every selected regular file has one link and matches one of 17 independently read Git blobs in remote-verified `a7c9f46bbbfeef59a042919231978436892be934`. The seven historical project roots are listed in [recovery-map.json](recovery-map.json). Nothing has been removed by the preparation check.

Root, W1 and the current hero owner released only these copies; see [owner-releases.json](owner-releases.json). Current continuation work, canonical sources, captured originals, caches, logs, user data, unmatched files and directories remain protected. Accessible processes had no references to the seven roots. The inaccessible `dockerd`/`containerd` processes are disclosed; zombies hold no files. Fresh checks repeat before execution. This operation concerns `/workspace`; it does not relieve the separate `/tmp` filesystem.

[storage-verification.json](storage-verification.json) records 182/182 verification, zero removals. [cleanup.py](cleanup.py) checks exact path scope, Git path/blob identity, SHA-256, size, mode, device, inode, allocation, nlink, remote ancestry and accessible process references. Removal additionally requires the map, owner release, this README and the guard itself to match the current remote commit. Root must acknowledge execution after publication. No canonical Git/configuration changes are performed by the guard.

After root confirms the pushed map and authorizes execution:

```sh
python games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/cleanup.py --remove --output games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/storage-execution.json
```

The guard records each removed path with its original bytes, mode, inode and recovery identity. It refuses to overwrite a previous receipt and retains a partial execution receipt if interrupted. No new engine/test/import/export is required for removing these inactive copies.

To restore an individual selected file, read its exact `blob` with `git cat-file blob`, confirm the recorded byte length and SHA-256, create its recorded path exclusively (never overwrite a later file), and apply its recorded filesystem `mode`. The `git_path` at `recovery_commit` independently identifies the same blob; filesystem mode differences from Git mode are preserved in the map. Restoration must be budgeted because the seven historical trees will intentionally be incomplete afterward. Do not run an old project until its required files have been restored and verified.

Integration source reviews will be recorded separately under this owned packet after the storage execution closes. No visual acceptance follows from this storage audit.
