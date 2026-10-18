"""Finite/topology and rest-envelope checks for one authoring clay cage."""
import argparse, hashlib, importlib.util, json
from collections import Counter, defaultdict, deque
from pathlib import Path
import numpy as np

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cage',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();assert not a.output.exists()
    data=json.loads(a.cage.read_text());v=np.array(data['vertices']);faces=data['faces'];checks=[]
    tri=np.array([[f[0],f[i],f[i+1]]for f in faces for i in range(1,len(f)-1)])
    def check(name,passed,**facts):checks.append(dict(name=name,passed=bool(passed),**facts))
    check('all positions finite',np.isfinite(v).all())
    check('indices bounded and face corners distinct',all(len(set(f))==len(f) and min(f)>=0 and max(f)<len(v)for f in faces))
    edges=Counter();direction=defaultdict(list);adj=defaultdict(set)
    for fi,f in enumerate(faces):
        for i,j in zip(f,f[1:]+f[:1]):
            edge=tuple(sorted([i,j]));edges[edge]+=1;direction[edge].append((i,j));adj[i].add(j);adj[j].add(i)
    seen=set();parts=[]
    for start in range(len(v)):
        if start in seen:continue
        q=deque([start]);seen.add(start);count=0
        while q:
            node=q.popleft();count+=1
            for nxt in adj[node]:
                if nxt not in seen:seen.add(nxt);q.append(nxt)
        parts.append(count)
    check('one shared-edge principal cage',len(parts)==1,component_vertex_counts=parts)
    check('every edge has one or two faces',max(edges.values())<=2,boundary_edges=sum(c==1 for c in edges.values()))
    check('shared faces consistently oriented',all(len(x)==1 or x[0]==x[1][::-1]for x in direction.values()))
    boundary=Counter(i for (i,j),count in edges.items()if count==1 for i in (i,j))
    check('shell boundary has no branch vertices',all(c==2 for c in boundary.values()))
    area=np.linalg.norm(np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]]),axis=1)*.5
    check('no zero-area cage triangles',np.all(area>1e-12),minimum_area_m2=float(area.min()))
    check('compact lower knot target',v[:,1].max()<1.902,maximum_y_m=float(v[:,1].max()),original_knot_maximum_y_m=1.9200853109359741)
    source=Path(data['source_glb']);check('accepted source untouched',sha(source)==data['source_glb_sha256'])
    project=Path(__file__).resolve().parents[4]
    probe=project/'docs/evidence/visual-rounds/round3/role10/geometry_probe.py'
    spec=importlib.util.spec_from_file_location('full_triangle_rest_probe',probe);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    comparisons={}
    for label,material_test in [
        ('head_and_face',lambda s:s in ['Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil']),
        ('head_gold_and_gems',lambda s:s in ['Worked warm gold','Recessed antique gold','Polished sapphire']),
        ('upper_clothing_and_quiver',lambda s:s not in ['Swept black hair','Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil','Worked warm gold','Recessed antique gold','Polished sapphire'])]:
        targets=[]
        for ref in data['reference_meshes']:
            if not material_test(ref['material']):continue
            rv=np.array(ref['vertices']);rt=np.array(ref['faces'])
            if label=='head_gold_and_gems':rt=rt[np.any(rv[rt,1]>1.75,axis=1)]
            if len(rt):targets.append(rv[rt])
        if not targets:continue
        comparison=mod.compare(v[tri],np.concatenate(targets),band=.008);comparisons[label]=comparison
        check('rest cage clear '+label,comparison['crossings']==0 and comparison['guaranteed_lower_bound_m']>.0001,comparison=comparison)
    result=dict(schema=1,scope='Rest-space coarse cage only, before evaluated Blender modifiers; no visual/animation/secondary/runtime acceptance.',
                cage_sha256=sha(a.cage),checker_sha256=sha(__file__),probe_sha256=sha(probe),selfcheck=mod.selfcheck(),checks=checks,
                passed=all(c['passed']for c in checks),vertices=len(v),faces=len(faces),triangles=len(tri),comparisons=comparisons,
                deferred=['Actual four-view clay silhouettes','Evaluated subdivision/thickness contacts','All new pose/bow/recoil/secondary gates','UV/LODs/strict import/runtime visual gates'])
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['passed','vertices','faces','triangles']}));print('failures:',[c['name']for c in checks if not c['passed']])
    raise SystemExit(0 if result['passed']else 1)
if __name__=='__main__':main()
