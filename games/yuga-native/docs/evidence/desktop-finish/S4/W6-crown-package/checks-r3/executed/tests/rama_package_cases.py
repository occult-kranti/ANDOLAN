#!/usr/bin/env python3
"""Counterexamples for Rama's package provenance gate; no real art is mutated."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import struct
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


def form_stage_cases(checks: list) -> None:
    """Challenge schema3's append gate without pretending fixtures are meshes."""
    with tempfile.TemporaryDirectory(prefix='rama-form-stage-cases-') as folder:
        root = Path(folder)
        base = packaging.RAMA_FORM_BASE
        historical_bytes = (PROJECT / 'NOTICE/RAMA-HERO-PROVENANCE.json').read_bytes()
        historical_notice = json.loads(historical_bytes)
        # Tests remain useful after promotion: recover the immutable schema2 notice.
        if historical_notice['schema'] >= 3:
            historical_bytes = (PROJECT / base / 'input/RAMA-HERO-PROVENANCE.json').read_bytes()
            historical_notice = json.loads(historical_bytes)
        historical = historical_notice['authoringStages']
        parent = historical[-1]
        files = {p: ('fixture: ' + p).encode() for p in packaging.RAMA_FORM_DEPENDENCIES}
        files.update({f'{base}/candidate.glb': b'form-output-fixture',
                      'art/visual-rounds/face/held-ring.json': (PROJECT / 'art/visual-rounds/face/held-ring.json').read_bytes(),
                      f'{base}/reconstruction.blend': b'form-editable-fixture',
                      'art/visual-rounds/face/build_form_candidate.py': b'# form generator fixture',
                      f'{base}/input/RAMA-HERO-PROVENANCE.json': historical_bytes})
        for level in ('mid', 'far'):
            source = PROJECT / f'assets/heroes/rama-hero-{level}.glb'
            if packaging.digest(source) != packaging.RAMA_FORM_LOD_INPUTS[level]:
                source = PROJECT / base / 'input' / source.name
            files[f'{base}/input/rama-hero-{level}.glb'] = source.read_bytes()
            files[f'assets/heroes/rama-hero-{level}.glb'] = files[f'{base}/rama-hero-{level}.glb']
        def sha(path):
            return packaging.hashlib.sha256(files[path]).hexdigest()
        files[f'{base}/edit-manifest.json'] = json.dumps({
            'schema': 1, 'task': 'R2-08', 'stage': 'principal-facial-form-v1',
            'input_sha256': parent['sha256'], 'output_sha256': sha(f'{base}/candidate.glb'),
            'partition_sha256': parent['metadataSha256'],
            'generator_sha256': sha('art/visual-rounds/face/build_form_candidate.py'),
            'vertex_edits_sha256': sha(f'{base}/vertex-edits.json'), 'bytes': len(files[f'{base}/candidate.glb'])}).encode()
        data = json.loads(files[f'{base}/edit-manifest.json'])
        data.update(original_held_ring_sha256=packaging.RAMA_FORM_HELD_RING_SHA256, original_held_ring_vertices=288)
        files[f'{base}/edit-manifest.json'] = json.dumps(data).encode()
        files[f'{base}/reconstruction.inspection.json'] = json.dumps({
            'candidate_sha256': sha(f'{base}/candidate.glb'), 'editable_sha256': sha(f'{base}/reconstruction.blend'),
            'original_held_ring_sha256': packaging.RAMA_FORM_HELD_RING_SHA256,
            'generator_sha256': sha('art/visual-rounds/face/import_editable.py'),
            'source_inspections': [{'sha256': sha('art/production/reconstruction-rama.blend')},
                                   {'sha256': parent['editableSha256']}]}).encode()
        files[f'{base}/lod-transfer-manifest.json'] = json.dumps({
            'schema': 1, 'task': 'R2-14', 'stage': 'principal-facial-form-lod-transfer-v1',
            'original_held_ring_sha256': packaging.RAMA_FORM_HELD_RING_SHA256,
            'near_input_sha256': parent['sha256'], 'near_candidate_sha256': sha(f'{base}/candidate.glb'),
            'generator_sha256': sha('tools/visual-rounds/integration/transfer_form_lods.py'),
            'levels': {level: {'input_sha256': packaging.RAMA_FORM_LOD_INPUTS[level],
                               'output_sha256': sha(f'{base}/rama-hero-{level}.glb'),
                               'bytes': len(files[f'{base}/rama-hero-{level}.glb']),
                               'all_other_binary_bytes_exact': True, 'json_exact_except_frame_bounds': True} for level in ('mid', 'far')}}).encode()
        stage = {'id': 'principal-facial-form-v1', 'parent': 'face',
                 'asset': f'{base}/candidate.glb', 'sha256': sha(f'{base}/candidate.glb'),
                 'editableSource': f'{base}/reconstruction.blend', 'editableSha256': sha(f'{base}/reconstruction.blend'),
                 'generator': 'art/visual-rounds/face/build_form_candidate.py',
                 'generatorSha256': sha('art/visual-rounds/face/build_form_candidate.py'),
                 'metadata': f'{base}/edit-manifest.json', 'metadataSha256': sha(f'{base}/edit-manifest.json'),
                 'inputEditableSha256': None, 'inputAssetSha256': parent['sha256'], 'editableOrigin': 'imported-stage-asset',
                 'generatedDependencies': [{'path': p, 'sha256': sha(p)} for p in packaging.RAMA_FORM_DEPENDENCIES],
                 'runtimeLods': [{'asset': f'assets/heroes/rama-hero-{level}.glb',
                                  'sha256': sha(f'{base}/rama-hero-{level}.glb')} for level in ('mid', 'far')]}
        for relative, data in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        dirty = set()
        def alter_file(relative, data):
            dirty.add(relative)
            (root / relative).write_bytes(data)
        def mutate_receipt(value, relative, mutate):
            data = json.loads((root / relative).read_text())
            mutate(data)
            alter_file(relative, json.dumps(data).encode())
            digest = packaging.digest(root / relative)
            if relative == value['metadata']:
                value['metadataSha256'] = digest
            else:
                next(d for d in value['generatedDependencies'] if d['path'] == relative)['sha256'] = digest
        def run(name, mutate=None, valid=False):
            for relative in dirty:
                path = root / relative
                if path.is_symlink(): path.unlink()
                path.write_bytes(files[relative])
            dirty.clear()
            value, ancestors = copy.deepcopy(stage), copy.deepcopy(historical)
            if mutate: mutate(value, ancestors)
            error = None
            try:
                packaging._validate_rama_form_stage(root, value, ancestors, {})
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name': 'schema3 ' + name, 'passed': (error is None) == valid, 'rejection': error})
        run('complete fixed form stage and both LODs accepted', valid=True)
        for key, wrong in [('id', 'arbitrary-stage'), ('parent', 'q3'), ('inputAssetSha256', '0'*64),
                           ('inputEditableSha256', parent['editableSha256']), ('editableOrigin', 'authored-from-original-blend'),
                           ('asset', '../candidate.glb'), ('generator', '/tmp/build.py'), ('editableSha256', True)]:
            run(key + ' contradiction rejected', lambda s, h, k=key, v=wrong: s.update({k: v}))
        run('extra stage fields rejected', lambda s, h: s.update(untrackedGenerator='elsewhere'))
        run('omitted dependency rejected', lambda s, h: s['generatedDependencies'].pop())
        run('unsafe dependency rejected', lambda s, h: s['generatedDependencies'][0].update(path='../helper.py'))
        run('rewritten historical stage rejected', lambda s, h: h[0].update(generatorSha256='0'*64))
        run('self-hashed rewritten historical notice rejected', lambda s, h: mutate_receipt(s, f'{base}/input/RAMA-HERO-PROVENANCE.json', lambda n: n.update(sha256='0'*64)))
        for key in ['input_sha256', 'output_sha256', 'partition_sha256', 'generator_sha256', 'vertex_edits_sha256', 'original_held_ring_sha256', 'original_held_ring_vertices']:
            run('self-hashed form metadata ' + key + ' rejected', lambda s, h, k=key: mutate_receipt(s, s['metadata'], lambda n: n.update({k: '0'*64})))
        run('boolean form metadata schema rejected', lambda s, h: mutate_receipt(s, s['metadata'], lambda n: n.update(schema=True)))
        for key in ['candidate_sha256', 'editable_sha256', 'generator_sha256', 'original_held_ring_sha256']:
            run('self-hashed editable receipt ' + key + ' rejected', lambda s, h, k=key: mutate_receipt(s, f'{base}/reconstruction.inspection.json', lambda n: n.update({k: '0'*64})))
        run('missing editable inspection inputs rejected', lambda s, h: mutate_receipt(s, f'{base}/reconstruction.inspection.json', lambda n: n.update(source_inspections=[])))
        for key in ['near_input_sha256', 'near_candidate_sha256', 'generator_sha256', 'original_held_ring_sha256']:
            run('self-hashed LOD ancestry ' + key + ' rejected', lambda s, h, k=key: mutate_receipt(s, f'{base}/lod-transfer-manifest.json', lambda n: n.update({k: '0'*64})))
        run('missing far body binding rejected', lambda s, h: s['runtimeLods'].pop())
        run('self-hashed original held-ring replacement rejected', lambda s, h: mutate_receipt(s, 'art/visual-rounds/face/held-ring.json', lambda n: n.update(held_vertices=287)))
        run('LOD binding order rejected', lambda s, h: s['runtimeLods'].reverse())
        run('stale LOD output binding rejected', lambda s, h: s['runtimeLods'][0].update(sha256='0'*64))
        for key, wrong in [('input_sha256', '0'*64), ('output_sha256', '0'*64), ('bytes', True),
                           ('all_other_binary_bytes_exact', False), ('json_exact_except_frame_bounds', False)]:
            run('self-hashed LOD receipt ' + key + ' rejected', lambda s, h, k=key, v=wrong: mutate_receipt(s, f'{base}/lod-transfer-manifest.json', lambda n: n['levels']['mid'].update({k: v})))
        for relative in files:
            run('changed source rejected: ' + relative, lambda s, h, r=relative: alter_file(r, files[r] + b'changed'))
        run('obsolete position-only LOD receipt rejected', lambda s, h: mutate_receipt(s, f'{base}/lod-transfer-manifest.json', lambda n: n['levels']['mid'].update(json_exact_except_frame_bounds=False, json_exact_except_position_bounds=True)))
        def symlink(s, h):
            relative = f'{base}/candidate.glb'
            dirty.add(relative)
            target = root / relative
            target.unlink()
            outside = root / 'matching-link-target.glb'
            outside.write_bytes(files[relative])
            target.symlink_to(outside)
        run('matching symlink rejected', symlink)
        run('restored fixed form stage accepted', valid=True)


