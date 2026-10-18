#!/usr/bin/env python3
"""Declared fresh-cache driver window: 15-second CPU/RSS samples, one 120s stack."""
import argparse,hashlib,json,os,signal,subprocess,time
from pathlib import Path

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def state(pid):
    p=Path('/proc')/str(pid);s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
    return {'starttime':v[19],'state':v[0],'user_ticks':int(v[11]),'system_ticks':int(v[12]),'rss_bytes':int((p/'statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')}
def main():
    a=argparse.ArgumentParser(description=__doc__)
    for name in ['engine','project','output']:a.add_argument('--'+name,type=Path,required=True)
    a=a.parse_args();engine=a.engine.resolve();project=a.project.resolve();output=a.output.resolve();logs=output.with_name(output.name+'-logs');receipt=logs/'driver-window-observer.json'
    assert not receipt.exists();started=time.monotonic();pid=None;next_sample=0
    r={'engine':str(engine),'engine_sha256':sha(engine),'project':str(project),'output':str(output),'observer_sha256':sha(Path(__file__)),'sample_interval_s':15,'stack_gate_s':120,'observer_deadline_s':640,'clock_ticks_per_s':os.sysconf('SC_CLK_TCK'),'stack_attempted':False,'samples':[],'scope':'Read-only exact-owned-process CPU/RSS sampling; one debugger attachment at first >=120s sample if no PNG. No source/cache/input/watchdog changes. Process RSS is resident memory, not heap or unique allocation; CPU is not FPS.'}
    def save():
        logs.mkdir(parents=True,exist_ok=True);tmp=receipt.with_suffix('.partial');tmp.write_text(json.dumps(r,indent=2)+'\n');os.replace(tmp,receipt)
    while time.monotonic()-started<640:
        if pid is None:
            matches=[]
            for p in Path('/proc').iterdir():
                if not p.name.isdigit():continue
                try:
                    argv=(p/'cmdline').read_bytes().decode().rstrip('\0').split('\0')
                    if argv[0]==str(engine) and str(project) in argv and '--output='+str(output) in argv:matches.append(int(p.name))
                except (FileNotFoundError,ProcessLookupError,PermissionError,UnicodeDecodeError):pass
            assert len(matches)<=1
            if matches:
                pid=matches[0];r['pid']=pid;r['starttime']=state(pid)['starttime'];r['owned_process_observed_elapsed_s']=time.monotonic()-started
        if pid is not None:
            try:
                st=state(pid)
                if st['starttime']!=r['starttime']:r['ended']='Owned process identity ended';break
            except (FileNotFoundError,ProcessLookupError):r['ended']='Owned process exited';break
            elapsed=time.monotonic()-started
            if elapsed>=next_sample:
                pngs=len(list(output.glob('*.png')));log=logs/'godot.log';row={'elapsed_s':elapsed,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'png_count':pngs,'log_bytes':log.stat().st_size if log.exists() else 0,**st};r['samples'].append(row);next_sample=elapsed+15;save();print(json.dumps(row),flush=True)
                if elapsed>=120 and not pngs and not r['stack_attempted']:
                    cmd=['/workspace/tooling/native-debug/gdb-local','--batch','-ex','set pagination off','-ex','set print frame-arguments none','-p',str(pid),'-ex','info threads','-ex','thread apply all bt 32','-ex','info proc mappings','-ex','detach'];r['stack_attempted']=True;r['debugger_command']=cmd;t=time.monotonic()
                    with (logs/'native-gdb-120s.log').open('x') as f:
                        try:r['debugger_exit']=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=20).returncode
                        except subprocess.TimeoutExpired:
                            r['debugger_exit']=None;r['debugger_failure']='20s debugger deadline; owned debugger terminated'
                            try:
                                if state(pid)['starttime']==r['starttime']:os.kill(pid,signal.SIGCONT);r['timeout_cleanup']='SIGCONT same owned engine after debugger timeout'
                            except (FileNotFoundError,ProcessLookupError):r['timeout_cleanup']='Engine already exited'
                    r['debugger_elapsed_s']=time.monotonic()-t;r['debugger_log_sha256']=sha(logs/'native-gdb-120s.log');save()
        time.sleep(1)
    else:r['ended']='Observer640s deadline'
    r['elapsed_s']=time.monotonic()-started;save();print(json.dumps({k:v for k,v in r.items() if k!='samples'},indent=2))
if __name__=='__main__':main()
