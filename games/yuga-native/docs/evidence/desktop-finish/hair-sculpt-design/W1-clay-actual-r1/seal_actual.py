from pathlib import Path
import json,hashlib
W=Path(__file__).parent;D=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/hair-sculpt-design/W1-clay-actual-r1')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not D.exists();D.mkdir(parents=True)
files={};mapping=[]
def copy(p,rel):
 t=D/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(p.read_bytes());assert h(t)==h(p);files[rel]={'bytes':t.stat().st_size,'sha256':h(t)};mapping.append({'source':str(p),'artifact':rel,**files[rel]})
for name in ('actual-execution-r1','actual-execution-r2'):
 for p in sorted((W/name).rglob('*')):
  if p.is_file() and not any(x in p.relative_to(W/name).parts for x in ('__pycache__','cache','config','temp')):copy(p,name+'/'+str(p.relative_to(W/name)))
copy(Path(__file__),'seal_actual.py')
exe=json.loads((W/'actual-execution-r2/execution.json').read_text());cap=json.loads((W/'actual-execution-r2/render-r1/capture.json').read_text());failure=json.loads((W/'actual-execution-r1/execution.json').read_text())
checks=[]
def check(label,ok):checks.append({'label':label,'passed':bool(ok)});assert ok,label
check('render complete exit0 unchanged sources',exe['complete'] and exe['exit_code']==0 and exe['source_unchanged'] and cap['complete'] and cap['scene_unchanged_after'])
check('exact raw32CPU Cycles1024',cap['samples']==32 and cap['resolution']==[1024,1024] and cap['render_engine']=='CYCLES' and cap['use_denoising'] is False and exe['argv'][0:3]==['taskset','-c','0,1'])
check('explicit prior unavailable OIDN failure',failure['exit_code']==1 and not failure['complete'] and 'build has no OpenImageDenoise support' in (W/'actual-execution-r1/run.log').read_text())
ids=['front','anatomical-left-profile','rear','cast-angle-authoring'];check('exact4orderedviews', [v['id'] for v in cap['views']]==ids)
originals=[]
for row in cap['views']:
 p=W/'actual-execution-r2/render-r1'/(row['id']+'.png');check(row['id']+' exact framed source original',h(p)==row['png_sha256'] and row['full_hair_framed'] and row['head_context_framed']);originals.append({'id':row['id'],'artifact':'actual-execution-r2/render-r1/'+p.name,'sha256':h(p),'directly_viewed_by_W1':True})
check('final actual log no error traceback',not any(s in (W/'actual-execution-r2/run.log').read_text() for s in ('Traceback','Error:','Failed to denoise')))
review='''# Coarse clay actual review — revise before detail or export

W1 directly opened all four1024×1024 originals and the approved conceptdc3e42d2. The current scalp is a smooth cap/bowl with little gathering direction at silhouette scale. The knot remains an upright capped protrusion rather than a compact folded gather. In rear view the two long forms cross as thin ribbon straps, leaving a diamond-shaped gap; profile and three-quarter views show flat tapered sheets rather than overlapping hair volumes. The head/crown stay visible and all four agreed projection bounds pass, but those technical checks do not accept the sculpt. W1 recommends revising the coarse volume before fine strands, UVs, LODs or any runtime GLB.

These are real Blender authoring renders from the frozen editable scene71763ab2, with locked rest-space head/crown context. The fourth is a rest-space cast-angle design camera, not an animated cast. No runtime/skeleton/material/secondary-motion acceptance is inferred. All geometry, materials, lights, camera transforms and the four admitted lenses remain unchanged from W2's framing-r3 scene. The initial actual attempt failed before any PNG because the installed Blender build lacks OpenImageDenoise. Its exact helper/log/exit1 and all inputs are retained. Root approved a narrow successor disabling only Cycles use_denoising, with actual flag recorded;32samples and all scene contents are unchanged. The successful render took87.248s total, CPU0,1/two threads, exit0, four originals, no source-file changes. These raw sampled images are for coarse-shape judgment, not finished surface quality.

W2's separate framing admission4b9a86b7 preserves the earlier profile margin and rear clipping failures and the only saved-scene lens corrections (profile55→53.9mm, rear55→44mm). That packet and the editable scene remain separate unchanged dependencies. This owner packet preserves both actual attempts, exact three-source before/after hashes, the denoising-only patch, full logs, original PNGs and capture metadata. No geometry was edited, no software installed, and no canonical game asset was replaced.
'''
(D/'REVIEW.md').write_text(review);(D/'artifact-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');(D/'integrity.json').write_text(json.dumps({'passed':all(x['passed'] for x in checks),'checks':checks},indent=2)+'\n')
files={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':h(p)} for p in sorted(D.rglob('*')) if p.is_file()}
receipt={'schema':1,'disposition':'REVISE coarse shape; no detail/GLB/runtime promotion','scene_sha256':'71763ab25ed84719a8479bcce771732d50db980780b47c7c4b68114bf2bb9c2f','helper_sha256':'3e3127e8401b3c8b2eb46b9d219a07902016affccac8b967eab175d255b52321','projection_dependency_sha256':'89072ccb9656879ca26c5f4c3d043597cc901a260c0ea163d0bc592a34b477df','concept_sha256':'dc3e42d25777233dba653ecd9223c63711fc5c73135660ffa69e1b577a6556c8','framing_receipt_sha256':'4b9a86b719c963a22cb666a543fc0b1b8d90892fad416cdf59f65208f9e232da','engine_scope':'Blender4.3.2 CPU Cycles; actual authoring render only','elapsed_seconds':exe['elapsed_seconds'],'originals':originals,'artifacts':files,'integrity_checks':len(checks),'immutable_after_seal':True}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'receipt':str(D/'receipt.json'),'sha256':h(D/'receipt.json'),'artifacts':len(files),'bytes':sum(v['bytes'] for v in files.values())}))