def groom_review_cases(checks: list, review: Path) -> None:
    """Challenge the real frozen proposal in disposable copies, including BIN/JSON drift."""
    validated = packaging.validate_rama_hero_notice(review)
    original = json.loads((review / 'NOTICE/RAMA-HERO-PROVENANCE.json').read_text())
    if original['schema'] not in (4, 5, 6):
        raise ValueError('--groom-review must contain the complete schema4, schema5 or schema6 proposal')
    schema = original['schema']
    checks.append({'name': f'schema{schema} real complete source validates', 'passed': True})
    with tempfile.TemporaryDirectory(prefix='rama-groom-package-cases-') as folder:
        root = Path(folder) / 'project'
        # Copy the validated source closure, not editor caches or unrelated art.
        for relative in validated['sources']:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(review / relative, target)
        (root / 'NOTICE').mkdir(exist_ok=True)
        if schema == 6:
            # The crown's outputs are not the groom's historical runtime trio.
            # Reconstruct the exact old binding before running unchanged adversaries.
            original = json.loads((root / packaging.RAMA_CROWN_PARENT).read_text())
            for name, _, _ in packaging.RAMA_CROWN_OUTPUTS.values():
                shutil.copyfile(root / f'{packaging.RAMA_GROOM_BASE}/{name}', root / f'assets/heroes/{name}')
        if original['schema'] == 5:
            original = json.loads((root / packaging.RAMA_SURFACE_PARENT).read_text())
            shutil.copyfile(root / packaging.RAMA_SURFACE_OLD_BINDING,
                            root / 'scripts/rama_surface_finish.gd')
        (root / 'NOTICE/RAMA-HERO-PROVENANCE.json').write_text(json.dumps(original))
        validated = packaging.validate_rama_hero_notice(root)
        checks.append({'name': 'schema4 historical notice validates with its own exact surface binding', 'passed': True})
        baseline = original['authoringStages'][-1]
        historical = original['authoringStages'][:-1]

        def run(name, mutate=None, valid=False, cloth=False):
            value = copy.deepcopy(original['clothStage'] if cloth else baseline)
            if mutate:
                mutate(value)
            error = None
            try:
                if cloth:
                    packaging._validate_rama_cloth_stage(root, value, {})
                else:
                    packaging._validate_rama_groom_stage(root, value, historical, copy.deepcopy(validated['sources']))
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name': 'schema4 ' + name, 'passed': (error is None) == valid, 'rejection': error})

        run('exact groom-r7 stage passes', valid=True)
        for key in baseline:
            run('missing groom field rejects: ' + key, lambda value, key=key: value.pop(key))
        for key, changed in {'id': 'future-groom', 'parent': 'face', 'asset': '../outside.glb',
                             'sha256': '0' * 64, 'inputAssetSha256': '0' * 64,
                             'inputEditableSha256': historical[-1]['editableSha256'],
                             'editableOrigin': 'native-modeling-stack', 'editableSha256': '0' * 64,
                             'metadataSha256': '0' * 64, 'generatorSha256': '0' * 64}.items():
            run('substituted groom field rejects: ' + key, lambda value, key=key, changed=changed: value.update({key: changed}))
        run('extra groom stage field rejects', lambda value: value.update(optionalShader=True))
        run('missing groom dependency rejects', lambda value: value['generatedDependencies'].pop())
        run('reordered groom dependencies reject', lambda value: value['generatedDependencies'].reverse())
        run('self-rehashed source substitution rejects', lambda value: value['generatedDependencies'][0].update(sha256='0' * 64))
        run('required runtime lifecycle substitution rejects', lambda value: value['runtimeSources'][0].update(sha256='0' * 64))
        run('old R2 runtime LOD binding rejects', lambda value: value['runtimeLods'][0].update(sha256=packaging.RAMA_GROOM_INPUTS['mid']))
        run('extra runtime LOD rejects', lambda value: value['runtimeLods'].append(value['runtimeLods'][0]))
        for relative in (f'{packaging.RAMA_GROOM_BASE}/rama-hero.glb',
                         'assets/heroes/rama-hero-mid.glb',
                         f'{packaging.RAMA_GROOM_BASE}/input/RAMA-HERO-PROVENANCE.json'):
            path = root / relative
            before = path.read_bytes()
            path.write_bytes(before + b' changed')
            run('changed source rejects: ' + relative)
            path.write_bytes(before)
        path = root / f'{packaging.RAMA_GROOM_BASE}/reconstruction.blend'
        before = path.read_bytes()
        path.unlink()
        path.symlink_to(review / f'{packaging.RAMA_GROOM_BASE}/reconstruction.blend')
        run('byte-identical external editable symlink rejects')
        path.unlink()
        path.write_bytes(before)
        run('exact cloth receipt passes', valid=True, cloth=True)
        for key in original['clothStage']:
            run('missing cloth field rejects: ' + key, lambda value, key=key: value.pop(key), cloth=True)
        run('cloth ancestry substitution rejects', lambda value: value.update(parentNoticeSha256='0' * 64), cloth=True)
        run('extra cloth shader declaration rejects', lambda value: value.update(optionalShader=True), cloth=True)
        for relative in (packaging.RAMA_CLOTH_ASSET, packaging.RAMA_CLOTH_ASSET + '.import',
                         'shaders/rama_secondary_cloth.gdshader', 'scripts/rama_surface_finish.gd'):
            path = root / relative
            before = path.read_bytes()
            path.write_bytes(before + b' changed')
            run('changed cloth/runtime source rejects: ' + relative, cloth=True)
            path.write_bytes(before)
        notice_path = root / 'NOTICE/RAMA-HERO-PROVENANCE.json'
        notice = copy.deepcopy(original)
        notice['optionalShader'] = {'approved': True}
        notice_path.write_text(json.dumps(notice))
        try:
            packaging.validate_rama_hero_notice(root)
            rejected = False
        except ValueError:
            rejected = True
        checks.append({'name': 'schema4 undeclared optional top-level shader rejects', 'passed': rejected})
        notice_path.write_text(json.dumps(original))
        # Independently exercise preservation rather than relying on hash pins.
        source = root / f'{packaging.RAMA_FORM_BASE}/candidate.glb'
        candidate = root / f'{packaging.RAMA_GROOM_BASE}/rama-hero.glb'
        doc, binary = packaging._rama_glb(candidate)
        for kind in ('nonhair-bin', 'nonhair-json'):
            changed_doc, changed_bin = copy.deepcopy(doc), bytearray(binary)
            if kind == 'nonhair-bin':
                changed_bin[0] ^= 1
            else:
                changed_doc['nodes'][0]['name'] += '-unauthorized'
            json_bytes = json.dumps(changed_doc, separators=(',', ':')).encode()
            json_bytes += b' ' * (-len(json_bytes) % 4)
            value = struct.pack('<III', 0x46546c67, 2, 28 + len(json_bytes) + len(changed_bin))
            value += struct.pack('<II', len(json_bytes), 0x4e4f534a) + json_bytes
            value += struct.pack('<II', len(changed_bin), 0x004e4942) + changed_bin
            changed_path = root / f'{kind}.glb'
            changed_path.write_bytes(value)
            try:
                packaging.rama_groom_preservation(source, changed_path)
                rejected = False
            except ValueError:
                rejected = True
            checks.append({'name': 'schema4 direct preservation rejects ' + kind, 'passed': rejected})
        run('restored groom accepts after adversaries', valid=True)
        run('restored cloth accepts after adversaries', valid=True, cloth=True)


