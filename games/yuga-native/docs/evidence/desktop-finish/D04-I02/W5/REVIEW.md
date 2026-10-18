# D04 / I02 — Dawn Volley feedback onset

The actual imported Confluence scene reproduced a delayed Volley arrow appearing 50 ms before its authoritative pulse. A second failure left the corresponding notch present until the next presentation update. The bounded correction changes only `scripts/rama_ability_effects.gd`: arrow eligibility and notch removal follow accepted authority age, while launched-arrow travel retains its existing interpolation. No duplicate audio onset was observed in this witness.

Source checkout at sealing: `4c9e0adf26dfb5f766a1e2140204ef08597bd94a`, with the owned working-tree correction below. No commit, import or raster was performed by this packet.

| Input | SHA-256 |
| --- | --- |
| Preserved baseline effects | `b77f68aeeb57ab5e7be8b84385505d1f7078cb90ef1cedc33c7e4d894ec9d8be` |
| Corrected effects | `119353e71e5ad1eee61360d52db036075a6be60ec30c4c2ee228b5656243db66` |
| Final combined fixture | `2cc5425fa44b09b61682a0b224066b78a1c181af343b91166d0c8699b1c4436c` |
| Unchanged motion | `8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8` |

## Failing witness and correction

The fixture instantiates the real world, imported hero, kit, vitals, action audio, effects and HUD. It removes troops to prevent unrelated contacts, grounds the actual player, and advances the ordinary authority API by 200 × 50 ms before a public Dawn Volley cast. It pauses between the first and second pulses, observes ten native paused process frames, resumes, applies lethal damage before pulse three, then restarts the same instance and completes another normal Volley. Kodanda and Piercing Dawn exercise the other projectile callers.

At army time 11.0 s, the second arrow had authoritative post-release age `0.0500000000000007` s and delay `0.1` s, but presentation age was `0.100000000000001` s. Baseline visibility was true, although audio correctly retained only draw + first pulse. The corrected arrow remains hidden until the next authority tick. This is a real clock-boundary mismatch; a cast beginning at time zero did not expose that arrow failure because floating-point rounding fell on the other side of the comparison.

The second authoritative tick also exposed stale notch geometry. Presentation was already in mesh frame 31. Baseline retained 756 contour indices across that tick; the correction removes exactly one 12-segment notch, yielding 684 indices on the same accepted event. A bounded count of eligible arrows invalidates only Volley's mesh cache when a pulse crosses its boundary. Eligibility uses the existing kit/audio tolerance of `1e-8` s. It does not alter authority clocks, event order, delay data or projectile movement.

Caller audit: only Dawn Volley has delayed projectiles in the current kit (`0`, `0.1`, `0.2` s). Kodanda and Piercing Dawn each have a single zero-delay projectile; Measured Step and Guardian Circle have none. The latter's authoritative ward-expiry logic is unchanged. Contact hiding, interpolation, reduced-effects options and per-generation retirement remain in their existing owners.

## Executed checks

| Run | Result | Disposition |
| --- | --- | --- |
| Initial zero-start combined witness, `baseline-r1` | 12/12 | Narrow passing scope, preserved |
| Nonzero-start witness, `baseline-r2` | 11/12 | First real early-arrow failure, preserved |
| Expanded baseline, `baseline-r3` | 15/17 | Arrow and notch/cache failures, preserved |
| First candidate at nonzero/zero starts | 16/17 each | Fixture exact-float equality failure, preserved |
| Final identical fixture, baseline `baseline-r4` | 15/17 | Both product failures remain |
| Final candidate, `candidate-r2` | 17/17 | Nonzero start, pause/resume, defeat, restart and next normal release pass |
| Final candidate, `candidate-zero-r2` | 17/17 | Zero-start boundary control passes |
| Existing `rama_effect_adversarial_cases.gd` | 56/56 | All five ability chronologies, duplicate release/contact and geometry adversaries pass |

The first candidate's remaining failure was a test assumption, not another product change: the authority clamp added `8.88178419700125e-16` s to the presentation clock. The corrected fixture requires the same actual 30 Hz mesh-frame key and records the raw delta, allowing at most `1e-12` s arithmetic roundoff. It retains the exact 72-index removal and two-arrow requirement. The final before/after runs use identical test bytes; only the effects source differs. Earlier test versions and failures remain under `source-r1`, `source-r2` and `source-r3`.

All final engine runs exited as expected with clean logs. [execution-final.json](execution-final.json) records exact commands, affinity, environment, elapsed time, source hashes and result/log hashes. CPU4 affinity and LP/OMP/BLAS/MKL environment values of 1 were used; the Godot worker pool was not capped. The final baseline was restored briefly inside the exclusive effects ownership interval, then the candidate restored in a `finally` block before the succeeding runs. The retained execution driver refuses to overwrite existing result files.

[comparison.json](comparison.json), reproducible with `python3 compare_feedback.py`, establishes exact equality of all 84 complete authority events, kit/vitals/audio state, HUD labels and army time at matching observations. Every recorded arrow position and interpolated clock is unchanged. Motion diagnostics match except the native preroll sample census; that census difference is retained and is not a pose-equivalence claim. Every run pins its actual raw/imported hero and script inputs before and after execution.

## Disposition and handoff

Accept this narrow authority-to-presentation synchronization correction for source integration. The frozen W1 render children and prepared motion comparison stages retain their earlier effects source. They cannot be relabelled as captures of this correction.

No new rendered image, audible listening, operating-system input, continuous motion or physical-GPU feel acceptance is claimed. The outstanding motion contact tradeoffs and pending matched motion capture remain separate. Root owns source integration and any later source-bound visual/audio review; no further W5 runtime edits are pending.
