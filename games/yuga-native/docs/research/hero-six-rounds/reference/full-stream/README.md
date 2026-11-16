# Complete-stream audit and audio addendum

Task **YUGA-HERO-6R**, native YUGA, reference/evidence worker. This extends the
R1/R2 sampled study after the user's request for comprehensive frame and audio
analysis. Baseline remains `7162b5d0b666e4422b0bc73100e1fba947d3323f`; all production
edits belong to other workers. No engine import, render, runtime edit or commercial
game extraction was performed in this lane.

## What is actually covered

Both complete video streams were decoded successfully with FFmpeg `-xerror`.
Every decoded frame has a full source-resolution YUV420P MD5 record and an
activity-index row. Every audio stream was decoded to mono 16 kHz PCM in full.
This establishes machine coverage and decode integrity, **not that a person
watched every frame or listened to the complete audio**. Original MP4s are intact.

| Input | Decoded frames / metadata frames | First–last frame PTS | Decode wall time |
| --- | --- | --- | --- |
| gameplay.mp4 | 61,341 / 61,341 | 0–2046.713380 s | 37.93 s |
| all ults.mp4 | 77,875 / 77,875 | 0–2595.800000 s | 47.80 s |

Source hashes, exact FFmpeg/ffprobe argv, version, all output hashes and exit
codes are in `gameplay/receipt.json` and `ults/receipt.json`. Counts match all
139,216 frames. The activity calculation compares all consecutive decoded
frames at 160×90, retaining central-region and whole-frame mean absolute
luminance differences plus a 16-bin histogram difference. The 640×360 source
frames are hashed before downscaling. `every-frame-activity.csv` retains each
PTS; `five-second-activity.json` summarizes every five-second interval.

The scene-candidate flag (`frame_delta >= 20` and histogram total variation
`>= 0.15`) is a heuristic. Its 867 gameplay and 363 tutorial candidates include
flash effects, fast camera movement and edits; they are **not 1,230 verified
scene cuts**. The highest gameplay activity bucket, 29:40–29:45, was personally
inspected at native cadence and contains extreme overlapping visual effects.

## Native-frame visual review

In addition to the 831 accepted sampled stills documented in the R1/R2 report,
the worker personally inspected all 32 contact sheets of these eight sequences:
480 frame images at native cadence (60 per sequence). Across all accepted old/new
sets there are1,311 reviewed image samples representing1,256 unique source frames
(538 gameplay,718 tutorial);55 samples overlap another accepted window. Exact
CFR/PTS-based accounting is retained in `visual-coverage.json`. Source-resolution PNGs
are retained. The two Celeste windows overlap by 0.5 s; these are image counts,
not 480 additional unique source frames. Selected original-size PNGs were also
inspected. This is about 15.5 s of new contiguous temporal windows, not continuous
human viewing of the 77-minute input pair. Audio was not auditioned by the worker.

