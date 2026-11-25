# Animator measurements

Blender 4.3.2 measured all 48 actions from the four distributed GLBs. The 1,745 sampled poses include every 1/30 s, the exact ends and the quarter marks. The receipt records each model’s SHA-256, world-space position ranges, quarter positions, largest excursions and quaternion angle changes. The sample clock starts at each action’s own first key. Distances below use Blender metres with Z up. [Machine-readable results](evidence/rig-motion.json) · [Measurement code](tools/measure_rigs.py)

| Rig | Delivery checks |
| --- | --- |
| Hanuman · 11 actions | The gada head travels 1.957 m from its first position in portable `cast3`. In `tail_sweep` the tail tip reaches 0.554 m from its start and its attached frame turns 168.30°. The four tail deform joints and the separate tip, gada head and grip nodes are sampled individually. |
| Rama · 19 actions | The string joint moves 0.280 m from its first position in `volley_release`. The bow follows the **right** hand and the left hand draws. The concept board depicts the opposite convention. Use the released rig when placing gameplay sockets. |
| Shiva · 9 actions | The sole reaches Z = 0.371 m during `cast3`. Both soles return to Z = 0.0096 m at source F24. Through F42 the left contact patch slides at most 0.29 mm in XY and the right 0.06 mm. The right sole stays between Z = 0.0004 and 0.0141 m over the whole action. The central trishula tip moves 0.552 m from its opening position. |
| Krishna · 9 actions | In `cast2`, the first marker from the short end of the flute stays **1.48 mm** from the painted lip surface throughout F6–17. It previously missed the lip by 98.61 mm at F6–15. The left index pad stays 3.76 mm from its far-hand marker. The right index articulates 3.01–9.69 mm from its own marker across the phrase. In `cast3` the raised left wrist moves 0.764 m while the sling carries the flute. |

## Retargeting

1. Keep the actor origin fixed when sampling the rig. All 48 root joints stay in place to the receipt’s 0.01 mm reporting precision. The deity’s stance and hips still move. Let the gameplay capsule supply ground travel. The two locomotion cycles for each rig close on the sampled landmarks, with one residual at Rama’s idle seam of 0.20 mm and 0.026° at the head. Matching end positions alone does not certify tangent continuity.
2. Preserve the three bone-parented Hanuman nodes during import. Blender imports these non-deforming glTF nodes as empties. Losing them removes the measurable gada/tail endpoints even if the skin still animates.
3. Recheck the local string space on another Rama skeleton. The left wrist and string move independently. Retain the source timing markers for aim, release and recovery.
4. Measure ankle skin against the destination floor before adding a foot lock to Shiva. The audit uses all 1,771 foot/toe-weighted low vertices per side and a 60-vertex sole patch per foot. Terrain slopes, footwear and a different capsule height require their own calibration.
5. For Krishna, anchor the terminal blow hole to the lower lip, keep the left index over the far hole and let the right index articulate over the inner hole. The mesh uses eight dark surface markers on a 454 mm bamboo tube. The gap calculation compares actual vertices of the lip and marker. Each finger check uses a point 80% down the distal phalanx as an approximate pad. Port the head-relative IK, rigid bamboo and independent disc scale channel together. Krishna’s `cast1` reduces the hand disc to 3% scale. A visible projectile or healing effect needs a separate runtime event.
6. The pack contains editable rig motion and sample-space evidence. Input interruptions, root displacement from network correction, final map collisions and live effects require their runtime clocks. The hero scripts also describe proposed revisions, so read actual action durations from the receipt when building a timeline. [Source timing and staged poses](scripts/hanuman.md)

To reproduce from the repository root with Blender 4.3.2:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 blender -b -t 1 --python-exit-code 1 \
  -P games/yuga-native/art/four-hero-motion/tools/measure_rigs.py -- --check-contacts
```
