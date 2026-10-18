# D07 atlas and route regression repair

Final current-world route checks pass **27/27**, and existing atlas checks pass **15/15**, with clean engine logs, exit0 and unchanged source bytes. Only these two suites ran after the final changes. This is headless component/physics evidence; no new pixels or package gameplay were reviewed.

The original route run and observation-only replay each remain17/19. Both failures came from requiring identical local pixel coordinates while the overview intentionally resizes the plot from142×229 to196×364. Manifest-derived XZ fractions were correct throughout; the original plot and raw pixels returned exactly.

A separate diagnostic then exposed a real runtime heading defect: the root body stayed north while the authored hero visual faced±45°. The17/21 receipt retains both heading failures separately from the two old resize failures. Root changed the marker source to actual visual+Z.

The first stronger fixture and camera diagnostic each remain23/25. Direct mathematical heading differed by up to1.097e−5 because the old implementation subtracted two float32 projected positions. Root replaced that operation with direct direction×plot/world-span scaling, retaining finite and zero handling. The camera position, parent and ownership were exact; only its SpringArm-computed basis changed by8.896e−8. The final fixture keeps exact owner/origin/parent restoration and uses Godot's existing Basis.is_equal_approx only for that measured basis drift.

The repaired fixture independently computes expected normalized position and heading from captured world-manifest bounds and actual visual facing. It preserves the original geometry checks and exact live map parent/plot/pixel/heading restoration. Four synchronous marker/facing corruptions must fail the same mapping predicate and then restore correctly. Two diagonal10km translation witnesses require exact heading independence and zero/NAN/INF rejection. W4 independently reviewed the diff and numerical diagnosis; root accepted the final results.

All failed reports, exact source snapshots, logs and source-before/after receipts remain in adjacent W5 diagnostic directories, pinned by receipt.json. The current motion5023 and accepted UV hero assets were unchanged. The earlier motion26/27 limitation remains separate. W5 changed only the route fixture; root owns the two narrow runtime heading corrections.
