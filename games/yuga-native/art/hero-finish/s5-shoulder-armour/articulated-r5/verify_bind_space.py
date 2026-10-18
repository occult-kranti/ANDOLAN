"""Compare actual imported skin data with source before revising articulation."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(PARENT))
from build_armour import GLB, SOURCE_SHA, sha
from check_source import transform, compare


def skin(v,j,w,matrices):
    points=np.c_[v,np.ones(len(v))];result=np.zeros((len(v),3))
    for k in range(j.shape[1]):result+=np.einsum('nij,nj->ni',matrices[j[:,k]],points)[:,:3]*w[:,k,None]
    return result


def main():
    out=HERE/'bind-space-verification-r1.json';assert not out.exists()
    native=HERE/'native-bind-r1';d=json.loads((native/'bind.json').read_text())
    assert d['complete'] and d['source_sha256']==SOURCE_SHA
    g=GLB(ROOT/'assets/heroes/rama-hero.glb');p=g.doc['meshes'][2]['primitives'][11];a=p['attributes']
    sv=g.array(a['POSITION']);sj=g.array(a['JOINTS_0']);sw=g.array(a['WEIGHTS_0']);st=g.array(p['indices']).reshape(-1,3)
    nv=np.fromfile(native/'skin-array-0.bin','<f4').reshape(-1,3)
    nj=np.fromfile(native/'skin-array-10.bin','<i4').reshape(len(nv),-1)
    nw=np.fromfile(native/'skin-array-11.bin','<f4').reshape(len(nv),-1)
    nt=np.fromfile(native/'skin-array-12.bin','<i4').reshape(-1,3)
    assert len(sv)==len(nv) and len(st)==len(nt)
    names=[g.doc['nodes'][index]['name'] for index in g.doc['skins'][0]['joints']]
    assert names==[x['name'] for x in d['bones']]==[x['name'] for x in d['binds']]
    sib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
    nib=np.array([x['matrix'] for x in d['binds']])
    assert np.array_equal(d['mesh_global'],np.eye(4)) and np.array_equal(d['rig_global'],np.eye(4))
    # Match actual imported vertices by coordinates and influence values, not
    # by the reorderable vertex index. Exact source duplicates are canonicalized.
    neighbors=cKDTree(sv).query_ball_point(nv,2e-6)
    mapping=[];errors=[];canonical=[];keys={}
    for v,j,w in zip(sv,sj,sw):
        key=(v.tobytes(),tuple(sorted((int(k),float(q)) for k,q in zip(j,w) if q>0)))
        if key not in keys:keys[key]=len(keys)
        canonical.append(keys[key])
    for i,ids in enumerate(neighbors):
        assert ids
        nweights={int(k):float(q) for k,q in zip(nj[i],nw[i]) if q>0}
        possible=[]
        for source in ids:
            sweights={int(k):float(q) for k,q in zip(sj[source],sw[source]) if q>0}
            error=max(abs(sweights.get(k,0)-nweights.get(k,0)) for k in sweights.keys()|nweights.keys())
            possible.append((error,source))
        error,source=min(possible);mapping.append(source);errors.append(error)
    mapping=np.array(mapping);canonical=np.array(canonical)
    position_error=float(np.linalg.norm(sv[mapping]-nv,axis=1).max());weight_error=float(max(errors))
    assert position_error<2e-6 and weight_error<3.1e-5
    source_faces=collections.Counter(tuple(sorted(x)) for x in canonical[st])
    native_faces=collections.Counter(tuple(sorted(x)) for x in canonical[mapping[nt]])
    topology_equal=source_faces==native_faces
    assert topology_equal
    tape=ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz'
    retained=json.loads(gzip.decompress(tape.read_bytes()))
    assert retained['source_before']==retained['source_after'] and retained['source_before']['res://assets/heroes/rama-hero.glb']==SOURCE_SHA
    sample=next(x for x in retained['samples'] if x['id']=='dawn_volley-pitch0.0-step35')
    poses=np.array(sample['bone_globals'])
    source_posed=skin(sv,sj,sw,poses@sib);native_posed=skin(nv,nj,nw,poses@nib)
    posed_error=float(np.linalg.norm(source_posed[mapping]-native_posed,axis=1).max())
    report=json.loads((PARENT/'representative-r4.json').read_text())
    old_witness=next(x for x in report['pose_replay']['rows'] if x['id']==sample['id'])['contacts']['Rama warm skin']
    source_triangle=np.array(old_witness['witness_other_triangle'])
    # Locate the actual imported triangle by its three posed points.
    tree=cKDTree(source_triangle);dist,match=tree.query(native_posed[nt])
    candidates=np.flatnonzero((dist.max(1)<.00005)&(np.sort(match,axis=1)==np.array([0,1,2])).all(1))
    assert len(candidates)>0
    native_triangle=native_posed[nt[candidates[0]]]
    witnessed=compare(np.array(old_witness['witness_hair_triangle'])[None,:,:],native_triangle[None,:,:],band=.001)
    assert witnessed['crossings']==1
    result={'schema':1,'passed':True,'scope':'Actual cached near skin arrays/bind poses versus source, then mathematical LBS on retained actual pose. No GPU skin readback, new asset import or continuous native action claim.',
            'sources':{str(p):sha(p) for p in [Path(__file__),native/'bind.json',native/'run.json',ROOT/'assets/heroes/rama-hero.glb',tape,PARENT/'representative-r4.json']},
            'vertices':len(nv),'triangles':len(nt),'all_164_bone_and_bind_names_exact':True,'mesh_and_rig_identity_transforms':True,
            'maximum_rest_vertex_distance_m':position_error,'maximum_weight_component_difference':weight_error,'canonical_triangle_multiset_equal':topology_equal,
            'maximum_inverse_bind_component_difference':float(abs(nib-sib).max()),'maximum_native_import_pose_vertex_difference_m':posed_error,
            'sample':sample['id'],'actual_imported_triangle_index':int(candidates[0]),'actual_imported_triangle_vertex_ids':nt[candidates[0]].tolist(),
            'actual_imported_skin_triangle':native_triangle.tolist(),'armour_triangle':old_witness['witness_hair_triangle'],'reproduced_actual_imported_skin_crossing':witnessed,
            'joint_pivots':[{k:bone[k] for k in ['index','name','parent','global_rest']} for bone in d['bones'][48:53]]}
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['passed','vertices','triangles','maximum_rest_vertex_distance_m','maximum_weight_component_difference','maximum_inverse_bind_component_difference','maximum_native_import_pose_vertex_difference_m']},indent=2))


if __name__=='__main__':main()
