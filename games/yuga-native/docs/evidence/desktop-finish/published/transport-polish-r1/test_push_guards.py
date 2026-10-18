#!/usr/bin/env python3
"""Local receipt/tree counterexamples; all subprocess/network execution forbidden."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('transport_push', ROOT / 'push.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
base = json.loads((ROOT / 'preparation-receipt.json').read_text())
base.update(orphan=True, transport_commit='a'*40, transport_tree='b'*40)
tests = json.loads((ROOT / 'guard-tests.json').read_text())
entries = p.expected_entries()
checks = []


def run(receipt=None, mode=None, bad_tests=None, bad_snapshot=None):
    receipt = copy.deepcopy(base if receipt is None else receipt)
    calls = []
    def fake_git(*args):
        calls.append(args)
        if args == ('cat-file', '-t', 'a'*40):
            return b'blob\n' if mode == 'wrong_object_type' else b'commit\n'
        if args == ('cat-file', '-p', 'a'*40):
            parent = 'parent ' + 'c'*40 + '\n' if mode == 'parent' else ''
            return ('tree ' + 'b'*40 + '\n' + parent + 'author fixture\ncommitter fixture\n\nfixture\n').encode()
        if args == ('ls-tree', '-r', 'b'*40):
            rows = [f'100644 blob {oid}\t{name}' for name,oid in sorted(entries.items())]
            if mode == 'wrong_tree':
                rows[-1] = '100644 blob ' + '0'*40 + '\tunexpected-file'
            return ('\n'.join(rows)+'\n').encode()
        raise AssertionError('Unexpected Git call: ' + repr(args))
    def forbidden(*args, **kwargs):
        raise AssertionError('No subprocess/network operation permitted')
    with patch.object(p.subprocess, 'run', forbidden), patch.object(p.subprocess, 'Popen', forbidden), patch.object(p.subprocess, 'check_output', forbidden):
        result = p.validate_local(receipt, tests if bad_tests is None else bad_tests,
                                  git=fake_git, snapshot=lambda: base['checkout_before'] if bad_snapshot is None else bad_snapshot)
    return result, calls


def check(name, operation, reject=False):
    try:
        operation()
    except ValueError:
        if not reject:
            raise
    else:
        if reject:
            raise AssertionError('Invalid receipt accepted: ' + name)
    checks.append({'name':name,'passed':True})

check('exact prepared parentless tree accepts only fixed branch', lambda: p.require(run()[0] == 'refs/heads/'+p.g.BRANCH, 'fixed output branch'))
for key,value,label in [('transport_branch','transport/unapproved-receipt-branch','changed branch'),('source_commit','0'*40,'changed source')]:
    changed=copy.deepcopy(base); changed[key]=value
    check(label+' rejected before remote/ref operation', lambda changed=changed:run(changed), True)
check('noncommit Git object rejected', lambda:run(mode='wrong_object_type'), True)
check('unexpected tree payload rejected', lambda:run(mode='wrong_tree'), True)
check('parent-bearing commit rejected', lambda:run(mode='parent'), True)
changed=copy.deepcopy(base); changed['entries'][next(iter(changed['entries']))]='0'*40
check('receipt entry drift rejected', lambda:run(changed), True)
def changed_source_pins():
    for key in ['generator_sha256','uploader_sha256','workflow_sha256','manifest_sha256']:
        changed=copy.deepcopy(base); changed[key]='0'*64
        try: run(changed)
        except ValueError: pass
        else: raise AssertionError('Source pin drift accepted: '+key)
check('generator/uploader/workflow/manifest pin drift rejected', changed_source_pins)
bad_tests=copy.deepcopy(tests); bad_tests['test_sha256']='0'*64
check('stale guard execution identity rejected', lambda:run(bad_tests=bad_tests), True)
changed=copy.deepcopy(base['checkout_before']); changed['index_sha256']='0'*64
check('normal checkout/index drift rejected', lambda:run(bad_snapshot=changed), True)
receipt={'checks':checks,'passed':len(checks),'failed':0,'scope':'Mocked local pre-network gate; no Git objects/refs/index or API operations','push_sha256':hashlib.sha256((ROOT/'push.py').read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'subprocess_operations':0,'network_operations':0}
(ROOT/'push-guard-tests.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'passed':len(checks),'failed':0,'subprocess_operations':0,'network_operations':0}))
