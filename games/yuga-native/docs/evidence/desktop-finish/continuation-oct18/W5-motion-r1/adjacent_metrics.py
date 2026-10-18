#!/usr/bin/env python3
"""Landing-window measurements, not a smoothness acceptance predicate."""
from pathlib import Path
import gzip, hashlib, json, math, sys
import numpy as np

def load(path):
    with gzip.open(path,'rt') as stream:return json.load(stream)
def matrix(row):
    result=np.eye(4);result[:3,:3]=np.array(row[:3],dtype=float).T;result[:3,3]=row[3];return result
def rotation(basis):
    u,_,v=np.linalg.svd(basis);return u@v
def metrics(path):
    data=load(path);names=data['bone_names'];shots=data['shots'];dt=1/30
    first=next(i for i in range(226,len(shots)) if shots[i]['final_modifier_body']['on_floor'] and not shots[i-1]['final_modifier_body']['on_floor'])
    rows=[]
    for i in range(first-4,first+5):
        shot=shots[i];prior=shots[i-1];body=shot['final_modifier_body'];rig=matrix(shot['sole_contacts']['rig_transform']);old_rig=matrix(prior['sole_contacts']['rig_transform'])
        row={'frame':i,'physics':body['physics_frame'],'grounded':body['on_floor'],'root_y':body['position_world'][1],'body_vertical_velocity':body['velocity'][1],'feet':{}}
        for side in ['L','R']:
            index=names.index('foot.'+side);now=rig@matrix(shot['rendered_pose_globals'][index]);old=old_rig@matrix(prior['rendered_pose_globals'][index]);delta=now[:3,3]-old[:3,3]
            point=shot['sole_contacts']['sides'][side];before=prior['sole_contacts']['sides'][side]
            same_vertex=point['minimum_vertex']==before['minimum_vertex']
            joint_steps={}
            for prefix in ['upperleg01.','upperleg02.','lowerleg01.','lowerleg02.','foot.']:
                bone=names.index(prefix+side);r=rotation(matrix(shot['rendered_pose_globals'][bone])[:3,:3]);q=rotation(matrix(prior['rendered_pose_globals'][bone])[:3,:3]);angle=math.degrees(math.acos(max(-1,min(1,(np.trace(q.T@r)-1)/2))))
                joint_steps[prefix+side]=angle
            row['feet'][side]={'signed_minimum_mm':point['minimum_signed_m']*1000,'locked':point['locked'],'ankle_step_mm':(delta*1000).tolist(),'ankle_velocity_mps':(delta/dt).tolist(),'adjacent_global_rotation_degrees':joint_steps,'minimum_vertex_same_across_pair':same_vertex,'minimum_vertex':point['minimum_vertex'],'lowest_world':point['lowest_world'],'same_vertex_step_mm':[(a-b)*1000 for a,b in zip(point['lowest_world'],before['lowest_world'])] if same_vertex else None}
        rows.append(row)
    return {'path':str(path),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'first_grounded_frame':first,'rows':rows}
if __name__=='__main__':
    paths=[Path(p) for p in sys.argv[1:-1]];out=Path(sys.argv[-1]);result={'scope':'Headless30Hz adjacent final-modifier values. Fixed ankle bones track identical joints. Lowest-skin-point displacement is given only when its source vertex identity is unchanged; extrema changes are not a tracked vertex velocity. Scalar easing is not temporal smoothness proof. No aesthetic pass/fail inferred.','takes':[metrics(p) for p in paths]};out.write_text(json.dumps(result,indent=2)+'\n');print(out)
