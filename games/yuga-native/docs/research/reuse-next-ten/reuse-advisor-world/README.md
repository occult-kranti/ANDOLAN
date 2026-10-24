# Owned-event playback inspector

Accepted for **offline inspection only**: a small Python adaptation of Source 2
Viewer's actual MIT event-window implementation, exercised on events emitted by
YUGA's existing Rama Kit and Army. This continuation changes no canonical runtime,
asset, damage rule, audio scheduler or map. Source checkpoint:
`3497197745beb8e0fd22a9b67efe505700dec469`.

The useful output is an event table and frame-by-frame report showing exactly
which recorded event ordinals fall in each playback window. This lets a motion
reviewer inspect begin/release/impact/recovery/end boundaries under a changed
display cadence while retaining the original 20 Hz simulation times and identity
pair `(generation, event_seq)`. It does not reconstruct either commercial game.

## Run and inspect

From the repository root, with the existing Godot and Python installations:

```sh
python3 games/yuga-native/docs/research/reuse-next-ten/reuse-advisor-world/experiment/run_experiment.py \
  --output /workspace/scratch/owned-event-inspection-fresh
```

The runner requires a fresh absolute directory, hashes its engine and five local
scripts, limits every subprocess to 45 seconds, captures the real fixture, runs
the checker, then writes 30/60/120 Hz and mixed-hitch JSON reports. It neither
installs tools nor downloads inputs. Each report maps window ordinals back to the
retained `event_table`, including original `time_s`, `cast_id`, `generation` and
`event_seq`. Windows are capped at 5,000 per ability.

To inspect an already captured trace:

```sh
python3 games/yuga-native/docs/research/reuse-next-ten/reuse-advisor-world/experiment/inspect_trace.py \
  --trace /workspace/scratch/owned-event-inspection-fresh/actual-events.json \
  --hz 60 --mixed-hitch \
  --output /workspace/scratch/owned-event-inspection-hitch-fresh.json
```

The mixed cadence repeats `1/60 s, 190 ms, 1/120 s, 37 ms`. These are **inspection
steps**; the captured Army still receives 170 accepted 50 ms simulation steps per
ability. Ordinary windows are half open, the final non-loop window retains its
exact terminal event, equal-time events retain source order, and pauses or
backward seeks produce no crossed events. For a window spanning one or more whole
loops, each authored event is reported once. Across wrap-around, source order is
retained rather than chronological order across loop iterations. A caller needing
occurrence counts or chronological execution must use a different contract.

## Executed result

[Accepted R3 receipt](evidence/accepted-r3/run.json): all six commands exited 0
under Godot `4.6.3.stable.official.7d41c59c4`. The actual fixture passed **24/24**
checks; the Python checker passed **67/67**, including all **19** retained source
and license hashes. The CLI reports retained all 27 selected actual event
ordinals once at each cadence.

| Actual ability | Observed events including ticks | Selected lifecycle/contact events | Terminal time |
| --- | ---: | ---: | ---: |
| Kodanda | 28 | 5 | 1.15 s |
| Piercing Dawn | 39 | 5 | 1.70 s |
| Measured Step | 13 | 5 | 0.40 s |
| Guardian Circle | 112 | 5 | about 5.35 s |
| Dawn Volley | 54 | 7 | 2.35 s |

There are 246 observed events; 219 `tick` events are counted and excluded from
this lifecycle report. The capture retains the 27 selected event snapshots, not
all tick payloads. Inspection traversed 331, 661, 1,317 and 174 windows at 30,
60, 120 Hz and the mixed cadence respectively. Each recorded ordinal also
appeared three times in three display loops at each fixed cadence. Separate
checks cover start/terminal equality, equal-time events, restart, pause,
multi-loop coalescing, malformed numbers, invalid terminal flags, duplicate
identities, reversed traces and a deliberately wrong closed-window comparison.

[Rejected R2](evidence/rejected-r2/checks.json) is retained: **62/65** checks
passed, with all three Measured Step loop cases reporting four begins over three
loops. The cause was `(3 * .4) / .4` rounding above 3. The accepted local fix
recognizes exactly represented duration multiples before fractional wrapping; it
uses no time epsilon. The failed adapter's exact bytes are retained and match its
recorded hash. R3 also verifies that a real advance past the endpoint still
reports the next beginning. This is an adapter repair, not evidence of a fault
in the compiled upstream tool, which was not executed.

