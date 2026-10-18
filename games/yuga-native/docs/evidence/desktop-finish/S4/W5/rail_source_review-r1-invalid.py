"""Independent stored-byte/frame/tape audit; no engine, asset mutation or render."""
from pathlib import Path
import collections, gzip, hashlib, json, struct, sys, time
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).parent
ART=ROOT/'art/hero-finish/s4-diadem-fit'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(path):
 raw=path.read_bytes(); magic,version,total=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and total==len(raw)
 chunks=[];offset=12
 while offset<len(raw):
  size,kind=struct.unpack_from('<II',raw,offset);chunks.append((kind,raw[offset+8:offset+8+size]));offset+=size+8
 assert offset==len(raw) and [k for k,_ in chunks]==[0x4e4f534a,0x004e4942]
 return raw,json.loads(chunks[0][1]),chunks[0][1],chunks[1][1]
def array(g,index):
 a=g[1]['accessors'][index];v=g[1]['bufferViews'][a['bufferView']];assert 'sparse' not in a
 dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 size=np.dtype(dtype).itemsize;stride=v.get('byteStride',size*width);base=v.get('byteOffset',0)+a.get('byteOffset',0)
 return np.ndarray((a['count'],width),dtype=dtype,buffer=g[3],offset=base,strides=(stride,size)).copy()
def transform(points,matrix):return points@matrix[:3,:3].T+matrix[:3,3]
def frame_reference(v,uv,t,n):
 edges=v[t[:,1:]]-v[t[:,0,None]];duv=uv[t[:,1:]]-uv[t[:,0,None]]
 determinant=np.linalg.det(duv);assert np.all(abs(determinant)>1e-12)
 derivatives=np.linalg.solve(duv,edges)
 u=np.zeros_like(v);vv=np.zeros_like(v)
 for k in range(3):
  for axis in range(3):
   u[:,axis]+=np.bincount(t[:,k],weights=derivatives[:,0,axis],minlength=len(v))
   vv[:,axis]+=np.bincount(t[:,k],weights=derivatives[:,1,axis],minlength=len(v))
 u-=n*np.einsum('ij,ij->i',n,u)[:,None];u/=np.linalg.norm(u,axis=1)[:,None]
 sign=np.sign(np.einsum('ij,ij->i',np.cross(n,u),vv))
 return u,sign
started=time.monotonic();checks=[]
def check(name,passed,details=None):
 checks.append({'name':name,'passed':bool(passed),'details':details or {}})
