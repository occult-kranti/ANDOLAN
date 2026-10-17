# Critical HUD authority timing correction

17 October 2026. The R2 continuous Guardian capture exposed a disagreement near expiry: the field boundary retired early while the HUD retained `field active` and `+55`. Combat owns the field-boundary correction. This evidence isolates the HUD's 80 ms refresh delay.

`rama_hero_hud.gd` now reads health, shield, return timer and status on each normal render update. The five cooldown slots retain their existing 80 ms formatting cadence. `_refresh()` still updates both groups for initial configuration and existing callers. No runtime authority, movement, animation or tuning changed here.

The new `rama_hud_expiry_cases.gd` instantiates the real Confluence scene, kit, army and hero vitals. It accepts Guardian around the real hero receiver and advances the army's actual 50 ms authority ticks. After sampling the final live tick, it resets the HUD clock to the worst previous throttle phase, advances to exact expiry, and calls only normal `_process(1/60)` before inspecting visible text. It also checks actual damage, defeat and reset on their next render updates.

| Source | Result | Evidence |
| --- | --- | --- |
| Old HUD | 5 pass, 4 fail, exit 1 | [before.json](before.json), [log](before.log) |
| Corrected HUD | **9/9 pass**, exit 0 | [after.json](after.json), [log](after.log) |

The four old-source failures are the expected stale visible expiry, damage, defeat and reset states. Authority preconditions passed. Both runs have no engine errors or warnings. [summary.json](summary.json) retains exact commands, source/report/log hashes and checked source stability. The runs used isolated user data, fixed 60 FPS and two-CPU affinity; no renderer was started.

These numerical checks establish that critical HUD text reflects authoritative state on the next normal render update. The strengthened integration test and short actual Guardian-expiry probe remain separate combined gates before another continuous capture.
