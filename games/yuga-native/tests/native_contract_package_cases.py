#!/usr/bin/env python3
"""Actual source-checker counterexamples for package preflight; never run Godot."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract_packaging', PROJECT / 'tools/package-native.py')
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    inputs = packaging._native_contract_inputs(PROJECT)
    checks = []
    with tempfile.TemporaryDirectory(prefix='native-contract-package-') as temporary:
        repository = Path(temporary) / 'repository'
        project = repository / 'games/yuga-native'
        originals = {}
        for relative in inputs:
            path = repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            originals[relative] = (PROJECT.parents[1] / relative).read_bytes()
            path.write_bytes(originals[relative])
        counter = 0

        def folder():
            nonlocal counter
            counter += 1
            target = Path(temporary) / ('run-' + str(counter))
            target.mkdir()
            return target

        def rejected(name, operation, reason):
            error = None
            try:
                operation()
            except ValueError as caught:
                error = str(caught)
            checks.append({'name': name, 'passed': error is not None and reason in error, 'rejection': error})

        # This contract fixture supplies valid unrelated UID/engine identity
        # prerequisites. The real contract subprocess and source binding are
        # never mocked; engine/UID policy has its own dedicated fixtures.
        fixture_selection = {'exporter': {'version': 'contract-fixture'}}

        def export_contract_gate():
            with patch.object(packaging, 'validate_runtime_script_uids', return_value={}), \
                 patch.object(packaging, 'linux_engine_selection', return_value=fixture_selection):
                return packaging.export_all(SimpleNamespace(), folder())

        def package_contract_gate(exported):
            exported = {'engine_selection': fixture_selection, 'godot_version': 'contract-fixture', **exported}
            with patch.object(packaging, 'linux_engine_selection', return_value=fixture_selection):
                return packaging.package_all(SimpleNamespace(), folder(), exported)

        proof_dir = folder()
        valid = packaging.prove_native_contract_sources(proof_dir / 'report.json', project)
        valid_report = json.loads((proof_dir / 'report.json').read_text())
        checks.append({'name': 'actual current checker and full exact source closure accept',
                       'passed': valid['checks'] > 0 and valid['sources'] == inputs,
                       'checker_assertions': valid['checks'], 'source_count': len(inputs)})
        player = project / 'scripts/player.gd'
        original_player = player.read_bytes()
        player.write_bytes(original_player + b'\n# stale contract fixture\n')
        stale_dir = folder()
        rejected('changed actual player bytes reject while catalog stays fixed',
                 lambda: packaging.prove_native_contract_sources(stale_dir / 'report.json', project),
                 'Native contract source check failed')
        actual_stale = json.loads((stale_dir / 'report.json').read_text())
        checks.append({'name': 'actual checker identifies the player content pin',
                       'passed': any(item['name'] == 'native-offline-triad_content_games/yuga-native/scripts/player.gd'
                                     and item['passed'] is False for item in actual_stale['checks'])})
        packaging.PROJECT = project
        rejected('export rejects stale player after valid unrelated prerequisites',
                 export_contract_gate, 'Native contract source check failed')
        rejected('package rejects stale player after valid engine identity',
                 lambda: package_contract_gate({'native_contracts': valid}),
                 'Native contract source check failed')
        player.write_bytes(original_player)
        rejected('old export without a source-bound native contract proof rejects before engine',
                 lambda: package_contract_gate({}),
                 'Native contract sources or proof changed since export')
        fixture = project / 'tests/fixtures/contracts/native-content3-descriptor.json'
        fixture_original = fixture.read_bytes()
        fixture.write_bytes(fixture_original + b'\n')
        rejected('changed retained input rejects even when checker still passes',
                 lambda: package_contract_gate({'native_contracts': valid}),
                 'Native contract sources or proof changed since export')
        fixture.write_bytes(fixture_original)
        rejected('existing successful report cannot stand in for fresh execution',
                 lambda: packaging.prove_native_contract_sources(proof_dir / 'report.json', project),
                 'fresh report/log paths')
        checker = project / 'tools/check-native-contracts.py'
        checker_original = checker.read_bytes()

        def replace_report(value):
            checker.write_text('import json,sys\nfrom pathlib import Path\n'
                               'Path(sys.argv[sys.argv.index("--report")+1]).write_text('
                               + repr(json.dumps(value)) + ')\n')

        replace_report({'passed': True, 'checks': []})
        rejected('exit-zero empty proof rejects',
                 lambda: packaging.prove_native_contract_sources(folder() / 'report.json', project),
                 'nonempty successful checks')
        replace_report(valid_report)
        rejected('replayed success does not bind a substituted checker',
                 lambda: packaging.prove_native_contract_sources(folder() / 'report.json', project),
                 'report/source bindings changed or differ')
        checker.write_bytes(checker_original)
        # Each new retained identity is a direct packaging input: absence
        # and changed bytes must reject instead of replaying an older proof.
        for revision in (6, 7):
            for kind in ('catalog', 'descriptor'):
                retained = project / f'tests/fixtures/contracts/native-content{revision}-{kind}.json'
                retained_bytes = retained.read_bytes()
                retained.write_bytes(retained_bytes + b'\n')
                rejected(f'changed retained content{revision} {kind} rejects source proof',
                         lambda: packaging.prove_native_contract_sources(folder() / 'report.json', project),
                         'Native contract source check failed')
                retained.write_bytes(retained_bytes)
                retained.unlink()
                rejected(f'missing retained content{revision} {kind} rejects input closure',
                         lambda: packaging._native_contract_inputs(project),
                         'Missing or unsafe native contract input')
                retained.write_bytes(retained_bytes)
        # The exact rejected source state is reconstructed from committed bytes,
        # independent of the currently corrected revision8 catalog/checker.
        for relative in ['assets/contracts/native-contracts-v1.json', 'tools/check-native-contracts.py', 'scripts/native_contracts.gd']:
            (project / relative).write_bytes(subprocess.check_output([
                'git', 'show', '83f88f840c59934155aec19d95b41d920d15c6c1:games/yuga-native/' + relative], cwd=PROJECT))
        historical_catalog = json.loads((project / 'assets/contracts/native-contracts-v1.json').read_text())
        for profile in historical_catalog['profiles']:
            for relative, expected_sha in profile['content_sources'].items():
                if relative == 'games/yuga-native/scripts/player.gd':
                    continue  # Preserve the intended real current-player mismatch.
                historical_bytes = subprocess.check_output([
                    'git', 'show', '83f88f840c59934155aec19d95b41d920d15c6c1:' + relative], cwd=PROJECT)
                if hashlib.sha256(historical_bytes).hexdigest() != expected_sha:
                    raise ValueError('Historical non-player input does not match frozen catalog: ' + relative)
                target = repository / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(historical_bytes)
        old_dir = folder()
        rejected('exact rejected83f catalog checker and runtime refuse its actual player',
                 lambda: packaging.prove_native_contract_sources(old_dir / 'report.json', project),
                 'Native contract source check failed')
        old_report = json.loads((old_dir / 'report.json').read_text())
        checks.append({'name': 'reconstructed83f rejects only the real player source pin',
                       'passed': [item['name'] for item in old_report['checks'] if not item['passed']]
                       == ['native-offline-triad_content_games/yuga-native/scripts/player.gd']})
        for relative, data in originals.items():
            (repository / relative).write_bytes(data)
        final = packaging.prove_native_contract_sources(folder() / 'report.json', project)
        checks.append({'name': 'restored complete current source proof matches first proof', 'passed': final == valid})
        args.report.parent.mkdir(parents=True, exist_ok=True)
        archive = args.report.parent / (args.report.stem + '-actual-checker-reports')
        archive.mkdir(exist_ok=False)
        for prefix, location in [('valid', proof_dir), ('changed-player', stale_dir), ('historical83f', old_dir)]:
            for name in ['report.json', 'report.log']:
                shutil.copyfile(location / name, archive / (prefix + '-' + name))
    packaging.PROJECT = PROJECT
    report = {'passed': all(item['passed'] for item in checks), 'checks': checks,
              'sources': {'tools/package-native.py': packaging.record(PROJECT / 'tools/package-native.py'),
                          'tools/check-native-contracts.py': packaging.record(PROJECT / 'tools/check-native-contracts.py'),
                          'tests/native_contract_package_cases.py': packaging.record(Path(__file__))},
              'scope': 'Actual source checker, isolated tiny source closure, entry-point early rejection and retained exact83f counterexample. No engine, import, export or runtime scene executed.'}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'checks': len(checks), 'failed': [item for item in checks if not item['passed']]}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
