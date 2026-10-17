# Read-only UV and corner diagnosis

`rama-baseline-domains.json` analyzes the exact repaired R4f source `de61dc4c…`.
`summary.json` separates measured geometry/UV facts from source-authoring
mechanisms and visibility, which has not been rendered here.

All 18,360 UV-degenerate faces have exactly collinear UV coordinates. 17,512
cover nonzero surface area; this is more than a harmless collection of collapsed
geometric poles. For example, their primitive rest-area shares are 7.61% for
brocade, 2.13% for hero gold and 2.06% for cobalt cloth. These figures are local
surface area, not screen coverage or proof of a visible seam.

Source text shows tube/lock end caps using a constant longitudinal UV, sphere
grids duplicating poles, and a Solidify operation that may create uncharted side
walls. The joined GLB does not retain original object-to-face ranges, so those
mechanisms cannot establish the intended use or visibility of an individual
exported face without an editable-source inspection.

The six valid corner conflicts range from 0.0067° to 10.94°. The report includes
all affected corner data and exact float32 direction differences. Independent
native calls reproduce each of the three zero tangents even on an isolated
face. At those corners the source normal is nearly tangent to the triangle's
plane. Reproducing the pinned Mikk projected-edge formula in float32 gives a
clamped cosine of one and a zero angular contribution. This is a bounded
conditioning diagnosis, not instrumentation of the library's internal branch
or permission to replace the source normal or tangent arbitrarily.

There are 5,256 coincident vertex-pair faces under the weaker skeletal/morph
POSITION proof. All also have equal COLOR_0, while **zero** have every attribute
and morph row byte-identical. The report does not grant universal removal
permission; shader-specific removal has its own exact shader and source pins.

```sh
python3 games/yuga-native/art/hero-rama-repair/diagnose_domains.py \
  --self-test --report=/absolute/fresh/uv-tests.json
python3 games/yuga-native/art/hero-rama-repair/diagnose_domains.py \
  --source=/absolute/source.glb --report=/absolute/fresh/domains.json \
  --mikk-report=/absolute/source-matched-mikk-report.json \
  --corners=/absolute/source-matched-corner-frames.npz \
  --library=/absolute/mikk-build/libyuga_mikktspace.so
```

The source-matched Mikk report, corner archive and library are optional for a
geometry/UV-only read. `--author-source=/absolute/generator.py` adds text-only
source pins and relevant lines. The thirteen self-tests cover clean charts,
nonzero cap area, exact coincidence, changing weights and morphs, strict record
identity, tiny area and analytic derivatives. No asset, UV, index, runtime or
shader changes are made.
