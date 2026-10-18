#!/usr/bin/env python3
"""Tiny streamed/legacy archive equivalence and adversaries; no engine or export."""
import argparse
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from unittest.mock import patch
from types import SimpleNamespace
import zipfile
PROJECT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stream_packaging',PROJECT/'tools/package-native.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--temp-root',type=Path);args=parser.parse_args()
    if args.report.exists():parser.error('Fresh report required')
    checks=[]
    def check(name,fn,accept=False):
        error=None
        try:fn();ok=accept
        except (ValueError,KeyError,FileNotFoundError,TypeError) as e:ok=not accept;error=str(e)
        checks.append({'name':name,'passed':ok,'error':error})
        if not ok:raise AssertionError(name)
    with tempfile.TemporaryDirectory(prefix='stream-package-',dir=args.temp_root) as temporary:
        root=Path(temporary);counter=0
        def fixture(platform='linux'):
            nonlocal counter
            counter+=1;base=root/str(counter);base.mkdir();inputs=base/'inputs';inputs.mkdir()
            engine=inputs/'engine';engine.write_bytes((b'engine bytes including executable payload\x00'*64));engine.chmod(0o640)
            pck=inputs/'pack';pck.write_bytes(b'PCK fixture, never passed to Godot\x00'*128)
            staging=base/('yuga-native-'+platform+'-x86_64');staging.mkdir();(staging/'NOTICE').mkdir();(staging/'NOTICE/license.txt').write_bytes(b'fixture notice')
            (staging/'NOTICE-extra.txt').write_bytes(b'sibling-prefix order fixture')
            launcher='launch.sh' if platform=='linux' else 'launch.bat';(staging/launcher).write_bytes(b'fixture launcher')
            (staging/'PACKAGE-MANIFEST.json').write_text('{"fixture":true}\n')
            virtual=pack._large_payload_sources(platform,engine,pck)
            return base,staging,engine,pck,virtual
        for platform in ('linux','windows'):
            base,staging,engine,pck,virtual=fixture(platform);before={p:pack._stream_source_snapshot(p) for p in (engine,pck)}
            streamed=base/'streamed.zip';pack.zip_directory(staging,streamed,virtual)
            check(platform+' streamed ZIP creates no engine/PCK staging copies',lambda:pack_need(not any((staging/name).exists() for name in virtual)),True)
            engine_name='godot' if platform=='linux' else 'godot.exe'
            shutil.copyfile(engine,staging/engine_name);shutil.copyfile(pck,staging/'yuga-native.pck')
            legacy=base/'legacy.zip';pack.zip_directory(staging,legacy)
            check(platform+' streamed ZIP byte-identical to unchanged legacy',lambda:pack_need(streamed.read_bytes()==legacy.read_bytes()),True)
            with zipfile.ZipFile(streamed) as archive:
                names=archive.namelist();prefix=staging.name+'/'
                check(platform+' deterministic sorted exact platform members',lambda:pack_need(names==sorted(names,key=lambda name:PurePosixPath(name).parts) and prefix+engine_name in names and prefix+'yuga-native.pck' in names),True)
                check(platform+' fixed timestamp and permissions',lambda:pack_need(all(i.date_time==(2026,1,1,0,0,0) and stat.S_IMODE(i.external_attr>>16)==(0o755 if Path(i.filename).name in {'godot','launch.sh'} else 0o644) for i in archive.infolist())),True)
            check(platform+' source bytes inode and permissions unmodified',lambda:pack_need(all(pack._stream_source_snapshot(p)==v for p,v in before.items())),True)
            check(platform+' copied runtime conflict rejects under streamed mode',lambda:pack.zip_directory(staging,base/'duplicate.zip',virtual))
        # Every mutation below uses a new tiny private fixture.
        for bad in ('../escape','/absolute','x/../godot','x\\godot','./godot',''):
            base,stage,engine,pck,v=fixture();v[bad]=v.pop('godot');check('unsafe/incorrect virtual name '+repr(bad),lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();v['godot.exe']=v.pop('godot');check('Windows engine name in Linux archive rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture('windows');v['godot']=v.pop('godot.exe');check('Linux engine name in Windows archive rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();v.pop('yuga-native.pck');check('missing virtual PCK rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();engine.write_bytes(b'changed');check('changed frozen engine rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();pck.write_bytes(b'changed');check('changed frozen PCK rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();engine.chmod(0o600);check('changed frozen mode rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();other=base/'replacement';other.write_bytes(engine.read_bytes());other.chmod(0o640);os.replace(other,engine);check('same bytes replacement inode rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();link=base/'symlink';link.symlink_to(engine);check('direct virtual symlink rejects',lambda:pack._large_payload_sources('linux',link,pck))
        base,stage,engine,pck,v=fixture();link=base/'linkdir';link.symlink_to(engine.parent,target_is_directory=True);check('virtual parent symlink rejects',lambda:pack._large_payload_sources('linux',link/engine.name,pck))
        base,stage,engine,pck,v=fixture();check('virtual directory rejects',lambda:pack._large_payload_sources('linux',engine.parent,pck))
        base,stage,engine,pck,v=fixture();fifo=base/'fifo';os.mkfifo(fifo);check('virtual FIFO rejects without opening',lambda:pack._large_payload_sources('linux',fifo,pck))
        base,stage,engine,pck,v=fixture();(stage/'bad-link').symlink_to(engine);check('staged symlink rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();(stage/'linked-dir').symlink_to(engine.parent,target_is_directory=True);check('staged directory symlink rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();os.mkfifo(stage/'fifo');check('staged FIFO rejects without opening',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();(stage/'back\\slash').write_bytes(b'bad path');check('staged backslash member rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();out=base/'bad.zip';out.symlink_to(engine);check('output symlink rejects without engine clobber',lambda:pack.zip_directory(stage,out,v));check('output symlink engine remains exact',lambda:pack_need(pack._stream_source_snapshot(engine)==v['godot']['snapshot']),True)
        for selected in ('engine','pck','staged'):
            for hardlink in (False,True):
                base,stage,engine,pck,v=fixture()
                source={'engine':engine,'pck':pck,'staged':stage/'NOTICE/license.txt'}[selected]
                output=base/'alias.zip' if hardlink else source
                if hardlink:os.link(source,output)
                v=pack._large_payload_sources('linux',engine,pck)
                before=pack._stream_source_snapshot(source)
                check('output '+selected+(' hardlink' if hardlink else ' exact path')+' rejects before truncation',lambda:pack.zip_directory(stage,output,v))
                if 'output aliases an input source' not in (checks[-1]['error'] or ''):raise AssertionError('alias guard must reject before any other predicate')
                check('rejected '+selected+(' hardlink' if hardlink else ' exact path')+' preserves source bytes inode mode',lambda:pack_need(pack._stream_source_snapshot(source)==before),True)
        base,stage,engine,pck,v=fixture();fifo=base/'output-fifo';os.mkfifo(fifo);before=pack._stream_source_snapshot(engine)
        check('nonregular output rejects before opening',lambda:pack.zip_directory(stage,fifo,v));check('nonregular output preserves engine',lambda:pack_need(pack._stream_source_snapshot(engine)==before),True)
        # Mutate a real input after its read stream opens; archive hashes and
        # source identity must fail even though a self-consistent ZIP is possible.
        for mutation in ('bytes','mode','replace'):
            base,stage,engine,pck,v=fixture();original=zipfile.ZipFile.open;triggered=[]
            def tamper(archive,name,*a,**kw):
                mode=a[0] if a else kw.get('mode','r')
                if mode=='w' and isinstance(name,zipfile.ZipInfo) and name.filename.endswith('/godot') and not triggered:
                    triggered.append(True)
                    if mutation=='bytes':engine.write_bytes(b'tampered mid-read')
                    elif mutation=='mode':engine.chmod(0o600)
                    else:
                        replacement=base/'swap';replacement.write_bytes(engine.read_bytes());replacement.chmod(0o640);os.replace(replacement,engine)
                return original(archive,name,*a,**kw)
            with patch.object(zipfile.ZipFile,'open',tamper):check('mid-read '+mutation+' mutation rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();engine.write_bytes(b'A'*(2*1024*1024+31));v=pack._large_payload_sources('linux',engine,pck)
        original_write=zipfile._ZipWriteFile.write;triggered=[]
        def mutate_next_block(target,data):
            result=original_write(target,data)
            if target._zinfo.filename.endswith('/godot') and not triggered:
                triggered.append(True)
                with engine.open('r+b') as f:f.seek(1024*1024+16);f.write(b'changed unread block')
            return result
        with patch.object(zipfile._ZipWriteFile,'write',mutate_next_block):check('mutation between real1MiB blocks rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        base,stage,engine,pck,v=fixture();original_crc=zipfile.ZipFile.testzip
        def mutate_after_write(archive):
            result=original_crc(archive);engine.chmod(0o600);return result
        with patch.object(zipfile.ZipFile,'testzip',mutate_after_write):check('source mutation after archive write rejects',lambda:pack.zip_directory(stage,base/'bad.zip',v))
        check('unsupported source platform rejects',lambda:pack._large_payload_sources('other',engine,pck))

        # Exercise the actual package_all mode plumbing and manifest assembly.
        # Only unrelated preflight/font/asset proofs and tiny synthetic PCK
        # parsing are mocked; stream ZIP implementation/source identity is real.
        assembly=root/'assembly';assembly.mkdir();engine=assembly/'linux-runtime';engine.write_bytes(b'linux fixture');engine.chmod(0o640)
        windows=assembly/'windows.exe';windows.write_bytes(b'windows fixture');windows.chmod(0o640)
        selection={'exporter':{'version':'fixture',**pack.record(engine)},'linux_runtime':{'kind':'fixture','provenance':None,**pack.record(engine)}}
        (assembly/'godot-windows-provenance.json').write_text(json.dumps({'files':[{'name':windows.name,**pack.record(windows)}]}))
        native={'sources':{'fixture':'stable'}};fonts={'fixture':True};source={'sha256':'fixture','files':{}}
        def notices(destination):
            (destination/'NOTICE').mkdir();(destination/'NOTICE/license.txt').write_bytes(b'fixture')
        with ExitStack() as stack:
            for name,value in [('linux_engine_selection',selection),('prove_native_contract_sources',native),('_native_contract_inputs',native['sources']),('source_state',source),('validate_rama_hero_notice',{'fixture':True}),('prove_imported_font_bindings',fonts),('qualify_bundled_font_package',{'passed':True}),('qualify_world_frontage_package',{'passed':True})]:stack.enter_context(patch.object(pack,name,return_value=value))
            stack.enter_context(patch.object(pack,'safe_notice_copy',side_effect=notices));stack.enter_context(patch.object(pack,'copy_public_runtime_notice',return_value=None))
            stack.enter_context(patch.object(pack,'inspect_pack',side_effect=lambda p:{**pack.record(p),'entry_count':1}))
            args_=SimpleNamespace(linux_engine=engine,windows_engine=windows,stream_large_payloads=False)
            def assemble(name,stream):
                build=assembly/name;build.mkdir();packs={}
                for platform in ('linux','windows'):
                    f=build/('yuga-native-'+platform+'.pck');f.write_bytes((platform+' synthetic PCK').encode());packs[platform]=pack.record(f)
                exported={'engine_selection':selection,'godot_version':'fixture','source':source,'git':{'head':'fixture'},'native_contracts':native,'rama_hero_provenance':{'fixture':True},'font_bindings':fonts,'packs':packs}
                args_.stream_large_payloads=stream;return build,pack.package_all(args_,build,exported)
            before={p:pack._stream_source_snapshot(p) for p in (engine,windows)}
            copied,copied_result=assemble('copied',False);streamed,stream_result=assemble('streamed',True)
            for platform in ('linux','windows'):
                name='yuga-native-'+platform+'-x86_64';check('actual package_all '+platform+' archive byte equivalence',lambda n=name:pack_need((copied/(n+'.zip')).read_bytes()==(streamed/(n+'.zip')).read_bytes()),True)
                manifest=json.loads((streamed/name/'PACKAGE-MANIFEST.json').read_text());engine_name='godot' if platform=='linux' else 'godot.exe'
                check('actual package_all '+platform+' virtual manifest payload records',lambda m=manifest,e=engine_name:pack_need(e in m['payloads'] and 'yuga-native.pck' in m['payloads']),True)
                check('actual package_all '+platform+' no expanded large payloads',lambda n=name,e=engine_name:pack_need(not (streamed/n/e).exists() and not (streamed/n/'yuga-native.pck').exists()),True)
            check('actual assembly never changes engine inode bytes or modes',lambda:pack_need(all(pack._stream_source_snapshot(p)==v for p,v in before.items())),True)
            original=pack._large_payload_sources
            def swap_pack(platform,engine_,pack_):
                pack_.write_bytes(b'changed after pack inspection');return original(platform,engine_,pack_)
            with patch.object(pack,'_large_payload_sources',side_effect=swap_pack):check('assembly rejects changed previously validated PCK',lambda:assemble('changed-pack',True))
            def swap_runtime(platform,engine_,pack_):
                engine_.write_bytes(b'changed after runtime selection');return original(platform,engine_,pack_)
            with patch.object(pack,'_large_payload_sources',side_effect=swap_runtime):check('assembly rejects changed previously validated runtime',lambda:assemble('changed-runtime',True))
    result={'passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'source_sha256':{'tools/package-native.py':pack.digest(PROJECT/'tools/package-native.py'),'tests/streamed_package_cases.py':pack.digest(Path(__file__))},'scope':'Tiny actual ZIP reads/writes, unchanged legacy byte-equivalence and path/source/mutation adversaries only. No export, Godot, real engine execution or release qualification.'}
    args.report.parent.mkdir(parents=True,exist_ok=True);temp=args.report.with_name('.'+args.report.name+'.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');os.replace(temp,args.report);print(json.dumps({'passed':result['passed'],'count':result['count']}));return 0 if result['passed'] else 1

def pack_need(value):
    if not value:raise ValueError('Synthetic assertion failed')
if __name__=='__main__':raise SystemExit(main())
