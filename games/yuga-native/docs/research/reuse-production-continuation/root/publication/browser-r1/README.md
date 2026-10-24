# Actual public dashboard browser audit

On 2026-10-24 at 03:37:03–03:37:15 UTC, Chromium 154.0.8037.57 visited the actual [public production dashboard](https://occult-kranti.github.io/ANDOLAN/production/). The reusable `tools/build-observatory/audit_browser.py` used no mocked requests or substituted page data. Its configured runtime proxy was used with TLS verification enabled.

The run passed **72 checks**. The publication pins dashboard commit `4de88232291289c6beaa7d2b921207539bb04da8`; the saved snapshot separately observes clean source `2fbc88fa5385ee1c5c4f610ed32a664a5dcbdf66`. Actual browser snapshot responses all match SHA256 `105295d3e1c9c4df4b3580958c62f64066fcb8b7d5f9ecc826a687a744815877`.

- The page visibly identifies itself as **Saved snapshot — not live**, with the saved source and branch.
- Seven job rows, 15 asset cards and ten stages match the delivered data. The blocked filter shows only `w3`; clearing restores seven jobs.
- Keyboard Enter selects `camera-readability`, updates the correct inspector, sets `aria-pressed`, and preserves focus on that job button.
- All 16 displayed image elements decode: one lead image plus 15 gallery images. The lead repeats the first gallery asset.
- Actual asset and job-output links match their snapshot URL fields. All 18 distinct local media/viewer URLs return HTTP200. Report outputs containing only a path remain display text, consistent with the existing UI contract.
- Actual 1440, 390 and 320 CSS-pixel viewports have no document horizontal overflow. Original viewport and full-page screenshots are retained without edits.
- There are zero page JavaScript exceptions and zero failed requests. The expected `/api/status` HTTP404 responses cause the saved-snapshot fallback. Resource404 console messages are retained in the receipt; this does not claim a silent console.

Review `public-1440-top.png`, `public-390-top.png`, `public-320-top.png`, `blocked-desktop.png` and `keyboard-selected-desktop.png` first. The three `*-full.png` files retain the full original page at each width. This verifies dashboard delivery and interactions, not game execution, online matches, native art acceptance or physical GPU performance. The separate HTTP auditor checks the complete published-byte inventory.

The initial direct-transport attempt failed before any checks because Playwright did not inherit the required proxy. Its zero-check receipt remains unchanged in adjacent `browser-r1-direct-transport-failure/`. Configuring the inherited proxy resolved the verifier issue; no product code changed.

## Exact invocation

Run from the repository root with a **fresh** output path:

```sh
python3 games/yuga-native/tools/build-observatory/audit_browser.py \
  --base-url https://occult-kranti.github.io/ANDOLAN/production/ \
  --source 4de88232291289c6beaa7d2b921207539bb04da8 \
  --observed-source 2fbc88fa5385ee1c5c4f610ed32a664a5dcbdf66 \
  --snapshot-sha256 105295d3e1c9c4df4b3580958c62f64066fcb8b7d5f9ecc826a687a744815877 \
  --expected-jobs 7 --expected-assets 15 --expected-stages 10 \
  --blocked-job w3 --select-job camera-readability \
  --output /workspace/ANDOLAN/games/yuga-native/docs/research/reuse-production-continuation/root/publication/browser-r1
```

Auditor SHA256: `ccc2cd4f2fef76220d08e9e0b7f6cbcf21b89b7446327df328631f7ef5721be1`.

Receipt SHA256: `fbeae80cd5042313ab91cf62dbb8519fead0c704fa4bd76c718129abdf2fc6b6`.

All accepted browser source changes are limited to the new parameterized auditor. Historical browser receipts, native runtime, production UI and snapshot data are unchanged.
