from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent
VIDEOS = ['9W7QgI3pmT8', 'Pl7ThC4PiVA', 's9HMWYxwnOw', 'tDWtcyeNNew']
REPOS = ['runpod/runpodctl', 'vast-ai/vast-python', 'modal-labs/modal-client']

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def fetch(url, folder, filename):
    folder.mkdir(parents=True, exist_ok=True)
    body, headers, error = folder/filename, folder/(filename+'.headers'), folder/(filename+'.stderr')
    command = ['curl', '--proto', '=https', '--tlsv1.2', '--location', '--max-redirs', '3',
               '--max-time', '20', '--max-filesize', '1048576', '--silent', '--show-error',
               '--dump-header', str(headers), '--output', str(body), '--write-out', '%{json}', url]
    before = stamp()
    result = subprocess.run(command, text=True, capture_output=True)
    error.write_text(result.stderr)
    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError:
        info = {}
    row = {'url':url, 'checked_at_utc':before, 'curl_exit':result.returncode,
           'http_status':info.get('http_code'), 'proxy_connect_status':info.get('http_connect'),
           'effective_url':info.get('url_effective'), 'error':result.stderr.strip(),
           'bytes':body.stat().st_size if body.exists() else 0,
           'body':str(body.relative_to(ROOT)) if body.exists() else None,
           'sha256':hashlib.sha256(body.read_bytes()).hexdigest() if body.exists() else None,
           'headers':str(headers.relative_to(ROOT)), 'stderr':str(error.relative_to(ROOT))}
    return row

def video(video_id):
    row = fetch('https://youtu.be/'+video_id, ROOT/'videos'/video_id, 'page.html')
    row.update(video_id=video_id, title=None, creator=None, transcript=None, frames_reviewed=False,
               audio_reviewed=False, video_inventory_qualified=False)
    return row

def repo(identity):
    result = subprocess.run(['git','ls-remote','https://github.com/'+identity+'.git','HEAD'],
                            text=True, capture_output=True, timeout=30)
    row = {'repository':identity, 'checked_at_utc':stamp(), 'git_exit':result.returncode}
    if result.returncode:
        row['error'] = result.stderr.strip()
        return row
    commit = result.stdout.split()[0]
    row['commit'] = commit
    row['sources'] = []
    folder = ROOT/'sources'/identity.replace('/','__')
    for filename in ['README.md', 'LICENSE']:
        item=fetch('https://raw.githubusercontent.com/'+identity+'/'+commit+'/'+filename, folder, filename)
        row['sources'].append(item)
    return row

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        videos=list(pool.map(video, VIDEOS))
    with ThreadPoolExecutor(max_workers=3) as pool:
        repos=list(pool.map(repo, REPOS))
    (ROOT/'video-ledger.json').write_text(json.dumps(videos,indent=2)+'\n')
    (ROOT/'source-ledger.json').write_text(json.dumps(repos,indent=2)+'\n')
    print(json.dumps({'videos':[{k:r.get(k) for k in ['video_id','curl_exit','http_status','proxy_connect_status','bytes']} for r in videos],
                      'repositories':[{k:r.get(k) for k in ['repository','commit','git_exit']} for r in repos]},indent=2))
