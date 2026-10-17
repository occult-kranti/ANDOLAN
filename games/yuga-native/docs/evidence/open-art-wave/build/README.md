# Focused authoring build gate

The final shared runner passed **259 checks across ten suites**. Every suite
returned native exit 0, every JSON assertion passed, and the pinned authoring
sources were unchanged through execution. The cloth suite ran **39 actual
Godot resource/lifecycle checks** in its own imported fixture: 38 synthetic
mesh/material cases and one committed material-resource case. No `WARNING:`,
`SCRIPT ERROR:` or `ERROR:` prefixes appeared in the retained run logs.

These are authoring, input-preservation and headless resource checks. They do
not accept hero appearance, an asset replacement, real-time performance,
human feel, online integration or a finished game. The actual candidate
deformation audit and rendered art review have separate evidence.

## Executed checks

| Suite | Passed checks |
| --- | ---: |
| Pinned MikkTSpace adapter | 54 |
| Native component input/process lifetime | 7 |
| UV domain diagnostic | 13 |
| Conservative mesh repair | 24 |
| Exact corner seam repair and path guards | 48 |
| Independent deformation proof fixtures | 26 |
| Independent open-art contracts | 23 |
| Exact CC0 material reproduction | 3 |
| Minimal cloth fixture staging guards | 22 |
| Actual imported cloth material and lifecycle | 39 |

[Full receipt](full-run-r1/summary.json), [individual reports](full-run-r1/reports/),
[separate stdout/stderr](full-run-r1/logs/), and the
[38-file archive manifest](full-run-r1/archive-manifest.json) retain this run.
The archive is 106,637 bytes before its manifest. Generated Godot caches,
copied texture bodies and synthetic user state are omitted; their inputs and
imported texture hashes remain in the receipts.

The [33 runner counterexamples](runner-cases.json) execute real child processes.
They cover native failure hidden by passing JSON, malformed/empty/unexercised
reports, timeout and descendant retirement, partial log retention, excessive
logging, engine errors on either stream, real unittest failures/errors/skips,
and import exit 0 without imported texture payloads. Four checks reject
contradictory duplicate JSON members in summary, nested assertion, builder
and staging receipts. Independent role 15 first exposed this false pass; its
before/after evidence is retained in the sibling `final-review` archive.

[Twelve static conditions](syntax-and-parity.json) verify Python/shell/YAML
syntax and setup/CI parity. The original sixteen-suite quality runner and its
workflow invocation were preserved byte for byte. These static checks are
separate from executed game tests and from a subsequent GitHub Actions run.

## Reproduce

From the repository root, with Godot 4.6.3 standard, a C99 compiler, NumPy
2.3.5 and Pillow 12.3.0 already installed:

```bash
python3 games/yuga-native/tests/authoring_runner_cases.py --report=/tmp/yuga-authoring-counterexamples-FRESH.json
python3 games/yuga-native/tools/run-authoring-checks.py --python python3 --engine godot --cloth-resource --output /tmp/yuga-authoring-FRESH
```

The report and output paths must be fresh. `--list` shows the shared catalog;
`--suite ID` selects a focused suite. Both the cloud setup and native workflow
invoke this same catalog and request the actual material case.

The product's `art/.gdignore` prevents source-art PNG imports. The runner
preserves that file and calls `stage-open-cloth.py` to copy exactly eight
dependencies plus a generated minimal project into its fresh output directory.
It verifies source-copy hashes, stages no ancestor art ignore, performs a
bounded editor import, checks all three real imported texture payloads, then
runs the resource case. Source copies, configuration and stage receipt must
remain unchanged after the test. The fixture uses the compatibility renderer
for resource tests; it is not the rendered hero/world comparison.

The archived run used `/workspace/tooling/yuga-native-python/bin/python` and
`godot`, with CPU affinity 0–1. The runner source digest is
`f756914c39a724461db3251d7b543c6c49597c1b6cab7a3e548d69e6eef19062`;
the counterexample source digest is
`5ec1090eab72c31afa5ffc3bae21e76373598382c5de9ca1be30b6e6dc4e765e`.
Every selected source and supporting authoring input is pinned in the full
receipt. Temporary scripts in boundary tests are deliberate failure fixtures,
not substitutes for Godot, game rendering or imported resource execution.
