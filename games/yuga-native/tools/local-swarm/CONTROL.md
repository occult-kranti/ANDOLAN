# Explicit local and SSH job control

`control.py` extends [the existing planner and GPU lock](README.md). It runs exact commands sequentially, records bounded output and exit status, and can quarantine an explicit inventory of generated files. It uses Python 3.10+ standard-library modules; Git is additionally required for cleanup. A lead using Codex, Claude Code or Kimi Code can write the same reviewed manifest and invoke the same CLI.

This is a command runner, not an autonomous agent platform or model router. It does not choose models, spend API credits, download weights, create servers, authenticate clients or qualify hardware. Read the [build-farm guide](../../docs/GAME_BUILD_FARM.md) for the larger workflow and [six project skills](../../../../.agents/skills/README.md) for role responsibilities.

## Plan and run a bounded job

From the repository root, inspect the example without executing its commands:

```sh
python3 games/yuga-native/tools/local-swarm/control.py jobs \
  games/yuga-native/tools/local-swarm/control.example.json \
  --workspace /absolute/path/to/ANDOLAN
```

Select an exact job and a new receipt for execution:

```sh
python3 games/yuga-native/tools/local-swarm/control.py jobs \
  games/yuga-native/tools/local-swarm/control.example.json \
  --workspace /absolute/path/to/ANDOLAN \
  --job w1-control-tests --execute \
  --receipt .local-swarm/receipts/w1-tests-001.json
```

Repeat `--job ID` to run a chosen sequence in that order. A failed job stops the batch; its receipt lists jobs not started. An execution without explicit job selection or a fresh receipt path is blocked. Dry runs write nothing. The example's status commands inspect source state; they do not implement or accept game work. Its model-list probe fails honestly if no local service is available, and a model list does not prove inference.

Receipts contain the manifest/source SHA-256, UTC time, workspace, exact arguments, working directory, target, ownership declaration, exit code, elapsed time and retained stdout/stderr. Each output stream retains at most 64 KiB and reports truncation. The SSH JSON transport has a separate bounded response allowance. Keep credentials out of arguments, manifests and command output: the helper does not redact arbitrary child output. Receipt files are never overwritten automatically.

Each job has `id`, `worker`, literal `argv`, relative `cwd`, `writes`, and `timeout_seconds` (0.05–3600). `target` defaults to `local`; `gpu` defaults to false. Paths reject traversal, absolute/drive syntax, globbing, protected credential names and symlink components. `cwd: "."` means the declared workspace. Use absolute executable paths in a production manifest when PATH resolution is ambiguous. `fallback` must be `null`.

The six worker declarations must have unique IDs, correct roles and non-overlapping `allowed_paths`. Ownership overlap and cleanup's tracked-file ancestry checks use case folding on every platform, conservatively rejecting case-only aliases on Linux too. Source-root and protected-component guards also ignore case. This is a portability precaution, not evidence of execution on Windows. Each job's `writes` must lie inside its worker's exclusive paths; `[]` declares no repository writes. Replace the example's scratch ownership with the actual assigned files before editing production code. The lead retains shared ledgers, source manifests and integration changes.

| Queue | Role | Suitable first operation |
| --- | --- | --- |
| W1 | QA | Run bounded tests; review actual source/output evidence independently |
| W2 | UI | Repair one reproduced screen/input issue in assigned files |
| W3 | hero | Author one accepted art/rig change through a queued Blender job |
| W4 | world | Build one environment pilot with collision/navigation verification |
| W5 | motion | Change one animation/contact issue with authority-clock checks |
| W6 | models | Pin downloads/builds, qualify one model/client, package source and evidence |

Ownership declarations are **not an OS sandbox**. An arbitrary executable, shell explicitly named in `argv`, imported code or agent client can access anything permitted to its OS account and can ignore `writes`. The helper passes argv literally with `shell=False`; it cannot make untrusted commands safe. Use the client's actual sandbox, an appropriate account or container when isolation is required. Review commands and source before execution. Do not run concurrent owners against the same mutable files, including during cleanup.

## One laptop GPU, explicit remote CPU work

The confirmed RTX 4070 Laptop has **8 GB dedicated VRAM plus 16 GB shared system memory**. Six roles share one qualified model backend; this does not mean six loaded models or 24 GB VRAM. Queue heavy GPU work and measure actual context/weights/editor headroom.

`gpu: true` wraps a local foreground command with the existing `gpu_job.py` and the common `<workspace>/.local-swarm/gpu.lock`. Linux/WSL and a filesystem supporting `flock` are required. Every cooperating caller must use that same lock. Busy returns 75 without launching the command. The lock does not unload a model daemon, reserve VRAM, schedule external requests or stop a command that bypasses it. Finish/unload resident model work before a heavy render when required by measured capacity. Commands must stay in the foreground until their work finishes.

