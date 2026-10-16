# Dependency audit

Checked on **16 October 2026 at 00:50 UTC** against the current lockfile. Package pins and the lockfile were left unchanged.

- **Production audit:** `npm audit --omit=dev --json` exited 0 with zero reported vulnerabilities.
- **Full audit:** three high-severity package entries arise from one development-only chain: `vite-plugin-singlefile@2.3.3 → micromatch@4.0.8 → braces@3.0.3`.
- **Advisory:** [GHSA-vfj7-8cjw-p6xm / CVE-2026-93687](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm), stack exhaustion from deeply nested brace patterns. All published braces versions through 3.0.3 are affected; the advisory and registry provide **no patched version** at this check.
- **Suggested downgrade rejected:** npm proposes `vite-plugin-singlefile@0.9.0`, whose Vite peer range is `^2.9.5`; this is incompatible with the current Vite 8.3.4 pin. No forced downgrade was applied.
- **Current reachability:** standalone packaging uses the plugin's default empty `inlinePattern`. The installed plugin calls the glob matcher only when that array is nonempty. No arbitrary game input reaches this build configuration, and no runtime exposure is evidenced. The advisory remains recorded; this observation does not patch the package.
- **Runtime packaging:** the Dockerfile prunes development dependencies before copying dependencies into the runtime stage. A production audit is narrower than a complete application security review.

Retain the existing compatible pins pending an upstream fix, or replace standalone packaging in a separate tested change if a clean build-tool audit becomes a release requirement. Exact dependency declarations, evidence, hashes and the scope of the source inspection are in [the detailed audit](research/DEPENDENCY_AUDIT.md), with [full audit JSON](research/evidence/npm-audit-current.json), [production audit JSON](research/evidence/npm-audit-production.json) and [check metadata](research/evidence/npm-audit-context.json).
