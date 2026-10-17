# Independent reuse review

Review base: `7c86cd430e2c878b4f5e6ba1b21f562b73fdc32f`,
`game/yuga-native-production`, 17 October 2026. This is a research and
scheduling review. It does not execute another visual campaign round or promote
an asset into the playable game.

## Acceptance criteria established before the recommendations

1. **Close a recorded defect.** Round 2 concerns residual skin stippling,
   eyelid/lip/chin/cheek forms and continuous face deformation. Retain the
   accepted shadow depth/normal bias baseline of 0.2/0.35. Principal groom and
   cloth work belongs in Round 3; the 0.91267 m rapid-reversal joint-origin step
   remains a Round 4 defect; blocklike live soldiers, repeated skyline and paving
   belong in Round 6; hardware cost belongs in Round 9. A tool demonstration is
   not evidence that any of these defects improved.
2. **Fit the actual stack.** Native YUGA uses Godot 4.6.3 standard, Forward+,
   60 Hz physics, Blender 4.3.2 and glTF. Preserve the 164-bone skeleton, nine
   embedded animations, separate 23-state runtime library, unique face writer,
   morph ordering, skin/UV boundaries, action clocks and pause/reset/cancel.
   A newer demo's project version or a Blender extension's minimum version
   cannot silently replace these pins.
3. **Separate rights by payload.** Record exact repository commit, selected
   files, byte hashes and actual license text. Tool/code licenses do not license
   external models, motion, textures, music, book editions, catalog photography
   or commercial game data. Unverified candidates stay conditional; continue
   with already documented inputs without inventing an approval dependency.
4. **State the evidence actually obtained.** Distinguish a retrieved page from
   a read source, source inspection from execution, catalog metadata from media,
   historical retained Reddit excerpts from fresh comments, and isolated
   fixtures from real-game art acceptance. Record missing samples and negative
   retrievals. A narrow or unavailable subreddit sample supports no community
   consensus claim.
5. **Avoid duplicate machinery.** MikkTSpace, meshoptimizer v0.24, Khronos glTF
   Validator, Blender, Godot, REA 6.5.0 and Ghidra 12.1.4 already have bounded
   local adoption evidence. Prefer them unless the proposed tool has a named
   missing capability. REA's unchanged Mikk bridge analysis adds no new art
   evidence. A newer source HEAD is distinct from the installed npm release.
6. **Make adaptation falsifiable and affordable.** Name the smallest input,
   expected output, invariants, rejection case, owner and round. Report license,
   download/install, conversion, integration and review costs separately; a
   no-cost license is not zero production cost. Prefer an isolated authoring
   experiment before adding runtime dependencies or replacing an engine.
7. **Keep dependencies executable.** Baseline/source/context work can run in
   parallel. Form/material candidates follow that baseline, deformation follows
   exact candidate geometry, integration precedes candidate capture, and
   independent art/resource reviews follow those captures. One owner serializes
   heavy exports/imports/renders. Six workers do not mean fifteen Round 2 roles
   were executed.
8. **Preserve evidence boundaries.** Software-render capture timing is not
   physical-GPU performance; snapshots are not continuous motion; wall contacts
   are not target hits. An open engine, parser or official SDK is not a recovered
   commercial game's implementation or an art license. Runtime promotion needs
   the existing source, deformation, image and resource evidence for the exact
   candidate.

The baseline documents and their SHA-256 identities are retained in
`review.json`.

## Decisions that change the roadmap

"Accepted" below qualifies the stated research/tooling use. It does not imply
runtime adoption, finished art, complete temporal review or a completed campaign
round.

