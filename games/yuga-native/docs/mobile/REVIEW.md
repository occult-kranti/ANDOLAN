# Mobile planning review and handoff

18 October 2026. **The researched roadmap is complete; mobile implementation and device qualification are not complete.** Start with [the roadmap](../MOBILE_PRODUCTION_ROADMAP.md), [architecture decisions](CODE_AND_STACK_DECISIONS.md) and [machine queue](../MOBILE_PRODUCTION_BACKLOG.json). M1 is the next implementation round.

## Six completed research assignments

| Assignment | Worker | Delivered report |
| --- | --- | --- |
| Touch, camera and screens | `mobile_touch` | [Touch UX](TOUCH_UX_AND_SCREENS.md) |
| Rendering and original map pipeline | `mobile_render` | [Rendering/map](RENDERING_AND_MAP_PIPELINE.md) |
| Hero, rig, animation and asset production | `r4_05_motion` | [Hero pipeline](HERO_ANIMATION_AND_ASSET_PIPELINE.md) |
| Rules, authority and services | `ui_03_loading` | [Network/gameplay](GAMEPLAY_NETWORK_AND_SERVICES.md) |
| Reusable code/tools and reverse engineering | `r3_08_groom` | [Reuse research](OPEN_SOURCE_AND_REVERSE_ENGINEERING.md) |
| Independent device/release/security gates | `ui_06_acceptance` | [Validation/release](DEVICE_VALIDATION_AND_RELEASE.md) |

Two initial research assignments could not start because their selected model was at capacity. Replacement workers completed those reports; failed starts are not counted as completed research or implementation. The six specialist deliverables are separate from 108 **planned**, zero completed mobile implementation packets. Native G1–G6 remains a distinct campaign.

## Decisions and review corrections

Retain the Godot/Blender/glTF pipeline and author mobile variants. Qualify Mobile and Compatibility rendering on real devices. Use a stripped headless Godot authority as the first service experiment, alongside Nakama/PostgreSQL; compare before committing to transport/server architecture. Original 5v5 rules have their own profile and do not replace browser 3v3 or desktop rules. The current one-hero desktop slice and software renderer provide useful source fixtures, not mobile performance evidence.

Independent review caught and resolved these integration issues:

- Network subpackets originally reused M1–M6 and different worker numbers. They now use N1–N6 and map to the single M1–M18 master schedule and stable W1–W6 ownership.
- All implemented playable heroes are explicitly unlocked in both competitive and practice modes.
- Shop/inventory and the proposed active item are assigned to W2, with server transaction and pointer ownership requirements. The architecture document records this addition to the touch screen inventory.
- M6 requires ten independently connected **rendered** clients, including at least two physical mobile clients; headless load is additional.
- The rendering plan's initial 20-minute diagnostic is distinguished from the final proposed device gate: three runs per device/profile, ten-minute warmup, then at least 30 minutes or two full matches, whichever is longer.

Historical report hashes before integration corrections are retained here: network `4d2e0e7e9e2b24b123e3ce4c5dfac957e538774b0a37209cda056a3be42baa4f`; rendering `cdad7a048c7d96940f77fcb2940538203c42a7df433d3ccdd450332004584266`. Their current hashes are in the review receipt. Source retrieval ledgers were preserved.

## Verification actually performed

[review.json](review.json) records document/queue checks, local source hashes and a bounded independent upstream re-fetch. Initial integrated validation passed 159 checks, verified 87 local source records and independently re-fetched eight pinned primary files with matching hashes. A final rerun includes this handoff and final navigation. It checks six role slots per round, unique packet IDs, prerequisite order, all 108 packets remaining planned, relative links, JSON, whitespace and source identity. The source ledgers collectively expose 91 distinct successful raw-GitHub file receipts in the review's recognized URL/hash format; this is not a claim that all external sources were independently reread by the lead.

The inspected source is baseline `f81ee18c90547b60fdcc26fb4b1a185ac9ad2b9c` plus concurrent uncommitted native graphics candidates. Local source hashes make that distinction explicit. Read current source before implementation; the roadmap publication does not publish or approve those runtime candidates. Historical desktop release evidence remains tied to its own source.

No Android/iOS export, physical-device run, commercial mobile binary disassembly, current Mobile Legends video analysis or fresh Reddit study occurred in M0. Blocked publisher/store/policy/website requests remain recorded rather than treated as read. No downloaded open-source candidate was promoted into runtime by these documentation assignments.

## Next owner's brief

Begin M1 with the six packets in the machine queue. Freeze the intent/action/map/profile interfaces, select named devices, prepare one original art fixture, then run matched renderer and authority experiments. Keep physical-device tests open until executed. Android toolchain setup is not established by finding a desktop Godot binary; iOS needs its macOS/Xcode/signing lane. Avoid new large downloads or a second engine until an active packet and a measured need justify them.

Maintain the existing desktop keyboard/gameplay tests while extracting shared interfaces. Preserve source/license notices, independent failures and original device footage. Review art and feel with people; a numerical pass count cannot establish the requested commercial visual target.
