"""Localize actual posed edge/seam failures in a saved skin-transfer candidate."""
import argparse, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path
import bpy
from mathutils import Matrix

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def coordinates(obj):
    dg=bpy.context.evaluated_depsgraph_get();eo=obj.evaluated_get(dg);me=eo.to_mesh()
    out=[eo.matrix_world@v.co for v in me.vertices];eo.to_mesh_clear();return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()))
    obj=bpy.data.objects['Rama generated skin-transfer candidate'];rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    rig.animation_data.action=None
    for t in rig.animation_data.nla_tracks:t.mute=True
    for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update();rest=coordinates(obj)
    seams=defaultdict(list)
    for i,v in enumerate(rest):seams[tuple(round(x,5) for x in v)].append(i)
    seams=[v for v in seams.values() if len(v)>1]
    def vertex(i,posed):
        return {'index':i,'rest':[float(x) for x in rest[i]],'posed':[float(x) for x in posed[i]],'influences':[{'bone':obj.vertex_groups[g.group].name,'weight':g.weight} for g in obj.data.vertices[i].groups if g.weight>1e-8]}
    samples=[]
    for action_name,frame in [('idle',0),('fire',8),('run',5),('cast1',12)]:
        rig.animation_data.action=next(x for x in bpy.data.actions if x.name.startswith(action_name+'_'))
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();posed=coordinates(obj)
        edges=[]
        for e in obj.data.edges:
            ia,ib=e.vertices;old=(rest[ia]-rest[ib]).length;new=(posed[ia]-posed[ib]).length
            if old>1e-7:edges.append({'a':ia,'b':ib,'rest_length_m':old,'posed_length_m':new,'ratio':new/old,'delta_m':new-old})
        seam_errors=[]
        for group in seams:
            maxdist=max((posed[ia]-posed[ib]).length for ia in group for ib in group)
            if maxdist>1e-5:seam_errors.append({'indices':group,'posed_gap_m':maxdist})
        worst=sorted(edges,key=lambda e:e['delta_m'],reverse=True)[:12]
        samples.append({'action':action_name,'frame':frame,'finite':all(math.isfinite(c) for v in posed for c in v),'stretched_edges_above_2':sum(e['ratio']>2 for e in edges),'stretched_edges_above_4':sum(e['ratio']>4 for e in edges),'edges_absolute_change_above_2cm':sum(abs(e['delta_m'])>.02 for e in edges),'max_rest_edge_m':max(e['rest_length_m'] for e in edges),'max_pose_edge_m':max(e['posed_length_m'] for e in edges),'worst_absolute_stretch_edges':[{**e,'vertices':[vertex(e['a'],posed),vertex(e['b'],posed)]} for e in worst],'uv_seam_groups_tested':len(seams),'uv_seam_groups_separating_above_1e5m':len(seam_errors),'largest_seam_gaps':sorted(seam_errors,key=lambda e:-e['posed_gap_m'])[:8]})
    report={'scope':'Diagnosis of frozen nearest-weight candidate; no quality acceptance','scene':{'path':str(a.scene),'sha256':sha(a.scene)},'script_sha256':sha(__file__),'samples':samples,'runtime_promoted':False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('RIG_DEFORMATION_LOCALIZATION_PASS',json.dumps([{k:v for k,v in s.items() if k not in {'worst_absolute_stretch_edges','largest_seam_gaps'}} for s in samples]))
if __name__=='__main__':main()
