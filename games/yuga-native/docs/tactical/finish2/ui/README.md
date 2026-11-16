# HERO-VIEW2 — actual Rama inspection

Native tactical Casual, baseline `143289f410ef17ced20d0546efc7fccafee75ba9`. The hero page now shows the existing skinned Rama model with the original SURYA asset beside the unchanged Q/E/C/X descriptions. The generated menu background is hidden on this page. Front/Back buttons, pointer drag, arrow keys while the view is focused, and bounded wheel zoom inspect the full character. The primary Casual action remains outside the scroll area.

The isolated viewport reuses `rama-hero.glb`, its validated 164-bone rest contract, the authored idle/finger pose and existing arm-chain solver. Production calibration, secondary material and surface finish bind in their existing order. The modifier and AnimationPlayer are stopped; only a static presentation pose is authored. `RamaBow` and the nocked arrow are hidden; the SURYA GLB attaches to `wrist.R` through a BoneAttachment3D. This is an inspection integration of the accepted model, not a newly sculpted body, new rig, new simulation or completed third-person firearm animation set. No shared asset is overwritten.

Missing character assets produce a truthful text fallback while abilities and Casual remain available. Leaving or re-entering the hero page disposes the previous viewport, character and isolated materials. Gameplay mouse capture and authority are absent.

## Verification

- `godot --headless --path games/yuga-native --script res://tests/tactical/showcase_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/finish2/ui/checks-r6/result.json`: **20/20**, exit 0, zero engine warnings/errors. Actual imported rig/material binding, bow visibility, socket, finite poses, wrist reach, rotation/zoom guards, repeated entry/exit, missing-resource fallback and 1280×720 / 960×540 containment.
- `godot --headless --path games/yuga-native --script res://tests/tactical/ui_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/finish2/ui/flow-r1/result.json`: **36/36**, exit 0, zero engine warnings/errors. Existing native frontend loading/cancel/error/settings and authoritative UI flow checks.
- Failed first parser fixture and unreachable initial left-hand target remain in `checks-r1` and `checks-r2`. The successful correction changes presentation targets, never skeleton rest lengths.

## Capture interface and remaining acceptance

After `frontend.show_page("hero")` and resource binding, `frontend.hero_showcase` exposes `set_view("front")`, `set_view("back")`, `rotate_by(radians)`, `zoom_by(amount)` and `inspection_report()`. There is no automatic spin, including when reduced motion is selected.

Root owns the serialized native capture. Front/back, hand/finger contact, original skin/materials, and compact/enlarged composition require actual pixel review. Headless wrist reach is not finger-contact evidence. Ordinary pointer/button interaction remains separately reviewable. Full firearm locomotion, reload and combat animations for this full-body model remain future work. Source pins and the exact boundaries are in [source-freeze.json](source-freeze.json).

## Actual capture correction and final freeze

The UI owner opened all three root originals in `showcase-probe-r1`: front, back and 960×540. The full body and static rifle are readable, the compact ability column scrolls, and the primary action stays visible. No gross detached hand/rifle gap appears at this scale; close finger deformation remains a stricter art limit. The visible old quiver was the concrete correction.

The quiver is merged into RamaHero rather than being a separate node. The inspection therefore makes a local ArrayMesh copy and omits exactly 40 complete disconnected source components / 8,100 triangles: quiver body, chased rims, seven shafts and fourteen fletchings. The mask requires source-defined rest-space bounds, the exact material and rigid spine01 weights; a component must match completely. All retained encoded vertex/normal/UV/skin buffers and material references are preserved exactly. An initial re-encoding path failed the equality gate and is retained as `checks-r4`; the final encoded-buffer route passes20/20 in `checks-r6`. Changed surfaces use their finest topology without stale gear-bearing LOD indices. The canonical GLB, skeleton and shared materials remain unchanged.

The buffer-copy adapter uses Godot4.6's internal serialized `_surfaces` property, confirmed against [the engine's ArrayMesh source](https://github.com/godotengine/godot/blob/4.6/scene/resources/mesh.cpp#L1466). Future engine upgrades must rerun the retained-array gate. The view fails closed if source inventory changes. Camera distance moves4.4→4.2m and target height1.06→1.0m to enlarge the full body modestly while retaining foot margin. Final front/back rendering belongs to root.

Root requested one lighting correction from the actual R1 originals: the first directional light now casts shadows (bias0.035, normal bias0.5,10m range); ambient is0.4, cool fill0.8 and rim1.1. This lighting-only successor passed the script compiler check. The20 behavior checks retain their prior exact source pin; final front/back native captures qualify the new lighting separately. Current showcase SHA is `ebdb2a7c7f4e7c81f1a3c5c133c126e969ad5d2c2c958bfdfd701d03d1e5b6ce`.

## Scoped visual acceptance — final originals

All three `showcase-probe-r2` originals were opened and reviewed: front, back and960×540. The capture is complete with unchanged sources and pins the final `ebdb2a7c…` showcase. Quiver and arrows are absent; cape, hair, skin and costume remain intact. Head and feet stay inside frame, the key light gives face/cloth form, and the visible platform shadow improves foot contact. No gross wrist/rifle separation appears at this full-body scale. At1280 all four abilities remain readable; at960 the ability list scrolls while the main action and inspection controls remain visible. No material blocker was found, and runtime remained frozen.

This accepts the scoped native inspection/art correction, not a new rig, full tactical animation set, close finger-contact audit or hardware performance. Ordinary pointer/keyboard inspection input and rendered150%scale were not exercised by these staged stills. Exact image hashes and findings: [visual-acceptance-r2.json](visual-acceptance-r2.json). Root owns final package delivery.

## Final combined UI and local preview

The UI owner personally opened all22 originals in `finish2/final-visual-r1`; [final-ui-review.json](final-ui-review.json) records each hash. The final native menu/front-back inspection, HUD, shop, guide, settings, pause, scorecard and result compositions retain their scoped acceptance. Map detail views were also opened for truthful gallery descriptions; map art acceptance remains with its owner.

[PREVIEW.html](../../PREVIEW.html) now features the actual3D hero and final arena,25 original images (22 current captures plus3 preserved isolated SURYA prop views), the final native film and a separately labelled Raea CPU asset turntable. The delivery link points to `finish2/DELIVERY.md`. One focused local Chromium load passed8/8 checks: all25 original images decode, both separate videos load metadata and appear, all local links exist, no script exceptions or desktop overflow, and HTML bytes remain unchanged during review. Native video12s1280×720; CPU turntable6s960×540. Final browser desktop capture was opened. No broad UI suite was repeated.

Final HTML SHA256: `8a7f80cb1fb9f24bd9c083f387f8a88fee1b2caa23477117159ab7a6ad7534cd`. Receipt: [preview-final-r1/receipt.json](preview-final-r1/receipt.json). Native and CPU media have distinct scopes; neither demonstrates hardware game FPS.
