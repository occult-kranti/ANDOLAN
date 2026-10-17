#!/usr/bin/env python3
"""Isolated siege-release counterexamples; synthetic data, no network/Git mutation."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
base=load('siege_release_base_fixture',HERE.with_name('release_traversal_cases.py'))
release=base.release
runner=load('siege_runner_review_fixture',PROJECT/'tools/run-siege-capture.py')
TAG='yuga-traversal-armies-review-fixture-siege'
CHECKS=[]
SIGNATURE={'width':1280,'height':720,'frames':180,'fps':30,'duration_seconds':6.0}
write=base.write

def fixture(path):
    repo,project,film,args=base.fixture(path)
    args.tag=TAG
    for name in ('tools/capture-siege.gd','tools/run-siege-capture.py','scripts/lane_vehicle_art.gd','scripts/siege_effects.gd','assets/world/architecture.glb','assets/world/nature.glb'):
        write(project/name,'synthetic source '+name)
    write(project/'docs/SIEGE_MILESTONE.md','Synthetic milestone; no gameplay claim.\n')
    write(project/'assets/audio/siege/provenance.json',{'synthetic':True})
    paths=set(release.CAPTURE_FIXED_SOURCES)
    for folder in ('scripts','scenes','assets'):
        paths.update(p.relative_to(project).as_posix() for p in (project/folder).rglob('*') if p.is_file())
    exported={'git':{'head':base.COMMIT},'source':{'files':{name:release.record(project/name) for name in paths if name=='project.godot' or name.split('/')[0] in ('scripts','scenes','assets')}}}
    write(args.build/'native-export-manifest.json',exported)
    traversal=project/release.TRAVERSAL_CAPTURE_DIRECTORY
    base.mutate_capture(traversal,lambda r:r.update(source_sha256={'res://'+name:release.digest(project/name) for name in paths}))
    paths.update(('tools/capture-siege.gd','tools/run-siege-capture.py'))
    capture=project/release.SIEGE_CAPTURE_DIRECTORY;capture.mkdir(parents=True)
    frames=[]
    for index in range(180):
        name=f'frame-{index:05d}.png'
        data=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II',1280,720)+name.encode()
        (capture/name).write_bytes(data)
        image={'file':name,'sha256':release.digest(capture/name),'width':1280,'height':720,'draw_calls':2,'rendered_objects':3,'rendered_primitives':4}
        frames.append({'index':index,'physics_tick_delta':2,'physics_tick':100+2*(index+1),'render_frame':index+20,'finite':True,'image':image,'army':{'finite':True},'effects':{'finite':True}})
        if index in release.SIEGE_SELECTED_FRAMES:(capture/f'siege-frame-{index:05d}.png').write_bytes(data)
    imports={}
    for i,name in enumerate(('assets/heroes/rama-production.glb','assets/world/architecture.glb','assets/world/nature.glb')):
        imported=f'.godot/imported/synthetic-{i}.scn';write(project/imported,'synthetic verified import')
        imports['res://'+name]={'fresh':True,'imported':'res://'+imported,'sha256':release.digest(project/imported)}
    render={'schema':1,'complete':True,'failure':'','renderer':'forward_plus','display':'x11','fps':30,'physics_hz':60,'time_scale':1.0,'take_physics_ticks':360,'take_start_tick':100,'width':1280,'height':720,'frames':frames,'source_sha256':{'res://'+name:release.digest(project/name) for name in paths},'imports':imports,'outcomes':{name:True for name in ('windup','impact','vehicles_moved','finite')},'events':[{'physics_tick':102,'event':{'kind':'windup'}},{'physics_tick':150,'event':{'kind':'impact','cancelled':False}}]}
    write(capture/'siege-render-review.json',render)
    write(capture/'yuga-siege-preview.mp4','synthetic video bytes; decoding mocked')
    video={'complete':True,'file':'yuga-siege-preview.mp4',**release.record(capture/'yuga-siege-preview.mp4'),'capture_report_sha256':release.digest(capture/'siege-render-review.json'),'probe':{'streams':[{'codec_type':'video','codec_name':'h264','width':1280,'height':720,'nb_read_frames':'180','avg_frame_rate':'30/1'}],'format':{'duration':'6.000000'}}}
    write(capture/'siege-video.json',video)
    write(capture/'SIEGE-RENDER-REVIEW.md','Synthetic review; no actual visual-quality approval.\n')
    return repo,project,film,args,capture,exported

def render_mutation(capture,change):
    path=capture/'siege-render-review.json';data=json.loads(path.read_text());change(data);write(path,data)
    video_path=capture/'siege-video.json';video=json.loads(video_path.read_text());video['capture_report_sha256']=release.digest(path);write(video_path,video)

def video_mutation(capture,change):
    path=capture/'siege-video.json';data=json.loads(path.read_text());change(data);write(path,data)

def record(name,expect,error,**details):
    CHECKS.append({'name':name,'passed':(error is None)==expect,'expected_success':expect,'rejection':error,**details})

def direct_case(name,mutation=None,expect=False,decode=False,decode_failure=False,target='release'):
    with tempfile.TemporaryDirectory(prefix='yuga-siege-release-case-') as temporary:
        repo,project,film,args,capture,exported=fixture(Path(temporary))
        if mutation:mutation(capture,project,exported)
        error=None
        with patch.object(release,'PROJECT',project),patch.object(release,'probe_traversal_movie',return_value=SIGNATURE,side_effect=ValueError('mock decoder rejected movie') if decode_failure else None) as decoder:
            try:
                if target=='runner':runner.validate(json.loads((capture/'siege-render-review.json').read_text()),capture,project)
                else:release.validate_siege_capture(capture,exported,decode=decode)
            except (ValueError,KeyError,OSError,TypeError,IndexError) as caught:error=str(caught)
        record(name,expect,error,decoder_calls=decoder.call_count)
        if decode and expect and error is None and decoder.call_count != 1:CHECKS[-1]["passed"]=False

def staged_case(name,mutation=None,expect=False,verify_mutation=None,tag=TAG):
    with tempfile.TemporaryDirectory(prefix='yuga-siege-staging-case-') as temporary:
        repo,project,film,args,capture,exported=fixture(Path(temporary));args.tag=tag
        if mutation:mutation(capture,project,args)
        error=None
        with patch.object(release,'REPO',repo),patch.object(release,'PROJECT',project),patch.object(release,'FILM',film),patch.object(release,'git',side_effect=lambda *a:base.COMMIT if a[0]=='rev-parse' else ''),patch.object(release,'validate_evidence',return_value={'passed':True}),patch.object(release,'probe_traversal_movie',return_value=SIGNATURE) as decoder:
            try:
                release.stage(args)
                if verify_mutation:
                    verify_mutation(args.output);base.update_inventory(args.output)
                    release.verify(args.output,tag,base.COMMIT)
            except (ValueError,KeyError,OSError,TypeError,IndexError) as caught:error=str(caught)
        record(name,expect,error,decoder_calls=decoder.call_count)
        expected_decodes=2 if release.siege_release(tag) else 1
        if expect and error is None and decoder.call_count != expected_decodes:CHECKS[-1]["passed"]=False

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path);args=parser.parse_args()
    direct_case('valid siege capture control',expect=True)
    direct_case('fresh decode control',expect=True,decode=True)
    direct_case('fresh decoder rejection',decode=True,decode_failure=True)
    direct_case('valid raw runner capture control',expect=True,target='runner')
    staged_case('valid siege staging and verification control',expect=True)
    staged_case('non-siege traversal tag remains compatible',expect=True,tag='yuga-traversal-armies-review-fixture')
    CHECKS.append({'name':'siege tag selection is bounded','passed':release.siege_release(TAG) and not release.siege_release('yuga-confluence-duel-review-siege') and not release.siege_release('yuga-traversal-armies-review')})
    mutations={
      'incomplete capture':lambda r:r.update(complete=False),
      'reported renderer failure':lambda r:r.update(failure='capture failed'),
      'headless capture':lambda r:r.update(display='headless'),
      'zero time scale':lambda r:r.update(time_scale=0),
      'nonfinite time scale':lambda r:r.update(time_scale=float('nan')),
      'missing time scale':lambda r:r.pop('time_scale'),
      'wrong render dimensions':lambda r:r.update(width=960),
      'missing sequence frame':lambda r:r['frames'].pop(),
      'physics discontinuity':lambda r:r['frames'][44].update(physics_tick=9999),
      'incorrect per-frame tick delta':lambda r:r['frames'][44].update(physics_tick_delta=1),
      'nonfinite frame':lambda r:r['frames'][44].update(finite=False),
      'numeric fake finite flag':lambda r:r['frames'][44].update(finite=1),
      'no observed impact':lambda r:r['outcomes'].update(impact=False),
      'invalid raw frame name':lambda r:r['frames'][44]['image'].update(file='../frame.png'),
      'zero actual draw calls':lambda r:r['frames'][44]['image'].update(draw_calls=0),
      'missing source set':lambda r:r.update(source_sha256={}),
      'changed source hash':lambda r:r['source_sha256'].update({'res://scripts/lane_vehicle_art.gd':'0'*64}),
      'unsafe source path':lambda r:r['source_sha256'].update({'res://../outside':'0'*64}),
      'nonadvancing rendered frame counter':lambda r:r['frames'][44].update(render_frame=1),
      'missing nonretained frame hash':lambda r:r['frames'][44]['image'].pop('sha256'),
      'invalid nonretained frame hash':lambda r:r['frames'][44]['image'].update(sha256='invalid'),
      'negative starting tick':lambda r:(r.update(take_start_tick=-1000),[row.update(physics_tick=-1000+2*(i+1)) for i,row in enumerate(r['frames'])]),
    }
    for name,change in mutations.items():direct_case(name,lambda c,p,e,f=change:render_mutation(c,f))
    for name in sorted(release.SIEGE_CAPTURE_ASSETS):
        direct_case('capture helper requires '+name,lambda c,p,e,n=name:(c/n).unlink())
        staged_case('released asset cannot be omitted and resealed: '+name,verify_mutation=lambda out,n=name:(out/n).unlink())
    for name in ('SIEGE-MILESTONE.md','SIEGE-AUDIO-PROVENANCE.json','ci-siege-army.json','ci-vehicle-art.json','ci-siege-effects.json','ci-siege-audio.json'):
        staged_case('released siege requirement: '+name,verify_mutation=lambda out,n=name:(out/n).unlink())
    direct_case('changed retained PNG bytes',lambda c,p,e:(c/'siege-frame-00045.png').write_text('substitute'))
    direct_case('changed checkout source bytes',lambda c,p,e:write(p/'scripts/lane_vehicle_art.gd','changed'))
    direct_case('missing checkout source',lambda c,p,e:(p/'tools/capture-siege.gd').unlink())
    direct_case('changed export source record',lambda c,p,e:e['source']['files']['scripts/lane_vehicle_art.gd'].update(sha256='0'*64))
    direct_case('missing exported runtime file',lambda c,p,e:e['source']['files'].pop('scripts/lane_vehicle_art.gd'))
    direct_case('extra exported runtime file',lambda c,p,e:e['source']['files'].update({'scripts/unrecorded.gd':{'bytes':1,'sha256':'0'*64}}))
    direct_case('movie bytes substituted',lambda c,p,e:write(c/'yuga-siege-preview.mp4','other movie'))
    direct_case('movie links other capture',lambda c,p,e:video_mutation(c,lambda v:v.update(capture_report_sha256='0'*64)))
    for key,value in [('nb_read_frames','179'),('avg_frame_rate','24/1'),('width',960)]:
        direct_case('movie metadata '+key,lambda c,p,e,k=key,v=value:video_mutation(c,lambda row:row['probe']['streams'][0].update({k:v})))
    direct_case('nonfinite movie duration',lambda c,p,e:video_mutation(c,lambda row:row['probe']['format'].update(duration='nan')))
    for name,change in [('runner draw counter regression',mutations['nonadvancing rendered frame counter']),('runner wrong per-frame tick delta',mutations['incorrect per-frame tick delta']),('runner wrong dimensions',mutations['wrong render dimensions']),('runner empty imported-asset proof',lambda r:r.update(imports={}))]:
        direct_case(name,lambda c,p,e,f=change:render_mutation(c,f),target='runner')
    for name in ('zero time scale','nonfinite time scale','missing time scale'):
        direct_case('runner '+name,lambda c,p,e,f=mutations[name]:render_mutation(c,f),target='runner')
    direct_case('runner missing actual raw PNG',lambda c,p,e:(c/'frame-00044.png').unlink(),target='runner')
    direct_case('runner changed actual raw PNG',lambda c,p,e:(c/'frame-00044.png').write_text('changed'),target='runner')
    for gate in ('siege-army','vehicle-art','siege-effects','siege-audio'):
        staged_case('failed stage gate '+gate,mutation=lambda c,p,a,g=gate:write(a.checks/(g+'.json'),{'passed':False}))
    reviewed=[PROJECT/'tools/release-native.py',PROJECT/'tools/capture-siege.gd',PROJECT/'tools/run-siege-capture.py',HERE]
    report={'passed':all(row['passed'] for row in CHECKS),'checks':CHECKS,'source_sha256':{p.relative_to(PROJECT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in reviewed},'scope':'Synthetic temporary files and mocked existing archive/decode/git checks only. No network, credential, repository, tag or release mutation; no rendering. Actual encoded media validation remains separate.'}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':len(CHECKS),'failures':[row for row in CHECKS if not row['passed']]},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
