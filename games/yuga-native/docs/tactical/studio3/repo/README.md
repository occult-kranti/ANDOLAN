# Studio3 repository and CI audit

Task: read-only maintenance support for the user-authorized finish2 source push,
then CI/control-coverage review. Product: native YUGA · Sanctum. Reviewed on
16 November 2026; CI results below were retrieved at 03:05 UTC through the
GitHub plugin. Root owns Git, ignore rules, workflows and publication. After
the read-only diagnosis, root assigned this owner one focused test correction
in `tools/map-reuse-placement/test_integrated.gd` and this evidence directory.

The pushed checkpoint is
[`e59a07a4786e9ad491cfef7a4e706dbd06063adc`](https://github.com/occult-kranti/ANDOLAN/commit/e59a07a4786e9ad491cfef7a4e706dbd06063adc)
on `game/yuga-native-production`, following `143289f410ef17ced20d0546efc7fccafee75ba9`.
The working branch remains `work/yuga-studio`; subsequent studio3 edits are
separate from that checkpoint. `git show --format= --shortstat e59a07a4`
confirmed 881 files changed, 176,998 insertions and 78 deletions.

## Repository boundary

The initial inventory contained 24 modified and 5,333 untracked files,
472,039,205 bytes altogether. Eight nested capture user directories accounted
for 4,478 files / 85,828,522 bytes, chiefly Godot/Mesa caches. Excluding those
left 879 files / 386,210,683 bytes before root's ignore maintenance. The largest
candidate file was a 5,588,912-byte editable Blender source. There were no
candidate files above 50 MiB. No tactical user-state paths were already tracked.

Root added recursive tactical `**/*-user/` and `**/user/` exclusions. This closes
the earlier one-level `evidence/*-user/` gap without deleting local evidence or
settings. The excluded roots were the two package-input `user/` trees and the
finish2 final-motion, final-visual, hero motion-probe, map visual-probe and two
UI showcase-probe user trees. No configuration contents were copied into this
report.

Safe checkpoint content includes runtime scripts/shaders/assets and their
required sidecars, notices, original art/editable sources, authoring tools,
focused tests, source receipts, accepted original captures and meaningful
failed attempts. Keep `dist/`, `.local-tools/`, `.godot/`, dependency caches,
credentials and capture user state outside source Git. Supplied reference
MP4s and bulk decoded reference streams retain their existing local-only
boundary. Do not remove archived failures or relabel historical packages.

The audit found two meaningful SURYA export logs omitted by the generic
`*.log` rule: `art/tactical/surya-carbine/export-r1.log` (695 bytes) and
`export-r2.log` (1,105 bytes). Root subsequently added the scoped tactical-art
log exception; both appeared untracked after the checkpoint. They still need
inclusion in a successor commit. The failed first export remains useful
provenance, alongside its successful correction.

There are no LFS rules in `.gitattributes`; current attributes preserve selected
raw evidence rather than changing binary storage. The observed Git object
store was already approximately 4.37 GiB. Future bulk films/original sequences
need durable artifact storage with committed source hashes and recovery links;
this observation does not authorize deletion or history rewriting.

Final local finish2 ZIPs are 119,668,939 bytes (Linux), 167,965,819 bytes
(Windows) and 613,742,452 bytes (source/art archive). They remain under ignored
`dist/sanctum-finish2-r1/`. GitHub warns above 50 MiB and blocks ordinary Git
files above 100 MiB; release assets have a separate limit below 2 GiB per file.
Use artifact/release storage for these archives, retaining exact SHA receipts,
rather than force-adding packages or submitting hundreds of Contents API
writes. See [large-file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
and [release assets](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
The prior [publication receipt](../../PUBLICATION_2026-11-15.md) and current
[finish2 delivery](../../finish2/DELIVERY.md) distinguish source pushes,
dashboard publication and native packages. This audit did not publish a release.

## Actual CI result for e59a07a4

| Workflow | Observed result | Scope |
| --- | --- | --- |
| [YUGA native build candidate, 43795505687](https://github.com/occult-kranti/ANDOLAN/actions/runs/43795505687) | **Success** | Package helper checks, verified runtime preparation, source binding, import, both package exports and artifact retention completed. This is a CI candidate, not a public release or Windows execution. |
| [YUGA native foundation, 43795505777](https://github.com/occult-kranti/ANDOLAN/actions/runs/43795505777) | **Failure** | Tactical startup/rules/bot/map/UI/world/full-match step passed. Step 19, “Reuse continuation HUD lane motion and native 3D authority contracts”, exited 1. Later acceptance steps were skipped. |

GitHub plugin run/job reads established the status and failing step. Job logs
redirected individual test output, so the exact cause required the retained
[acceptance artifact](https://github.com/occult-kranti/ANDOLAN/actions/runs/43795505777/artifacts/14194199020).
The plugin does not return binary archives; an authenticated, read-only
`gh api repos/occult-kranti/ANDOLAN/actions/artifacts/14194199020/zip` fallback
read the ZIP into memory with Python `zipfile`. No extraction, imports,
reruns, Git mutations or runtime edits were performed by this audit.

The artifact has 30 members, 107,092 bytes, SHA-256
`29d216cbe5a9a1e66671c87989770a4f2a2c08bda015ad35cc70ce7e98c6590f`.
Its `_temp/reuse-next-ten/W4-integrated.json` has SHA-256
`2b13f4da1c13c39103ed07302a1c04bfef03c731276eb1e1c68cb4d9d106c0b8`.
Exactly one of its 23 checks failed:

```json
{"name":"default caller retains gate10/garden4/relay9 private footprints without mutating manifest","passed":false,"detail":{"army_boxes":43,"opening_clear":true,"pier_clear":false,"source_native_boxes":8}}
```

The checkpoint's `tools/map-reuse-placement/test_integrated.gd:74` expects
8 authority + 8 native decks + 10 gate + 4 garden + 9 relay boxes = 39.
`scripts/confluence_world.gd:531–536` also deliberately appends the four
reviewed Sangam ground covers through
`scripts/sangam_district.gd:171–185`, yielding the observed 43. The source
manifest still contains eight native boxes; opening/pier LOS, all full-map
capsule routes and the other 22 assertions passed. The evidence supports a
stale aggregate-count oracle, not removal of the four cover colliders.

The original report is preserved byte-for-byte as
[ci-e59a07a4-W4-integrated.json](ci-e59a07a4-W4-integrated.json). Root authorized
the focused correction below. A successor CI run is still required before
claiming foundation success; the local correction does not replace this failed
published result.

## Focused correction and local verification

The corrected test requires exactly 43 combined boxes and the unchanged
original manifest. It reads the approved Sangam specification, verifies all
four complete footprint rows against actual district metadata and its report,
then requires each corresponding position/size exactly once in the real
army's geometry. This preserves identity even though the army deliberately
does not retain authoring IDs. Same-count wrong-identity and moved-cover
counterexamples both reject, alongside the existing broad-blocker and route
checks. No runtime, asset, collision or source specification changed.

Final test SHA-256:
`b7eb61516320bc617de701427e9bf732c685582b2f40e7b45dbc489724e101f3`.
[Local successor report](integrated-r2/integrated.json): **26/26 passed**,
exit 0, 4.475 seconds, zero `SCRIPT ERROR`, `ERROR` or `WARNING` diagnostics.
Its SHA-256 is
`49bcf864408cf6fee96625a255eaa0bfb2eaf4d6e80f3dd07e0518364b93e6b2`.
The [run receipt](integrated-r2/run.json) records the exact command,
isolated XDG directories, six unchanged before/after source hashes and the
`e59a07a4` baseline. The command was:

```sh
/usr/local/bin/godot --headless --audio-driver Dummy \
  --path /workspaces/ANDOLAN/games/yuga-native \
  --script res://tools/map-reuse-placement/test_integrated.gd -- \
  --output=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/studio3/repo/integrated-r2/integrated.json
```

The harness imposed a 45-second timeout, `OMP_NUM_THREADS=1` and
`GODOT_SILENCE_ROOT_WARNING=1`; it did not import or render. `git diff --check`
for the changed test passed. The initial local
[integrated-r1 log](integrated-r1/integrated.log) remains: it exited 1 on a
duplicate local variable name before running tests. Renaming that test-only
variable produced the fresh r2 result. Neither failed run was overwritten.

## Controls and CI expectations for studio3

At the reviewed checkpoint, `.github/workflows/yuga-native.yml` runs tactical
`round_rules`, `bot`, `map`, `ui`, `world` and `full_match` after import, with
separate user directories, Dummy audio and error/warning rejection. The newer
`hero_finish_cases.gd` and `showcase_cases.gd` are not in that loop. Their local
receipts therefore remain distinct from automated CI coverage.

The existing UI tests require exactly five saved controls in both frontend
and pause settings, plus specific `F hold` / `Hold Tab` guidance. The five
settings are sensitivity, volume, FOV, reduced motion and UI scale.
`tactical_theme.save_settings` writes a fresh config containing those player
keys. If new controls use that same file, preserving unrelated sections must
be intentional. `tactical_world._register_input` only adds missing `tac_*`
actions; it does not replace events on an already registered action. Its
pause/reset path releases all `tac_*` latches, an important behavior to retain.

If studio3 introduces rebinding, test persistence, conflicts, cancel/reset and
pause/focus release using actual tactical actions and refresh displayed key
labels. Q/E/C/X, F and Tab text is currently authored directly. The separate
legacy `input_binding_cases.gd` suite exercises classic/Confluence bindings;
its success would not establish tactical remapping. New hero inspection
controls need their own local interaction/visual evidence and deliberate CI
wiring, without attributing them to this older checkpoint.

No new native visuals or manual input sequences were reviewed for this task;
local execution was limited to the focused headless Confluence integration
suite above. Accepted finish2 art remains in its original
[map review](../../finish2/map/visual-review-final-r1.json) and delivery receipts.
Next owner: root, for the successor checkpoint/CI run and studio3 control
integration. No full foundation success, new visual acceptance or hardware
performance claim follows from this focused correction.
