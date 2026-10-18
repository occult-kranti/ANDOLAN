#!/usr/bin/env python3
"""Schema-5 and promoted graphics PCK counterexamples; no engine or real-source writes."""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

PROJECT = Path(__file__).resolve().parents[1]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

P = module('graphics_packager', PROJECT / 'tools/package-native.py')
F = module('graphics_pck_fixtures', PROJECT / 'tests/traversal_security_cases.py')


def surface_cases(checks):
    notice_path = PROJECT / 'NOTICE/RAMA-HERO-PROVENANCE.json'
    notice = json.loads(notice_path.read_text())
    active_schema = notice['schema']
    assert notice['schema'] in (5, 6), 'These adversaries require the exact current or preserved schema-5 proposal'
    validated = P.validate_rama_hero_notice(PROJECT)
    if notice['schema'] == 6:
        notice = json.loads((PROJECT / P.RAMA_CROWN_PARENT).read_text())
    before = {path: P.record(PROJECT / path) for path in validated['sources']}
    before['NOTICE/RAMA-HERO-PROVENANCE.json'] = P.record(notice_path)
    checks.append({'name': f'complete actual schema{active_schema} source closure validates with exact schema5 surface history', 'passed': True,
                   'sources': len(validated['sources'])})
    checks.append({'name': 'schema5 records current and historical surface bindings separately',
                   'passed': all(path in validated['sources'] for path in
                                  ('scripts/rama_surface_finish.gd', P.RAMA_SURFACE_OLD_BINDING))})
    paths = [P.RAMA_SURFACE_PARENT, P.RAMA_SURFACE_OLD_BINDING, *P.RAMA_SURFACE_DEPENDENCIES]
    files = {path: (PROJECT / path).read_bytes() for path in paths}
    with tempfile.TemporaryDirectory(prefix='graphics-surface-cases-') as tmp:
        root = Path(tmp) / 'project'

        def restore():
            for relative, content in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink():
                    path.unlink()
                path.write_bytes(content)

        def run(name, mutate=None, valid=False):
            restore()
            value = copy.deepcopy(notice)
            if mutate:
                mutate(value)
            error = None
            try:
                P._validate_rama_surface_stage(root, value)
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name': name, 'passed': (error is None) == valid, 'rejection': error})

        run('exact bounded surface stage accepts', valid=True)
        run('missing surface stage rejects', lambda n: n.pop('surfaceStage'))
        run('extra surface stage field rejects', lambda n: n['surfaceStage'].update(activatedUpperHair=True))
        for key in notice['surfaceStage']:
            run('missing surface field rejects: ' + key, lambda n, k=key: n['surfaceStage'].pop(k))
        for key, wrong in {'id': 'unreviewed-stage', 'parentNotice': '../outside.json',
                           'parentNoticeSha256': '0'*64, 'historicalBinding': 'scripts/rama_surface_finish.gd',
                           'historicalBindingSha256': '0'*64}.items():
            run('substituted surface field rejects: ' + key,
                lambda n, k=key, w=wrong: n['surfaceStage'].update({k:w}))
        run('missing ordered surface dependency rejects', lambda n: n['surfaceStage']['generatedDependencies'].pop())
        run('reordered surface dependencies reject', lambda n: n['surfaceStage']['generatedDependencies'].reverse())
        run('extra surface dependency rejects', lambda n: n['surfaceStage']['generatedDependencies'].append(
            {'path':'scripts/rama_upper_hair_layers.gd','sha256':'0'*64}))
        run('rewritten geometry ancestry rejects', lambda n: n['authoringStages'][0].update(sha256='0'*64))
        run('rewritten cloth ancestry rejects', lambda n: n['clothStage'].update(parentNoticeSha256='0'*64))
        run('rewritten historical limitations reject', lambda n: n['limitations'].append('new historical claim'))

        for relative in paths:
            run('missing source rejects: ' + relative,
                lambda n, r=relative: (root / r).unlink())
            run('changed source rejects: ' + relative,
                lambda n, r=relative: (root / r).write_bytes(files[r] + b'changed'))

            def self_hash(n, r=relative):
                path = root / r
                path.write_bytes(files[r] + b'changed')
                sha = P.digest(path)
                if r == P.RAMA_SURFACE_PARENT:
                    n['surfaceStage']['parentNoticeSha256'] = sha
                elif r == P.RAMA_SURFACE_OLD_BINDING:
                    n['surfaceStage']['historicalBindingSha256'] = sha
                else:
                    next(d for d in n['surfaceStage']['generatedDependencies'] if d['path'] == r)['sha256'] = sha
            run('self-hashed source substitution rejects: ' + relative, self_hash)

        for relative in (P.RAMA_SURFACE_PARENT, P.RAMA_SURFACE_OLD_BINDING,
                         'assets/hero-finish/hair-bundle-roughness.png',
                         'art/hero-finish/build_g1_maps.py'):
            def symlink(n, r=relative):
                path = root / r
                path.unlink()
                path.symlink_to(PROJECT / r)
            run('matching external source symlink rejects: ' + relative, symlink)

        restore()
        original_dir = root / 'assets/hero-finish'
        moved = root / 'assets/identical-finish'
        original_dir.rename(moved)
        original_dir.symlink_to(moved, target_is_directory=True)
        error = None
        try:
            P._validate_rama_surface_stage(root, copy.deepcopy(notice))
        except (ValueError, OSError) as exc:
            error = str(exc)
        checks.append({'name':'matching internal ancestor-directory symlink rejects',
                       'passed':error is not None, 'rejection':error})
        original_dir.unlink()
        moved.rename(original_dir)
        run('restored exact stage still accepts', valid=True)
    checks.append({'name':'all real provenance inputs unchanged after adversaries',
                   'passed':before == {path:P.record(PROJECT / path) for path in before}})
    return before


