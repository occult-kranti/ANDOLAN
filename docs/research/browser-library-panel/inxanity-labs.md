# INXANITY Labs source-reuse panel

15 November 2026. Product: YUGA native and its separate browser builds. Research
lane only; baseline `work/yuga-studio@7162b5d0`. Existing uncommitted work and
incoming videos were preserved. This lane owns this report and
[the source/access ledger](inxanity-labs-sources.json), not production code.

## Panel decision

The strongest immediately useful donor is **Universal Modder's MIT-licensed
offline GLB/Blender inspection code**, linked directly by the INXANITY homepage.
Use a bounded helper on our original Rama/Relay Foundry assets, retain its
copyright/license, and record actual geometry/bounds/material/camera results.
It needs no INXANITY membership, commercial game data, fal API or MCP registration.
The build owner has received exact pinned files and is implementing that spike.

INXANITY itself is a Windows membership launcher/community and public game-link
catalog. Public access did not expose launcher source, its private MCP source
or a downloadable launcher without checkout. Its screenshots and marketing
claims do not establish code access, a reusable engine or tested functionality
in this workspace. The public terms explicitly separate membership from rights
to the games/ROMs/assets a mod requires. [Homepage](https://www.inxanitylabs.com/),
[terms](https://www.inxanitylabs.com/terms).

## What was actually accessible

- Raw homepage, `/mods`, `/terms`, `robots.txt`, small `hero-logos.js`, and the
  public `/assets/dome-games.json` were retrieved normally. The JSON contains
  **216 slug/title/cover records**, not source code or game executables. Its
  SHA-256 is `64fecf78eb66469e9e97bf9430c1f8c498243c8f9d8d130d0f5865e195fb8250`.
- Homepage HTML is 109,775 bytes, SHA-256
  `16b6039bbdec36b39a77b59e79da550f8b67fb2e5c41147567a773bf5561cdaf`.
  A default urllib request returned 403; a normal browser User-Agent succeeded
  with 200. Root independently retrieved exactly the same bytes.
- Inline gallery code identifies a plain-JS port of React Bits Dome Gallery
  with **MIT + Commons Clause** terms. Visible webpage JS is not automatically
  an unrestricted code donor. No gallery/UI code or cover artwork was copied.
- Public Git source and immutable license/source files were retrieved for the
  projects below. No upstream script/launcher, game binary, ROM or extracted
  commercial asset was run or downloaded in this lane. Checkout/account changes
  and persistent integration were not attempted.

The site's claims about game counts, one-click verification, tested mashups and
browser-port performance remain creator claims unless independently tested.
The public catalog's availability is distinct from each linked port's license.

## Concrete candidate matrix

| Project / verified source | Specific resource worth using | Terms / data boundary | Decision |
| --- | --- | --- | --- |
| [Universal Modder](https://github.com/rehan-remade/universal-modder/tree/3c4ac6c38e411b8c543bce217eae197039516bfc) | `um/render3d.py`, `um/blender/render_sprites.py`: transformed GLB bounds, explicit model grounding/scale, camera/heading normalization, repeatable still/turntable renders. Collision/combat field notes help expose ownership/unit/epoch questions. | Exact root MIT license verified. Keep the copyright/permission text with adapted code. Its illustrative synthetic root motions are not production skeletal animation. Optional fal services/plugin installers are separate and unnecessary here. | **Adopt a bounded offline helper**, then run on owned assets with input/output hashes. |
| [2010 Rust Rewrite Mashup / IW4L fork](https://github.com/chasmlol/2010-rust-rewrite-mashup/tree/f608f85e407ff1b7689d54a9aafdd16e95711ac4) | Public Rust `movement_iw4` accelerate/friction/slide, input-to-command separation and controller targeting. Reusable small pure algorithms may support a later isolated Godot feel test. | Apache-2.0 LICENSE plus NOTICE verified. Full runtime requires owned MW2 data and optional Skate 3 data; Minecraft first-run downloads proprietary game files. Source units/constants are not YUGA tuning. Preserve notices/change attribution if actual code is adapted. | **Source study / separately reviewed pure-code adaptation**; do not run the full mashup in this intake. |
| [N64Recomp](https://github.com/N64Recomp/N64Recomp/tree/598ce2080004a5672d604dceadbda436045307b7) | Symbol/metadata-driven translation, overlay separation and recorded patch inputs. | MIT tool. Needs a selected binary/ELF metadata and an appropriate runtime. Generated game code does not gain the tool's MIT grant. | **Defer**: no selected owned N64 input answers a current YUGA question. |
| [XenonRecomp](https://github.com/hedge-dev/XenonRecomp/tree/ddd128bcca99fe8bfbb99bea583c972351fa6ace) | Function-boundary/jump-table analysis and explicit patch configuration. | MIT tool; converts Xbox 360 XEX code to C++, not a complete game runtime. No XEX/game input was accessed. | **Defer**, keep as an analysis reference. |
| [libsm64](https://github.com/libsm64/libsm64/tree/fd11813208272b4271d92bd92feb8f3fdbe61be5) | Clean C API boundary, surface-collision and state update organization. | Root CC0 code verified; runtime requires a user-supplied official ROM for textures/animations. CC0 does not grant Mario art, animation or marks. It is not a drop-in Rama controller. | **Architecture study**, no ROM/assets or avatar import. |
| [GhidraMCP](https://github.com/LaurieWired/GhidraMCP/tree/1e980252087b2479a21b9ca6d82d5829538651a7) | Bounded native analysis if source cannot answer a selected owned-binary question. | Apache-2.0; no Ghidra process/bridge installed or registered by this lane. Tool licensing does not license targets. | **Defer**; readable source is available for the chosen helper. |
| [BepInEx](https://github.com/BepInEx/BepInEx/tree/dbc82f05b8ea34833de5b6a723eb60dd8398e0b1) | Loader/plugin initialization and versioning architecture for future owned Unity/.NET targets. | Root LGPL-2.1 license retrieved; dependency/per-file obligations require separate review. Host game and asset terms stay separate. | **Defer**: not a native Godot runtime dependency. |
| [AI game modding guides](https://github.com/trevaintdead/ai-game-modding-guides) | Bridge-contract, lineage, playtest and handoff templates named by the cached README. | Live `git ls-remote` returned repository not found. Exa returned cached text describing MIT, but exact current license/source bytes were not accessible. | **Unavailable primary source**; do not copy from a cached license claim. |
| INXANITY Launcher / INXANITY MCP | Observe useful workflow patterns: explicit required game/version, backed-up files, actual readiness before Play, reversible uninstall. | No public launcher/MCP source license established. Terms say Windows 10/11 and membership; public page/gallery rights are not a blanket MIT grant. | **Original design inspiration only**. |

## Selected source contract

Universal Modder pin: `3c4ac6c38e411b8c543bce217eae197039516bfc`.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `LICENSE` | 1,096 | `db6cfa2ad2c44f73080440c866c4a3a078749d84ba40b4dfa27d50f18a525543` |
| `um/render3d.py` | 6,882 | `7352f7cf80f2d8b8b30e1627ba8b2786bc9c21315b89c2f55258c5b62767dfa9` |
| `um/blender/render_sprites.py` | 8,040 | `358dc36a2712f640b02da6d5ce28ef48cc54daebc5a4760c790997fb2e27bd71` |

The CLI writes a configuration and calls Blender. The Blender helper imports a
GLB, computes bounds from transformed object corners, centers/grounds/scales a
root, creates a camera/light, then renders explicit headings. The `bob`, `lunge`,
`die` and `spin` examples transform that root; they do not demonstrate rig/clip
playback, weapon contact or animation quality. Use still views for the initial
inspection, preserving original GLB and .blend files.

Finite acceptance for the build owner: pin/source/notice, no source-asset changes,
nonempty mesh/material/bounds results, explicit source-to-camera transforms,
finite dimensions, actual original output views inspected, failure for missing
or malformed input, and truthful static-render scope. Any later clip/rig review
needs a different test and actual animated evidence. The source helper can
advance asset review; it does not complete hero art or match gameplay.

The Rust donor's `accelerate_velocity` has a hard minimum wish-speed in original
game units, and its controller helper carries original FOV/range/timing values.
A direct GDScript translation without unit and behavior tests would alter YUGA
feel arbitrarily. Keep Godot physics and current authority unchanged while
studying one explicitly bounded algorithm. The caller should compare held-out
inputs, collision/ramp behavior and frame-rate independence before promotion.

## Verification and handoff

This lane used four Exa searches requesting **20 result slots**, then direct
primary-page/source inspection. Slots include duplicates/irrelevant results;
eight live repositories were attempted, seven pinned successfully and one
source-guide repository was unavailable. Twenty-four initial immutable source
and license records plus additional selected input/build files were inspected;
the JSON ledger retains exact accessible URLs and hashes.

No native renderer, emulator, game, mod or decompiler was executed by this
research lane. Root/build owners separately own the selected helper's actual
execution, product edits, output inspection and credits. Round-2 challenge:
source-readable does not mean asset-reusable; source preparation is not a built
game; a static render is not animation; catalog metadata is not reverse-engineered
game source. These counterexamples remain part of the adoption decision.
