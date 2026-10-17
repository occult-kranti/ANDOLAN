# Reuse decisions and next production goals

17 October 2026 · native source baseline `7c86cd430e2c878b4f5e6ba1b21f562b73fdc32f`.
Six parallel specialists researched community coverage, art, animation, mythology,
engine tools and independent review. This consultation and its two offline tools
do not complete a visual campaign round. One round remains complete, nine planned.

**Reddit access:** supplied application credentials authenticated successfully,
but the subreddit request returned HTTP 403. Three HTTP requests produced zero
new posts/comments. [Community evidence](community.md) separates that result from
retained reports of 19 mythology posts and 21 comments; their raw corpus is absent.
Tool choices below come from inspected upstream sources, not a new subreddit poll.

## Selected reuse, with an actual integration boundary

| Resource | Decision | Evidence and next gate |
| --- | --- | --- |
| Existing Godot 4.6.3 / Blender 4.3.2 / editable Rama | Keep the current stack and rig. Use release-matched Rigify documentation where useful; do not replace the skeleton for this face pass. | [Animation study](animation.md), [art study](art.md). Existing 164 bones, nine embedded clips and separate 23-state runtime library remain authoritative. |
| ValveResourceFormat MIT animation exporter | **Implemented:** a small attributed quaternion alignment/key-reduction adaptation, with strict channel admission and external JSON proposals. | [Tool and commands](../../../tools/reuse-animation/README.md). Current library: 20,989 → 13,230 proposed keys, 36.97% fewer. This is numerical storage research; runtime motion, file-size savings and contact are not accepted. Optional Round 9. |
| glTF-Transform 4.3.0 + meshoptimizer 0.24 | **Implemented:** isolated static-world weld/reorder preflight with geometry, material and image preservation checks. | [Tool and commands](../../../tools/reuse-art/README.md). Courtyard saving only 19,196 bytes / 0.113%; runtime replacement rejected as insufficient benefit. Optional Round 9, no rendering-performance claim. |
| Material Maker 1.6 | Candidate offline PNG bakes for fabric/stone, with explicit Godot 4 channel bindings. | Its examined Godot export template still uses Godot 3 `SpatialMaterial`; direct resource import rejected. No bake executed. Optional Round 3/6. |
| Godot native IK / ozz-animation | Compare current motion with already-available Godot tools first. ozz scratch probe supplies a counterexample, not a new runtime dependency. | Rama has a four-segment leg chain; two-bone IK is not a drop-in. Fractional ozz correction loses contact. Separate Round 4 investigation. |
| REA / Source 2 tooling / open game sources | Use analysis tools for a specific unanswered format/code question; reuse an inspected algorithm when its terms permit. | [Engine study](engine-reuse.md). Existing REA/Ghidra was exercised on owned code. No commercial client/model recovery is claimed; source-available algorithms do not require decompilation. |
| Epic passages and architectural references | Six original art briefs: bow silhouette, deliberate motion, five troop roles, Lanka masses, reed margins and civic lighting. | [Mythology briefs MY-01–06](mythology.md). Literary sources, historical forms and game inventions are labeled separately. Museum metadata does not clear an uninspected image. |

## Next five production goals

1. **Freeze the Round 2 face baseline.** Use runtime source `09dac7220544374a471a11d953b67de20ab99d7d`
   and its final film/anchors; `7c86cd4` adds the publication documents. Roles
   R2-02/04/07 define context, actions and source constraints; R2-06 captures the
   fixed control. Diagnose remaining stippling before creating replacement maps.
2. **Author face/skin candidates.** R2-01/03/08 isolate material, light and form
   changes. Preserve rig, morph boundaries, indigo/gold identity and existing
   asset rights. MY-01 is identity guidance here; bow/costume production waits
   for Round 3. No optimizer or new engine is a prerequisite.
3. **Integrate and independently judge the face slice.** R2-05 tests actual
   deformation; R2-14 integrates in scratch; R2-06 records matched day/night,
   gameplay-scale and continuous action views. R2-09–13 review their scopes and
   R2-15 gives explicit per-element acceptance/rejection. Numerical passes alone
   cannot close this goal.
4. **Produce hair/cloth, then repair continuous motion.** Round 3 authors
   silhouette, thickness and folds on accepted forms. Round 4 compares current
   support release with native IK under start/stop/reversal/action fixtures.
   Retain rejected prototypes and contact failures. MY-02 informs motion/effect
   design without inventing source support for frame timings or powers.
5. **Build readable troops and coherent districts.** Round 6 uses MY-03–06:
   five weapon-led roles, complete hit/death and siege deploy/fire/reload cycles,
   a strong Lanka gate, quiet gold/turquoise hierarchy and clear reed margins.
   Respect Round 5 threat hierarchy; review mixed waves and traversable edges.
   Round 9 measures crowd/resource costs on stated hardware.

These are dependency-ordered goals, not five completed milestones. The exact
fifteen face assignments remain in [VISUAL_ROUND2_TASKS.json](../../VISUAL_ROUND2_TASKS.json).
Root owns shared roadmaps and integration. At most six workers run concurrently;
one owner serializes Blender exports, imports and captures. Source research,
candidate authoring and independent review can run in parallel when their inputs
are frozen. Each handoff includes source hashes, changed files, actual commands,
counterexamples, original captures when relevant and unresolved defects.

## Evidence and resumption

Read [independent review](review.md) before promoting a candidate. Each domain has
a neighboring JSON ledger of immutable upstream pins, actual reading scope,
licenses and observed results. Run the two tool test commands from their READMEs;
the native CI workflow also runs them. Neither tool replaces a runtime asset.
The animation verifier compares actual Godot resources in memory, including loop
boundaries; finite numerical probes still do not establish continuous skin/contact
equivalence. No new game render, human play test or physical-GPU measurement was
performed for this consultation. Commercial-game art quality remains open.
