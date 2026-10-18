# Keyboard-opener contract reconciliation

CI run39081728080 at5bf84061e3c6212248d218d7768386616082070a found two old integration expectations: F3 opened the guide from the focused Continue button, but the test expected closing it to select the separate Rama button. The new shared modal contract correctly returns to the actual opener.

The fixture now records the exact focused control before F3 and requires that same control on return, while retaining every visible, paused, viewport and scroll-containment assertion. Button and slider opener cases remain independently covered by U3 pause navigation tests. No runtime code or tolerance changed.

Full native hero integration passes138/138 on the frozen U3 runtime with approved R2 imports. Original CI failure, exact new source pins and clean native log are retained. Earlier stale imported-mesh evidence is historical and is not relabeled. The full CI rerun remains separate.
