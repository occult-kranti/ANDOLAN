# Resource audit, source push and dashboard publication

Task `YUGA-RESOURCE-AUDIT-2026-11-15`, product **YUGA native · Sanctum**. Session date: 15 November 2026, America/New_York. Starting source `e59a07a4786e9ad491cfef7a4e706dbd06063adc`. The existing `work/yuga-studio` checkout and normal `game/yuga-native-production` destination are retained.

## Deliverables and verification

- Detailed source research: **22 Blender/art resources and 26 engine/game/tool resources**, with source ledgers, catalog corrections and RC-01–RC-06 adoption packets. This is research completion; zero newly researched asset packs or tools were imported or installed.
- README, native README, start guide, tactical/full roadmaps, machine-readable backlog, research brief and observatory guide updated. Historical campaign counts remain unchanged.
- Inherited Rama studio/UI work independently checked: **706 passing checks**, ten tactical suites plus map integration, no engine errors/warnings. The [verification report](VERIFICATION.md) records exact commands and source hashes.
- Existing studio capture checked: all **148 image hashes** match; **135 film frames** decode. The independent reviewer inspected six originals; root additionally inspected the ready-studio original used on the dashboard. These checks are distinct from native input and hardware profiling.
- Observatory tests: `python3 -m unittest discover -s games/yuga-native/tools/build-observatory -p 'test_*.py' -v` — **34 passed**. [Retained log](verification/observatory-tests.log).
- Independent research review checked all ledgers, matrix revision consistency, local links and three sampled immutable licenses. Two scope/wording corrections were applied. No remaining research blocker was identified; this is not a full dependency or asset-archive audit.
- [Document/link checks](verification/document-checks.json) passed. The roadmap validator initially detected the deliberately edited roadmap's stale evidence hash; [that failure](verification/roadmap-r1.json) is retained. After recording the new document hash and clarifying its historical scope, [the validator passed](verification/roadmap-r2.json): 16 milestones, 70 tasks and 30 evidence files. No task completion status was changed.

The separately completing [studio3 packet](../../tactical/studio3/README.md) owns its package export and normal Linux input results. Its [input receipt](../../tactical/studio3/package-input-r1/review.json) records 19 events, nine original images, native Quit 0 and no engine diagnostics. This resource audit did not rerun that route and does not broaden it to a natural match, Windows execution, listening or hardware performance.

## Publication sequence

The concurrent studio owner committed and pushed `c22b292319097031391773caebae0ba434852fca` to `game/yuga-native-production`; a fresh `git ls-remote` observation confirmed that identity. It includes the inherited studio source, captures, package/input receipts and shared roadmap entries. This packet follows with reviewed research and remaining entry documents; the dashboard is exported from clean committed source and committed as a successor. Final research/dashboard identities and public delivery results are recorded below after they exist. A pushed source commit is not by itself a successful Pages deployment.

| Identity | Commit / receipt |
| --- | --- |
| Studio source and native evidence | `c22b292319097031391773caebae0ba434852fca` |
| Exact tactical log preservation | `97fe83cb7189084c0b07256aa94a17551e9c1acf` |
| Research, documentation and reviewed media | `ec9b1ac9da818a26f00118f9331fb4a29d348d01` |
| Saved dashboard publication | `0d630478038d796ebb9aa52b4baba230ab53aadb` |
| Normal push / remote-ref observation | [source-publication.json](verification/source-publication.json) |
| Pages workflow | [43798119082](https://github.com/occult-kranti/ANDOLAN/actions/runs/43798119082) |
| Native foundation workflow | [43798119121](https://github.com/occult-kranti/ANDOLAN/actions/runs/43798119121) |

The dashboard's observed source is clean `ec9b1ac9`; its publication commit is the separate successor `0d630478`. It contains eight jobs, seven artifact records and nine stage gates. No job is presented as running. The source and snapshot commits were pushed together normally and the remote branch matched `0d630478` on a fresh read. Final public verification is recorded after the workflow completes.

Producer state: `.local-swarm/observatory-resource-catalog-2026-11-15/`, run ID `sanctum-resource-catalog-2026-11-15`. Only the public projection is committed; raw producer state, user settings, shader caches, credentials and tool installations remain local. Existing approved dashboard media and the browser baseline are preserved. The new studio image is an unchanged original with [provenance](../../../tools/build-observatory/web/media/licenses/YUGA-STUDIO3-PREVIEW.md).

## Remaining work and next owner

Rama support-hand/ADS contact, face/hair, compact-window hero size, full-body tactical gameplay, bot art, human art/feel/listening, physical-GPU measurements, Windows execution and native Online Casual/Ranked remain open. Next: world artist owns RC-01, hero/motion artists own RC-02, integration lead owns shared imports, manifests and acceptance. Browser/mobile expansion remains deferred.
