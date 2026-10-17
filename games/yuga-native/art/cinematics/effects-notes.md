# Confluence duel: deterministic effects candidate

The effects in `scripts/duel_effects.gd` and `scripts/duel_energy.gdshader` are original Godot geometry and shader work for the 24-second, two-fighter film. They visualize the choreography in `assets/cinematics/confluence-duel.json`; they do not evaluate authoritative collisions, apply multiplayer damage, or establish a complete hero kit.

## Director contract

Create the script as a `Node3D` under an identity world root, then call `configure(manifest, socket_at_time=Callable())`. It validates the entire cue list before building a fixed mesh pool and returns `false` with diagnostics on rejection. Call `sample(time, manifest={})` after actor transforms. `sample_time(time, reduced_effects=false)` is a convenience alias which also sets both accessibility toggles. For independent controls use `set_accessibility(reduced_flash, reduced_motion)` followed by `sample(time)`.

An optional socket resolver receives `(actor_id, socket, absolute_time)` and returns a finite world `Vector3`. Recognized requests are `bow` for projectile starts and `chest` for missing targets or centers. Solar arrows prefer the director's **cached release-time bow position**, even when an authored `from_position` is present. A missing or non-finite socket falls back to that authored position. Other cue coordinates remain explicit; in particular, the opening block impact stays at Ravana's authored position rather than following its feedback target ID. Cached lookups must not resample or move the current actor pose. Actual agreement with rendered bow and guard poses requires frame review.

Cue intervals are half-open: `start <= time < start + duration`. At exactly 4.75 seconds, the first arrow disappears and its block impact begins. Using absolute end times avoids the subtraction-rounding discrepancy discovered by the boundary test. Rewind resets every inactive mesh transform and opacity, making hidden state deterministic as well as visible state. Material progress is explicitly supplied; the shader has no `TIME` dependency. There are no tweens, physics particles, random generators, timers, frame-integrated trails or accumulating scene nodes.

`diagnostics()` exposes configuration errors, sampled time, cue and mesh counts, active cue IDs and the visible state/12 transform components/opacity/progress of every part. Its state can be compared exactly across reversed and nonmonotonic seek orders. Reconfiguring replaces only this effect root's children.

## Authored effects

| Cue | Anticipation and visible action | Decay and readability |
| --- | --- | --- |
| Solar draw | A small charge at the authored bow anchor and a quiet six-petal ground ring. | Both fade before the arrow cue; the symbol is an original graphic, not a claimed reconstruction of a sacred diagram. |
| Solar arrow | Pointed head, short gold shaft/trail and restrained corona travel from the declared release point to the receipt point. | A half-open handoff prevents a lingering arrow after impact. |
| Ravana guard | Violet circular shield with a restrained faceted grid and separate outer ring, oriented toward the incoming projectile. | It is already visible before the opening arrow and fades when the guard window closes. |
| Wave warning | A ground corridor with borders and static directional marks identifies the locked attack line before release. | The corridor is not retargeted toward Rama's later dodge position. |
| Spectral fan | Five violet bolts spread across the declared corridor width. | Every bolt is sampled from its own fixed endpoint; no random projectile creation. |
| Evade | Three short height-separated gold ribbons and three restrained ground puffs mark the authored sidestep. | Reduced motion lowers ribbon prominence; the character motion and warning remain available. |
| Block/hit | An expanding facing ring, ground ring, six bounded sparks and three low-opacity puffs mark the receipt. | Decay is monotonic, with no full-screen flash, camera shake or prolonged opaque explosion. |

The shader is additive and depth-tested against opaque scenery. Its masks use UVs for circles, warning marks, shield pattern and ribbons. This introduces transparent overdraw and is not a free performance feature. It does not write scene depth or add colliders. The small dust puffs are stylized energy-lit geometry, not simulated volumetric dust. Actual capture determines whether their color and opacity are useful.

## Budgets and accessibility

The current ten cues allocate **57 meshes once**, under hard caps of 32 cues and 128 meshes. Guard and telegraph cues use two meshes each; a solar arrow uses three; the fan uses fifteen; an impact uses eleven; an evade uses six. Shapes are low-segment spheres, cylinders/cones and planes. Sampling changes transforms and shader parameters without allocation of new mesh instances.

Reduced flash multiplies visible opacity by 0.65. Reduced motion shortens projectile tails, reduces spark/ring travel and reduces dash ribbon opacity. Critical warning and projectile cues remain present. The shader uses a single slow, four-percent breathing term within each cue, not periodic flashes. These bounded choices are accessibility implementation, not a clinical certification or a GPU benchmark.

