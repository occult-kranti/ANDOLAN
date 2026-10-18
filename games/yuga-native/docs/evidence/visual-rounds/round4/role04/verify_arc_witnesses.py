from pathlib import Path
import ast, json, hashlib
import numpy as np
O=Path(__file__).resolve().parent
P=O.parents[1]/'round3/role04/verify_witnesses.py'
# Import only the independent strict segment/triangle function, without running its report producer.
tree=ast.parse(P.read_text()); body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cuts']; exec(compile(ast.Module(body=body,type_ignores=[]),str(P),'exec'))
j=json.loads((O/'wrist-arc-feasibility.json').read_text()); rows=[]
for s in j['samples']:
 w=s['gaps']['cloth'].get('minimum_bound_pair')
 hits=cuts(np.array(w['first_xyz']),np.array(w['bow_xyz'])) if w else []
 rows.append({'id':s['id'],'strict_segment_triangle_intersections':hits,'crossing_confirmed':bool(hits)})
report={'scope':'Source pose experiment only; no actual imported modifier, shader or pixel judgment. These strict witnesses reject the one bounded +15 degree correction before controller staging.', 'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),P,O/'wrist-arc-feasibility.json']},'witnesses':rows,'confirmed_remaining_crossings':sum(r['crossing_confirmed']for r in rows)}
(O/'wrist-arc-witnesses.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