receipt_path=ROOT/'docs/evidence/desktop-finish/S4/W3/receipt.json';receipt=json.loads(receipt_path.read_text())
assert sha(receipt_path.read_bytes())=='e1199cf16f4e7da2e1eb060356658a3f558348c1df95140e8e9d161ca8e08cf4'
allpins=receipt['source_inputs']+receipt['owned_sources_and_evidence']+receipt['candidate_glbs']
pin_results=[{'path':r['path'],'match':(ROOT/r['path']).is_file() and sha((ROOT/r['path']).read_bytes())==r['sha256'] and (ROOT/r['path']).stat().st_size==r['bytes']} for r in allpins]
check('All author receipt input and output pins still exact',all(x['match'] for x in pin_results),{'files':len(pin_results),'mismatches':[x for x in pin_results if not x['match']]})
manifest=json.loads((ART/'candidate-r1/source-manifest.json').read_text());levels={}
for label,row in manifest['levels'].items():
 old=read(ROOT/row['source']);new=read(ART/'candidate-r1'/Path(row['output']).name);p=old[1]['meshes'][2]['primitives'][2];ids=np.array(row['selected_vertex_ids']);mask=np.zeros(len(old[3]),bool)
 assert old[2]==new[2] and len(old[0])==len(new[0])
 changed_accessors=set()
 for name in ['POSITION','NORMAL','TANGENT']:
  ai=p['attributes'][name];changed_accessors.add(ai);a=old[1]['accessors'][ai];view=old[1]['bufferViews'][a['bufferView']];width=3 if name!='TANGENT' else 4;stride=view.get('byteStride',width*4);base=view.get('byteOffset',0)+a.get('byteOffset',0)
  for i in ids:mask[base+int(i)*stride:base+int(i)*stride+width*4]=True
 b=np.frombuffer(old[3],np.uint8);c=np.frombuffer(new[3],np.uint8);diff=b!=c
 untouched_accessors=[i for i in range(len(old[1]['accessors'])) if i not in changed_accessors]
 exact_accessors=all(np.array_equal(array(old,i),array(new,i)) for i in untouched_accessors)
 check(label+' exact JSON, other accessors and nonselected bytes',not np.any(diff&~mask) and exact_accessors,{'unchanged_accessors':len(untouched_accessors),'changed_bytes':int(diff.sum()),'allowed_bytes':int(mask.sum())})
 # Independently derive differential tangent directions from stored float positions/UVs.
 v=array(new,p['attributes']['POSITION']).astype(float);uv=array(new,p['attributes']['TEXCOORD_0']).astype(float);n=array(new,p['attributes']['NORMAL']).astype(float);tangent=array(new,p['attributes']['TANGENT']).astype(float);tris=array(new,p['indices']).reshape(-1,3);t=tris[np.any(np.isin(tris,ids),axis=1)]
 assert np.all(np.isin(t,ids));lookup=np.full(len(v),-1);lookup[ids]=np.arange(len(ids));local=lookup[t]
 reference,sign=frame_reference(v[ids],uv[ids],local,n[ids]);stored=tangent[ids];alignment=np.einsum('ij,ij->i',reference,stored[:,:3]);sign_match=np.array_equal(sign,stored[:,3])
 face=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]);accum=np.zeros((len(ids),3))
 for k in range(3):
  for axis in range(3):accum[:,axis]+=np.bincount(local[:,k],weights=face[:,axis],minlength=len(ids))
 _,weld=np.unique(np.round(v[ids],7),axis=0,return_inverse=True);joined=np.zeros((int(weld.max())+1,3));np.add.at(joined,weld,accum);geometric=joined[weld];geometric/=np.linalg.norm(geometric,axis=1)[:,None];normal_dot=np.einsum('ij,ij->i',geometric,n[ids])
 check(label+' normal agrees with stored triangle area orientation',normal_dot.min()>1-1e-6,{'minimum_geometric_N_dot':float(normal_dot.min())})
 unit_error=max(float(abs(np.linalg.norm(n[ids],axis=1)-1).max()),float(abs(np.linalg.norm(stored[:,:3],axis=1)-1).max()));orth=float(abs(np.einsum('ij,ij->i',n[ids],stored[:,:3])).max())
 check(label+' stored TBN agrees with UV derivatives',alignment.min()>1-1e-7 and sign_match and unit_error<1e-6 and orth<1e-6,{'minimum_U_direction_dot':float(alignment.min()),'handedness_mismatches':int(np.count_nonzero(sign!=stored[:,3])),'max_unit_error':unit_error,'max_N_dot_T':orth})
 bad=stored.copy();bad[0,3]*=-1
 check(label+' tangent handedness negative control rejected',not np.array_equal(sign,bad[:,3]))
 # Confirm source inverse bind labels and rigid binding of every chosen record.
 joints=old[1]['skins'][0]['joints'];names=[old[1]['nodes'][x]['name'] for x in joints]
 w=array(new,p['attributes']['WEIGHTS_0']);j=array(new,p['attributes']['JOINTS_0']);colors=array(new,p['attributes']['COLOR_0'])
 check(label+' source rail rigidly belongs to named head and alpha0',names[104]=='head' and np.all(j[ids,0]==104) and np.all(w[ids]==[1,0,0,0]) and np.all(colors[ids,3]==0))
 levels[label]={'rail_vertices':len(ids),'rail_triangles':len(t),'source_sha256':sha(old[0]),'candidate_sha256':sha(new[0]),'stored_frame_reference_method':'Solve two-dimensional UV Jacobian per triangle, accumulate U/V per vertex, orthogonalize U against stored normal, compare cross(N,U) handedness to accumulated V.'}
 if label=='near':near_old,near_new,near_ids,near_tri=old,new,ids,t
# Verify the actual retained engine report, its producer and exact sample census.
archive=ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz';raw=gzip.decompress(archive.read_bytes());native=json.loads(raw)
archive_record=next(x for x in json.loads((archive.parent/'report-archives.json').read_text()) if x['archive'].endswith('native-r5.json.gz'))
check('Retained engine archive and lossless raw hash exact',sha(archive.read_bytes())==archive_record['archive_sha256'] and sha(raw)==archive_record['raw_sha256'] and len(raw)==archive_record['raw_bytes'])
probe=archive.parent/'source-r5/desktop_s3_arrow_fletching_cases.gd';probe_sha=sha(probe.read_bytes());source_key='res://tests/desktop_s3_arrow_fletching_cases.gd'
check('Recorded producer and imported source pins stable',native['source_before']==native['source_after'] and native['source_before'][source_key]==probe_sha and native['source_before']['res://assets/heroes/rama-hero.glb']==sha(near_old[0]) and native['source_before']['res://scripts/rama_motion.gd']=='8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8')
samples=native['samples'];groups=collections.defaultdict(list)
for s in samples:groups[s['id'].rsplit('-step',1)[0]].append(s)
kit=json.loads((ROOT/'assets/design/rama-ability-kit.json').read_text());expected={}
for ability in kit['abilities']:
 if ability['id'] not in ['kodanda','piercing_dawn','dawn_volley']:continue
 elapsed=0.;times=[]
 for frac in [.1,.5,1.05]:
  target=ability['windup_s']*frac
  while elapsed<target:
   elapsed+=min(1/60,target-elapsed);times.append(elapsed)
 expected[ability['id']]=times
