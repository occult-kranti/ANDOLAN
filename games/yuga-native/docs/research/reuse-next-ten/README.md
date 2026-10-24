# Reuse continuation — 24 October 2026

This packet continues source `f09953428767ddbdd7ede27fe53ca72bb3483d15` on
`game/yuga-native-production`. The user requested ten rounds of reuse-first
production. The [ten-stage execution guide](../ten-rounds-oct23/REUSE_FIRST_NEXT_TEN.md)
defines their dependencies; a scheduled stage is not a completed game round.

[Final source, publication and next-owner handoff](root/FINAL_HANDOFF.md) is the
shortest entry point after this continuation.

**Latest runtime repair:** `c97bb67e5947f2bd5257af48f1257a93d0a50469` restores
readable minimap bounds after the full CI run on `34971977` exposed a failure
outside the earlier narrow checks. The original 42 atlas assertions pass without
relaxation; the strengthened 41 adaptive checks and four new actual captures also
pass. See [repair evidence](root/ci-repair/README.md) and
[exact remote run status](root/remote-ci.json). The 19-step input journey below
belongs to the preceding source; the follow-up changes only map layout and has
its own four rendered comparisons.

The exact repaired source passed [all 39 foundation CI steps](https://github.com/occult-kranti/ANDOLAN/actions/runs/40048661708)
and [all 15 candidate-build steps](https://github.com/occult-kranti/ANDOLAN/actions/runs/40048661697).
That candidate run contains Linux/Windows test-build artifacts; packaging success
does not establish native Windows execution or full-match acceptance.

## Active ownership

| Worker | Reused foundation | Concrete output and boundary |
| --- | --- | --- |
| W1 independent review | Existing native tests, original captures and source contracts | Independent counterexamples and review in `W1/`; never repairs the candidate it reviews. |
| W2 screens | Existing HUD, theme, settings and world layout | Reproduce high-scale combat obstruction, repair adaptive layout, then actual input journey. |
| W3 artist | Existing Rama geometry, material assignments and editable hair | Non-destructive lower-hair sculpt, protected body and four matched clay views. Generated-source segmentation remains rejected. |
| W4 world | Existing CC0 courtyard, architecture, nature and sandstone maps | Extract complete useful structures, assemble a lane fixture, test routes/collision and capture ordinary views. |
| W5 motion | Existing Rama rig, motion controller and 23 external clips | Repair reproduced warm-draw bowstring discontinuity; test contact, timing, interruption and reset. |
| W6 authority | Existing protocol-2 server, native client and physics fixtures | Isolated server-owned 3D movement experiment. Existing browser authority remains planar. |

Root owns source integration, CI, dashboard, publication and this index. An initial
bounded W4 source audit used the seventh slot, finished, and released it to W2.
Six worker conversations share four CPU cores of quota. Actual renders use one
serialized lane and at most two software workers; this is not a physical-GPU
performance run or an autonomous background swarm.

## Ten-stage execution record

1. Freeze sources and reproduce defects — current native sources and original
   screenshots inspected; source identities accompany worker packets.
2. Build isolated candidates by adapting existing resources — hero, map, motion,
   screens and authority work in parallel.
3. Review actual art, collision, transitions and failure cases — accept or reject
   the exact output, without replacing a visual decision with a structural test.
4. Integrate accepted changes — preserve canonical asset identity and scope each
   runtime edit; rejected art remains outside gameplay.
5. Qualify continuous first-hero and lane play — motion studies alone cannot close
   the complete hero gate.
6. Expand distinct heroes and districts — depends on accepted source art; the
   existing Arjuna template still looks like Rama.
7. Rehearse three lanes and native online lifecycle — depends on rendered native
   authority and complete match rules.
8. Review the competitive slice — requires independently accepted Rama, Hanuman,
   Sita and an uninterrupted 3v3 match; remains separate from a transport test.
9. Measure hardware and packages — physical-GPU timing and exact released package
   behavior require actual execution on that hardware/package.
10. Publish the verified checkpoint and repair queue — publication of a partial
    checkpoint does not close stages 5–9.

The final worker and root receipts in this directory record execution results.
Do not infer that all ten stages passed from this list. The full-game campaign
continues to use its existing acceptance ledger; Android remains deferred.

## Implemented and reviewed checkpoint

- **Motion:** the production warm-draw bowstring now starts from its outgoing
  pose, removing the reproduced roughly 19 cm mesh jump. The 113-check matched
  comparison, existing motion regressions and actual 1.2-second comparison video
  support this narrow repair. See [W5](W5/README.md).
- **World:** one carved Lanka gateway reuses 241 complete pieces of the existing
  original CC0 courtyard. Its cached native scene has 17,862 triangles, 11
  surfaces and one structural collider. Ten source-derived ground footprints
  feed the existing army API through a private manifest copy, fixing attacks
  through the piers while keeping the opening clear. See [W4](W4/README.md).
- **Screens:** the existing HUD uses less combat space at enlarged UI scale,
  retaining essential fonts and cues. Forty-one layout checks and 22 actual
  originals cover the changes. The smallest 200% stress viewport remains dense;
  this is bounded layout improvement, not final all-screen art acceptance.
  See [W2](W2/README.md).
- **Hero art:** R1 is an isolated editable sculpt/GLB study with protected
  body/rig data and 23-clip compatibility. R2 has eight actual clay views but
  is **rejected for runtime use** because of broad lobes and large gaps. The
  canonical Rama mesh/LODs remain unchanged. See [W3](W3/README.md).
- **Online foundation:** the existing server transport and native client now
  have an isolated actual-3D authority experiment, with vertical collision,
  malformed input, reconnect and persistent slot controls. It is not integrated
  production multiplayer or a rendered complete match. See [W6](W6/README.md).

[W1](W1/README.md) independently reviewed the originals and counterexamples.
The mandatory new CI sequence passed locally; its exact source-change boundary
and affected replay are in [the local receipt](root/continuation-ci-local.json).
Remote CI, exported-pack behavior and public publication need their own receipts;
earlier releases do not qualify these changed bytes.

The final combined source passed a **19-step actual keyboard/mouse journey**:
launch, loading, world/map/pause, return, training, settings/controls and quit.
There are 23 original frames and a separate independent review. Both platform
resource packs exported; the actual Linux `--main-pack` probe passed **13 checks**
for exported gateway resources, collision, cache and army cover. These checks
do not establish Windows execution, hardware performance or a new playable
release. [Root verification](root/verification.json) records scope and failures;
[package evidence](root/native-export/gateway-package-launch-r2.json) binds the
actual command and resource-pack hash.

The next six-owner assignments and ten dependency-ordered stages are in
[NEXT_ROUND_ASSIGNMENTS.md](NEXT_ROUND_ASSIGNMENTS.md). The full-game ledger stays
at **17/78 accepted packets and 0/13 complete production rounds**; Android is
**0/108 and deferred**. These counts are acceptance gates, not a time estimate.

## Additional reuse requested during publication

The [Source 2 / Overwatch tooling packet](reuse-advisor-world/README.md) retains
19 licensed primary files and adapts Source 2 Viewer's event-window algorithm
into an executable offline inspector. It passed 24 actual Godot-fixture checks
and 67 inspection checks on existing Rama ability events. Overwatch's timed
effect/attachment schema is a reference for the next diagnostic sidecar; its
parser and commercial assets are not imported.

The [systems packet](reuse-advisor-systems/README.md) inspects netfox, Godot motion
matching and authentic Valorant endpoint documentation at exact MIT source pins.
Six executed component checks expose both valid typed interpolation and concrete
counterexamples. These tools do not provide Valorant's gameplay source or art.
Whole-framework replacement is rejected; proposed narrow adapters retain the
existing ownership, motion-contact and discontinuity checks.

The [hero reuse packet](reuse-advisor-hero/README.md) retrieves the verified CC0
MPFB hair-authoring asset and fits its existing guide curves to Rama. Six actual
textured images record the initial rejected thin/gold appearance and a denser
black refinement using existing density/material controls. The final 14,744-curve
study is an **editable source candidate**, with exact donor and master archives;
it is not a new canonical game model. The next work reuses card/texture baking,
then qualifies binding, contact, animation and LODs before native promotion.

## Live observer and public snapshot

The local observer for this work uses the ignored state directory
`.local-swarm/observatory-reuse-next-ten` and port `8768`. It records actual local
capacity and explicit job evidence. Start it with:

```sh
python3 games/yuga-native/tools/build-observatory/observatory.py serve \
  --workspace /workspace/ANDOLAN \
  --state-dir /workspace/ANDOLAN/.local-swarm/observatory-reuse-next-ten --port 8768
```

The public [production dashboard](https://occult-kranti.github.io/ANDOLAN/production/)
is a dated export, not live cloud telemetry. No model inference or remote GPU
utilization is implied by a worker's source-editing activity.
