#!/usr/bin/env python3
"""Source-bound full-triangle checks for the actual Godot-generated G2 mesh."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT/'docs/evidence/graphics-six/G2'
PROBE = PROJECT/'docs/evidence/visual-rounds/round3/role10/geometry_probe.py'
POSE = Path('/workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json')
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('triangles', PROBE)
triangles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triangles)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    started = time.monotonic()
    data = json.loads((OUT/'hero-geometry.json').read_text())
    g = triangles.GLB(PROJECT/'assets/heroes/rama-hero.glb')
    assert sha(g.path) == data['source_glb_sha256']
    assert sha(PROJECT/'scripts/rama_upper_hair_layers.gd') == data['helper_sha256']
    assert sha(PROJECT/'assets/hero-finish/upper-hair-layers.json') == data['guides_sha256']
    vertices = np.array(data['rest_vertices'])
    indices = np.array(data['indices']).reshape(-1,3)
    inverse = g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    names = [g.doc['nodes'][i]['name'] for i in g.doc['skins'][0]['joints']]
    head = names.index('head')
    groups = {}
    for mi, mesh in enumerate(g.doc['meshes']):
        for pi, primitive in enumerate(mesh['primitives']):
            name = g.doc['materials'][primitive['material']]['name']
            if name == 'Swept black hair': continue  # Intentional root overlap with existing hair.
            group = 'bow' if mi == 0 else ('skin_face' if name in ['Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil'] else 'metal_gems' if name in ['Worked warm gold','Recessed antique gold','Polished sapphire'] else 'cloth_leather')
            array = g.array(primitive['attributes']['POSITION'])
            index = g.array(primitive['indices']).reshape(-1,3)
            used, remap = np.unique(index, return_inverse=True)
            groups.setdefault(group,[]).append({'v':array[used], 'tri':remap.reshape(-1,3),
                'j':g.array(primitive['attributes']['JOINTS_0'])[used],
                'w':g.array(primitive['attributes']['WEIGHTS_0'])[used]})
    def pose_group(parts, transforms):
        result=[]
        for part in parts:
            p=np.c_[part['v'],np.ones(len(part['v']))]
            posed=np.zeros((len(p),3))
            for slot in range(4):
                posed+=np.einsum('nij,nj->ni',transforms[part['j'][:,slot]],p)[:,:3]*part['w'][:,slot,None]
            result.append(posed[part['tri']])
        return np.concatenate(result)
    def row(label,transforms):
        posed=(transforms[head]@np.c_[vertices,np.ones(len(vertices))].T).T[:,:3][indices]
        comparisons={name:triangles.compare(posed,pose_group(parts,transforms),band=.015) for name,parts in groups.items()}
        print(label,{name:value['crossings'] for name,value in comparisons.items()},flush=True)
        return {'pose':label,'comparisons':comparisons}
    rows=[row('source_rest',np.repeat(np.eye(4)[None],len(names),axis=0))]
    poses=json.loads(POSE.read_text())
    seen={}
    for sample in poses['samples']:
        transforms=np.array([sample['bone_global_poses'][name] for name in names])@inverse
        key=hashlib.sha256(transforms.astype('<f4').tobytes()).hexdigest()
        if key in seen:
            rows.append({'pose':sample['id'],'identical_bone_transforms_to':seen[key]})
            continue
        seen[key]=sample['id']
        rows.append(row(sample['id'],transforms))
    passed=all(value['crossings']==0 for item in rows for value in item.get('comparisons',{}).values())
    result={'passed':passed,'source_glb_sha256':sha(g.path),'helper_sha256':data['helper_sha256'],
            'geometry_sha256':sha(OUT/'hero-geometry.json'),'probe_sha256':sha(__file__),
            'triangle_dependency_sha256':sha(PROBE),'pose_archive_sha256':sha(POSE),
            'selfcheck':triangles.selfcheck(),'triangles':len(indices),'vertices':len(vertices),
            'source_rest_bounds':{'min':vertices.min(0).tolist(),'max':vertices.max(0).tolist()},
            'collider_triangles':{name:sum(len(p['tri']) for p in parts) for name,parts in groups.items()},
            'rows':rows,'seconds':time.monotonic()-started,
            'scope':'Full-triangle source-rest and archived bone-matrix stress against all nonhair source surfaces, including bow/face/gold/cloth. Archive is historical R2 role05 input, not execution of current G2 actions. No face morph deltas or secondary offsets applied. Existing hair overlap is intentional and omitted; actual fresh head-following checks and rendered ablation remain separate.'}
    (OUT/'hero-clearance.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':passed,'unique_archived_poses':len(seen),'seconds':result['seconds']}))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__': main()
