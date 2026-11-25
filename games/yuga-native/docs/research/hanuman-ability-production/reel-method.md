# Hanuman ability reel

The five shots run the native Hanuman Trial and use the same Hanuman mesh, trial input, collision, authority clock and effects as practice. The storyboard resets the trial between shots to keep the ward shield and ground hazards from carrying into the next demonstration. A separate capture camera follows Hanuman and leaves his player camera responsible for aim. The Mountain Pulse shot moves from the hero to the landing area during travel.

Each video image comes from one software-rendered Godot viewport sample. The trial runs its 60 Hz physics clock at a fixed 24 fps capture cadence. The 1280 × 720 reel plays those frames at 24 fps. This cadence records visible timing and does not benchmark GPU performance. The original renderer ran with the Dummy audio driver. The receipt distinguishes game capture from any sound cues added in editing.

The frame ledger indexes the beginning, release, impact, recovery and end of each ability. The Maruti Udayana impact event accepts movement. Its separate landing frame records the first completed vault that reaches the destination without a block. The published video adds the authored trial cues at their measured release and impact sample indices. [Storyboard](../../../tools/hanuman-capture/ability-storyboard.json) · [Video](../../../art/hanuman/reels/hanuman-abilities.mp4) · [Frame and source receipt](reel-receipt.json) · [Cue receipt](reel-audio.json) · [Decoded frame study](reel-contact.jpg)

## Reproduce from the repository root

Use a fresh absolute output directory, an active display and imported Godot assets.

```sh
godot --path games/yuga-native --rendering-method forward_plus --audio-driver Dummy \
  --fixed-fps 24 --resolution 1280x720 --disable-vsync \
  --script res://tools/hanuman-capture/native_reel.gd -- \
  --storyboard=res://tools/hanuman-capture/ability-storyboard.json \
  --output=/absolute/fresh/hanuman-abilities

python3 games/yuga-native/tools/hanuman-capture/encode_reel.py \
  --frames /absolute/fresh/hanuman-abilities --name hanuman-abilities-silent

python3 games/yuga-native/tools/hanuman-capture/score_ability_reel.py \
  /absolute/fresh/hanuman-abilities/render.json \
  /absolute/fresh/hanuman-abilities/hanuman-abilities-silent.mp4 \
  /absolute/fresh/hanuman-abilities/hanuman-abilities.mp4 \
  --report /absolute/fresh/hanuman-abilities/reel-audio.json

python3 games/yuga-native/tools/hanuman-capture/review_ability_reel.py \
  --frames /absolute/fresh/hanuman-abilities \
  --movie /absolute/fresh/hanuman-abilities/hanuman-abilities.mp4 \
  --report /absolute/fresh/hanuman-abilities/reel-receipt.json \
  --contact /absolute/fresh/hanuman-abilities/reel-contact.jpg
```

Add `--headless` to the Godot options and `--simulate-only` after `--` to check the input path and event times without capturing video. Encoding, cue mixing and frame review require FFmpeg and Python with NumPy and Pillow.
