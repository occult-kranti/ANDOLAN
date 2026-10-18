The initial independent checker returned 8/9 in `navigation-check-partial.json`. The failure was an overbroad focus assertion against synchronous loader phase signals, not a demonstrated displayed UI failure. Its exact script is retained as `check_package_navigation_initial.py`.

`scene_transition.gd` emits the queued phase in `_set_phase()` before the next statement calls `back_button.grab_focus()`. The film-return queued signal therefore recorded an empty focus owner. The corresponding actual displayed `auto-queued-3` original and JSON, at frame87, show Back focused and interactive, with the film controls disabled. The preceding outgoing-scene process mode was already disabled in every busy event.

The corrected check retains the single transition owner, visible loader and disabled outgoing-scene requirements for every busy signal. It separately requires focused, interactive Back and no other interactive controls in every captured loader frame. This uses the actual temporal contract instead of treating an internal signal snapshot as a completed frame. No runtime source or acceptance threshold changed.

The completed first process passes the corrected nine checks. A later combined check adds distinct two-process lifecycle and relaunch checks; repeated first-process checks are not additional unique coverage.
