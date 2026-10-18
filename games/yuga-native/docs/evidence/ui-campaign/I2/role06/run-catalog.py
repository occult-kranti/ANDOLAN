import hashlib,json,os,pathlib,subprocess,time
project=pathlib.Path('/tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native')
output=pathlib.Path('/tmp/yuga-i2-independent-screen-catalog-r1')
receipt=pathlib.Path('/tmp/yuga-i2-independent-screen-catalog-r1-receipt.json')
manifest_path=project/'ui-source-freeze.json';manifest=json.loads(manifest_path.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 return {kind:[name for name,h in manifest[kind].items() if not(project/name).is_file() or sha(project/name)!=h] for kind in ['source_sha256','existing_import_sha256']}
manifest_hash=sha(manifest_path)
assert manifest_hash=='9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088',manifest_hash
assert not output.exists(),'fresh output required'
before=verify();assert not any(before.values()),before
command=['taskset','-c','2','python3',str(project/'tools/run-visual-checks.py'),'--catalog','screens','--max-cpus','1','--timeout','120','--output',str(output)]
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',LP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
started=time.monotonic()
with open(str(output)+'-stdout.txt','w') as out,open(str(output)+'-stderr.txt','w') as err:
 result=subprocess.run(command,env=env,stdout=out,stderr=err,timeout=1800,check=False)
after=verify();summary=json.loads((output/'summary.json').read_text())
report={'passed':result.returncode==0 and summary.get('passed') is True and not any(after.values()),'command':command,'exit_code':result.returncode,'elapsed_wall_seconds':time.monotonic()-started,'manifest_sha256':manifest_hash,'source_files':len(manifest['source_sha256']),'cache_files':len(manifest['existing_import_sha256']),'before_mismatches':before,'after_mismatches':after,'summary_sha256':sha(output/'summary.json'),'runner_sha256':sha(project/'tools/run-visual-checks.py'),'suite_count':len(summary['suites']),'checks':summary.get('checks'),'engine_version':summary.get('engine_version'),'scope':'One new complete final frozen screen catalog run; no prior passes substituted. CPU2 affinity, single-threaded scene; OMP/BLAS environment one thread. Frozen runner sets LP_NUM_THREADS=2 internally; all Godot work here is headless, no render/import.'}
receipt.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','exit_code','elapsed_wall_seconds','suite_count','checks','before_mismatches','after_mismatches']}),flush=True)
raise SystemExit(0 if report['passed'] else 1)
