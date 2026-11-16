# Sanctum dashboard preparation

Task `YUGA-TACTICAL-CASUAL-13`; source base
`7162b5d0b666e4422b0bc73100e1fba947d3323f` plus working changes.
This packet qualifies the prepared dashboard, not public deployment.

The dashboard records six jobs, six artifacts and eight current tactical
gates, with no job left artificially running. Local Casual and its tested
source prototype remain separate from online/Ranked, final art, human feel,
physical-GPU performance and portable package acceptance. The older desktop
17/78 and 0/13 counts, and deferred mobile 0/108, are preserved explicitly.

`unit-tests.log` records 34 passing existing observatory, additive-publisher
and public-audit tests. `browser-check.json` records 21 passing checks in
actual local Chromium: snapshot labels/content, queue filters, keyboard job
selection, pause/refresh, all image decodes, stage states, no JavaScript page
errors and no page-level horizontal overflow at 1440×1080 and 390×844.
The two original browser screenshots were inspected. The provenance table
retains its intentional horizontal scroll region on mobile.

The retained `check-browser.cjs` is the exact bounded local check invoked as
`node /tmp/yuga-dashboard-sanctum-r2/check-browser.cjs`, using the existing
repository Playwright and an ordinary loopback static server on port 8779.
It does not mock responses or test native gameplay. The server served only
`games/yuga-native/tools/build-observatory/web/`. Public-source/byte checks
remain owned by root after committing, final clean-source export and deploy.

Four actual native R2 originals were also reviewed and copied unchanged:
menu, first-person approach, equipment shop and map overview. Their exact
hashes and upstream nineteen-shot source receipt are in the
[preview notice](../../web/media/licenses/YUGA-SANCTUM-PREVIEWS.md).
Initial R1 copies were moved into ignored producer state; their unchanged
original evidence remains under `docs/tactical/evidence/visual-r1/`.

Next owner: root/release. Finalize delivery results in producer state,
commit all reviewed source, export the clean source to `web/status.json`,
commit that saved export, push and verify the actual deployment.
