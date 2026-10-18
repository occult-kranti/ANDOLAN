"""Bound final float32 world-position storage error on every checked pose."""
import gzip,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));from check_candidate import ROOT,GLB,sha
out=HERE/'stored-pose-margin-r6.json';assert not out.exists()
manifest=json.loads((HERE/'replacement-r6/replacement-manifest.json').read_text());proof=json.loads((HERE/'replacement-proof-r6.json').read_text());admission=json.loads((HERE/'source-admission-r6.json').read_text());stress=json.loads((HERE/'secondary-stress-r5.json').read_text());assert stress['passed']and len(stress['rows'])==120
old=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()));fresh=json.loads((ROOT/'docs/evidence/desktop-finish/hair-silhouette/W2/smooth-parent-pose-r1.json').read_text());poses=[np.array(s['bone_globals'])[49]for s in old['samples']]+[np.array(s['bone_global_poses']['shoulder01.L'])for s in fresh['samples']]
rows=[]
for level,item in manifest['levels'].items():
 g=GLB(item['source']);ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)[49];gain=max(float(np.linalg.svd((pose@ib)[:3,:3],compute_uv=False).max())for pose in poses)
 stored=next(r for r in proof['levels']if r['level']==level)['maximum_world_rest_storage_rounding_m'];bound=gain*stored+1e-12
 nominal=admission['summary'][level];gaps=[c.get('guaranteed_lower_bound_m',c.get('minimum_distance_m'))for row in stress['rows']if row['level']==level for c in row['contacts'].values()];stress_gap=min(x for x in gaps if x is not None);minimum=min(nominal['minimum_guaranteed_source_gap_m'],nominal['minimum_additional_pose_gap_m'],stress_gap);assert bound<minimum
 rows.append({'level':level,'checked_pose_operators':len(poses),'maximum_operator_norm':gain,'maximum_actual_float32_storage_error_m':stored,'maximum_posed_surface_error_bound_m':bound,'minimum_checked_contact_lower_bound_m':minimum,'retained_clearance_after_storage_bound_m':minimum-bound,'passed':True})
result={'schema':1,'passed':True,'checker_sha256':sha(__file__),'replacement_proof_sha256':sha(HERE/'replacement-proof-r6.json'),'admission_sha256':sha(HERE/'source-admission-r6.json'),'stress_sha256':sha(HERE/'secondary-stress-r5.json'),'rows':rows,'argument':'Every new vertex differs only by bounded world-rest float32 rounding. Existing rigid49 skin operator bounds posed vertex error; linear triangle interpolation has the same bound. Original colliders are byte-exact. All source gaps exceed this bound, so final stored new triangles retain positive clearance in the checked fixtures. Newarmoursecondaryalpha0. This is a numerical transfer bound, not new imported/GPU execution.'};out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
