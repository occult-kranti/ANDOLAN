# Cold Forward+ scheduling review — source only

No supported configuration was found that reliably separates the two relevant
task classes in unmodified public Godot `35e80b3a`. The most direct bounded next
experiment is the **already-built one-line pipeline-low-priority executable** with
the exact current package PCK and otherwise identical cold controls. Root authorized
W1 to prepare that separate diagnostic after the current 600-second control ends.
The production dce wrapper and qualified source/package identities remain unchanged.

## Exact source finding

`source-proof.json` binds seven selected files read directly from the pristine
archive, the unchanged dce and retained e69 executable bytes, and W1's current
owned-process stack identity. `source-excerpts.txt` retains original line numbers.
Only the existing pipeline-priority header differs between those seven archive
files and the current diagnostic tree. This is a selected-file recheck, not a new
13,847-file build audit; the historical full build audit is linked below.

| Source | Relevant behavior |
| --- | --- |
| `shader_rd.cpp:555` | `ShaderCompilation` group submission passes **`true`**, i.e. high priority. A conversational claim that this was low priority was corrected with the pristine bytes. |
| `render_forward_clustered.cpp:4553` → `pipeline_hash_map_rd.h:143` | Original pipeline submission passes `p_ubershader` as `p_high_priority`; ubershader pipelines can therefore enter the same high-priority queue. |
| `worker_thread_pool.cpp:247–258, 203–212` | High tasks append to the common FIFO, and workers take its front. High priority is not a separate reserved shader pool. |
| `shader_rd.h:186–201` | The Version recursive mutex remains held through `_compile_version_end`. |
| `shader_rd.cpp:559–565` → `worker_thread_pool.cpp:725–757` | The version waits for its shader group. Group waiting uses a semaphore; it does not steal queued work as the separate task-wait path can. |
| `worker_thread_pool.cpp:818` | Low task admission is capped by `CLAMP(thread_count * ratio, 1, thread_count - 1)`. The public documentation's word “reserved” does not mean that high tasks cannot occupy every worker. |

A source-permitted saturation sequence is: pipeline tasks occupy the finite pool
and block on a Version mutex; its holder waits for shader group tasks that are still
queued behind occupied workers. The current stack is consistent with this: all five
workers return at relative `0x30dc675`, while main waits through `0x3c1803b` →
`0x30134e7` → `0x30dc8eb`. W4's prior relocation-aware binary/object mapping identifies
the functions and lock/wait sites. **The fresh stack contains no mutex pointer/owner
or queue snapshot**, so it does not freshly prove that every wait is on the same
Version instance or that the awaited group remains queued. No attach was performed
by W3 and no ownership result from the older f64 process is transferred here.

## Why the configuration alternatives do not establish a fix

- `threading/worker_pool/low_priority_thread_ratio` changes low-task admission;
  both relevant original classes above can be high, so the ratio cannot separate
  them. Raising it is not a shader-worker reservation.
- `threading/worker_pool/max_threads` changes the saturation threshold. Additional
  workers can change an interleaving, but finite high pipeline work can still occupy
  them. The old 32-worker attempt was stopped early and is not a result.
- Zero workers is unsafe in this threaded build: `_post_tasks` falls back to the
  calling thread, while `_process_task:57–58` indexes `threads` using the caller's
  pool index. This agrees with the retained earlier zero-worker fatal result;
  it is not a recommended synchronous-compilation switch. One worker and a separate
  render thread already failed the earlier bounded workload.
- `threads.reserve(5)` reserves vector storage for possible pump threads; it is not
  five spare compilation workers. Runtime recovery for pump-task counts does not
  reserve a worker for this mutex/group dependency.
- No general Forward+ async-compilation-off project setting appears in the inspected
  `ProjectSettings.xml` and initialization paths. Shader/pipeline cache settings
  do not change the lock/queue contract. Supplying warm caches is a separate condition,
  not evidence that a first cold launch works. Unsupported `--max-threads` is not used.

The existing one-line change makes `PipelineHashMapRD` submissions low priority,
while shader groups remain high. Under normal admission with at least two workers,
pipeline tasks alone cannot occupy all worker slots. Readiness waits, shader code,
render features, materials and output publication are retained. This addresses the
specific saturation hypothesis without reducing renderer quality. Cooperative task
waits may promote low work, other high clients exist, and other pipeline submission
classes remain; **universal deadlock freedom is not established**.

## Retained candidate and bounded test

Candidate: `/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority`

- SHA256 `e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e`
- 85,447,128 bytes; archived actual version `4.6.3.stable.custom_build`.
- Public source `35e80b3a8822a9df9be390814b62f44c0a9c69e8`; pristine archive SHA256
  `fe5b661d0e7b062201ebffc8740cb309ff96c4f1edca79cdb0ecda50ff2af8d5`.
- Existing build: `python3 -m SCons -j4 platform=linuxbsd target=template_debug
  dev_build=no debug_symbols=no lto=none use_sowrap=yes disable_path_overrides=no`.

The [archived build receipt](../template-priority-build-r1/receipt.json) is
`2ff2289520bd43e74d55810b40d47c64b61197bf956f14c4a09140b7b0d4bfc8`;
[one-line patch](../template-priority-build-r1/proposed.patch) is
`df9032765f5fd348f3e1ef7f35c6de9148a74734172f94efe562e1753db8b4d7`;
[finished verification](../template-priority-build-r1/finished-build-verification.json)
is `67d485da0bd2d78cbb2cd304723f0bd10774626c44c47de814483d396826a134`.
The candidate's full bytes were independently rehashed now; its version command,
build and full historical source audit were not rerun.

W1's diagnostic must preserve the exact current PCK/source, Forward+ settings,
materials/shaders, command/observer, CPU affinity and driver environment. Both Godot
and Mesa caches/preferences must start fresh. Only the retained engine identity
changes; any wrapper admission change must be confined to a separately named
diagnostic wrapper. Use the already declared bounded clock/watchdog, retain failures,
and require actual first 3D draw plus the intended controls/images before a success
claim. A later repeat cold process is needed to challenge scheduling sensitivity.

The [earlier patched 120-second run](../template-priority-cold-r1/REVIEW.md) reached
active LLVM work but produced no image within that bound. A later long patched run
completed, and the [unmodified 600-second control](../template-baseline-cold-600-r1/REVIEW.md)
also completed. Those observations disprove “the patch was necessary” and prevent
crediting one future success as a universal repair. They do not erase the separately
observed mutex/group-wait failures. This review performs no new engine, build, source
mutation, process attachment or package qualification.
