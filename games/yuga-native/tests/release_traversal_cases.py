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


def staging_case(name, mutation=None, expect_success=False, tag_override=None, git_override=None):
    with tempfile.TemporaryDirectory(prefix='yuga-release-feature-test-') as temporary:
        repo, project, film, args = fixture(Path(temporary))
        if tag_override is not None: args.tag = tag_override
        if mutation: mutation(args, project)
        def fake_git(*arguments):
            return git_override(arguments) if git_override else COMMIT
        error = None
        with patch.object(release,'REPO',repo), patch.object(release,'PROJECT',project), patch.object(release,'FILM',film), \
             patch.object(release,'git',fake_git), patch.object(release,'validate_evidence',return_value={'passed':True}):
            try: release.stage(args)
            except (ValueError,KeyError,OSError,TypeError) as caught: error = str(caught)
        check(name, (error is None)==expect_success, expected_success=expect_success, rejection=error)


def verify_case(name, mutation, expect_success=False):
    with tempfile.TemporaryDirectory(prefix='yuga-release-feature-verify-') as temporary:
        repo, project, film, args = fixture(Path(temporary))
        with patch.object(release,'REPO',repo), patch.object(release,'PROJECT',project), patch.object(release,'FILM',film), \
             patch.object(release,'git',return_value=COMMIT), patch.object(release,'validate_evidence',return_value={'passed':True}):
            try:
                release.stage(args)
            except (ValueError,KeyError,OSError,TypeError) as caught:
                check(name, False, fixture_setup_error=str(caught))
                return
        mutation(args.output)
        error = None
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
    check('workflow immutable official action pins',all(re.fullmatch(r'actions/(checkout|upload-artifact|download-artifact)@[0-9a-f]{40}',pin)
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
