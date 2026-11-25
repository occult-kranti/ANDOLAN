# Gada and Lanka in the practice court

The raised oblique cameras keep the whole actor, outer boundary and strike in frame. Gada’s brass crescent crosses the first training target when its health falls from 90 to 56. Lanka’s rear sweep hits three targets for 28 apiece. The image one sample later shows them at 61.6 as exposure begins. The target pedestals still cover parts of the floor symbols where they stand. [Gada](gada-impact.png) · [Lanka](lanka-impact.png) · [Camera, impact and file evidence](receipt.json)

| Action | Authority impact (video frame / physics tick) | Displayed image (video frame / physics tick) |
| --- | --- | --- |
| Gada | 31 / 88 | 31 / 89 |
| Lanka | 236 / 600 | 237 / 604 |

The 960 × 540 replay ran at 24 samples per second with 60 Hz physics in software-rendered Forward+. Each complete impact record matched the original reel. The retained images also matched the original samples’ actor and effects states. The camera offset and aim use metres in Hanuman’s right, up and forward directions. The receipt includes the exact storyboard and sparse-capture patch. [Original gameplay reel](../../../../art/hanuman/reels/hanuman-abilities.mp4)

## Reproduce

Use a separate checkout of the pinned capture commit in the receipt, Godot 4.6.3 and an active X11/Vulkan display. Copy this receipt into a fresh working directory. From that directory, run the following with the absolute path to the pinned checkout in `repo`. The original captured PNGs use llvmpipe LLVM 19.1.7. Driver or GPU differences can affect pixel hashes.

```sh
git -C "$repo" show HEAD:games/yuga-native/tools/hanuman-capture/native_reel.gd > driver-original.gd
python3 - <<'PY'
from hashlib import sha256
import json
from pathlib import Path
r = json.loads(Path("receipt.json").read_text())
assert sha256(Path("driver-original.gd").read_bytes()).hexdigest() == r["driver_original_sha256"]
Path("driver.patch").write_text(r["driver_patch"])
p = Path("storyboard-wide.json")
p.write_text(json.dumps(r["storyboard"], indent=2) + "\n")
assert sha256(p.read_bytes()).hexdigest() == r["storyboard_sha256"]
PY
patch driver-original.gd -o driver-wide.gd < driver.patch
godot --headless --path "$repo/games/yuga-native" --editor --import --quit
godot --path "$repo/games/yuga-native" --display-driver x11 --rendering-method forward_plus \
  --audio-driver Dummy --fixed-fps 24 --resolution 960x540 --disable-vsync --disable-render-loop \
  --script "$PWD/driver-wide.gd" -- --storyboard="$PWD/storyboard-wide.json" --output="$PWD/wide-output"
```

Open `frame-00031.png` and `frame-00237.png` in `wide-output` and compare the two impact events in `render.json` against the receipt.
