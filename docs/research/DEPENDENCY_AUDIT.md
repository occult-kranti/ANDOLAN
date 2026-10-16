# Dependency audit during final integration

Checked against the current lockfile on 16 October 2026 UTC. No package, lockfile or application source was changed during this review. Exact lockfile/package hashes and observation time are in [npm-audit-context.json](evidence/npm-audit-context.json).

`npm audit --json` returned three high-severity package entries. These represent **one underlying advisory in a development-only dependency chain**, rather than three independent vulnerabilities:

```text
vite-plugin-singlefile@2.3.3  direct devDependency
└── micromatch@4.0.8         transitive, dev:true
    └── braces@3.0.3         transitive, dev:true
```

The underlying advisory is [GHSA-vfj7-8cjw-p6xm / CVE-2026-93687](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm): stack-exhaustion denial of service through deeply nested brace patterns, affecting braces `<=3.0.3`. The npm audit response reports CVSS v3 score 7.5; the inspected GitHub advisory page additionally displays CVSS v4 score 8.7. Both classify it high. The page explicitly lists **patched versions: None**, published 18 September 2026 and reviewed 2 October 2026.

`npm audit --omit=dev --json` exited 0 with **zero reported vulnerabilities**. This is the production dependency audit result, not a claim that the application has no security defects. Full audit output: [all dependencies](evidence/npm-audit-current.json), [production dependencies](evidence/npm-audit-production.json).

## Fixed-version assessment

The registry was queried directly with `npm view` for current versions, dependency declarations and peer ranges:

| Package | Locked / registry latest | Fixed compatible pin available? |
| --- | --- | --- |
| braces | 3.0.3 / 3.0.3 | No. Published versions stop at 3.0.3, which remains affected. |
| micromatch | 4.0.8 / 4.0.8 | No. Its declared braces dependency is `^3.0.3`. |
| vite-plugin-singlefile | 2.3.3 / 2.3.3 | No. It depends on micromatch `^4.0.8`. |

Npm suggests `vite-plugin-singlefile@0.9.0` as a SemVer-major change because that older release does not carry this chain. Its peer dependency is **Vite `^2.9.5`**, while ANDOLAN pins **Vite 8.3.4**. That is an incompatible downgrade, not a supported patch for this build. Do not use `npm audit fix --force` to perform it.

## Present exposure and disposition

The application uses this plugin only in `vite.standalone.config.ts`, with `viteSingleFile()` and no custom patterns. The installed plugin defaults `inlinePattern` to `[]`; its two `micromatch.isMatch` calls are guarded by `inlinePattern.length`. Consequently this configuration does not call the affected glob-matching path. That is a source-derived reachability observation, not a patched package or a reason to erase the audit finding. Do not introduce untrusted nested glob patterns into build configuration.

The ordinary client/server build uses the separate Vite configuration. The Docker build performs `npm prune --omit=dev` before copying `node_modules` into its runtime stage, excluding this development chain by design. The production audit above independently confirms no advisory in the production dependency graph; inspecting a deployed image is a separate verification step owned by release integration.

The compatible disposition for the frozen build is to retain the exact existing pins, record the unresolved development advisory and keep production dependencies pruned. Follow up when an upstream fixed release becomes available, or deliberately replace standalone packaging in a separate tested change if a zero-finding build-tool inventory is required. No compatible fixed pin currently exists, and none was invented or installed by this review.
