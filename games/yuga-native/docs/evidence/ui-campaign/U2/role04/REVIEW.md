# U2-04 — HUD integration with actual practice state

Product: native YUGA. Source base: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. This role changed only `scripts/rama_hero_hud.gd`, added `tests/ui_hud_context_cases.gd`, and wrote this role's evidence. Completed before beginning the separate U2-05 controls assignment.

Read SCREEN_CAMPAIGN.json and the U1-04/U1-05 reviews. Actually viewed the historical `docs/evidence/rama-hero/window/1280x720-r1/09-confluence-hud-live.png`: five live readout cards and the health/status strip occupy the established bottom-center footprint. It is baseline evidence, not a new rendering of this change.

The source previously formatted READY solely from cooldown, even while the actual runtime was suspended, defeated or the army had finished. The HUD now uses configured runtime/player/kit/vitals/army state. A single notice identifies pause, return timer or the actual winner; unavailable actions show a dash instead of READY. A change of availability bypasses the existing 80 ms formatting throttle, while regular cooldown formatting keeps it. Unconfigured or detached HUDs show no invented full-health readout. Parent-owned HUD visibility, pause state, input focus and simulation clocks remain unchanged.

The live health/notice contract is preserved after reset: the healthy inactive player still displays the runtime's own notice while its action readiness remains unavailable. An initial regression run overrode this notice with generic inactive copy; the `*-rejected-r1` reports/logs preserve that failure. The correction retains the real notice instead of changing those existing tests.

Ability names now reuse `InputBindings.TITLES` for the four remappable abilities; the primary remains Kodanda. Ammunition capacity comes from the actual player constant. Shared spacing, corner and text-color tokens replace repeated local values; the existing dense 12px HUD typography and 600×103 footprint remain explicit.

## Executed checks

Exact commands, separate XDG directories, exit statuses and logs are recorded in `execution.json`. All commands used Godot 4.6.3 headless on CPU 0 with one worker thread, loading existing imported assets without running an import or renderer.

| Suite | Passed | Evidence |
|---|---:|---|
| ui_hud_context_cases | 14 | Configured/unconfigured/detached runtime, actual pause/overview/defeat, immediate resume, preserved clocks/focus, real outcome tick, saved labels, 960×540/1280×720/1920×1080 containment |
| rama_hud_expiry_cases | 9 | Real Guardian expiry, first-frame shield retirement, damage, defeat and reset |
| rama_hud_layout_cases | 9 | Existing world HUD peer separation, neutral torso clearance and complete ability text |
| ui_hud_information_cases | 8 | Opaque backing, long/empty notices, real health changes and no authority advancement |

**40/40 checks pass**, all processes exit 0, and final logs contain no engine errors or warnings. The outcome check stages a terminal core-health boundary, then lets the normal army simulation tick compute the winner; it does not invent online participants or a separate winner model. The first exploratory context run exposed the repository's audio shutdown timing warning; the final fixture uses the same one-buffer retirement wait as existing HUD suites.

Source pins are in `source-hashes.json` and each executed report:

- HUD: `3f34c07e2098e637653463b36a84996bd7ea34e2ac1490ebb220f364bb9ccc7c`
- New context test: `c0042ae59c865dde0b8a2b1e2a4d1284a3198149ed4d7243e7d9e8d997987e61`

No new actual-window, OS-input, 2× scale, 3D-render, physical GPU or Windows claim is made. Role06 owns current integrated pixel/input review. Root owns the world atlas, objective/pause copy and later result hierarchy; no changes to confluence_world.gd, courtyard.gd, loader, launch shell or theme were made by this assignment.
