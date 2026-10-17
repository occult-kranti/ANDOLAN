#!/usr/bin/env python3
"""Counterexamples for Rama's package provenance gate; no real art is mutated."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_packaging', PROJECT / 'tools/package-native.py')
packaging = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(packaging)


def authoring_chain_cases(checks: list) -> None:
    """Challenge stage identity, ancestry, dependency completeness and safe paths."""
    with tempfile.TemporaryDirectory(prefix='rama-authoring-cases-') as folder:
        root = Path(folder) / 'project'
        specs = [
            ('r7', 'art/hero-rama/history/r7-runtime/rama-hero.glb', 'art/hero-rama/rama-hero.blend',
             'art/hero-rama/build_hero.py', 'art/hero-rama/history/r7-runtime/RAMA-HERO-PROVENANCE.json',
             ['art/hero-rama/rebind_dhoti.py', 'art/hero-rama/weight-correction.json']),
            ('q3', 'art/hero-rama-quality/rama-hero-quality.glb', 'art/hero-rama-quality/rama-hero-quality.blend',
             'art/hero-rama-quality/build_quality.py', 'art/hero-rama-quality/provenance.json', ['art/hero-rama/build_hero.py']),
            ('face', 'art/hero-rama-face/rama-hero-face.glb', 'art/hero-rama-face/rama-hero-face.blend',
             'art/hero-rama-face/build_native_face.py', 'art/hero-rama-face/candidate.json',
             ['art/hero-rama-face/build_face.py', 'art/hero-rama-face/sources/face-poseunits.json',
              'art/hero-rama-face/sources/face-poseunits.bvh',
              'art/hero-rama-face/history/r4f-reviewed-before-tangents.glb']),
        ]
        files = {'assets/heroes/rama-hero.glb': b'face output fixture',
                 'art/hero-rama/rebind_dhoti.py': b'# retained R7 correction\n',
                 'art/hero-rama/weight-correction.json': b'{"retained": true}\n',
                 'art/hero-rama-face/build_face.py': b'# shared helper fixture; rejected overlay entry is not final generator\n'}
        for stage_id, asset, editable, generator, _metadata, _deps in specs:
            files[asset] = b'face output fixture' if stage_id == 'face' else (stage_id + ' output fixture').encode()
            files[editable] = (stage_id + ' editable fixture').encode()
            files[generator] = ('# ' + stage_id + ' generator fixture\n').encode()
        for relative in [*specs[2][5][1:], 'art/hero-rama-face/sources/source-ledger.json', 'art/hero-rama-face/NOTICE.md']:
            files[relative] = (PROJECT / relative).read_bytes()
        reviewed_generator = 'art/hero-rama-face/history/r4f-reviewed/build_native_face.py'
        reviewed_metadata = 'art/hero-rama-face/history/r4f-reviewed/candidate.json'
        files[reviewed_generator] = (PROJECT / reviewed_generator).read_bytes()

        def sha(path):
            return packaging.hashlib.sha256(files[path]).hexdigest()

        old = {'schema': 1, 'asset': 'assets/heroes/rama-hero.glb', 'sha256': sha(specs[0][1]),
               'editableSource': specs[0][2], 'editableSha256': sha(specs[0][2]),
               'generator': specs[0][3], 'generatorSha256': sha(specs[0][3]),
               'weightCorrectionGenerator': 'art/hero-rama/rebind_dhoti.py',
               'weightCorrectionGeneratorSha256': sha('art/hero-rama/rebind_dhoti.py'),
               'weightCorrection': 'art/hero-rama/weight-correction.json',
               'weightCorrectionSha256': sha('art/hero-rama/weight-correction.json'),
               'generatedDependencies': [{'path': 'art/hero-rama/rebind_dhoti.py', 'sha256': sha('art/hero-rama/rebind_dhoti.py')}]}
        metadata = [old,
                    {'acceptedInputGlbSha256': sha(specs[0][1]), 'acceptedInputEditableSha256': sha(specs[0][2]),
                     'candidateGlbSha256': sha(specs[1][1]), 'candidateEditableSha256': sha(specs[1][2]),
                     'generatorSha256': sha(specs[1][3])},
                    {'inputBlendSha256': sha(specs[1][2]), 'outputSha256': sha(specs[2][1]),
                     'editableSha256': sha(specs[2][2]), 'generatorSha256': sha(specs[2][3]),
                     'zeroTangentRepair': {'sourceSha256': '1fdb01ccb894004a618a594cb41b2e955810c7bdc76855c42f7ce19b0516d92b',
                                           'resultSha256': sha(specs[2][1]), 'allowedRecords': 3, 'changedBytes': 37,
                                           'allOtherBytesIdentical': True, 'positionsNormalsUVsSkinMorphsFaceUnchanged': True},
                     'nativeGeometryGeneratorSha256': sha(reviewed_generator),
                     'postExportProcessorSha256': sha(specs[2][3])}]
        files[reviewed_metadata] = json.dumps({'schema': 1, 'inputBlendSha256': sha(specs[1][2]),
                                              'outputSha256': sha(specs[2][5][3]),
                                              'editableSha256': sha(specs[2][2]),
                                              'generatorSha256': sha(reviewed_generator)}).encode()
        for spec_, value in zip(specs, metadata):
            files[spec_[4]] = json.dumps(value).encode()
        stages = []
        for index, (stage_id, asset, editable, generator, meta, deps) in enumerate(specs):
            stages.append({'id': stage_id, 'parent': specs[index-1][0] if index else None,
                           'asset': asset, 'sha256': sha(asset), 'editableSource': editable,
                           'editableSha256': sha(editable), 'generator': generator,
                           'generatorSha256': sha(generator), 'metadata': meta, 'metadataSha256': sha(meta),
                           'generatedDependencies': [{'path': p, 'sha256': sha(p)} for p in deps],
                           'inputEditableSha256': sha(specs[index-1][2]) if index else None})
        stages[2].update(sourceLedger='art/hero-rama-face/sources/source-ledger.json',
                         sourceLedgerSha256=sha('art/hero-rama-face/sources/source-ledger.json'),
                         licenseNotice='art/hero-rama-face/NOTICE.md',
                         licenseNoticeSha256=sha('art/hero-rama-face/NOTICE.md'),
                         reviewedMetadata=reviewed_metadata, reviewedMetadataSha256=sha(reviewed_metadata),
                         reviewedGenerator=reviewed_generator, reviewedGeneratorSha256=sha(reviewed_generator))
        original = {'schema': 2, 'asset': 'assets/heroes/rama-hero.glb', 'sha256': sha('assets/heroes/rama-hero.glb'),
                    'bytes': len(files['assets/heroes/rama-hero.glb']), 'editableSource': specs[2][2],
                    'editableSha256': sha(specs[2][2]), 'authoringStages': stages}

        def run(name, mutate=None, valid=False):
            for relative, data in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink():
                    path.unlink()
                path.write_bytes(data)
            value = copy.deepcopy(original)
            if mutate:
                mutate(value)
            notice_path = root / 'NOTICE/RAMA-HERO-PROVENANCE.json'
            notice_path.parent.mkdir(exist_ok=True)
            notice_path.write_text(json.dumps(value))
            error = None
            try:
                packaging.validate_rama_hero_notice(root)
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name': name, 'passed': (error is None) == valid, 'rejection': error})

        def change_metadata(value, index, mutate):
            stage = value['authoringStages'][index]
            path = root / stage['metadata']
            data = json.loads(path.read_text())
            mutate(data)
            path.write_text(json.dumps(data))
            stage['metadataSha256'] = packaging.digest(path)

        run('ordered R7 Q3 face authoring accepted', valid=True)
        run('schema2 boolean schema rejected', lambda n: n.update(schema=True))
        run('schema2 unknown schema rejected', lambda n: n.update(schema=99))
        run('schema2 active asset traversal rejected', lambda n: n.update(asset='../outside.glb'))
        run('schema2 wrong active byte count rejected', lambda n: n.update(bytes=n['bytes']+1))
        run('schema2 boolean byte count rejected', lambda n: n.update(bytes=True))
        run('schema2 obsolete direct generator claim rejected', lambda n: n.update(generator='art/hero-rama/build_hero.py'))
        run('schema2 stage list required', lambda n: n.update(authoringStages={}))
        run('schema2 omitted parent stage rejected', lambda n: n['authoringStages'].pop(0))
        run('schema2 extra stage rejected', lambda n: n['authoringStages'].append(copy.deepcopy(n['authoringStages'][2])))
        run('schema2 reordered stages rejected', lambda n: n['authoringStages'].reverse())
        run('schema2 nonobject stage rejected', lambda n: n['authoringStages'].__setitem__(1, []))
        run('schema2 unknown stage field rejected', lambda n: n['authoringStages'][1].update(hiddenGenerator='../other.py'))
        run('schema2 skipped ancestry rejected', lambda n: n['authoringStages'][2].update(parent='r7'))
        run('schema2 unrelated editable input rejected', lambda n: n['authoringStages'][2].update(inputEditableSha256='0'*64))
        run('schema2 nonempty R7 parent rejected', lambda n: n['authoringStages'][0].update(parent='other'))
        run('schema2 stage editable traversal rejected', lambda n: n['authoringStages'][1].update(editableSource='../outside.blend'))
        run('schema2 stage absolute generator rejected', lambda n: n['authoringStages'][2].update(generator='/tmp/face.py'))
        run('schema2 rejected overlay entry cannot be relabeled final generator', lambda n: n['authoringStages'][2].update(generator='art/hero-rama-face/build_face.py', generatorSha256=sha('art/hero-rama-face/build_face.py')))
        run('schema2 unsafe metadata rejected', lambda n: n['authoringStages'][2].update(metadata='../candidate.json'))
        run('schema2 malformed stage digest rejected', lambda n: n['authoringStages'][1].update(sha256='g'*64))
        run('schema2 missing weight evidence dependency rejected', lambda n: n['authoringStages'][0]['generatedDependencies'].pop())
        run('schema2 missing Q3 imported generator dependency rejected', lambda n: n['authoringStages'][1].update(generatedDependencies=[]))
        run('schema2 extra face dependency rejected', lambda n: n['authoringStages'][2].update(generatedDependencies=[{'path':'other.py','sha256':'0'*64}]))
        run('schema2 missing face pose dependency rejected', lambda n: n['authoringStages'][2]['generatedDependencies'].pop())
        run('schema2 missing imported face helper dependency rejected', lambda n: n['authoringStages'][2]['generatedDependencies'].pop(0))
        run('schema2 missing reviewed tangent-repair input rejected', lambda n: n['authoringStages'][2]['generatedDependencies'].pop(3))
        run('schema2 unsafe reviewed tangent-repair input rejected', lambda n: n['authoringStages'][2]['generatedDependencies'][3].update(path='../r4f-reviewed.glb'))
        def replace_reviewed_face(n):
            entry = n['authoringStages'][2]['generatedDependencies'][3]
            path = root / entry['path'];path.write_bytes(b'different self-hashed reviewed face')
            entry['sha256'] = packaging.digest(path)
        run('schema2 self-hashed replacement cannot forge reviewed face input', replace_reviewed_face)
        run('schema2 missing pose source ledger rejected', lambda n: n['authoringStages'][2].pop('sourceLedger'))
        run('schema2 unsafe pose source ledger rejected', lambda n: n['authoringStages'][2].update(sourceLedger='../source-ledger.json'))
        run('schema2 missing pose license notice rejected', lambda n: n['authoringStages'][2].pop('licenseNotice'))
        run('schema2 missing original reviewed metadata rejected', lambda n: n['authoringStages'][2].pop('reviewedMetadata'))
        run('schema2 unsafe original reviewed metadata rejected', lambda n: n['authoringStages'][2].update(reviewedMetadata='../candidate.json'))
        run('schema2 missing original reviewed generator rejected', lambda n: n['authoringStages'][2].pop('reviewedGenerator'))
        run('schema2 unsafe original reviewed generator rejected', lambda n: n['authoringStages'][2].update(reviewedGenerator='/tmp/build_native_face.py'))
        def change_reviewed_metadata(n, mutate):
            stage = n['authoringStages'][2];path = root / stage['reviewedMetadata']
            value = json.loads(path.read_text());mutate(value)
            path.write_text(json.dumps(value));stage['reviewedMetadataSha256'] = packaging.digest(path)
        for key in ['inputBlendSha256', 'outputSha256', 'editableSha256', 'generatorSha256']:
            run('schema2 original reviewed metadata '+key+' contradiction rejected',
                lambda n, k=key: change_reviewed_metadata(n, lambda m: m.update({k:'0'*64})))
        run('schema2 original reviewed metadata boolean schema rejected', lambda n: change_reviewed_metadata(n, lambda m: m.update(schema=True)))
        def replace_original_generator(n):
            stage = n['authoringStages'][2];path = root / stage['reviewedGenerator']
            path.write_bytes(b'# different self-hashed original geometry generator\n')
            stage['reviewedGeneratorSha256'] = packaging.digest(path)
            change_reviewed_metadata(n, lambda m: m.update(generatorSha256=stage['reviewedGeneratorSha256']))
            change_metadata(n, 2, lambda m: m.update(nativeGeometryGeneratorSha256=stage['reviewedGeneratorSha256']))
        run('schema2 self-hashed replacement cannot forge original face generator', replace_original_generator)
        def change_source_ledger(n, mutate):
            stage = n['authoringStages'][2]
            path = root / stage['sourceLedger']
            value = json.loads(path.read_text());mutate(value)
            path.write_text(json.dumps(value));stage['sourceLedgerSha256'] = packaging.digest(path)
        run('schema2 wrong pose revision self-hashed ledger rejected', lambda n: change_source_ledger(n, lambda s: s.update(revision='0'*40)))
        run('schema2 wrong pose license self-hashed ledger rejected', lambda n: change_source_ledger(n, lambda s: s.update(license='unknown')))
        run('schema2 omitted pose entry self-hashed ledger rejected', lambda n: change_source_ledger(n, lambda s: s['files'].pop()))
        def replace_pose(n):
            stage = n['authoringStages'][2]
            entry = next(entry for entry in stage['generatedDependencies'] if entry['path'].endswith('.bvh'))
            path = root / entry['path'];path.write_bytes(b'different self-hashed BVH')
            entry['sha256'] = packaging.digest(path)
            change_source_ledger(n, lambda s: s['files'][1].update(sha256=entry['sha256'], bytes=path.stat().st_size))
        run('schema2 self-hashed replacement pose cannot bypass pinned inputs', replace_pose)
        def erase_license(n):
            stage = n['authoringStages'][2];path = root / stage['licenseNotice']
            path.write_text('Missing attribution');stage['licenseNoticeSha256'] = packaging.digest(path)
        run('schema2 self-hashed removed attribution rejected', erase_license)
        run('schema2 unsafe dependency rejected', lambda n: n['authoringStages'][1]['generatedDependencies'][0].update(path='../build_hero.py'))
        run('schema2 malformed dependency hash rejected', lambda n: n['authoringStages'][1]['generatedDependencies'][0].update(sha256=True))
        run('schema2 misleading final editable rejected', lambda n: n.update(editableSource=specs[0][2], editableSha256=sha(specs[0][2])))
        run('schema2 final editable digest mismatch rejected', lambda n: n.update(editableSha256='0'*64))
        for index, key in [(0,'sha256'), (0,'weightCorrectionSha256'), (1,'acceptedInputGlbSha256'),
                           (1,'acceptedInputEditableSha256'), (1,'candidateEditableSha256'),
                           (2,'inputBlendSha256'), (2,'outputSha256'), (2,'generatorSha256')]:
            run(f'schema2 metadata contradiction {index} {key} rejected',
                lambda n, i=index, k=key: change_metadata(n, i, lambda m: m.update({k:'0'*64})))
        run('schema2 archived schema1 missing dependency still rejected',
            lambda n: change_metadata(n, 0, lambda m: m.update(generatedDependencies=[])))
        run('schema2 missing tangent-repair metadata rejected', lambda n: change_metadata(n, 2, lambda m: m.pop('zeroTangentRepair')))
        for key in ['nativeGeometryGeneratorSha256', 'postExportProcessorSha256']:
            run('schema2 final face '+key+' ancestry contradiction rejected',
                lambda n, k=key: change_metadata(n, 2, lambda m: m.update({k:'0'*64})))
        for key, value in [('sourceSha256', '0'*64), ('resultSha256', '0'*64), ('allowedRecords', 4),
                           ('allowedRecords', True), ('changedBytes', 49), ('changedBytes', 0),
                           ('allOtherBytesIdentical', False), ('positionsNormalsUVsSkinMorphsFaceUnchanged', False)]:
            run(f'schema2 tangent-repair {key} contradiction {value} rejected',
                lambda n, k=key, v=value: change_metadata(n, 2, lambda m: m['zeroTangentRepair'].update({k:v})))
        for relative in files:
            def corrupt(n, path=relative):
                target = root / path
                target.write_bytes(target.read_bytes()+b' altered')
            run('schema2 changed authoring source rejects: '+relative, corrupt)
        def replace_active(n):
            path = root / n['asset']
            path.write_bytes(b'unrelated but self-hashed final asset')
            n['sha256'] = packaging.digest(path)
            n['bytes'] = path.stat().st_size
        run('schema2 self-hashed active asset must match terminal stage', replace_active)
        for relative in [specs[0][1], specs[1][4], specs[2][3]]:
            def outside_symlink(n, path=relative):
                destination = root / path
                outside = Path(folder) / ('outside-'+destination.name)
                outside.write_bytes(destination.read_bytes())
                destination.unlink()
                destination.symlink_to(outside)
            run('schema2 matching external symlink rejects: '+relative, outside_symlink)
        run('schema2 restored sources accepted', valid=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    checks = []
    with tempfile.TemporaryDirectory(prefix='rama-package-cases-') as folder:
        root = Path(folder) / 'project'
        files = {
            'assets/heroes/rama-hero.glb': b'original asset fixture',
            'art/hero-rama/rama-hero.blend': b'editable authoring fixture',
            'art/hero-rama/build_hero.py': b'# generator fixture\n',
            'art/hero-rama/rebind_dhoti.py': b'# weight correction generator fixture\n',
            'art/hero-rama/weight-correction.json': b'{"fixture": true}\n',
        }
        for path, content in files.items():
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        notice_path = root / 'NOTICE/RAMA-HERO-PROVENANCE.json'
        notice_path.parent.mkdir()
        original = {
            'schema': 1,
            'asset': 'assets/heroes/rama-hero.glb',
            'sha256': packaging.digest(root / 'assets/heroes/rama-hero.glb'),
            'editableSource': 'art/hero-rama/rama-hero.blend',
            'editableSha256': packaging.digest(root / 'art/hero-rama/rama-hero.blend'),
            'generator': 'art/hero-rama/build_hero.py',
            'generatorSha256': packaging.digest(root / 'art/hero-rama/build_hero.py'),
            'weightCorrectionGenerator': 'art/hero-rama/rebind_dhoti.py',
            'weightCorrectionGeneratorSha256': packaging.digest(root / 'art/hero-rama/rebind_dhoti.py'),
            'weightCorrection': 'art/hero-rama/weight-correction.json',
            'weightCorrectionSha256': packaging.digest(root / 'art/hero-rama/weight-correction.json'),
            'generatedDependencies': [{'path': 'art/hero-rama/rebind_dhoti.py',
                                       'sha256': packaging.digest(root / 'art/hero-rama/rebind_dhoti.py')}],
            'limitations': ['Synthetic identity fixture, not a valid GLB or art acceptance.'],
        }

        def run(name, mutate=None, valid=False):
            value = copy.deepcopy(original)
            if mutate:
                mutate(value)
            notice_path.write_text(json.dumps(value))
            error = None
            try:
                packaging.validate_rama_hero_notice(root)
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name': name, 'passed': (error is None) == valid, 'rejection': error})

        run('matching asset editable and generator hashes accepted', valid=True)
        run('boolean schema rejected', lambda value: value.update(schema=True))
        run('legacy notice cannot become schema2 merely by relabeling', lambda value: value.update(schema=2))
        run('path traversal rejected before reading outside', lambda value: value.update(asset='../outside.glb'))
        run('absolute editable path rejected', lambda value: value.update(editableSource='/tmp/other.blend'))
        run('missing digest rejected', lambda value: value.pop('sha256'))
        run('nonhex digest rejected', lambda value: value.update(sha256='z' * 64))
        run('omitted weight correction dependency rejected', lambda value: value.pop('weightCorrectionGenerator'))
        run('weight correction dependency traversal rejected', lambda value: value.update(weightCorrectionGenerator='../rebind_dhoti.py'))
        run('omitted weight correction evidence hash rejected', lambda value: value.pop('weightCorrectionSha256'))
        run('generated dependency ledger mismatch rejected', lambda value: value.update(generatedDependencies=[]))
        for relative in files:
            path = root / relative
            path.write_bytes(files[relative] + b' changed')
            run('changed source rejects: ' + relative)
            path.write_bytes(files[relative])
        asset = root / original['asset']
        asset.unlink()
        run('missing asset rejects')
        outside = Path(folder) / 'outside.glb'
        outside.write_bytes(files[original['asset']])
        asset.symlink_to(outside)
        run('matching external symlink still rejects')
        asset.unlink()
        asset.write_bytes(files[original['asset']])
        run('restored source passes', valid=True)
    authoring_chain_cases(checks)
    passed = all(check['passed'] for check in checks)
    report = {'suite': 'rama_package_cases', 'passed': passed, 'checks': checks,
              'source_sha256': {'tools/package-native.py': packaging.digest(PROJECT / 'tools/package-native.py'),
                                'tests/rama_package_cases.py': packaging.digest(Path(__file__))},
              'scope': 'Historical schema1 and ordered schema2 authoring provenance, source identity, ancestry and safe-path counterexamples; not GLB format or art quality.'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'checks': len(checks), 'failures': [check for check in checks if not check['passed']]}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
