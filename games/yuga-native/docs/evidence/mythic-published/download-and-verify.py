#!/usr/bin/env python3
"""Read-only published release retrieval and comparison; never tags or publishes."""
from pathlib import Path, PurePosixPath
import argparse, datetime, hashlib, importlib.util, json, shutil, subprocess, sys, zipfile
ROOT=Path('/workspace/ANDOLAN'); PROJECT=ROOT/'games/yuga-native'
REPOSITORY='occult-kranti/ANDOLAN'
TAG='yuga-traversal-armies-2026-10-17-mythic'
COMMIT='e2dc0ecd3f6903e0c8af68b2c5717ba5947108ed'
LOCAL=Path('/workspace/scratch/yuga-next/mythic-package-r3')
DOWNLOAD=Path('/workspace/scratch/yuga-next/mythic-public-download')
EVIDENCE=PROJECT/'docs/evidence/mythic-published'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def record(path):
    sha=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):sha.update(block)
    return {'bytes':path.stat().st_size,'sha256':sha.hexdigest()}

def write(name,data):
    path=EVIDENCE/name
    if path.exists():raise ValueError('Refusing to overwrite evidence: '+name)
    path.write_text(json.dumps(data,indent=2)+'\n')

def run(argv):
    return subprocess.run(argv,check=True,capture_output=True,text=True,cwd=ROOT)

def api(endpoint):return json.loads(run(['gh','api',endpoint]).stdout)

def public_metadata():
    raw=api('repos/'+REPOSITORY+'/releases/tags/'+TAG)
    assert raw['draft'] is False and raw['prerelease'] is True and raw['tag_name']==TAG and raw.get('published_at'), 'Expected a published Mythic prerelease'
    return {k:raw.get(k) for k in ['id','node_id','html_url','tag_name','target_commitish','name','draft','prerelease','created_at','published_at']} | {'assets':[{k:a.get(k) for k in ['id','name','size','state','digest','created_at','updated_at','browser_download_url']} for a in raw['assets']]}

def remote_tag():
    obj=api('repos/'+REPOSITORY+'/git/ref/tags/'+TAG)['object'];chain=[]
    for _ in range(8):
        chain.append({k:obj.get(k) for k in ['type','sha','url']})
        if obj['type']=='commit':
            assert obj['sha']==COMMIT,'Public tag differs from the requested source commit'
            return chain
        assert obj['type']=='tag','Unexpected tag target type'
        obj=api('repos/'+REPOSITORY+'/git/tags/'+obj['sha'])['object']
    raise ValueError('Excessive annotated tag depth')

