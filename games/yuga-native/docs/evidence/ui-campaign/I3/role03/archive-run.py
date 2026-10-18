#!/usr/bin/env python3
"""Copy complete raw UI capture evidence; no image editing or resampling."""
import argparse,hashlib,json,pathlib,shutil,html
P=pathlib.Path
p=argparse.ArgumentParser();p.add_argument('--source',type=P,required=True);p.add_argument('--output',type=P,required=True);a=p.parse_args()
if a.output.exists():raise SystemExit('Use a fresh archive directory')
a.output.mkdir(parents=True)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
manifest={}
for f in sorted(a.source.iterdir()):
 if not f.is_file() or f.suffix not in ['.png','.json','.log','.txt','.gd','.py']:continue
 out=a.output/(f.stem+'-output.txt' if f.suffix=='.log' else f.name);shutil.copy2(f,out);assert sha(f)==sha(out);manifest[out.name]=sha(out)
 if f.suffix=='.log':
  original=a.output/f.name;shutil.copy2(f,original);assert sha(f)==sha(original);manifest[original.name]=sha(original)
r=json.loads((a.output/'run.json').read_text())
shots=r.get('shots',[])+r.get('automatic_shots',[])
for shot in shots:assert sha(a.output/shot['file'])==shot['sha256']
sections=['<!doctype html><meta charset="utf-8"><title>'+html.escape(a.output.name)+'</title><style>body{background:#111827;color:#f6f2e7;font:17px sans-serif;margin:24px}img{max-width:100%;height:auto;border:1px solid #64748b}a{color:#eed095}figure{margin:32px 0}small{display:block;margin:8px 0}</style><h1>'+html.escape(a.output.name)+'</h1><p>Untouched framebuffer originals. Native window 960×600; integrated framebuffer 960×540. Read each JSON for actual phase, state and fixture scope.</p>']
for shot in shots:
 filename=shot['file'];stage=shot.get('authority_staging',{}).get('last_action','');note='STAGED AUTHORITY / simulation hold: '+stage if stage not in ['', 'release'] else 'Native navigation / observed loading phase.'
 sections.append('<figure><figcaption><a href="'+filename+'">'+filename+'</a> · <a href="'+P(filename).stem+'.json">state</a></figcaption><small>'+html.escape(note)+'</small><img src="'+filename+'"></figure>')
(a.output/'index.html').write_text('\n'.join(sections))
(a.output/'archive-receipt.json').write_text(json.dumps({'source':str(a.source),'files_sha256':manifest,'manual_originals':len(r.get('shots',[])),'automatic_originals':len(r.get('automatic_shots',[])),'scope':'Byte-identical raw originals; gallery uses CSS sizing only.'},indent=2)+'\n')
print(json.dumps({'output':str(a.output),'manuals':len(r.get('shots',[])),'automatic':len(r.get('automatic_shots',[])),'files':len(manifest)}))
