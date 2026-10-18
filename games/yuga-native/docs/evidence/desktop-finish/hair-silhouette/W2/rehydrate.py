"""Restore exact large JSON working inputs from portable gzip artifacts."""
from pathlib import Path
import gzip,hashlib,json
root=Path(__file__).resolve().parent
for row in json.loads((root/'portable-artifacts.json').read_text())['artifacts']:
 packed=(root/row['gzip']).read_bytes();assert hashlib.sha256(packed).hexdigest()==row['gzip_sha256']
 raw=gzip.decompress(packed);assert len(raw)==row['raw_bytes'] and hashlib.sha256(raw).hexdigest()==row['raw_sha256']
 path=root/row['raw']
 if path.exists():assert path.read_bytes()==raw
 else:path.write_bytes(raw)
 print(row['raw'],'exact')
