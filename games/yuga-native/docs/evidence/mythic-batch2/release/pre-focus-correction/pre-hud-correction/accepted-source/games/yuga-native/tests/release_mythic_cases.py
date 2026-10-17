#!/usr/bin/env python3
"""Synthetic mythic publication counterexamples; no real render, Git or network writes."""
import argparse, copy, hashlib, importlib.util, json, re, shutil, struct, subprocess, tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();PROJECT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('mythic_base',HERE.with_name('release_traversal_cases.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
release=base.release;write=base.write;TAG='yuga-traversal-armies-review-fixture-mythic';CHECKS=[]
SIGNATURE={'width':1280,'height':720,'frames':120,'fps':30,'duration_seconds':4.0}
TRAVERSAL_SIGNATURE={'width':1280,'height':720,'frames':180,'fps':30,'duration_seconds':6.0}
SHAPES={h['id']:next(a['native_demo']['shape'] for a in h['abilities'] if a['slot']=='R') for h in json.loads((PROJECT/'assets/design/hero-codex.json').read_text())['heroes']}

SYNTHETIC_PIN_PATHS = {
 'tools/check-native-contracts.py','assets/contracts/native-contracts-v1.json','scripts/native_contracts.gd','tests/native_contract_cases.gd',
 'scripts/hero_pose.gd','assets/heroes/rama-production.glb','scripts/mythic_environment.gd','scripts/world_lighting.gd','tests/world_presentation_cases.gd',
 'scripts/entity_bridge.gd','tests/entity_bridge_cases.gd','scripts/ultimate_rules.gd','scripts/ultimate_session.gd','scripts/lane_army.gd','scripts/lane_minion.gd','assets/design/native-ultimate-rules.json','tests/ultimate_cases.gd',
 'scripts/invocation_panel.gd','scripts/input_bindings.gd','assets/design/hero-codex.json','tests/invocation_ui_cases.gd','scripts/invocation_audio.gd','assets/audio/invocations/manifest.json','tests/invocation_audio_cases.gd',
 'scripts/confluence_world.gd','scripts/player.gd','scripts/ultimate_effects.gd','tests/mythic_integration_cases.gd','tools/release-native.py','tests/release_mythic_cases.py','tests/release_traversal_cases.py',
 'tools/check-hero-codex.py','art/production/reconstruct_rama.py','tools/audio/build-invocation-audio.py','assets/contracts/physics-fixture-v1.json','tools/physics/reference.ts','tests/physics_authority_cases.gd','tools/physics/compare.py','tests/hero_pose_cases.gd'
}
def synthetic_checks(project,checks):
 pin=lambda p:release.digest(project/p)
 pins={p:pin(p) for p in SYNTHETIC_PIN_PATHS}
 for name in release.MYTHIC_CHECKS:
  r={'passed':True,'checks':[{'passed':True,'name':'Synthetic bounded check'}],'source_sha256':pins}
  if name=='hero-codex':r.update(heroes=14,ability_slots=42,errors=[],catalogue_sha256=pin('assets/design/hero-codex.json'))
  elif name=='hero-codex-cases':r.update(checks=1,cases=[{'passed':True}],catalogue_sha256=pin('assets/design/hero-codex.json'),validator_sha256=pin('tools/check-hero-codex.py'))
  elif name=='hero-reconstruction':r.update(asset_sha256=pin('assets/heroes/rama-production.glb'),generator_sha256=pin('art/production/reconstruct_rama.py'))
  elif name=='hero-pose':r.update(test_sha256=pin('tests/hero_pose_cases.gd'))
  elif name=='ultimate-effects':r.update(effect_source_sha256=pin('scripts/ultimate_effects.gd'),rules_source_sha256=pin('assets/design/native-ultimate-rules.json'))
  elif name=='invocation-audio-build':r.update(mode='check',files=16,failures=[],sum_of_three_maximum_peaks=.5,manifest_sha256=pin('assets/audio/invocations/manifest.json'))
  elif name=='physics':r.update(cross_engine_equivalence=False,inputs={k:{'sha256':pin(p)} for k,p in {'fixture':'assets/contracts/physics-fixture-v1.json','typescript_source':'tools/physics/reference.ts','godot_source':'tests/physics_authority_cases.gd','comparison_source':'tools/physics/compare.py'}.items()},summary={'queries':34,'paired_actor_samples':480,'query_count_per_implementation':1474})
  write(checks/(name+'.json'),r)

def fixture_events():
 events=[]
 for hero,cast,timeline in [('rama',21,[('begin',0,-1),('release',1,-1),('impact',36/30,0),('impact',38/30,1),('impact',40/30,2),('end',76/30,-1)]),('sita',22,[('begin',0,-1),('release',24/30,-1),('impact',24/30,-1),('cancel',114/30,-1)])]:
  for sequence,(kind,at,index) in enumerate(timeline):events.append({'hero_id':hero,'cast_id':cast,'event_seq':sequence,'kind':kind,'time_s':at,'projectile_index':index,'reason':'scripted_study_contact' if index>=0 else 'scripted_visual_fixture'})
 return sorted(events,key=lambda e:e['time_s'])

def fixture(root):
 repo,project,film,args=base.fixture(root);args.tag=TAG
 for name in release.MYTHIC_CHECKS:write(args.checks/(name+'.json'),{'passed':True,'scope':'Synthetic fixture'})
 for name in release.MYTHIC_FIXED_SOURCES|release.MYTHIC_REQUIRED_RUNTIME|SYNTHETIC_PIN_PATHS:write(project/name,'Synthetic source '+name)
 write(project/'assets/design/hero-codex.json',{'heroes':[{'id':h,'abilities':[{'slot':'R','native_demo':{'shape':SHAPES[h]}}]} for h in release.MYTHIC_HERO_IDS]})
 manifest={'generator_sha256':release.digest(project/'tools/audio/build-invocation-audio.py'),'files':{}}
 for filename in ['windup.wav','cancel.wav']+[h+'-release.wav' for h in release.MYTHIC_HERO_IDS]:
  write(project/'assets/audio/invocations'/filename,'Synthetic cue '+filename);manifest['files'][filename]=release.record(project/'assets/audio/invocations'/filename)
 write(project/'assets/audio/invocations/manifest.json',manifest)
 synthetic_checks(project,args.checks)
 paths=set(release.MYTHIC_FIXED_SOURCES)
 for folder in ('scripts','scenes','assets','shaders'):paths.update(p.relative_to(project).as_posix() for p in (project/folder).rglob('*') if p.is_file())
 runtime={p:release.record(project/p) for p in paths if p=='project.godot' or p.split('/')[0] in ('scripts','scenes','assets','shaders')}
 exported={'git':{'head':base.COMMIT},'source':{'files':runtime}};write(args.build/'native-export-manifest.json',exported)
 traversal=project/release.MYTHIC_TRAVERSAL_CAPTURE_DIRECTORY;shutil.copytree(project/release.TRAVERSAL_CAPTURE_DIRECTORY,traversal)
 base.mutate_capture(traversal,lambda r:r.update(source_sha256={'res://'+p:release.digest(project/p) for p in set(release.CAPTURE_FIXED_SOURCES)|set(runtime)}))
 capture=project/release.MYTHIC_ULTIMATE_CAPTURE_DIRECTORY;capture.mkdir(parents=True)
 def image(name,retained=None):
  data=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II',1280,720)+name.encode()
  if retained:(capture/retained).write_bytes(data)
  return {'file':name,'sha256':hashlib.sha256(data).hexdigest(),'width':1280,'height':720,'draw_calls':30,'rendered_objects':44,'rendered_primitives':4000}
 def fx(active=1,low=False,motion=False):return {'active':active,'finite':True,'nodes':active*8,'triangles':active*600,'particles':0,'lights':0,'voices':0,'reduced_effects':low,'reduced_motion':motion}
 frames=[]
 for i in range(120):
  phases=(['begin','begin'] if i<24 else ['begin','impact'] if i<30 else ['release','impact'] if i<36 else ['impact','impact'] if i<76 else ['impact'] if i<114 else [])
  frames.append({'index':i,'physics_tick':100+2*(i+1),'physics_tick_delta':2,'render_frame':100+i,'finite':True,'presentation_seconds':i/30,'image':image(f'frame-{i:05d}.png',f'ultimate-frame-{i:05d}.png' if i in release.MYTHIC_SELECTED_FRAMES else None),'fx':fx(len(phases)),'effect_phases':phases})
 render={'complete':True,'failure':'','kind':'actual-staged-native-ultimate-vfx','gameplay_applied':False,'renderer':'forward_plus','display':'X11','fps':30,'expected_frames':120,'physics_hz':60,'take_physics_ticks':240,'width':1280,'height':720,'time_scale':1.0,'take_start_tick':100,'frames':frames,'outcomes':{k:True for k in ('begin','release','contact','expired','persistent_zone_cancelled_for_take_end')},'source_sha256':{'res://'+p:release.digest(project/p) for p in paths},'events':fixture_events(),'imports':{'res://assets/heroes/rama-production.glb':{'fresh':True,'sha256':'a'*64,'imported':'res://.godot/imported/rama-production.glb-fixture.scn'}},'stills':[{'hero_id':h,'effect_id':h+'.r.v1','codex_shape':SHAPES[h],'sample_age_s':.4,'image':image('still-'+h+'.png','still-'+h+'.png'),'fx':fx()} for h in release.MYTHIC_HERO_IDS],'variants':[{'id':name,'image':image('still-'+name+'.png','still-'+name+'.png'),'fx':fx(4 if name=='four-overlap' else 1,name=='low-effects',name=='reduced-motion')} for name in ('low-effects','reduced-motion','four-overlap')]}
 write(capture/'ultimate-render-review.json',render);write(capture/'ULTIMATE-RENDER-REVIEW.md','Synthetic fixture; not rendered gameplay.');write(capture/'yuga-ultimate-studies.mp4','Synthetic movie, external decode mocked.')
 write(capture/'ultimate-video.json',{'complete':True,'file':'yuga-ultimate-studies.mp4',**release.record(capture/'yuga-ultimate-studies.mp4'),'capture_report_sha256':release.digest(capture/'ultimate-render-review.json'),'probe':{'streams':[{'codec_type':'video','codec_name':'h264','width':1280,'height':720,'nb_read_frames':'120','avg_frame_rate':'30/1'}],'format':{'duration':'4.000000'}}})
 return repo,project,film,args,capture,exported

def mutate(capture,fn):
 p=capture/'ultimate-render-review.json';r=json.loads(p.read_text());fn(r);write(p,r)
 video=json.loads((capture/'ultimate-video.json').read_text());video['capture_report_sha256']=release.digest(p);write(capture/'ultimate-video.json',video)

def check(name,expected,error,**details):CHECKS.append({'name':name,'passed':(error is None)==expected,'expected_success':expected,'rejection':error,'details':details})

def direct(name,fn=None,expected=False,decode=False,decoder_failure=False):
 with tempfile.TemporaryDirectory(prefix='yuga-mythic-release-') as tmp:
  _,project,_,_,capture,exported=fixture(Path(tmp));error=None
  if fn:fn(capture,project,exported)
  with patch.object(release,'PROJECT',project),patch.object(release,'probe_mythic_movie',return_value=SIGNATURE,side_effect=ValueError('Synthetic decoder rejection') if decoder_failure else None) as decoder:
   try:release.validate_mythic_capture(capture,exported,decode=decode)
   except (ValueError,KeyError,TypeError,OSError,IndexError,StopIteration) as caught:error=str(caught)
  check(name,expected,error,decoder_calls=decoder.call_count)
  if expected and decode:CHECKS[-1]['passed'] &= decoder.call_count==1

def staged(name,fn=None,expected=False,reseal=None,git_failure=None):
 with tempfile.TemporaryDirectory(prefix='yuga-mythic-stage-') as tmp:
  repo,project,film,args,capture,_=fixture(Path(tmp));error=None;seen=[]
  if fn:fn(capture,project,args)
  def git(*argv):
   seen.append(argv)
   if git_failure:
    value=git_failure(argv)
    if value is not None:return value
   return base.COMMIT if argv[0]=='rev-parse' else ''
  with patch.object(release,'REPO',repo),patch.object(release,'PROJECT',project),patch.object(release,'FILM',film),patch.object(release,'git',side_effect=git),patch.object(release,'validate_evidence',return_value={'passed':True}),patch.object(release,'probe_traversal_movie',return_value=TRAVERSAL_SIGNATURE) as traversal,patch.object(release,'probe_mythic_movie',return_value=SIGNATURE) as ultimate:
   try:
    release.stage(args)
    if reseal:reseal(args.output);base.update_inventory(args.output);release.verify(args.output,TAG,base.COMMIT)
   except (ValueError,KeyError,TypeError,OSError,IndexError,StopIteration,subprocess.CalledProcessError) as caught:error=str(caught)
  check(name,expected,error,traversal_decodes=traversal.call_count,ultimate_decodes=ultimate.call_count)
  if expected and error is None:
   tracked=[v for cmd in seen if cmd[0]=='ls-files' for v in cmd]
   CHECKS[-1]['passed'] &= traversal.call_count==1 and ultimate.call_count==1 and all(str((capture/n).relative_to(repo)) in tracked for n in release.MYTHIC_CAPTURE_ASSETS)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path);a=p.parse_args();before=release.digest(PROJECT/'tools/release-native.py')
 workflow=(PROJECT.parents[1]/'.github/workflows/yuga-native-release.yml').read_text()
 reports=set(re.findall(r'\$RUNNER_TEMP/checks/([a-z-]+)\.json',workflow))
 check('workflow writes all mandatory mythic reports',True,None if set(release.MYTHIC_CHECKS)<=reports else str(sorted(set(release.MYTHIC_CHECKS)-reports)))
 check('workflow pins Node22 and installs locked dependencies',True,None if 'actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020' in workflow and "node-version: '22.14.0'" in workflow and 'run: npm ci' in workflow else 'Node dependency setup missing')
 check('mythic traversal demands shader coverage without changing historical default',True,None if release.validate_traversal_capture.__defaults__==(False,False) and 'require_shaders=mythic_release(args.tag)' in (PROJECT/'tools/release-native.py').read_text() else 'source scope routing differs')
 check('exact mythic suffix and old routing preserved',True,None if release.mythic_release(TAG) and not any(release.mythic_release(t) for t in ('yuga-confluence-duel-x-mythic','yuga-traversal-armies-x-mythic-other',TAG+'\n')) and release.traversal_capture_directory(TAG)==release.MYTHIC_TRAVERSAL_CAPTURE_DIRECTORY and release.traversal_capture_directory(base.TAG)==release.TRAVERSAL_CAPTURE_DIRECTORY else 'routing mismatch')
 direct('valid actual full-only schema without preview key',expected=True);direct('explicit false preview remains accepted',lambda c,p,e:mutate(c,lambda r:r.update(preview=False)),expected=True);direct('fresh decoder invoked',expected=True,decode=True);direct('fresh decode failure rejects',decode=True,decoder_failure=True)
 staged('valid mythic stage binds fresh traversal plus ultimate',expected=True)
 mutations={
  'incomplete':lambda r:r.update(complete=False),'preview':lambda r:r.update(preview=True),'numeric preview':lambda r:r.update(preview=0),'string preview':lambda r:r.update(preview='false'),'null preview':lambda r:r.update(preview=None),'failure':lambda r:r.update(failure='failed'),'fake gameplay claim':lambda r:r.update(gameplay_applied=True),'headless':lambda r:r.update(display='headless'),'fallback renderer':lambda r:r.update(renderer='gl_compatibility'),'wrong frames':lambda r:r['frames'].pop(),'wrong ticks':lambda r:r.update(take_physics_ticks=239),'bad time scale':lambda r:r.update(time_scale=True),'zero time scale':lambda r:r.update(time_scale=0),'invalid start':lambda r:r.update(take_start_tick=-1),'tick gap':lambda r:r['frames'][40].update(physics_tick=999),'draw did not advance':lambda r:r['frames'][40].update(render_frame=1),'nonfinite pose':lambda r:r['frames'][40].update(finite=False),'wrong sample time':lambda r:r['frames'][40].update(presentation_seconds=float('nan')),'zero counters':lambda r:r['frames'][40]['image'].update(draw_calls=0),'missing source':lambda r:r.update(source_sha256={}), 'changed source hash':lambda r:r['source_sha256'].update({'res://scripts/ultimate_effects.gd':'0'*64}),'missing hero':lambda r:r['stills'].pop(),'duplicate hero':lambda r:r['stills'].__setitem__(1,copy.deepcopy(r['stills'][0])),'wrong effect identity':lambda r:r['stills'][0].update(effect_id='ravana.r.v1'),'wrong shape':lambda r:r['stills'][0].update(codex_shape='same-circle'),'nonfinite age':lambda r:r['stills'][0].update(sample_age_s=float('nan')),'zero age':lambda r:r['stills'][0].update(sample_age_s=0),'missing events':lambda r:r.pop('events'),'events reordered':lambda r:r['events'].reverse(),'wrong event sequence':lambda r:r['events'][4].update(event_seq=12),'wrong projectile contact':lambda r:r['events'][5].update(projectile_index=2),'no persistent cancel disclosure':lambda r:r['outcomes'].pop('persistent_zone_cancelled_for_take_end'),'no active hero':lambda r:r['stills'][0]['fx'].update(active=0),'too many effects':lambda r:r['frames'][30]['fx'].update(active=5),'unbounded triangles':lambda r:r['frames'][30]['fx'].update(triangles=100000),'nonfinite FX':lambda r:r['frames'][30]['fx'].update(finite=False),'fake phase':lambda r:r['frames'][30].update(effect_phases=['invented']),'phase population mismatch':lambda r:r['frames'][30].update(effect_phases=[]),'no expired tail':lambda r:r['frames'][-1].update(fx=copy.deepcopy(r['frames'][0]['fx']),effect_phases=['begin']),'no contact outcome':lambda r:r['outcomes'].update(contact=False),'missing variant':lambda r:r['variants'].pop(),'low effects not applied':lambda r:r['variants'][0]['fx'].update(reduced_effects=False),'reduced motion not applied':lambda r:r['variants'][1]['fx'].update(reduced_motion=False),'four overlap missing':lambda r:r['variants'][2]['fx'].update(active=3),'missing import':lambda r:r.update(imports={}),'stale import':lambda r:r['imports']['res://assets/heroes/rama-production.glb'].update(fresh=False),'unsafe import':lambda r:r['imports']['res://assets/heroes/rama-production.glb'].update(imported='res://../bad.scn')}
 for name,fn in mutations.items():direct(name,lambda c,p,e,fn=fn:mutate(c,fn))
 for name in release.MYTHIC_CAPTURE_ASSETS:
  direct('required capture file '+name,lambda c,p,e,name=name:(c/name).unlink())
  staged('resealed package cannot omit '+name,reseal=lambda d,name=name:(d/name).unlink())
 for gate in release.MYTHIC_CHECKS:
  staged('failed required check '+gate,fn=lambda c,p,a,gate=gate:write(a.checks/(gate+'.json'),{'passed':False}))
  staged('resealed package cannot omit check '+gate,reseal=lambda d,gate=gate:(d/('ci-'+gate+'.json')).unlink())
 staged('empty successful gameplay report rejects',fn=lambda c,p,a:write(a.checks/'ultimate.json',{'passed':True,'checks':[]}))
 def stale_report(c,p,a):
  path=a.checks/'ultimate.json';r=json.loads(path.read_text());r['source_sha256']['scripts/ultimate_session.gd']='0'*64;write(path,r)
 staged('stale gameplay source pin rejects',fn=stale_report)
 def missing_pin(c,p,a):
  path=a.checks/'ultimate.json';r=json.loads(path.read_text());r['source_sha256'].pop('scripts/ultimate_session.gd');write(path,r)
 staged('missing mandatory gameplay source pin rejects',fn=missing_pin)
 direct('actual source changed',lambda c,p,e:write(p/'scripts/ultimate_effects.gd','changed after capture'))
 direct('export source differs',lambda c,p,e:e['source']['files']['scripts/ultimate_effects.gd'].update(sha256='0'*64))
 direct('export omits runtime',lambda c,p,e:e['source']['files'].pop('scripts/ultimate_effects.gd'))
 direct('retained PNG substituted',lambda c,p,e:write(c/'still-rama.png','replacement'))
 direct('movie substituted',lambda c,p,e:write(c/'yuga-ultimate-studies.mp4','replacement'))
 staged('cannot substitute historical traversal directory',fn=lambda c,p,a:shutil.rmtree(p/release.MYTHIC_TRAVERSAL_CAPTURE_DIRECTORY))
 staged('changed committed mythic capture rejects',git_failure=lambda argv:'changed' if argv[0]=='diff' and any(release.MYTHIC_ULTIMATE_CAPTURE_DIRECTORY in str(v) for v in argv) else None)
 def untracked(argv):
  if argv[0]=='ls-files' and any(release.MYTHIC_ULTIMATE_CAPTURE_DIRECTORY in str(v) for v in argv):raise subprocess.CalledProcessError(1,['git',*argv])
 staged('untracked mythic capture rejects',git_failure=untracked)
 check('validator source unchanged during test',True,None if before==release.digest(PROJECT/'tools/release-native.py') else 'source changed')
 report={'passed':all(c['passed'] for c in CHECKS),'checks':CHECKS,'source_sha256':{str(p.relative_to(PROJECT)):release.digest(p) for p in (HERE,PROJECT/'tools/release-native.py',HERE.with_name('release_traversal_cases.py'))},'scope':'Synthetic packages/images and mocked decoder/Git; validates fail-closed publication behavior, not pixels, builds or a real release.'}
 if a.report:write(a.report,report)
 print(json.dumps({'passed':report['passed'],'checks':len(CHECKS),'failures':[c for c in CHECKS if not c['passed']]},indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
