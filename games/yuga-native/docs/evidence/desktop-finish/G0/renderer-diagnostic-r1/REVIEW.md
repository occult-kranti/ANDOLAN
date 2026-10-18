# G0 renderer diagnosis — checkpoint 1

The full G2 environment finish still blocks the actual Forward+ first draw. The strongest completed comparison is a one-method diagnostic ablation: replacing `EnvironmentSurfaceFinish.configure` with a no-op produced **two original 1280×960 framebuffers and passed 5/5 observer checks in 88.437 seconds**. The same scene, focus helper, engine, camera, MSAA and Mesa seed otherwise remained unchanged. The original Shader resource is still preloaded, but no custom finish materials are bound to environment meshes. Both originals were directly viewed. They show the actual hero and courtyard; broad pale surfaces and floor stippling remain. This is not a final art fix.

The unchanged G1 groom probe also times out on full G2, arguing against a regression confined to the new focus helper. A narrower shader-body ablation that removes only derivative-derived shallow normal relief still times out. The last shader-cache line is not enough to identify which material owns a blocked native shader version.

| Attempt | Outcome | Original images |
| --- | --- | --- |
| Worker pool 0 | Engine fatal index/count error during first CanvasSdf compile; log signal4, final process exit−6 | 0 |
| Worker pool 1 | 132.744s; no-progress watchdog before first draw completes | 0 |
| Separate render thread | 133.903s; same first-draw boundary | 0 |
| Worker pool32 | Coordinator stopped at30.913s; incomplete, no passing/failing scheduling conclusion | 0 |
| Unchanged prior G1 groom probe | 128.817s; no-progress watchdog | 0 |
| Environment configure no-op | 88.437s; complete,5/5 checks | 2 |
| Only derivative normal-relief block removed | No-progress watchdog, same boundary | 0 |

The successful diagnostic reaches initial-draw completion at41.022s, title anchor at physics27/render13 and training anchor at physics51/render25. Same-callback imported sole minima are titleL+0.572000/R+0.571720mm and trainingL+0.855399/R+0.855557mm above actual rays. These settled anchors do not measure the first provisional-to-measured support transition. The title `idle_support_y` field alone is insufficient to infer a visual foot gap; actual skin/ray data is retained.

All source/cache inventories were verified after these runs. The parent997-entry snapshot is `5d94a7b64b2387f9f8899e82b6a499fb28a93a3ac0a4ace921496af5b589a8ca`; each derivative pins its one changed path. Canonical runtime and product shaders were not edited. The only canonical launcher change adds the supported optional `--render-thread` argument for reproducibility. The old unsupported `--max-threads` flag is not used as a worker limit. Every engine used CPU0,1 affinity, two llvmpipe threads and one OMP/BLAS/MKL thread; fixed30Hz sampling is not hardware FPS.

Official4.6.3-tag sources and exact retrieval hashes are retained under `research/`. They explain supported settings and suggest shader-worker synchronization, but the exact native lock cycle is not proven by a symbolic stack. The local binary reports commit7d41c59c457bd5a245092b4e7eb2d833e3b3f8c3; that raw source URL returned404, while the currently fetched tag resolves35e80b3a…. This is not an engine-integrity failure: fresh official godot-builds release metadata agrees with the retained archiveSHA256d0bc2113…, and both installed Linux binaries match payloadSHA256f64d4ed1…. No engine replacement was performed.

[Receipt](receipt.json) pins every raw log, exact command, helper, derivative source, research input and original image. The two support originals and full observer JSON are under `noenvironment/`. The next authorized diagnostic replaces only the shader body with a minimal texture-preserving body while retaining full bindings. That run is separate from this sealed checkpoint. A production fix and fresh full-quality originals remain required before closing G0.
