"""Curate bounded rig evidence; preserve large rejected candidates in scratch."""
import argparse,hashlib,json,shutil
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--scratch',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    copies={'input-inspection.json':'input-inspection.json'}
    for name in ['transfer.json','deformation-localization.json','export-integrity.json','inspect.log','localization.log','render.log']:
        src='transfer-r1/'+name
        if (a.scratch/src).exists():copies[src]='r1/'+name
    for name in ['rest.png','idle.png','fire.png','fire-wrist.png','run-cloth.png','views.json']:copies['transfer-r1/views/'+name]='r1/views/'+name
    for name in ['transfer.json','deformation-localization.json','repose-audit.json','repose-audit-v2.json','localization.log','repose-audit.log','repose-audit-v2.log']:copies['transfer-r2-fixed2/'+name]='r2/'+name
    copies.update({'transfer-r1/build_transfer-at-run.py':'frozen-code/r1-build-transfer.py','transfer-r2-fixed2/build_transfer-at-run.py':'frozen-code/r2-build-transfer.py','transfer-r2-fixed2/anatomy_gate-at-run.py':'frozen-code/r2-anatomy-gate.py','transfer-r2.log':'execution-failures/r2-incompatible-corner.log','transfer-r2-fixed.log':'execution-failures/r2-degenerate-face.log','transfer-r2-fixed2.log':'r2/build.log'})
    files=[]
    for src,rel in copies.items():
        source=a.scratch/src;dest=a.output/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert sha(dest)==sha(source),'Refusing to overwrite changed evidence '+str(dest)
        else:shutil.copyfile(source,dest)
        files.append({'path':rel,'bytes':dest.stat().st_size,'sha256':sha(dest)})
    large=[]
    for rel in ['transfer-r1/skin-transfer.blend','transfer-r1/rama-skin-transfer.glb','transfer-r2-fixed2/skin-transfer.blend']:
        path=a.scratch/rel;large.append({'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'status':'REJECTED; scratch retained; not promoted or duplicated in repository'})
    r1=json.loads((a.output/'r1/transfer.json').read_text());r2=json.loads((a.output/'r2/transfer.json').read_text())
    rows=[]
    for action,frame in [('idle',0),('fire',8),('run',5)]:
        one=next(s for s in r1['samples'] if s['action']==action and s['frame']==frame);two=next(s for s in r2['samples'] if s['action']==action and s['frame']==frame)
        one_loc=next(s for s in json.loads((a.output/'r1/deformation-localization.json').read_text())['samples'] if s['action']==action);two_loc=next(s for s in json.loads((a.output/'r2/deformation-localization.json').read_text())['samples'] if s['action']==action)
        rows.append({'action':action,'frame':frame,'r1_edge_p99':one['edge_ratio']['p99'],'r2_edge_p99':two['edge_ratio']['p99'],'r1_edges_abs_change_gt_2cm':one_loc['edges_absolute_change_above_2cm'],'r2_edges_abs_change_gt_2cm':two_loc['edges_absolute_change_above_2cm'],'r1_max_pose_edge_m':one_loc['max_pose_edge_m'],'r2_max_pose_edge_m':two_loc['max_pose_edge_m']})
    report={'schema_version':1,'scope':'Measured rig reuse investigation; both R1 and R2 rejected for production. Not a completed hero or quality upgrade.','inputs':r1['inputs'],'outcomes':{'binding_candidates':2,'failed_r2_executions_before_completed_candidate':2,'production_candidates_accepted':0,'runtime_promoted':False,'new_art_game_completion_credit':0},'deformation_comparison':rows,'r2_repose_edge_audit':json.loads((a.output/'r2/repose-audit-v2.json').read_text())['repose_edge_ratio'],'r2_geometry_changed_intentionally':True,'prefix_filter_zeros_are_not_validated_source_anatomy':True,'actual_r1_views':5,'r2_rendered':False,'r2_exported':False,'weapon_contact_tested':False,'reason_no_weapon_contact':'Generated source has no bow/weapon; fire is a reused action pose, not a weapon-contact acceptance.','files':files,'scratch_artifacts':large,'next_gate':'Measure asymmetric source arm/hand/garment correspondence and continuous rest-space repose before another transfer. Inspect original-fit→REST plus action edge deltas; then independent matched-view and bow-contact review.','package_script_sha256':sha(__file__)}
    (a.output/'rig-handoff.json').write_text(json.dumps(report,indent=2)+'\n');print('RIG_EVIDENCE_PACKAGE_PASS',json.dumps({'files':len(files),'bytes':sum(f['bytes'] for f in files),'candidates_rejected':2,'runtime_promoted':False}))
if __name__=='__main__':main()
