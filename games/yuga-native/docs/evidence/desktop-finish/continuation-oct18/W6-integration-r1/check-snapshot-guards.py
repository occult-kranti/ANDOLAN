#!/usr/bin/env python3
"""Bounded corruption/isolation checks; no application checkout or exporter."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('snapshot', HERE / 'prepare-package-snapshot.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checks = []
def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)
def rejects(name, fn):
    try:
        fn()
    except ValueError:
        check(name, True)
    else:
        check(name, False)
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)
def main():
    area = m.AREA / 'snapshot-guard-fixture-r1'
    area.mkdir()
    source, target = area / 'source', area / 'copy'
    source.mkdir(); target.mkdir()
    git(source, 'init', '-q')
    samples = {'games/yuga-native/scripts/sample.gd': 'extends Node\n',
               'games/yuga-native/scripts/sample.gd.uid': 'uid://abc\n',
               'games/yuga-native/tests/sample.gd': 'extends SceneTree\n',
               'games/yuga-native/assets/sample.png': 'immutable fixture bytes\n'}
    for name, text in samples.items():
        p = source / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    git(source, 'add', '.')
    git(source, '-c', 'user.name=Snapshot fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Synthetic guard fixture')
    commit = git(source, 'rev-parse', 'HEAD').decode().strip()
    entries = m.tracked(source, commit)
    m.audit(source, entries); m.audit_index(source, entries)
    check('full exact tracked source and index accepted', len(entries) == len(samples))
    check('runtime script private', m.private(Path('games/yuga-native/scripts/sample.gd')))
    check('test script private', m.private(Path('games/yuga-native/tests/sample.gd')))
    check('all UID metadata private', m.private(Path('historical/x.gd.uid')))
    check('all import metadata private', m.private(Path('historical/x.png.import')))
    check('immutable raw input eligible for frozen hardlink', not m.private(Path('games/yuga-native/assets/sample.png')))
    for row in entries:
        p, q = source / row['path'], target / row['path']; q.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copy2 if row['private'] else os.link)(p, q)
    m.audit_isolation(source, target, entries)
    check('private mutable inputs and linked immutable inputs accepted', True)
    script = source / 'games/yuga-native/scripts/sample.gd'
    copied_script = target / 'games/yuga-native/scripts/sample.gd'
    copied_script.unlink(); os.link(script, copied_script)
    rejects('shared mutable script inode rejected', lambda: m.audit_isolation(source, target, entries))
    copied_script.unlink(); shutil.copy2(script, copied_script)
    copied_script.write_text('corrupted\n')
    rejects('artifact payload corruption rejected', lambda: m.audit(target, entries))
    shutil.copy2(script, copied_script)
    script.write_text('canonical changed\n')
    rejects('canonical source drift rejected', lambda: m.audit(source, entries))
    rejects('snapshot refuses mismatched commit blob', lambda: m.tracked(source, commit))
    script.write_text(samples['games/yuga-native/scripts/sample.gd'])
    git(source, 'update-index', '--assume-unchanged', 'games/yuga-native/scripts/sample.gd')
    rejects('assume-unchanged index flag rejected', lambda: m.audit_index(source, entries))
    git(source, 'update-index', '--no-assume-unchanged', 'games/yuga-native/scripts/sample.gd')
    git(source, 'update-index', '--skip-worktree', 'games/yuga-native/scripts/sample.gd')
    rejects('sparse or skip-worktree index flag rejected', lambda: m.audit_index(source, entries))
    git(source, 'update-index', '--no-skip-worktree', 'games/yuga-native/scripts/sample.gd')
    git(source, 'update-index', '--force-remove', 'games/yuga-native/scripts/sample.gd')
    rejects('missing tracked index member rejected', lambda: m.audit_index(source, entries))
    git(source, 'read-tree', commit)
    copied_script.unlink(); copied_script.symlink_to(script)
    rejects('symlink source substitution rejected', lambda: m.hashes(copied_script))
    copied_script.unlink(); shutil.copy2(script, copied_script)
    cache = source / '.godot'; cache.mkdir(); (cache / 'fixture.bin').write_bytes(b'cache-seed')
    before = m.cache_records(cache); shutil.copytree(cache, target / '.godot')
    check('cache byte and mode snapshot copied exactly', before == m.cache_records(target / '.godot'))
    a, b = cache / 'fixture.bin', target / '.godot/fixture.bin'
    check('cache copy inode is private', (a.stat().st_dev, a.stat().st_ino) != (b.stat().st_dev, b.stat().st_ino))
    (target / '.godot/fixture.bin').write_bytes(b'private mutation')
    check('artifact cache mutation preserves canonical seed', m.cache_records(cache) == before)
    (cache / 'unsafe-link').symlink_to(script)
    rejects('cache symlink rejected', lambda: m.cache_records(cache))
    for label, arguments in [('source freeze mismatch', ['--commit', '0' * 40]),
                             ('reserve below approved minimum', ['--commit', '0' * 40, '--reserve-mib', '127']),
                             ('unsafe artifact traversal', ['--commit', '0' * 40, '--artifact-name', '../escape'])]:
        result = subprocess.run([sys.executable, str(HERE / 'prepare-package-snapshot.py'), *arguments,
                                 '--report', str(m.AREA / 'not-created.json')], capture_output=True, text=True)
        check(label + ' rejected before materialization', result.returncode != 0 and not (m.AREA / 'not-created.json').exists())
    check('approved exact exclusion bytes match pinned hash', hashlib.sha256(m.APPROVED_EXCLUDE.read_bytes()).hexdigest() == m.APPROVED_EXCLUDE_SHA256)
    report = {'passed': all(c['passed'] for c in checks), 'count': len(checks), 'checks': checks,
              'scope': 'Synthetic source, index, inode and corruption checks only; no production artifact checkout/export/import or package execution.',
              'fixture': str(area), 'scripts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE / 'prepare-package-snapshot.py', HERE / 'run-package-phase.py']}}
    m.dump_new(HERE / 'snapshot-guard-checks.json', report)
    print(json.dumps({'passed': report['passed'], 'count': len(checks), 'report': str(HERE / 'snapshot-guard-checks.json')}))
if __name__ == '__main__':
    main()
