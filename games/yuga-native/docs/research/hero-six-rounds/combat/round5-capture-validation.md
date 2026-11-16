# Retained hero capture: strict oracle correction

Task YUGA-HERO-6R, native offline hero; owner `hero_combat`, root-authorized
`tools/run-rama-gameplay.py` change. `tools/capture-rama-gameplay.gd` is unchanged.
Frozen capture project, original PNGs and original JSON report are unchanged.

The original runner rejected frame 0 because it required displayed HUD text to
equal `runtime.notice`. The HUD already intentionally presents explicit combat
phase text: `drawing` becomes `DRAWING`, and the last `released` event becomes
`RECOVERING` while the action is still locked. All 118 differences in the 363
frames match this behavior; the other 245 notices already matched exactly.

The corrected oracle derives expected text from the recorded authority cast
phase and release flag, and ability labels in the frozen rules JSON. It rejects
multiple committed actions and inconsistent phase/release/runtime notices.
After recovery it still requires exact runtime text. It does not accept
case-insensitive text, arbitrary substitutions or stale phase labels.

The new `--validate-only` path checks retained bytes against their frozen source
project and writes a fresh separate receipt. It starts no renderer, modifies no
capture source/image/report and records both the captured runner and independent
validator hashes. All **363 frames and 25 stills** passed complete image hash,
source/import identity, clock, lifecycle, health/shield and field-expiry checks.

```sh
python games/yuga-native/tools/run-rama-gameplay.py \
  --output /workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/root/hero-capture-r1 \
  --project /workspaces/ANDOLAN/.local-tools/review/hero-six-r1-source \
  --validate-only \
  --validation-report /workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/round5/hero-capture-validation-r2.json
python games/yuga-native/docs/research/hero-six-rounds/combat/capture_oracle_cases.py
```

[Independent cases](round5/capture-oracle-cases.json) passed **22/22**, including
premature recovery, stale drawing, stale old event copy, a different ability's
label, false release flag, inconsistent runtime event, duplicated committed
cast, stale recovery after readiness and a changed original image hash. The
first probe command had an incorrect repository-parent path and failed before
testing; corrected source finds the actual workspace. Python compilation and
`git diff --check` passed. The meaningful original rejection is preserved at
`../root/hero-capture-r1.log`.

The [video receipt](../root/hero-capture-r1/rama-video.json) binds the successfully
encoded and fully decoded silent MP4: 363 original 1280 × 720 frames, 30 fps,
12.100 seconds, SHA256
`e5a4e91cd1e4683c084c9ec96332077ddcf4bbbf741ff88c476a9d65179c565d`.
Encoding used the existing runner's FFmpeg arguments (`libx264`, two threads,
medium, CRF 18, yuv420p, faststart); ffprobe confirmed exactly one video stream
and 363 decoded frames; FFmpeg `-xerror -f null -` completed successfully.

These are five separately reset actual offline takes with staged live receivers
and deliberate cuts, plus separate low-angle replay stills. Silent simulated
30 fps does not establish real-time hardware performance or audio audition.
The [pixel review](round5/hero-pixel-review-r1.json) lists the exact 49 originals
actually opened by this reviewer; validation of all byte hashes is distinct
from visually inspecting all 363 frames. Warm ordinary input and the new map
need their separate evidence. Root owns delivery and the next capture.
