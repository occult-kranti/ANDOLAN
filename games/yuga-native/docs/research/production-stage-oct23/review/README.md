# Independent production-stage review

Reviewed 23 October 2026 against baseline `7c7259260782c181b29276c4429353f9445f2a22`. This is a finite review of the new observatory, static publisher and reuse/art evidence. It does not accept finished Deadlock-level graphics, native online play, a new playable hero or additional game-campaign packets.

## What was independently exercised

- [Runtime route/CLI checks](runtime-corrected.json): 18 checks passed against a real loopback server and explicitly synthetic jobs. An owned process was reported running, then stale after exit; heartbeat expiry, eight concurrent CLI writes, dated snapshot export, Host checks, traversal/symlink rejection, inert unsafe links and absence of write routes were exercised. All reviewer-owned servers/children stopped. The [original font-route failure](runtime-original.json) is retained.
- [Actual backend/frontend integration](browser-integration.json): 10 Chromium checks passed for live data, filtered selection/empty inspector, pause/manual refresh/resume, font loading, truthful GPU absence and no page exceptions. This used private reviewer state, not production-job claims.
- [UI visual inspection](ui-visual-review.json): six originals were viewed as one desktop/narrow/zoom-width/snapshot/error batch, followed by two confirmation images after the shared fix batch. Controls, wrapping and evidence labels were coherent. The UI worker's final 29 fixture checks remain its own result. A 720 CSS-pixel viewport is a 200% layout-width approximation, not actual browser zoom or screen-reader execution.
- [Material intake](material-source-check.json) and [reuse sources](reuse-sources.json): all three 1K maps were independently decoded and matched their SHA-256, publisher MD5, sizes and dimensions; eight retained primary-source bodies matched their ledger hashes. The official CC0 material grant is separate from add-on GPL and commercial-game assets.
- [Generated model container](generated-hero-container.json): independent GLB parsing matched the recorded hash/size, 96,660 triangles, one mesh/material, two embedded WebP images, zero skins and zero animations. The GPU verifier checked 32 bindings without another network/GPU call.
- [Seven actual Blender views](art-visual-review.json): four current-avatar views, one water-court composition and two generated-source views were independently inspected and hash-bound. Presentation is useful; defects and promotion gates remain explicit.
- [Publisher negative checks](publisher-corrected.json): an unreadable directory now blocks the census, and private heartbeat tracking cannot enter a public snapshot. These were local synthetic checks, with directory permissions restored. The publisher worker's 16 unit tests additionally cover additive baseline preservation, snapshot-only mode and actual compiled-viewer license files.

## Named corrections

The shared correction batches fixed the missing TTF response type, unknown Git cleanliness, filter-hidden inspector selection, malformed/null observation rows, unsupported decorative glyphs, incomplete publisher traversal, private tracking metadata and omission of the actual PlayCanvas notice/license files. The viewer's separate strict TypeScript check initially found nullable mesh/material handling and a non-tuple spread; [the original result](viewer-typecheck-original.json) is retained. Its final result is recorded in `final-review.json`.

## Art and GPU decision

The exact existing animated avatar remains distinct from the generated source. Existing foot/hand/face contact and hair/garment limits survive the presentation render; no continuous-motion, groom or game-collision gate closes. The generated Rama has a clearer layered costume silhouette, but rear hair is visibly pitted/melted and cape/ornament textures smear. It remains outside runtime pending artist cleanup, topology/UV work, scale, rigging, deformation, animation, LOD/collision and gameplay-distance checks.

The official 512 GPU generation and export succeeded. The later [1024 comparator](../gpu/ramasource-hires-comparator/README.md) made one generation submission and was quota-denied: no export, no candidate, no improved-resolution result. The provider's HTTP success/queue events do not override its explicit failed result. No access or quota bypass is credited.

The composed prototype contains one contextual lighting state. The separate proposed day/night look-development acceptance remains open. Desktop stays **17/78 accepted packets, 0/13 complete rounds**; Android stays **0/108**, deferred.

## Hosting boundary

The local observer can report actual running-worker telemetry. The public page is a dated saved snapshot, with recorded-running labels; polling it does not expose cloud hardware. The additive publisher preserves sibling bytes within its supplied freshly assembled pinned browser baseline. It does not establish equality with every historical deployed public byte. Publication, public fetch/byte verification and ongoing hosting are separate root-owned actions.

The interactive viewer displays the actual source GLB and embedded materials using the existing pinned PlayCanvas engine. Three actual-model screenshots were independently inspected; source-only/no-rig/no-animation labels are visible. Software Chromium rendering establishes display and controls, not physical-GPU FPS or commercial art acceptance.
