# Public production dashboard — source-bound verification

The production dashboard was successfully published by [Actions run 40023890649](https://github.com/occult-kranti/ANDOLAN/actions/runs/40023890649), from exact source **`069ab775c66fff838c4aed149912dd483df4d564`**. Both build and deploy jobs completed successfully. This worker performed read-only checks; it did not deploy, rerun workflows or change the public site.

- [Public dashboard](https://occult-kranti.github.io/ANDOLAN/production/)
- [Public 3D source viewer](https://occult-kranti.github.io/ANDOLAN/production/viewer/)
- [Public Rama GLB](https://occult-kranti.github.io/ANDOLAN/production/media/rama-generated.glb)

All **19** selected dashboard/viewer/source/notice and existing-route requests returned HTTP 200. Thirteen dashboard static files—including HTML, app/CSS, the viewer's compiled JS/CSS, notices and GLB—matched the exact committed source bytes. The public GLB is **4,480,716 bytes**, SHA-256 `0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b`. No runtime hero or animation acceptance follows from publication of this unrigged source.

## Snapshot identity and live limits

The captured [publication receipt](captured/production/publication.json) records dashboard source `069ab775c66fff838c4aed149912dd483df4d564` and browser baseline `176b6f8e71fcffd3d570d96e66643d8cb9893603`. The [public data capture](captured/production/status.json) explicitly has **`mode: snapshot`**, collected **23 October 2026 at 20:59:35 UTC**.

That data's observed working tree was `7c7259260782c181b29276c4429353f9445f2a22`, `dirty: true`, before the production checkpoint commit. This is preserved rather than falsely relabeled as a post-commit live observation. The deployment source is separately bound by the publication receipt. Pages serves saved data; it does not keep this cloud's telemetry service, CPU model or public GPU queue running. No persistent GPU access is established by this publication.

## Existing game routes were preserved

These five public entries returned 200 and byte-matched the supplied locally assembled baseline:

| Entry | URL |
| --- | --- |
| ANDOLAN | `https://occult-kranti.github.io/ANDOLAN/` |
| Browser YUGA | `https://occult-kranti.github.io/ANDOLAN/yuga/` |
| Mechanics lab | `https://occult-kranti.github.io/ANDOLAN/yuga/lab/` |
| Lane lab | `https://occult-kranti.github.io/ANDOLAN/yuga/lane-lab/` |
| Control lab | `https://occult-kranti.github.io/ANDOLAN/yuga/control-lab/` |

The complete supplied baseline census has 90 files; its canonical census hash also equals the public publisher receipt. This verifies the publisher's additive preservation of the assembled baseline and these five independently fetched entry bytes. This worker did not download all 90 public baseline files, execute the older games, or establish equality to some earlier historical deployment. The baseline staging directory contains archived source rather than its own `.git`; its pinned source identity is supplied by the workflow and receipt, while local byte comparisons and the full census are retained independently.

## Separate native CI outcome

[Native foundation run 40023890588](https://github.com/occult-kranti/ANDOLAN/actions/runs/40023890588), on the same initial source, **failed** at “Validate production dependency ledger and its counterexamples.” Root was notified immediately and owns diagnosis, correction and any successor run. This report does not relabel that run as passing because the independent dashboard deployment succeeded.

## Retained evidence

[Verification summary](verification.json), [public response/byte bindings](public-byte-bindings.json), [baseline census](baseline-census.json), initial Actions metadata, jobs, bounded monitoring history and the exact public snapshot/publication JSON are retained. Bundled baseline HTML totals about 28 MB; these response bodies, the GLB and JS bundles are not duplicated in this research handoff. Their measured public hashes bind either to the exact source commit or the provided baseline census. Full downloaded bodies remain in this worker's scratch publication directory; the [duplicate-exclusion receipt](duplicate-exclusion.json) records the baseline-body decision.

`python3 verify.py` checks retained receipts, exact historical Git source bytes, baseline response/census hash bindings and snapshot labels without network/GPU work. It does not re-download the public files or independently recreate omitted response bodies. A future shallow checkout needs the normal historical Git source object available for the exact-source comparisons. Publication verification is a dated HTTP/byte check; browser interaction and visual evidence belong to the separate UI/runtime review.
