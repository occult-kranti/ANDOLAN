# W4 native scheduling review and bounded engine remedy proposal

Read-only review, 2026-10-18. No engine run, engine patch, project setting or canonical shader change was performed. Native lock evidence and exact binary mappings remain in [W4-native-cross-review.md](W4-native-cross-review.md). The warm-cache comparison is W1-owned; it is not cold-launch acceptance.

## Finding and supported settings

The observed main thread owns a ShaderRD Version mutex while waiting for a compilation group. All five workers wait for that same mutex in version_get_shader. Public source explains a capacity cycle: Forward+ pipeline preloads/ubershaders enqueue high-priority PipelineCompilation tasks; ShaderCompilation groups are also high priority. Admitted tasks share a FIFO; high priority does not preempt a running native mutex wait. Shader variant callbacks themselves do not acquire this Version mutex.

WorkerThreadPool::wait_for_task_completion has cooperative queue processing for a pool-thread caller, with protection against waiting for older tasks. Group completion uses a semaphore, including on the main thread; raw pthread_mutex_lock does not cooperate. Thus general work sharing exists but cannot rescue this captured cycle.

The low-priority ratio restricts only low-priority task admission. With five threads and the default .3 ratio, the ordinary cap is one. It does not restrict current high-priority pipeline jobs. Increasing max_threads adds capacity without reserving it. Existing zero-worker probe crashed with index0/count0; one-worker probe timed out. No further pool setting diagnostic is justified by this evidence. No supported async-disable setting was established.

## Smallest defensible engine diagnostic

In PipelineHashMapRD::compile_pipeline, enqueue PipelineCompilation with `false` for the priority argument, leaving ShaderCompilation groups high priority. Do not alter the Version mutex, group lifecycle, pipeline wait/readiness behavior, cache format, shader source or assets.

For the observed graph, with at least two workers and a low-priority admission cap below the pool size, ordinary pipeline jobs cannot occupy every worker: shader callbacks have remaining capacity to finish the group that main awaits. The main wait can therefore complete without unlocking Version prematurely. Pipeline tasks still publish into compiled_queue and get_pipeline(wait=true) still waits for completion. This changes startup/background scheduling and may increase pipeline latency; it changes neither shader math nor the readiness requirement.

This is a proposed diagnostic patch, not a proven production fix. One-worker configurations remain unsafe. Cooperative waits can promote additional low-priority work, and other high-priority consumers of Version are outside this narrow proof. Verify the actual pipeline callback call graph and task population in the unmodified baseline. A global semaphore acquired inside worker callbacks would consume workers while waiting and recreate starvation; an inflight cap must operate at admission, before occupying workers. Simply giving shader groups queue-front priority cannot interrupt workers already blocked.

Releasing Version across the group wait is a larger correctness change: concurrent callers may consume the same group ID, finalize/cache/free shared variant state, or race a Version code update/free. It needs an explicit shared completion/publication/lifetime protocol, not an unlock/relock one-liner. A dedicated shader compilation pool could separate dependencies more robustly, but adds pool ownership/shutdown and bounded-capacity design; it is not the first small diagnostic.

## Official upstream check and identity limits

Installed binary SHA256: f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3. Reported/embedded commit: 7d41c59c457bd5a245092b4e7eb2d833e3b3f8c3. Four raw critical-source requests at that full commit returned404. Public 4.6.3-stable resolves to35e80b3a8822a9df9be390814b62f44c0a9c69e8. Consequently a public-tag build is not an exact reconstruction of the installed binary.

Official GitHub release metadata currently identifies 4.7.2-stable (2026-08-18) as latest, source ed1daf0bf001b61586d9930840f2f1394092c079. The 4.6 branch checked at3b853ac6f016102b16e5056e2c2f33971f228892 and main at81ab961f91066a63bcbf3ec340962bb1a1ada558. All retain the critical pattern: passed-through pipeline priority, Version lock across compile-end, high-priority shader group, and semaphore group wait. The 4.7.2 WorkerThreadPool diff against the reviewed 4.6.3 file only adds two includes. The 4.6 shader change skips disabled cached variant bytes; it does not repair this scheduling cycle. No existing fix was identified in these critical paths. This is a bounded source review, not proof that every upstream issue or driver change was searched, nor that a newer official binary must reproduce the stall. The immutable source URLs and hashes are in the receipt.

A newer official binary is available, but upgrading the whole engine changes more than this cycle. It requires its own source-bound import/runtime/graphics regression comparison. An unmodified pinned-tag source build baseline is essential before attributing a patched-tag success to the priority change.

## Rebuild feasibility and gate

Observed tools: GCC/G++14.2.0, binutils and pkg-config present; SCons absent. About25GiB RAM available, no swap; /tmp has12GiB free and /workspace3.2GiB. Affinity exposed CPUs0–4; parent schedules a four-CPU work budget and exclusive rendering lane. No source archive/build was started.

A separate /tmp source/build tree is plausible with release-style symbols disabled and LTO off, but its fit/time are unmeasured. Keep the installed official engine and symlink untouched. Use a pinned, checksum-recorded source archive, original MIT license, locally installed pinned SCons, and a captured configure/build log. Start with two compiler jobs on assigned free CPUs; never contend with W1's render lane. Reuse one object tree for the unmodified binary then the narrow header rebuild, preserving the baseline binary and patch before rebuilding. Avoid a second full tree. Record actual peak RSS/disk and stop before exhausting scratch space (proposed3GiB free floor, not an engine requirement).

Candidate configuration for later root review: platform=linuxbsd target=editor dev_build=no debug_symbols=no lto=none use_sowrap=yes, bundled dependencies, full GDScript/glTF/text/Vulkan/Forward+ capabilities. Existing pkg-config development entries for X11/audio/fontconfig/udev were absent, but this source defaults to sowrap and bundled Linux headers, so their absence alone does not prove a blocking dependency. A real configure check is still required. Do not silently omit rendering/import modules to make the build fit. Build duration and full output size remain unknown.

Acceptance after explicit assignment: unmodified pinned source cold-cache reproduction first; only then identical patched build with fresh user/Mesa/Godot caches, original complete materials and final runtime. Capture first draw and native task/lock states, two original anchors, visual comparisons and existing affected gates. Repeat a fresh-process cold launch to avoid accepting a lucky schedule. Preserve title/training/world, gold/normal/packed/frieze function, scene disposal and rebuild/version changes. Warm caches are a useful operational workaround with pinned provenance, not the cold graphics gate.

## Seed-runner read-only review

run_focus.py SHA at review:0d0c2e5fdb62b617468c05e6a3bc634038af0920fd4fe796adbd5214fd1ef902. The standard Linux target is correct for current project `YUGA • Confluence`: compositor defaults to user://shader_cache; OS standard user data resolves under XDG_DATA_HOME/godot/app_userdata/<safe application name>. No custom-user-directory setting exists, and this name is unchanged by safe-dir sanitization. It is not the XDG_CACHE_HOME path used for Mesa. Runner copies only .cache files into a fresh isolated user data tree, records file hashes and verifies seed source hashes afterward; it copies no preferences and shares no mutable cache with the source. No current-path/provenance blocker was found. The narrow name parser is not a general replacement for Godot's directory sanitization for arbitrary projects.
