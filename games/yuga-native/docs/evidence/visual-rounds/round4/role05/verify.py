from pathlib import Path
import hashlib,json,zipfile
p=Path(__file__).resolve().parent
manifest=json.loads((p/'archive-manifest.json').read_text()); archive=p/'motion-continuity-study.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256']
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(manifest['members'])
 for name,expected in manifest['members'].items():assert hashlib.sha256(z.read(name)).hexdigest()==expected,name
for name in ['rama_motion.baseline.gd','rama_motion.release-r3a.gd','rama_motion.release-r4.gd','probe-continuity.gd','probe-events.gd']:
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==manifest['members'][name],name
print(f"Verified {len(manifest['members'])} archive members and5 staged files; candidates remain rejected.")
