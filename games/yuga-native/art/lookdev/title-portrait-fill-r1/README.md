# Title portrait fill — original look-development candidate

Review-only. Canonical courtyard and all current screen/motion/art snapshots remain untouched.

The lead inspected the actual title200 original in D09/W1-current-screens-r1 and the original Rama/Hanuman/Sita concept. The title composition now reads, but Rama's face and upper costume remain dark against the much brighter architecture. The concept communicates large facial planes, blue fabric and warm gold through soft frontal modeling. Geometry, hair, garment volume and face performance remain separate deficits; changing light cannot finish those assets.

The existing title-only fill sits on the opposite X side from the title camera: light(-1.8,2.8,-2.0), camera(+3.4,1.7,-5.2), each relative to player. This candidate moves only that existing shadowless fill to(+1.8,2.8,-2.4), changes its blue tint to a restrained warm neutral, and raises energy1.8→2.2. Range5.5, sun/fill environment, exposure, fog, camera, all materials and meshes are untouched. Training already hides this exact light; no additional light, draw, texture, resource, control or gameplay writer is introduced.

Acceptance requires an actual matched title100/200 and training comparison with identical hero pose, camera, environment, current runtime and copied warm caches. Only the three declared title-light parameters may differ. Accept if face/eyes and gold/cobalt separation read more clearly without a bright forehead hotspot, washed-out fabric, orange skin cast or distracting bright floor patch. Training should remain byte-identical except any documented nondeterministic pixel rounding. Reject if the difference mostly lights architecture or makes the hero flatter. Night title is a separate view before default promotion.

Do not activate from source inspection or a headless pass. The intended change is local title presentation, not full-game lighting, improved physics or commercial graphics acceptance. The ordinary title remains an actual gameplay actor, not a generated image substituted for the runtime model.
