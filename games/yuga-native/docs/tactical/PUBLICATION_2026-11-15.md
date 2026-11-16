# Sanctum source and dashboard publication — 15 November 2026

Task `YUGA-TACTICAL-CASUAL-13`, product YUGA native desktop. This publication checkpoint preserves the studio/Rama/Sangam work and the original first-person, local 5v5 Casual mode. First team to 13 wins; sides swap after round 12. Source checkpoint: `789dd1268bbac63208d0d49ec77635dff9ce7567` on `work/yuga-studio`, destined for `game/yuga-native-production`.

**Published and independently checked:** `d541dbcff7273fffa464660f7e46f674ed1600b5` is pushed to `game/yuga-native-production`. [Deployment succeeded](https://github.com/occult-kranti/ANDOLAN/actions/runs/43788072967); all 65 public HTTP observations, seven exact-byte/source checks and 21 actual public Chromium checks passed. Desktop/mobile originals were reviewed. [Publication receipt](evidence/publication-r1/publication-result.json).

The [production dashboard](https://occult-kranti.github.io/ANDOLAN/production/) is a dated saved snapshot. Deployment and public-byte verification are recorded in [the publication packet](evidence/publication-r1/README.md). Current development continues independently in the shared checkout; those later edits are preserved separately.

## Verified evidence

The exact committed source independently passed all **479 tactical checks** (53 rules, 21 bots, 335 map, 37 UI, 27 world, 6 complete-match checks), plus actual default startup, with no warnings/errors and no source drift. Its natural match again ended Moon 13–11 Sun over 24 rounds. All 36 migrated ground-detail colliders retained the same positions and dimensions. [Exact-commit qualification](evidence/publication-r1/commit-789dd/qualification.json).

- 717 scoped assertions passed on their recorded source revisions: tactical authority, bots, physical map, UI, world, a full match, retained classic flows, native contracts and packaging provenance. [Summary](evidence/publication-r1/verification-summary.json).
- The recorded full scene match ended Moon 13–11 Sun after 24 rounds, with eight plants, one defuse, 153 eliminations and one side swap. This is accelerated automated local play, not human-balance or hardware evidence.
- Nineteen actual Forward+ captures bind their source hashes. Root reviewed menu, A approach, ward/veil and shop; the dashboard reviewer also reviewed the overview. [Originals and receipt](evidence/publication-r1/visual-r2/review.json).
- The extracted Linux package passed ordinary XTest title → Casual → deploy → shop purchase → movement → pause → menu → native Quit 0, with no engine errors/warnings. Nine original screenshots include two explicitly intermediate frames. [Input review](evidence/publication-r1/ordinary-input-r2/REVIEW.json).
- Dashboard preparation passed 34 existing tests and 21 actual local Chromium checks at desktop/mobile sizes. [Dashboard evidence](../../tools/build-observatory/evidence/sanctum-publication-r1/README.md).

## Local native artifacts and source boundaries

[Linux ZIP](../../../../dist/yuga-sanctum-linux-x86_64.zip) and [Windows ZIP](../../../../dist/yuga-sanctum-windows-x86_64.zip) passed all archive CRC/payload checks: 42 ZIP members, 693 PCK entries each. These are local artifacts, not a replacement public executable release. Windows execution remains unrun. [Package manifests](evidence/publication-r1/package-r2/native-package-manifest.json).

Both packages bind the exact 704-file source set `195adc492c67cad6923331348187003b75881afcfac93ec747a2965479f0635b`. A comparison against the later source commit found **700 matching files and four newer files**: the tactical map JSON/map adapter move identical physical detail footprints into shared data; the tactical UI draws those footprints; the world updates objective/outcome hints. The retained [comparison](evidence/publication-r1/source-commit-match.json) deliberately fails exact equivalence. Package execution and screenshots retain their earlier source scope; the committed successor has its own focused qualification. No binary equivalence is claimed.

The first package export generated three missing Godot metadata sidecars and was correctly rejected by the source guard. Those files were included in a fresh successor snapshot. The failed export and accelerated world-only audio cleanup diagnostic remain retained; normal-clock world and complete-match runs were clean.

## Changed work and next owner

The source commit contains tactical runtime/scenes/assets/tests/notices, original studio and Sangam authoring sources, prior source-bound evidence, the new startup and legacy-screen CI routing, and dashboard data/media. Supplied commercial-reference videos, bulk extracted reference images/audio/transcripts and disposable user/cache state remain local; their analytical reports and receipts are retained. No local files were deleted.

A newer SURYA weapon-art pass is actively changing the shared checkout. It remains outside this publication's verified runtime. The native art/integration owner should finish and qualify that successor before promotion. Root/release owns publication receipts. Final art/contact/motion, human balance/listening, Windows execution, physical-GPU performance, online Casual and Ranked remain open. Historical campaign counts stay 17/78 scoped packets and 0/13 complete rounds; mobile remains deferred.

## Foundation CI correction

The [native package candidate workflow](https://github.com/occult-kranti/ANDOLAN/actions/runs/43788073047) succeeded for the publication source. The [first foundation run](https://github.com/occult-kranti/ANDOLAN/actions/runs/43788073049) passed tactical Casual, then rejected a stale Rama-motion source pin in the historical Arjuna authoring manifest. The validator was preserved. A deliberate intake requalification changed only the motion byte count/hash; all other 18 source pins and rig/library/socket fields stayed identical. The exact rejected command now passes, along with 345 existing authoring, native-template and motion checks. [Correction evidence](evidence/publication-r1/authoring-pin-refresh/). The successor foundation result is recorded separately; no runtime bytes changed in this correction.
