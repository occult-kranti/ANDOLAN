# Pending studio checkpoint: independent verification

Task `YUGA-RESOURCE-AUDIT-2026-11-15`; product **native YUGA · Sanctum**.
Reviewed 15 November 2026 America/New_York (16 November UTC), on
`work/yuga-studio`, baseline commit
`e59a07a4786e9ad491cfef7a4e706dbd06063adc` plus the existing studio3 changes.
This owner changed only this report and `verification/`. Runtime sources,
assets, manifests, workflows, Git publication and dashboard remain root-owned.

**Result: all 706 focused checks passed.** The existing Rama studio changes
are suitable for a source checkpoint within their documented preview scope.
This is not a new packaged-release, ordinary-input, final-art, online or
physical-GPU acceptance. No runtime correction was needed in this review.

## Exact execution

[Execution receipt](verification/checks-r1/execution.json) retains every exact
argument array, elapsed wall time, source SHA-256 and result. Each run used
Godot `4.6.3.stable.official.7d41c59c4`, headless mode and Dummy audio, with
fresh XDG data/config/cache under
`/tmp/yuga-resource-verification-state-20261115-r1`. No shared import or renderer
ran in this lane. No reviewed source changed during the checks.

| Existing suite | Checks passed | What this establishes |
| --- | ---: | --- |
| `round_rules` | 53 | Local match/economy/objective rules and adverse inputs |
| `bot` | 21 | Existing bot decisions and movement contract |
| `map` | 335 | Tactical map structure and physical-route checks |
| `ui` | 37 | Screen flow and updated hero-dossier integration |
| `world` | 33 | Instantiated native scene, ray hits, barriers, inventory and lifecycle |
| `hero_finish` | 94 | Existing hero presentation/material contract |
| `showcase` | 31 | Studio modes, isolated SURYA, ADS, pause, reduced motion and invalid inputs |
| `hero_pose` | 37 | Actual skin/rig pose preservation, bounds, interruption and reset |
| `hero_dossier` | 33 | Ability facts, selectors, supported previews and isolated state |
| `full_match` | 6 | A complete local bot match in the actual instantiated world |
| Map-reuse `test_integrated.gd` | 26 | Corrected exact 43-footprint oracle, route checks and counterexamples |
| **Total** | **706** | **All exit 0; no `SCRIPT ERROR`, `ERROR` or `WARNING` lines** |

The `world` suite prints its 33-check JSON summary to
[world.log](verification/checks-r1/world.log); it does not implement the
workflow's optional `--report` argument. The receipt explicitly records that
distinction instead of inventing a missing JSON artifact.

Representative commands, from the repository root:

```sh
godot --headless --audio-driver Dummy --path games/yuga-native \
  --script res://tests/tactical/showcase_cases.gd -- \
  --report=/absolute/fresh/showcase.json
godot --headless --audio-driver Dummy --disable-render-loop --fixed-fps 60 \
  --path games/yuga-native --script res://tests/tactical/full_match_cases.gd -- \
  --report=/absolute/fresh/full_match.json
godot --headless --audio-driver Dummy --path games/yuga-native \
  --script res://tools/map-reuse-placement/test_integrated.gd -- \
  --output=/absolute/fresh/integrated.json
git diff --check
```

Python `ast.parse()` passed for `tools/studio/run-tactical-capture.py` without
creating a bytecode cache. `git diff --check` passed. The updated workflow
explicitly adds `hero_finish`, `showcase`, `hero_pose` and `hero_dossier` to the
existing tactical loop; its final hosted result belongs to the successor
commit and must be observed separately.

The full-match run finished **24 rounds, 13–11**, with one halftime switch,
eight plants and one defuse. Its 1,273.67 simulated seconds used the fixture's
accelerated clock, an idle human actor and nine local bots. It is not a human
balance session or elapsed player experience. The integrated map run rejects
both a same-count substituted cover identity and a moved cover while retaining
the same 43-box total; this is a stronger oracle than merely changing 39 to 43.

## Existing visual evidence actually reviewed

