Propose removal of exactly two regular, single-link public r4 ZIP aliases under `/workspace/scratch/yuga-desktop-integrated-package-r4/build`. **No deletion performed.** They occupy **243,978,240 allocated bytes** (243,968,199 logical bytes). Both are mode 0600; exact inode/device/mtime/link count and absolute paths are pinned in recovery-map.json.

| File | Bytes | SHA256 | GitHub asset ID |
|---|---:|---|---:|
| `yuga-native-linux-x86_64.zip` | 97835664 | `27c36e5523643c647b245614721c0160b3d1548bf6da851d922886cffc180d0e` | 653297487 |
| `yuga-native-windows-x86_64.zip` | 146132535 | `34d8c19d30f7cafe6ad56247c2524d09c15f307cc0cde20572a56eb3d29b1fc6` | 653297683 |

Fresh local full SHA256 hashes match both the retained independently downloaded W5 audit and a fresh standard GitHub release API response. Release 416367666 remains published at the exact tag yuga-desktop-finish-2026-10-18; asset IDs, uploaded state, sizes and server SHA256 digests are unchanged. These are the published r4 source 96d5 artifacts, not a package of the newer 0964564 frontage source. No stale asset identity was found and no ZIP was downloaded again.

Each recovery entry gives the exact public browser download URL and API asset URL. To recover, download to a fresh temporary path, verify exact byte count and SHA256, apply mode 0600, then restore only if the destination is absent or already byte-identical. Never overwrite a differing file. The prior public audit also checked ZIP payloads; local SHA agreement binds these aliases to those already audited bytes without another extraction.

Fresh process metadata found no exact target open FD or mapped path and no inaccessible live process owned by the current UID. The 175 zombies are recorded separately; they have no live file-descriptor tables. Two other-UID platform processes (PID 123/175, UID 0) denied FD/maps access; their absence of holdings is not claimed. All observations are point-in-time. W1 and W5 explicitly release only these two aliases. W6 was at capacity and supplied no fresh release in this packet; root must resolve final coordinator ownership before execution.

Preserve all Linux actual extraction files, raw Linux and Windows PCKs, manifests/reports/logs/source/caches/user state/originals, and every other file/directory. Parent must retain or commit this small recovery proposal and then recheck exact hashes/stat identities, releases and open holders immediately before executing any removal. audit.py has no delete option. This worker changed no canonical source or index and ran no engine.
