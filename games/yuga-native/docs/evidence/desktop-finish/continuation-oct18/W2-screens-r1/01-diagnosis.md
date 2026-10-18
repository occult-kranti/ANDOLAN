# D09-W2 diagnosis: focused controls vanish on resize

The controls and Rama guide retain keyboard focus when the logical canvas changes from 1280×720 to 640×360, but their ScrollContainers do not reveal the unchanged focus after the smaller layout. A player can keep capturing a key or navigating an ability whose focused button is no longer visible.

I read the native PRODUCT/DESIGN documents and pinned Impeccable polish guidance, and directly opened committed controls-capture, settings and enlarged guide originals (`package-native-review/W1-patched-r1/warm/05-controls-awaiting-key.png`, `04-settings-edited.png`, and `D09/W1-current-screens-r2/originals/09-guide-200.png`). They establish the incumbent controls and scrolling composition, not a dynamic-resize pass. The already accepted title/loading and next-focus fallback work were excluded.

## Settled live witness

The independent tiny read-only audit settles layout **before** changing focus and entering capture/selection. It then preserves focus while changing actual canvas scale, without manual layout repair:

| Component | 100% initial button / scroll y | 200% button / scroll y | Result after ten frames |
| --- | --- | --- | --- |
| Controls, Guardian Circle | 518–566 / 156–566 | 518–566 / 156–206 | Focus/capture retained, button invisible; scroll remains394 |
| Guide, Dawn Volley | 490–538 / 215–538 | 414–462 / 139–254 | Focus retained, button invisible; scroll remains5 |

Exact coordinates and source pins are in `audit-settled-report.json`; native command/exit0 and clean log are retained. Baseline sources are controls `423dac3e…` and guide `b4badc83…`, preserved byte-for-byte under `baseline-sources/`.

The first audit focused before containers had settled, so even its initial button was outside the scroll. That attempt did **not** establish a valid before/after precondition and is retained as an insufficient fixture. The settled successor corrects that setup rather than attributing the initial condition to the game.

Root approved controls-only ownership, then expanded it after the settled guide witness and W1 route handoff. The shared fix is justified because both ALWAYS modals need the same guarded, deferred scroll reveal. Their distinct close, capture, capability, feedback and host-return behavior remains local. No broad widget/style extraction is proposed.
