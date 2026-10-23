# Explicit CPU llama.cpp qualification

This opt-in workflow builds a pinned CPU-only server and qualifies one small official instruct model. It is separate from the six-worker planner and does not establish autonomous agents, GPU performance, or the suitability of larger models. Nothing here belongs in an ordinary setup hook that automatically downloads weights.

The recipe targets Linux x86-64 with Python 3.11+, Git, a C/C++ compiler, Make, and curl. It installs the verified CMake wheel only into the selected cache's virtual environment. Retain the cache outside Git; the tool rejects a cache directory within a checkout. It preserves an existing source checkout or artifact that does not match its pins instead of overwriting it.

```sh
python cpu_llama.py build --cache-dir /workspace/scratch/ps4-swarm-oct23/cpu
python cpu_llama.py fetch-model --cache-dir /workspace/scratch/ps4-swarm-oct23/cpu
python cpu_llama.py qualify --cache-dir /workspace/scratch/ps4-swarm-oct23/cpu
```

`build` prepares only the source, toolchain, and server. `fetch-model` is the explicit weight-download step. It must be rerun after a supported network change if access was denied; it performs no automatic retry or alternate-source fallback. `qualify` requires the exact verified weights and a matching recorded build, starts its own loopback server, checks health and the model list, performs one real bounded chat completion, then stops and reaps that server. A missing model returns `BLOCKED_NO_VERIFIED_WEIGHTS` with exit 2; it never substitutes a mock response or another model.

The default cache is `/workspace/.cache/local-llm-cpu`, configurable using `--cache-dir` or `LOCAL_LLM_CACHE`. `--port` changes the qualification port from 8093. The server binds only `127.0.0.1`; localhost requests bypass proxies solely for that literal loopback connection and never follow redirects. Download requests use the inherited HTTPS proxy and TLS verification. No cloud-inference route is configured.

Downloads disable ambient curl configuration, reject symlink path components and artifacts (including dangling partial symlinks), and write through an exclusively created file descriptor before checking size and hash. A partial attempt is preserved for inspection rather than silently retried. Qualification uses a fresh per-launch API key held only in memory and verifies the exact model alias in both the model list and completion response. Build-step logs record timeout and budget failures. Qualification failures, including binary-hash and occupied-port preflight failures, replace any previous qualification success receipt when its output path is safe. The cache directory and its parent directories must remain trusted; this helper is not a sandbox against concurrent directory replacement.

`manifest.json` pins:

- llama.cpp source commit `1a24df163920a4744a95373d178d790b72a9bb2f`, checked by Git object verification. The upstream source license is MIT.
- CMake 3.31.10 from the official PyPI wheel, verified against its published SHA-256 before installation.
- Official `Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF` revision `ebb2015119c907b064c512bf053e945850b5875f`, file `qwen2.5-coder-0.5b-instruct-q4_k_m.gguf`.
- Weight size **491,400,064 bytes**, SHA-256 **`1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32`**. The inspected pinned model card and license identify Apache-2.0; their hashes are included too.

The limits are 1 GiB for weights, 3 GiB for the complete cache, two build jobs, two inference threads, one request slot, 2,048 context tokens, and at most 128 output tokens for the qualification prompt. CPU native optimization is enabled, so rebuild on a different machine rather than assuming the binary is portable. CUDA, HIP, Vulkan, Metal, SYCL, OpenCL, WebGPU and RPC backends are disabled. Prebuilt UI downloads and subprocess tools are disabled. At runtime GPU layers are zero, offline mode is enabled, and the optional prompt RAM cache is disabled.

The game-related qualification asks for one JSON regression case: moving from `(2,2)` into blocked tile `(3,2)` must leave the player at `(2,2)`. The receipt retains the exact prompt, generated response, API token counts, latency, startup time, process peak RSS and service shutdown outcome. A separate content check evaluates the response's three-field JSON shape and expected position. Generated text is treated as data and never executed. Passing this small check is not a general coding benchmark.

For a manually retained server after qualification, use the exact `command` recorded in `evidence/qualification.json`; run it in the foreground and stop it when finished. Qualification itself always stops the service. Do not copy weights, the source checkout, virtual environment, or build products into Git.

Evidence stays under the cache's `evidence/` directory. `build.json` records the initial full build, `build-receipt.json` records the reusable build/version check, `model-transfer.json` records the explicit download attempt, and `qualification.json` records whether actual inference ran. The initial transfer failure and a later attempt after an environment restart are retained separately. The official resolver redirected the selected weight to `us.aws.cdn.hf.co`; this is the storage host whose access was relevant, not a mirror.

Run `python -m unittest -v test_cpu_llama.py` in this directory for mocked boundary tests. Those fixtures verify artifact and identity handling; they are separate from the retained real generation evidence. The original live run is retained in `first-qualification.json` and `cpu_llama.first-generation.py`; a second run after the boundary fixes is recorded in `qualification.json`, with its exact tested source in `cpu_llama.verified-generation.py`. A later change only to preflight failure receipts is separately mock-tested; it did not change successful serving or trigger another generation. Both model outputs remain available, including their content-check failures.

Check the current receipt before claiming readiness. A built binary, a downloaded model, an endpoint health response, and a real generation are separate outcomes. Existing receipts describe the machine and exact settings that produced them; new machines and client integrations need their own qualification.
