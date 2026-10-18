# R4-10 — independent contact witnesses and rejected motion review

**Strict contact witnesses confirmed; motion acceptance remains open.** A scalar implementation independent of R4-12’s NumPy skinning reproduces24 side-minimum measurements across12 original imported-pose samples, then four adversarial witness checks. All28 checks pass. No controller, geometry, threshold, clock or runtime source was changed, and no new import or render was executed.

The input is R4-12’s promoted R7 actual imported-array/native-callback tape. The scalar implementation explicitly applies each named inverse bind, each final bone transform, weighted summation, actual secondary displacement and live rig transform. It does not call the vectorized evaluator or reconstruct a GLB. Exact input/runtime pins are in `test-receipt.json`; shared HEAD changes do not substitute for those identities.

| Independent witness | Result |
| --- | --- |
| Grounded left sole, sample91 |−24.744474 mm, original imported skin vertex `2:40856`;3,403 selected vertices below−5 mm |
| Fixed planted left vertex166→170 |3.055982 mm drift; original plant target remains exactly fixed |
| Maximum selected sole finite world step21→22 |183.521288 mm, reproduced from identical imported vertex IDs |
| Maximum rig-space joint-origin step |125.488853 mm, `toe1-1.R`, sample109, one60 Hz interval |
| Maximum world-space joint-origin step |198.151649 mm, `finger2-2.R`, sample98; local step only0.538640 mm |

The last two measurements demonstrate why world displacement alone cannot diagnose a pose discontinuity: the entire rig moves/turns. These finite differences are observed values, not acceptance thresholds or a C0/C1 proof. The strict below-plane witness is stronger: actual capsule-floor coincidence and a normalUP contact coexist with an unlocked skinned sole more than20 mm below that plane. Initial retained50.57 mm plant clearance and the first post-placement stale slide contact remain separately labeled in R4-12; this review does not erase those cases or relabel them ordinary gait.

The meaningful failed motion proposals remain intact. Executing the independent R4-05 archive verifier validates44 archived members and five staged source files. Its r3a/r4 controllers remain rejected: ordinary120 Hz sampled skin floor worsens from−31.584 to−47.123 mm, start/stop steps worsen, and constrained release C0/C1 errors remain despite passing ordinary39-check motion suites. This verification authenticates those historical reports; it is not a new execution of every rejected prototype on R7.

`check_contact_witnesses.py` and `contact-witnesses.json` contain the separate implementation, exact witnesses, all actual input control events and maximum joint steps. Run the command recorded in `test-receipt.json` from repository root. The R4-12 raw tape is shared read-only evidence, not duplicated or rewritten.

No actual R4 motion frame sequence was available to this role at sealing. Adversarial reversal, action release/cancel, non-flat ground, LOD switches and full normal-speed motion remain for the one uninterrupted role06 tape and later independent image review. No additional motion correction is proposed. Root and role06 should preserve the strict floor witnesses, original anchors and coherent callback sampling in that review.
