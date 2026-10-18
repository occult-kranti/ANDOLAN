# World return regression contract

The original fixture exhausted120 unthrottled headless frames before threaded resource loading completed. It failed the first Explore transition; the report and log are preserved. The correction bounds real elapsed time to30 seconds and stops on an explicit loader error. Actual scene identity, active player, pause behavior, old-instance disposal and collision-group cleanup remain required.

The frozen U3 runtime passes13/13 checks across three complete courtyard → world → courtyard cycles, with no engine diagnostics. No production change is included. This establishes headless lifecycle behavior, not OS input or visible layout.
