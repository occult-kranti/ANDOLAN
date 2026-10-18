#!/usr/bin/env python3
"""Preserve an R4 original take with exact source, import and harness receipts."""
import argparse,hashlib,json,shutil
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 d=json.loads((a.capture/'capture.json').read_text());r=json.loads((a.capture/'run.json').read_text());assert d['complete'] and d['source_unchanged'] and r['complete'];assert sha(a.capture/'capture.json')==r['report_sha256']
 for shot in d['shots']:assert sha(a.capture/shot['file'])==shot['sha256']
 for path,h in d['source_sha256'].items():assert sha(a.project/path.removeprefix('res://'))==h,path
 for suffix,key in [('.godot.log','godot_log_sha256'),('.xvfb.log','xvfb_log_sha256')]:assert sha(a.capture.with_suffix(suffix))==r[key]
 shutil.copytree(a.capture,a.output)
 for suffix in ['.godot.log','.xvfb.log']:shutil.copy2(a.capture.with_suffix(suffix),a.output/('producer'+suffix))
 shutil.copy2(a.project/'motion-freeze.json',a.output/'motion-freeze.json')
 for path in d['source_sha256']:
  if path.startswith('res://tools/'):
   relative=Path(path.removeprefix('res://tools/'))
   archive_relative=Path(path.removeprefix('res://tools/visual-rounds/')) if path.startswith('res://tools/visual-rounds/') else Path('shared')/relative
   dest=a.output/'harness'/archive_relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a.project/'tools'/relative,dest)
 print(json.dumps({'complete':True,'raw_pngs':len(d['shots']),'archive':str(a.output)}))
if __name__=='__main__':main()
