"""Run existing motion suites against an isolated source without runtime edits."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]
SUITES=['rama_motion_cases.gd','rama_motion_polish_cases.gd','rama_motion_adversarial_cases.gd']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--motion-source',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--godot',default='godot');a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
 if not a.motion_source.startswith('res://'):raise ValueError('Use explicit isolated res:// motion source')
 candidate=PROJECT/a.motion_source.removeprefix('res://');start_sha=sha(candidate);rows=[];started=time.monotonic()
 for name in SUITES:
  source=PROJECT/'tests'/name;text=source.read_text();needle='res://scripts/rama_motion.gd';assert needle in text
  wrapper=a.output/name;wrapper.write_text(text.replace(needle,a.motion_source));report=a.output/(source.stem+'.json');log=a.output/(source.stem+'.log')
  command=[a.godot,'--headless','--path',str(PROJECT),'--script',str(wrapper),'--','--report='+str(report)]
  begin=time.monotonic()
  with log.open('w') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=90)
  data=json.loads(report.read_text()) if report.exists() else {};checks=data.get('checks',[]);passed=result.returncode==0 and bool(data.get('passed')) and bool(checks) and all(c['passed'] for c in checks)
  rows.append({'suite':name,'source_sha256':sha(source),'wrapper_sha256':sha(wrapper),'command':command,'exit_code':result.returncode,'checks':len(checks),'passed':passed,'report':str(report),'report_sha256':sha(report) if report.exists() else None,'seconds':time.monotonic()-begin})
  print('MOTION_EXISTING_SUITE',name,'PASS' if passed else 'FAIL',len(checks),flush=True)
 report={'schema_version':1,'scope':'Existing actual-rig motion suites with only explicit controller source redirected; canonical tests/assets unchanged.','motion_source':a.motion_source,'motion_sha256':start_sha,'motion_unchanged':start_sha==sha(candidate),'runner_sha256':sha(__file__),'suites':rows,'passed':all(r['passed'] for r in rows) and start_sha==sha(candidate),'elapsed_seconds':time.monotonic()-started}
 (a.output/'regressions.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
