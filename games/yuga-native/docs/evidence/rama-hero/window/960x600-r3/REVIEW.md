# Final package R3 — actual Linux smoke

17 October 2026. **Accepted bounded 960 × 600 smoke**, source `9eb6323ef20d8f10436a893ffcd434096686247a`. The packaged native working tree is clean; its 352 runtime-source manifest hash is `65b5b8f4baff7bf5393b2051b96181bfed6fc48436869428835177e3a05566e3`.

Exact executed bytes, for later downloaded-package equivalence checking:

- PCK SHA-256: `0b48d929c08285ffdcd1a7b2cc01136f6e53e1e4ad9b2645b927ce0cd047cf04`
- Linux engine SHA-256: `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`

[review.json](review.json) and [package-manifest.json](package-manifest.json) pin exact sources, commands and receipts. These are the locally extracted bytes actually executed; this smoke does not itself claim a later public download was checked.

| Actual observed state | Screenshot |
| --- | --- |
| Loaded title and real Rama actor | [01](01-title-loaded.png) |
| Confluence entry and live ability HUD | [02](02-confluence-entry.png) |
| Guardian field visible, `field active` and `+55` shield | [03](03-guardian-active.png) |
| Natural expiry: field gone, `Rama is ready`, no shield | [04](04-guardian-expired.png) |
| Pause panel and focused Continue | [05](05-paused.png) |
| Resumed gameplay | [06](06-resumed.png) |
| F5 reset restores entry camera and ready HUD | [07](07-reset.png) |

All seven stills were visually inspected. [input-review.json](input-review.json) records real XTest clicks, a downward aim motion, C, Escape and F5. Aiming downward put the actual accepted field around Rama; no simulation state was injected. The expired snapshot follows natural field expiry and cooldown completion. It does not resolve the exact expiry frame; numerical authority/HUD tests and the short/continuous render probes own that claim.

No engine errors or warnings appear in [game.log](game.log). The helper exited 0 and closed its game/Xvfb; game code −15 is requested cleanup. Xvfb's existing `/tmp/.X11-unix` ownership notice is retained in [xvfb.log](xvfb.log). The render slot was released directly to the final R3 continuous-capture owner.

Rendering used software Vulkan llvmpipe/Forward+ and Dummy audio. This is not physical-GPU performance, listening quality or Windows evidence. Unchanged Settings, guide, remapping and other UI flows retain their separately pinned [R1/R2 reviews](../REVIEW.md); they were not all repeated here. No runtime changes were made during the smoke.
