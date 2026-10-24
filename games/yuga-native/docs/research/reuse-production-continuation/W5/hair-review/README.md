# Independent mechanical eligibility of MPFB hair cards

**32/32 checks pass for the isolated card candidate after W3 fixed a real placement bug.** This accepts numerical binding/placement eligibility only. The native stills were visually rejected as a thin/noisy curtain, and the planned 120-frame motion capture was stopped before execution. There is no new rendered-motion, contact, art-quality or production-hero acceptance.

The W5 reviewer did not author the card asset, binding adapter or its correction. The independent probe reads the actual imported vertex, weight and skin arrays itself; it does not call the author's `Adapter.points` or `Contacts.skin` helper. W3 owns the source, mask proof, material experiments and art decisions.

## Exact reviewed inputs

| Input | SHA-256 |
| --- | --- |
| R3 near card GLB, 2,304 vertices | `a7add6b73b690f9fd8e5c88d7d0eaa36e248ad3368a1bdbc2a06d5d73bd038d9` |
| Exact original-body GLB with the nine-component nape index mask | `491567c6bc0fa7e530e7668290961a177f1f681f441a290b980720a80582c8c4` |
| Corrected W3 attachment adapter | `e9b128b944632c81ada403eefb49d5618fd61f0e670dec9a13643596fb7bc1af` |
| Existing production motion | `6261a692308e84863dbac4ff049fb7855cc8c5ebf70d8ec844b1dfb2225e53c1` |
| Independent probe | `ceabff058e06eb622b73b87d980a54d3d50f06dc6111db3707a4ebb23e54aa7a` |

These are the standalone cards. A later mass underlayer is a new asset candidate requiring its own source and skin/contact checks; it inherits no automatic acceptance from this packet.

## Findings and correction

All 2,304 vertices have unit total weight on the native `head` bone. There is one canonical 164-bone animation owner. The imported carrier skeleton is discarded; the actual skin uses inverse binds derived from canonical native rest transforms.

The first complete independent run passed **31/32** controls. Attaching at the origin and subsequently moving the hero worked. Attaching to an already translated/yawed hero left the hair in the source world position, producing **9.1397657 m** maximum correspondence error for translation `(7,3,-5)` and yaw `0.6`. W3 corrected its adapter by aligning the temporary hair carrier with the model before rebuilding inverse binds and reparenting. The **unchanged** reviewer then passed **32/32**, with zero measured error for both placement orders. The failed receipt and exact prior adapter bytes are retained; the successful run verifies source hashes before and after execution.

For each of the 23 external production clips, the reviewer samples normalized times `0, .25, .5, .75, 1`. All 115 actual skin samples are finite and follow the observed head transform with maximum numerical residual **3.58945 × 10⁻⁷ m**. The `1e-5 m` check is an algebra/float consistency budget, **not a contact-clearance or artistic threshold**. The author's original helper returns rig-local positions; the independent helper explicitly includes the rig's world transform.

The scratch negative changes only the 2,304 nonzero-weight `JOINTS_0` bytes from existing joint `head` (104) to existing joint `spine05` (41). It remains a valid imported mesh with valid bone references, but the independent head-binding eligibility check rejects it. This is a meaningful wrong-owner negative, not a malformed file that fails to import. The candidate and canonical game assets are not edited. The negative's SHA-256 is `f2bb14ddbad8ce2578db7e85a384b225667322345bf19de1c07d2f23361e16f0`; [the small reproducer](make_wrong_head.py) reconstructs its exact bytes from the pinned candidate.

## Motion coverage and open contact work

The W3 `native-r4.json` probe contains 115 clip samples and a separate 300-step, 60 Hz numerical sequence. The latter has 188 distinct recorded bounds and action counts: neutral 113, Kodanda 58, Piercing Dawn 39, death 30, respawn 60. Its code also changes velocity and aim while advancing the existing motion controller. These are staged numerical poses, with running in place; they are neither all clips continuously rendered nor ordinary player input. The 23 names are retained in [coverage](coverage.json).

This skin is rigidly attached to the head. It contains **no independent hair motion, cloth physics, collision response or secondary strand animation**. Finite bounds and correct head following do not establish that lower hair edges avoid the neck/collar during aiming, turning, death or respawn. No hair/body intersection oracle, swept surface contact measurement or accepted near/mid/far LOD comparison was executed. The mask's protected topology is W3's separately source-pinned proof; this reviewer did not re-author or independently reproduce that Blender mapping.

The proposed underlayer may restore volume using existing audited nape geometry, but it needs its own actual boundary/contact review. Keep it within the same original coordinate/rest-binding contract and preserve the body/crown/UV mask proof. Do not infer good contact from the present finite-skin checks or keep its lower fringe automatically safe merely because it shares the head bone.

## Reproduce

After recovering W3's exact masked body and R3 hair paths, create a fresh scratch negative:

```sh
python3 games/yuga-native/docs/research/reuse-production-continuation/W5/hair-review/make_wrong_head.py \
  --source /absolute/path/mpfb-nape-cards-near.glb \
  --output /tmp/rama-wrong-head-fresh.glb

godot --headless --path games/yuga-native \
  --script res://tools/reuse-event-sync/hair_review.gd -- \
  --base=/absolute/path/rama-nape-masked.glb \
  --hair=/absolute/path/mpfb-nape-cards-near.glb \
  --wrong-hair=/tmp/rama-wrong-head-fresh.glb \
  --output=/tmp/rama-independent-hair-fresh.json
```

Executed with a 90-second process bound and one allowed CPU. No raster job was launched. The initial R1 reviewer had an invalid `PackedVector3Array.all()` call and was terminated; the ordinary loop correction preceded the complete failed R2 and successful R3 runs. Those later two runs use identical reviewer source bytes and differ only in the author's adapter correction. Root owns integration and visual acceptance; no canonical promotion is requested by this packet.