census={};valid=True
for group,rows in groups.items():
 action=group.split('-pitch')[0];times=np.array([x['declared_elapsed_s'] for x in rows]);want=expected[action]
 ok=len(want)==len(rows) and np.allclose(times,want,rtol=0,atol=1e-12) and [int(x['id'].rsplit('-step',1)[1]) for x in rows]==list(range(len(rows)))
 valid=valid and ok;census[group]={'samples':len(rows),'last_elapsed_s':float(times[-1]),'expected_steps_exact':bool(ok)}
check('348 unique actual recorded poses across nine declared API series',native['passed'] and native['sample_mode']=='348-fixed-step-direct-api' and len(samples)==348 and len({x['id'] for x in samples})==348 and len(groups)==9 and valid,{'groups':census})
poses=np.array([s['bone_globals'] for s in samples]);check('Every retained sample contains 164 finite affine bone matrices',poses.shape==(348,164,4,4) and np.isfinite(poses).all() and np.all(poses[:,:,3]==[0,0,0,1]))
ib=array(near_old,near_old[1]['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib);influences=native['hand_geometry']['vertices'];points=[];bones=[];weights=[];dests=[];rest_points=[];spreads=[]
for i,slots in enumerate(influences):
 recovered=[]
 for slot in slots:
  points.append([*slot['point'],1]);bones.append(slot['bone']);weights.append(slot['weight']);dests.append(i);recovered.append((rest[slot['bone']]@[*slot['point'],1])[:3])
 recovered=np.array(recovered);rest_points.append(recovered[0]);spreads.append(np.linalg.norm(recovered-recovered[0],axis=1).max())
skin=near_old[1]['meshes'][2]['primitives'][11];source_points=array(near_old,skin['attributes']['POSITION']);errors,indices=cKDTree(source_points).query(rest_points)
check('Imported hand influences recover source rest points without raw vertex-index mapping',errors.max()<2e-6 and max(spreads)<2e-6,{'max_nearest_source_error_m':float(errors.max()),'max_influence_spread_m':float(max(spreads)),'vertices':len(influences),'triangles':len(native['hand_geometry']['triangles'])})
points=np.array(points);bones=np.array(bones);weights=np.array(weights);dests=np.array(dests);hand_tris=np.array(native['hand_geometry']['triangles']);p=near_new[1]['meshes'][2]['primitives'][2];rail_source=array(near_new,p['attributes']['POSITION'])[near_ids];head_local=transform(rail_source,ib[104]);bounds=[]
for s,pose in zip(samples,poses):
 rig=np.array(s['rig_global']);hand=np.zeros((len(influences),3));weighted=np.einsum('nij,nj->ni',pose[bones],points)[:,:3]*weights[:,None];np.add.at(hand,dests,weighted);hand=transform(hand,rig)[hand_tris];rail=transform(transform(head_local,pose[104]),rig)
 # AABB distances are lower bounds for every included triangle, independent of author narrow phase.
 low=np.maximum(np.maximum(rail.min(0)-hand.max(1),hand.min(1)-rail.max(0)),0)
 bounds.append(float(np.linalg.norm(low,axis=1).min()))
check('Independent conservative box bounds separate rail from selected hands in every pose',min(bounds)>.04,{'minimum_lower_bound_m':min(bounds),'samples':len(bounds),'method':'Whole rail AABB versus each actual posed hand triangle AABB; no pair inside the minimum bound can intersect.'})
result={'schema':1,'scope':'Independent source-only byte/frame/tape audit; no new import, native execution, render or whole-body/continuous motion acceptance. Bone order provenance requires separate retained indexed-name receipt.','author_receipt_sha256':sha(receipt_path.read_bytes()),'reviewer_script_sha256':sha(Path(__file__).read_bytes()),'levels':levels,'native_archive_sha256':sha(archive.read_bytes()),'native_raw_sha256':sha(raw),'native_producer_sha256':probe_sha,'checks':checks,'passed':all(x['passed'] for x in checks),'elapsed_seconds':time.monotonic()-started}
(OUT/'rail-source-review-r1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[x for x in checks if not x['passed']],'elapsed_seconds':result['elapsed_seconds']},indent=2))
sys.exit(0 if result['passed'] else 1)