| Window / folder under `../native-frames/` | Direct visible observation | Design inference, with limits |
| --- | --- | --- |
| `gameplay-traversal-995`, 16:35.028–16:36.997 | Hero ascends an orange line in an enclosed vertical shaft; a framed opening grows closer; health/HUD remain anchored. | A vertical connector is a readable route, not merely a high roof. Exact control bindings, speed and ability/item ownership remain unknown. |
| `gameplay-traversal-exit-997`, 16:37.030–16:38.999 | Rope ascent exits to a roof at about 16:37.5; the hero lands, approaches a labeled Sinner's Sacrifice machine and strikes it at about 16:38.5; health/numbers change. | Utility access follows a traversal commitment into exposed space. This is not a shop UI or confirmed exchange formula. Rama already has flight/tether traversal, but his kit requires a legal ground-plane cast origin; an analogous balcony needs supported navigation and an honest return route. |
| `gameplay-objective-1199`, 19:59.032–20:01.001 | Hero runs through an opening into a yard with cart/log cover, fires a small shot, then turns into another route. | Small secondary props can frame an approach without forming an impassable clutter wall. This window is the approach, not the later target's stun. |
| `gameplay-target-1210`, 20:10.010–20:11.979 | Large stationary target in a separate chamber, overhead health bar, very clear large body and approach ring; repeated hero attacks; target changes pose and rises. | Dedicated objective encounter space supports target windup/readability. Whether this target is neutral or team-owned, its exact name, rewards and spawn rules remain unconfirmed. Earlier 'neutral-looking' wording was an inference. |
| `gameplay-motion-532`, 08:52.032–08:54.001 | Several large white/purple effects overlap hero and enemies; visible STUNNED status persists across consecutive frames; after effects recede, hero moves into open lane and attacks again. | Stable crowd-control labels, a quiet floor and retreat space are as important as additional VFX. Copying the reference's highest particle density would reduce clarity. |
| `gameplay-overload-1780`, 29:40.013–29:41.982 | Elevated camera near a large sign, several beams/orbs, bright purple stars and rotating geometry obscure the center; HUD remains visible. | Density must be budgeted around reticle, actor feet and hostile warnings. This is selected by an objective activity index, not just an attractive screenshot. Individual effect ownership cannot reliably be attributed in the overlap. |
| `ults-celeste-light-eater-291`, 04:51.000–04:52.967 | Small attacks repeatedly trigger a bright target outline/column; target health changes while the Light Eater tooltip stays on screen. | A persistent debuff and repeated proc feedback need visual separation from the base attack. The tooltip explains the sequence; do not assume every shot shown is a fresh ability cast. |
| `ults-celeste-primary-292`, 04:52.500–04:54.467 | Close staff/body attack, a large target outline response, return/recovery, then another small attack. | Weapon/action pose should communicate commitment and recovery independently of the target's proc effect. Folder name is a sampling label, not an authoritative classification of every action as primary fire. |

## Local speech transcription and audio energy

The tool discovery found no local-file audio-listening/understanding tool.
Magnific's video inspection tools require completed service creations and do
not establish local MP4 listening. No upload or paid generation was used.

Full decoded PCM is fed locally to faster-whisper **1.2.1**, CTranslate2 **4.9.0**,
using CPU int8, six threads, beam size 3, English, word timestamps and VAD.
Model: [Systran/faster-whisper-small.en](https://huggingface.co/Systran/faster-whisper-small.en),
revision `d1d751a5f8271d482d14ca55d9e2deeebbae577f`, model-card MIT license.
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) is MIT software;
its public benchmark is not this machine's performance claim. Exact package
versions, checkpoint file hashes and parameters are in each ASR receipt.
Dependencies/model caches remain in `/tmp/yuga-hero-audio-venv` and
`/tmp/yuga-hero-asr-models`; no model was integrated into YUGA.

`segments.jsonl` retains timestamps, word probabilities, average log probability,
compression ratio and no-speech probability. `transcript.txt` is machine text.
It is not a verified quotation or current authoritative Deadlock rules. Proper
names and phrases are visibly mistranscribed (e.g. 'Deadman Danny', 'Repost',
'route' for root). The original visual title cards take precedence for the roster.
VAD may suppress speech; full-input processing is not proof every utterance was
recognized. Narrator evaluations and exact numerical claims are not balance facts.

Both transcription jobs completed. The tutorial processed all 2595.8748125 s,
with VAD retaining the whole stream, producing 594 segments / 8,312 timestamped
words through 43:13.49 in 252.29 s wall time. The worker read all 594 machine-text
segments; this is not audio listening. No segment had average log probability
below −0.6 or no-speech probability above 0.6, but confident recognition still
contains obvious proper-name errors. These thresholds do not establish accuracy.

