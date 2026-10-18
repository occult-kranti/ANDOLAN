# Workspace Git discovery handoff

This packet inventories actual Git roots under `/workspace` for cloud setup. It performs no Git writes, configuration save, installation, network access, engine run or project adoption. `/workspace/ANDOLAN` is the sole managed project. The cloud-environment-onboarding setup skill guided this read-only preparation; runtime readiness and reusable configuration remain separate root-owned work.

`workspace-discovery-r2.json` is a complete historical scan pinned to `85d5831dd8586a264caa93a7ba4625d1ec0b7f21`: 47,098 directories, 181,542 files, 397 symlinks and seven Git roots; no blockers, with primary HEAD/ref/index identities unchanged. Its exact executed helper is retained as `discover_workspace_r2.py`. This does not establish completeness after subsequent artifact materialization or source commits.

| Actual root in completed r2 scan | Classification |
| --- | --- |
| `/workspace/ANDOLAN` | Sole primary managed project |
| `/workspace/scratch/community-reuse/animation/sources/blender-addons` | Pinned third-party reference |
| `/workspace/scratch/community-reuse/animation/sources/godot-demo-projects` | Pinned third-party reference |
| `/workspace/scratch/community-reuse/animation/sources/ozz-animation` | Pinned third-party reference |
| `/workspace/scratch/community-reuse/art/upstream/material-maker` | Pinned third-party reference |
| `/workspace/scratch/yuga-continuation-W6-r1/package-successor-r1/ANDOLAN` | Isolated export artifact, proven by its exact materialization receipt |
| `/workspace/scratch/yuga-continuation-W6-r1/snapshot-guard-fixture-r1/source` | Synthetic guard fixture, proven by its exact guard receipt |

The final helper also supports the exact `/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2/ANDOLAN` artifact, only after a matching completed W6 materialization receipt exists and its source commit equals the clone HEAD. R2 artifact creation was pending at handoff. No general scratch-path exemption exists: an unknown Git root or incomplete artifact receipt fails the scan.

`workspace-discovery-r1.json` preserves the initial incomplete scan and its three dangling-link failures; `discover_workspace_r1.py` is the exact executed helper. `negative-fixture-evidence.json` verifies the links at `/workspace/scratch/rea-bootstrap-guards-r{1,2,3}/dangling` point to their respective missing `absent-target`. Committed guard reports, committed dry-run output roots and the inspected generator explicitly establish these finite negative test nodes. Current generator identity matches the third report; the earlier reports retain their historical harness hashes. The final helper records each exception and its proof. Unknown missing links, changed targets, scan errors and inaccessible paths remain blockers. No link was removed or changed.

`workspace-discovery-r3.json` preserves a successful negative test of `--expected-head`: after HEAD advanced to `79e5c15d8a3657e16fda67acb277b2406120dcd1`, requesting the old 85d commit failed before walking any directory. This is an expected guard failure, not a completed current inventory.

`discover_workspace.py` is the final reusable helper. It resolves `.git` directories, files and symlinks, validates actual worktree/bare roots and common directories, records exact commits or positively proven unborn branches, sanitizes remote URLs and explicitly inventories traversal boundaries. It traverses directory symlinks inside `/workspace`, deduplicates directory identities, prunes only identified Git storage and records external symlink targets. It polls the expected primary HEAD and checks primary HEAD/ref/index identities, repository HEADs and walked directory timestamps for concurrent changes. It refuses to overwrite an output report.

The final helper's 11 pure self-tests pass, including remote redaction, pointer parsing, positive unborn versus failed Git metadata, unknown-root refusal and finite missing-link refusal. Final finite negative-fixture proof passes for all three links. The final helper's durable proof enhancement postdates the completed r2 scan; its full current scan is deliberately deferred until W6 Git materialization settles. Do not claim current completeness from the historical r2 result.

After all Git materialization and the final source commit settle, root runs from `/workspace/ANDOLAN`, replacing `<final-full-commit>` with the intended full commit hash and choosing a fresh output name:

```sh
python docs/evidence/desktop-continuation-cloud-r1/discover_workspace.py --self-test
python docs/evidence/desktop-continuation-cloud-r1/discover_workspace.py \
  --expected-head <final-full-commit> \
  --output docs/evidence/desktop-continuation-cloud-r1/workspace-discovery-final.json
```

Require exit zero, `complete=true`, no blockers, unchanged primary metadata and only `/workspace/ANDOLAN` in `managed_project_roots`. Inspect every repository classification and proof, including the new r2 artifact if present. Preserve any failed report and use a new output for a rerun. This inventory alone neither verifies application behavior nor saves cloud configuration.
