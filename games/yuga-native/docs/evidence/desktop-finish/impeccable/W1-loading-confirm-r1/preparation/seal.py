from pathlib import Path
import os,json,hashlib,shutil,difflib
from PIL import Image
W=Path('/workspace/scratch/yuga-impeccable-loading-confirm-r1');P=W/'source';PRE=W/'preparation';D=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/impeccable/W1-loading-confirm-r1')
assert not D.exists();assert shutil.disk_usage(W).free>500*1024**2;D.mkdir();checks=[];mapping={};journal=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ck(name,v):checks.append({'name':name,'passed':bool(v)});assert v,name
def put(src,rel):
 dst=D/rel;dst.parent.mkdir(parents=True,exist_ok=True);os.link(src,dst);mapping[rel]={'source':str(src),'sha256':sha(src),'bytes':src.stat().st_size,'same_inode':src.stat().st_ino==dst.stat().st_ino}
ck('Exact compact runtime',sha(P/'scripts/loading_presentation.gd')=='c3c785b8fe73876510109601b0a4f80c3567ced2ba6fb12ed38b54d1182088d7')
ck('Only explicit fixture key type corrected',(PRE/'board-r1.gd').read_text().replace('var key :=','var key: int =')==(P/'tools/ui-campaign/board.gd').read_text())
for scale in [1,2]:
 name='loading'+str(scale*100);raw=W/(name+'-r2');r=json.loads((raw/'run.json').read_text());e=json.loads((W/(name+'-execution-r2')/'execution.json').read_text());pngs=sorted(raw.glob('*.png'))
 ck(name+' complete owned execution',e['complete'] and e['exit_code']==0 and e['source_stable'] and e['actual_scale_canvas_assertion'] and r['complete'] and r['source_unchanged'])
 ck(name+' actual native input/no cache seed',len(r['events'])==7 and not r['godot_shader_cache_seed']['files_sha256'] and not r['shader_cache_seed']['files_sha256'])
 ck(name+' log scope','SCRIPT ERROR:' not in (raw/'godot.log').read_text() and '\nERROR:' not in (raw/'godot.log').read_text() and (raw/'godot.log').read_text().count('WARNING:')==1 and 'Could not set V-Sync mode' in (raw/'godot.log').read_text())
 ck(name+' exactly seven planned plus five automatic originals',len(r['shots'])==7 and len(pngs)==12)
 for f in pngs:
  s=json.loads(f.with_suffix('.json').read_text());ck(name+'/'+f.name+' raw identity and scale',sha(f)==s['sha256'] and Image.open(f).size==(960,540) and s['content_scale_factor']==scale and s['logical_viewport_size']==[1280/scale,720/scale])
  journal.append({'path':name+'/'+f.name,'sha256':sha(f),'sidecar_sha256':sha(f.with_suffix('.json')),'actual_phase':s['transition']['phase'],'held_sample':s['fixture_review']['held_sample'],'direct_W1_visual_review':not f.name.startswith('auto-')})
 for i,phase in enumerate(['queued','loading','constructing'],1):
  s=json.loads((raw/(f'0{i}-sample-{phase}.json')).read_text());fr=s['fixture_review'];required=['heading','detail','progress_scope','back_button']+(['progress_bar'] if phase=='loading' else [])
  ck(name+'/'+phase+' initially visible operation/scope/action',fr['held_sample'] and fr['phase']==phase and all(fr['controls'][key]['inside_ancestor_clips'] for key in required) and s['focus_name']=='TransitionBack')
  ck(name+'/'+phase+' explicit sampled progress',s['transition']['resource_progress']==(.475 if phase=='loading' else -1))
 for n,ticket in [('04-real-error',7),('05-real-retry',8)]:
  s=json.loads((raw/(n+'.json')).read_text());ck(name+'/'+n+' real controller/focus/actions',not s['fixture_review']['held_sample'] and s['transition']['phase']=='error' and s['transition']['attempt']==ticket and s['focus_name']=='TransitionRetry' and all(s['fixture_review']['controls'][key]['inside_ancestor_clips'] for key in ['heading','detail','back_button','retry_button']))
 for n,ticket in [('06-real-back',9),('07-real-queued-cancel',11)]:
  s=json.loads((raw/(n+'.json')).read_text());ck(name+'/'+n+' exact ticket owner/caller/focus restoration',not s['fixture_review']['held_sample'] and s['transition']['phase']=='cancelled' and s['transition']['attempt']==ticket and s['scene_can_process'] and not s['transition_owner_present'] and s['focus_name']=='OpenMissingScene')
 for f in raw.iterdir():
  if f.is_file():put(f,name+'/'+f.name)
 for f in (W/(name+'-execution-r2')).iterdir():
  if f.is_file():put(f,'execution/'+name+'/'+f.name)
