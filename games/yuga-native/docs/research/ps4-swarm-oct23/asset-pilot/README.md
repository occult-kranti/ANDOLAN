# Actual image → public GPU → GLB → Blender/Godot pilot

The original [concept and mesh](../../../../art/concepts/cloud-diya-pilot/README.md) are source candidates, outside runtime promotion. Image generation produced the RGBA input; one anonymous official TRELLIS.2 generation and one same-session export produced `candidate.glb`. [The service report](../access/README.md) owns parameters, source/model limitations, request identities, wall times and output hashes.

Blender 4.3.2 imported the exact 3,805,612-byte GLB. It has 68,890 imported vertices, 96,190 triangles, one material and two embedded images. The source inspection rejected nonfinite positions/degenerate bounds and confirmed UV/image presence, then rendered four actual 640 × 640 Cycles CPU views at 16 samples without denoising. [The inspection receipt](../../../../art/concepts/cloud-diya-pilot/inspection/inspection.json) binds those images; the reproducible Blender script is retained with the source.

Root reviewed all four images. The brass/cobalt palette, bowl/pedestal and feather-shaped finial survive the conversion. Fine relief and edges are softer than the input; the flame is opaque mesh geometry and needs separate effect authoring. This is useful source intake, not approval of a finished game prop. Real-world scale, material polish, topology/LODs, appropriate flame effects, collision and gameplay-distance review remain open.

An isolated Godot 4.6.3 project imported the original GLB successfully and instantiated one mesh with one surface. Both editor import and `--script check.gd` exited 0; the [execution receipt](godot-execution.json) retains commands, hashes and output excerpts. This verifies GLB import and mesh/surface instantiation; Godot material/texture rendering remains unchecked. No game scene, collision, animation, screen or physical-GPU performance was accepted. The main YUGA runtime was not modified.

To reproduce that isolated check in a fresh scratch directory, copy `project.godot`, `check.gd`, and the source `candidate.glb` renamed to `diya.glb`, then run:

```sh
godot --headless --path /absolute/fresh/prop-check --editor --import --quit
godot --headless --path /absolute/fresh/prop-check --script check.gd
```

Do not run the template in the main game directory or copy its generated `.godot/` cache into Git. The source concept, generated mesh, original failed transport, successful public GPU work and actual import/render reviews retain separate identities. No finished-game packet is closed by this pilot.
