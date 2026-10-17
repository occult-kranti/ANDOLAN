# Open art implementation: next fifteen assignments

The target remains the same Rama hero/arena slice. Fifteen bounded specialist
assignments rotate through at most six workers plus the moderator. This is
three implementation/review groups, not fifteen concurrent workers or fifteen
finished characters. Group 2 responds to group 1's actual findings; group 3
tests and integrates the changed artifacts. The moderator owns shared docs,
notices, CI and final publication decisions.

| # | Owner role | Concrete output and acceptance |
| --- | --- | --- |
| 01 | Mesh authoring engineer | Conservative offline GLB repair; only persistently degenerate geometry can be removed. Preserve skin, morphs, materials, clips and useful topology. |
| 02 | Open art/material artist | Acquire a small pinned resource with file-level permission; create reproducible derived maps and a native candidate material. |
| 03 | UV/frame diagnostician | Material/mesh-level UV and corner evidence with exact causes and source hashes; no arbitrary UV overwrite. |
| 04 | Toolchain engineer | Locked external REA install and actual fresh-install validation; no runtime dependency. |
| 05 | Independent contract reviewer | Counterexamples for authoring safety, resource provenance and tooling boundaries. |
| 06 | Seam authoring engineer | Implement a bounded response to confirmed corner conflicts, preserving every vertex channel and morph; refuse unsupported cases. |
| 07 | Native lookdev engineer | Actual candidate integration in a review fixture; current shipped assets remain separately identifiable. |
| 08 | Material/render engineer | Matched native frames with fixed lighting, camera and pose, and raw images preserved. |
| 09 | Deformation reviewer | Check candidate skin/morph/animation equivalence, including animated-degeneracy counterexamples. |
| 10 | Build integrator | Add focused authoring checks and fresh tool instructions to reproducible setup/CI. |
| 11 | Adversarial authoring QA | Independent malformed/shared-storage/seam/normal-space cases against frozen implementation. |
| 12 | Image reviewer | Review actual candidate pixels and record specific accept/reject/limited findings. |
| 13 | Provenance/package reviewer | Verify exact asset/tool notices, source pins, archive completeness and runtime boundary. |
| 14 | Corrective implementer | Fix the highest supported defect from changed-artifact review and repeat its focused checks. |
| 15 | Release/handoff reviewer | Verify final source checks and CI; update the actionable next queue and source-bound handoff. |

Status and exact executed receipts are recorded in
[`evidence/open-art-wave/`](evidence/open-art-wave/). Assignment numbers do not
represent passing quality gates. Keep unresolved findings visible. An unsafe
candidate is rejected even if its generation and tests complete successfully.

The [reuse guide](REUSE_ADOPTION_GUIDE.md) explains adopted tools and studies.
Production sculpt, hair, drape, expression, continuous contact/motion, listening,
hardware and native multiplayer gates remain open. Passing this finite wave
does not imply commercial-game visual parity or completion of the full game.
