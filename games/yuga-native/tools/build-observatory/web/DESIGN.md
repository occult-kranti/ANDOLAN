# YUGA production observatory

This is a read-only production tool inside the existing YUGA identity. It reports actual jobs, retained outputs and next acceptance gates. It does not change the game UI, production acceptance or roadmap counts.

The working scene is a long desktop review session, with a narrow-screen check available away from the workstation. The design uses a charcoal-green ground, warm ivory text, restrained worked-gold links and selected states, the existing Noto Sans body face and Noto Serif identity/headings. Tokens are defined once in `styles.css`: canvas `#171c19`, surface `#202721`, text `#f1ecdf`, muted `#bac2b7`, accent `#e2bf80`, line `#485346`, radius `4px`. Existing font attribution is retained in the root-owned media licenses.

The monitoring task determines composition: connection and data age first, actual asset and run/source identity next, then a dense work queue with an inline job inspector. Artifacts, explicit next gates and reuse provenance follow. The work list is the operating surface; small status marks complement readable text, and no invented percent-complete graphic is used.

Controls use native buttons/selects/links, visible focus, 44px primary hit targets and stable selection. Narrow layouts recompose rather than shrink. Filtered selection follows visible work; no matching jobs clears the inspector. There is no modal or decorative persistent animation. Reduced motion disables smooth scrolling.

Live worker observation, saved snapshot, stale data and paused updates have distinct labels. Running jobs in a saved/stale/paused observation are labeled **Recorded running**. Machine availability describes the observed host, not a public GPU service or an unconnected personal device. A failed refresh preserves the last observation and explains that current activity is unconfirmed.

Observation data is inserted with DOM text APIs. Links allow safe HTTPS or same-origin HTTP(S), without credentials; unsupported values stay inert text. Malformed/null job/context records are rejected before rendering. This is a rendering boundary, not a substitute for backend validation or an OS sandbox.

Verification uses the installed Chromium and Python Playwright via `verify_ui.py`, with explicitly synthetic fixture data. Root owns real `status.json` and media. First visual review covered desktop, 390px, 320px, 720 CSS-pixel zoom-equivalent layout, snapshot and unavailable states; one combined correction addressed hidden filtered selection, malformed records, invalid future timestamps and unsupported decorative glyphs. Final receipts name exact checks. Actual browser zoom, a screen reader, other browser engines and personal-device execution remain unverified.
