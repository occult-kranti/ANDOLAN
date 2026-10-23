"""Bounded read-only Actions observation; never retries failed HTTP requests."""
from pathlib import Path
import datetime,hashlib,json,subprocess,time
out=Path(__file__).resolve().parent
start=time.monotonic();history=[]
for number in range(20):
 if time.monotonic()-start>480:break
 began=time.monotonic();p=out/f'observatory-poll-{number:02d}.json'
 url='https://api.github.com/repos/occult-kranti/ANDOLAN/actions/runs/40023890649'
 r=subprocess.run(['curl','--disable','--silent','--show-error','--proto','=https','--tlsv1.2','--max-time','20','--max-filesize','2000000','--output',str(p),'--write-out','%{http_code}',url],capture_output=True,text=True)
 raw=p.read_bytes() if p.exists() else b''
 row={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'curl_exit':r.returncode,'http_status':r.stdout,'body_path':p.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 if r.returncode or r.stdout!='200':
  row['stderr']=r.stderr[:400];history.append(row);print(json.dumps(row),flush=True);break
 d=json.loads(raw)
 assert d['head_sha']=='069ab775c66fff838c4aed149912dd483df4d564','Observed run source changed'
 row.update({k:d.get(k) for k in ['head_sha','status','conclusion','html_url','updated_at']});history.append(row)
 (out/'monitor-history.json').write_text(json.dumps(history,indent=2)+'\n')
 print(json.dumps({k:row.get(k) for k in ['checked_at_utc','status','conclusion','updated_at']}),flush=True)
 if d['status']=='completed':break
 time.sleep(max(0,25-(time.monotonic()-began)))
(out/'monitor-history.json').write_text(json.dumps(history,indent=2)+'\n')
