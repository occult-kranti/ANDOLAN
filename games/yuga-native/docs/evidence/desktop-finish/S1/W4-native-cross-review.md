# S1 / W4 — Independent native wait-path cross-review

Read-only cross-review of W1's actual native debugger capture. [The compact receipt](W4-native-cross-review.json) pins the binary, raw debugger/mutex evidence, exact addresses/literals, unwind ranges and public-source hashes. No engine run, cache mutation, canonical shader change or further material ablation was performed.

The main wait function is identified directly in the stripped binary: unwind range `0x480a4e0..0x480abef` contains cross-references to `wait_for_group_task_completion`, `core/object/worker_thread_pool.cpp` and `Invalid Group ID.`. Main's `0x480a6a5` frame is the return from the semaphore condition-wait call, inside a zero-count retry loop.

Its caller, unwind range `0x3d3d530..0x3d3d9ed`, reads a nonzero group-task slot from Version offset `0x68`, calls that proven worker-group wait at `0x3d3d592`, then clears the slot and checks group variants at Version offset `0x88`. This strongly corresponds to public `ShaderRD::_compile_version_end`: wait for group completion, zero the task ID, validate variants and save a valid cache result. Main's captured return address is `0x3d3d597`.

Independent inspection also agrees with W1's `version_get_shader` identification: function/header literals are referenced within unwind range `0x3dc08f0..0x3dc0c65`; its worker path calls `pthread_mutex_lock` at `0x3dc09cd` and its main path calls the version-completion routine at `0x3dc0b93`. The public method holds the version mutex across that wait.

W1's live 40-byte mutex receipt identifies owner TID **220843**, the main thread. All five WorkerThread threads wait on that same mutex; main waits for worker-group completion. This is concrete evidence of a native lock/worker-starvation cycle. It does not establish that shader derivatives are generally unsupported, that a material's arithmetic is invalid, or that more shader reductions repair the engine scheduling path.

The exact binary reports `7d41c59c4`; the separately fetched public `4.6.3-stable` tag resolves to `35e80b3a8822a9df9be390814b62f44c0a9c69e8`. Address/literal/unwind evidence belongs to the actual binary; source-body correspondences retain this identity qualification. No exact-build symbols were invented.

Actual binary strings and the fetched public ProjectSettings expose shader/pipeline **disk-cache** controls, worker count/ratio and rendering thread model. No supported shader/pipeline asynchronous-disable switch was identified. Turning disk cache off does not remove the public compilation-group queue/wait path. A successful exact-source `_load_from_cache` hit returns before compilation is queued, so an independently pinned existing cache can support a bounded warm-cache workaround; it cannot qualify a fresh cold launch or an uncached shader revision. Worker-count and thread-model changes likewise remain unproven remedies.

W1/root owns the next decision and actual graphics gate. Preserve the unmodified intended materials, the failed full-textured candidate and these native receipts. No new engine experiment or source modification is requested by this cross-review.
