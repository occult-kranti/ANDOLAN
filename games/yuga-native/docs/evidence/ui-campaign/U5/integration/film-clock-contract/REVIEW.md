# Legacy film transition clock correction

CI39084375153 failed its120-headless-frame deadline while the threaded film resource was still loading. The fixture now bounds elapsed time to30 seconds and returns early on explicit loader error; all actual actor, scene, seek, audio-state, fatal-path and return assertions remain.

The complete fixture passes42/42 against frozen U5r2. Its one intentional missing-model diagnostic is expected and verifies the visible fatal path and working Return button. There are no unexpected errors or warnings. The rejected CI log is retained. No runtime change is part of this correction. Other asynchronous transition fixtures were inspected: ui_boot, ui_end_to_end, ui_transition_lifecycle and I1 preferences already use elapsed-time bounds.
