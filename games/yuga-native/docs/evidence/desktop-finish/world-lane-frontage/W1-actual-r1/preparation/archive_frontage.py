from pathlib import Path
import hashlib,json,gzip,shutil
WORK=Path(__file__).parent
DEST=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/world-lane-frontage/W1-actual-r1')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not DEST.exists(), 'fresh archive required'
 for branch in ('baseline','candidate'):
  report=json.loads((WORK/(branch+'-originals-r1/capture.json')).read_text())
  run=json.loads((WORK/(branch+'-originals-r1-logs/run.json')).read_text())
  assert report['complete'] and not report['failure']
  assert len(list((WORK/(branch+'-originals-r1')).glob('*.png')))==3
 assert json.loads((WORK/'actual-comparison-r1.json').read_text())['passed']
 DEST.mkdir(parents=True)
 files={};mapping=[]
 def copy(source,relative):
  source=Path(source);target=DEST/relative;data=source.read_bytes();compressed=len(data)>1000000 and source.suffix in ('.json','.log')
  if compressed:target=target.with_name(target.name+'.gz')
  target.parent.mkdir(parents=True,exist_ok=True)
  if compressed:target.write_bytes(gzip.compress(data,compresslevel=9,mtime=0));assert gzip.decompress(target.read_bytes())==data
  else:target.write_bytes(data)
  key=str(target.relative_to(DEST));files[key]={'bytes':target.stat().st_size,'sha256':h(target)}
  mapping.append({'source':str(source),'source_bytes':len(data),'source_sha256':hashlib.sha256(data).hexdigest(),'artifact':key,'encoding':'gzip-lossless' if compressed else 'original'})
 for source in sorted(WORK.iterdir()):
  if source.is_file() and source.suffix in ('.py','.json','.log','.md'):copy(source,'preparation/'+source.name)
 for source in sorted((WORK/'harness').rglob('*')):
  if source.is_file() and '__pycache__' not in str(source):copy(source,'harness/'+str(source.relative_to(WORK/'harness')))
 for n in ('yuga-frontage-helper-r1','yuga-frontage-helper-r2'):
  base=Path('/workspace/scratch')/n
  for source in sorted(base.rglob('*')):
   if source.is_file() and '__pycache__' not in str(source):copy(source,'preserved-helper-inputs/'+n+'/'+str(source.relative_to(base)))
 for phase in ('baseline-preflight-r1','baseline-preflight-r2','baseline-preflight-r3','baseline-preflight-r4','candidate-preflight-r4','baseline-originals-r1','candidate-originals-r1'):
  base=WORK/phase
  if base.exists():
   for source in sorted(base.iterdir()):
    if source.is_file():copy(source,'runs/'+phase+'/'+source.name)
  for name in ('godot.log','xvfb.log','run.json'):
   source=WORK/(phase+'-logs')/name
   if source.exists():copy(source,'runs/'+phase+'/logs/'+name)
 for branch in ('baseline','candidate'):
  for suffix in ('','-r2','-r3','-r4'):
   source=WORK/(branch+suffix)/'.graphics-six-snapshot.json'
   if source.exists():copy(source,'source-markers/'+branch+suffix+'.json')
 (DEST/'artifact-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
 print(json.dumps({'archive':str(DEST),'files':len(files),'bytes':sum(v['bytes'] for v in files.values())}))
if __name__=='__main__':main()
