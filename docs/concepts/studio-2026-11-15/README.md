# Studio screen targets — 15 November 2026

Three original AI concept boards cover twenty representative screens across the
native YUGA game, browser YUGA/mechanics labs and ANDOLAN city game. Generated
with the built-in `image_gen` tool; the complete prompts are in [prompts.json](prompts.json).
These are art-direction targets, not screenshots or evidence of implemented features.

| Board | Intended use |
| --- | --- |
| [Native YUGA](yuga-native-screen-targets.png) | Eight screen compositions: title/practice, ability guide, HUD, pause, settings, loading/recovery, city overview, outcome. |
| [Browser YUGA and labs](yuga-browser-lab-targets.png) | Six compositions: roster, bot practice, control lab, lane lab, forge and result. |
| [ANDOLAN](andolan-screen-targets.png) | Six compositions: title, crew lobby, city play, jobs, evidence and controls. |

## Accepted direction and rejected generated details

Use native indigo/ivory/gold hierarchy, a large original character silhouette,
one clear launch action, readable opaque HUD surfaces and concise mode context.
The actual title continues to render the existing Rama model. No concept image
is substituted for the live world or used as a completed character asset.

The image model invented some text and mechanics. **Do not use the lettering as
a control, lore, numerical-balance or implementation specification.** The native
board incorrectly shows Step on Space, Guardian on E and Volley on Q. Current
native defaults are LMB bow, Q Piercing Dawn, E Measured Step, C Guardian Circle,
X Dawn Volley; Space jumps. Saved remappings take precedence. Measured Step does
not confer invulnerability; Guardian Circle shields/heals rather than repelling
or slowing enemies; Dawn Volley fires three paced lanes rather than an arbitrary
area rain. Display actual kit/binding data in code.

The browser board invents a different fourteen-name roster, upgrade prices,
extra labs and result statistics; the current roster and economy remain in
`games/yuga/shared/`. The city board invents missions, prices, a server URL and
some controls. Those are visual exploration, not additions to City Reform or a
provisioned backend. The loading illustration's percentage does not authorize
fake total progress. Existing native loading reports real phases.

Actual source-bound screenshots, tests and executable packages are linked from
[the studio delivery](../../research/STUDIO_DELIVERY.md). Concept quality does
not qualify animation, map collision, multiplayer or hardware performance.
