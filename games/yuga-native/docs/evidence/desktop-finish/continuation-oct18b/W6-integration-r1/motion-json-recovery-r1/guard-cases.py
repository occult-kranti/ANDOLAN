"""Finite synthetic counterexamples; never unlinks the real candidate."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

PACKET = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('single_json_guard', PACKET / 'motion-json.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
rows = []

def reject(name, fn):
    try:
        fn()
    except (ValueError, OSError, EOFError):
        rows.append({'name': name, 'passed': True})
    else:
        raise AssertionError(name + ' unexpectedly accepted')

with tempfile.TemporaryDirectory(prefix='w6-json-negative-', dir='/workspace/scratch') as directory:
    p = Path(directory)
    data = b'finite recovery witness\n' * 200
    raw, packed = p/'raw', p/'packed.gz'
    raw.write_bytes(data)
    packed.write_bytes(gzip.compress(data, mtime=0))
    expected = hashlib.sha256(data).hexdigest()
    assert g.roundtrip(raw, packed, len(data), expected)['byte_exact']
    rows.append({'name': 'Exact regular gzip roundtrip positive', 'passed': True})
    link = p/'symlink'; link.symlink_to(raw)
    reject('Raw symlink', lambda:g.regular(link))
    parent = p/'parent-link';parent.symlink_to(p, target_is_directory=True)
    reject('Symlink ancestor', lambda:g.regular(parent/'raw'))
    reject('Directory instead of regular file', lambda:g.regular(p))
    reject('Missing recovery file', lambda:g.regular(p/'absent'))
    hard = p/'hardlink';hard.hardlink_to(raw)
    reject('Hardlink alias on original', lambda:g.regular(raw))
    reject('Hardlink alias on duplicate', lambda:g.regular(hard))
    hard.unlink()
    reject('Wrong decoded size', lambda:g.roundtrip(raw,packed,len(data)-1,expected))
    reject('Wrong decoded hash', lambda:g.roundtrip(raw,packed,len(data),'0'*64))
    wrong=p/'wrong.gz';wrong.write_bytes(gzip.compress(b'X'+data[1:],mtime=0))
    reject('Same-sized wrong decoded bytes', lambda:g.roundtrip(raw,wrong,len(data),expected))
    truncated=p/'truncated.gz';truncated.write_bytes(packed.read_bytes()[:-6])
    reject('Truncated gzip footer', lambda:g.roundtrip(raw,truncated,len(data),expected))
    crc=p/'crc.gz';bad=bytearray(packed.read_bytes());bad[-8]^=1;crc.write_bytes(bad)
    reject('Corrupted gzip CRC', lambda:g.roundtrip(raw,crc,len(data),expected))
    extra=p/'extra.gz';extra.write_bytes(packed.read_bytes()+gzip.compress(b'overflow',mtime=0))
    reject('Extra concatenated decoded member', lambda:g.roundtrip(raw,extra,len(data),expected))
    ident=g.identity(raw)
    for field in ['dev','ino','nlink','mode','bytes','mtime_ns','ctime_ns','sha256']:
        changed=copy.deepcopy(ident)
        changed[field]=str(changed[field])+'x' if isinstance(changed[field],str) else changed[field]+1
        reject('Identity '+field+' drift',lambda c=changed:g.validate_identity(ident,c))
    m=json.loads((PACKET/'recovery-map.json').read_text())
    for key,field,value in [('target','path',str(g.TARGET)+'.other'),('recovery','path',str(g.RECOVERY)+'.other'),('owner_receipt','path',str(g.OWNER)+'.other'),('target','sha256','0'*64),('recovery','sha256','0'*64),('owner_receipt','sha256','0'*64)]:
        changed=copy.deepcopy(m);changed[key][field]=value
        reject('Fixed '+key+' '+field+' substitution',lambda c=changed:g.audit(c))
g.write_new(PACKET/'guard-cases.json',{'passed':all(x['passed'] for x in rows),'count':len(rows),'checks':rows,'scope':'Synthetic tiny files and map substitutions only; no real target removal, network or engine.'})
print(json.dumps({'passed': True,'count':len(rows)}))