The gameplay full-input pass completed in 11.23 s, retaining 30.304 s after VAD
and returning one introduction at 00:06–00:09.36. **The rest is not silent**:
one-second RMS analysis found no window below −60 dBFS; median RMS was −27.357
dBFS. For the tutorial, median was −23.117 dBFS, with no one-second window below
−40 dBFS. These are downmixed signal-energy measurements, not a loudness-mix,
spatial-audio, sound-design or speech-quality review. Original stereo audio is
preserved in the source MP4s. `audio-energy.json` records every second.

ASR first attempt failed before producing text because PyAV 19's `av.open()`
rejects faster-whisper's `metadata_errors` argument. The failed receipt remains
at `gameplay/asr-small-en/`. Successor `gameplay/asr-small-en-r2/` feeds verified
16-bit PCM samples using Python's `wave` module, avoiding that incompatible API.
An exploratory energy calculation also encountered a NumPy int64 JSON encoding
error before writing a result; `audio_energy.py` casts scalar types explicitly.

## Narration-supported design questions

These are paraphrases of machine transcript intervals, cross-checked against
the already reviewed tutorial imagery where stated. They are not listening claims.

| Tutorial interval | Narration claim / visual relationship | Original YUGA implication |
| --- | --- | --- |
| 03:19–03:25 | Billy's pull can be broken with line of sight. | Real cover must match visual cover; telegraphs should communicate the available escape action. |
| 03:59–04:10 | Calico's alternate form accesses restricted tunnels; tutorial says four heroes can use them. Earlier dense frames show the form/traversal. | Route access is a gameplay contract; inaccessible decorative holes need no misleading use affordance. Do not claim Rama has this traversal. |
| 04:29–04:45 | Celeste has distinct gravity/aerial control; clip gameplay shows frequent aerial movement. | Hero motion traits and map verticality must be designed together. Rama already supports flight/tether traversal, while ability casts require the army's ground plane; provide return routes to legal cast origins. |
| 05:51–06:05 | Donny's jetpack has heat and a forced dive with miss risk. | Movement power should expose commitment/failure state in HUD and pose, rather than giving a cost-free escape everywhere. |
| 06:37–06:46 | Doorman's paired portals can be used by either team. | Utility ownership/access rules must be visible and testable; a shortcut can also create enemy risk. |
| 08:44–08:59 | Dynamo pulls targets while remaining committed to channeling. | Strong control needs a readable commitment window and interruption policy; map cover should leave counter-approaches. |
| 14:51–14:58 | Kelvin creates traversable paths. | A dynamic path is actual navigation/collision work, not a shader stripe. Keep future feature scope explicit. |
| 16:46–17:04 | Lash's attack depends on height and his grapple needs another actor. | Vertical access, target availability and landing space constrain power; adding rooftops alone cannot recreate that kit. |
| 17:43–17:51 | McGinnis has an area healing pod and a wall the opponent must break. | Distinguish area-bound healing, already granted shields and solid obstruction. Rama guide was corrected after independent code review. |
| 20:34–20:51 | Mirage map relocation has a vulnerable waiting period; damage cancels it. | Travel UX needs arrival/destination clarity and a cancellation reason; do not suggest arbitrary free teleports. |
| 21:01–21:07 | Mo + Krill can enter the underground burrows. | Repeated route systems need explicit per-hero access, not hard-coded visual exceptions. |
| 24:05–24:54 | Paradox's wall and swap interact with the path between actors. | Projectile/path geometry must be shared by warning, authoritative hit testing and visible effect. This motivates Rama's per-lane X warning fix. |
| 26:42–27:33 | Rat swarm can be escaped by dashing; planted banner claims an area; Rat King also uses tunnels. | Distinguish mobile buff, placed zone and retained protection; present an escape response rather than only larger particles. |
| 28:05–28:34 | Rem's helpers collect boxes/Sinner's Sacrifice or support allies/troopers; narration describes team economy effects. | Side utilities and lane units can create map decisions beyond kills. No exact economy amount, ownership or respawn rule is established by this transcript. |
| 28:55–28:59 | Rem is described as the fourth tunnel-access character. | The tutorial's four named access cases are Calico, Mo + Krill, Rat King and Rem; this is the supplied clip's roster, not a current roster guarantee. |
| 29:47–29:57 | Seven's ultimate is described as doing no damage outside line of sight. | Actual solid cover is a counterplay tool and must match the visual perimeter of the new architecture. |
| 37:37–37:47 | Violet's created vantage/blocking shapes are described as breakable by heavy melee. | If a surface can be traversed or broken, it needs real collision and a visible durability/use contract. Decorative jali must not impersonate a breakable shortcut. |
| 40:31–40:42 | Warden's delayed bind can be avoided by leaving a circle. | Clearly distinguish danger now from danger on expiry; preserve warning boundary contrast against detailed paving. |

