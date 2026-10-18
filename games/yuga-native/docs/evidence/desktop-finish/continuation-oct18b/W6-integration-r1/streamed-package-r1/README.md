# Explicit large-payload streaming

`tools/package-native.py --stream-large-payloads` retains original archive member paths, fixed timestamps/modes, manifest payload records and qualification gates while reading the validated engine and raw PCK directly. Only small launchers/notices/companions/manifests are staged. The default copied mode remains unchanged. No hardlink/reflink, engine chmod or raw-PCK write occurs in streamed mode.

Exact platform names and map census, regular nonsymlink inputs/parents, collision checks, frozen hash/size/inode/mode/mtime/ctime before/during/after reading, exact ZIP CRC/member/hash checks and final source rechecks apply. Merged order uses path components to preserve legacy ordering, including directory/sibling prefix cases. Both tiny ZIP and actual package_all fixtures produce byte-identical Linux/Windows archives and manifest payloads through copied and streamed modes.

Fresh small reflink probes returned Operation not supported twice; no existing asset was touched. Streamed mode therefore uses ordinary read streams rather than shared inodes.

Executed: new streamed cases50/50; existing Linux runtime cases50/50 (including corrupt copied-runtime rejection); native contract package cases21/21; native source checker58/58. These are synthetic archives/source gates, not real export, runtime or publication qualification.

Literal new test command from repository root:

```sh
python3 -B games/yuga-native/tests/streamed_package_cases.py --report /workspace/scratch/yuga-next-W6-r1/fresh-streamed-cases.json --temp-root /workspace/scratch/yuga-next-W6-r1
```

Observed prior expanded large payloads total399,046,696B. Removing only those future copies from the historical budget projects669,039,832B including128MiB export reserve and32MiB growth allowance. This is a planning projection; fresh accepted-source/cache/output growth and separate actual extraction+500MiB render reserve must be audited before any build/run. No real build/engine/export or source snapshot has been started.
