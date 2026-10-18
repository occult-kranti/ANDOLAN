#!/usr/bin/env python3
"""Bounded Python fixtures for explicit Linux exporter/runtime provenance."""
import argparse
from contextlib import ExitStack
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('native_package', PROJECT / 'tools/package-native.py')
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    checks = []

    def check(name, passed):
        checks.append({'name': name, 'passed': bool(passed)})

    def rejects(name, callback, fragment):
        try:
            callback()
        except (ValueError, FileNotFoundError) as error:
            check(name, fragment in str(error))
        else:
            check(name, False)

    # The committed build/source/license evidence is validated without any engine.
    proof = PROJECT / PACKAGE.PUBLIC_RUNTIME_PROOF
    provenance = PACKAGE.public_runtime_provenance(proof)
    check('pinned_zero_patch_public_build_and_license_closure',
          provenance['source_patches'] == 0 and provenance['target'] == 'template_debug'
          and provenance['source_commit'] == '35e80b3a8822a9df9be390814b62f44c0a9c69e8'
          and len(provenance['evidence']) == 5)
    check('diagnostic_patch_hash_not_admitted', PACKAGE.PUBLIC_LINUX_RUNTIME['sha256'] ==
          'dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f')

    with tempfile.TemporaryDirectory(prefix='yuga-linux-runtime-') as folder, ExitStack() as stack:
        root = Path(folder)
        exporter = root / 'official-exporter'
        runtime = root / 'public-runtime'
        windows = root / 'godot.exe'
        exporter.write_bytes(b'official fixture bytes')
        runtime.write_bytes(b'public unmodified fixture bytes')
        windows.write_bytes(b'windows fixture bytes')
        public = {**PACKAGE.record(runtime), 'version': PACKAGE.PUBLIC_LINUX_RUNTIME['version']}
        stack.enter_context(patch.object(PACKAGE, 'PUBLIC_LINUX_RUNTIME', public))
        stack.enter_context(patch.object(PACKAGE, 'PUBLIC_RUNTIME_EXPORTER_SHA', PACKAGE.digest(exporter)))
        versions = {str(exporter): PACKAGE.PUBLIC_RUNTIME_EXPORTER_VERSION, str(runtime): public['version']}
        probe = stack.enter_context(patch.object(PACKAGE.subprocess, 'check_output', side_effect=lambda command, **kw: versions[command[0]] + '\n'))
        selected_args = argparse.Namespace(linux_engine=exporter, linux_runtime=runtime,
                                          linux_runtime_provenance=proof, windows_engine=windows)
        default_args = argparse.Namespace(linux_engine=exporter, windows_engine=windows)
        default = PACKAGE.linux_engine_selection(default_args)
        check('no_override_keeps_exporter_as_runtime',
              default['linux_runtime']['sha256'] == default['exporter']['sha256']
              and default['linux_runtime']['provenance'] is None and probe.call_count == 1)
        selection = PACKAGE.linux_engine_selection(selected_args)
        check('override_records_distinct_exporter_and_runtime',
              selection['exporter']['sha256'] != selection['linux_runtime']['sha256']
              and selection['linux_runtime']['provenance'] == provenance)
        for field in ['linux_runtime', 'linux_runtime_provenance']:
            broken = copy.copy(selected_args)
            setattr(broken, field, None)
            before = probe.call_count
            rejects('paired_argument_' + field, lambda: PACKAGE.linux_engine_selection(broken), 'supplied together')
            check('unpaired_' + field + '_does_not_execute_binary', probe.call_count == before)
        bad_proof = root / 'proof.json'
        broken = copy.copy(selected_args)
        broken.linux_runtime_provenance = bad_proof
        rejects('missing_build_proof_rejected', lambda: PACKAGE.linux_engine_selection(broken), 'provenance')
        bad_proof.write_bytes(proof.read_bytes().replace(b'"source_patches": 0', b'"source_patches": 1'))
        rejects('modified_build_proof_rejected', lambda: PACKAGE.linux_engine_selection(broken), 'provenance')
        with patch.object(PACKAGE, 'PUBLIC_RUNTIME_EVIDENCE', {**PACKAGE.PUBLIC_RUNTIME_EVIDENCE, 'NOTICE/absent.txt': '0' * 64}):
            rejects('missing_linked_evidence_rejected', lambda: PACKAGE.linux_engine_selection(selected_args), 'evidence changed or is missing')
        raw_runtime = runtime.read_bytes()
        runtime.write_bytes(b'patched runtime fixture bytes!!')
        before = probe.call_count
        rejects('patched_runtime_rejected_before_execution', lambda: PACKAGE.linux_engine_selection(selected_args), 'unmodified public binary')
        check('wrong_runtime_never_probed', probe.call_count == before)
        runtime.write_bytes(raw_runtime)
        versions[str(runtime)] = '4.6.3.stable.wrong_build'
        rejects('wrong_runtime_version_rejected', lambda: PACKAGE.linux_engine_selection(selected_args), 'runtime version')
        versions[str(runtime)] = public['version']
        versions[str(exporter)] = '4.6.3.fake'
        rejects('wrong_exporter_version_rejected', lambda: PACKAGE.linux_engine_selection(selected_args), 'exporter version')
        versions[str(exporter)] = PACKAGE.PUBLIC_RUNTIME_EXPORTER_VERSION
        swapped = copy.copy(selected_args)
        swapped.linux_engine = runtime
        rejects('public_runtime_cannot_export', lambda: PACKAGE.linux_engine_selection(swapped), 'official exporter')
        changed = copy.deepcopy(selection)
        changed['exporter']['version'] = '4.6.3.fake'
        rejects('altered_exporter_version_in_manifest_rejected', lambda: PACKAGE.linux_engine_selection(selected_args, changed), 'exporter version')
        rejects('runtime_switch_between_phases_rejected', lambda: PACKAGE.linux_engine_selection(default_args, selection), 'identity changed')
        changed = copy.deepcopy(selection)
        changed['linux_runtime']['provenance']['source_patches'] = 1
        rejects('altered_expected_provenance_rejected', lambda: PACKAGE.linux_engine_selection(selected_args, changed), 'selection or provenance changed')
        before = probe.call_count
        PACKAGE.linux_engine_selection(selected_args, selection)
        check('final_byte_guard_does_not_execute_binaries', probe.call_count == before)
        real_record = PACKAGE.record
        read_count = 0
        def changed_record(path):
            nonlocal read_count
            if path == runtime:
                read_count += 1
                if read_count > 1:
                    return {'bytes': 1, 'sha256': 'changed'}
            return real_record(path)
        with patch.object(PACKAGE, 'record', side_effect=changed_record):
            rejects('binary_mutation_during_probe_rejected', lambda: PACKAGE.linux_engine_selection(selected_args), 'during identity validation')
        check('linux_override_readme_is_explicit', 'community-built, unmodified' in PACKAGE.start_readme('linux', selection)
              and 'official Linux editor binary performed PCK export' in PACKAGE.start_readme('linux', selection))
        check('default_and_windows_readme_unchanged_by_override',
              PACKAGE.start_readme('windows', selection) == PACKAGE.start_readme('windows')
              and PACKAGE.start_readme('linux', default) == PACKAGE.start_readme('linux'))

        # Exercise actual package assembly/ZIP copying with tiny PCKs and mocked
        # unrelated source/font/asset proofs. No engine/export is invoked.
        (root / 'godot-windows-provenance.json').write_text(json.dumps({'files': [{'name': windows.name, **PACKAGE.record(windows)}]}))
        native = {'sources': {'fixture': 'stable'}}
        fonts = {'fixture': 'official-exporter-only'}
        stack.enter_context(patch.object(PACKAGE, 'prove_native_contract_sources', return_value=native))
        stack.enter_context(patch.object(PACKAGE, '_native_contract_inputs', return_value=native['sources']))
        stack.enter_context(patch.object(PACKAGE, 'source_state', return_value={'sha256': 'fixture-source'}))
        stack.enter_context(patch.object(PACKAGE, 'validate_rama_hero_notice', return_value={'fixture': True}))
        font_probe = stack.enter_context(patch.object(PACKAGE, 'prove_imported_font_bindings', return_value=fonts))
        stack.enter_context(patch.object(PACKAGE, 'inspect_pack', side_effect=lambda path: {**PACKAGE.record(path), 'entry_count': 1}))
        stack.enter_context(patch.object(PACKAGE, 'qualify_bundled_font_package', return_value={'passed': True}))
        def notices(destination):
            (destination / 'NOTICE').mkdir()
            for name in ['GODOT-LICENSE.txt', 'GODOT-COPYRIGHT.txt']:
                shutil.copyfile(PROJECT / 'NOTICE' / name, destination / 'NOTICE' / name)
        stack.enter_context(patch.object(PACKAGE, 'safe_notice_copy', side_effect=notices))
        build = root / 'build'
        build.mkdir()
        packs = {}
        for platform in ['linux', 'windows']:
            path = build / ('yuga-native-' + platform + '.pck')
            path.write_bytes((platform + '-pck').encode())
            packs[platform] = PACKAGE.record(path)
        exported = {'engine_selection': selection, 'godot_version': selection['exporter']['version'],
                    'source': {'sha256': 'fixture-source'}, 'git': {'head': 'fixture'},
                    'native_contracts': native, 'rama_hero_provenance': {'fixture': True}, 'font_bindings': fonts, 'packs': packs}
        bad_export = copy.deepcopy(exported)
        bad_export['godot_version'] = '4.6.3.fake'
        rejects('contradictory_export_manifest_version_rejected', lambda: PACKAGE.package_all(selected_args, build, bad_export), 'contradicts')
        result = PACKAGE.package_all(selected_args, build, exported)
        linux = build / 'yuga-native-linux-x86_64'
        win = build / 'yuga-native-windows-x86_64'
        manifest = json.loads((linux / 'PACKAGE-MANIFEST.json').read_text())
        check('package_copies_selected_runtime_and_preserves_windows', (linux / 'godot').read_bytes() == raw_runtime and (win / 'godot.exe').read_bytes() == windows.read_bytes())
        check('font_proof_uses_official_exporter', font_probe.call_args.args[0] == exporter)
        check('package_and_aggregate_bind_both_identities', manifest['exporter'] == selection['exporter']
              and manifest['runtime'] == selection['linux_runtime'] and result['engine_selection'] == selection)
        check('public_proof_and_notices_only_in_linux_zip',
              (linux / 'NOTICE/GODOT-RUNTIME-PROVENANCE.json').is_file()
              and (linux / 'NOTICE/godot-public-runtime/finished-build-verification.json').read_bytes() == proof.read_bytes()
              and not (win / 'NOTICE/GODOT-RUNTIME-PROVENANCE.json').exists()
              and all(result['packages'][p]['all_crc_and_payload_sha256_verified'] for p in ['linux', 'windows']))
        original_copy = shutil.copyfile
        def corrupt_copy(source, target, *a, **kw):
            result = original_copy(source, target, *a, **kw)
            if Path(target).name == 'godot':
                Path(target).write_bytes(b'changed during copy')
            return result
        with patch.object(PACKAGE.shutil, 'copyfile', side_effect=corrupt_copy):
            rejects('copied_runtime_mismatch_rejected', lambda: PACKAGE.package_all(selected_args, build, exported), 'Copied Linux runtime')
        no_identity = copy.deepcopy(exported)
        del no_identity['engine_selection']
        rejects('old_manifest_requires_fresh_export', lambda: PACKAGE.package_all(default_args, build, no_identity), 'lacks exporter/runtime identity')

    result = {'passed': all(c['passed'] for c in checks), 'count': len(checks),
              'passed_count': sum(c['passed'] for c in checks), 'checks': checks,
              'scope': 'Temporary Python fixtures, committed proof hashes and real ZIP assembly; no engine, PCK export, or game execution.'}
    if args.report:
        if args.report.exists():
            raise ValueError('Report must be fresh')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
