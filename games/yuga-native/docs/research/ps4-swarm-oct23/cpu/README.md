# Actual cloud CPU-model pilot

Use the canonical [reproducible tool and instructions](../../../../tools/local-swarm/cpu/README.md). `build`, `fetch-model` and `qualify` are separate opt-in operations. Cached dependencies, source checkout, native executable and weights remain outside Git at `/workspace/scratch/ps4-swarm-oct23/cpu` in this session.

The official Qwen2.5-Coder-0.5B-Instruct Q4_K_M file is pinned by revision, Apache-2.0 license, **491,400,064-byte** size and SHA-256. Pinned llama.cpp source built with two jobs and every GPU backend disabled. The full build took **183.36 seconds**; the reusable incremental build and version checks passed.

Two real generation receipts are retained:

- [First generation](evidence/first-qualification.json): 87 prompt/102 output tokens, 1.769-second completion, failed bounded content check.
- [Corrected-tool generation](evidence/qualification.json): 87 prompt/102 output tokens, 1.727-second completion, server-reported 68.89 generation tokens/second, peak process RSS 601,784 KiB. The same answer and content failure are preserved. The service stopped and was reaped.

The generated response used a Markdown fence, the wrong field shape, and a contradictory blocked-tile move. It was treated as data and never executed. This establishes small-model CPU serving on this cloud; it does not qualify autonomous QA, coding-client tool calls, PS4 speed or game quality.

The [summary](evidence/qualification-summary.json), [14 boundary tests](evidence/boundary-tests.json) and [independent revalidation](evidence/independent-revalidation.json) distinguish real runs from mocked counterexamples. Path, transfer-policy, launch identity and failure-receipt findings were repaired. The final source changes after the second real run only improve preflight failure reporting; [the actual-generation source](evidence/cpu_llama.verified-generation.py) is retained separately.

`reusable/` is the frozen source snapshot bound by this research's [promotion manifest](promotion.json) and `SHA256SUMS`. The executable project copy lives under `tools/local-swarm/cpu/`; change that canonical tool for future work, then produce new evidence rather than rewriting these receipts. No model weights, virtual environment, compiler output or llama.cpp checkout are included in the bundle.
