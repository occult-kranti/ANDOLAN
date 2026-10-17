# Apparent title-label dropout is absent from the saved PNG data

The original R2 PNGs **all contain the same primary button label pixels**.
Decoded RGB in `(160,314)–(400,348)`, covering `Explore Confluence →`, is
byte-identical across all four R2 title views, all four R1 views and all four
floor-probe title views:

`d9fe0d724cc0a29d899488a004a7b715b0a931e35f6c593e99b56eef9cfa75dc`

Each region contains 630 dark text pixels and matches the clearly legible
`title-day-before.png` reference. An ASCII threshold of the supposedly blank
`title-day-after.png` also exposes the full glyph raster. This contradicts the
apparent blank seen in some image-preview inspections. The preview/perception
cause itself is undiagnosed; the saved native capture has the text.

Source inspection is consistent with the pixel finding: text is assigned once,
never cleared or animated; all primary normal/hover/pressed/focus font colours
are opaque dark; the UI CanvasLayer processes ALWAYS. The lighting helper does
not reference Canvas or Button state. Capture pins 3D pose/camera/exposure but
does not record Button state, so an actual future missing-label PNG would still
need targeted UI-state logging before a fix.

No engine, import, heavy render or new capture was run for this diagnosis. No
runtime or capture-tool source was changed. The pixel check reads the original
PNGs; it does not edit or repair images. Exact source/image hashes and the
conditional next-probe proposal are in `summary.json`.

Reproduce with `python3` on `verify_label_pixels.py`; it verifies all twelve
original file hashes and the decoded label equality. No speculative runtime,
font, theme or capture-timing change is justified for this specific finding.
This comparison does not establish all continuous UI states or full-screen
production acceptance.
