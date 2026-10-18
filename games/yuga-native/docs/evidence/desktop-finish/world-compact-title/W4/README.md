# Live compact-title visibility repair

At source `8d597dea33a60dbbbfecbbb98cc31d78345667053d79f69d55c8d4316973d0e9`, viewport layout hid LanePopulation below 1100 logical pixels, while each .12-second HUD refresh enabled it again during active lane practice. The native TitleCard container then grew, emitted resized, and triggered the layout rule again.

The world-process-active baseline at production 125% (1024×576 logical) recorded eight visibility callbacks and eight title-resize callbacks after settling, across 32 observed frames. The full timeline includes TitleCard heights 144 and 155. This proves conflicting visibility ownership and repeated layout work; no rasterized flicker claim is made. At 150/200%, the lane flag was enabled inside a hidden title parent; that is not a visible-row defect.

One helper now owns LanePopulation visibility for both layout and periodic refresh: width >=1100, active lane round, and no siege drill. It retains the existing compact strip, text, normal layout, terminal state and authority. No shader, geometry, collider, camera, imported asset or gameplay rule changed. The immutable baseline source is retained here; renderer comparison children must explicitly select the newer source.

| Executed check | Baseline | Candidate |
| --- | --- | --- |
| Same live compact-title fixture | 13/16, exit 1 | 16/16, exit 0 |
| Settled 125% visibility / title resize callbacks | 8 / 8 | 0 / 0 |
| Existing atlas/composite fixture | Earlier scope retained separately | 39/39, exit 0 |
| Existing actual-key overview navigation | Earlier scope retained separately | 29/29, exit 0 |

The live fixture runs actual world processing and native resize/container signals at 100→125→150→200→100%, with no manual layout or HUD refresh calls. It freezes simulation physics, observes unchanged army authority, sends real pause/help cancel key events, then stages a destroyed core and calls the existing army simulation step to exercise the genuine outcome/pause route before repeating scale transitions. This staged terminal route is not a played match. All candidate logs are clean of engine errors/warnings. The 39/29 suites retain their original, bounded scopes; these numbers are not added into a new graphics acceptance claim.

The exact script is unchanged between baseline and candidate. Command receipts pin invocation, source and engine. Pending: actual 125% whole-screen pixels and the separate cold-launch renderer gate. This fixture does not establish hardware performance, map-wide route correctness or complete UI pixel acceptance.
