# Optional original arrow fletching

Current RamaMotion makes a shaft and arrowhead, but no nocked-arrow fletching.
The carried quiver already has ivory feathers. This candidate tests whether a
small matching rear shape makes the held arrow easier to recognize without
changing the bow or either hand. Native pixel review is pending.

`build_fletching.py` is the editable source: three closed vanes, 34.8 mm long,
0.8 mm thick, under 12 mm in radius, positioned 50–84.8 mm along the existing
arrow's local +Y axis. The retained first profile failed hand clearance.
The generator emits 60 triangles and 180 vertices with
normals, tangents and UVs. One ArrayMesh is shared for the script's lifetime;
each configured hero adds one MeshInstance3D and borrows its own existing
finished ivory material. No textures, materials, bones, callbacks or arrow
visibility writers are added. The original shaft and tip stay intact.

From `games/yuga-native/`:

```sh
python3 art/hero-finish/s3-arrow-fletching/build_fletching.py --verify-only
```

The SHA-bound data file stays under the ignored authoring tree. This is
intentional: the helper is not default-active and this packet does not change
the export contract. A review overlay must copy both the helper and data file.
Do not infer packaged availability from a successful local FileAccess read.

For a source-frozen capture only, after the ordinary Player and finish owners
are ready, find the existing StandardMaterial3D named
`Ivory silk · Rama finish v2` among its active mesh materials. Then:

```gdscript
var helper = load("res://scripts/rama_arrow_fletching.gd").new()
player.visual.add_child(helper)
assert(helper.configure(player.rama_motion.nocked_arrow, existing_ivory))
```

`configure(arrow, ivory)` rejects the wrong arrow dimensions, skeleton, material
or another owner. Repeated configuration preserves node/geometry identity.
`helper.release()` hides and queues only its still-owned mesh; it removes its
arrow ownership marker and never edits the borrowed material. A mesh explicitly
reparented elsewhere is preserved. The helper also releases on its or the
arrow's tree exit. The shared geometry retains no material.

For matched review, use the same frozen source, camera, light, deterministic
draw time and input/pose for candidate off/on. Compare one normal rear gameplay
draw and one hand/bow close view, with the optional upper-hair helper off. Pin
the arrow frame, full posed skeleton, material and sample clocks on both sides.
Reject this candidate if it reads as a bright paddle, clips the hand/string,
shimmers or is too small to improve recognition. A projected bounding box alone
does not establish visibility. Released projectile art is outside this change.

The focused native test exports the actual imported hand vertices/influences
and declared direct-controller draw samples. `check_clearance.py` replays
them without normalizing quantized weights, then compares all candidate
triangles with the selected hand triangles. It also tests known separated and
crossing triangles and an edge crossing an actual hand face. This is bounded
component evidence, not a continuous native action, whole-body or pixel gate.

See `docs/evidence/desktop-finish/S3/W3.md` for exact commands, source identity,
failed fixture history and final numerical disposition.
