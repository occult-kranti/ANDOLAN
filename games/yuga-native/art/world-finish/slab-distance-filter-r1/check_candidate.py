#!/usr/bin/env python3
"""Source boundary and analytic endpoint checks; never execute a renderer."""
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
rows = []


def check(name, passed, detail=None):
    rows.append(dict(name=name, passed=bool(passed), detail=detail))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def detail(footprint, slab):
    span = max(footprint[0] / slab[0], footprint[1] / slab[1])
    t = min(1.0, max(0.0, (span - .20) / (.65 - .20)))
    return 1 - t * t * (3 - 2 * t)


original = (HERE / "world_ground_common.original.gdshaderinc").read_text()
candidate = (HERE / "world_ground_common.candidate.gdshaderinc").read_text()
manifest = json.loads((HERE / "source-manifest.json").read_text())
check("canonical original remains byte-identical", sha(ROOT / "scripts/world_ground_common.gdshaderinc") == manifest["original_sha256"])
check("candidate matches staged source pin", sha(HERE / "world_ground_common.candidate.gdshaderinc") == manifest["candidate_sha256"])
prefix = "\tfloat variation ="
check("distance/joint and cell-address code unchanged", original.split(prefix)[0] == candidate.split("\t// Screen-space footprint")[0])
check("roughness, route/court masks and shared include suffix unchanged", original.split("float world_paving_roughness")[1] == candidate.split("float world_paving_roughness")[1])
check("shader derives cell footprint from continuous fragment position", "vec2 cell_footprint = fwidth(p) / slab_size;" in candidate and "fwidth(tiled)" not in candidate)

slabs = [(1.65, 1.10), (2.40, 1.20), (2.2, 2.2)]
check("all three authored slab sizes retain full colour at >=5px per cell", all(detail((x*.20, y*.20), (x,y)) == 1 for x,y in slabs))
check("all three authored slab sizes reach mean at <=1/0.65px per cell", all(detail((x*.65, y*.65), (x,y)) == 0 for x,y in slabs))
weights = [detail((i*.01, i*.01), (1,1)) for i in range(101)]
check("weight remains finite/bounded and falls monotonically", all(math.isfinite(v) and 0 <= v <= 1 for v in weights) and all(a >= b for a,b in zip(weights,weights[1:])))
check("grazing footprint filters when either axis is subpixel", detail((.01, 1), (2.4, 1.2)) == 0 and detail((2, .01), (2.4, 1.2)) == 0)

# Endpoint algebra is independent of cell hash values. This verifies the
# declared colour relation, not GPU floating-point sin/hash output or fwidth.
lo, hi = (.88,.96,1.0), (1.05,.99,.88)
mean = tuple((a+b)*.5 for a,b in zip(lo,hi))
near_ok = True
far_ok = True
for random_brightness in [0,.125,.5,.875,1]:
    for random_mineral in [0,.125,.5,.875,1]:
        for weather in [-.12,0,.12]:
            mineral = tuple(a+(b-a)*random_mineral for a,b in zip(lo,hi))
            variation = (random_brightness-.5)*.18
            old = tuple(m*(1+variation+weather) for m in mineral)
            near = tuple(m*(1+variation*1+weather) for m in mineral)
            far = tuple(m*(1+variation*0+weather) for m in mean)
            near_ok &= old == near
            far_ok &= far == tuple(m*(1+weather) for m in mean)
check("near endpoint preserves original random colour algebra", near_ok)
check("far endpoint independent of both per-cell random inputs", far_ok, {"neutral":mean})
check("counterexample: unfiltered full detail cannot satisfy far endpoint", any(abs(a-b) > .01 for a,b in zip(lo,mean)))

result = dict(passed=all(row["passed"] for row in rows), count=len(rows), checks=rows,
              scope="Source boundaries and CPU analytic endpoint contract only. Does not execute/compile GLSL, measure actual derivatives, establish visual quality, shimmer or physical GPU performance.")
(HERE / "checks.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({"passed":result["passed"], "count":len(rows)}))
raise SystemExit(0 if result["passed"] else 1)
