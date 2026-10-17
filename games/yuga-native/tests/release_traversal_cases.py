#!/usr/bin/env python3
"""Isolated release gate counterexamples. No real GitHub or git mutation.

Temporary synthetic packages prove staging/verification controls, not game build
quality. Existing publication-operation fixtures use only mocked subprocesses.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import struct
import subprocess
import tempfile
import types
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / 'tools/release-native.py'
SPEC = importlib.util.spec_from_file_location('release_traversal_fixture', SOURCE)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
TAG = 'yuga-traversal-armies-review-fixture'
COMMIT = 'a' * 40
CHECKS = []


def check(name, passed, **details):
    CHECKS.append({'name': name, 'passed': bool(passed), 'details': details})


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, dict): path.write_text(json.dumps(value, indent=2) + '\n')
    else: path.write_text(value)


def fixture(root):
    repo = root / 'repository'
    project = repo / 'games/yuga-native'
    film = project / 'docs/evidence/combat-film-r4'
    build, engines, checks = root/'build', root/'engines', root/'checks'
    packages = {}
    for platform in ('linux', 'windows'):
        name = 'yuga-native-' + platform + '-x86_64.zip'
        write(build/name, 'synthetic previously validated package ' + platform)
        packages[platform] = {'filename':name, **release.record(build/name)}
    write(build/'native-package-manifest.json', {'git':{'head':COMMIT},'packages':packages})
    write(build/'native-export-manifest.json', {'git':{'head':COMMIT}})
    write(engines/'engine-downloads.json', {'synthetic':True})
    for name in release.CHECKS + release.TRAVERSAL_CHECKS:
        write(checks/(name+'.json'), {'passed':True,'fixture':True})
    archive_files = {}
    for name in ('yuga-confluence-duel.mp4','combat-film-render.json','combat-film-video.json','media-release-check.json'):
        write(film/name, 'synthetic archived content')
        archive_files[name] = release.record(film/name)
    write(film/'archive-manifest.json', {'files':archive_files})
    write(film/'REVIEW.md', 'Synthetic archive review; actual archive validator mocked in this unit fixture.\n')
    write(project/'docs/RELEASE_TRAVERSAL_ARMIES.md', 'Synthetic feature release notes.\n')
    write(project/'docs/RELEASE_CONFLUENCE_DUEL.md', 'Synthetic base release notes.\n')
    write(project/'docs/TRAVERSAL_ARMY_VERIFICATION.md', 'Synthetic traversal verification document.\n')
    loop = project/'assets/audio/traversal/lane-procession-loop.wav'
    write(loop, 'synthetic original loop bytes')
    write(project/'NOTICE/TRAVERSAL-AUDIO-PROVENANCE.json', {'assets':[{'asset':'assets/audio/traversal/lane-procession-loop.wav', **release.record(loop)}]})
    for name in release.CAPTURE_FIXED_SOURCES | release.CAPTURE_REQUIRED_RUNTIME:
        write(project/name, 'synthetic captured source '+name)
    paths = set(release.CAPTURE_FIXED_SOURCES)
    for folder in ('scripts','scenes','assets'):
        paths.update(p.relative_to(project).as_posix() for p in (project/folder).rglob('*') if p.is_file())
    runtime = {name:release.record(project/name) for name in paths if name=='project.godot' or name.split('/')[0] in ('scripts','scenes','assets')}
    write(build/'native-export-manifest.json', {'git':{'head':COMMIT},'source':{'files':runtime}})
    capture = project/release.TRAVERSAL_CAPTURE_DIRECTORY
    capture.mkdir(parents=True)
    images={}
    for name in release.TRAVERSAL_STILLS:
        # Synthetic headers test archive identity and dimension controls, not PNG decoding.
        data=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II',1280,720)+name.encode()
        (capture/name).write_bytes(data)
        images[name]={'file':name,'sha256':release.digest(capture/name),'width':1280,'height':720,
                      'draw_calls':2,'rendered_objects':3,'rendered_primitives':4}
    frames=[]
    for index in range(180):
        image={'file':f'frame-{index:05d}.png','sha256':'b'*64,'width':1280,'height':720,
               'draw_calls':2,'rendered_objects':3,'rendered_primitives':4}
        if index==145:image['sha256']=images['still-05-actual-take-hud.png']['sha256']
        frames.append({'index':index,'physics_tick_delta':2,'physics_tick':100+2*(index+1),
                       'render_frame':index+1,'finite':True,'pose_sha256':'a'*64,'image':image,
                       'presentation_seconds':index/30,'sample_end_simulation_seconds':(index+1)/30})
    render={'complete':True,'failure':'','preview':False,'kind':'actual-staged-native-traversal-input',
            'renderer':'forward_plus','display':'x11','expected_frames':180,'take_physics_ticks':360,
            'physics_hz':60,'fps':30,'width':1280,'height':720,'take_start_tick':100,'frames':frames,
            'stills':[{'image':row,**({'take_frame':145} if name=='still-05-actual-take-hud.png' else {})} for name,row in images.items()],
            'outcomes':{key:True for key in ('grapple','flight','visible_rope','pose_overlay','pose_finite')},
            'army_staging':{'observed_queued_attack':True},
            'source_sha256':{'res://'+name:release.digest(project/name) for name in paths}}
    write(capture/'traversal-render-review.json',render)
    write(capture/'yuga-traversal-preview.mp4','synthetic movie bytes; actual decoder mocked')
    video={'complete':True,'file':'yuga-traversal-preview.mp4',**release.record(capture/'yuga-traversal-preview.mp4'),
           'capture_report_sha256':release.digest(capture/'traversal-render-review.json'),
           'probe':{'streams':[{'codec_type':'video','codec_name':'h264','width':1280,'height':720,
                               'nb_read_frames':'180','avg_frame_rate':'30/1'}],'format':{'duration':'6.000000'}}}
    write(capture/'traversal-video.json',video)
    write(capture/'REVIEW.md','Synthetic full capture review; no pixels decoded in this unit fixture.\n')
    args = argparse.Namespace(build=build,engines=engines,checks=checks,output=root/'output',tag=TAG,commit=COMMIT)
    return repo, project, film, args


def update_inventory(directory):
    manifest = directory/'release-manifest.json'
    inventory = json.loads(manifest.read_text())
    inventory['files'] = {p.name:release.record(p) for p in directory.iterdir()
                          if p.name not in {'release-manifest.json','SHA256SUMS'}}
    if 'sources' in inventory:
        inventory['sources'] = {k:v for k,v in inventory['sources'].items() if k in inventory['files']}
    release.write_json(manifest, inventory)
    rows = {**inventory['files'],'release-manifest.json':release.record(manifest)}
    (directory/'SHA256SUMS').write_text(''.join(f"{row['sha256']}  {name}\n" for name,row in sorted(rows.items())))


def staging_case(name, mutation=None, expect_success=False, tag_override=None, git_override=None, decode_failure=False):
    with tempfile.TemporaryDirectory(prefix='yuga-release-feature-test-') as temporary:
        repo, project, film, args = fixture(Path(temporary))
        if tag_override is not None: args.tag = tag_override
        if mutation: mutation(args, project)
        def fake_git(*arguments):
            if arguments[0]!='rev-parse':return ''
            return git_override(arguments) if git_override else COMMIT
        error = None
        with patch.object(release,'REPO',repo), patch.object(release,'PROJECT',project), patch.object(release,'FILM',film), \
             patch.object(release,'git',fake_git), patch.object(release,'validate_evidence',return_value={'passed':True}), \
             patch.object(release,'probe_traversal_movie',return_value={'width':1280,'height':720,'frames':180,'fps':30,'duration_seconds':6.0},
                          side_effect=ValueError('Mock decoder rejected video') if decode_failure else None) as decoder:
            try: release.stage(args)
            except (ValueError,KeyError,OSError,TypeError) as caught: error = str(caught)
        okay=(error is None)==expect_success
        if expect_success and release.traversal_release(args.tag):okay=okay and decoder.call_count==1
        check(name, okay, expected_success=expect_success, rejection=error, fresh_decode_calls=decoder.call_count)


def verify_case(name, mutation, expect_success=False):
    with tempfile.TemporaryDirectory(prefix='yuga-release-feature-verify-') as temporary:
        repo, project, film, args = fixture(Path(temporary))
        with patch.object(release,'REPO',repo), patch.object(release,'PROJECT',project), patch.object(release,'FILM',film), \
             patch.object(release,'git',side_effect=lambda *a:COMMIT if a[0]=='rev-parse' else ''), \
             patch.object(release,'validate_evidence',return_value={'passed':True}), \
             patch.object(release,'probe_traversal_movie',return_value={'width':1280,'height':720,'frames':180,'fps':30,'duration_seconds':6.0}):
            try:
                release.stage(args)
            except (ValueError,KeyError,OSError,TypeError) as caught:
                check(name, False, fixture_setup_error=str(caught))
                return
        mutation(args.output)
        error = None
        with patch.object(release,'PROJECT',project):
            try: release.verify(args.output,TAG,COMMIT)
            except (ValueError,KeyError,OSError,TypeError) as caught: error = str(caught)
        check(name,(error is None)==expect_success,expected_success=expect_success,rejection=error)


def remove_and_reseal(filename):
    def mutate(directory):
        (directory/filename).unlink()
        update_inventory(directory)
    return mutate


def fail_and_reseal(filename):
    def mutate(directory):
        report=json.loads((directory/filename).read_text())
        report['passed']=False
        write(directory/filename,report)
        update_inventory(directory)
    return mutate


def mutate_capture(directory, change):
    path=directory/'traversal-render-review.json'
    render=json.loads(path.read_text());change(render);write(path,render)
    video_path=directory/'traversal-video.json'
    video=json.loads(video_path.read_text());video['capture_report_sha256']=release.digest(path);write(video_path,video)


def capture_counterexamples():
    for name in sorted(release.TRAVERSAL_CAPTURE_ASSETS):
        verify_case('feature capture asset required: '+name,remove_and_reseal(name))
    mutations={
        'incomplete':lambda r:r.update(complete=False),
        'reported failure':lambda r:r.update(failure='stopped early'),
        'preview only':lambda r:r.update(preview=True),
        'short frame sequence':lambda r:r['frames'].pop(),
        'wrong total physics ticks':lambda r:r.update(take_physics_ticks=359),
        'physics discontinuity':lambda r:r['frames'][40].update(physics_tick=9999),
        'draw counter did not advance':lambda r:r['frames'][40].update(render_frame=1),
        'incorrect frame presentation time':lambda r:r['frames'][40].update(presentation_seconds=4),
        'headless render claim':lambda r:r.update(display='headless'),
        'missing flight observation':lambda r:r['outcomes'].update(flight=False),
        'nonfinite pose flag':lambda r:r['frames'][40].update(finite=False),
        'zero actual draw calls':lambda r:r['frames'][40]['image'].update(draw_calls=0),
        'incorrect HUD take association':lambda r:r['stills'][next(i for i,x in enumerate(r['stills']) if x['image']['file']=='still-05-actual-take-hud.png')].update(take_frame=144),
        'missing recorded army engagement':lambda r:r['army_staging'].update(observed_queued_attack=False),
        'missing source inventory':lambda r:r.update(source_sha256={}),
        'source hash differs from checkout':lambda r:r['source_sha256'].update({'res://scripts/player.gd':'0'*64}),
        'unsafe captured source path':lambda r:r['source_sha256'].update({'res://../outside':'0'*64}),
    }
    for name,mutate in mutations.items():
        def alter(directory,change=mutate):
            mutate_capture(directory,change);update_inventory(directory)
        verify_case('self-consistent capture rejected: '+name,alter)
    staging_case('preview capture blocked before staging',lambda a,p:mutate_capture(p/release.TRAVERSAL_CAPTURE_DIRECTORY,lambda r:r.update(preview=True)))
    staging_case('missing capture blocked before staging',lambda a,p:(p/release.TRAVERSAL_CAPTURE_DIRECTORY/'traversal-render-review.json').unlink())
    staging_case('current runtime differs from captured runtime',lambda a,p:write(p/'scripts/player.gd','changed runtime after capture'))
    staging_case('fresh decoder failure blocks staging',decode_failure=True)
    def substitute_movie(directory):
        (directory/'yuga-traversal-preview.mp4').write_text('substituted movie');update_inventory(directory)
    verify_case('self-consistent inventory cannot substitute the captured movie',substitute_movie)
    def break_movie_link(directory):
        path=directory/'traversal-video.json';video=json.loads(path.read_text());video['capture_report_sha256']='0'*64
        write(path,video);update_inventory(directory)
    verify_case('movie must link the actual capture report',break_movie_link)
    def wrong_export_hash(directory):
        path=directory/'native-export-manifest.json';exported=json.loads(path.read_text())
        exported['source']['files']['scripts/player.gd']['sha256']='0'*64;write(path,exported);update_inventory(directory)
    verify_case('capture must match exported runtime source bytes',wrong_export_hash)
    def omit_export_file(directory):
        path=directory/'native-export-manifest.json';exported=json.loads(path.read_text())
        del exported['source']['files']['scripts/player.gd'];write(path,exported);update_inventory(directory)
    verify_case('capture source cannot be omitted from export inventory',omit_export_file)
    for field,value in [('nb_read_frames','24'),('width',960),('avg_frame_rate','24/1')]:
        def wrong_probe(directory,key=field,bad=value):
            path=directory/'traversal-video.json';video=json.loads(path.read_text());video['probe']['streams'][0][key]=bad
            write(path,video);update_inventory(directory)
        verify_case('movie probe rejects incorrect '+field,wrong_probe)


def feature_publication_cases():
    for name in ('valid full capture','missing capture','preview capture','incomplete capture','substituted movie','runtime changed'):
        with tempfile.TemporaryDirectory(prefix='yuga-feature-publication-') as temporary:
            repo,project,film,args=fixture(Path(temporary))
            with patch.object(release,'REPO',repo), patch.object(release,'PROJECT',project), patch.object(release,'FILM',film), \
                 patch.object(release,'git',side_effect=lambda *a:COMMIT if a[0]=='rev-parse' else ''), \
                 patch.object(release,'validate_evidence',return_value={'passed':True}), \
                 patch.object(release,'probe_traversal_movie',return_value={'width':1280,'height':720,'frames':180,'fps':30,'duration_seconds':6.0}):
                release.stage(args)
                if name=='missing capture':(args.output/'traversal-render-review.json').unlink()
                elif name=='preview capture':mutate_capture(args.output,lambda r:r.update(preview=True))
                elif name=='incomplete capture':mutate_capture(args.output,lambda r:r.update(complete=False))
                elif name=='substituted movie':(args.output/'yuga-traversal-preview.mp4').write_text('substituted')
                elif name=='runtime changed':write(project/'scripts/player.gd','changed runtime after validated staging')
                update_inventory(args.output)
                calls=[]
                def fake_run(argv,**kwargs):
                    calls.append(argv)
                    if argv[:2]==['gh','api']:
                        data={'object':{'type':'commit','sha':COMMIT}} if '/git/ref/tags/' in argv[2] else {'draft':True,'target_commitish':COMMIT}
                        return types.SimpleNamespace(returncode=0,stdout=json.dumps(data),stderr='')
                    if argv[:3]==['gh','release','download']:
                        shutil.copytree(args.output,Path(argv[argv.index('--dir')+1]),dirs_exist_ok=True)
                    if argv[:3] not in (['gh','release','upload'],['gh','release','download'],['gh','release','edit']):
                        raise AssertionError('Unexpected external command in fixture')
                    return types.SimpleNamespace(returncode=0,stdout='',stderr='')
                error=None;result=None
                with patch.object(release.subprocess,'run',fake_run):
                    try:result=release.publish(argparse.Namespace(directory=args.output,tag=TAG,commit=COMMIT,repository='fixture/repository'))
                    except (ValueError,KeyError,OSError,TypeError) as caught:error=str(caught)
                edits=[c for c in calls if c[:3]==['gh','release','edit']]
                okay=(result is not None and result.get('published') is True and len(edits)==1 and calls[-1]==edits[0]) if name=='valid full capture' else (error is not None and not calls)
                check('mocked feature publication: '+name,okay,github_calls=len(calls),publication_calls=len(edits),rejection=error)


def legacy_publication_cases():
    # Reuse the archived review's mocked publication scenarios but stop before
    # its old tag-only workflow assertion and its historical evidence writer.
    source=PROJECT/'tests/evidence/combat-film-release-review-fixtures.py.txt'
    prefix=source.read_text().split('workflow = yaml.load',1)[0].replace('\nimport yaml\n','\n')
    scope={'__name__':'legacy_mocked_release_fixtures'}
    try:
        exec(compile(prefix,str(source),'exec'),scope)
        for row in scope['checks']:
            check('publication: '+row['name'],row['passed'],**row['details'])
    except Exception as caught:
        check('legacy mocked publication fixtures',False,error=repr(caught))


def workflow_cases():
    workflow=PROJECT.parents[1]/'.github/workflows/yuga-native-release.yml'
    text=workflow.read_text()
    build=text.split('\n  build:',1)[1].split('\n  release:',1)[0]
    publish=text.split('\n  release:',1)[1]
    check('workflow privilege separation and successful-build dependency',
          '\npermissions: {}\n' in text and '    permissions:\n      contents: read\n' in build
          and '    permissions:\n      contents: write\n' in publish and '    needs: build\n' in publish)
    check('workflow immutable official action pins',all(re.fullmatch(r'actions/(checkout|setup-node|upload-artifact|download-artifact)@[0-9a-f]{40}',pin)
          for pin in re.findall(r'uses: (\S+)',text)))
    check('workflow keeps checkout credentials disabled',text.count('persist-credentials: false')==2)
    check('workflow has no continue-on-error bypass','continue-on-error' not in text)
    reports=set(re.findall(r'--report(?:=| )"\$RUNNER_TEMP/checks/([a-z-]+)\.json"',text))
    check('workflow writes every required report filename',set(release.CHECKS+release.TRAVERSAL_CHECKS)<=reports,
          missing=sorted(set(release.CHECKS+release.TRAVERSAL_CHECKS)-reports))
    check('workflow explicit pinned numerical interpreter','numpy==2.3.5 scipy==1.15.3' in text and
          '"$RUNNER_TEMP/media-venv/bin/python" games/yuga-native/tools/audio/build-traversal-audio.py --check' in text)
    check('workflow release artifact name matches upload and download',text.count('name: yuga-native-release-assets')==2)
    lines=text.splitlines();blocks=0;syntax_ok=True
    for index,line in enumerate(lines):
        match=re.fullmatch(r'(\s*)run: \|',line)
        if not match: continue
        indent=len(match.group(1));body=[]
        for following in lines[index+1:]:
            if following.strip() and len(following)-len(following.lstrip())<=indent:break
            body.append(following[indent+2:])
        commands='\n'.join(body)
        result=subprocess.run(['bash','-n'],input=commands,text=True,capture_output=True)
        syntax_ok=syntax_ok and result.returncode==0 and 'set -euo pipefail' in commands
        blocks+=1
    check('all workflow shell blocks parse and fail fast',syntax_ok and blocks>=7,shell_blocks=blocks)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    staging_case('feature stage accepts all required gates',expect_success=True)
    staging_case('base film tag remains compatible',expect_success=True,tag_override='yuga-confluence-duel-review-fixture')
    for gate in release.TRAVERSAL_CHECKS:
        staging_case('missing stage gate '+gate,lambda a,p,g=gate:(a.checks/(g+'.json')).unlink())
        staging_case('failed stage gate '+gate,lambda a,p,g=gate:write(a.checks/(g+'.json'),{'passed':False}))
        verify_case('self-consistent inventory missing '+gate,remove_and_reseal('ci-'+gate+'.json'))
        verify_case('self-consistent failed report '+gate,fail_and_reseal('ci-'+gate+'.json'))
    for filename in ('lane-procession-loop.wav','TRAVERSAL-AUDIO-PROVENANCE.json','TRAVERSAL-VERIFICATION.md',
                     'yuga-native-linux-x86_64.zip','yuga-native-windows-x86_64.zip','native-package-manifest.json','native-export-manifest.json'):
        verify_case('self-consistent inventory missing '+filename,remove_and_reseal(filename))
    staging_case('unsafe tag rejected',tag_override='yuga-traversal-armies-../../outside')
    staging_case('unrecognized tag rejected',tag_override='feature-release-2026')
    staging_case('checkout differs from requested commit',git_override=lambda a:'b'*40 if a[1:]==(COMMIT+'^{commit}',) else COMMIT)
    staging_case('local tag differs from checkout',git_override=lambda a:'b'*40 if a[1].startswith('refs/tags/') else COMMIT)
    def wrong_package(a,p):
        manifest=json.loads((a.build/'native-package-manifest.json').read_text());manifest['git']['head']='b'*40;write(a.build/'native-package-manifest.json',manifest)
    staging_case('package source commit mismatch',wrong_package)
    def unsafe_filename(a,p):
        manifest=json.loads((a.build/'native-package-manifest.json').read_text());manifest['packages']['linux']['filename']='../outside.zip';write(a.build/'native-package-manifest.json',manifest)
    staging_case('package path traversal rejected',unsafe_filename)
    def symlink_asset(directory):
        path=directory/'lane-procession-loop.wav';content=path.read_bytes();path.unlink();outside=directory.parent/'outside.wav';outside.write_bytes(content);path.symlink_to(outside);update_inventory(directory)
    verify_case('self-consistent symlink asset rejected',symlink_asset)
    def changed_sound(directory):
        (directory/'lane-procession-loop.wav').write_text('substituted loop');update_inventory(directory)
    verify_case('self-consistent changed loop conflicts with provenance',changed_sound)
    def changed_zip(directory):
        (directory/'yuga-native-linux-x86_64.zip').write_text('substituted package');update_inventory(directory)
    verify_case('self-consistent changed ZIP conflicts with package manifest',changed_zip)
    def changed_source(directory):
        manifest=json.loads((directory/'native-export-manifest.json').read_text());manifest['git']['head']='b'*40
        write(directory/'native-export-manifest.json',manifest);update_inventory(directory)
    verify_case('self-consistent package source mismatch rejected',changed_source)
    def numeric_pass(directory):
        write(directory/'ci-stress.json',{'passed':1});update_inventory(directory)
    verify_case('integer one cannot substitute for boolean pass',numeric_pass)
    def platform_alias(directory):
        path=directory/'native-package-manifest.json';manifest=json.loads(path.read_text())
        manifest['packages']['windows']=manifest['packages']['linux'].copy()
        write(path,manifest);update_inventory(directory)
    verify_case('Windows cannot alias the Linux package',platform_alias)
    def wrong_audio_path(directory):
        path=directory/'TRAVERSAL-AUDIO-PROVENANCE.json';notice=json.loads(path.read_text())
        notice['assets'][0]['asset']='unrelated/lane-procession-loop.wav'
        write(path,notice);update_inventory(directory)
    verify_case('audio provenance requires the exact source asset path',wrong_audio_path)
    capture_counterexamples()
    feature_publication_cases()
    legacy_publication_cases()
    workflow_cases()
    reviewed=[SOURCE,PROJECT/'tools/package-native.py',PROJECT.parents[1]/'.github/workflows/yuga-native-release.yml',Path(__file__)]
    report={'passed':all(x['passed'] for x in CHECKS),'checks':CHECKS,
      'source_sha256':{str(path.relative_to(PROJECT.parents[1])):hashlib.sha256(path.read_bytes()).hexdigest() for path in reviewed},
      'scope':'Temporary synthetic artifacts plus mocked git/GitHub operations only; no credentials, requests, releases, tags, graphics or runtime edits.',
      'limits':'Actual build/export checks and workflow CI execution remain separate. Synthetic passing reports stand in for completed game suites.'}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':len(CHECKS),'failures':[x for x in CHECKS if not x['passed']]},indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
