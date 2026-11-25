# EldenCraft terrain-cache source study

This standalone Rust crate preserves the unmodified `worldterrain.rs` source and its 18 upstream unit tests from EldenCraft. The original module builds an incremental cache of surfaces returned by a caller-supplied ray query. It has no dependency on the Elden Ring SDK, game files or native process hooks. The module and its upstream license are pinned by SHA-256 in the test receipt. [Upstream source at commit 22a2ff959dd82f6e694af45eeb637ce849a9c2dc](https://github.com/SocketByte/EldenCraft/blob/22a2ff959dd82f6e694af45eeb637ce849a9c2dc/native/src/worldterrain.rs) · [EldenCraft MIT license](LICENSE.upstream) · [Test receipt](verification.json)

The cache covers a moving 32 × 12 × 32 metre grid using up to six queries per coarse cell. Nearby floor samples are refined to 25 cm columns. A cost estimate adjusts the number of rays between bounded minimum and maximum limits. A published snapshot carries its coverage, revision, surface boxes, materials and query failures. It can contain at most 4,096 boxes. Empty samples are not an exact-mesh or clearance guarantee. [Module API](src/lib.rs)

## Reproduce the isolated test

Use Rust 1.88 or newer. The pinned manifest uses `serde` with the derive feature. Once the locked dependencies are cached, run from the repository root.

```sh
cargo test --locked --offline --manifest-path games/yuga-native/docs/research/elden-ring-world-study/worldterrain-probe/Cargo.toml
```

On 25 November 2026 the 18 upstream tests passed with Rust 1.88.0. They used synthetic rays and deterministic hit geometry. The first build took 7.38 seconds, and the tests completed in 1.41 seconds on this cloud workspace. The copied module matches upstream byte for byte. The small harness has its own lockfile, which pins `serde` to the version in the upstream lockfile and resolves cached procedural-macro dependencies independently. An Elden Ring client and YUGA's playable match were outside the test.

## Next integration experiment

YUGA's Confluence authority already loads authored obstacle boxes and runs Parry queries on the XZ ground plane. Compare that source of truth against the sampled cache using named test routes, ramps and moving obstacles, with a real 3D raycast callback supplied by the target engine. Measure correctness, incomplete coverage, query budget and CPU time before choosing a use for the cache. Any dynamic collider or network integration needs its own authority and synchronization tests. [Current YUGA collision source](../../../../../yuga-rust/src/world.rs)
