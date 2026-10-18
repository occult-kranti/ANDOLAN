#!/usr/bin/env python3
"""Bounded private component runner. No import, source copy, or raster."""
from pathlib import Path
import datetime, gzip, hashlib, json, os, signal, subprocess, sys, time
ROOT=Path('/workspace/ANDOLAN/games/yuga-native')
OWNER=ROOT/'docs/evidence/desktop-finish/continuation-oct18b/W5-motion-r1'
STAGE=Path('/workspace/scratch/yuga-continuation-W5-r1/project-r2')
ENGINE=Path('/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority')
def sha(p): return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def pins():
    names=[ROOT/'scripts/rama_motion.gd', OWNER/'canonical-rama_motion.gd', OWNER/'rama_motion.gd',OWNER/'component_authored_descent.gd',ROOT/'tests/graphics_g2_support_cases.gd',ENGINE,STAGE/'project.godot',STAGE/'assets/animations/rama_hero_motion.tres',STAGE/'assets/heroes/rama-hero.glb',STAGE/'assets/heroes/rama-hero.glb.import']
    names+=list((STAGE/'.godot/imported').glob('rama-hero.glb-*.scn'))
    return {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in names}
def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    before=pins();assert before[str(ROOT/'scripts/rama_motion.gd')]['sha256']=='5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5'
    free=os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize;assert free>=500*1024*1024
    env=os.environ.copy();env.update({'LP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','XDG_DATA_HOME':str(out/'user/data'),'XDG_CACHE_HOME':str(out/'user/cache'),'XDG_CONFIG_HOME':str(out/'user/config')})
    cmd=['taskset','-c','3',str(ENGINE),'--headless','--path',str(STAGE),'--script',str(OWNER/'component_authored_descent.gd'),'--','--report='+str(out/'report.json')]
    start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();timed=False
    with open(out/'godot.log','xb') as log:
        proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=proc.wait(timeout=180)
        except subprocess.TimeoutExpired:
            timed=True;os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
    after=pins();rec={'command':cmd,'env':{k:env[k] for k in ['LP_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME']},'start_utc':start,'elapsed_s':time.monotonic()-t,'pid':proc.pid,'exit_code':code,'timeout':timed,'source_before':before,'source_after':after,'source_unchanged':before==after,'free_before':free,'engine_worker_pool':'Not capped; CPU affinity and listed library settings only.'}
    raw=out/'report.json'
    if raw.exists():
        assert raw.stat().st_size<20*1024*1024
        packed=out/'report.json.gz'
        with raw.open('rb') as src,packed.open('xb') as dst,gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as gz:
            while chunk:=src.read(1024*1024):gz.write(chunk)
        with gzip.open(packed,'rb') as z:restored=hashlib.file_digest(z,'sha256').hexdigest()
        assert restored==sha(raw)
        rec['report']={'raw_bytes':raw.stat().st_size,'raw_sha256':sha(raw),'gzip_bytes':packed.stat().st_size,'gzip_sha256':sha(packed),'roundtrip_sha256':restored}
    (out/'execution.json').write_text(json.dumps(rec,indent=2)+'\n')
    print(json.dumps({'exit_code':code,'timeout':timed,'elapsed_s':rec['elapsed_s'],'source_unchanged':before==after,'report':rec.get('report')}))
    return code if before==after else 99
if __name__=='__main__':sys.exit(main())