def zip_file_record(archive,name):
    info=archive.getinfo(name)
    assert info.file_size<512*1024*1024,'Unexpected oversized critical package member'
    sha=hashlib.sha256()
    with archive.open(info) as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):sha.update(block)
    return {'bytes':info.file_size,'sha256':sha.hexdigest()}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--publication-confirmed',action='store_true',required=True);parser.parse_args()
    assert not DOWNLOAD.exists() or not any(DOWNLOAD.iterdir()),'Download directory must be new/empty'
    assert not EVIDENCE.exists() or not any(EVIDENCE.iterdir()),'Evidence directory must be new/empty'
    DOWNLOAD.mkdir(parents=True,exist_ok=True);EVIDENCE.mkdir(parents=True,exist_ok=True)
    release=load('published_release_validator',PROJECT/'tools/release-native.py');packager=load('published_package_inspector',PROJECT/'tools/package-native.py')
    summary={'passed':False,'tag':TAG,'commit':COMMIT,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Public downloaded asset integrity, exact release identity, source-bound media and Linux engine/PCK comparison. No execution of downloaded binaries; local reviewed OS behavior is transferable only when payloads match. Windows execution, hardware performance and online play are not established.'}
    shutil.copy2(Path(__file__),EVIDENCE/'download-and-verify.py')
    try:
        metadata=public_metadata();chain=remote_tag();write('public-release-metadata.json',metadata);write('public-tag-resolution.json',{'passed':True,'commit':COMMIT,'chain':chain})
        names=[a['name'] for a in metadata['assets']]
        assert names and len(names)==len(set(names)) and all(release.NAME.fullmatch(n) for n in names),'Unsafe or duplicate public asset names'
        assert all(a['state']=='uploaded' for a in metadata['assets']),'Public asset upload incomplete'
        command=['gh','release','download',TAG,'--repo',REPOSITORY,'--dir',str(DOWNLOAD)]
        downloaded=run(command);(EVIDENCE/'download.log.txt').write_text(downloaded.stdout+downloaded.stderr)
        actual={p.name:record(p) for p in sorted(DOWNLOAD.iterdir()) if p.is_file() and not p.is_symlink()}
        assert set(actual)==set(names),'Downloaded assets differ from all public release assets'
        for asset in metadata['assets']:
            assert actual[asset['name']]['bytes']==asset['size'],'Public asset size mismatch: '+asset['name']
            if asset.get('digest'):assert asset['digest']=='sha256:'+actual[asset['name']]['sha256'],'Public asset digest mismatch: '+asset['name']
        write('public-download-records.json',{'passed':True,'assets':len(actual),'files':actual})
        verify=run([sys.executable,str(PROJECT/'tools/release-native.py'),'verify','--directory',str(DOWNLOAD),'--tag',TAG,'--commit',COMMIT]);(EVIDENCE/'release-verify.log.txt').write_text(verify.stdout+verify.stderr);write('release-verification.json',json.loads(verify.stdout))
        exported=json.loads((DOWNLOAD/'native-export-manifest.json').read_text());local=json.loads((LOCAL/'native-export-manifest.json').read_text())
        media={'passed':True,'export_manifest':record(DOWNLOAD/'native-export-manifest.json'),'traversal':release.validate_traversal_capture(DOWNLOAD,exported,decode=True,require_shaders=True),'ultimates':release.validate_mythic_capture(DOWNLOAD,exported,decode=True),'checks':release.validate_mythic_checks(DOWNLOAD,exported,prefix='ci-')};write('public-export-capture-verification.json',media)
        source_comparison={'passed':exported['source']==local['source'],'published_source':exported['source']['sha256'],'reviewed_source':local['source']['sha256'],'published_files':len(exported['source']['files']),'reviewed_files':len(local['source']['files']),'changed':[p for p in sorted(set(exported['source']['files'])|set(local['source']['files'])) if exported['source']['files'].get(p)!=local['source']['files'].get(p)],'scope':'Runtime source inventory compared exactly; Git metadata may differ because local review preceded the final commit.'};write('source-comparison.json',source_comparison)
        local_dir=LOCAL/'yuga-native-linux-x86_64';zip_path=DOWNLOAD/'yuga-native-linux-x86_64.zip';package=json.loads((DOWNLOAD/'native-package-manifest.json').read_text())['packages']['linux']
        with zipfile.ZipFile(zip_path) as archive:
            members=archive.namelist();assert len(members)==len(set(members)),'Duplicate ZIP members'
            assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in members),'Unsafe ZIP member path'
            assert archive.testzip() is None,'ZIP CRC mismatch'
            prefix='yuga-native-linux-x86_64/';engine=zip_file_record(archive,prefix+'godot');pck=zip_file_record(archive,prefix+'yuga-native.pck')
            extracted=DOWNLOAD.parent/'mythic-public-linux.pck';assert not extracted.exists(),'Comparison PCK path must be new'
            with archive.open(prefix+'yuga-native.pck') as source,extracted.open('xb') as target:shutil.copyfileobj(source,target)
        actual_pack=packager.inspect_pack(extracted);reviewed_pack=packager.inspect_pack(local_dir/'yuga-native.pck')
        public_entries={e['path']:e for e in actual_pack['entries']};reviewed_entries={e['path']:e for e in reviewed_pack['entries']}
        comparison={'passed':False,'published_linux_zip':record(zip_path),'reviewed_linux_zip':record(LOCAL/'yuga-native-linux-x86_64.zip'),'published_engine':engine,'reviewed_engine':record(local_dir/'godot'),'published_pck':pck,'reviewed_pck':record(local_dir/'yuga-native.pck'),'published_pck_entries':len(public_entries),'reviewed_pck_entries':len(reviewed_entries),'changed_pck_entries':[p for p in sorted(set(public_entries)|set(reviewed_entries)) if public_entries.get(p)!=reviewed_entries.get(p)],'public_manifest_matches_payloads':engine==package['engine'] and pck=={k:package['pck'][k] for k in ['bytes','sha256']},'scope':'Actual streamed Linux engine/PCK bytes and parsed resource payloads. ZIP envelopes may differ through commit-specific documentation/manifests; no downloaded executable was run.'}
        comparison['passed']=comparison['published_engine']==comparison['reviewed_engine'] and comparison['published_pck']==comparison['reviewed_pck'] and not comparison['changed_pck_entries'] and comparison['public_manifest_matches_payloads'];write('linux-package-comparison.json',comparison)
        after=public_metadata();assert metadata==after,'Public release metadata or assets changed during retrieval';assert remote_tag()==chain,'Public tag changed during retrieval';write('public-release-metadata-after.json',after)
        write('verification-source-pins.json',{'helper':record(Path(__file__)),'validator':record(PROJECT/'tools/release-native.py'),'packager':record(PROJECT/'tools/package-native.py'),'local_export':record(LOCAL/'native-export-manifest.json'),'public_export':record(DOWNLOAD/'native-export-manifest.json'),'checkout_head':run(['git','rev-parse','HEAD']).stdout.strip()})
        assert source_comparison['passed'],'Published runtime source differs from reviewed local source'
        assert comparison['passed'],'Published Linux engine or PCK differs from reviewed local bytes; inspect comparison before transferring OS review'
        summary.update(passed=True,assets=len(actual),bytes=sum(r['bytes'] for r in actual.values()),published_url=metadata['html_url'],linux_engine_matches_reviewed=True,linux_pck_matches_reviewed=True,runtime_sources_match_reviewed=True)
    except Exception as error:
        summary['failure']={'type':type(error).__name__,'message':str(error)}
    summary['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();write('verification-summary.json',summary);print(json.dumps(summary,indent=2));return 0 if summary['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
