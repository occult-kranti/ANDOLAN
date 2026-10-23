# PS4 Linux: llama.cpp CPU portability and Vulkan gates

Research date: 2026-10-23. This is a source review, not a successful PS4 build or inference result. The user identifies an **original PS4**; their “and yes” provisionally confirms an existing jailbreak/Linux setup, pending clarification. Firmware, Linux distribution, kernel, installed memory allocation, CPU flags and GPU driver remain unknown. No console was accessed; no software, weights, firmware or exploits were installed or executed.

The practical first target is a **CPU-only, single-request worker** reachable through the laptop's SSH connection. Begin with a user-supplied small GGUF and a short context after inspecting Linux's actual available memory. A PS4 marketing memory figure does not determine memory available to Linux or inference. No throughput or usefulness claim follows from x86-64 instruction-set compatibility alone.

## Findings from pinned source

| Finding | Source evidence | Consequence |
| --- | --- | --- |
| llama.cpp has a CPU backend and a documented CMake CPU build | llama.cpp `1a24df163920a4744a95373d178d790b72a9bb2f`, `ggml/CMakeLists.txt:189`; `docs/build.md:33–40` | A CPU build is the sensible portable starting point, subject to real PS4 Linux compilation and execution. |
| `GGML_NATIVE=OFF` alone is insufficient to guarantee an old-x86-compatible binary | `ggml/CMakeLists.txt:105–166` can set `INS_ENB=ON` when native optimization is explicitly disabled | Explicitly turn off unsupported ISA options. A laptop-built `-march=native` binary is unsuitable as an assumed portable PS4 binary. |
| AVX, AVX2, BMI2, FMA, F16C and SSE4.2 are separate current options | `ggml/src/ggml-cpu/CMakeLists.txt:345–408` maps them to separate compiler flags | AVX support must not be treated as AVX2 or FMA support. |
| GCC's `btver2` CPU feature profile contains AVX, F16C, SSE4.2 and BMI, but omits AVX2, FMA and BMI2 | GCC `8d3bac71a9433f90161a22dd13812457d32c2352`, `gcc/config/i386/i386.h:2551–2556`; target mapping in `gcc/common/config/i386/i386-common.cc:2500–2502` | This establishes a compiler profile, not the actual console's CPU identity or enabled features. The retrieved GCC files do not themselves name Jaguar. Use the target's actual reported flags. |
| The current Vulkan backend requires a Vulkan loader exposing at least API 1.2 | `ggml/src/ggml-vulkan/ggml-vulkan.cpp:5202–5212` explicitly rejects older loader API versions | Merely having an AMD GPU, Mesa, or working OpenGL is insufficient. |
| The Vulkan backend rejects a device lacking `storageBuffer16BitAccess` | Same file, `4649–4651`, with selection check at `16347–16358` | Inspect the actual hardware Vulkan device and required features. A software Vulkan device is not PS4 GPU acceleration. |
| Building Vulkan also needs development tools | `ggml/src/ggml-vulkan/CMakeLists.txt:1–14` requires CMake 3.19, Vulkan with `glslc`, and SPIRV-Headers; build guide `515–555` asks for successful `vulkaninfo` | A build success alone does not prove the PS4 kernel/Mesa stack can perform model inference. Shader feature tests targeting Vulkan 1.3 do not override the runtime's explicit 1.2 loader minimum. |

The current root build requires CMake 3.14 or later; GGML requests C11 and C++17 (`ggml/CMakeLists.txt:289–293`). Distribution headers, linker, libc and libstdc++ must also be compatible. Prefer a build on the console's running Linux, or a deliberately matched Linux toolchain/sysroot. Copying a binary from a newer laptop distribution can fail on libc/libstdc++ versions even when its CPU instructions are compatible. This report does not qualify any prebuilt Ollama package for PS4 Linux.

A bounded follow-up checked `gcc/config/i386/x86-tune-costs.h` and `gcc/config/i386/x86-tune.def` at the same GCC commit. Both contain `btver2` definitions, but neither contains “Jaguar” or an explicit Jaguar-to-`btver2` mapping. That mapping remains **unverified by this source set**; no further files were fetched to pursue it. This does not change the verified `btver2` feature list or substitute for the console's actual CPU flags.

## Read-only target inventory

These commands are intended for an already functioning, user-owned PS4 Linux shell. They have **not been run on the console**:

```sh
uname -a
uname -m
LC_ALL=C lscpu
awk -F: '/^flags/{print $2; exit}' /proc/cpuinfo
free -h
df -h .
cmake --version
c++ --version
ls -l /dev/dri
```

Record `MemAvailable` and the configured CPU/GPU memory split, not just physical memory. Preserve the Linux/kernel/Mesa versions with the results. If `lscpu` or a build dependency is missing, use the distribution's supported packages after identifying the distribution; do not assume all PS4 Linux installations use the same package manager.