Invalid cue IDs/types/times, duplicate IDs, missing required endpoints, malformed or non-finite positions, excessive radii, out-of-film events and resource-cap excess are rejected before mesh allocation. World coordinates are bounded to ±10,000 metres. Invalid seek times fall back to zero; finite seek times clamp to the film duration.

## Evidence and next review

Run the committed unit suite with:

```sh
godot --headless --path games/yuga-native --script res://tests/duel_effects_cases.gd -- --report=/tmp/duel-effects-cases.json
```

The current result is **32 passing checks**, including 241 nonmonotonic samples, exact reverse-order state, unchanged node IDs across seeks, the arrow/impact boundary, completed decay at 24 seconds, preservation of critical reduced-effects cues, repeated configuration and thirteen invalid-input cases. Three socket tests verify that a cached bow overrides the fallback, lookup uses release time, and a non-finite cache result falls back safely. The pinned report is `tests/evidence/combat-film/duel-effects-cases.json`, with effect, shader, manifest and test hashes. The failed boundary case preceded the absolute-end comparison fix; no failed result is represented as a successful render.

These are headless resource and state checks. The integration owner separately captures real Vulkan frames to compile the shader and inspect shot direction, shield orientation, hand/bow contact, warning visibility, actor silhouettes and reduced-flash appearance. No actual-render quality or frame-rate claim follows from the unit suite. Code is frozen for that capture; changes after review require a fresh source manifest and report.

Engineering reference: the project previously inspected the official [Godot 4.6 spatial shader reference](https://github.com/godotengine/godot-docs/blob/b10b7ed373c2d15555186914b82e167169b5b87b/tutorials/shaders/shader_reference/spatial_shader.rst). This implementation uses its documented UV, normal/view, alpha and render-mode interfaces. No commercial game assets or third-party shader code were copied.

## Film lighting revision from R1 captures

Actual frames 0, 3, 4, 6, 8 and 9 in `build/film-scene-r1` showed a flat brown sky hemisphere, dark actor-facing surfaces and stippled flooring. They also established that the violet warning and shield were visible around the intended corridor and defender. `scripts/film_lighting.gd` is a film-only candidate with a cool sky horizon, warm directional key, cool unshadowed fill and two bounded unshadowed soft lights. It retains low-density ordinary fog rather than obscuring the floor, disables SSAO, and limits the shadowed directional source to two splits/48 metres. Shared courtyard lighting and GLB bytes are unchanged.

Inspection of `art/build_courtyard.py` and the actual GLB found 550 separate slabs with top Y=0, a mortar foundation at Y=-0.002000004, and quiet-stone inlay bounds Y=[-0.003794228,+0.011794228]. The inlay therefore intersects the floor; the film instance alone is lifted 8 mm, idempotently. The mortar remains unchanged for the next capture. Floor instances stop casting shadows onto themselves but still receive actor and architecture shadows. This is a controlled candidate, not proof that all stippling was shadow noise: material aliasing, near-surface depth and shadow contact must be compared in the next real render. The film light helper does not change actor poses, collision or shared materials.

The completed R2 frames showed clearer color separation and framing, but frame 9 still had coarse holes/grain across the actor's cast shadow. Thin floor joins and inlays also remained dotted. The final bounded lighting candidate changes only the sun's angular distance from 0.65 to 0.0, disabling PCSS contact-hardening sampling while preserving the shadow distance, bias, floor geometry, materials and fog. The official [Godot 4.6 lights and shadows reference](https://github.com/godotengine/godot-docs/blob/b10b7ed373c2d15555186914b82e167169b5b87b/tutorials/3d/lights_and_shadows.rst) documents both this switch and visible grain in soft-shadow filtering. This identifies and disables a plausible source of shadow grain; a subsequent matched real-render comparison must establish the actual improvement. Remaining floor-line aliasing is a separate unresolved visual issue, not claimed fixed by the switch.

Source provenance: official `godotengine/godot-docs` commit `b10b7ed373c2d15555186914b82e167169b5b87b`, file SHA-256 `0250d2db8150223ef284d6e8ba049bc8f154358ea874f94813975a80857ba392`, retrieved from GitHub and matched to the pinned revision during this session. Its PCSS recommendations state:

> “Provide a setting for users to disable PCSS shadows. On directional lights, this can be done by setting the DirectionalLight3D's `light_angular_distance` property to `0.0` in a script.”

The shadow-blur discussion also states: “The downside of increasing shadow blur is that it will make the grainy pattern used for filtering more noticeable.” These statements support the isolated implementation experiment; they do not establish its result before the capture.
