# Original PS4 Linux as a worker for the laptop

Research date: 2026-10-23. The user identifies an **original PS4** and answered “and yes” to the existing jailbreak/Linux question. Treat an existing Linux installation as provisional; firmware, distribution, kernel, Mesa version, memory allocation and current SSH access remain unknown. No console was accessed and no firmware, exploit, model, package or driver was installed.

The practical recommendation is to keep the laptop's RTX 4070 as the primary LLM and GPU-asset machine, and qualify the PS4 first as **one SSH-controlled CPU worker**. A tiny local LLM on the PS4 is an optional measured experiment after the basic worker is useful. GPU inference on the PS4 remains a separate compatibility experiment. An additional machine does not pool its memory with the laptop's VRAM or automatically make six agent roles faster.

## What the linked forum establishes here

The supplied [“A.I. on ps4linux” thread](https://ps4linux.com/forums/d/130-ai-on-ps4linux) initially failed with **CONNECT 403** at 2026-10-23 19:55:41 UTC. After a meaningful environment restart/network change, one new request through the same supported HTTPS route succeeded at **20:06:34 UTC**, returning 96,780 bytes. All **15 visible post records** were extracted and read, spanning **5 July 2023 to 15 February 2024**. `forum-fetch.json` preserves the first failure; `post-restart-fetches.json`, `forum-thread-post-restart.html`, and `forum-posts.json` preserve the successful retrieval and exact post metadata. No mirror, alternate proxy, cache or bypass was used. Linked images, installers, archives, model weights and external tutorials were not downloaded or inspected.

| Actual forum statement | Attribution and date | Evidence assessment |
| --- | --- | --- |
| Stable Diffusion: one image took **2–3 hours**, using **4 GB RAM plus 6 GB swap**; installation was copied from another PC. | `misfit-mischief`, [post 1](https://ps4linux.com/forums/d/130/1), 5 July 2023 | Single historical self-report; installation untested here. |
| GPT4All: unspecified **7B** was slow; **Orca Mini 3B GGML Q8** was fastest among the author's trials; **six threads**, **75–85% CPU**. | `misfit-mischief`, [post 5](https://ps4linux.com/forums/d/130/5), edited 12 July 2023 | No tokens/second benchmark. Linked model: `TheBloke/orca_mini_3B-GGML`. Six threads are not an established optimum. |
| FastSD CPU: **512×512**, just under **20 seconds/step**, at least **four steps**; recommended **1 GB payload**, **8 GB swap**, and `lcm-lora`/`lykon/dreamshaperv8`. | `misfit-mischief`, [post 6](https://ps4linux.com/forums/d/130/6), 31 January 2024 | CPU image generation; per-step time is not total latency. Historical payload advice is not prescribed here. Linked project: `rupeshs/fastsdcpu`. |
| kexec booting; later claim that drivers are all built in, without modules. | `noob404`, [posts 11](https://ps4linux.com/forums/d/130/11) and [13](https://ps4linux.com/forums/d/130/13), February 2024 | kexec broadly corroborated; the inspected kernel config enables modules, contradicting a universal reading. |

These are historical CPU-AI leads, not reproduced results. GPU training and six-agent performance were not demonstrated. Qualify current packages and GGUF artifacts separately from the linked legacy installer and GGML model.

The official [PlayStation PS4 technical-specification page](https://www.playstation.com/en-us/ps4/tech-specs/) returned CONNECT 403 on both the initial request and the single post-restart retry; no further retries were made. The standard retail background is that original/Slim systems use an eight-core AMD Jaguar-class CPU and 8 GB shared GDDR5; Pro has a different, stronger GPU and revised hardware. That background was not freshly manufacturer-verified here and is not a measurement of this console. This report does not assume a Pro GPU, CPU clock, auxiliary memory arrangement, or Linux allocation applies to the user's original model. The actual CPU flags and `MemTotal`/`MemAvailable` from the running console determine the worker profile.

## Verified source findings and their limits

| Evidence | What it supports | What it does not establish |
| --- | --- | --- |
| `ps4boot/ps4-linux` at `cf76ce01eedc200ddc836f315cc7568f3e5fba18`, `Makefile:2–4` and `config:250,298,336` | This published PS4 fork is kernel **5.3.18**, configured for x86-64, PS4 and up to eight CPUs. | It is not the user's observed kernel, a current kernel recommendation, or a verified installation for every PS4 revision. |
| Same pinned `config:2155–2176` | This fork enables `CONFIG_DRM_AMDGPU=y` and `CONFIG_DRM_AMDGPU_CIK=y`, while disabling the Radeon driver and **`CONFIG_HSA_AMD`**. | Working AMD graphics does not imply ROCm/KFD support. A different PS4 kernel may have different options. |
| Same pinned `config:669,671,3064` | This fork enables loadable modules, module unloading and procfs. | The forum's blanket statements about all PS4 Linux kernels lacking modules or procfs should not be generalized. The running console's mounts/configuration remain unobserved. |
| `fail0verflow/ps4-kexec` at `e79feb87311f79084ee63a354e5646135efc4ac5`, README opening and Features section | The project supplies a kernel-boot mechanism requiring an existing way to run kernel code; its historical firmware handling describes the Radeon driver. | It is not a universal Linux installer or evidence of any particular firmware's present compatibility. No instructions from it were executed. |
| ROCm at `63fd8390bf645ae3c0c715537025137127f892e3`, compatibility matrix and `docs/data/gpus.yaml` | The vendor documents a coordinated firmware/driver/userspace stack and enumerates supported GPU families; no PS4/PlayStation/Liverpool target appears in this inspected device table. | It does not prove no experiment could ever work. It does mean official PS4 ROCm support was not established. |
| Current llama.cpp and GCC sources in [CPU/Vulkan report](cpu/README.md) | CPU-only build options, explicit ISA controls, and current Vulkan loader/device requirements are inspectable and pinned. | No compiler success, console inference, GPU acceleration, memory fit or throughput has been measured. |

Do not install a random kernel, replace graphics drivers, set fake GPU-architecture environment variables, or assume a newer Mesa package alone resolves these unknowns. The existing working Linux installation is the starting point; a firmware/kernel change is not needed to collect inventory or use SSH.

## First action: read-only console inventory

[ps4-inventory.sh](ps4-inventory.sh) reads the running kernel, distribution, CPU flags, actual Linux memory, free disk space, PCI driver bindings, DRM/KFD device nodes, relevant running-kernel configuration when readable, compiler availability and SSH/inference listening sockets. It makes no network request, needs no root privilege, installs nothing and writes no target files. `--gpu` optionally runs an installed `vulkaninfo --summary` under a 15-second timeout; the default does not exercise Vulkan.

The script passed `bash -n` in the cloud. **It has not run on the console.** It is a diagnostic collector, not a readiness test: unavailable commands and nonzero command statuses remain visible in its output.

If SSH already works from the laptop, copy the script and collect its output with the following **unexecuted PowerShell templates**. `ps4-worker` is a configured SSH host alias, not a discovered hostname:

```powershell
scp .\ps4-inventory.sh ps4-worker:~/ps4-inventory.sh
ssh ps4-worker "bash ~/ps4-inventory.sh" | Tee-Object -FilePath .\ps4-inventory.txt
```

Otherwise run `bash ps4-inventory.sh` in the console's existing Linux terminal first. Identify the distribution before configuring its supported OpenSSH server; service/package names vary. Use the existing Linux user and existing SSH identity where available. A minimal laptop SSH configuration uses placeholders that must be replaced with the actual LAN address and Linux account:

```sshconfig
Host ps4-worker
    HostName <PS4_LAN_IP>
    User <PS4_LINUX_USER>
```

Verify the initial SSH host fingerprint through the console. Keep ordinary host-key verification enabled. No internet port forwarding, root SSH account or separate VPN is required for this LAN workflow.

Interpret the inventory before building:

- The expected architecture is `x86_64`. Record the **actual** flags exposed by Linux. AVX/SSE4 support is not AVX2/FMA support.
- Record `MemAvailable` and free disk space with the normal desktop workload running. Physical shared GDDR5, CPU-visible memory and GPU allocations are not three additive pools. The Linux boot/payload allocation and driver reservations matter.
- Identify the bound GPU driver. `/dev/dri` and a desktop prove less than working hardware Vulkan. `/dev/kfd` and HSA-enabled kernel support are separate observations.
- Record compiler, CMake, libc and runtime compatibility. A modern laptop binary can fail on an older PS4 distribution even if both are x86-64.

## Use the PS4 as a normal worker first

Give the console one bounded CPU task at a time: validate a JSON or asset manifest, run an already-supported small test subset, check source links locally, process text, or prepare a compact result. The laptop keeps planning, code generation, interactive review, primary model serving and GPU-heavy asset jobs. Task suitability must be established by an actual run; this report does not promise a speedup over the laptop CPU.

Use a separate working directory on the console and agree an input contract before dispatch:

1. A packet contains a task ID, exact input/source revision and hashes, an explicitly allowed command, expected output files, and a time/resource limit.
2. Transfer only needed inputs. Avoid sending a full model library, all six conversation histories, credentials, or unrelated large game assets.
3. Run the agreed command through SSH with one active job. Do not give model-generated arbitrary shell text automatic execution rights.
4. Return output files, the command's actual exit code, elapsed time and input/output hashes. Keep stdout/stderr with the receipt.
5. Review the result on the laptop. The console does not push, merge, publish or overwrite the main checkout automatically.

Example directory preparation, after SSH is established, is `ssh ps4-worker "mkdir -p ~/swarm/inbox ~/swarm/outbox"`. This is an unexecuted reversible setup template. The exact project test command should be selected after inventory rather than copying a generic test that could trivially pass without exercising the task.

This arrangement is task distribution, not tensor/model parallelism. No distributed inference protocol, reliable memory pooling or PS4 GPU sharing has been established. A single laptop model can continue to supply six role prompts while the console performs selected external tools.

## Optional CPU-only LLM qualification

Use the exact source-verified templates in [cpu/README.md](cpu/README.md). Current pin: `ggml-org/llama.cpp` **`1a24df163920a4744a95373d178d790b72a9bb2f`**. They assume the user has prepared a checkout and selected/downloaded a properly licensed model; no install or weight download was performed here.

`GGML_NATIVE=OFF` by itself does not disable all advanced x86 instructions. The report explicitly disables AVX2, FMA, BMI2, AVX512 and AMX options, and offers an initial conservative no-AVX build. GCC's inspected `btver2` profile includes AVX/F16C/SSE4.2/BMI while omitting AVX2/FMA/BMI2; that compiler profile is not an observation of the console. Enable AVX, F16C and SSE4.2 only after the target reports usable support, and measure the result. Build on the target distribution or with a deliberately matching toolchain/sysroot; do not copy a laptop `-march=native` executable.

Start with a roughly **0.5B–1.5B Q4** model, a short 1,024–2,048-token context, one request and a small thread count. This is an unmeasured starting hypothesis. Advance model/context size only after observing available RAM, real task output, prompt processing and generation time. Swapping a large model into slow storage is not a practical success criterion. Do not start with six resident models or assume a 7B model is useful because a model file can be opened.

The child report's server template binds to **PS4 loopback port 8081**. To reach it from the laptop without exposing the server on the LAN, keep the following SSH tunnel open in a second laptop terminal:

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:18081:127.0.0.1:8081 ps4-worker
```

The laptop client then uses `http://127.0.0.1:18081/v1`. This is a local tunnel template, not a live service or user-facing preview link. The laptop's Ollama can retain its own port 11434. Test a real bounded completion, not just `/health`, before routing a role to the PS4 endpoint. Record model hash, source/build version, prompt and context, peak RAM/swap, errors, latency and output quality. Only then decide whether using the PS4 for inference improves this workload over its simpler tool-worker role.

## GPU inference remains a separate experiment

Current llama.cpp source requires a Vulkan loader exposing **API 1.2 or later** and rejects devices without **`storageBuffer16BitAccess`**. These are necessary conditions identified from source, not an exhaustive guarantee. Build dependencies include `glslc` and SPIRV-Headers. `vulkaninfo` must identify the actual PS4 hardware device, required features and usable memory; `llvmpipe`/`lavapipe` is software rendering and must not be reported as PS4 GPU acceleration.

Only after the running driver meets the observations should a separate Vulkan build and tiny-model offload correctness/memory experiment be considered. Preserve the passing CPU build. Do not infer a universal Vulkan outcome from the label “AMD GCN,” a working OpenGL desktop, or a PS4 kernel fork's graphics configuration.

ROCm/HIP is not the initial recommendation: the inspected vendor compatibility table has no PS4 target, and the inspected PS4 fork disables HSA. The user's actual kernel might differ, but no supported PS4 ROCm path has been verified. There is no NVIDIA GPU in the PS4, so the laptop's CUDA path is not transferable to the console.

## Acceptance and handoff

| Gate | Current result | Next evidence |
| --- | --- | --- |
| Original PS4 identity and existing Linux | User-reported; Linux interpretation provisional | Running console inventory, exact firmware/distro/kernel |
| Read the supplied forum | All 15 posts retrieved/read after restart; historical self-reports separated from primary-source checks | Current target reproduction would be new evidence; linked images/installers remain uninspected |
| SSH and file exchange | Unrun | Successful laptop-to-console login and small round-trip file/hash check |
| Useful non-LLM worker | Unrun | One representative task with correct output and bounded resource use |
| CPU build and inference | Source options verified; target unrun | Exact source builds; real small-model completion and task-quality check |
| GPU inference | Necessary source requirements identified; target unrun | Actual hardware device/features, compatible build, output and memory measurements |
| Speedup from using the PS4 | Unmeasured | Matched task timing against the laptop-only workflow |

Files owned by this research packet: this README, `evidence.json`, fetch metadata/raw source files, `ps4-inventory.sh`, and `cpu/` source study. No ANDOLAN repository file was edited. The next owner is the root integrator; the next hardware action is a console inventory, not flashing or automatic model installation.

## Pinned source entry points

- [PS4 kernel config](https://github.com/ps4boot/ps4-linux/blob/cf76ce01eedc200ddc836f315cc7568f3e5fba18/config#L2155) and [version](https://github.com/ps4boot/ps4-linux/blob/cf76ce01eedc200ddc836f315cc7568f3e5fba18/Makefile#L2).
- [PS4 kexec README](https://github.com/fail0verflow/ps4-kexec/blob/e79feb87311f79084ee63a354e5646135efc4ac5/README.md), read only as boot/firmware-context evidence.
- [ROCm compatibility matrix](https://github.com/ROCm/ROCm/blob/63fd8390bf645ae3c0c715537025137127f892e3/docs/compatibility/compatibility-matrix.rst) and its [GPU data](https://github.com/ROCm/ROCm/blob/63fd8390bf645ae3c0c715537025137127f892e3/docs/data/gpus.yaml).
- [CPU/Vulkan source ledger](cpu/evidence.json): exact upstream files, commits, hashes, line-level claims and unexecuted templates.
- [Supplied forum](https://ps4linux.com/forums/d/130-ai-on-ps4linux), retrieved 23 October 2026 at 20:06:34 UTC; HTML SHA-256 `5506c5e61a714d40d895289c0e9dd2078a263564390758e6796e90182c61f18d`. Exact authored/edited dates and links appear in `forum-posts.json`.

`evidence.json` preserves successful sources, historical self-reports, missing paths, initial and remaining denied requests, checked hashes, unverified hardware background and unrun hardware gates. Source inspection, forum reading and a script syntax check are the completed verification, not a PS4 deployment.
