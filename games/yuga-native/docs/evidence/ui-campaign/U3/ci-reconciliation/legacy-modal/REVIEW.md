# Legacy-modal opener reconciliation

Run39082007988 reached the separate Mythic integration suite and exposed the same historical fixed-button expectations in its invocation and Rama modal checks. These fixtures open directly from the focused Continue action, before pending pause callbacks settle. They now record that exact opener and require it to regain visible focus after closing. All pause, clipping, focus-loss and held-input assertions remain intact; no runtime change was made.

The full Mythic integration suite passes116/116 with clean logs on the frozen U3 runtime. Original failures and exact checked-source identities are retained. A repository-wide search found no remaining assertions that require Rama/invocation buttons after opening from another control. Full CI remains a separate gate.
