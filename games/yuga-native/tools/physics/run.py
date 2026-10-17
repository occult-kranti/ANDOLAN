#!/usr/bin/env python3
"""Reproduce the bounded 3D authority experiment without imports/rendering."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--godot',default='godot');a=p.parse_args()
repo=Path(__file__).resolve().parents[4];native=repo/'games/yuga-native';output=a.output.resolve()
if output.exists():raise SystemExit('Use a fresh output directory; earlier evidence is preserved.')
output.mkdir(parents=True)
fixture=native/'assets/contracts/physics-fixture-v1.json';ts=native/'tools/physics/reference.ts';gd=native/'tests/physics_authority_cases.gd'
commands=[
 ['node','--experimental-strip-types','--test',str(ts.with_name('reference.test.ts'))],
 [str(repo/'node_modules/.bin/tsc'),'--noEmit','--target','ES2022','--module','NodeNext','--moduleResolution','NodeNext','--allowImportingTsExtensions','--strict','--skipLibCheck',str(ts),str(ts.with_name('reference.test.ts'))],
 ['node','--experimental-strip-types',str(ts),str(fixture),str(output/'typescript.json')],
 [a.godot,'--headless','--path',str(native),'--script','res://tests/physics_authority_cases.gd','--','--report='+str(output/'godot.json')],
 ['python3',str(ts.with_name('compare.py')),'--fixture',str(fixture),'--typescript',str(output/'typescript.json'),'--godot',str(output/'godot.json'),'--report',str(output/'comparison.json')],
]
receipt={'format':1,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'uncommitted_sources':True,'sources':{},'commands':[],'passed':False}
for path in [fixture,ts,gd,ts.with_name('reference.test.ts'),ts.with_name('compare.py'),Path(__file__).resolve()]:receipt['sources'][str(path.relative_to(repo))]=hashlib.sha256(path.read_bytes()).hexdigest()
for index,cmd in enumerate(commands):
 log=output/f'{index+1:02d}.log';env=dict(os.environ);env['XDG_DATA_HOME']=str(output/'user');env['XDG_CONFIG_HOME']=str(output/'config')
 with log.open('w') as f:
  try:result=subprocess.run(cmd,cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=90);code=result.returncode
  except subprocess.TimeoutExpired:code=124
  except OSError as error:f.write(str(error));code=127
 receipt['commands'].append({'argv':cmd,'exit_code':code,'log':log.name})
 (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 if code:raise SystemExit(f'Check {index+1} failed ({code}); see {log}')
receipt['passed']=True;(output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'passed':True,'receipt':str(output/'receipt.json')}))
