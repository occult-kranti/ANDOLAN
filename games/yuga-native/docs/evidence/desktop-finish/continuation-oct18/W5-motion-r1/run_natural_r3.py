#!/usr/bin/env python3
"""One bounded private headless comparison; proven regular output, then lossless streaming gzip."""
from pathlib import Path
import gzip, hashlib, importlib.util, json, os, re, subprocess, time

OWNER = Path(__file__).resolve().parent
REPO = OWNER.parents[6]
ROOT = Path('/workspace/scratch/yuga-continuation-W5-r1')
PROJECT = ROOT / 'project-r2'
OUTPUT = ROOT / 'natural-r3'
ENGINE = Path('/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority')
ENGINE_SHA = 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    validator = Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/next-motion/W5-locomotion-current-r1/snapshot.py')
    spec = importlib.util.spec_from_file_location('snapshot', validator)
    snapshot = importlib.util.module_from_spec(spec); spec.loader.exec_module(snapshot)
    snapshot.verify(PROJECT)
    before = sha(PROJECT / snapshot.MARKER)
    assert before == json.loads((OWNER/'stage-r2.json').read_text())['candidate_marker_sha256']
    assert sha(ENGINE) == ENGINE_SHA and not OUTPUT.exists()
    assert sha(Path('/workspace/ANDOLAN/games/yuga-native/scripts/rama_motion.gd')) == '5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5'
    logs = ROOT / 'natural-r3-logs'; logs.mkdir()
    env = os.environ.copy()
    env.update(LP_NUM_THREADS='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    for name, part in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        target=logs/'user'/part; target.mkdir(parents=True); env[name]=str(target)
    cmd=['taskset','-c','3',str(ENGINE),'--path',str(PROJECT),'--audio-driver','Dummy','--disable-vsync','--fixed-fps','30','--headless','--script','res://tools/graphics-six/capture_locomotion.gd','--',f'--output={OUTPUT}','--case=locomotion','--preflight']
    report_path=OUTPUT/'preflight.json'; zipped=OUTPUT/'preflight.json.gz'; stream_result={}
    record={'command':cmd,'engine_sha256':ENGINE_SHA,'stage_sha256':before,'started_unix':time.time(),'timeout_s':180,'streaming_gzip_after_regular_report':True,'raw_limit_bytes':20*1024**2,'source_scope':'Historical96d5 stage plus private motion; full helper/input/import bytes unchanged. Headless only; no rendering or cache seeding.','worker_pool_capped':False,'affinity':'3','thread_environment':{k:env[k] for k in ['LP_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}}
    start=time.monotonic(); process=None
    try:
        with (logs/'godot.log').open('wb') as log:
            process=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT);record['pid']=process.pid
            print(json.dumps({'started_pid':process.pid,'output':str(OUTPUT)}),flush=True)
            record['exit_code']=process.wait(timeout=180)
        assert report_path.is_file() and report_path.stat().st_size<=20*1024**2
        raw_sha=sha(report_path); raw_size=report_path.stat().st_size
        with report_path.open('rb') as source, zipped.open('wb') as destination, gzip.GzipFile(filename='',mode='wb',fileobj=destination,mtime=0) as packed:
            while block:=source.read(65536): packed.write(block)
        with gzip.open(zipped,'rb') as restored:
            restored_hash=hashlib.file_digest(restored,'sha256').hexdigest()
        assert restored_hash==raw_sha
        stream_result.update(raw_bytes=raw_size,raw_sha256=raw_sha,gzip_bytes=zipped.stat().st_size,gzip_sha256=sha(zipped),roundtrip_sha256=restored_hash)
        with gzip.open(zipped,'rt') as packed: report=json.load(packed)
        # Explicit root authorization: remove only this newly created exact raw duplicate.
        assert report_path.parent==OUTPUT and not report_path.is_symlink() and sha(report_path)==raw_sha
        report_path.unlink();stream_result['new_raw_duplicate_removed']=True
        record['checks']=report.get('checks',[])
        errors=[line for line in (logs/'godot.log').read_text().splitlines() if re.search(r'(^|\s)(SCRIPT ERROR|ERROR|WARNING):',line)]
        record['engine_diagnostics']=errors
        record['passed']=record['exit_code']==0 and report.get('complete') is True and len(report.get('shots',[]))==270 and len(record['checks'])==10 and all(r['passed'] is True for r in record['checks']) and not errors
        snapshot.verify(PROJECT);record['source_unchanged']=sha(PROJECT/snapshot.MARKER)==before
        record['passed']=record['passed'] and record['source_unchanged']
    except Exception as error: record.update(passed=False,failure=repr(error))
    finally:
        if process and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill();process.wait()
        record.update(stream=stream_result,elapsed_s=time.monotonic()-start,finished_unix=time.time())
        (logs/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)
    return 0 if record.get('passed') else 1
if __name__=='__main__': raise SystemExit(main())
