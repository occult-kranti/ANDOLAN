# Extracted Linux package window review

Root launched the engine and PCK extracted from the actual release candidate
Linux ZIP, on an owned X11 display with llvmpipe software Vulkan. XTest supplied
real window keyboard/mouse events; no game-state injection was used.

Observed title → Explore Confluence → world; movement changed the camera/atlas
position; N changed daylight to night; a longer firing press reduced arrows
from 12 to 11; Esc opened pause; keyboard focus selected coast travel; F1 opened the
atlas camera; pause → Return to courtyard returned to the original title.
The first short firing press did not show an ammo change; the later one-second
press did. This software-rendered session is not an input-latency benchmark.
All eight screenshots were inspected. The game log contains no ERROR/WARNING.

The review helper deliberately terminated its owned game/display during cleanup;
the recorded termination status is not a spontaneous game crash. Windows was
archive-validated, not executed. The exact package, engine and PCK hashes are
recorded in the manifests. Package source is 7f17c12394c1f52e150ce3dd3267b6ace062d899.