Correction after native R5 review: the shorthand 'ground-only Rama' in an early
message/addendum draft was too broad. `player.gd` exposes flight and grapple;
`rama_ability_kit.gd:126` rejects cast origins with army-local elevation above
0.4 m. The existing R1 report already distinguished flight/grapple from ground-only
**casts**. Map art must not imply the abilities work on every elevated surface.

## Original map production priorities

The worker sent primary architecture references to the map owner: the
[Archaeological Survey of India](https://asi.nic.in/pages/WorldHeritageFatehpurSikri),
[UNESCO](https://whc.unesco.org/en/list/255/),
[Ministry of Culture](https://culture.gov.in/fatehpur-sikri), and
[Uttar Pradesh tourism's Fatehpur Sikri page](https://tajmahal.gov.in/fatehpur-sikri.aspx).
They support studying terraces, linked courts/corridors, sandstone masses and
screened openings. Fatehpur Sikri is a 16th-century reference; using bracket,
chajja, jali and pavilion ideas in original Sangam fiction is not an ancient-period
reconstruction or a single historically exact style. These URLs grant no photo,
texture or model reuse license. No source image/asset was copied into runtime.

Prioritize a coherent street/court composition with genuine cover choices,
shaded connective arcade, upper/lower silhouette and distant landmark before
small ornament. Existing imported textures retain their existing notices;
`assets/environment-finish/NOTICE.md` documents only the project's original
procedural finish and does not relicense imported source maps. New authored
collision and sightline changes need native traversal, obstruction, ability
and day/night visual tests. Architecture richness is not verified GPU performance.

## Reproduction

From repository root (fresh output folders required):

```sh
python3 -m venv /tmp/yuga-hero-audio-venv
/tmp/yuga-hero-audio-venv/bin/python -m pip install faster-whisper==1.2.1
/tmp/yuga-hero-audio-venv/bin/python games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/audit_stream.py gameplay.mp4 games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/gameplay
/tmp/yuga-hero-audio-venv/bin/python games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/audit_stream.py 'all ults.mp4' games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/ults
/tmp/yuga-hero-audio-venv/bin/python games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/transcribe_stream.py games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/gameplay/speech-16k-mono.wav games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/gameplay/asr-small-en-r2 --threads 6 --revision d1d751a5f8271d482d14ca55d9e2deeebbae577f
/tmp/yuga-hero-audio-venv/bin/python games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/transcribe_stream.py games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/ults/speech-16k-mono.wav games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/ults/asr-small-en --threads 6 --revision d1d751a5f8271d482d14ca55d9e2deeebbae577f
/tmp/yuga-hero-audio-venv/bin/python games/yuga-native/docs/research/hero-six-rounds/reference/full-stream/audio_energy.py
python3 tools/studio/analyze-hero-reference.py gameplay.mp4 --output games/yuga-native/docs/research/hero-six-rounds/reference/native-frames/gameplay-traversal-995 --start 995 --duration 2 --step 0
```

All native-window extraction commands are retained in their receipts; substitute
the listed start/source/output to reproduce the other seven. The script pins
the checkpoint's resolved revision in its receipt; exact dependencies and model
files must be restored from the recorded pins for strict reproduction.
