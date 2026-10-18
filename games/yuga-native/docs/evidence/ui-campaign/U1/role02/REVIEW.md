# U1 role 02 — shared native UI system

Goal: give YUGA's launch and settings controls one legible indigo/gold/ivory system without changing native input ownership. Source commit before this work: `0437ea91edf6989ff78c1eeadb3661f4825b60f2` on `game/yuga-native-production`.

## Actual baseline reviewed

- `docs/evidence/rama-hero/window/1280x720-r2/01-title-loaded.png`: gold primary action and serif YUGA identity are worth preserving; secondary and utility controls lack a shared explicit role contract.
- `docs/evidence/rama-hero/window/1280x720-r2/02-settings-first-entry.png`: native gray toggle/scroll indicators and inherited setting states diverge from the gold action language. The final Back row is clipped by the scroll viewport in this historical image; theme checks do not resolve or accept that layout.

Paths above are relative to `games/yuga-native/`. No new rendered image was produced by this role.

## Delivered contract

- Preserved `create`, `panel_style`, `button`, `label`, `display_font` signatures. Added `build` alias, `text_font`, and `button_variant(control, variant)` for `primary`, `secondary`, `utility`, and `selected` roles.
- Indigo surfaces, ivory reading text and gold action/focus accents. Opaque interactive surfaces give deterministic contrast over either day or night world renders. Disabled text is explicit and readable.
- Shared 4/8/12/20/32 spacing and 14/17/22/32/64 type tokens. `YugaDisplay` and `YugaTitle` use the existing serif fallback stack; body text uses installed sans fallbacks. Label variations also include `YugaSection`, `YugaCaption`, `YugaEyebrow`.
- Complete native Button, OptionButton and CheckButton styling, including disabled, mirrored option-arrow space, toggle knob position and checked mark. Primary/utility variants may be changed in place without retaining stale colors. Button resources are private per control; themes are private per screen.
- Button/choice/ScrollContainer focus uses a 2px gold ring with dark separation. Native ScrollBar uses its actual `scroll_focus` style. Native Slider has no focus StyleBox: its `grabber_highlight` icon carries the 2px ring used for keyboard focus and hover. Slider disabled icons remain distinct and legible. ScrollBar has no disabled property/state; no unsupported state is claimed.
- Original small SVG icons are generated locally through Godot, with no assets, downloads, dependencies, input interception or gameplay changes.

## Verification

Run from `/workspace/ANDOLAN`:

```sh
godot --headless --path games/yuga-native --script res://scripts/hero_ui_theme.gd --check-only
godot --headless --path games/yuga-native --script res://tests/ui_theme_cases.gd -- --report=res://docs/evidence/ui-campaign/U1/role02/theme-checks.json
git diff --check -- games/yuga-native/scripts/hero_ui_theme.gd games/yuga-native/tests/ui_theme_cases.gd
```

Godot 4.6.3: **61/61 checks passed**, plus parse and whitespace checks. Actual native keyboard events activate the enabled primary action, reject disabled activation, adjust an enabled slider and reject editing a disabled slider. Resource checks cover visible indicator geometry, reciprocal arrow space, control/theme ownership and variant changes. Measured text contrast across checked states is at least **8.011:1**; the tested threshold is 4.5:1. The JSON records every check and the exact source hashes.

## Source identity and remaining review

- `scripts/hero_ui_theme.gd`: `cc95ffdc4d2563c5a09b39fd70aab2cd84d6c8dc0810ce5eb905c971de3672e4`
- `tests/ui_theme_cases.gd`: `41d03200b9c977e53ab93328feff47054c90f087fac7002677229fcc08ed2ef4`

Changed only those two source/test files and this role's evidence folder. No commit, imports or heavy render performed. Font fallback can vary on another OS. Headless resource/input checks do not establish rendered ring clipping, complete settings visibility, 960×540/1280×720 layout, 2× UI scaling, screen-reader access or Windows appearance. Role 01 owns launch integration; role 06 owns serialized actual-window capture and review. Those are the next owners for visible regression acceptance.
