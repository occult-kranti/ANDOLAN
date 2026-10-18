# S1 lead — title camera framing

The title camera now shows Rama at roughly two thirds of the supported window height. It uses the actual actor and idle motion. FOV changes from34 to27degrees, with horizontal aim compensated from1.65m to1.25m; the gameplay camera is unchanged. The historical G1 title original showed the actor occupying about53% of a960×540 framebuffer.

Executed `taskset -c 2 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 godot --headless --path games/yuga-native --script res://tests/ui_s1_portrait_cases.gd -- --report=/tmp/yuga-s1-portrait-r1/report.json`. All18 actual-scene projection/camera-ownership checks passed, exit0, clean log. Tested960×540,960×600,1280×720,1920×1080,2560×1440: crown/sole margins, idle side envelope, face/control/scrim clearance and training/title camera handoff. [Exact sources and results](portrait-report.json).

Actual new title pixels, equipment silhouette and motion extrema still require W1 review. This is geometry/layout qualification, not a rendered quality verdict.
