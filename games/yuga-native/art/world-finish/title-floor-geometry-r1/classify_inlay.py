"""Reproduce the retained inline classification of the primary audit's overlaps."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import audit
p=Path(__file__).resolve().parent
groups=dict(audit.triangles());document=json.loads((p/'audit.json').read_text());regions=defaultdict(list)
for hit in document['horizontal_coplanar_audit']['positive_area_hits']:
    a=groups[hit['a'][0]][hit['a'][1]];b=groups[hit['b'][0]][hit['b'][1]]
    y=float(a[0,1]);na=np.sign(np.cross(a[1]-a[0],a[2]-a[0])[1]);nb=np.sign(np.cross(b[1]-b[0],b[2]-b[0])[1])
    regions[(round(y,8),int(na),int(nb))].append((a,b,hit['area_m2']))
result=[]
for (y,na,nb),rows in regions.items():
    points=np.concatenate([q for row in rows for q in row[:2]])
    result.append({'plane_y_m':y,'cross_normal_signs_Y':[na,nb],'pair_count':len(rows),'pair_area_sum_m2_not_union':sum(row[2] for row in rows),'bounds_min':points.min(axis=0).tolist(),'bounds_max':points.max(axis=0).tolist()})
(p/'inlay-classification.json').write_text(json.dumps({'regions':result,'scope':'All detected positive-area horizontal overlaps are within original Quiet_stone_inlay. Pair areas are not union area. Cross-product signs classify face winding, not measured shaded normals. No arbitrary sloped intersection scan.'},indent=2)+'\n')
