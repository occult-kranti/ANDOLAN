#!/usr/bin/env python3
"""Display-free checks for capture engine selection, fixture closure and cache isolation."""
import argparse
import ast
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

PROJECT = pathlib.Path(__file__).resolve().parents[1]
DRIVER = PROJECT / 'tools/ui-campaign/run.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=pathlib.Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('ui_capture_driver', DRIVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before = module.sha(DRIVER)
    checks = []

    def check(name, passed, detail=None):
        checks.append({'name': name, 'passed': bool(passed), 'details': detail})

    with tempfile.TemporaryDirectory(prefix='yuga-capture-tool-') as temporary:
        root = pathlib.Path(temporary)
        seed, project = root / 'seed', root / 'project'
        (seed / 'nested').mkdir(parents=True)
        project.mkdir()
        (seed / 'nested/one.cache').write_bytes(b'exact shader bytes\0')
        (project / 'project.godot').write_text('[application]\nconfig/name="YUGA test"\n')
        original = module.sha(seed / 'nested/one.cache')
        _, target, pins = module.copy_godot_cache(seed, project, root / 'data')
        check('Godot cache copy is exact and limited to declared shader members',
              pins == {'nested/one.cache': original} and module.sha(target / 'nested/one.cache') == original)
        (target / 'nested/one.cache').write_bytes(b'private rewritten cache')
        check('Private cache writes leave source seed unchanged', module.sha(seed / 'nested/one.cache') == original)
        for label, prepare, undo in [
            ('preferences', lambda: (seed / 'courtyard-settings.cfg').write_text('not a shader'), lambda: (seed / 'courtyard-settings.cfg').unlink()),
            ('symlink', lambda: (seed / 'alias.cache').symlink_to(seed / 'nested/one.cache'), lambda: (seed / 'alias.cache').unlink()),
            ('custom user directory', lambda: (project / 'project.godot').write_text('[application]\nconfig/name="YUGA test"\nconfig/use_custom_user_dir=true\n'), lambda: (project / 'project.godot').write_text('[application]\nconfig/name="YUGA test"\n')),
        ]:
            prepare()
            try:
                module.copy_godot_cache(seed, project, root / 'rejected')
                rejected = False
            except ValueError:
                rejected = True
            check('Cache copy rejects ' + label + ' before writing destination', rejected and not (root / 'rejected').exists())
            undo()
        engine = pathlib.Path(shutil.which('godot')).resolve()
        plan = root / 'plan.json'
        plan.write_text('[{"stage":"outcome-sun"}]')
        base = [sys.executable, str(DRIVER), '--dry-run', '--output', str(root / 'capture'), '--mode', 'integrated', '--plan', str(plan), '--engine', str(engine)]
        accepted = subprocess.run(base + ['--allow-authority-staging'], capture_output=True, text=True)
        receipt = json.loads(accepted.stdout) if accepted.returncode == 0 else {}
        check('Dry plan binds the explicit executable without creating capture files',
              accepted.returncode == 0 and receipt.get('engine') == str(engine) and receipt.get('engine_sha256') == module.sha(engine)
              and receipt.get('starts_processes') is False and not (root / 'capture').exists())
        rejected = subprocess.run(base, capture_output=True, text=True)
        check('Authority stages require explicit opt-in before any engine starts', rejected.returncode == 2 and 'explicit --allow-authority-staging' in rejected.stderr)
        rejected = subprocess.run(base[:-1] + [str(root / 'absent-engine'), '--allow-authority-staging'], capture_output=True, text=True)
        check('Missing explicit engine rejects before creating output', rejected.returncode == 2 and not (root / 'capture').exists())
        imports = project / '.godot/imported'
        imports.mkdir(parents=True)
        (imports / 'hero.scn').write_bytes(b'exact imported resource fixture')
        frozen = {'existing_import_sha256': module.imported_files(project)}
        (project / 'ui-source-freeze.json').write_text(json.dumps(frozen))
        pins, receipt_sha = module.qualify_imports(project)
        check('Integrated capture qualifies exact imported resources against its freeze',
              pins == frozen['existing_import_sha256'] and receipt_sha == module.sha(project / 'ui-source-freeze.json'))
        (imports / 'hero.scn').write_bytes(b'replaced resource with unchanged raw source')
        try:
            module.qualify_imports(project)
            rejected = False
        except ValueError:
            rejected = True
        check('Changed imported bytes reject despite unchanged raw project source', rejected)

    tree = ast.parse(DRIVER.read_text())
    files = next(ast.literal_eval(node.value) for node in ast.walk(tree)
                 if isinstance(node, ast.Assign) and isinstance(node.value, ast.List)
                 and any(isinstance(target, ast.Name) and target.id == 'files' for target in node.targets))
    missing = []
    for name in files:
        if not name.endswith('.gd'):
            continue
        text = (PROJECT / name).read_text()
        for dependency in re.findall(r'(?:preload|load)\("res://([^"\n]+\.gd)"\)', text):
            if dependency not in files:
                missing.append({'caller': name, 'dependency': dependency})
    check('Tiny scene fixtures include current production script dependencies', not missing, missing)
    check('Driver source is unchanged during these checks', before == module.sha(DRIVER))
    report = {'passed': all(row['passed'] for row in checks), 'count': len(checks), 'checks': checks,
              'driver_sha256': before, 'test_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
              'scope': 'Python CLI, exact file copy and preload closure only. No engine, renderer, OS input or pixels.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'count': report['count']}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
