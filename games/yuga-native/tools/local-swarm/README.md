# Six-specialist local planning tools

These Python standard-library tools validate a work plan, inspect the local model list, and serialize cooperating foreground commands. They are a planner and a command lock, not an agent launcher or a true mixture-of-experts router. They do not install models, generate tokens, or automatically send work to cloud services.

The target machine's recorded hardware is **8 GB dedicated GPU memory** plus **16 GB shared memory**. Shared memory is not additional VRAM. The proposed shape is six logical specialists sharing one local server and one selected 3B or 7B Q4 model. Those model classes are candidates to qualify, not a guarantee that a particular model, context length, client, or concurrent workload fits. Model weights, context/KV cache, and other GPU processes all affect memory use. Six specialists do not mean six loaded models or six parallel GPU jobs.

Run from this directory with Python 3.10 or later. Linux or WSL is required for the cooperative `fcntl` lock; the planner itself uses portable Python standard-library modules.

```sh
python local_swarm.py validate plan.example.json
python local_swarm.py probe --timeout 3
python -m unittest -v test_local_swarm.py test_gpu_job.py
```

The example deliberately has `model_id: null`. Validation reports `UNRESOLVED`, `runnable: false`, and exit **2**. Invalid plans return exit **1**. A complete set of bindings returns `CONFIGURED` and exit **0**; `runnable` then refers only to plan bindings, while `runtime_qualified` remains false. This does not prove a model exists, fits in memory, generates valid output, or works with an intended client.

The validator requires exactly six unique worker IDs `W1` through `W6` and one each of the roles `QA`, `UI`, `hero`, `world`, `motion`, and `models`. `gpu_parallelism` must be integer `1`. Paths are literal relative POSIX paths; traversal, absolute paths, backslashes, globs, empty components, and overlapping ancestor/descendant ownership are rejected. Example paths are planning placeholders relative to an agreed project root. Ownership is a declaration only: the validator does not enforce actual agent writes, inspect symlink targets, or provide a filesystem sandbox. Resolve real target paths and enforce any needed restrictions in the eventual client.

Both `local` and `cloud` routes must be declared, the default must be `local`, fallback must be `null`, and every worker must explicitly name its route. A worker assigned to `cloud` requires an explicit HTTPS endpoint and non-null model ID. Unused cloud bindings may remain null. A null model ID or endpoint on any **selected** route leaves that plan unresolved; it is never silently replaced. Cloud credentials do not belong in this plan. The planner performs no cloud requests.

The probe accepts only `http://127.0.0.1:11434/v1/models` and the equivalent literal `localhost` spelling; it normalizes the latter to `127.0.0.1` before sending the request. It performs a single GET with no authorization header or request body. Environment proxies are disabled only for this exact loopback operation. Credentials, other hosts/ports/paths, HTTPS, queries, fragments, and redirects are rejected. The socket timeout is bounded to 0.1–10 seconds, and the response is bounded to at most 1 MiB. A model listing is not an inference or performance test. Probe failures return exit **1**; an empty valid model list returns `NO_MODELS` with exit **0**.

To serialize a cooperating foreground command on Linux/WSL, all clients must use the same absolute lock path on a local filesystem supporting `flock`. Its parent directory must already exist and be trusted so another process cannot replace the lock file:

```sh
python gpu_job.py --lock /tmp/yuga-local-gpu.lock -- python -c 'print("cooperating command")'
```

The default is nonblocking. A busy lock returns **75** without starting the command. Ordinary child exit codes are preserved; termination by a signal uses `128 + signal`. The command is executed with `shell=False`; arguments are passed literally. Lock errors return **73**, a missing executable **127**, other launch errors **126**, unsupported platforms **69**, and CLI usage errors **2**. The lock file is retained so its inode remains stable; do not remove or replace it while clients are active.

The child inherits the lock descriptor, so killing only the wrapper does not release the lock while that child retains it. Inheriting descendants can retain the lock too. Release uses close-only semantics: the last inherited descriptor must close before another command can acquire the lock.

This is a cooperative file lock, **not a GPU reservation**. It does not serialize requests that bypass the wrapper, control a running model daemon, unload resident weights, isolate VRAM, or enforce the plan's path ownership. Long-running clients and servers must have their request scheduling qualified separately. Keep wrapped commands in the foreground and have them wait for their GPU work to finish. A process that closes inherited descriptors, or submits work to a daemon that never held the descriptor, can continue computing outside this lock's scope.

No Ollama/Open WebUI/Pinokio client integration is implemented here. Each actual client needs a separate qualification: exact version and model identity, successful local inference, bounded context and peak memory, scheduling behavior, and intended file ownership. See `receipt.json` for executed checks and `SHA256SUMS` for source hashes.
