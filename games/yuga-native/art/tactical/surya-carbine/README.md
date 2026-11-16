# SURYA: original native hero firearm

Task YUGA-TACTICAL-CASUAL-13, native desktop Casual tactical FPS. This is the
focused replacement for the block-shaped procedural carbine visible in native
`docs/tactical/evidence/visual-r2/05-a-approach.png`. The dedicated generated
reference is `../surya-reference.png`; its prompt and unchanged hash are retained.

The editable Blender scene contains separate intentional components. Real
beveled geometry, ivory inlaid petals, an open swept stock and curved trigger
guard, exposed faceted solar cells and hexagonal lattice replace the old block
masses. Joining by animation parent creates two runtime meshes while preserving
the component source in the saved `.blend`. Materials use explicit metallic and
roughness values. Microscopic wear in the reference is not claimed as modeled.

Godot coordinates are metres, Y up and negative Z forward. `SURYA/Fixed` holds
the fixed body. `SURYA/Magazine` pivots at `(0,-.1,-.14)` for the existing reload;
`SURYA/Muzzle` is a source socket at `(0,.012,-.65)`. This asset has no arms,
skeleton, projectile simulation, collision or attack authority. Root owns
`tactical_weapon.gd` integration, FPS hand placement and motion review.

Reproduce in the serialized authoring lane:

```sh
blender4.3 --background --threads 8 --python-exit-code 1 --python tools/studio/build_surya_carbine.py
```

The generator refuses to replace an existing runtime GLB. Preserve a candidate
and its spec before a successor. `candidate-r1/` retains the editable first
candidate and generator; `export-r1.log` records the failed merge of stale
Blender object references. The successor collects both animation groups before
joining either, preserving the same authored geometry.

`export-receipt.json` and the runtime companion JSON record exact source,
reference, blend and GLB hashes, bounds, triangles, materials, Blender version
and command. The completed [native R4 review](native-review-r4.json) binds six
actual Forward+ originals: left, right, oblique muzzle, hip, aimed and reload
views. It accepts this original static art checkpoint, with the final aimed
pose reducing the butt pad's obstruction. The model remains frozen in
`sanctum-art-r1`.

The combat owner's [continuous native motion review](../../../docs/tactical/combat/motion-r1-review/review.json)
reviews all 180 consecutive originals across the 12-second scripted rehearsal;
17/17 behavior checks passed. Recoil/return, magazine reload and aimed-pose
transitions are covered. This is staged native motion evidence, not ordinary
desktop input, synchronized audio, natural match balance or hardware profiling.
Reload hand contact remains coarse, and dedicated utility hand casts are absent.

The asset has 79,804 triangles across two meshes and 14 material primitives,
above the initial approximate 30–70k target. Surfaces remain simpler than the
generated reference; no microscopic wear or AAA parity is claimed. See the
[map review](../../../docs/tactical/research/map-final-review-r2.json) for its
separate environment checkpoint and [ART_DELIVERY](../../../docs/tactical/ART_DELIVERY.md)
for final package identities and ordinary desktop input status.
