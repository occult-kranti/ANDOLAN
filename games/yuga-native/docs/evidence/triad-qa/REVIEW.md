# Independent Triad relay integration QA

The final actual-world headless run passes **37 of 37 checks** on Godot 4.6.3. The final log has no engine warnings or errors. This verifies the offline relay integration and its bounded fixtures; actual rendering, listening, OS input, online authority and hardware performance require separate evidence.

## What was exercised

- Actual world entry with the thirty-unit army and all three relay sites; solo capture at eight seconds; all three sites captured independently with supplies delivered only at the occupied site.
- Real troop IDs counted once despite duplicated list references, a two-contributor cap, dead and nonfinite-health exclusions, oversized actor input rejection, contest freeze, idle partial decay, and enemy neutralization before takeover.
- The height contract rejects feet above 2.5 m. The exact 2.5 m boundary counts; low hovering is deliberately permitted by this milestone's rule, rather than excluded by traversal mode.
- Actual troop health and hero ammunition after the five-second supply interval: healing caps at maximum health, ammunition caps at twelve, and issued receipts apply once. Old epochs and unissued IDs are rejected. Delayed receipts recheck current life, range and height. A real 4 cm thick wall blocks supply; removing it restores the next eligible delivery.
- Capture, supply clocks and rewards freeze during pause, focus loss, overview, siege drill and core outcomes. Resume applies only one due supply. A simultaneous core draw receives draw wording. Successful normal/drill resets clear relay progress; rejected drill entry preserves existing state.
- Thirty normal resets leave relay node counts, three plinth bodies and the army collision-box inventory unchanged.
- Actual physics rays hit the three authored 0.56 m plinth tops at x = −34, −6, 34 and z = 4. The real player's collision test and camera-mask sphere sweep detect those solids. All nine plinth step boxes also appear in army geometry.
- Real capsule sweeps cover all three lane polylines and both rotation routes, including the circuit's closing segment. Radius 0.65 m and perpendicular center offsets ±1.35 m cover the authored four-metre clear floor corridor. This is a sampled geometric gate, not an exhaustive movement proof.
- Relay HUD rectangles fit 960 × 600 and 1280 × 720 logical viewports. All eleven pause actions receive focus and scroll fully into view at both sizes.

The tests instantiate the actual Confluence scene and run relay steps through its production scheduler inside a physics callback. Automatic army/player stepping is disabled for deterministic fixtures; real troop nodes are deliberately isolated or repositioned. Receipt issuance/application is temporarily separated to exercise actor changes between those APIs. This does not model an authenticated network protocol.

## Findings and retained attempts

1. **Confirmed mixed-ID runtime bug:** the first supply containing integer troop IDs and the String hero ID failed in `relay_session.gd` when it compared incompatible types with `==`. The implementation owner added an explicit String guard. `integration-attempt1.log` preserves the stack trace; `integration-attempt1-summary.json` states that the aborted run was incomplete. The final mixed troop/hero supply checks pass.
2. **Confirmed crossing obstruction found by the parallel existing-world physics gate:** original plinths at z = 0 obstructed the canonical cross-mid route. The art owner moved them to z = 4 while leaving capture pads at z = 0. This independent final suite verifies the corrected physical routes and collisions. The original obstruction evidence belongs to the world/art owners' reports.
3. `integration-attempt2.json` passed 35 of 36 checks. Its drill check compared the entire report, including the allowed ambient station animation clock. The corrected assertion compares every gameplay field, receipt and reward counter while recording ambient time separately. Attempt 3 passed all 36 checks; the final run adds the explicit three-site capture/supply isolation case.
4. `integration-parse2.log` preserves a test-author type-inference error while adding perpendicular route sweeps. It was corrected with an explicit Vector3 type before the third run. No runtime change addressed that harness error.

## Reproduce and identify the tested source

Run from the repository root:

```sh
XDG_DATA_HOME=/tmp/yuga-triad-qa-user godot --headless --fixed-fps 60 \
  --path games/yuga-native --script res://tools/test-relay-integration.gd -- \
  --report=res://docs/evidence/triad-qa/integration-final.json
```

The report pins all relevant sources and fails if any change during execution. Key SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `confluence_world.gd` | `e0fb3f66e8a2c60d3956173f5d1cb2da661b13ad3a5040475114a959001d7514` |
| `relay_session.gd` | `3c15d66e32e59f0b593fa7e3a815a4163edaaf427e50c9e8a5186908330ff0a3` |
| `relay_control.gd` | `42d68a7d034c31033c5e105fd227e9e179d35d88209428544f396fa39f2fe000` |
| `relay_art.gd` | `32e42d32a4a1e52414c2e274d076c1aac4531fd10084b052082f0cc08cd31cb6` |
| `test-relay-integration.gd` | `c7b3361efbd15a05be32982b9c99e451a12219b269182049547d14f140a0254e` |

`evidence-manifest.json` lists the byte counts and hashes of the reports and retained logs. The independent QA owner changed only this test helper and this evidence directory; gameplay fixes belong to their implementation owners.
