# Four-view clay framing successor

Status: four-camera **projection preflight passed**, no actual clay images yet. This is an authoring scene, not runtime evidence or visual acceptance. W1 owns the four serialized renders. The fourth view is a rest-space cast-angle design view, not the animated public cast.

Root authorized camera-only corrections. From the original b2bcea87 scene, profile lens is reduced from55 to53.9mm and rear from55 to44mm. Transforms, target, the other two cameras, all hair/reference geometry, materials and lights are preserved. The fourth camera already meets the required margin and was not changed. Exact in-session before/after and fresh-load persistent-scene proofs are retained.

The original clay source/payload/receipt9656d5a1, initial failed profile preflight, and r2 rear failure remain unchanged. The r2 packet also retains verifier setup/serialization findings: an unused factory Material with zero users is omitted by Blender save, and session_uid is process-local. Root explicitly approved comparison of persistent scene data; these are recorded rather than hidden.

Native Blender4.3.2 preflight used CPU3/one thread and --python-exit-code1; exit0 in2.428s,0PNGs. All four evaluated-hair bounds and locked source head/crown/brows/ear-region bounds pass. Reference context selects source y>=1.65m, |x|<=.13m and |z|<=.20m from the locked head/face/gold/hair-brow objects; intentionally cropped shoulders and distant props are outside this head-framing contract.

The census emits one retained RNA warning when reading the installed Cycles denoiser enum. Logs are not described as clean; no actual render success is claimed. No mesh, rig, UV, GLB or canonical file changed.

Final editable scene and scripts are preserved in art/hero-finish/hair-sculpt-design/clay-framing-r3/. The scratch scene/helper are byte-identical to these durable copies. The local projection_contract.py dependency is required by the capture helper.

Prepared actual W1 command (not run by W2):

```sh
taskset -c 0,1 blender --background /workspace/scratch/yuga-hair-clay-r1/framing-r3/whole-hair-clay-framing-r3.blend --threads 2 --python-exit-code 1 --python /workspace/scratch/yuga-hair-clay-r1/framing-r3/capture_clay_framing_r3.py -- --output /workspace/scratch/yuga-hair-clay-r1/framing-r3/render-r1
```