## Conservative CPU build template

This is an **unexecuted template**, verified only for option names at the pinned source revision. It assumes a user-prepared checkout at that revision and a working GNU/Clang-style x86-64 Linux compiler. It performs no download. Use a fresh build directory so cached options do not silently carry over from a GPU or modern-laptop build.

```sh
cmake -S /path/to/llama.cpp -B /path/to/llama.cpp/build-ps4-cpu \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS='-march=x86-64 -mtune=generic' \
  -DCMAKE_CXX_FLAGS='-march=x86-64 -mtune=generic' \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DGGML_CPU=ON -DGGML_NATIVE=OFF \
  -DGGML_SSE42=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF \
  -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_BMI2=OFF \
  -DGGML_AVX_VNNI=OFF -DGGML_AVX512=OFF \
  -DGGML_AVX512_VBMI=OFF -DGGML_AVX512_VNNI=OFF -DGGML_AVX512_BF16=OFF \
  -DGGML_AMX_TILE=OFF -DGGML_AMX_INT8=OFF -DGGML_AMX_BF16=OFF \
  -DGGML_CUDA=OFF -DGGML_HIP=OFF -DGGML_VULKAN=OFF \
  -DGGML_BLAS=OFF -DGGML_CPU_ALL_VARIANTS=OFF -DGGML_BACKEND_DL=OFF
cmake --build /path/to/llama.cpp/build-ps4-cpu --target llama-cli llama-server -j 2
```

The two-job build limit is a conservative starting choice, not a measured optimum. Inspect configuration warnings, the CMake cache and `compile_commands.json` for unintended architecture flags. Do not describe this template as tested until the intended source actually builds on the selected Linux installation.

The first profile deliberately disables even AVX/F16C/SSE4.2 to establish a conservative baseline. After the target explicitly reports those features and the baseline executes correctly, a separately recorded profile can turn on `GGML_AVX`, `GGML_F16C` and `GGML_SSE42` while keeping AVX2/FMA/BMI2/AVX512/AMX disabled. This is a proposed optimization experiment. It does not assume every kernel or boot setup exposes usable AVX state, and it does not assert a speed improvement without a benchmark. Use the same source, model, prompt and context when comparing.

## First local inference and server gates

Check the built binaries' `--version` and `--help`. Then try a small, already downloaded and verified GGUF with a bounded prompt. Choose the model from actual free memory and model-format support; begin with a roughly 0.5B–1.5B Q4 candidate if available rather than assuming a 7B model is practical. This model-size suggestion is a planning hypothesis, not a tested capability.

```sh
/path/to/llama.cpp/build-ps4-cpu/bin/llama-server \
  --model /path/to/user-downloaded-model.gguf \
  --ctx-size 2048 --parallel 1 \
  --threads 2 --threads-batch 2 \
  --batch-size 128 --ubatch-size 64 \
  --n-gpu-layers 0 \
  --host 127.0.0.1 --port 8081
```

The server flags are documented in the pinned server README. Context, thread and batch values above are conservative test settings, not benchmark results. Bind the server to loopback and let the laptop reach it through SSH forwarding. A healthy process or `/health` response is only a startup check: submit a real bounded request and record output, peak RAM, swap activity, prompt-processing time, generation rate and errors before calling the worker usable. Keep one request active. Measure whether this device helps the workload; it can remain a non-LLM SSH worker if inference is too slow.

## GPU qualification boundary

If the console already has the tools, run `vulkaninfo` and inspect the actual GPU device, driver, API version, memory heaps and `storageBuffer16BitAccess`. Exclude `llvmpipe`/`lavapipe` from evidence of hardware acceleration. The presence of `/dev/dri` or a functioning graphical desktop is not sufficient.

Only after the real hardware driver passes these observations should a separate `GGML_VULKAN=ON` build and tiny-model offload experiment be attempted. Keep the passing CPU build available. Record backend logs, actual selected device, output correctness and memory behavior. No GPU build or offload experiment was performed here. ROCm/HIP is a distinct driver and device-support question; the existence of `GGML_HIP` does not prove PS4 GPU support.

This CPU report does not address which firmware can boot Linux, prescribe an exploit or kernel flash, or establish compatibility for every original/Slim/Pro console. Those prerequisites need the exact user hardware and boot state.

## Evidence

`evidence.json` contains claim records, exact source URLs, full commit IDs, SHA-256 checksums, bytes and fetch outcomes. All files were fetched through the inherited HTTPS proxy with TLS verification. Every source file is below 1 MB. No endpoint was bypassed. Source inspection and checksum validation are the only checks actually completed; compilation, CPU inference, SSH connectivity and GPU inference remain unrun.
