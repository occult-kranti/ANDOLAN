#!/usr/bin/env python3
"""Finite schema6 crown and ordered sash provenance cases. No import/export."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import struct
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('crown_packager', PROJECT / 'tools/package-native.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('Use a fresh report path')
    checks = []
    validated = P.validate_rama_hero_notice(PROJECT)
    expected = P.rama_crown_notice()
    paths = set(validated['sources']) | set(P.RAMA_CROWN_DEPENDENCIES) | {P.RAMA_CROWN_PARENT}
    paths.update(row['authoredAsset'] for row in expected['crownStage']['runtimeAssets'])
    paths.update(P.RAMA_SASH_DEPENDENCIES)
    paths.add(P.RAMA_CROWN_NOTICE_HISTORY)
    paths.update(row['authoredAsset'] for row in P.rama_finish_notice()['editStages'][1]['runtimeAssets'])
    before = {r: P.record(PROJECT / r) for r in sorted(paths)}
    before['NOTICE/RAMA-HERO-PROVENANCE.json'] = P.record(PROJECT / 'NOTICE/RAMA-HERO-PROVENANCE.json')
    before['tools/package-native.py'] = P.record(PROJECT / 'tools/package-native.py')
    before['tests/rama_crown_package_cases.py'] = P.record(Path(__file__))
    checks.append({'name': 'actual current schema5 or schema6 complete source closure validates', 'passed': True})
    with tempfile.TemporaryDirectory(prefix='rama-crown-package-cases-') as tmp:
        root = Path(tmp) / 'project'
        for relative in sorted(paths):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / relative, target)
        (root / 'NOTICE').mkdir(exist_ok=True)
        notice_path = root / 'NOTICE/RAMA-HERO-PROVENANCE.json'
        notice_path.write_text(json.dumps(expected))
        for row in expected['crownStage']['runtimeAssets']:
            target = root / row['asset']
            if target.exists():
                target.unlink()
            shutil.copyfile(PROJECT / row['authoredAsset'], target)
        baseline = P.validate_rama_hero_notice(root)
        checks.append({'name': 'complete exact schema6 source proposal validates', 'passed': True,
                       'sources': len(baseline['sources'])})
        portable = root / 'portable-notice-fixture'
        companions = P.copy_rama_crown_companions(root, portable)
        checks.append({'name': 'portable parent and crown attribution companions remain exact at referenced paths',
                       'passed': len(companions) == 2 and all(P.record(portable / r) == value for r, value in companions.items())})
        for level, proof in baseline['crownPreservation'].items():
            checks.append({'name': level + ' direct JSON/nonrail preservation and declared rail counts match',
                           'passed': proof['json_exact'] and proof['outside_selected_records_exact']
                                     and 0 < proof['changed_binary_bytes'] <= proof['allowed_record_bytes'],
                           'proof': proof})
        checks.append({'name': 'schema5 parent preserved byte-exact with its own original trio and binding',
                       'passed': P.digest(root / P.RAMA_CROWN_PARENT) == P.RAMA_CROWN_PARENT_SHA
                                 and P.RAMA_SURFACE_OLD_BINDING in baseline['sources']
                                 and all(row['inputAsset'] in baseline['sources'] for row in expected['crownStage']['runtimeAssets'])})
        dirty = {}

        def replace(relative, data):
            path = root / relative
            if relative not in dirty:
                dirty[relative] = path.read_bytes()
            path.unlink()  # replace the disposable fixture file before mutation
            path.write_bytes(data)

        def restore():
            for relative, data in dirty.items():
                path = root / relative
                if path.exists() or path.is_symlink():
                    path.unlink()
                path.write_bytes(data)
            dirty.clear()

        def run(name, mutate=None, valid=False):
            value = copy.deepcopy(expected)
            error = None
            try:
                if mutate:
                    mutate(value)
                P._validate_rama_crown_notice(root, value, notice_path)
            except (ValueError, OSError) as exc:
                error = str(exc)
            finally:
                restore()
            checks.append({'name': name, 'passed': (error is None) == valid, 'rejection': error})

        for key in expected:
            run('missing crown field rejects: ' + key, lambda n, k=key: n.pop(k))
        run('boolean schema rejects', lambda n: n.update(schema=True))
        run('integer cannot replace exact boolean edit declaration', lambda n: n['crownStage']['editScope'].update(jsonExact=1))
        run('unexpected editable claim rejects', lambda n: n.update(editableSource='unreviewed.blend'))
        run('unknown extra stage rejects', lambda n: n['crownStage'].update(upperHairApproved=True))
        run('missing LOD rejects', lambda n: n['crownStage']['runtimeAssets'].pop())
        run('reordered LODs reject', lambda n: n['crownStage']['runtimeAssets'].reverse())
        run('old groom output cannot masquerade as crown', lambda n: n['crownStage']['runtimeAssets'][0].update(sha256=P.RAMA_GROOM_OUTPUTS['near']))
        run('unrestricted changed-channel claim rejects', lambda n: n['crownStage']['editScope'].update(attributes=['POSITION','NORMAL','TANGENT','JOINTS_0']))
        run('wrong parent ancestry rejects', lambda n: n.update(parentNoticeSha256='0'*64))
        run('parent traversal rejects', lambda n: n.update(parentNotice='../outside.json'))
        run('missing dependency rejects', lambda n: n['crownStage']['generatedDependencies'].pop())
        run('reordered dependencies reject', lambda n: n['crownStage']['generatedDependencies'].reverse())
        relevant = [P.RAMA_CROWN_PARENT, *P.RAMA_CROWN_DEPENDENCIES]
        relevant += [row[key] for row in expected['crownStage']['runtimeAssets'] for key in ('asset','authoredAsset')]
        for relative in relevant:
            def missing(n, r=relative):
                dirty[r] = (root / r).read_bytes()
                (root / r).unlink()
            run('missing source rejects: ' + relative, missing)
            run('tampered source rejects: ' + relative,
                lambda n, r=relative: replace(r, (root / r).read_bytes() + b'altered'))
        for relative in (P.RAMA_CROWN_PARENT, f'{P.RAMA_CROWN_BASE}/build_candidate.py',
                         f'{P.RAMA_CROWN_BASE}/candidate-r2/source-manifest.json',
                         'assets/heroes/rama-hero.glb'):
            def self_hash(n, r=relative):
                replace(r, (root / r).read_bytes() + b'changed')
                digest = P.digest(root / r)
                if r == P.RAMA_CROWN_PARENT:
                    n['parentNoticeSha256'] = digest
                elif r == 'assets/heroes/rama-hero.glb':
                    n['sha256'] = digest
                    n['crownStage']['runtimeAssets'][0]['sha256'] = digest
                else:
                    next(d for d in n['crownStage']['generatedDependencies'] if d['path'] == r)['sha256'] = digest
            run('self-hashed replacement rejects: ' + relative, self_hash)
        for relative in ('assets/heroes/rama-hero.glb', P.RAMA_CROWN_PARENT,
                         f'{P.RAMA_CROWN_BASE}/build_candidate.py'):
            def linked(n, r=relative):
                path = root / r
                dirty[r] = path.read_bytes()
                path.unlink()
                target = root / 'identical-external-target'
                target.write_bytes(dirty[r])
                path.symlink_to(target)
            run('matching-content symlink rejects: ' + relative, linked)
        directory = root / 'assets/heroes'
        moved = root / 'assets/hidden-heroes'
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        run('matching internal ancestor-directory symlink rejects')
        directory.unlink()
        moved.rename(directory)
        manifest = json.loads((root / f'{P.RAMA_CROWN_BASE}/candidate-r2/source-manifest.json').read_text())
        row = expected['crownStage']['runtimeAssets'][0]
        source, candidate = root / row['inputAsset'], root / row['asset']
        doc, binary = P._rama_glb(candidate)
        for kind in ('nonrail-bin', 'nonrail-json', 'nonrail-json-whitespace'):
            raw = bytearray(candidate.read_bytes())
            json_length = struct.unpack_from('<I', raw, 12)[0]
            if kind == 'nonrail-bin':
                raw[28 + json_length] ^= 1
            elif kind == 'nonrail-json-whitespace':
                assert raw[20 + json_length - 1] == ord(' ')
                raw[20 + json_length - 1] = ord('\t')
            else:
                name = doc['nodes'][0]['name']
                needle = json.dumps(name).encode()
                start = raw.index(needle, 20) + 1
                raw[start] = ord('Z') if raw[start] != ord('Z') else ord('Y')
            target = root / (kind + '.glb')
            target.write_bytes(raw)
            error = None
            try:
                P.rama_crown_preservation(source, target, manifest['levels']['near']['selected_vertex_ids'])
            except ValueError as exc:
                error = str(exc)
            checks.append({'name': 'direct finite byte gate rejects ' + kind + ' without trusting output hash',
                           'passed': error is not None and ('nonrail binary' in error if kind == 'nonrail-bin' else 'JSON' in error),
                           'rejection': error})
        run('restored exact schema6 proposal still validates', valid=True)
        # Retain all crown-only adversaries above. The accepted successor is an
        # ordered flat stage sequence under the same schema5 parent.
        sequence = P.rama_finish_notice()
        notice_path.write_text(json.dumps(sequence))
        for binding in sequence['editStages'][1]['runtimeAssets']:
            shutil.copyfile(root / binding['authoredAsset'], root / binding['asset'])
        final = P.validate_rama_hero_notice(root)
        checks.append({'name': 'ordered crown then sash validates with exact historical crown and schema5 parent',
                       'passed': sequence['parentNotice'] == expected['parentNotice']
                                 and sequence['editStages'][0] == expected['crownStage']
                                 and P.digest(root / P.RAMA_CROWN_NOTICE_HISTORY) == P.RAMA_CROWN_NOTICE_HISTORY_SHA})
        for level, proof in final['sashPreservation'].items():
            checks.append({'name': level + ' selected sash UV replays exact float32 scale with all other bytes unchanged',
                           'passed': all(proof[k] is True for k in ('json_exact', 'outside_selected_uv_bytes_exact', 'scale_replay_exact'))
                                     and proof['changed_bytes'] > 0, 'proof': proof})
        companions = P.copy_rama_crown_companions(root, portable)
        checks.append({'name': 'ordered stage portable provenance retains exact parent crown fixture and both attributions',
                       'passed': len(companions) == 4 and all(P.record(portable / r) == value for r, value in companions.items())})
        for name, mutate in (
                ('reordered edit stages reject', lambda n: n['editStages'].reverse()),
                ('replayed duplicate edit stage rejects', lambda n: n['editStages'].append(n['editStages'][1]))):
            value = copy.deepcopy(sequence)
            mutate(value)
            error = None
            try:
                P._validate_rama_finish_notice(root, value, notice_path)
            except ValueError as exc:
                error = str(exc)
            checks.append({'name': name, 'passed': error is not None, 'rejection': error})
        row = sequence['editStages'][1]['runtimeAssets'][0]
        source, candidate = root / row['inputAsset'], root / row['asset']
        doc, binary = P._rama_glb(candidate)
        primitive = doc['meshes'][2]['primitives'][3]
        for attribute, vertex, reason in (
                ('POSITION', 0, 'non-UV payload'),
                ('TEXCOORD_0', row['selectedVertexRangeInclusive'][0], 'scale replay')):
            raw = bytearray(candidate.read_bytes())
            accessor = doc['accessors'][primitive['attributes'][attribute]]
            view = doc['bufferViews'][accessor['bufferView']]
            stride = view.get('byteStride', 12 if attribute == 'POSITION' else 8)
            offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0) + vertex * stride
            raw[28 + struct.unpack_from('<I', raw, 12)[0] + offset] ^= 1
            target = root / ('altered-sash-' + attribute + '.glb')
            target.write_bytes(raw)
            error = None
            try:
                P.rama_sash_preservation(source, target, row['selectedVertexRangeInclusive'])
            except ValueError as exc:
                error = str(exc)
            checks.append({'name': 'direct sash gate rejects altered ' + attribute + ' independently of fixed output hash',
                           'passed': error is not None and reason in error, 'rejection': error})
    after = {relative: P.record(PROJECT / relative) for relative in before}
    checks.append({'name': 'all actual source and helper bytes unchanged by disposable adversaries', 'passed': before == after})
    report = {'passed': all(c['passed'] for c in checks), 'count': len(checks), 'checks': checks,
              'source_before': before, 'source_after': after,
              'scope': 'Unchanged crown-only adversaries plus bounded ordered sash stages, exact float32 UV replay and non-UV preservation. Schema5 and crown-only history retained. No engine, import, export, raster or art acceptance.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'count': report['count']}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
