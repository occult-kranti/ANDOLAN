# Independent public r4 byte audit — ready, public execution unrun

The exact r4 five-file/source reference is pinned in `reference.json`. The tool defaults to plan-only and has no network path without `--execute-public-download`. Root must trigger that command only after publication; no upload or publication operation exists here.

After root's trigger, from `/workspace/ANDOLAN`:

```sh
taskset -c 4 python3 -B games/yuga-native/docs/evidence/desktop-finish/published/W5-download-preparation-r1/audit_public.py --execute-public-download --output /workspace/scratch/yuga-desktop-r4-public-audit-r1
```

The output must be fresh. The audit reads the public release API, verifies fixed ID416367666/tag/source96d5, resolves the public Git tag independently, and downloads all five exact URLs with ordinary TLS checks. Public API digests/sizes, locally qualified pins and downloaded checksums must agree. Download failures and partial audit state are retained; no proxy/TLS bypass or retry loop is provided.

All ZIP member CRCs, names, inventory, size, SHA256 and executable modes are inspected. Both PCK directories independently match all543 expected per-entry sizes/SHA256 and storedMD5 fields. Linux's11 source/build proof bytes and exact one-patch e69 runtime declaration remain distinct from the officialf64 exporter; Windows's official runtime stays explicit. Neither engine runs.

Disk handling is bounded: retain the three small downloaded manifests/checksums and complete audit; download one ZIP at a time, validate fully, then remove only that newly downloaded verified ZIP before fetching the next. Maximum ZIP plus small files is under148MB; the tool requires512MiB initial scratch reserve. It does not extract archives, duplicate PCKs, alter local source/caches or delete prior outputs. A failed ZIP remains for diagnosis. PCK parsing uses a bounded70.2MB in-memory payload.

Preparation performed: AST parse and default plan-only command; local parser rehearsal passed both existing qualified archives (45Linux/34Windows members,543PCK entries each), and two altered per-entrySHA negative controls rejected. This4-check local rehearsal is not a public download audit. No network or engine was used. EarlierI3 public verification informed the method; its old public bytes/results are not reused as r4 evidence.

Public execution remains **UNRUN**. Even a later byte-identity pass will not claim new downloaded-build gameplay, Windows execution, physicalGPU performance, listening or final art acceptance.
