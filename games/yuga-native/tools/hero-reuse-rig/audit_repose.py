"""Read-only source-fit → R2 rest audit; exposes damage hidden by a new rest base."""
import argparse, hashlib, json, sys
from collections import Counter,defaultdict
from pathlib import Path
import bpy
from mathutils import Matrix,Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from anatomy_gate import segment,smooth,family
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def quant(v,p):return sorted(v)[int((len(v)-1)*p)]
def main():
    p=argparse.ArgumentParser();p.add_argument('--transfer',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);data=json.loads(a.transfer.read_text());bpy.ops.wm.open_mainfile(filepath=data['saved_scene']['path'])
    target=bpy.data.objects['Rama generated skin-transfer candidate'];rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    surface=bpy.data.objects['Existing Rama rest-weight surface']
    def identity(matrix):return max(abs(matrix[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))
    assert identity(surface.matrix_world)<1e-6 and identity(rig.matrix_world)<1e-6 and identity(target.matrix_world)<1e-6
    rig.animation_data.action=None
    for t in rig.animation_data.nla_tracks:t.mute=True
    for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
    reposed=[v.co.copy() for v in target.data.vertices];before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=data['inputs']['generated']['path'])
    source=next(o for o in bpy.context.scene.objects if o not in before and o.type=='MESH');mapping=Matrix(data['method']['coordinate_mapping'])
    original=[mapping@source.matrix_world@v.co for v in source.data.vertices];assert len(original)==len(reposed)==data['target']['vertices']
    chains={s:[Vector(x) for x in v] for s,v in data['anatomy_gate']['source_landmarks_fit_space'].items()};labels=[]
    for v in original:
        side='L' if v.x>=0 else 'R';chain=chains[side];parts=[segment(v,chain[i],chain[i+1]) for i in range(3)];best=min(range(3),key=lambda i:parts[i][2]);distance=parts[best][2]
        inner=.085 if best==0 else .075;outer=.15 if best==0 else .12;blend=(1-smooth(inner,outer,distance))*smooth(.17,.29,abs(v.x))
        if v.z<.80 or v.z>1.64:blend=0
        if blend>0:label=('arm.' if blend>=1-1e-8 else 'arm_core_boundary.')+side
        else:label='core' if v.z>1.02 else 'nonarm.'+side
        labels.append(label)
    assert dict(Counter(labels))==data['anatomy_gate']['source_label_counts']
    opposite_core=[];opposite_groups=defaultdict(lambda:{'vertices':0,'maximum_weight':0.})
    for vi,label in enumerate(labels):
        if not label.startswith('arm'):continue
        opposite='R' if label.endswith('.L') else 'L';total=0.
        for g in target.data.vertices[vi].groups:
            name=target.vertex_groups[g.group].name
            if name.endswith('.'+opposite) and family(name)=='core' and g.weight>1e-8:
                total+=g.weight;opposite_groups[name]['vertices']+=1;opposite_groups[name]['maximum_weight']=max(opposite_groups[name]['maximum_weight'],g.weight)
        opposite_core.append(total)
    ratios=[];rows=[];pairs=defaultdict(list)
    for e in target.data.edges:
        ia,ib=e.vertices;old=(original[ia]-original[ib]).length;new=(reposed[ia]-reposed[ib]).length
        if old<=1e-7:continue
        row={'a':ia,'b':ib,'source_fit_length_m':old,'reposed_rest_length_m':new,'ratio':new/old,'delta_m':new-old,'labels':[labels[ia],labels[ib]]}
        rows.append(row);ratios.append(new/old);pairs[' ↔ '.join(sorted({labels[ia],labels[ib]}))].append(row)
    worst=sorted(rows,key=lambda x:abs(x['delta_m']),reverse=True)[:12]
    report={'schema_version':1,'scope':'Read-only original-fit→reposed-rest audit. No quality acceptance; failed bind remains frozen.','transfer':{'path':str(a.transfer),'sha256':sha(a.transfer)},'script_sha256':sha(__file__),'source_vertices_preserved':len(original),'geometry_changed_intentionally':True,'common_fit_coordinate_space_identity_asserted':True,'source_label_counts_recomputed_exactly':True,'repose_edge_ratio':{'min':min(ratios),'p95':quant(ratios,.95),'p99':quant(ratios,.99),'max':max(ratios)},'repose_edges_absolute_change_above_2cm':sum(abs(r['delta_m'])>.02 for r in rows),'worst_repose_edges':[{**r,'original':[list(original[r['a']]),list(original[r['b']])],'reposed':[list(reposed[r['a']]),list(reposed[r['b']])]} for r in worst],'boundary_pairs':{key:{'edges':len(v),'max_ratio':max(r['ratio'] for r in v),'min_ratio':min(r['ratio'] for r in v),'max_absolute_delta_m':max(abs(r['delta_m']) for r in v),'above_2cm':sum(abs(r['delta_m'])>.02 for r in v)} for key,v in pairs.items()},'runtime_promoted':False,'quality_accepted':False}
    report['side_classifier_gap_audit']={'maximum_opposite_sided_core_weight_in_inferred_arm':max(opposite_core,default=0.),'opposite_sided_core_groups':dict(opposite_groups),'arm_leg_prefix_zero_is_not_complete_cross_limb_proof':True}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('RIG_REPOSE_AUDIT_PASS',json.dumps({k:report[k] for k in ['repose_edge_ratio','repose_edges_absolute_change_above_2cm','common_fit_coordinate_space_identity_asserted','side_classifier_gap_audit']}))
if __name__=='__main__':main()