def bundled_font_cases(checks: list, engine: Path | None = None, evidence: Path | None = None) -> None:
    """Pin source licenses, challenge exact PCK mappings, optionally decode real imports."""
    with tempfile.TemporaryDirectory(prefix='bundled-font-cases-') as folder:
        root = Path(folder) / 'project'
        sources = packaging.validate_bundled_font_sources()
        for relative in sources:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / relative, target)

        def run(name, action, valid=False):
            error = None
            try:
                action()
            except (ValueError, OSError) as exc:
                error = str(exc)
            checks.append({'name': 'fonts: ' + name, 'passed': (error is None) == valid, 'rejection': error})

        run('three exact raw fonts and five notice files accept', lambda: packaging.validate_bundled_font_sources(root), True)
        for relative in sources:
            path = root / relative
            original = path.read_bytes()
            path.write_bytes(original + b' changed')
            run('changed source rejects ' + relative, lambda: packaging.validate_bundled_font_sources(root))
            path.unlink()
            run('missing source rejects ' + relative, lambda: packaging.validate_bundled_font_sources(root))
            path.write_bytes(original)
        font = next(iter(packaging.BUNDLED_FONT_FILES))
        path = root / font
        original = path.read_bytes()
        path.unlink()
        path.symlink_to(PROJECT / font)
        run('matching external raw-font symlink rejects', lambda: packaging.validate_bundled_font_sources(root))
        path.unlink()
        path.write_bytes(original)
        bindings = {'schema': 1, 'sources': sources, 'imports': {}}
        pack = {'entries': []}
        for source, raw in packaging.BUNDLED_FONT_FILES.items():
            resource = 'res://.godot/imported/' + Path(source).name + '-' + 'a' * 32 + '.fontdata'
            payload = ('synthetic imported payload for ' + source).encode()
            record = {'path': resource, 'bytes': len(payload), 'sha256': packaging.hashlib.sha256(payload).hexdigest()}
            bindings['imports'][source] = {'resource': record, 'decoded_raw_ttf': raw}
            pack['entries'].extend([{**record, 'stored_md5_verified': True},
                {'path': 'res://' + source + '.import', 'font_import_target': resource, 'stored_md5_verified': True}])
        run('complete exact payload and remap fixture accepts', lambda: packaging.qualify_bundled_font_package(pack, bindings, root), True)
        unprefixed = copy.deepcopy(pack)
        for entry in unprefixed['entries']:
            entry['path'] = entry['path'].removeprefix('res://')
        run('actual-export unprefixed paths accept', lambda: packaging.qualify_bundled_font_package(unprefixed, bindings, root), True)
        for name, mutate in (
            ('missing font payload', lambda value: value['entries'].pop(0)),
            ('missing runtime remap', lambda value: value['entries'].pop(1)),
            ('duplicate font path', lambda value: value['entries'].append(copy.deepcopy(value['entries'][0]))),
            ('duplicate alias font path', lambda value: value['entries'].append(dict(value['entries'][0], path=value['entries'][0]['path'].removeprefix('res://')))),
            ('duplicate runtime remap', lambda value: value['entries'].append(copy.deepcopy(value['entries'][1]))),
            ('payload substring trick', lambda value: value['entries'][0].update(path=value['entries'][0]['path'] + '-extra')),
            ('substituted font bytes', lambda value: value['entries'][0].update(sha256='0' * 64)),
            ('substituted font size', lambda value: value['entries'][0].update(bytes=1)),
            ('unverified font payload', lambda value: value['entries'][0].update(stored_md5_verified=False)),
            ('wrong remap target', lambda value: value['entries'][1].update(font_import_target=value['entries'][2]['path'])),
            ('unverified runtime remap', lambda value: value['entries'][1].update(stored_md5_verified=False)),
        ):
            changed = copy.deepcopy(pack)
            mutate(changed)
            run(name + ' rejects', lambda: packaging.qualify_bundled_font_package(changed, bindings, root))
        for name, mutate in (
            ('boolean schema', lambda value: value.update(schema=True)),
            ('missing binding', lambda value: value['imports'].pop(font)),
            ('wrong decoded TTF', lambda value: value['imports'][font].update(decoded_raw_ttf={'bytes': 1, 'sha256': '0' * 64})),
            ('wrong raw-source pin', lambda value: value['sources'][font].update(sha256='0' * 64)),
            ('traversal resource path', lambda value: value['imports'][font]['resource'].update(path='res://../outside.fontdata')),
        ):
            changed = copy.deepcopy(bindings)
            mutate(changed)
            run(name + ' rejects', lambda: packaging.qualify_bundled_font_package(pack, changed, root))
        resource = bindings['imports'][font]['resource']['path']
        descriptor = ('[remap]\nimporter="font_data_dynamic"\ntype="FontFile"\npath="' + resource + '"\n').encode()
        run('trimmed Godot remap parses', lambda: packaging._font_import_target(descriptor + b'\0', font), True)
        run('duplicate remap target rejects', lambda: packaging._font_import_target(descriptor + ('path="' + resource + '"\n').encode(), font))
        run('wrong importer rejects', lambda: packaging._font_import_target(descriptor.replace(b'font_data_dynamic', b'texture'), font))
        run('wrong resource type rejects', lambda: packaging._font_import_target(descriptor.replace(b'FontFile', b'Texture2D'), font))
        run('other font target rejects', lambda: packaging._font_import_target(descriptor.replace(b'NotoSans', b'NotoSerif'), font))
        run('target in wrong section rejects', lambda: packaging._font_import_target(descriptor.replace(b'[remap]', b'[deps]'), font))
        run('split remap target rejects', lambda: packaging._font_import_target(descriptor.replace(b'path=', b'[deps]\npath='), font))
        run('duplicate remap section rejects', lambda: packaging._font_import_target(descriptor + b'[remap]\nuid="uid://unused"\n', font))
        run('default section target injection rejects', lambda: packaging._font_import_target(descriptor.replace(b'[remap]', b'[DEFAULT]'), font))
        run('wrong-case section rejects', lambda: packaging._font_import_target(descriptor.replace(b'[remap]', b'[Remap]'), font))
        run('duplicate cross-section target rejects', lambda: packaging._font_import_target(descriptor + ('[deps]\npath="' + resource + '"\n').encode(), font))
        if engine:
            output = evidence or Path(folder) / 'evidence'
            output.mkdir(parents=True, exist_ok=True)
            for source in packaging.BUNDLED_FONT_FILES:
                config = PROJECT / (source + '.import')
                target = root / (source + '.import')
                shutil.copyfile(config, target)
                resource = packaging._font_import_target(config.read_bytes(), source).removeprefix('res://')
                target = root / resource
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PROJECT / resource, target)
            actual = packaging.prove_imported_font_bindings(engine, output / 'fontfile-data.json', root)
            packaging.json_write(output / 'font-bindings.json', actual)
            repeated = packaging.prove_imported_font_bindings(engine, output / 'fontfile-data-repeat.json', root)
            checks.append({'name': 'fonts: actual three FontFile.data identities and repeated proof stable', 'passed': actual == repeated})
            font_names = list(packaging.BUNDLED_FONT_FILES)
            wrong = actual['imports'][font_names[1]]['resource']['path'].removeprefix('res://')
            replaced = actual['imports'][font_names[0]]['resource']['path'].removeprefix('res://')
            shutil.copyfile(root / wrong, root / replaced)
            run('real cache substitution rejects despite intact pinned raw fonts',
                lambda: packaging.prove_imported_font_bindings(engine, output / 'substituted-fontfile-data.json', root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--groom-review', type=Path, help='Complete schema4/5/6 proposal; preserves schema4 own-binding adversaries')
    parser.add_argument('--font-engine', type=Path, help='Optional actual FontFile decode and substituted-cache adversary')
    parser.add_argument('--font-evidence', type=Path)
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
    bundled_font_cases(checks, args.font_engine, args.font_evidence)
    authoring_chain_cases(checks)
    form_stage_cases(checks)
    if args.groom_review:
        groom_review_cases(checks, args.groom_review.resolve(strict=True))
    passed = all(check['passed'] for check in checks)
    report = {'suite': 'rama_package_cases', 'passed': passed, 'checks': checks,
              'source_sha256': {'tools/package-native.py': packaging.digest(PROJECT / 'tools/package-native.py'),
                                'tests/rama_package_cases.py': packaging.digest(Path(__file__))},
              'groom_review': str(args.groom_review) if args.groom_review else None,
              'scope': 'Historical schema1/schema2 and fixed schema3 remain covered. --groom-review accepts schema4/5/6 source closures and tests schema4 with its exact historical trio and surface binding, nonhair BIN/JSON preservation, dependencies, editable identity, source paths and excluded shader. Separate graphics_package_cases.py challenges preserved schema5; rama_crown_package_cases.py challenges schema6. Bundled font raw/license identities and exact payload/remap qualification are covered; optional --font-engine runs actual FontFile.data binding and a substituted-cache adversary. No visual acceptance or complete release export.'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'checks': len(checks), 'failures': [check for check in checks if not check['passed']]}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
