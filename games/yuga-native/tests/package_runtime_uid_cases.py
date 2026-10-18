#!/usr/bin/env python3
"""Small source-only counterexamples for the pre-engine runtime UID gate."""
import argparse
import importlib.util
import json
from pathlib import Path
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

    with tempfile.TemporaryDirectory(prefix='yuga-runtime-uids-') as folder:
        root = Path(folder)
        scripts = root / 'scripts'
        (scripts / 'nested').mkdir(parents=True)
        for name, uid in [('boot', 'uid://b12\n'), ('nested/loader', 'uid://c34\n')]:
            (scripts / (name + '.gd')).write_text('extends Node\n')
            (scripts / (name + '.gd.uid')).write_text(uid)
        sidecar = scripts / 'nested/loader.gd.uid'
        check('nested_runtime_scripts_have_distinct_uids', PACKAGE.validate_runtime_script_uids(root)['scripts'] == 2)

        def rejects(name, value, fragment):
            if value is None:
                sidecar.unlink()
            else:
                sidecar.write_bytes(value)
            try:
                PACKAGE.validate_runtime_script_uids(root)
            except ValueError as error:
                check(name, fragment in str(error))
            else:
                check(name, False)
            sidecar.write_text('uid://c34\n')

        rejects('missing_sidecar_rejected', None, 'Missing regular')
        rejects('empty_sidecar_rejected', b'', 'Malformed')
        rejects('uppercase_or_extra_content_rejected', b'uid://C34\nextra\n', 'Malformed')
        rejects('missing_terminal_newline_rejected', b'uid://c34', 'Malformed')
        rejects('duplicate_nested_uid_rejected', b'uid://b12\n', 'Duplicate')
        rejects('leading_zero_numeric_alias_rejected', b'uid://ab12\n', 'Malformed')
        rejects('noncanonical_base34_digit_rejected', b'uid://z9\n', 'Malformed')
        rejects('signed63_bit_overflow_rejected', b'uid://eeeeeeeeeeeee\n', 'Out-of-range')
        for folder in ['tests', 'tools']:
            (root / folder).mkdir()
            (root / folder / 'fixture.gd').write_text('extends SceneTree\n')
        check('nonruntime_test_tool_sidecars_not_required', PACKAGE.validate_runtime_script_uids(root)['scripts'] == 2)
        outside = root / 'outside'
        outside.mkdir()
        (outside / 'uncovered.gd').write_text('extends Node\n')
        for name, target in [('linked_directory', outside), ('linked_script.gd', outside / 'uncovered.gd')]:
            link = scripts / name
            link.symlink_to(target, target_is_directory=target.is_dir())
            try:
                PACKAGE.validate_runtime_script_uids(root)
            except ValueError as error:
                check(name + '_rejected', 'symlink' in str(error))
            else:
                check(name + '_rejected', False)
            link.unlink()
        sidecar.unlink()
        with patch.object(PACKAGE, 'PROJECT', root), patch.object(PACKAGE, 'prove_native_contract_sources') as proof, patch.object(PACKAGE.subprocess, 'run') as engine:
            try:
                PACKAGE.export_all(argparse.Namespace(), root / 'build')
            except ValueError as error:
                check('missing_uid_fails_before_proofs_or_engine', 'Missing regular' in str(error) and not proof.called and not engine.called)
            else:
                check('missing_uid_fails_before_proofs_or_engine', False)
    actual = PACKAGE.validate_runtime_script_uids(PROJECT)
    check('current_runtime_uid_closure', actual['scripts'] > 0 and len(actual['sidecars']) == actual['scripts'])
    result = {'passed': all(c['passed'] for c in checks), 'count': len(checks), 'passed_count': sum(c['passed'] for c in checks), 'checks': checks, 'runtime_scripts': actual['scripts'], 'scope': 'Python temporary fixtures and source metadata only; no engine launched.'}
    if args.report:
        if args.report.exists():
            raise ValueError('Report must be fresh')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