The optional PS4 target means an **existing original PS4 Linux CPU worker**, not a qualified GPU backend. No real PS4 is connected or tested by these helper tests. Configure and verify your normal OS SSH alias and host key outside the manifest; keep passwords/private keys/client credentials out of it. Use an ordinary remote user: the bootstrap rejects root. This helper does not install Linux or alter console firmware.

For a declared SSH alias, add the actual remote checkout path:

```json
"ssh_targets": {"ps4-dev": {"workspace": "/home/your-user/ANDOLAN"}}
```

Set a selected job's `target` to `ps4-dev`, choose its remote executable (for example `python3`) and use `gpu: false`. Before executing, install this **exact** `control.py` at `games/yuga-native/tools/local-swarm/control.py` in that remote checkout. The worker needs Python 3.10+ and every dependency required by the selected job. SSH execution additionally requires `--allow-ssh`. All remote selections are checked for this flag before any earlier local job begins.

The OS SSH invocation forces `BatchMode=yes`, `StrictHostKeyChecking=yes`, bounded connection/keepalive settings and a declared alias. It runs one fixed, shell-quoted Python bootstrap. Job argv/cwd/workspace travel in JSON on stdin; they never enter the remote shell command string. The installed helper must match the local source SHA-256 and have no symlink components. This verifies helper identity, not the whole remote checkout or executables; pin and verify those separately.

Jobs are sequential within one invocation. Multiple invocations are not a distributed scheduler. A lost SSH connection can leave the remote outcome unknown; receipts say `unknown_inspect_before_retry`. Inspect the remote process and outputs before retrying a non-idempotent job. Remote stdout is returned to the local receipt; no remote durable receipt or exactly-once delivery is claimed.

On POSIX, timeout or Ctrl-C terminates the foreground process group. An intentionally detached process can escape that group. On native Windows, timeout terminates only the direct child; use WSL for the documented process-group and GPU-lock behavior. The command must manage any daemon or external work it starts. Child exit codes appear in the receipt; the CLI returns 0 for passed/dry-run, 1 for a failed/partial execution and 2 for blocked input/setup. A child timeout is recorded as 124 and interruption as 130.

## Downloads and recoverable cleanup

A download/build job uses the same explicit argv/cwd contract. Invoke an already reviewed script with exact publisher revision, destination, expected hash and time/disk budget; verify the artifact before using it. The helper provides no implicit URL selection or trust in a generated installer. External service use and charges remain a deliberate client/job choice; there is no automatic cloud fallback.

The cleanup example deliberately contains a nonexistent filename and invalid placeholder identity. Replace it with an exact inventory of inactive generated outputs after checking ownership and recoverability. Neither an untracked file nor a matching extension establishes that a file is disposable. Keep original art, unique captures, meaningful failure evidence, saves and source.

```sh
python3 games/yuga-native/tools/local-swarm/control.py cleanup \
  my-reviewed-cleanup.json --workspace /absolute/path/to/ANDOLAN
python3 games/yuga-native/tools/local-swarm/control.py cleanup \
  my-reviewed-cleanup.json --workspace /absolute/path/to/ANDOLAN \
  --execute --receipt .local-swarm/receipts/quarantine-001.json
```

Cleanup is local-only. It requires the workspace to be the Git root, an explicit `generated_roots` list, and exact per-file path, byte size, SHA-256 and `classification: "generated"`. It blocks tracked files and gitlink descendants, nested Git repositories, known source/editable-file suffixes, common source trees, credential paths, control receipts/locks, symlinks, directories, duplicate entries and outside-root paths. This conservative guard does not classify every possible source format; an owner must still review the inventory.

Eligible files move to a fresh `.local-swarm/quarantine/<run-id>/<original-relative-path>`. The receipt preserves both paths and identities, allowing an owner to move each file back after checking the destination is free. A partially failed run records files already moved; the operation is not transactional. Quarantine preserves bytes on the same filesystem: **`freed_bytes` is zero**. There is no purge or broad deletion command. A later intentional storage reclamation needs its own reviewed recovery/retention procedure; see [workspace cleanup guidance](../../../../docs/WORKSPACE_AND_CLEANUP.md).

## Verification scope

```sh
python3 -B -m unittest discover \
  -s games/yuga-native/tools/local-swarm -p test_control.py -v
```

Tests use temporary workspaces and Git repositories. They execute literal arguments, failures, timeout, bounded-output and quarantine/receipt paths; they challenge traversal, ownership, credential/source guards, missing targets and implicit SSH. Transport tests inspect the SSH command and execute the installed bootstrap locally with a simulated non-root identity. They do not connect to a PS4, validate a user's credentials, run a model or establish GPU/game performance.
