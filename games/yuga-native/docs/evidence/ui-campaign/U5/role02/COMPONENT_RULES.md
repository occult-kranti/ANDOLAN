# Shared native UI component rules

These rules describe the consolidated implementation reviewed in U5. They are implementation contracts for new screens, not a claim that every supported scale or platform has received visual acceptance. The role review and source receipt identify the accepted capture bytes.

## Type, surfaces and spacing

- Install `HeroUITheme.create()` on each standalone screen root. Use the bundled Noto Sans for controls and reading text, Noto Serif for display/title roles, and bundled DejaVu Sans for missing symbols. System fallback stays disabled so machine fonts cannot silently change metrics.
- Reuse the spacing steps 4, 8, 12, 20 and 32 logical pixels. Standard control insets are 20 horizontally and 12 vertically; panel padding is normally 20. Corners are 3px, not large pills.
- Use opaque deep-indigo or ink cards behind text over the 3D scene. Shared text colors are ivory, mist and muted blue-grey; gold identifies accents, selection and primary actions. A background screenshot is insufficient to establish text contrast if a surface becomes translucent.
- Shared type roles are 64 display, 32 title, 22 section, 17 body and 14 caption. Production screens have explicit overrides: the compact title uses 44, and auxiliary world HUD labels currently use 11–12 logical pixels. Those smaller labels require direct compact-screen review; the shared type scale does not certify their physical readability.

## Actions and states

| Role | Native API | Meaning and treatment |
|---|---|---|
| Primary | `button(control, true)` | One next action; gold surface with dark text and dark inset focus ring. Terminal lane practice makes Restart primary because continuing only returns to the ended world. |
| Secondary | `button(control)` | Standard action; indigo surface, ivory text and gold inset focus ring. |
| Utility | `button(control, false, true)` | Lower emphasis through a deep surface; retain native focus and disabled behavior. |
| Selected | `button_variant(control, &"selected")` | Persistent selection uses a gold left edge. Selection and keyboard focus remain separate visible states. |

Every role defines normal, hover, pressed, hover-pressed and disabled appearances. Changing a role must replace every state together. Do not approximate disabled interaction by lowering opacity: use the control's actual `disabled` property, and omit disabled/read-only entries from custom Tab loops.

Buttons have a minimum 44px logical target height. Focus uses a 2px border inset 4px, so a full-width control inside a clipping scroll viewport retains all sides of its ring. A disabled control can retain native focus; its disabled fill must still contrast with that indicator.

OptionButton reserves a 40px arrow gutter in every state, including the open popup's `hover_pressed`; mirrored styles reserve the same space on the opposite side. The native popup uses the same opaque palette. CheckButton/CheckBox use separate on/off and disabled symbols. Sliders use Godot's highlighted grabber for keyboard focus; do not assume they support a button-style focus box. Scrollbars keep native scrolling authority and their own focused/pressed states.

## Scroll, modal and lifecycle behavior

- Preserve the actual valid opener when a modal closes. Validate visibility, focusability and disabled/read-only state; choose an available fallback if the opener is gone.
- Keep settings Done in the fixed footer outside the scrolling body. Reveal focused body controls after resize without moving focus to an unrelated action.
- Preserve a fresh panel's heading when the heading and primary action fit together. For a lower action, reveal that action instead of resetting scroll to the top. Do not use one unconditional scroll rule for both cases.
- Deferred layout/focus work must check that its host is still live and attached before awaiting a frame and again afterward. No detached host may restore focus into a replacement scene.
- Guide selection and reading scroll are separate. Bow and four-ability group headings provide hierarchy; PageUp/PageDown/Home/End scroll details. The compact initial Bow reveal must not override a newer focus choice.
- Loading text distinguishes threaded resource progress from synchronous construction. Unknown progress stays indeterminate. Cancelled, detached or replaced callers cannot later complete navigation. Back/Retry labels must describe actions that remain usable in the observed state.

## Evidence required for future changes

Record source hashes and native state receipts for the changed screen. Inspect original frames at the supported compact size, including the focused and disabled states that can actually occur there. Headless geometry catches overflow and ownership failures; it does not replace rasterized readability, OS input, DPI or packaged-font checks. Retain meaningful failures even when assertion-only reports remain green.
