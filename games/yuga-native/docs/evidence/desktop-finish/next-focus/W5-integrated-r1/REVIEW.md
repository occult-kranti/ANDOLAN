# Integrated guide and controls focus recovery

The approved private fix is now present byte-for-byte in the canonical guide and controls scripts. When focus is absent or filtered out, backward navigation selects the last eligible control and forward navigation selects the first. Freed entries are checked before property access. Controls no longer evaluates a void-returning focus call as a ternary expression. Normal wrap remains unchanged.

The [preserved private comparison](../W5-private-candidate-r1/REVIEW.md) retains baseline **19/26 plus 10 script errors** and candidate **26/26 clean**. This integration uses the same 26 behavioral/source-stability assertions with canonical preloads and a portable report argument. The final source-stability label now describes canonical sources; the other 25 labels and all input sequences remain unchanged. A disposed focus-list peer is an explicit adversary, while effect-receiver disposal exercises the actual guide capability path.

The registered `ui-focus-recovery` suite passes **26/26**. Existing controls state **19/19**, controls lifecycle **14/14**, and guide capability **18/18** also pass: **77/77**, all clean exit 0 with source-before equal to source-after. The existing catalog selfcheck passes **35/35**, including the new registration/source-closure check. [Raw reports and process logs](checks/summary.json) retain exact invocations; [execution.json](execution.json) records CPU4 affinity and the runner's LP setting. No unsupported worker-limit flag was used.

Only two runtime scripts changed. The new tracked fixture and one catalog entry use existing source pinning and report/error gates; no threshold or runner policy changed. The original private sources/reports and W6's [independent private review](../W6-independent-r1/REVIEW.md) remain unchanged. Courtyard, shared builders, motion, input binding authority and the frozen f8 package/owned diagnostic clone were not edited.

This is native viewport-dispatched 2D behavior evidence. No new raster, OS-window input, package qualification or 3D scene navigation claim is made. A future package must include and qualify these new source bytes separately from f8.
