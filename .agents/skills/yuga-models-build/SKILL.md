---
name: yuga-models-build
description: "Qualify YUGA local model workloads, GPU scheduling, builds and package provenance. Use for W6 inference setup, loading, resource capacity, artifact integrity and delivery assignments."
---

# YUGA W6: models, capacity and build delivery

Prepare one reproducible model or packaging workflow for the assigned machine.
Six workers are work owners, not six GPUs or six resident model copies.
Keep a capacity check, working inference, accepted art and publication distinct.

## Entry points and ownership

Read [AGENTS.md](../../../AGENTS.md), [start here](../../../docs/START_HERE.md),
[active handoff](../../../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md),
[build handbook](../../../games/yuga-native/docs/BUILD_HANDBOOK.md) and the
[AI study](../../../games/yuga-native/docs/research/ai-pipeline-oct21/README.md).
The user now confirms 8 GB dedicated VRAM plus 16 GB shared system memory;
this replaces the earlier proposed 5090 laptop as the current setup budget.

| Workflow | Actual entry point |
| --- | --- |
| Declared GPU/disk capacity | [preflight.py](../../../games/yuga-native/tools/ai-assets/preflight.py), [usage](../../../games/yuga-native/tools/ai-assets/README.md) |
| Source contracts | [check-native-contracts.py](../../../games/yuga-native/tools/check-native-contracts.py), [NATIVE_CONTRACTS.md](../../../games/yuga-native/docs/NATIVE_CONTRACTS.md) |
| CI package boundary | [ci-native-package.py](../../../games/yuga-native/tools/ci-native-package.py) |
| Release staging/validation | [release-native.py](../../../games/yuga-native/tools/release-native.py) |
| Recoverable cleanup | [workspace guide](../../../docs/WORKSPACE_AND_CLEANUP.md) |

Lead owns common manifests, roadmap, publication and source freezes. Coordinate
W1 package execution and W3/W4/W5 asset contracts before shared export/import.

## Phase 1: establish workload, routing and budget

1. Record task ID, product, exact source, exclusive paths, outcome and selected
   model/runtime. Read the current source-pinned interop report before choosing
   Codex/Claude/Kimi provider settings; similar API shapes do not prove support.
2. Inspect actual CPU/RAM limits, disk and free dedicated VRAM. Budget weights,
   tokenizer, environment, kernels, caches, extraction and scratch plus reserve.
   Shared system memory/offload does not become additional fast dedicated VRAM.
3. Pin code revision separately from model-weight revision, quantization,
   tokenizer, dependencies, hashes and code/model/output terms. Total MoE
   weights and KV cache still need storage/memory despite fewer active experts.
4. Define one heavy GPU lane. Start by qualifying one small quantized coding
   service with bounded context; share it across agents. Queue generation and
   rendering, and unload competing residents when their memory is needed.

## Phase 2: qualify the assigned workflow

Run the capacity tool with the selected workload's real declared requirements.
Its saved 8 GiB/20 GiB example is illustrative, not measured model demand.
Use its focused suite from the repository root:

```sh
python3 -m unittest discover -s games/yuga-native/tools/ai-assets -p 'test_*.py' -v
```

- A failed/unknown capacity check blocks that job; continue independent source
  and configuration work. Exit 0 does not establish inference, CUDA kernels,
  model permissions, practical speed or accepted game assets.
- Reuse compatible installed dependencies and isolate new ones. Verify actual
  CUDA architecture and custom-extension support. Preserve TLS/checksums and
  inspect installers before execution. Avoid downloading every candidate first.
- Keep endpoints on loopback by default. Resolve actual installed model IDs.
  Verify local-only routing: localhost can still forward cloud model requests.
  Use explicit hosted profiles only when authorized; no silent paid fallback.
- Qualify inventory, bounded generation and required client tool-call behavior
  separately. A healthy model-list endpoint is not proof of correct file edits,
  shell permissions or Codex/Claude/Kimi interoperability.
- Keep secrets out of repository files/logs. Use supported credential bindings.
  Shared model serving and role routing are orchestration, not training a MoE.
- Record peak VRAM/RAM, duration, settings, inputs/output hashes and failures.
  W1/W3 judge output and cleanup cost; a generated GLB is not a finished hero.
- REA metadata inspection requires a selected owned artifact and independent
  oracle; reading model headers is not loading weights or running inference.
- For packages freeze exact source/runtime/notice identities. Use fresh outputs,
  validate inventories/hashes, and require W1 actual cold/warm package input.
  Separate build success, archive validity, platform execution and public bytes.

## Phase 3: review and hand off

Return exact identities, commands/results, capacity/inference or package
receipts, original evidence, rights/notices, unrun gates and next owner.
One correction pass follows a concrete finding. Save reproducible setup/start
instructions through the supported flow; saved drafts are not applied access.
Preserve unique work and user saves; use the verified cleanup procedure only.
Continue authorized work without repeated confirmation. This skill grants no
new purchase, credential disclosure or publication. User instructions prevail.
Android remains deferred and still requires actual device/export/service gates.
