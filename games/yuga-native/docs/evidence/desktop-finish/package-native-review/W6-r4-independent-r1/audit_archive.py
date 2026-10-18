#!/usr/bin/env python3
"""Read-only final owner-archive integrity and independently viewed-original closure."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWNER = HERE.parent / 'W1-patched-r1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    receipt = json.loads((OWNER / 'receipt.json').read_text())
    artifacts = receipt['artifacts']
    for relative, row in artifacts.items():
        path = OWNER / relative
        assert path.resolve().is_relative_to(OWNER.resolve()) and not path.is_symlink()
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], relative
    runs = {}
    originals = []
    for phase, count in [('warm', 40), ('cold', 19)]:
        viewed = json.loads((HERE / (phase + '-originals-viewed.json')).read_text())
        root = OWNER / phase
        run = json.loads((root / 'run.json').read_text())
        assert sha(root / 'run.json') == viewed['run_sha256']
        assert run['complete'] and run['verified_exit_code'] == 0 and run['cleanup_exit'] == 0
        assert run['mode'] == 'package' and run['export_manifest']['git']['head'] == '96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
        assert run['engine_sha256'] == 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'
        assert run['package_archive']['sha256'] == '27c36e5523643c647b245614721c0160b3d1548bf6da851d922886cffc180d0e'
        assert run['export_manifest']['sha256'] == '4cb3316300092dcdb99016f3c0e6f024066df2f94999a3b7b4944247870aa4a7'
        command = run['command']
        engine, pck = Path(command[0]), Path(command[command.index('--main-pack')+1])
        assert engine.parent == pck.parent and engine.name == 'godot' and pck.name == 'yuga-native.pck'
        assert '/extracted/yuga-native-linux-x86_64/' in str(engine)
        assert run['package_sha256'][str(engine)] == run['engine_sha256']
        assert run['package_sha256'][str(pck)] == 'b84ac0f4f1e70fbfc5366234729a9e97012e5664bd6a3a43bfb77fe61e7b6903'
        for flag in ['package_unchanged','instrumentation_unchanged','archive_unchanged','export_manifest_unchanged','source_unchanged']:
            assert run[flag] is True, flag
        assert run['user_state']['before'] == {}
        rows = viewed['originals']
        assert len(rows) == count and {x['file'] for x in rows} == {x.name for x in root.glob('*.png')}
        for row in rows:
            png = root / row['file']; sidecar = png.with_suffix('.json')
            assert sha(png) == row['png_sha256'] and sha(sidecar) == row['sidecar_sha256']
            data = json.loads(sidecar.read_text())
            assert data['sha256'] == row['png_sha256'] and row['directly_opened_original'] is True
            assert data.get('transition', {}).get('phase') == row['actual_phase']
        stages = run['authority_staging']
        if phase == 'warm':
            assert stages['enabled'] and [s['action'] for s in stages['stages']] == ['outcome-sun','release','outcome-moon','release','outcome-draw','release']
            assert all(s['passed'] and s['scope'].startswith('STAGED AUTHORITY:') for s in stages['stages'])
        else:
            assert stages['enabled'] is False and not stages['stages']
            for seed in ['shader_cache_seed', 'godot_shader_cache_seed']:
                assert not run.get(seed, {}).get('files_sha256', {})
                assert not run.get(seed, {}).get('reused_isolated_cache_sha256', {})
        runs[phase] = {'run_sha256':sha(root/'run.json'),'manual':len(run['shots']),
                       'automatic':len(run['automatic_shots']),'native_quit':run['verified_exit_code'],
                       'cleanup_exit':run['cleanup_exit'],'staged_actions':[s['action'] for s in stages['stages']]}
        originals.extend({'phase':phase, 'file':r['file'],'sha256':r['png_sha256']} for r in rows)
    report = {'passed':True,'owner_receipt_sha256':sha(OWNER/'receipt.json'),
              'owner_artifacts_verified':len(artifacts),'owner_bytes_verified':sum(r['bytes'] for r in artifacts.values()),
              'directly_viewed_originals_verified':len(originals),'runs':runs,
              'scope':'Read-only exact archived evidence closure; no engine, network, copied PNGs or publication.'}
    (HERE/'archive-integrity.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,sort_keys=True))

if __name__ == '__main__':
    main()
