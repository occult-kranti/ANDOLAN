#!/usr/bin/env python3
"""Independent scalar evaluation of actual imported contact witnesses."""
import gzip,hashlib,json,math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROLE12=HERE.parent/'role12'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def apply(t,p):return [t[3][axis]+sum(t[c][axis]*p[c] for c in range(3)) for axis in range(3)]
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def posed(part,vertex,final,part_index):
    result=[0.,0.,0.]
    for bind_index,weight in vertex['bind_weights']:
        if weight==0:continue
        bind=part['binds'][bind_index]
        value=apply(final['bones'][bind['name']],apply(bind['inverse'],vertex['rest']))
        for axis in range(3):result[axis]+=value[axis]*weight
    offset=final['parts'][part_index]['secondary_offset']
    for axis in range(3):result[axis]+=offset[axis]*vertex['alpha']**2
    return apply(final['rig_global'],result)

def run():
    tape_path=ROLE12/'actual-imported-contact-r2.json.gz';analysis_path=ROLE12/'imported-contact-analysis.json'
    tape=json.loads(gzip.decompress(tape_path.read_bytes()));analysis=json.loads(analysis_path.read_bytes())
    result={'task':'R4-10','source_tape_sha256':sha(tape_path),'role12_analysis_sha256':sha(analysis_path),'source_sha256':tape['source_sha256'],'checks':[],'witnesses':[],'scope':'Independent scalar imported-vertex evaluation and actual finite-step witnesses. No new renderer or authored motion candidate. No continuous C0/C1 or ordinary-speed acceptance.'}
    def check(name,condition,details=None):result['checks'].append({'name':name,'passed':condition,'details':details or {}})
    worst=analysis['summary']['capsule_contact_unlocked']['minimum'];wi=worst['index'];side=worst['side'];cache={}
    indices=sorted(set([0,5,13,21,22,23,wi-1,wi,wi+1,166,170,212]))
    for index in indices:
        sample=tape['samples'][index];final=sample['final_pose'];parts=tape['geometry_sets'][sample['geometry_set']];cloud={'L':{},'R':{}}
        for pi,part in enumerate(parts):
            if not final['parts'][pi]['visible']:continue
            for vertex in part['selected']:cloud[vertex['side']][f'{pi}:{vertex["index"]}']=posed(part,vertex,final,pi)
        cache[index]=cloud
        declared=analysis['rows'][index];plane=declared['plane'];point=plane.get('point',plane.get('position'));normal=plane['normal'];witness={'index':index,'fixture':sample['fixture'],'physics_frame':final['physics_frame'],'on_floor':sample['on_floor'],'capsule_bottom_plane_distance_m':declared['capsule_bottom_plane_distance_m'],'sides':{}}
        for side_ in ['L','R']:
            distances={key:dot(sub(value,point),normal) for key,value in cloud[side_].items()};key=min(distances,key=distances.get);value=distances[key]
            witness['sides'][side_]={'minimum_signed_m':value,'minimum_vertex_id':key,'world':cloud[side_][key],'locked':final['motion']['foot_locks'][side_],'vertices':len(distances)}
            check(f'scalar minimum matches vectorized sample{index} {side_}',abs(value-declared['sides'][side_]['minimum_signed_m'])<1e-10)
        result['witnesses'].append(witness)
    check('actual grounded penetration witness is strict',worst['capsule_on_sampled_plane'] and not worst['locked'] and result['witnesses'][indices.index(wi)]['sides'][side]['minimum_signed_m']<-.020,{'sample':wi,'side':side,'minimum_signed_m':worst['minimum_signed_m'],'penetrating_vertices_below_minus_5mm':worst['penetrating_vertices_below_minus_5mm']})
    anchor=analysis['summary']['max_original_anchor_vertex_drift'];key=anchor['anchor_vertex_id'];start=anchor['anchor_start_index'];end=anchor['index'];side=anchor['side'];drift=distance(cache[start][side][key],cache[end][side][key])
    check('fixed same-vertex plant drift matches',abs(drift-anchor['anchor_vertex_world_drift_m'])<1e-10,{'start':start,'end':end,'side':side,'vertex':key,'drift_m':drift})
    a=tape['samples'][start]['final_pose']['foot_targets'][side];b=tape['samples'][end]['final_pose']['foot_targets'][side]
    check('original plant target unchanged while skin vertex moves',distance(a,b)==0 and drift>.003,{'target_drift_m':distance(a,b),'skin_vertex_drift_m':drift})
    deltas={key:distance(value,cache[21]['R'][key]) for key,value in cache[22]['R'].items()};key=max(deltas,key=deltas.get);step=deltas[key]
    check('maximum sole finite step independently reproduced',abs(step-analysis['summary']['max_vertex_step']['maximum_vertex_step_m'])<1e-10,{'from':21,'to':22,'side':'R','vertex':key,'step_m':step,'physics_frames':[tape['samples'][i]['final_pose']['physics_frame'] for i in [21,22]],'root_step_m':distance(tape['samples'][21]['position'],tape['samples'][22]['position'])})
    joint_steps=[]
    for index in range(1,len(tape['samples'])):
        previous=tape['samples'][index-1];sample=tape['samples'][index]
        if previous['fixture']!=sample['fixture']:continue
        old=previous['final_pose'];new=sample['final_pose'];elapsed=(new['physics_frame']-old['physics_frame'])/60.
        if elapsed<=0:continue
        for name in new['bones']:
            local=distance(old['bones'][name][3],new['bones'][name][3]);world=distance(apply(old['rig_global'],old['bones'][name][3]),apply(new['rig_global'],new['bones'][name][3]))
            joint_steps.append({'index':index,'bone':name,'local_step_m':local,'world_step_m':world,'dt_seconds':elapsed,'local_average_speed_mps':local/elapsed,'fixture':sample['fixture']})
    result['max_joint_local_step']=max(joint_steps,key=lambda v:v['local_step_m']);result['max_joint_world_step']=max(joint_steps,key=lambda v:v['world_step_m'])
    result['controls']=tape['controls'];result['meaningful_limits']=['Finite world vertex/joint steps include root motion and intentional articulation; these maxima alone do not establish a discontinuity.','No adversarial reversal, action release/cancel, non-flat ground, LOD switch or actual motion-frame sequence is executed here.','R4-05 rejected r3a/r4 floor and C0/C1 counterexamples remain open; ordinary suite pass does not supersede them.','Initial title/fixture retained50.57mm plant and first post-placement stale slide contact are retained, separate from grounded ordinary-route penetration.']
    result['passed']=all(c['passed'] for c in result['checks']);(HERE/'contact-witnesses.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(result['checks']),'worst':worst,'max_joint_local_step':result['max_joint_local_step']},indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(run())
