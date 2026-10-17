# Native traversal capture

These tools record actual Forward+ frames while injected Godot input actions drive
the normal player and collision simulation. Spawn and camera are staged before
the take. No player transforms are rewritten during the take. This is a scripted
input scenario, not evidence of human OS input, online play, or realtime rendering
performance.

Use a new absolute output directory for every run. Existing evidence, logs and
isolated user directories are never overwritten.

```bash
python games/yuga-native/tools/run-traversal-capture.py \
  --output /tmp/yuga-traversal-preview-r2 --preview

python games/yuga-native/tools/run-traversal-capture.py \
  --output /tmp/yuga-traversal-full-r2 \
  --shader-cache-seed /tmp/yuga-traversal-recovery-preview-user/cache/mesa
```

| Mode | Resolution | Consecutive frames | Measured physics ticks | Stills | Video |
| --- | --- | --- | --- | --- | --- |
| Preview | 960×540 | 24 | 48 | 3 | None |
| Full | 1280×720 | 180 | 360 | 5 | Silent six-second H.264 MP4, 30 fps |

The engine runs with `--fixed-fps 30` and the project retains 60 Hz physics. Every
captured frame must advance exactly two physics ticks. The take starts with a
grapple toward the first Sun ring, releases the tether, then starts flight with
ascent and lateral movement. The JSON records the exact input schedule, player
position/velocity, traversal state, actual modified skeleton pose digest, and
image hash. Every frame image and still also records the renderer's draw calls,
object count and primitive count. These counters describe the rendered workload;
they do not establish hardware frame-rate performance.

After the take, the overview, landing-deck and night views use separate camera
staging. The army engagement still advances the public army simulation by bounded
1/60-second steps until a real queued attack is observed. Its additional ticks,
simulation time and army counts are recorded separately and are absent from the
six-second video. The HUD still duplicates an exact frame from the take.

The runner verifies PNG dimensions/checksums, sequential frame/tick counts, source
hashes, fresh imported GLBs, and actual traversal outcomes before encoding. FFprobe
then verifies the full video's 1280×720 dimensions, 180 frames, 30 fps, six-second
duration and absence of an audio stream. The video contains no fabricated audio
synchronization. Root review of the actual images remains a separate visual gate.

The optional shader-cache seed copies only regular cache files into the new
isolated XDG cache and verifies each copied hash. It records a cache-file manifest
digest; Mesa handles driver/cache compatibility. Gameplay assets and existing user
settings are never copied. Omitting the option starts with a cold isolated cache.
`--dry-run` prints the renderer command and output dimensions without starting any
processes. The runner owns and terminates its Xvfb process; it does not use a shared
interactive display.
