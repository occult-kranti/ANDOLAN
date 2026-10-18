# Successor journey preparation

The new child `/tmp/yuga-desktop-journey-r2/project` binds the repaired first-entry world and the capture runner's imported-resource checks. Its freeze receipt is `5a6fb07e1055d112fb7516ae9e42bda9ca85d4f230ca47ba50bf57ebb9f40337`. The [input inventory](capture-inputs.json), SHA `2a4754e9ee329f25f566d9750e3f9905d67671c87447efcabc818513b424e081`, contains **608 source/tool/test files and 358 existing cache/support files**. W1 verified all 966 before and after staging. No imported-cache input changed from the earlier inventory.

The earlier `journey-r1` child (`002c09a53820ddfaf3997bf906cfd82145eacf784b78f031c68c88094bc2f719`) and its [65-check headless preflight](../../journey-preparation/W6/preflight-r1/report.json) remain separate. That preflight used world `7570abd0…01dc36bb`. The old actual ten-shot take exposed a 22-pixel summary strip at 150% scale. This successor uses world `6e9d88657b5b3a69b67e0bc93e4f45988faa65d5206d9cabdaea45543e2d19bf`; W4's [fresh-entry receipt](../../world-first-compact-entry/W4/receipt.json) retains the failing 9/10 baseline and passing 10/10 repair plus affected regressions. Those checks do not establish raster acceptance or a general dynamic-wrapping guarantee.

Four bounded regressions now belong to the existing catalogs:

| Catalog | Suite | Checks | Source scope |
| --- | --- | ---: | --- |
| screens | `ui-title-identity` | 33 | Real compact title identity and layout |
| screens | `ui-outcome-shortcuts` | 20 | Actual terminal-state shortcut copy |
| screens | `ui-world-compact-first-entry` | 10 | First constrained world entry without manual layout repair |
| visual | `desktop-volley-feedback` | 17 | Actual combined Volley feedback after 200 authority warmup ticks |

The catalogs contain 41 screen suites and 17 visual suites. The [catalog selftest](catalog-selftest.json) passes **31/31**, including category separation, dependency closure and the explicit Volley warmup argument. These are registration checks; the full catalogs were not rerun. The new entries retain their authors' separate source-bound execution evidence.

The integrated runner now records each `.godot/imported` payload hash and checks it against the frozen receipt before launch. It rejects imported-resource or receipt changes after execution. This supplements raw-source identity; it does not prove that an arbitrary stale cache was correctly generated. [Tool tests](tool-checks.json) pass **12/12**, including a changed-cache counterexample while raw source stays unchanged. Package mode continues to use the executable/PCK identity. The runner is `322e919185825c5b6bd49911fbe2b64b70a2149ffbb0199958e98c45ce22763d`.

The [23-view native plan](../../../../../tools/ui-campaign/desktop-journey-plan.json), observer and preflight source remain unchanged. It uses real keyboard navigation and explicitly labeled authority staging for three rule outcomes and one terminal HUD view. The engine remains the unmodified public template `dce0422d…cf730f`; Godot and Mesa shader seeds are copied into a private user directory, with no preferences copied. The original per-observation timeout is unchanged. W1 is the sole renderer owner and will execute the native journey after the repaired ten-shot take. This preparation report makes no native-input, Quit, pixel, cold-start, performance or packaging acceptance claim.

After execution, W6 will use the existing independent raw-frame validator, separately inspect the new import-cache guards and directly review original images. The final source-specific review and allowlisted checkpoint inventory follow that evidence. Lead-owned documentation and other workers' still-active art/motion packets are excluded until separately sealed.
