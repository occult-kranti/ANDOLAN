from pathlib import Path
import json,hashlib
R=Path('/workspace/ANDOLAN');N=R/'games/yuga-native';O=Path(__file__).parent
spec=[
('production_actual','games/yuga-native/docs/evidence/desktop-finish/world-lane-frontage/W1-production-actual-r1/receipt.json','9709d45636e83c9ef29dfdc86d4721d0ac300d10de8b79024ae565083d50ee52'),
('motion_independent','games/yuga-native/docs/evidence/desktop-finish/next-motion/W1-locomotion-sampled-review-r1/receipt.json','665080f142542abc2450e1b3f16e3795b7fe051c335c6630cd8ce26f44c49726'),
('clay_c3_actual','games/yuga-native/docs/evidence/desktop-finish/hair-volume-r3/W1-actual-r1/receipt.json','9bb1021c905d35d0ed99202f61eee438d049ec661ccc05faceff53148c832edb'),
('clay_c3_validation','games/yuga-native/docs/evidence/desktop-finish/hair-volume-r3/W2-validation/receipt.json','66a52a7241620a3224a880e8c51cb53c5fbcfd16d86730ee18acdd441e245b65'),
('clay_c3_visual','games/yuga-native/docs/evidence/desktop-finish/hair-volume-r3/W2-visual-r1/receipt.json','5b7251e3868028587fd852bda518f9fe5831ec28909bf192eacd6a1f1e8ef02c'),
('clay_c3_source','games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r3/source-receipt.json','5c0ffe5d6967d73843c59ca18e73c065a1d9313dbf37aa2dc7f80435c6f570d5'),
('public_zip_cleanup_preparation','docs/evidence/desktop-finish-r4-public-zip-cleanup-r1/receipt.json','543efadd50b423362e745ede1bffa55ae4a746e139e9bde183d9d74ac170c4ec'),
('public_zip_cleanup_execution','docs/evidence/desktop-finish-r4-public-zip-cleanup-r1/execution-receipt.json',None),
('runtime_ci_failure','games/yuga-native/docs/evidence/desktop-finish/checkpoint-0964564-ci/root/receipt.json',None),
]
s=json.loads((O/'scope.json').read_text());files=set(s['files']);owners={x['name']:x for x in s['owner_sealed_packets']}
for label,rel,expected in spec:
 p=R/rel;h=hashlib.sha256(p.read_bytes()).hexdigest()
 if expected: assert h==expected,(rel,h)
 doc=json.loads(p.read_text()); files.add(rel)
 for k in ('artifacts','files'):
  table=doc.get(k);entries=table.items() if isinstance(table,dict) else [(x.get('path'),x) for x in table] if isinstance(table,list) else []
  for name,pin in entries:
   if isinstance(pin,str):pin={'sha256':pin}
   assert isinstance(name,str) and isinstance(pin,dict),(rel,name,pin)
   q=Path(name); candidates=[q] if q.is_absolute() else [p.parent/q,N/q,R/q]
   target=next((x for x in candidates if x.is_file() and not x.is_symlink()),None)
   assert target and target.is_relative_to(R),(rel,name)
   assert hashlib.sha256(target.read_bytes()).hexdigest()==pin['sha256'],target
   if 'bytes' in pin:assert target.stat().st_size==pin['bytes'],target
   files.add(str(target.relative_to(R)))
 owners[label]=dict(name=label,receipt=rel,sha256=h)
s['files']=sorted(files);s['owner_sealed_packets']=list(owners.values());s['status']='SEALED_OWNER_CUTOFF_C3_AND_PRODUCTION_MOTION_COMPLETE_ROOT_DOCS_AND_ACTIVE_SUCCESSORS_EXCLUDED'
s['exclusions_note']='Root evolving docs, C4, active CI repair and private motion successor are excluded. No new workspace discovery, staging or deletion.'
(O/'scope.json').write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps(dict(scope_files=len(files),owners=len(owners),new_packets=[owners[x[0]] for x in spec]),indent=2))