| Candidate | Decision | Concrete next use and limit |
| --- | --- | --- |
| Existing Blender 4.3.2, Rama source, original maps, MikkTSpace and glTF Validator | **Accepted: retain the current pipeline.** | Start R2 with the actual skin/channel/morph audit and an isolated face-form edit. The reconstruction lacks original modeling history. Existing Mikk degeneracy findings still prohibit an unconditional tangent replacement. |
| `tools/reuse-art` using glTF-Transform 4.3.0 and meshoptimizer 0.24.0 | **Accepted: bounded offline adapter; runtime candidate conditional.** | Six independently rerun tests pass. Current courtyard output saves 322 vertices and 19,196 bytes (about 0.113% of the file), with 135,654 oriented attribute triangles, 22 primitives and 12 embedded images retained by its comparison. This is optional R9 work. No captured appearance, collision integration or physical-GPU improvement is established. |
| `tools/reuse-animation` adapting VRF's MIT nonconstant key reduction | **Accepted: offline numerical proposal; runtime candidate conditional.** | Ten independently rerun Python tests pass. The actual library's 20,989 keys become 13,230 proposed JSON keys across 23 clips and 1,185 tracks. Python checks 160,227 finite probes; the owner-run Godot comparison checks interpolation and loop boundaries in memory. Source hashes match the current input and audit script. No `.tres` size, chained skin/contact behavior, smoother reversal or frame-time gain is established. |
| Original mythology art briefs MY-01–06 | **Accepted: reference-led original design.** | R2 uses identity constraints only. Bow/costume form is R3; controlled motion/effects are R4/R5; original five-role soldiers, architecture, wetland and lamps are R6. Source passages constrain attribution; none supplies a finished model or canonical uniform. |
| Existing Godot native IK and exact Rama chain audit | **Accepted: native baseline before an external solver.** | The existing five-case synthetic IK result and new rig audit justify a separate R4 comparator. Rama rotates two upper and two lower leg segments; a generic two-bone correction does not reproduce that behavior automatically. Keep rejected reversal prototypes rejected. |
| Rigify release-matched control and bake workflows | **Conditional: copied authoring scene only.** | GPL applies to copied plugin/UI code. An optional control rig may bake original motion back to the retained deform skeleton after mapping/rest/socket checks. Do not replace the 164-bone rig or make Rigify a Round 2 dependency. |
| Godot RetargetModifier3D / SpringBoneSimulator3D | **Conditional, deferred.** | Current clips already match the rig. The humanoid profile requires explicit name mapping; a per-frame retargeter adds ownership risk without a demonstrated benefit. No named hair/cloth/sash chain was found; springs require an accepted compatible skin/chain design and must justify their cost over the existing masked secondary motion. |
| Material Maker 1.6 weave/brick nodes | **Conditional: later PNG authoring experiment.** | Test one original cloth or paving texture for R3/R6. Its inspected `.tres` template writes Godot 3 `SpatialMaterial`, so use texture bytes with explicit Godot 4 material bindings. Verify actual packed channels and color space. No new skin texture is needed to begin R2 diagnostics. |
| ozz-animation solver | **Accepted as a small source/API study; runtime port deferred.** | The four owner-run synthetic cases show partial weight is not planted contact. They do not solve support-release scheduling. C++ extension, animation-format and platform integration costs lack a measured payoff for this defect. |
| Met Open Access repository | **Accepted metadata discovery; media conditional.** | The inspected dataset grant excludes images. Select a specific object/accession and verify the individual downloadable media's rights before asset reuse. Continue original authoring from current sources meanwhile. |

The [community report](community.md) records three fresh HTTP requests:
one public metadata refusal, successful official application authentication and
an authenticated metadata refusal. **Zero fresh posts/comments were obtained.**
The historical report records 19 posts and 21 comments; this review did not
recompute uniqueness or recover the missing raw corpus. Its attributed
paraphrases, original links and counterarguments are suitable for hypotheses,
not current community/tool consensus. No additional credential request is
justified by the observed result. Community material is a lead for bounded
experiments and tradition/source questions; neither a post nor an upvote
establishes licensing, engine compatibility or an accepted visual result.

## Rejected approaches and resolved corrections

| Finding sent to owner | Resolution / disposition |
| --- | --- |
| Material Maker's selected template is `SpatialMaterial`, resource format 2, with Godot 3 texture types. | Art owner explicitly rejects direct import and limits the recommendation to texture baking and new current-engine bindings. |
| meshoptimizer 1.0 was proposed despite the already exercised v0.24 authoring stack. | Adapter now pins 0.24.0. The newer source is a comparison, not an implicit upgrade or new runtime dependency. |
| A post-import metadata comparison cannot promise preservation of arbitrary raw GLB provenance. | Static adapter now refuses unsupported asset/accessor/buffer/image metadata and states its narrower normalized scene/node/material/mesh comparison. Six tests include metadata rejection. |
| An alternate fifteen-role animation table renamed roles 03 and 15, conflicting with the canonical Round 2 assignments. | Owner replaced it with exact R2-01…R2-15 IDs/titles and moved support-release work to its separate Round 4 lane. |
| The VRF key-reduction proposal initially described loop sampling as 48 Hz and overlooked current constant pruning. | Corrected: loops have 48 intervals per clip, nonloops use at least 16 or approximately 60 Hz intervals; the builder already prunes constant channels. The useful new experiment is bounded reduction of nonconstant keys. |
| An animation exporter initially guarded only lexical output paths. | Owner added symlink-component refusal so an outside path cannot silently redirect to the checkout; execution evidence is recorded in the engine/tooling packet. |
| The first in-memory verifier compared only clip counts, allowing duplicated clips to hide missing coverage. | Owner now requires unique exact source-name coverage; duplicate/unknown names and five altered track contracts are rejected. The final current-source comparison passes 182,246 probes across all 23 clips. |
| MY-01 could imply bow/costume changes during the face-only round; MY-02 lacked its production round; unit loops omitted hit/death and siege stages. | Both mythology artifacts now constrain R2 to reference use, schedule motion/effects to R4/R5, and include hit/death and deploy/fire/reload for R6. |
| Root integration identified optional npm dependencies inside the Godot project tree. | `tools/reuse-art/.gdignore` keeps those dependencies out of Godot's resource scan. The animation scripts remain available to their explicit tooling commands. |

