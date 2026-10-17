# TRIAD effects: siege warning readability

17 October 2026. Owner: `/root/traversal_audio`. Product: native YUGA, offline troop siege presentation. Starting commit: `af9dae258936a2fc1854587736dd847ef1c0d604` on `game/yuga-native-production`. This packet changes presentation and focused tests; it adds no relay rules, hero damage, networking or commercial game assets.

## Round 1 — inspect the existing result

Read [practice UX](SIEGE_PRACTICE_UX.md) and the [retained render review](evidence/siege-render-r2/SIEGE-RENDER-REVIEW.md), then opened these actual captured images:

| Existing evidence | Observed issue | SHA256 |
| --- | --- | --- |
| [Frame 45](evidence/siege-render-r2/siege-frame-00045.png) | Separate gold/cyan circles resemble the map's thin decorative circles. | `b402e504d412d156aa10592a394c0163825fd789b582534258309a643e13e245` |
| [Frame 90](evidence/siege-render-r2/siege-frame-00090.png) | Several overlapping concentric rings obscure which boundary and motion belong to each attack. | `e21a8d076dd514e75d84f7539d766764bd141e2f6dce7ff2cb735f59d4e768a0` |
| [Frame 145](evidence/siege-render-r2/siege-frame-00145.png) | A broad bright aftermath ring competes with active warnings. | `3e1a49a9f0ce71664aed7867166334b1962b478a3b79ac23b529af912068ba7f` |

These are images of the prior build, not proof of the revised art. The whole movie and audible output were not reviewed for this task. Existing published findings are retained in their own source-pinned reports.

## Round 2 — implement a bounded visual grammar

Changes in [siege_effects.gd](../scripts/siege_effects.gd):

- Twelve broken, dark-edged boundary ribbons indicate the exact declared attack radius. Each sector retains a 42% angular gap. A broad notch on the firing-unit side points inward toward the committed target.
- Sun uses eight triangular ticks and warm gold. Moon uses four squared brackets and cyan. Shape remains an ownership cue without relying on color. These indicate the attack's owning team; the module does not infer a viewer's friendly/enemy team.
- During windup, inner ticks converge from scale 1.0 to 0.35 across the original authoritative delay. The boundary and target stay fixed. There is no bright filled disk, pulsating opacity or emissive bloom.
- At impact, the team's ticks turn outward, expand within the same radius and fade over the existing 0.48 seconds. Initial opacity is 0.62; windup opacity remains 0.88. Aftermath does not imply a larger damage radius.
- Ground placement, projectile arc, barrel charge, cancellation, duplicate history, expiration, reset, pause, mute, voice priority and public event/API/report fields are preserved. Cancelled attacks disappear without an impact burst or cue.
- Each warning still owns one material and four mesh nodes; impact aftermath owns one material and two mesh nodes. The existing cap is 32 live effects and six voices. Animation mutates existing transforms/material values without allocating replacement resources.

This is an original geometric design based on the captured prototype. No model, texture, sample or commercial effect was imported. The audio assets, generator and provenance are unchanged. Native siege attacks currently damage troops; these markers do not establish a hero-health mechanic.

## Round 3 — verify the changed behavior

Expanded [the canonical effects suite](../tests/siege_effects_cases.gd) from 63 to 76 checks, preserving all original checks. Added actual ImmediateMesh vertex/radius/gap/area checks, color-independent team topology, source orientation, monotonic countdown/aftermath, resource identity, coincident source/target, exact-camera projection and twenty mixed pause/mute/cancel/expiry/reset cycles.

Both commands completed successfully under Godot `4.6.3-stable (official)`:

```sh
XDG_DATA_HOME=/tmp/yuga-triad-effects-r2/user godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/siege_effects_cases.gd -- --report=/tmp/yuga-triad-effects-r2/effects-fixed60.json
XDG_DATA_HOME=/tmp/yuga-triad-effects-normal-r2/user godot --headless --path games/yuga-native --script res://tests/siege_effects_cases.gd -- --report=/tmp/yuga-triad-effects-normal-r2/effects-normal.json
```

| Result | Evidence |
| --- | --- |
| Fixed 60 FPS clock | 76/76 pass; `/tmp/yuga-triad-effects-r2/effects-fixed60.json` |
| Ordinary clock | 76/76 pass; `/tmp/yuga-triad-effects-normal-r2/effects-normal.json` |
| Both report hashes | `8b054ba58ce63e1563ef1d946d9006f555bc3fc5e5da0645328497afda17b393` |
| Frozen runtime SHA256 | `ef39110b21b9f3d1f6ee6591d4ce0a883a86f1e98587916823cf2b95997f75c0` |
| Frozen canonical test SHA256 | `dddbfac8a1070cc13627f4febb59b7c8c9503197386536a6e8639b44263af4d5` |
| Unchanged audio provenance SHA256 | `c7b420a7b990db720427831a5c7524e0a44d0b2aa50509a02cdfaf8f60497e05` |

The first expanded run is retained at `/tmp/yuga-triad-effects-r1/effects-fixed60.json`. It failed an exact upper-bound assertion because Godot stores material alpha 0.62 as `0.620000004768372`. The test now allows a one-millionth numerical tolerance and records all sampled opacity/scale values. No runtime behavior was changed to resolve that test issue.

Actual geometry checks cover radii 0.1, 2.4, 3.0 and 20.0. Boundary vertices reach but do not exceed the declared radius; the bright footprint ribbon/notch covers less than 12% of the circular area. Both inward and outward team glyphs remain within it. All mesh vertices are finite. Ten thousand windup events still cap at 32 live warnings and 167 total owned nodes; impact floods retain their 103-node bound. Pause/mute/cancel/reset and release tests use real nodes and audio player state, not mocked substitutes.

Projection uses the same `(8,12,-28)` camera, looking at `(0,1,0)`, 58-degree FOV and 1280×720 viewport as the retained siege capture. It projects actual warning vertices at four committed targets from that capture's event ledger:

| Owner / role | Target Z | Footprint width × height |
| --- | ---: | ---: |
| Sun cannon | 4.2000 | 110.9 × 37.6 px |
| Moon cannon | -4.0100 | 140.5 × 60.3 px |
| Moon chariot | -0.9700 | 102.1 × 39.8 px |
| Sun chariot | 1.1600 | 96.1 × 35.3 px |

## Remaining acceptance and handoff

Root owns the next serial render and integrated UI review. Capture source must match the frozen runtime above. Inspect multiple overlapping windups and aftermath from the exact siege camera, then from normal third-person play in daylight and night. Verify boundary contrast over the actual floor, discernible inward movement across the short 0.55/0.80-second windows, team shape distinction when desaturated, and no obstruction by the new relay card or troops. Reject unreadable marks even if these numerical checks pass.

Headless projection proves framing and size only. It does not prove pixel thickness, occlusion, blended overlap, player understanding, audible quality, physical-GPU performance or finished production art. The sparse ribbons trade some continuous boundary coverage for separation; exact coincident same-team attacks can still overlap. No new render, import, package, commit or deployment was performed by this owner. The next owner should archive accepted fresh visuals and current test reports with the milestone evidence.
