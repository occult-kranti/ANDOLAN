#!/usr/bin/env python3
"""Actual Godot import/bind/final modifier tape; no GLB reconstruction."""
import argparse, collections, gzip, hashlib, json
from pathlib import Path
import numpy as np

def matrix(value):
    result=np.eye(4);result[:3,:]=np.array(value,dtype=float).T;return result
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(gzip.open(path,'rt').read() if str(path).endswith('.gz') else Path(path).read_text())
def prepare(parts):
    result=[]
    for part in parts:
        selected=part['selected'];rows=np.array([v['bind_weights'] for v in selected])
        result.append(dict(meta=part,rest=np.c_[[v['rest'] for v in selected],np.ones(len(selected))],joints=rows[:,:,0].astype(int),weights=rows[:,:,1],alpha=np.array([v['alpha'] for v in selected]),sides=np.array([v['side'] for v in selected]),indices=np.array([v['index'] for v in selected]),inverses=np.array([matrix(b['inverse']) for b in part['binds']])))
    return result

def analyze(source):
    tape=read(source);sets=[prepare(g) for g in tape['geometry_sets']];rows=[];anchors={};prev=None;max_steps=[]
    for index,sample in enumerate(tape['samples']):
        final=sample['final_pose'];rig=matrix(final['rig_global']);bones={name:matrix(value) for name,value in final['bones'].items()}
        contacts=[c for c in sample['slide_contacts'] if c['normal'][1]>.7]
        plane=max(contacts,key=lambda c:c['normal'][1]) if sample['on_floor'] and contacts else sample['down_ray']
        point=np.array(plane.get('point',plane.get('position')),float);normal=np.array(plane['normal'],float)
        clouds={'L':[],'R':[]};ids={'L':[],'R':[]};screen=[];shader_max=0
        for part_index,part in enumerate(sets[sample['geometry_set']]):
            state=final['parts'][part_index]
            if not state['visible']:continue
            transforms=np.array([bones[b['name']] for b in part['meta']['binds']])@part['inverses']
            posed=np.einsum('nkj,nk->nj',np.einsum('nkij,nj->nki',transforms[part['joints']],part['rest']),part['weights'])
            displacement=part['alpha'][:,None]**2*np.array(state['secondary_offset'])[None,:]
            shader_max=max(shader_max,float(np.max(np.linalg.norm(displacement,axis=1))))
            posed[:,:3]+=displacement
            posed[:,3]=1.0
            world=(rig@posed.T).T[:,:3]
            for side in ['L','R']:
                mask=part['sides']==side;clouds[side].append(world[mask]);ids[side]+=[f'{part_index}:{int(v)}' for v in part['indices'][mask]]
        row=dict(index=index,tick=sample['tick'],physics_frame=final['physics_frame'],fixture=sample['fixture'],on_floor=sample['on_floor'],position=sample['position'],velocity=sample['velocity'],plane=plane,plane_basis='actual_slide_contact' if sample['on_floor'] and contacts else 'actual_down_ray_support_plane',lod=final['lod']['level'],secondary_displacement_max_m=shader_max,locks=final['motion']['foot_locks'],targets=final['foot_targets'],sides={})
        capsule=final['capsules'][0];bottom=matrix(capsule['transform'])[:3,3]-np.array([0,capsule['height']/2,0])
        row['capsule_bottom_plane_distance_m']=float((bottom-point)@normal)
        row['capsule_on_sampled_plane']=bool(sample['on_floor'] and contacts and abs(row['capsule_bottom_plane_distance_m'])<.002)
        all_points=[]
        for side in ['L','R']:
            cloud=np.concatenate(clouds[side]);all_points.append(cloud);dist=(cloud-point)@normal;minimum=int(np.argmin(dist));lock=final['motion']['foot_locks'][side]
            side_row=dict(vertices=len(cloud),minimum_signed_m=float(dist[minimum]),maximum_signed_m=float(dist.max()),minimum_vertex_id=ids[side][minimum],minimum_world=cloud[minimum].tolist(),penetrating_vertices_below_minus_5mm=int((dist<-.005).sum()),locked=lock)
            anchor=anchors.get(side)
            if lock and (anchor is None or anchor['fixture']!=sample['fixture'] or anchor['geometry_set']!=sample['geometry_set']):
                anchor=dict(fixture=sample['fixture'],geometry_set=sample['geometry_set'],index=index,vertex_id=ids[side][minimum],world=cloud[minimum].copy(),target=np.array(final['foot_targets'][side]));anchors[side]=anchor
            elif not lock:anchors.pop(side,None);anchor=None
            if anchor:
                vertex=ids[side].index(anchor['vertex_id']);side_row.update(anchor_start_index=anchor['index'],anchor_vertex_id=anchor['vertex_id'],anchor_original_world=anchor['world'].tolist(),anchor_vertex_world_drift_m=float(np.linalg.norm(cloud[vertex]-anchor['world'])),original_target_drift_m=float(np.linalg.norm(np.array(final['foot_targets'][side])-anchor['target'])))
            if prev and prev['fixture']==sample['fixture'] and prev['ids'][side]==ids[side]:
                delta=np.linalg.norm(cloud-prev['clouds'][side],axis=1);side_row['maximum_vertex_step_m']=float(delta.max())
            row['sides'][side]=side_row;clouds[side]=cloud
        camera=matrix(final['camera_transform']);points=np.concatenate(all_points);camera_points=(np.linalg.inv(camera)@np.c_[points,np.ones(len(points))].T).T[:,:3]
        width,height=final['viewport'];depth=-camera_points[:,2];tan=np.tan(np.deg2rad(final['camera_fov'])/2)
        pixels=np.c_[width/2+camera_points[:,0]/depth*height/(2*tan),height/2-camera_points[:,1]/depth*height/(2*tan)]
        row['sole_projection']={'min':pixels.min(axis=0).tolist(),'max':pixels.max(axis=0).tolist(),'behind':int((depth<=final['camera_near']).sum()),'within_24px':bool((pixels.min(axis=0)>=24).all() and (pixels.max(axis=0)<=np.array([width,height])-24).all() and (depth>final['camera_near']).all())}
        rows.append(row);prev={'fixture':sample['fixture'],'ids':ids,'clouds':clouds}
    flat=[dict(index=r['index'],fixture=r['fixture'],side=side,grounded=r['on_floor'],capsule_on_sampled_plane=r['capsule_on_sampled_plane'],**value) for r in rows for side,value in r['sides'].items()]
    summary={}
    for name,subset in [('all',flat),('grounded',[r for r in flat if r['grounded']]),('locked',[r for r in flat if r['locked']]),('grounded_unlocked',[r for r in flat if r['grounded'] and not r['locked']]),('capsule_contact_locked',[r for r in flat if r['capsule_on_sampled_plane'] and r['locked']]),('capsule_contact_unlocked',[r for r in flat if r['capsule_on_sampled_plane'] and not r['locked']])]:
        summary[name]={'samples':len(subset),'minimum':min(subset,key=lambda r:r['minimum_signed_m']) if subset else None,'maximum_minimum':max(subset,key=lambda r:r['minimum_signed_m']) if subset else None,'samples_penetrating_below_5mm':sum(r['minimum_signed_m']<-.005 for r in subset)}
    summary['max_original_anchor_vertex_drift']=max((r for r in flat if 'anchor_vertex_world_drift_m' in r),key=lambda r:r['anchor_vertex_world_drift_m'])
    summary['max_original_target_drift']=max((r for r in flat if 'original_target_drift_m' in r),key=lambda r:r['original_target_drift_m'])
    summary['max_vertex_step']=max((r for r in flat if 'maximum_vertex_step_m' in r),key=lambda r:r['maximum_vertex_step_m'])
    checks={
        'native_receipt_passes':tape['passed'],
        'actual_imported_selector_nonempty':all(r['sides'][s]['vertices']>1000 for r in rows for s in ['L','R']),
        'actual_visible_near_counts_match_source_selector':all(r['sides'][s]['vertices']==6790 for r in rows if r['lod']==0 for s in ['L','R']),
        'final_pose_and_body_same_physics_frame':all(s['final_pose']['physics_frame']==s['record_physics_frame'] for s in tape['samples']),
        'selected_imported_meshes_have_no_morphs':all(p['blend_shape_count']==0 for g in tape['geometry_sets'] for p in g),
        'mesh_to_rig_identity':all(np.allclose(matrix(p['mesh_to_rig']),np.eye(4),atol=1e-6) for g in tape['geometry_sets'] for p in g),
        'selected_vertices_actual_shader_offset_zero':all(r['secondary_displacement_max_m']==0 for r in rows),
        'native_camera_entire_sole_inside_24px':all(r['sole_projection']['within_24px'] for r in rows),
        'capsule_floor_does_not_prove_skin_clearance':summary['grounded']['samples_penetrating_below_5mm']>0,
    }
    return dict(task='R4-12',source_tape_sha256=sha(source),source_sha256=tape['source_sha256'],checks=checks,summary=summary,rows=rows,geometry_selector=[{'node':p['node'],'surface':p['surface'],'material':p['material'],'counts':dict(collections.Counter(v['side'] for v in p['selected']))} for p in tape['geometry_sets'][0]],scope='CPU skinning of actual imported Godot arrays, actual named binds and final modifier snapshots with same-callback collision/body state. Camera projection is numerical, not pixels. No GPU/render contact or motion acceptance.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output');args=parser.parse_args();result=analyze(args.source);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':result['checks'],'summary':result['summary']},indent=2))
