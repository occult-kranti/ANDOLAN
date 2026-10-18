# R3-04 five-ability source clearance

Source commit `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. **Cloth clearance
fails the source replay gate.** All 15 archived runtime poses were replayed on
actual groom-r6 near geometry: windup, release/recovery .05 s and recoil .15 s for
Kodanda, Piercing Dawn, Measured Step, Guardian Circle and Dawn Volley.
The replay is not newly executed gameplay or a render.

Three independent analytic sanity cases pass. Complete-triangle separation uses
AABB distances refined by normalized triangle separating axes; a radius-partitioned
sphere search excludes only pairs provably beyond the current bound. Positive
reported gaps are conservative lower bounds. Values .080 m may be capped search
bounds, not exact nearest distances. No nearest-vertex proxy approves clearance.
All 15 fullbody/weapon source projections pass the 24 px border at the supplied
common camera. The bounds do not yet include current shader offsets.

Hair-to-bow minimum is 39.702 mm in Piercing windup. Every sampled hair gap clears
the full 18 mm hair displacement bound plus 1 mm. All bow vertex motion masks are
zero. Cloth-to-bow lower bounds are 30.855–56.202 mm for the bow attacks, which
cannot prove separation under arbitrary allowed 75 mm cloth displacement.

Measured Step and Guardian Circle each have zero bounds in all three phases.
`verify_witnesses.py` independently finds strict interior segment/triangle
crossings in **all six** stored witness pairs. Measured Step intersects cobalt
cloth near source-pose y=.55 m; Guardian intersects ivory near y=.70–.76 m.
Coordinates, triangle identities, barycentric coordinates and exact inputs are
retained in `intersection-witnesses.json` and `action-clearance.json`.
The seven checked bow/cloth primitive arrays are exact to R2 r6: these source
crossings predate the new groom and roughness candidate. They are not classified
as candidate regressions. Actual shader displacement and visible penetration
remain separate runtime and pixel questions.

Two actual original R2 corrected-action PNGs were opened with `view_image`:
Kodanda and Measured Step. Both show only head/upper body; the thigh-level contact
region is outside them. No cloth clearance conclusion can be drawn from those
face crops. Their hashes are in `reviewed-originals.json`.

`ability-fixtures.json` supplies exact source/authority phase contracts, one
common fullbody camera and warning/weapon review rules. It keeps the eight-still,
one-continuous-take budget: source-pose checks do not create 15 new capture tasks.
The continuous take should use actual cast events for all five abilities and
retain uncut phase frames, motion states, shader uniforms and fullbody bounds.

Executed successfully:

```sh
OPENBLAS_NUM_THREADS=1 python3 games/yuga-native/docs/evidence/visual-rounds/round3/role04/check_action_clearance.py
python3 games/yuga-native/docs/evidence/visual-rounds/round3/role04/verify_witnesses.py
```

An initial global-radius broadphase was interrupted with exit130 after no pose
completed; its source and reason are retained. Partitioning by actual bow triangle
radius removed excessive candidate pairs without dropping geometry. The completed
report has `source_projection_passed=true`, `clearance_gate_passed=false`.

No imports, renders, clocks, controller, geometry or canonical assets changed.
Next owner: 06 for actual imported offset-aware checks and original fullbody
pixels; root/motion owner for a separately scoped correction if runtime confirms
the source contacts. Gold hem, integrated quiver, runtime string/arrow sweeps and
unsampled intermediate frames remain unverified by this bounded calculation.
