"""Independent CPU skinning of actual Godot-imported face/body/eye arrays.

The runtime sampler owns all actual writer updates; independent asymmetric
targets here are offline combinations, never a second runtime face writer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import ConvexHull, cKDTree

PROJECT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PROJECT / 'art/hero-rama-face'))
from validate_face import front_hits, read, accessor


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_meshes(report):
    data = json.loads(Path(report['imported_mesh_path']).read_text())
    meshes = {}
    for item in data['meshes']:
        m = dict(item)
        m['p'] = np.array(m['positions'], dtype=np.float64)
        m['tri'] = np.array(m['indices'], dtype=np.int64).reshape(-1, 3)
        m['j'] = np.array(m['joints'], dtype=np.int64).reshape(len(m['p']), -1)
        m['w'] = np.array(m['weights'], dtype=np.float64).reshape(len(m['p']), -1)
        m['inv'] = np.array([b['inverse'] for b in m['binds']])
        m['d'] = np.array(m['shape_positions'], dtype=np.float64)
        if len(m['d']) and m['blend_shape_mode'] == 0:
            m['d'] -= m['p'][None, :, :]
        meshes[(m['node'], m['material'])] = m
    return meshes


def skin(mesh, poses, morph):
    p = mesh['p'].copy()
    for name, delta in zip(mesh['shape_names'], mesh['d']):
        p += float(morph.get(name, 0)) * delta
    matrices = np.array([poses[b['name']] for b in mesh['binds']]) @ mesh['inv']
    homogeneous = np.column_stack([p, np.ones(len(p))])
    result = np.zeros((len(p), 3))
    for slot in range(mesh['j'].shape[1]):
        value = np.einsum('nij,nj->ni', matrices[mesh['j'][:, slot]], homogeneous)
        result += value[:, :3] * mesh['w'][:, slot, None]
    return result


def canonical(points, poses, rests):
    transform = np.array(rests['head']) @ np.linalg.inv(np.array(poses['head']))
    return (np.column_stack([points, np.ones(len(points))]) @ transform.T)[:, :3]


def target(left, right):
    return dict(zip(['rama_blink_left', 'rama_blink_right',
                     'rama_blink_half_left', 'rama_blink_half_right'],
                    [max(0, 2*left-1), max(0, 2*right-1),
                     1-abs(2*left-1), 1-abs(2*right-1)]))


def point_map(points):
    result = {}
    for i, p in enumerate(points):
        result.setdefault(tuple(np.round(p, 6)), []).append(i)
    return result


def paired_indices(first, second, coordinates):
    af, bf = point_map(first), point_map(second)
    a, b, missing = [], [], []
    for c in coordinates:
        key = tuple(np.round(c, 6))
        if key not in af or key not in bf:
            missing.append(list(c))
        else:
            a.append(af[key][0]); b.append(bf[key][0])
    return np.array(a, dtype=int), np.array(b, dtype=int), missing


def eye_scan(face, eyes, face_tri, eye_tri, meta):
    result = {}
    for side, center_ in meta['eyeOriginsBlender'].items():
        x, y, z = center_
        center = np.array([x, z, -y])
        gaps, visible = [], 0
        for dx in np.linspace(-.010, .010, 9):
            for dy in np.linspace(-.003, .004, 7):
                e = front_hits(eyes, eye_tri, center[0]+dx, center[1]+dy)
                f = front_hits(face, face_tri, center[0]+dx, center[1]+dy)
                if not len(e):
                    continue
                gap = float(np.max(f)-np.max(e)) if len(f) else -1.0
                visible += gap < -.0002
                gaps.append(gap)
        result[side] = {'actual_eye_rays':len(gaps), 'visible_rays':visible,
                        'min_front_skin_minus_eye_m':min(gaps) if gaps else None,
                        'gaps_m':gaps}
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--baseline-runtime', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--held-ring', type=Path)
    p.add_argument('--candidate-glb', type=Path, help='Explicit source-geometry replay when candidate import is not yet available.')
    p.add_argument('--baseline-glb', type=Path, default=PROJECT/'assets/heroes/rama-hero.glb')
    a = p.parse_args()
    actual = json.loads(a.runtime.read_text())
    baseline = json.loads(a.baseline_runtime.read_text())
    meshes, controls = read_meshes(actual), read_meshes(baseline)
    meta_path = PROJECT / 'art/hero-rama-face/candidate.json'
    meta = json.loads(meta_path.read_text())
    face_key, body_key = ('RamaFace','Rama warm skin'), ('RamaHero','Rama warm skin')
    lip_key = ('RamaHero','Natural lips')
    f, b, lips = meshes[face_key], meshes[body_key], meshes[lip_key]
    cf, cb, cl = controls[face_key], controls[body_key], controls[lip_key]
    checks = []
    def check(name, ok, **details):
        checks.append({'name':name,'passed':bool(ok),'details':details})
        print(('PASS ' if ok else 'FAIL ')+name)
    if a.candidate_glb:
        _, bd, bb = read(a.baseline_glb)
        _, cd, cbinary = read(a.candidate_glb)
        max_mapping = 0.0
        exact_contract = True
        for key, mesh in meshes.items():
            primitives=[]
            for doc, binary in [(bd,bb),(cd,cbinary)]:
                node=next(n for n in doc['nodes'] if n.get('name')==key[0])
                primitive=next(p for p in doc['meshes'][node['mesh']]['primitives'] if doc['materials'][p['material']]['name']==key[1])
                primitives.append(primitive)
            bp, cp = primitives
            old=accessor(bd,bb,bp['attributes']['POSITION'])
            new=accessor(cd,cbinary,cp['attributes']['POSITION'])
            distance, indices=cKDTree(old).query(mesh['p'])
            max_mapping=max(max_mapping,float(distance.max()))
            exact_contract=exact_contract and np.array_equal(accessor(bd,bb,bp['indices']),accessor(cd,cbinary,cp['indices']))
            for attr in ['JOINTS_0','WEIGHTS_0']:
                exact_contract=exact_contract and np.array_equal(accessor(bd,bb,bp['attributes'][attr]),accessor(cd,cbinary,cp['attributes'][attr]))
            for bt, ct in zip(bp.get('targets',[]),cp.get('targets',[])):
                for attr in bt:
                    exact_contract=exact_contract and np.array_equal(accessor(bd,bb,bt[attr]),accessor(cd,cbinary,ct[attr]))
            mesh['p'] += new[indices]-old[indices]
        check('Candidate source replay preserves topology skin and all morph payloads',exact_contract and max_mapping<1e-7,maximum_GLTF_to_imported_vertex_mapping_error_m=max_mapping,scope='Source candidate rest-position delta applied to actual baseline imported vertices; no claim that candidate importer executed.')
    check('Baseline actual runtime checks passed; candidate pose schedule is replayed' if a.candidate_glb else 'Runtime checks executed and passed on both exact imported assets',
          actual['passed'] and baseline['passed'] and actual['count']>=73 and baseline['count']>=73,
          actual_checks=actual['count'], baseline_checks=baseline['count'])
    check('Imported mesh export hash matches runtime report', sha(actual['imported_mesh_path'])==actual['imported_mesh_sha256'])
    coordinates = [[x,z,-y] for x,y,z in [r['position'] for r in meta['boundary']]]
    fi, bi, missing = paired_indices(cf['p'], cb['p'], coordinates)
    check('All 146 source attachments map into actual imported face and body',len(fi)==146 and not missing, matched=len(fi), missing=missing)
    neutral_seam = float(np.max(np.linalg.norm(f['p'][fi]-b['p'][bi],axis=1)))
    morph_boundary = float(np.max(np.linalg.norm(f['d'][:,fi],axis=2)))
    check('Evaluated geometry keeps attachment rest positions and all four morph boundary deltas',neutral_seam<2e-6 and morph_boundary<2e-6,rest_gap_m=neutral_seam,morph_delta_m=morph_boundary)
    check('Four imported morph deltas retain baseline correspondence',f['shape_names']==cf['shape_names'] and f['d'].shape==cf['d'].shape and np.max(abs(f['d']-cf['d']))<3e-7,maximum_delta_difference_m=float(np.max(abs(f['d']-cf['d']))))
    # Baseline coincident lip/body vertices are actual attachment witnesses.
    lp, bp = point_map(cl['p']), point_map(cb['p'])
    common = sorted(set(lp)&set(bp))
    li = np.array([lp[k][0] for k in common],dtype=int)
    lbi = np.array([bp[k][0] for k in common],dtype=int)
    check('Original lip/body attachment witnesses exist',len(common)>0,matched=len(common))
    if a.held_ring:
        held = json.loads(a.held_ring.read_text())
        points = np.array(held['positions_gltf_m'])
        cfmap = point_map(cf['p']); selected = []
        for pos in points:
            selected.extend(cfmap.get(tuple(np.round(pos,6)),[]))
        moved = float(np.max(np.linalg.norm(f['p'][selected]-cf['p'][selected],axis=1))) if selected else 1
        morph = float(np.max(np.linalg.norm(f['d'][:,selected],axis=2))) if selected else 1
        check('Exact 288 source quad held-ring positions remain fixed in candidate and morphs',len(points)==288 and len(selected)>=288 and moved<2e-6 and morph<2e-6,source_vertices=len(points),exported_copies=len(selected),candidate_delta_m=moved,morph_delta_m=morph,source_sha256=sha(a.held_ring))
    rest = actual['bone_global_rests']
    max_rest_error = max(float(np.max(np.linalg.norm(skin(m,rest,{})-m['p'],axis=1))) for m in meshes.values())
    weighted_rest_error = max(float(np.max(np.linalg.norm(skin(m,rest,{})-m['p']*m['w'].sum(axis=1)[:,None],axis=1))) for m in meshes.values())
    check('CPU rest skinning matches imported quantized weights and inverse binds',weighted_rest_error<2e-6,maximum_unweighted_rest_difference_m=max_rest_error,maximum_weighted_rest_error_m=weighted_rest_error,minimum_imported_weight_sum=min(float(m['w'].sum(axis=1).min())for m in meshes.values()),scope='No renormalization: imported 16-bit skin weight sums can be below one. Compare rest to position times actual sum; retain raw deviation rather than masking it.')
    pairs = [(s, baseline['samples'][i]) for i,s in enumerate(actual['samples'])]
    for left,right in [(0,0),(.25,0),(.5,0),(.75,0),(1,0),(0,.25),(0,.5),(0,.75),(0,1),(.25,.75),(.75,.25),(.5,.5),(1,1)]:
        s={'id':f'offline_individual_L{left}_R{right}','morph_weights':target(left,right),'bone_global_poses':rest,'offline_combination':True}
        pairs.append((s,s))
    eye_keys=[('RamaHero',name) for name in ['Warm sclera','Deep brown iris','Pupil']]
    eye_tri=[];offset=0
    for key in eye_keys:
        eye_tri.append(meshes[key]['tri']+offset);offset+=len(meshes[key]['p'])
    eye_tri=np.concatenate(eye_tri)
    sclera=controls[('RamaHero','Warm sclera')]['p']
    hulls={side:ConvexHull(sclera[sclera[:,0]*sign>0]).equations for side,sign in [('L',1),('R',-1)]}
    samples=[]
    max_seam=max_lip=max_drift=0.0; finite=True; inverted=0; uncovered=[]
    maximum_added_inset=0.0; new_inside=0; worse_inside=0
    for s,control in pairs:
        posed={key:skin(mesh,s['bone_global_poses'],s['morph_weights']) for key,mesh in meshes.items()}
        cp={key:skin(mesh,control['bone_global_poses'],control['morph_weights']) for key,mesh in controls.items()}
        finite = finite and all(np.isfinite(v).all() for v in posed.values())
        seam=float(np.max(np.linalg.norm(posed[face_key][fi]-posed[body_key][bi],axis=1)))
        lip=float(np.max(np.linalg.norm(posed[lip_key][li]-posed[body_key][lbi],axis=1))) if len(li) else 1
        pface=canonical(posed[face_key],s['bone_global_poses'],rest)
        cface=canonical(cp[face_key],control['bone_global_poses'],baseline['bone_global_rests'])
        eye=canonical(np.concatenate([posed[k] for k in eye_keys]),s['bone_global_poses'],rest)
        ceye=canonical(np.concatenate([cp[k] for k in eye_keys]),control['bone_global_poses'],baseline['bone_global_rests'])
        scan=eye_scan(pface,eye,f['tri'],eye_tri,meta)
        control_scan=eye_scan(cface,ceye,cf['tri'],eye_tri,meta)
        globe_intersections={}
        for side,sign in [('L',1),('R',-1)]:
            planes=hulls[side]; mask=cf['p'][:,0]*sign>0
            original=(cface[mask]@planes[:,:3].T+planes[:,3]).max(axis=1)
            candidate=(pface[mask]@planes[:,:3].T+planes[:,3]).max(axis=1)
            new_count=int(np.count_nonzero((candidate<-.0002)&(original>=-.0002)))
            worsened=int(np.count_nonzero((candidate<-.0002)&(candidate<original-.0002)))
            extra=float(max(0,np.max(original-candidate)))
            new_inside=max(new_inside,new_count); worse_inside=max(worse_inside,worsened); maximum_added_inset=max(maximum_added_inset,extra)
            globe_intersections[side]={'baseline_inside_vertices':int(np.count_nonzero(original<-.0002)),'candidate_inside_vertices':int(np.count_nonzero(candidate<-.0002)),'new_inside_vertices':new_count,'worsened_beyond_0_2mm':worsened,'maximum_extra_inset_m':extra,'baseline_maximum_inset_m':float(max(0,-original.min())),'candidate_maximum_inset_m':float(max(0,-candidate.min()))}
        triangle=pface[f['tri']]; ctr=cface[cf['tri']]
        normals=np.cross(triangle[:,1]-triangle[:,0],triangle[:,2]-triangle[:,0])
        cnormals=np.cross(ctr[:,1]-ctr[:,0],ctr[:,2]-ctr[:,0])
        new_inversions=int(np.count_nonzero((normals*cnormals).sum(axis=1)<=0))
        inverted=max(inverted,new_inversions)
        newly_visible={side:max(0,scan[side]['visible_rays']-control_scan[side]['visible_rays']) for side in scan}
        complete={side:s['morph_weights'].get('rama_blink_left' if side=='L' else 'rama_blink_right',0)>.999999 for side in scan}
        for side in scan:
            if complete[side] and scan[side]['visible_rays']>0: uncovered.append([s['id'],side,scan[side]['visible_rays']])
            scan[side].pop('gaps_m');control_scan[side].pop('gaps_m')
        drift=float(np.max(np.linalg.norm(pface-cface,axis=1)))
        max_seam=max(max_seam,seam);max_lip=max(max_lip,lip);max_drift=max(max_drift,drift)
        samples.append({'id':s['id'],'offline_combination':s.get('offline_combination',False),'skinned_vertices':sum(len(x)for x in posed.values()),'attachment_gap_m':seam,'lip_attachment_gap_m':lip,'candidate_face_delta_m':drift,'new_triangle_inversions':new_inversions,'cornea':scan,'baseline_cornea':control_scan,'new_visible_rays':newly_visible,'sclera_vertex_inset':globe_intersections})
    check('All sampled CPU skinned positions remain finite',finite,samples=len(samples),vertices_per_sample=samples[0]['skinned_vertices'])
    check('All posed face/body attachment gaps stay below 0.05 mm',max_seam<.00005,maximum_gap_m=max_seam)
    check('All posed original lip/body attachment gaps stay below 0.05 mm',max_lip<.00005,maximum_gap_m=max_lip,witnesses=len(common))
    check('Candidate face has no inverted triangles relative to corresponding baseline poses',inverted==0,maximum_new_inversions=inverted)
    check('Full individual/combined blinks cover actual sampled eye surfaces',not uncovered,uncovered=uncovered,rays_per_eye=63,depth_tolerance_m=.0002)
    check('Candidate does not expose new cornea rays in matching baseline samples',all(not any(s['new_visible_rays'].values()) for s in samples),extra_visible_samples=[{'id':s['id'],'new_visible_rays':s['new_visible_rays']} for s in samples if any(s['new_visible_rays'].values())])
    check('Candidate creates no new sampled vertex penetration beyond 0.2 mm into actual sclera hull',new_inside==0 and worse_inside==0,maximum_new_inside_vertices=new_inside,maximum_worsened_existing_vertices=worse_inside,maximum_additional_inset_m=maximum_added_inset,scope='Convex hull of actual imported sclera, in head-rest coordinates. Retains existing hidden inset vertices; vertex test does not prove exhaustive triangle collision freedom.')
    result={'task':'R2-05','passed':all(c['passed']for c in checks),'count':len(checks),'checks':checks,'sample_count':len(samples),'actual_runtime_samples':len(actual['samples']),'offline_asymmetric_and_combined_samples':13,'samples':samples,'runtime_sha256':sha(a.runtime),'baseline_runtime_sha256':sha(a.baseline_runtime),'asset_sha256':actual['source_pins']['res://assets/heroes/rama-hero.glb'],'baseline_asset_sha256':baseline['source_pins']['res://assets/heroes/rama-hero.glb'],'analyzer_sha256':sha(__file__),'maximum_candidate_face_delta_m':max_drift,'scope':'CPU linear blend skinning of actual imported meshes at real runtime pose/target samples, plus offline independent-target combinations. Frontal actual-eye triangle rays are bounded visibility/closure checks, not exhaustive triangle collision or visual acceptance. Existing open-cornea obstruction is retained and separately reported by source validator. Held288 proof included only when exact source quad ring provided.'}
    if a.candidate_glb:
        result.update(asset_sha256=sha(a.candidate_glb),actual_runtime_samples=0,replayed_baseline_runtime_samples=len(actual['samples']),candidate_import_executed=False,scope='Exact candidate GLB rest-position deltas replayed through actual baseline imported skin weights and 37 runtime poses, plus 13 offline target combinations. Source skin/topology/morph invariance verified. This is candidate CPU deformation evidence, not a candidate Godot import or rendered acceptance. Eye triangle rays and vertex-in-sclera-hull checks are bounded, not exhaustive collision tests.')
    a.report.write_text(json.dumps(result,indent=2)+'\n')
    return 0 if result['passed'] else 1


if __name__=='__main__':
    sys.exit(main())
