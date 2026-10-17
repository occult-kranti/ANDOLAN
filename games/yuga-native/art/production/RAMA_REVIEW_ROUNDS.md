# Four bounded Rama art review rounds

The goal was one improved original native hero, preserving the existing rig and
animations. The concept images remain a quality target. None of these rounds
establishes commercial-game parity or a finished likeness.

| Round | Concrete subgoal | Evidence and finding | Result |
| --- | --- | --- | --- |
| 1 | Replace uniform brocade and short costume silhouette with authored cobalt/ivory layers, hair, eyes, quiver and embedded PBR maps. | Actual native v1 studio views exposed a grip decoration on the string plane, small rear outlines reading as holes and overly glossy skin. Structural validation had passed, demonstrating why rendered review is a separate gate. | Original model revision produced; visual correctness findings carried forward. |
| 2 | Correct the grip position and failed decoration; reduce skin gloss. | Actual native v2 frames show the corrected decoration, but jump/run review exposed inflated ivory hand shells. The trouser selector was including lowered rest-pose hands. | First corrections implemented; hand selector defect carried forward. |
| 3 | Restore genuine skin fingers and restrict trousers to the leg region. | The model preserves all 3,274 source hand/wrist vertices and rejects hand/arm groups in trousers. Actual v3 frames confirm restored hands, but reveal rectangular calf openings. Source inspection identifies ten legitimate calf polygons just outside the 0.24 m guard. | Hand subgoal passed; calf coverage defect carried forward. |
| 4 | Close the ten calf openings while preserving the restored hands and exact animation curves. | The fixed-body guard is 0.25 m. All 334 faces dominated by lower-leg joints in the trouser height band are included; zero are omitted. All 3,274 hand/wrist vertices remain, with no hand/arm garment groups. The author inspected actual v4 three-quarter idle, run and defeat captures: the rectangular skin openings are absent and fingers remain intact. Capture metadata confirms the same v4 hash before and after all 13 shots. | This bounded calf-coverage subgoal passed structural and sampled visual acceptance. Broader art quality remains unfinished. |

Artifact identity by round:

- v1: `65140691ffed9546ab3ed4919ec7ebe38e118fca1543e1b173273de65d99c312`
- v2: `86e4acc36c7da2d4abef8823e9bd1b4549ede34091d5518c89f9edbf6a7ea808`
- v3: `459fab62bcf29066490c0156cdf1a3ba7378ff3dba2fa6e4882b9eff96a801a0`
- v4: `6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`

The frozen fourth artifact has 59,759 exported vertices, 100,938 triangles,
164 bones, nine unchanged animation curves, and 15 embedded original material
images. The source/generator/texture hashes and 45 bounded pose samples are
recorded in `rama-production.provenance.json`; the independent binary result is
`rama-production.validation.json`.

The isolated studio frames are actual native-engine rendering of sampled
poses, not gameplay or a smooth-motion recording. Remaining work includes
professional anatomy and facial refinement, cloth silhouette and deformation,
hair construction, animation transitions and motion quality, LODs, performance
profiling, and comparison against the approved concept. They remain explicit
quality gaps; they are not silently accepted by the structural checks.

Fourth-round visual evidence: `build/hero-review-production-v4/` under the
native game, specifically `04-three-quarter-idle.png`, `13-pose-run.png` and
`09-pose-defeat.png`, with `hero-render-review.json`. That review is scoped to
the reported coverage defect. It does not replace a full animation-continuity
or exhaustive intersection test.
