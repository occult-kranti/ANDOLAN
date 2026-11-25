# Mountain Pulse · tail recovery

The five-action native kit already gives Lanka Dahan a four-link whip and Maruti Udayana a moving vault. This pass gives the grounded Mountain Pulse impact its own recovery. The breastplate and mace stop on the impact beat. The tail carries the remaining impulse sideways, then returns through a smaller opposing swing. That lets the player read a heavy stop even when the remote ground effect falls outside the camera. [Native five-action authoring](../../../tools/hanuman-art/author_ability_motion.py) · [Ability timing and geometry](../../../assets/design/hanuman-ability-kit.json)

| Clip phase | Art and timing |
| --- | --- |
| 0–0.55 | Existing gather and release. |
| 0.78 | Existing remote impact. Head, hands, mace and support feet retain their contact poses. |
| 0.833–0.875 | Tail-root recoil leads. The four sampled additions peak in succession at 6.91°, 7.71°, 9.41° and 10.73°. The two middle joints peak on the same exported frame. The character’s tail tip moves 64.35 mm away from its original path at 0.83125. |
| 0.90–1.00 | A smaller opposing swing dissipates the impulse. The final pose matches the source. Returning to idle or interrupting the cast does not accumulate animation state. |

The native Godot clip and the portable GLB originally share a planted pose through normalized impact phase 0.78. The enhanced GLB layers its four local quaternions *after* that moment using the original sampler times. Each link gets a short positive sine-squared lobe and a smaller negative one, delayed progressively down the tail. The rig’s bind transforms convert the common vertical axis to each joint’s local coordinates. The change occupies 243 bytes in the canonical embedded buffer. Every other channel, joint, material, mesh and key time stays byte-identical during this step. [Motion layer](../tools/motion.py)

## Review and reproduce

The locked rear three-quarter camera shows a 33-pixel registration change at peak recoil. The teal cross on the finished image marks the original socket and the amber ring follows the new tip. [Rendered comparison](../media/images/tail-recoil.webp)

Compare from behind at a three-quarter angle. Scrub to 0.78, 0.835, 0.875 and 0.965 in that order. Each pose has recorded baseline and enhanced tip locations. An independent Blender import sampled 168 phases. The test checks the root, head, wrists, feet and both gada sockets, all motion through impact, endpoint reset and floor clearance of the distal tail centreline. Centreline and socket checks do not establish collision distance to every fur or clothing triangle. [Motion-only measurements](../evidence/tail-recoil.json) · [Combined groom and material measurements](../evidence/combined-tail-recoil.json) · [Comparison tool](../tools/check_motion.py)

Run from the repository root. The first command can also accept the output of the material and grooming stages. It recognizes the canonical motion tracks and rejects conflicting edits. Reapplying the same operation is idempotent. The restoration command reproduces the exact original quaternion bytes while preserving other contributors’ work.

```sh
art=games/yuga-native/art
python "$art/hanuman-hero-finish/tools/motion.py" \
  "$art/four-hero-motion/models/hanuman.glb" /tmp/hanuman-recoil.glb
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 blender -b -t 1 --python-exit-code 1 \
  -P "$art/hanuman-hero-finish/tools/check_motion.py" -- \
  "$art/four-hero-motion/models/hanuman.glb" /tmp/hanuman-recoil.glb /tmp/tail-recoil.json
python "$art/hanuman-hero-finish/tools/motion.py" \
  /tmp/hanuman-recoil.glb /tmp/hanuman-restored.glb --restore
cmp "$art/four-hero-motion/models/hanuman.glb" /tmp/hanuman-restored.glb
```
