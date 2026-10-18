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
    patched_proof = PROJECT / PACKAGE.PATCHED_RUNTIME_PROOF
    patched_provenance = PACKAGE.patched_runtime_provenance(patched_proof)
    check('explicit_patched_build_source_and_license_closure',
          patched_provenance['source_patches'] == 1
          and patched_provenance['source_commit'] == provenance['source_commit']
          and patched_provenance['source_archive'] == provenance['source_archive']
          and patched_provenance['variant'] == 'pipeline-low-priority-v1'
          and len(patched_provenance['evidence']) == 11
          and PACKAGE.PATCHED_LINUX_RUNTIME['sha256'] == 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e')
    patch_base = PROJECT / PACKAGE.PATCHED_RUNTIME_BASE
    check('one_priority_substitution_reproduces_exact_patched_header',
          (patch_base / 'pipeline_hash_map_rd.original.h').read_bytes().replace(
              b', p_high_priority, "PipelineCompilation")', b', false, "PipelineCompilation")')
          == (patch_base / 'pipeline_hash_map_rd.proposed.h').read_bytes()
          and patched_provenance['patches'][0]['sha256'] == PACKAGE.digest(patch_base / 'proposed.patch'))
    mapping = patched_provenance['bundled_evidence']
    check('baseline_and_patched_proofs_have_unique_bundled_paths',
          len(set(mapping.values())) == len(mapping)
          and mapping[PACKAGE.PUBLIC_RUNTIME_PROOF] != mapping[PACKAGE.PATCHED_RUNTIME_PROOF]
          and all(not Path(path).is_absolute() and '..' not in Path(path).parts for path in mapping.values()))

    with tempfile.TemporaryDirectory(prefix='yuga-linux-runtime-') as folder, ExitStack() as stack:
        root = Path(folder)
        exporter = root / 'official-exporter'
        runtime = root / 'public-runtime'
        patched_runtime = root / 'patched-runtime'
        windows = root / 'godot.exe'
        exporter.write_bytes(b'official fixture bytes')
        runtime.write_bytes(b'public unmodified fixture bytes')
        patched_runtime.write_bytes(b'public pipeline-priority fixture bytes')
        windows.write_bytes(b'windows fixture bytes')
        public = {**PACKAGE.record(runtime), 'version': PACKAGE.PUBLIC_LINUX_RUNTIME['version']}
        stack.enter_context(patch.object(PACKAGE, 'PUBLIC_LINUX_RUNTIME', public))
        patched_public = {**PACKAGE.record(patched_runtime), 'version': PACKAGE.PATCHED_LINUX_RUNTIME['version']}
        stack.enter_context(patch.object(PACKAGE, 'PATCHED_LINUX_RUNTIME', patched_public))
        stack.enter_context(patch.object(PACKAGE, 'PUBLIC_RUNTIME_EXPORTER_SHA', PACKAGE.digest(exporter)))
        versions = {str(exporter): PACKAGE.PUBLIC_RUNTIME_EXPORTER_VERSION, str(runtime): public['version'],
                    str(patched_runtime): patched_public['version']}
        probe = stack.enter_context(patch.object(PACKAGE.subprocess, 'check_output', side_effect=lambda command, **kw: versions[command[0]] + '\n'))
        selected_args = argparse.Namespace(linux_engine=exporter, linux_runtime=runtime,
                                          linux_runtime_provenance=proof, windows_engine=windows)
        default_args = argparse.Namespace(linux_engine=exporter, windows_engine=windows)
        patched_args = argparse.Namespace(linux_engine=exporter, linux_runtime=patched_runtime,
                                         linux_runtime_provenance=patched_proof, windows_engine=windows,
                                         linux_runtime_variant='pipeline-low-priority')
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
        patched_selection = PACKAGE.linux_engine_selection(patched_args)
        check('explicit_patched_selection_separates_exporter_and_declared_variant',
              patched_selection['exporter'] == selection['exporter']
              and patched_selection['linux_runtime']['provenance'] == patched_provenance
              and patched_selection['linux_runtime']['kind'] == 'patched-public-source-template-debug')
        before = probe.call_count
        for label, fields, fragment in [
            ('patched_runtime_with_unmodified_variant', {'linux_runtime_variant': 'unmodified-public'}, 'unmodified public binary'),
            ('patched_runtime_with_baseline_proof', {'linux_runtime_provenance': proof}, 'pipeline-priority build proof'),
            ('unmodified_runtime_with_patched_variant', {'linux_runtime': runtime}, 'pipeline-priority patched binary'),
            ('unknown_variant', {'linux_runtime_variant': 'arbitrary'}, 'Unknown Linux runtime variant'),
            ('patched_variant_without_override', {'linux_runtime': None, 'linux_runtime_provenance': None}, 'requires'),
        ]:
            broken = copy.copy(patched_args)
            for field, value in fields.items():
                setattr(broken, field, value)
            rejects(label, lambda: PACKAGE.linux_engine_selection(broken), fragment)
        for label, field, value in [('changed_expected_variant', 'variant', 'unmodified-public'),
                                    ('changed_expected_patch', 'source_patches', 0)]:
            changed = copy.deepcopy(patched_selection)
            changed['linux_runtime']['provenance'][field] = value
            rejects(label, lambda: PACKAGE.linux_engine_selection(patched_args, changed), 'selection or provenance changed')
        changed = copy.deepcopy(patched_selection)
        changed['linux_runtime']['provenance']['bundled_evidence'][PACKAGE.PATCHED_RUNTIME_PROOF] = mapping[PACKAGE.PUBLIC_RUNTIME_PROOF]
        rejects('changed_expected_proof_mapping', lambda: PACKAGE.linux_engine_selection(patched_args, changed), 'selection or provenance changed')
        with patch.object(PACKAGE, 'PATCHED_RUNTIME_EVIDENCE', {**PACKAGE.PATCHED_RUNTIME_EVIDENCE,
                                                             'NOTICE/absent-patch.txt': '0' * 64}):
            rejects('missing_patched_evidence', lambda: PACKAGE.linux_engine_selection(patched_args), 'evidence changed or is missing')
        check('cross_variant_and_proof_mutations_reject_before_execution', probe.call_count == before)
        check('patched_readme_is_explicit_without_changing_windows',
              'one pipeline native-task priority patch' in PACKAGE.start_readme('linux', patched_selection)
              and 'This is a modified runtime' in PACKAGE.start_readme('linux', patched_selection)
              and PACKAGE.start_readme('windows', patched_selection) == PACKAGE.start_readme('windows'))

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
        stack.enter_context(patch.object(PACKAGE, 'qualify_world_frontage_package', return_value={'passed': True}))
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

        patched_build = root / 'patched-build'
        patched_build.mkdir()
        patched_export = copy.deepcopy(exported)
        patched_export['engine_selection'] = patched_selection
        for platform in ['linux', 'windows']:
            shutil.copyfile(build / ('yuga-native-' + platform + '.pck'), patched_build / ('yuga-native-' + platform + '.pck'))
        patched_result = PACKAGE.package_all(patched_args, patched_build, patched_export)
        patched_linux = patched_build / 'yuga-native-linux-x86_64'
        patched_manifest = json.loads((patched_linux / 'PACKAGE-MANIFEST.json').read_text())
        check('patched_package_copies_exact_runtime_and_declares_unexecuted_variant',
              (patched_linux / 'godot').read_bytes() == patched_runtime.read_bytes()
              and patched_manifest['packaging'] == 'patched-public-template-debug-with-official-exported-pck'
              and patched_manifest['runtime'] == patched_selection['linux_runtime']
              and patched_manifest['execution_status'] == 'not_executed_by_packager'
              and patched_result['engine_selection'] == patched_selection)
        check('every_mapped_patch_build_and_license_proof_survives_copy', all(
            PACKAGE.record(patched_linux / target) == patched_provenance['evidence'][source]
            for source, target in mapping.items()))
        check('patched_notice_and_zip_distinguish_exporter_and_patch',
              'Source patches: 1' in (patched_linux / 'NOTICE/GODOT-RUNTIME.txt').read_text()
              and 'not the official editor binary' in (patched_linux / 'NOTICE/GODOT-RUNTIME.txt').read_text()
              and all(patched_result['packages'][p]['all_crc_and_payload_sha256_verified'] for p in ['linux', 'windows'])
              and font_probe.call_args.args[0] == exporter)
        check('patched_selection_does_not_change_windows_archive_payloads',
              json.loads((patched_build / 'yuga-native-windows-x86_64/PACKAGE-MANIFEST.json').read_text())['payloads']
              == json.loads((win / 'PACKAGE-MANIFEST.json').read_text())['payloads'])
        final_source = next(reversed(patched_provenance['evidence']))
        def corrupt_prior_proof(source, target, *a, **kw):
            result = original_copy(source, target, *a, **kw)
            if Path(source) == PROJECT / final_source:
                (patched_linux / mapping[PACKAGE.PUBLIC_RUNTIME_PROOF]).write_bytes(b'overwritten proof')
            return result
        with patch.object(PACKAGE.shutil, 'copyfile', side_effect=corrupt_prior_proof):
            rejects('earlier_proof_changed_by_later_copy_rejected',
                    lambda: PACKAGE.copy_public_runtime_notice(patched_linux, patched_selection), 'proof closure differs')

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
