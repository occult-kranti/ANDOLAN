"""Bounded package_all source-snapshot witness; tiny PCKs are never executed."""
from pathlib import Path
import argparse
import copy
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
PROJECT = Path('/workspace/ANDOLAN/games/yuga-native')
FRONTAGE = 'assets/world/block2-frontage.json'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class PastFrontageQualification(Exception):
    pass

def main():
    current = (PROJECT / 'tools/package-native.py').read_bytes()
    assert sha(current) == '79c899ad88f3ef862752fc5b54d2cbfcf35435cad773b55518b9b7639dfe65cf'
    (ROOT / 'corrected-package-native.py').write_bytes(current)
    old = load('old_packager', ROOT / 'original-package-native.py')
    new = load('corrected_packager', ROOT / 'corrected-package-native.py')
    builder = load('tiny_pck_builder', ROOT / 'current-test-builder.py')
    original_data = b'{"fixture":"approved frontage A"}'
    changed_data = b'{"fixture":"substituted frontage B"}'
    files_a = {FRONTAGE: {'bytes': len(original_data), 'sha256': sha(original_data)}}
    files_b = {FRONTAGE: {'bytes': len(changed_data), 'sha256': sha(changed_data)}}
    live = {'sha256': sha(json.dumps(files_a, sort_keys=True).encode()), 'files': files_a}
    forged = {'sha256': live['sha256'], 'files': files_b}
    assert sha(json.dumps(forged['files'], sort_keys=True).encode()) != forged['sha256']
    fixture_packs = {}
    for label, payload in [('a', original_data), ('b', changed_data)]:
        entries = [(name, payload if name == FRONTAGE else ('benign fixture ' + name).encode())
                   for name in builder.NAMES]
        for source, target in builder.GRAPHICS_TEXTURE_FIXTURES.items():
            entries.extend([(source + '.import', f'[remap]\npath="res://{target}"\n'.encode()),
                            (target, b'benign structural texture, not engine-decodable')])
        fixture_packs[label] = builder.pack(entries)[0]
        (ROOT / ('fixture-' + label + '.pck')).write_bytes(fixture_packs[label])
    results = []
    for version, module in [('original', old), ('corrected', new)]:
        for case, pack_label, exported_source, expected in [
            ('valid_control', 'a', live, 'past_frontage'),
            ('changed_pack_retained_source_record', 'b', live, 'frontage_rejection'),
            ('changed_pack_forged_files_retained_signature', 'b', forged,
             'past_frontage' if version == 'original' else 'source_rejection'),
        ]:
            work = ROOT / ('run-' + version + '-' + case)
            work.mkdir(exist_ok=True)
            engine = work / 'dummy-engine'
            engine.write_bytes(b'non-executable engine-copy fixture')
            (work / 'godot-windows-provenance.json').write_text(json.dumps(
                {'files': [{'name': engine.name, **module.record(engine)}]}))
            pck = work / 'yuga-native-linux.pck'
            pck.write_bytes(fixture_packs[pack_label])
            engine_record = module.record(engine)
            engines = {'exporter': {'version': '4.6.3.fixture'},
                       'linux_runtime': {**engine_record, 'kind': 'fixture', 'provenance': None}}
            native = {'sources': {'fixture': 'unchanged'}}
            fonts = {'fixture': 'unrelated proof mocked'}
            exported = {'engine_selection': engines, 'godot_version': '4.6.3.fixture',
                        'native_contracts': native, 'source': copy.deepcopy(exported_source),
                        'rama_hero_provenance': {'fixture': True}, 'font_bindings': fonts,
                        'packs': {'linux': module.record(pck)}, 'git': {'head': 'fixture'}}
            outcome = None
            detail = None
            with ExitStack() as stack:
                for name, value in [('linux_engine_selection', engines),
                                    ('prove_native_contract_sources', native),
                                    ('source_state', copy.deepcopy(live)),
                                    ('validate_rama_hero_notice', {'fixture': True}),
                                    ('prove_imported_font_bindings', fonts),
                                    ('qualify_bundled_font_package', {'fixture': True})]:
                    stack.enter_context(patch.object(module, name, return_value=value))
                stack.enter_context(patch.object(module, 'PLATFORMS', {'linux': 'fixture'}))
                stack.enter_context(patch.object(module, 'safe_notice_copy',
                                                side_effect=PastFrontageQualification()))
                try:
                    module.package_all(argparse.Namespace(linux_engine=engine, windows_engine=engine),
                                       work, exported)
                except PastFrontageQualification:
                    outcome = 'past_frontage'
                except ValueError as error:
                    detail = str(error)
                    outcome = ('source_rejection' if 'Runtime sources changed since PCK export' in detail
                               else 'frontage_rejection' if 'Frontage PCK data differs' in detail
                               else 'unexpected_rejection')
            results.append({'version': version, 'case': case, 'outcome': outcome,
                            'expected': expected, 'passed': outcome == expected, 'detail': detail})
    assert all(x['passed'] for x in results)
    assert (PROJECT / 'tools/package-native.py').read_bytes() == current
    report = {'schema': 1, 'checks': results, 'passed': len(results),
              'original_defect_reproduced': True, 'corrected_defect_rejected': True,
              'scope': 'Actual package_all and real inspect_pack/frontage qualifier on tiny inert structural PCKs. '
                       'Unrelated engine/native/hero/font proofs mocked; stopped after frontage qualification before notices/ZIP. '
                       'No engine, import, export, runtime gameplay or full package acceptance.',
              'source_pins': json.loads((ROOT / 'source-pins.json').read_text()),
              'corrected_source_sha256': sha(current), 'canonical_source_unchanged': True,
              'live_source': live, 'forged_exported_source': forged}
    (ROOT / 'probe-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': len(results), 'old_acceptance': results[2]['outcome'],
                      'corrected_rejection': results[5]['outcome']}))

if __name__ == '__main__':
    main()