[Capture audit](verification/capture-audit.json) independently verifies all
**13 stills and 135 frame PNGs** against the existing studio3 receipt. All
eight pinned runtime/asset hashes match current source. `ffprobe` successfully
read all 135 H.264 frames of `studio-motion.mp4`: 1280 × 720, 15 fps, 9 seconds.
This is a file/decoded-frame check; it does not itself establish motion quality.

This reviewer actually inspected these original images under
[`studio3/visual-r1`](../../tactical/studio3/visual-r1/):

- `01-hero-ready.png`: hero silhouette, weapon presentation, ability text and pinned Casual action.
- `02-hero-aim.png`: raised firearm/upper-body pose.
- `02-hero-x.png`: free left-hand gesture and X dossier information.
- `03-hero-back.png`: rear garment/hair silhouette and firearm hold.
- `05-first-person-q.png`: native first-person hand/weapon component, paused controls and dossier.
- `07-studio-960-large.png`: 960 × 540 window with 1.5× UI scaling.

The inspected normal-size views render the actual Rama/SURYA and legible
selected ability/counterplay. Hero and first-person views are visibly distinct;
the first-person view disables Front/Back. The enlarged compact-window view
retains navigation and **Choose Casual**, but the hero occupies a small area
and the ability facts/firearm details require scrolling. These are concrete
remaining presentation limits, not full accessibility or final-art acceptance.
The source capture uses Forward+ on **llvmpipe**, not a physical GPU.

The capture script selects modes/actions programmatically and advances an
explicit preview clock. This lane did **not** perform new OS mouse/keyboard
input, listen to audio or watch the film in real time. Do not call it an ordinary
input journey or a new continuous-motion review. Earlier specialist reviews
and meaningful rejected pose/UI attempts remain in their original directories.

## Publication hygiene and remaining ownership

[Candidate audit](verification/candidate-audit.json), observed at
03:16:45 UTC, covered 237 changed/untracked files totaling 20,578,220 bytes;
the largest was 827,105 bytes, with none above 50 MiB. No user/cache path was
present in the earlier untracked inventory. A bounded scan of 83 text files
found no private-key, GitHub-token, AWS-access-key or OpenAI-key patterns.
This is not comprehensive secret detection, and concurrent owners can add
files after the observation. Root must inspect the final staged inventory.

The two retained SURYA export logs include the meaningful failed first export
and its correction; preserve both. Existing studio3 failed checks are evidence,
not grounds for deleting files to make the checkpoint look cleaner. Packages
and runtime user state stay under their established ignored paths.

At the initial review, `studio3/STATE.json` and its README still described
visual capture, packaging and publication as pending even though capture
files existed; root owns reconciling those current-state summaries with actual
receipts. Package files appeared concurrently, so this report deliberately
does not claim their completion, source identity or run results.

**Next owner: root** for final source/manifest consistency, concrete README,
roadmap/dashboard update, normal Git push and successor CI observation.
Ordinary studio input, package execution, supported-platform checks,
human art/feel review, improved compact-window hero framing, full-body
gameplay motion, another distinct hero and online Casual remain separate gates.

## Key source hashes

**Later integration note:** after the independent review above, the concurrent
studio owner completed its [package and Linux input handoff](../../tactical/studio3/README.md)
and updated the studio state. Its [separate input receipt](../../tactical/studio3/package-input-r1/review.json)
records 19 events, nine reviewed originals and native Quit 0. These are that
owner's results, not an additional execution by this reviewer. Publication and
dashboard checks belong to [the resource publication record](PUBLICATION.md).

The execution receipt contains the full reviewed set. Principal new/changed
runtime identities at this review:

| Source | SHA-256 |
| --- | --- |
| `scripts/tactical_frontend.gd` | `fe1b31b920eeb4a6b08c0807ecde3400ce6dd8627bf247ad20e172dfe62018b5` |
| `scripts/tactical_hero_showcase.gd` | `ddd77d6076ee6f1b4b844c9b15576c27e52ccbe98e17e1ba9b2a6788668d3143` |
| `scripts/tactical_hero_pose.gd` | `43dee1cd2c890e38b09377bba3158405331b1599e10c325555ee0f383a77c61e` |
| `scripts/tactical_hero_dossier.gd` | `0746a845396cc113d807fe26baf366a80b87ab077a4c06dd5a21c7ed0ce66168` |