## Source and adoption decisions

All immutable URLs, acquisition times, byte counts and file hashes are in
[sources.json](sources.json). The 19 retained text files total 179,786 bytes.
They were acquired by the interrupted worker before this continuation; their
local hashes were verified here. [NOTICE.md](NOTICE.md) retains attribution and
links the full MIT license texts. [provenance.json](provenance.json) records local
modifications and the eleven checked production file hashes.

| Source actually inspected | Decision and evidence |
| --- | --- |
| [Source 2 Viewer `SampledAnimationEvents.cs`](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/a2d07483864d380940f61abf52ddfcb905a00633/Renderer/Animation/SampledAnimationEvents.cs), commit `a2d07483864d380940f61abf52ddfcb905a00633`, SHA-256 `0529e7eb646c9dace4b0bd7ad6f28a1d6c33a7d206e1de0bce1a7a00504ceed6` | **Accept adapted algorithm for this inspector.** The half-open, wrapped and whole-timeline conditions are ported to Python, with local validation and endpoint corrections documented in the notice. |
| [Upstream event tests at the same pin](https://github.com/ValveResourceFormat/ValveResourceFormat/blob/a2d07483864d380940f61abf52ddfcb905a00633/Tests/Renderer/SampledAnimationEventsTest.cs), SHA-256 `d42e22c3ee60a941bb943fa75bdd30a4be8b1a9ff749b5b08112bc20570f0c5d` | **Read, not executed.** They identify pause/restart/start/loop cases, but load upstream game-resource fixtures. Our executable cases use original Rama data and local synthetic values. |
| VRF `GltfModelExporter.World.cs` / `.Skeleton.cs` at the same pin | **Defer exporter integration.** Parent transforms, material/skin selection, physics pairing and recursive bone hierarchy are useful inspection contracts. No export, commercial map intake or rig retarget was run. |
| [OWLib `EffectParser.cs`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/DataTool/Helper/EffectParser.cs), commit `546efa19516d7df7ba138802d221c73ad886df28`, SHA-256 `6f26bc818a268596e36f36f188a81eae2756a9f7584b94a1c44fc1600b9ec8b9`, plus `SaveLogic/Effect.cs` | **Accept as a future metadata reference only.** `ChunkPlaybackInfo` carries time and hardpoint data; model effect records preserve model/material/animation links. This is a useful dependency-inspection pattern. No OWLib parser is ported or executed. Its assignment of `component.Duration` to `EndTime` is not treated as proof of absolute-end semantics. |
| OWLib `owmap.txt` / `RefPoseSkeleton.cs` at the same pin | **Defer format import.** Instances retain position/scale/rotation and model/material references; skeleton export handles hierarchy and reference transforms. Available code does not grant rights to commercial map/hero data. |
| Applying the sampler to combat, repeated audio or replay authority | **Reject.** Whole-loop hitches deliberately coalesce repeated occurrences; wrapped output is in source order. Combat timing continues to belong to the existing Kit/Army owner. |

## Next specific integration

The motion owner can add an **offline sidecar** to the existing
[`W5/source/diagnostic-event-resampling-r1.gd`](../W5/source/diagnostic-event-resampling-r1.gd)
review: pair each real `ability_event` identity with a sampled bow/string/muzzle
socket transform and the effect/audio receiver's acknowledgement, then have this
inspector group those records by playback window. Keep missing attachment or
acknowledgement records visible as missing rather than inventing success. This
would make a release-frame disagreement inspectable without changing scheduling.

Acceptance for that next packet: one actual Kodanda release and one Dawn Volley
with three impacts; captured reset/cancel boundaries keyed by generation; all
records source-pinned; paired continuous rendered review at 30/60/120 Hz. The
sidecar must preserve the 20 Hz owner and distinguish real-clock audio cooldown
from simulation time. No integration code for that next packet is claimed here.

Actual visuals/input/audio reviewed in this packet: **none**. There is no rig,
contact, listening, online, hardware-performance or full-match acceptance. No
full extraction tool, game binary, leaked asset or commercial fixture was
downloaded. The next owner is the motion-review worker; root owns publication.