def payload_cases(checks):
    entries = [(name, ('structural fixture ' + name).encode()) for name in F.NAMES]
    for source, target in F.GRAPHICS_TEXTURE_FIXTURES.items():
        # Exercise the actual reviewed source descriptors as well as trimmed PCK ones.
        payload = (PROJECT / (source + '.import')).read_bytes()
        entries.extend([(source + '.import', payload), (target, b'structural ctex payload')])
        checks.append({'name':'actual pinned descriptor resolves: ' + source,
                       'passed':P._graphics_texture_target(payload, source) == target})
    with tempfile.TemporaryDirectory(prefix='graphics-pck-cases-') as tmp:
        pack_path = Path(tmp) / 'fixture.pck'

        def run(name, fixture, valid=False):
            pack_path.write_bytes(F.pack(fixture)[0])
            error = None
            try:
                P.inspect_pack(pack_path)
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name':name, 'passed':(error is None) == valid, 'rejection':error})

        run('complete promoted graphics structural pack accepts', entries, True)
        for path in [*F.GRAPHICS_NAMES, *[p + '.import' for p in F.GRAPHICS_TEXTURE_FIXTURES],
                     *F.GRAPHICS_TEXTURE_FIXTURES.values()]:
            run('missing exact graphics resource rejects: ' + path,
                [(p,b) for p,b in entries if p != path])
            run('graphics filename decoy rejects: ' + path,
                [(p+'.backup' if p == path else p,b) for p,b in entries])
        for source in (p for p in F.GRAPHICS_NAMES if p.endswith('.gd')):
            remapped = [(p,b) for p,b in entries if p != source]
            remapped.extend([(source+'.remap',f'[remap]\npath="res://{source}c"\n'.encode()),
                             (source+'c', b'structural compiled script fixture')])
            run('compiled graphics remap accepts: ' + source, remapped, True)
            run('orphan graphics remap rejects: ' + source,
                [(p,b) for p,b in remapped if p != source+'c'])
            run('source/remap ambiguity rejects: ' + source, remapped + [(source,b'raw duplicate')])
            run('cross-script graphics remap rejects: ' + source,
                [(p,b'[remap]\npath="res://scripts/boot.gdc"\n' if p == source+'.remap' else b)
                 for p,b in remapped])
        for source,target in F.GRAPHICS_TEXTURE_FIXTURES.items():
            descriptor = f'[remap]\npath="res://{target}"\n'.encode()
            for label, altered in {
                'wrong target':descriptor.replace(b'.ctex',b'-wrong.ctex'),
                'duplicate target':descriptor + f'path="res://{target}"\n'.encode(),
                'wrong section':descriptor.replace(b'[remap]',b'[deps]'),
                'duplicate remap section':descriptor + b'[remap]\n',
            }.items():
                run('texture '+label+' rejects: '+source,
                    [(p,altered if p == source+'.import' else b) for p,b in entries])
            run('trimmed texture descriptor accepts: '+source,
                [(p,descriptor if p == source+'.import' else b) for p,b in entries], True)
        checks.append({'name':'optional inactive upper-hair helper not required or claimed',
                       'passed':not any('rama_upper_hair_layers' in p for p,b in entries)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    checks = []
    sources = surface_cases(checks)
    payload_cases(checks)
    passed = all(c['passed'] for c in checks)
    report = {'suite':'graphics_package_cases', 'passed':passed, 'count':len(checks),
              'passed_count':sum(c['passed'] for c in checks), 'checks':checks,
              'source_sha256':{p:P.digest(PROJECT/p) for p in ('tools/package-native.py',
                  'tests/graphics_package_cases.py','tests/traversal_security_cases.py')},
              'provenance_sources':sources,
              'scope':'Actual current source closure with preserved schema5 surface history and small disposable mutation fixtures; structural PCK mappings only. No texture decoding, export, engine, visual acceptance or activated optional hair claim.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':passed,'count':len(checks),'failures':[c for c in checks if not c['passed']]}))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