Reject direct import of the current Godot 4.7 IK demo into the 4.6.3 project,
silent wholesale engine migrations, a replacement Rigify rig, bulk unverified
asset packs, and commercial-game artwork inferred from an extractor's license.
VRF is a resource parser/exporter; Source SDK 2013 is official Source 1 game/mod
code; OpenMW/OpenLara are independent compatible engines. None is evidence of
recovered Deadlock/Overwatch/Dota 2 client or server implementation. Keep the
previous source-specific GPL/custom-license decisions separate from asset terms.

Do not bundle the fetched Ganguli electronic edition as a permissively licensed
asset: its header contains mixed public-domain and noncommercial-file wording.
The inspected Griffith bow passage describes Shiva's test bow; it cannot identify
the native Kodanda weapon or justify breaking it during ordinary attacks. The
Pampā passage does not attest a poisonous Lanka swamp. These exclusions leave
original game design and the accepted reference briefs available.

## Dependency and acceptance order

Keep the face pass on the current critical path: root freezes exact inputs;
R2-02/04/07 prepare contexts, events and sources while R2-06 records the baseline;
R2-01/03/08 propose bounded map/light/form changes; R2-05 validates their actual
deformation; R2-14 integrates an isolated candidate; R2-06 captures it; R2-09–13
review their evidence; R2-15 makes source-bound art decisions. Corrections repeat
only affected checks and captures. A single owner schedules heavy exports,
imports and renders.

Parallel source/motif work and small offline audits can continue without adding
dependencies to this chain. Accepted principal forms precede secondary-motion
experiments in R3. R4 compares the unchanged/native solvers and support release
before external ports. R6 soldier/world work needs complete action loops,
formation-scale readability and existing gameplay boundaries. R9 is where actual
resource savings and physical-GPU costs can justify optimization candidates.
One completed limited Round 1 and nine planned rounds remain the campaign state;
these research outputs do not execute the fifteen Round 2 roles.

The final synthesis was checked against the prior assignment JSON: all fifteen
original contracts are unchanged apart from added research links, all remain
planned, and the campaign still contains 135 future assignments. The publication
receipt and Git comparison support runtime baseline `09dac722…` and the later
documentation/evidence checkpoint `7c86cd4…`. The added CI commands install the
static tool's isolated lock and run its six test groups plus the ten Python
cases; configured Node 22.14 satisfies the tool's Node 20.9 minimum. After the
existing native import, CI also extracts the actual library, audits it, runs the
in-memory Godot comparison and checks its JSON result/error log. A new CI run
is a separate post-commit result.

## Independent checks and limits

The reviewer read the project instructions/current campaign contracts, all five
domain reports when finalized, selected upstream license/API/algorithm files,
the current Rama contact and motion-library source, and both new adapters.
Independent runs passed the static adapter's six test groups and the animation
adapter's ten Python cases. Retained-download SHA-256 checks matched 101 ledger
entries across the four source reports; some entries refer to the same upstream
source. Hash verification does not mean every downloaded file was semantically
reviewed. The static input/candidate hashes and animation input/extraction/audit
script hashes were independently checked against the owners' receipts.

The ozz API exercise, ten-part rig audit, glTF Validator runs, Godot extraction,
Godot interpolation comparison and exporter-rejection runs were performed by
their owners; this review inspected their bounded receipts and source. No new
renderer, Blender export, human input, artwork, full motion playback, listening
or physical-GPU test was performed by this reviewer. Actual pixel acceptance
remains in the pinned visual campaign evidence and future candidate captures.
`review.json` records exact checked inputs, decisions, corrections and limits.
