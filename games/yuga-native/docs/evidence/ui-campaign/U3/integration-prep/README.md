# Screen round3 preparation

Root extracted the existing world atlas, added core names from actual objective positions and the hero heading, and removed duplicated world menu styles in favor of the shared theme. The existing25-check siege/menu suite passed. This is source preparation, not a completed worker assignment or rendered acceptance.

The title/body now use unmodified bundled Noto fonts and explicit symbol fallbacks with system fallback disabled. Font resources are shared across panels. Source and license identities live under NOTICE/Noto-fonts. The88-check theme suite and5 glyph/resource checks passed; final glyph checks include both fallback resources. The2D boot recovery images were independently inspected by root at960×600; text, focus and Retry/Back/Quit controls fit. Integrated3D/map, scaling and packaged font acceptance remain with U3/I3 workers.

The initial Noto Symbols fallback inflated line metrics and was rejected after the world worker measured HUD overlap. Final shared fonts retain Noto body/display and use unmodified DejaVu Sans for symbols. Seven glyph/metric/resource checks pass:17px body height24px,11px caption height16px. The two unused root-created Noto Symbols runtime copies were removed; original installed fonts and prior frozen evidence remain. Final combined layout is owned by U3 reviewers.
