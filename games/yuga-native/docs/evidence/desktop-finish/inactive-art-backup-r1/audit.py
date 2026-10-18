#!/usr/bin/env python3
"""Read-only source audit; writes only this allowlist packet. Never stages/deletes."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import subprocess
import tarfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[5]
NATIVE = ROOT / 'games/yuga-native'
ROOTS = [
    'art/hero-finish/hair-silhouette-r1',
    'art/hero-finish/hair-knot-bridge-r5',
    'art/hero-finish/s5-shoulder-armour/compact-r6',
    'art/hero-finish/s5-shoulder-armour/articulated-r5',
    'docs/evidence/desktop-finish/hair-silhouette',
    'docs/evidence/desktop-finish/hair-knot-bridge-r5',
    'docs/evidence/desktop-finish/shoulder-armour/W3-render-preparation-r1',
]
def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()
def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
def rel(path): return path.relative_to(ROOT).as_posix()
def record(path):
    assert path.is_file() and not path.is_symlink(), path
    before = path.stat()
    h = hashlib.sha256()
    blob = hashlib.sha1(f'blob {before.st_size}\0'.encode())
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b); blob.update(b)
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino), path
    return dict(path=rel(path), bytes=before.st_size, sha256=h.hexdigest(), git_blob=blob.hexdigest(), mode=oct(before.st_mode & 0o777))

def main():
    head = git('rev-parse', 'HEAD').decode().strip()
    index = ROOT / '.git/index'
    index_before = sha(index)
    tracked, blobs = {}, collections.defaultdict(list)
    for entry in git('ls-tree', '-rlz', head).split(b'\0'):
        if not entry: continue
        fields, path = entry.split(b'\t', 1)
        mode, kind, oid, size = fields.split()
        if kind != b'blob': continue
        s = path.decode(); tracked[s] = oid.decode(); blobs[oid.decode()].append(s)
    paths = {p for root in ROOTS for p in (NATIVE / root).rglob('*') if p.is_file()}
    pins = []
    def add(path, metadata, receipt, kind):
        expected = metadata if isinstance(metadata, str) else metadata['sha256']
        pins.append(dict(path=rel(path), expected_sha256=expected, receipt=rel(receipt), kind=kind))
        paths.add(path)
    def mapping(receipt, key, base):
        value = json.loads(receipt.read_text())[key]
        if isinstance(value, dict):
            for name, metadata in value.items(): add(base / name, metadata, receipt, key)
        else:
            for item in value: add(base / item['path'], item, receipt, key)
    compact = NATIVE / ROOTS[2] / 'receipt.json'
    mapping(compact, 'files', compact.parent)
    mapping(compact, 'external_inputs', ROOT)
    prep = NATIVE / ROOTS[6] / 'receipt.json'
    mapping(prep, 'files', prep.parent)
    r4 = NATIVE / 'docs/evidence/desktop-finish/hair-silhouette/W2/receipt.json'
    for key, base in [('art_sources', NATIVE), ('dependencies', NATIVE), ('evidence', r4.parent)]: mapping(r4, key, base)
    r5 = NATIVE / 'docs/evidence/desktop-finish/hair-knot-bridge-r5/W2/receipt.json'
    for key in ['artifacts', 'dependencies']: mapping(r5, key, NATIVE)
    for name in ['hair-silhouette', 'hair-knot-bridge-r5']:
        receipt = NATIVE / f'docs/evidence/desktop-finish/{name}/W1-native-r1/receipt.json'
        mapping(receipt, 'artifacts', receipt.parent)
    missing = [rel(p) for p in paths if not p.exists()]
    assert not missing, missing
    inventory = {rel(p): record(p) for p in sorted(paths)}
    for pin in pins:
        pin['actual_sha256'] = inventory[pin['path']]['sha256']
        pin['passed'] = pin['actual_sha256'] == pin['expected_sha256']
    assert all(p['passed'] for p in pins), [p for p in pins if not p['passed']]
    portable = {}
    for row in json.loads(r4.read_text())['portable_raw_inputs']:
        raw, packed = r4.parent / row['raw'], r4.parent / row['gzip']
        h = hashlib.sha256(); size = 0
        with gzip.open(packed, 'rb') as f:
            for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b); size += len(b)
        assert h.hexdigest() == row['raw_sha256'] == inventory[rel(raw)]['sha256']
        assert size == row['raw_bytes'] == inventory[rel(raw)]['bytes']
        assert inventory[rel(packed)]['sha256'] == row['gzip_sha256']
        portable[rel(raw)] = dict(kind='gzip_exact_raw', source=rel(packed), raw_sha256=h.hexdigest(), raw_bytes=size)
    archives = []
    for path, row in list(inventory.items()):
        if not path.endswith('.tar.gz'): continue
        with tarfile.open(ROOT / path) as t:
            members = t.getmembers()
            assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
            entry = dict(path=path, sha256=row['sha256'], members=len(members), expanded_bytes=sum(m.size for m in members), cache_members=[m.name for m in members if '.godot' in Path(m.name).parts])
            entry['import_descriptors'] = []
            for m in members:
                if m.name.endswith('.import'):
                    data = t.extractfile(m).read(); target = NATIVE / m.name
                    assert target.read_bytes() == data
                    b = record(target); inventory.setdefault(rel(target), b)
                    entry['import_descriptors'].append(dict(member=m.name, recover_from=rel(target), sha256=b['sha256'], git_blob=b['git_blob']))
            archives.append(entry)
    actions, selected, selected_hash = {}, [], {}
    for path in sorted(inventory):
        row = inventory[path]; parts = Path(path).parts
        if any(x in ['.godot', '__pycache__'] or x.startswith('xdg-') for x in parts) or path.endswith('.pyc') or 'candidate-import-cache-' in path:
            action = dict(kind='excluded_generated_cache', reason='Deliberately not included in Git backup; not a deletion instruction.')
        elif path in portable: action = portable[path]
        elif row['git_blob'] in blobs:
            same = tracked.get(path) == row['git_blob']
            origin = path if same else sorted(blobs[row['git_blob']], key=lambda s: (s.count('/'), s))[0]
            action = dict(kind='already_in_head' if same else 'recover_from_head_blob', commit=head, source=origin, git_blob=row['git_blob'])
        elif row['sha256'] in selected_hash:
            action = dict(kind='recover_from_selected_file', source=selected_hash[row['sha256']])
        else:
            action = dict(kind='include_new_file'); selected.append(row); selected_hash[row['sha256']] = path
        actions[path] = action
    # This branch adds descriptor records above; every one must already be committed.
    assert all(tracked.get(d['recover_from']) == d['git_blob'] for a in archives for d in a['import_descriptors'])
    # All tmp preparation scripts/receipts pinned by R5 are archived byte-for-byte.
    r5prep = NATIVE / 'docs/evidence/desktop-finish/hair-knot-bridge-r5/W2-capture-preparation-r1.json'
    bysha = collections.defaultdict(list)
    for path, row in inventory.items(): bysha[row['sha256']].append(path)
    tmp_closure = []
    for row in json.loads(r5prep.read_text())['prepared_files']:
        matches = bysha[row['sha256']]
        tmp_closure.append(dict(original=row['path'], sha256=row['sha256'], archived_paths=matches, passed=bool(matches)))
    assert all(row['passed'] for row in tmp_closure)
    counts = collections.Counter(a['kind'] for a in actions.values())
    sums = {k: sum(inventory[p]['bytes'] for p, a in actions.items() if a['kind'] == k) for k in counts}
    groups = []
    for root in ROOTS:
        prefix = 'games/yuga-native/' + root + '/'
        rows = [row for row in selected if row['path'].startswith(prefix)]
        groups.append(dict(root=prefix[:-1], include_count=len(rows), include_bytes=sum(x['bytes'] for x in rows)))
    assert git('rev-parse', 'HEAD').decode().strip() == head
    assert sha(index) == index_before
    summary = dict(schema=1, head=head, index_sha256=index_before, head_and_index_unchanged=True,
        status='PREPARED_ONLY_NO_STAGING_DELETION_OR_SOURCE_CHANGES',
        approved_roots=ROOTS, active_r6_excluded=True, receipt_pin_checks=len(pins), receipt_pin_failures=0,
        inventory_count=len(inventory), inventory_bytes=sum(x['bytes'] for x in inventory.values()),
        include_count=len(selected), include_bytes=sum(x['bytes'] for x in selected),
        action_counts=counts, action_bytes=sums, groups=groups,
        over_95_MiB=[r for r in selected if r['bytes'] > 95*1024*1024], missing_pinned_files=missing,
        tmp_preparation_pins_archived=len(tmp_closure),
        largest_included=sorted(selected,key=lambda r:r['bytes'],reverse=True)[:10])
    write('summary.json', summary)
    write('allowlist.json', dict(schema=1, base_commit=head, files=selected))
    (OUT/'allowlist.paths').write_text(''.join(row['path']+'\n' for row in selected))
    (OUT/'allowlist.paths0').write_bytes(b''.join(row['path'].encode()+b'\0' for row in selected))
    write('inventory-and-recovery.json', dict(schema=1, base_commit=head, files=[{**row,'backup':actions[path]} for path,row in inventory.items()]))
    write('receipt-closure.json', dict(pins=pins, portable_raw=portable, external_tmp_pins=tmp_closure, archives=archives))
    print(json.dumps({k:summary[k] for k in ['head','receipt_pin_checks','inventory_count','include_count','include_bytes','action_counts','action_bytes','over_95_MiB','missing_pinned_files']},indent=2))

if __name__ == '__main__': main()