failed=W/'loading100-r1';fe=json.loads((W/'loading100-execution-r1/execution.json').read_text());ck('Original zero-image fixture parse failure retained',not fe['complete'] and fe['exit_code']==1 and fe['png_count']==0 and 'Cannot infer the type of "key"' in (failed/'godot.log').read_text())
for base,rel in [(failed,'failed-fixture-r1'),(W/'loading100-execution-r1','failed-fixture-r1/execution')]:
 for f in base.iterdir():
  if f.is_file():put(f,rel+'/'+f.name)
for f in PRE.iterdir():
 if f.is_file():put(f,'preparation/'+f.name)
for rel in ['scripts/loading_presentation.gd','scripts/hero_ui_theme.gd','scripts/scene_transition.gd','tools/ui-campaign/board.gd','tools/ui-campaign/observer.gd']:
 put(P/rel,'source/'+rel)
put(Path(__file__),'preparation/seal.py')
(D/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');(D/'validation.json').write_text(json.dumps({'passed':True,'count':len(checks),'checks':checks,'image_journal':journal},indent=2)+'\n')
(D/'REVIEW.md').write_text('''# Single compact-loading confirmation

ACCEPT the bounded compact layout. W1 and W2 directly opened all 14 planned originals. Root directly opened all seven 200% endpoints and the 100% queued/loading/constructing/error views. At 200%, the operation, resource scope, loading bar and focused Cancel now fit initially. Context and chosen fonts remain. Both error actions and the full specific recovery message are visible. Native Retry increments the real controller attempt; Back and queued cancellation restore the active local opener and release input ownership. At 100%, the normal wordmark/rule and composition remain.

This is the one correction after the first batch's hidden 200% progress/scope. Only logical heights at or below 360 hide the redundant wordmark/rule and remove artificial detail/progress minimum heights. Title69162 and theme5a726 remain unchanged. No further correction or raster is requested.

The 960×540 native windows have exactly observed logical1280×720 and640×360 at scale1/2. This small GL fixture uses production loading presentation c3c785 and unchanged transition a5d236, with real XTest keyboard input. Keys1/2/3 deliberately hold visual queued/loading/constructing samples. The displayed48% comes from declared sample0.475 and is NOT measured resource timing. Keys4/Return/Escape and the5+Escape burst exercise genuine missing-resource/error, Retry, Back and queued-cancel controller behavior. The fixture loads no world or hero; it is not a new integrated/package run. Original genuine boot phases remain in ../W1-actual-r1 unchanged.

Each successful take exited the outer runner0 in about3.60s, with7 planned and5 automatic originals. Automatic sample frames retain truthful held_sample metadata; auto-queued7/8 belong to real controller attempts. The engine is exact e69; no cache seed was supplied. Both logs retain one expected GL V-Sync warning and no engine errors. After planned endpoints the runner terminates its own process; this is not a native Quit claim.

The first attempt failed before images because the new fixture board inferred an untyped key. Its complete log/source identity and zero-PNG report are preserved. The sole harness correction is `var key :=` to `var key: int =`; check-only passed before the two successful takes. The earlier missing global-script-cache error is preserved separately in W1-actual-r1. Neither failure is reclassified as success.

All24 originals and sidecars are hashed; W1's direct visual review covers14 planned frames. Closed files are hardlinked into this packet to preserve the500MiB reserve; caches and fonts are not duplicated. No runtime promotion, export or full campaign-round completion is inferred.
''')
arts={str(f.relative_to(D)):{'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(D.rglob('*')) if f.is_file()}
(D/'receipt.json').write_text(json.dumps({'disposition':'ACCEPT bounded compact-loading correction; one correction complete','source_sha256':'c3c785b8fe73876510109601b0a4f80c3567ced2ba6fb12ed38b54d1182088d7','first_batch_receipt_sha256':'ad3ec9f8ed896e208ed95438063eb1cb80ad1cc913d049d0fc895cc379f102fe','originals':24,'planned_originals_directly_reviewed':14,'validation_checks':len(checks),'artifacts':arts},indent=2)+'\n')
print(json.dumps({'path':str(D),'receipt':sha(D/'receipt.json'),'artifacts':len(arts),'checks':len(checks),'free':shutil.disk_usage(W).free}))
