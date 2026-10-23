"""Download only the fixed deployed routes needed for byte verification."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime,hashlib,json,subprocess
out=Path(__file__).resolve().parent
base='https://occult-kranti.github.io/ANDOLAN/'
web=Path('/workspace/ANDOLAN/games/yuga-native/tools/build-observatory/web')
baseline=Path('/workspace/scratch/production-stage-oct23/site-baseline/dist/site')
targets={
 'production/index.html':('production/',web/'index.html'),
 'production/app.js':('production/app.js',web/'app.js'),
 'production/styles.css':('production/styles.css',web/'styles.css'),
 'production/status.json':('production/status.json',web/'status.json'),
 'production/publication.json':('production/publication.json',None),
 'production/media/rama-generated.glb':('production/media/rama-generated.glb',web/'media/rama-generated.glb'),
 'production/viewer/index.html':('production/viewer/',web/'viewer/index.html'),
 'production/viewer/assets/index-C3j7jJja.css':('production/viewer/assets/index-C3j7jJja.css',web/'viewer/assets/index-C3j7jJja.css'),
 'production/viewer/assets/index-DX6om3MO.js':('production/viewer/assets/index-DX6om3MO.js',web/'viewer/assets/index-DX6om3MO.js'),
 'production/viewer/NOTICE.txt':('production/viewer/NOTICE.txt',web/'viewer/NOTICE.txt'),
 'production/viewer/PLAYCANVAS-LICENSE.txt':('production/viewer/PLAYCANVAS-LICENSE.txt',web/'viewer/PLAYCANVAS-LICENSE.txt'),
 'production/media/licenses/PRODUCTION-SOURCE-NOTICE.md':('production/media/licenses/PRODUCTION-SOURCE-NOTICE.md',web/'media/licenses/PRODUCTION-SOURCE-NOTICE.md'),
 'production/media/licenses/CLOUD-DIYA-PILOT.md':('production/media/licenses/CLOUD-DIYA-PILOT.md',web/'media/licenses/CLOUD-DIYA-PILOT.md'),
 'production/media/licenses/Noto-fonts/COPYRIGHT.txt':('production/media/licenses/Noto-fonts/COPYRIGHT.txt',web/'media/licenses/Noto-fonts/COPYRIGHT.txt'),
 'index.html':('',baseline/'index.html'),
 'yuga/index.html':('yuga/',baseline/'yuga/index.html'),
 'yuga/lab/index.html':('yuga/lab/',baseline/'yuga/lab/index.html'),
 'yuga/lane-lab/index.html':('yuga/lane-lab/',baseline/'yuga/lane-lab/index.html'),
 'yuga/control-lab/index.html':('yuga/control-lab/',baseline/'yuga/control-lab/index.html')}

def fetch(item):
 name,(route,expected)=item;p=out/'public'/name;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),'Do not overwrite the original observation'
 r=subprocess.run(['curl','--disable','--silent','--show-error','--proto','=https','--tlsv1.2','--max-time','25','--max-filesize','20000000','--output',str(p),'--write-out','%{http_code}',base+route],capture_output=True,text=True)
 body=p.read_bytes() if p.exists() else b''
 row={'path':name,'url':base+route,'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'curl_exit':r.returncode,'http_status':r.stdout,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
 if expected is not None and expected.is_file():
  raw=expected.read_bytes();row['expected_local_bytes']=len(raw);row['expected_local_sha256']=hashlib.sha256(raw).hexdigest();row['matches_expected_local']=raw==body
 if r.returncode or r.stdout!='200':row['stderr']=r.stderr[:500]
 return row
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,targets.items()))
(out/'public-fetch-ledger.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps({'responses':len(rows),'all_200':all(r['curl_exit']==0 and r['http_status']=='200' for r in rows),'byte_matches':sum(r.get('matches_expected_local',False) for r in rows),'failed':[r for r in rows if r['http_status']!='200' or r.get('matches_expected_local') is False]},indent=2))
