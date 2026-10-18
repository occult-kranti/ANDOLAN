# W4 night/water presentation — initial source audit

Current-source baseline images are pending from W1. Older coastal/night originals were inspected only as historical context; they do not establish a defect in the current released build.

1. Inspect the current coast-day and swamp-night originals. Identify one actual distracting material/lighting behavior and retain the unmodified baseline.
2. Make one bounded presentation correction in the active water shader, or lighting only if the actual endpoint demonstrates that need. Reuse all existing geometry/resources. Preserve dry-route masks, shallow-film semantics and protected source pins. Do not add SSR/refraction, lights, geometry or an implied swimming route.
3. Review matched stills and a short fixed-clock sequence, plus the relevant existing lighting/native assertions. Reject a correction that merely moves shimmer to another distance, harms the bank/dry-route distinction, or changes protected geometry/collision/authority state.

The coast is a 26 × 260 m opaque plane outside native actor bounds at Y −0.15. Swamp film is 12 × 12 m at Y 0.012 over the same flat authority ground, with a dry crossing strip. Existing water uses dielectric shading and procedural sky reflections; there is no reflected-scene/SSR promise. Broad ripple components currently remain unfiltered while the finest component fades with its screen derivative. Whether this produces a visible problem is still a hypothesis pending current pixels.

No canonical runtime source changed. Exact initial pins and requested cameras are in initial-audit.json. W1 owns native preflight/rendering; new bulk output belongs under /workspace/scratch.
