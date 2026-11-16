# Browser-library panel — actual access and build feasibility

15 November 2026. Build owner: `/root/reuse_build_panel`. Baseline is
`work/yuga-studio@7162b5d0b666e4422b0bc73100e1fba947d3323f`, with the earlier
studio changes and user files preserved. This audit owns this document and
[its machine-readable record](access-and-build.json). It initially changed no
product source, ran no old game suites and started no heavy renderer.

## What is available now

Sixteen lightweight version probes returned exit 0. An original blank-page
Playwright fixture also launched successfully, validated an empty WebAssembly
module and reported no page errors. This establishes tool availability, not
successful execution of either supplied site's games.

| Tool / access | Executed observation | Practical use and limit |
| --- | --- | --- |
| Godot | Official 4.6.3, `godot --version` | Existing native runtime, scenes, typed receivers and focused headless fixtures. Software rendering and the earlier qualified public runtime retain their separate receipts. |
| Blender | `blender4.3 --version` → 4.3.2 | Owned GLB geometry, bounds, rig/material and still-view inspection. No paid generation API is needed. Blender output alone does not accept native contact/motion. |
| REA | Actual CLI `--version` → 6.5.0; JavaScript analyzer help works | Bounded static JS/TS/Electron source reconstruction. Existing prior owned-source analysis has a comparison oracle for three exports; it is not commercial-game recovery. |
| Playwright Chromium | Actual browser 156.0.8078.4 at `/home/codespace/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome` | Public page/client/network inspection and owned HTTP fixtures. Browser WebAssembly API works; that API does not recover original source or server behavior. |
| Native tools | GNU objdump/strings 2.42, file 5.45, C/Clang compiler, readelf, Java/Javac, gdb/lldb discovered | File/section/symbol/assembly inspection and original executable oracles. No third-party native program was executed by this audit. |
| FFmpeg/ffprobe | 6.1.1 | Media metadata, static frame review and encoding. The two new user videos were only hashed/probed, not watched or decoded here. |
| Python/Node | Default Python 3.14.2; authoring Python 3.12; Node24.22.2/npm11.19.1 | Existing isolated authoring/analysis environments. Native provider dependencies must use a compatible environment rather than assume default Python suffices. |
| Public source preparation | Four existing exact source/notice receipts: REA, script-only GDQuest TPS, Rapier, HyperFrames | Reuse the existing pinned intake helper. A checkout is neither an installed runtime nor permission to use unrelated artwork. |
| Connected source tools | Exa and public Git/HTTPS access are available to the panel | Findings are traced to primary repo/license files by the site researchers. Tool discovery alone is not proof of access to a private account or game server. |

No `cargo`, `rustc`, `wasm-tools`, WABT (`wasm2wat`/`wasm-objdump`), Emscripten,
Ghidra launcher/headless executable, rizin or radare2 was found on PATH. Ghidra
was not found in inspected tool-root directories; an unprivileged `/opt` scan
could not read its containerd directory. Repository records describe earlier
Ghidra12.1.4/native-provider work but do not establish that those tools are
restored on this host. No MCP server was registered during this audit.

The source-backed native analysis helper remains useful: choose an accessible
owned/permitted binary, retain its version/hash and a narrow behavior question,
then use `tools/native-analysis/inspect-component.py` with a separately restored
provider and independent executable oracle. For readable source, direct source
inspection is preferable to compiling it merely to make a decompilation claim.

## Panel source candidates and contracts

| Candidate | Scope verified by panel | Small useful adoption / counterexample |
| --- | --- | --- |
| [universal-modder](https://github.com/rehan-remade/universal-modder/tree/3c4ac6c38e411b8c543bce217eae197039516bfc) | MIT LICENSE SHA `db6cfa2ad2c44f73080440c866c4a3a078749d84ba40b4dfa27d50f18a525543`; inspected `um/render3d.py` and `um/blender/render_sprites.py` | Adopt transformed-corner bounds and camera/headings into an isolated GLB inspector. Preserve raw metre-scale geometry; render still views with input/tool/camera hashes. Exclude synthetic bob/lunge/die root transforms from any animation/contact claim. |
| [Vice City browser client](https://github.com/JonCodeOfficial/gta-vice-city-wasm/tree/5c6cccc56c1df5c3717c0b39953d5fe833f97b73) | MIT explicitly covers original client, Service Worker, OPFS layer and build tooling; engine/game data excluded | Study OPFS/save and immutable asset-serving workflow. Source Range handling returns a full 200 when invalid/unsatisfiable; repair semantics and same-origin boundaries before adapting any server/cache handler. |
| Existing native YUGA | Original offline armies, last-hit rewards, Rama vitals/kit and source-pinned map | The highest-value immediate game gap is earned gold with no native spending/return-to-base decision. Reuse owned receivers for a live field shop instead of adding a new engine or unavailable hero roster. |

The agreed asset-inspector contract was a bounded original CLI plus adapted MIT
framing snippets, three still views, geometry/material/armature/action census,
projected camera-fit checks, preserved input hash and complete MIT notice. It
would use owned Relay Foundry/Rama assets and existing Blender, with no toolkit
installation, fal/API credentials, synthetic motion or MCP registration.

Root first redirected priority to actual native gameplay. After the original
field shop passed its 50-case fixture and froze, root authorized the bounded
MIT-adapted inspector. It now has code, the complete upstream notice and 27
passing tests, extended to 28 after independent review reproduced and repaired an
empty-worker-JSON false-success counterexample and challenged finite bounds.
One serialized actual Blender job then rendered three stills with unchanged
source bytes; all three were visually reviewed. See the
[tool contract and evidence](blender-inspector.md).
No foreign game data or engine code was copied into product sources.

## Current gameplay implementation assignment

Root owns HUD/shop UI and `confluence_world.gd`; the build owner is assigned the
original `native_field_shop.gd`, declarative `native-field-shop.json` and focused
tests, using existing heal/ammo/shield/temporary-unit receivers. Its interface
and bounded failure cases were sent to root before editing. The source/catalog
are frozen; 50 focused cases pass. Root coordinates integration and assigned
the content revision8→9 migration to the separate contract owner.

The API is `configure(army, runtime, player, spawn)`,
`purchase(item_id, expected_epoch, nonce)` and `report()`. The shop owns offline
spending, not enemy rewards; `army.gold` remains a monotonic earned total for the
round. A new reset epoch invalidates stale commands. Scene pause, outcome,
defeat, range/height, invalid nonces, duplicate/reentrant calls, unavailable
receivers, no-benefit purchases and blocked unit placement must be challenged.
Those tests do not substitute for the root's actual in-world shopping journey.

## Media intake observation

`gameplay.mp4` and `all ults.mp4` appeared as untracked inputs. The first probe
recorded H.264 640×360/AAC with durations 2046.885442 and 2595.874830 seconds.
Root subsequently observed increased sizes/mtime during upload. Their hashes
and byte counts in the JSON are **preliminary intake snapshots**, not stable
analysis inputs. The media owner must freeze and rehash completed uploads before
describing their contents. No frames were viewed or narrative inferred here.

## Handoff

Executed: tool/version probes, a tiny original browser capability fixture,
source/helper/license reads, metadata/hash-only video probes. Source helpers and
lockfile hashes are retained in the JSON. No native game suite or renderer was
rerun for this documentation audit. Any later shop/source changes and checks
have their own source-bound evidence under the video-study continuation.

Next owner: root integrates selected original gameplay work; site researchers
finish primary-source/reuse matrices; the independent reviewer challenges actual
shop behavior and final captures. Native online authority, full roster,
commercial art, physical-GPU performance and human feel remain separate gates.
