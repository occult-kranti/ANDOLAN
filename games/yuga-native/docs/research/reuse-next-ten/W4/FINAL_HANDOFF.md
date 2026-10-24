# W4 final boundary — 24 October 2026

**Frozen: one reused Lanka gate is enabled in the native Confluence game.** Its carved source entrance, real opening and pier cover were reviewed in actual day/night frames. Existing source meshes, UVs, materials and image bytes are preserved. This is one accepted map section, not a full-map or commercial-quality claim.

Production is `scripts/lanka_lane_gate.gd` plus the self-contained `assets/world/lanka-lane-gate.scn`. Confluence adds the construction/report and configures the existing army with a deep private copy of the manifest containing ten source-derived ground footprints. Original map files, army source, eight authority solids, eight decks and ten anchors remain intact. This corrects the reproduced AI shooting-through-pier bug without filling the arch opening or changing browser authority.

| Frozen item | SHA256 |
| --- | --- |
| Final combined world | `4f81cbbe3d0fba76e39daae76bee7c312b1feec9e87c283bcb0e116e419eb8ea` |
| Native helper | `aba897af4f5683df031841c7e8c10d1b8a8e81e1e359f62ce491318630865238` |
| Native scene, 3,793,793 bytes | `e895e0aaef172901e445aa1e782b7ecbfbdf6b021cf13f1c311db3c60cae7d25` |
| External package probe | `7e45afdaf1908e9a84443fcbd2ac8b1179d4a82a8f747817e12a8f1abed5e54d` |
| Real exported PCK, 74,404,664 bytes / 553 entries | `55bf2c325d03b3869ff3a8bf2551005462c3a00e4df5c3680ebfa80f53d99a52` |

Passed checks: isolated source/physics 22; native correspondence/cache/lifecycle 17; fresh rebuild equivalence 6; army footprint/copy/reset/LOS 14; final canonical integration 23; retained legacy physics 29 with an explicit gate opt-out; unchanged strict render-resource 40. Independent QA additionally passed 18 actual full-role collider/height-sensitive ceiling and broad-box negative checks. Whole-file rebuild identity is not claimed because Godot resource IDs may differ; source attributes/material/image/collision/footprint data must remain equal.

Root ran the corrected external probe **against the real exported Linux PCK from outside the checkout: 13/13, exit0**. Mounted `res://project.binary`, actual packaged scene FileAccess/hash, production helper, shared resources, unique collision, open passage, pier cover and private army-copy behavior all passed. The launcher independently records actual `--main-pack` argv and pack hash. The `--expected-pack` user argument labels report identity only. The initial engine-consumed-argv failure is retained as a diagnostic. See the [actual package report](../root/native-export/gateway-package-probe-r2.json) and [launch receipt](../root/native-export/gateway-package-launch-r2.json). Matching Linux/Windows PCK identity is recorded; **Windows execution and a newly published release are not claimed**.

Actual art evidence is in `art/map-reuse-placement/`: corrected ordinary southbound day/night images, the 72-frame staged traversal video, selected originals and exact historical source snapshots. R1 held import-A-pose stills remain diagnostic. R2 uses a different ordinary southbound camera and properly evaluated idle; it is not relabelled as the northbound R1 baseline. These earlier art frames use their own frozen HUD/motion bytes; current combined-source journey evidence is owned by W2/root.

Current comparison tools explicitly disable the already integrated gate before building their isolated comparison candidate, evaluate the production idle, and probe actual army heights/radii. Their affected current checks passed 23/27/14 after the earlier full CI local receipt; that earlier receipt remains bound to its original parent-script bytes. The final GitHub CI step executes current source.

Next owners: root owns final publication and exact-source release checks; W2 owns the normal combined-source journey; W6 owns native 3D authority/online work. Continue modular adoption one distinct source section at a time, with actual collision/camera/ordinary art gates. Physical-GPU performance, temporal/LOD review, the full map and commercial visual parity remain open. Mobile remains deferred. No further W4 code, asset or source mutation is planned.
