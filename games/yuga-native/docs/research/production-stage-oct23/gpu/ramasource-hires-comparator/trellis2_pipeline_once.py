"""Reuse the previously verified official Gradio transport; one anonymous pipeline."""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import struct
import sys
import time
import uuid
import httpx

BASE = 'https://microsoft-trellis-2.hf.space/gradio_api'
parser=argparse.ArgumentParser()
parser.add_argument('--input',required=True,type=Path)
parser.add_argument('--sha256',required=True)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
args.output.mkdir(exist_ok=False)
SID=uuid.uuid4().hex
MAX_GLB=80*1024*1024

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def safe(value):
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
    if isinstance(value,list):return [safe(v) for v in value]
    if isinstance(value,str):
        def clean(match):
            p=urlsplit(match.group());return urlunsplit((p.scheme,p.netloc,p.path,'',''))
        return re.sub(r'https?://[^\s<>\"\']+',clean,value)
    return value

receipt={'started_at_utc':now(),'status':'PREPARING','session_hash':SID,'client_pid':os.getpid(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'input':{'path':str(args.input),'sha256':args.sha256},
 'transport':'Anonymous plain HTTPX; inherited HTTPS proxy/CA, no HF SDK or token.',
 'max_paid_cost':0,'max_gpu_submissions':2,'gpu_submission_attempts':0,
 'gpu_generation_verified':False,'glb_produced':False,'calls':[],
 'source_reuse':'Based on prior verified trellis2_direct_once.py and trellis2_export_once.py, source SHA ebf60b20fc5a4607f90a1c11c0aab0ceeda5429d.'}

def save():
    p=args.output/'receipt.json'
    temp=args.output/'receipt.json.tmp'
    temp.write_text(json.dumps(safe(receipt),indent=2)+'\n')
    temp.replace(p)

def call(client,name,data,seconds,gpu=False):
    row={'api_name':name,'gpu_function':gpu,'started_at_utc':now(),'status':'POSTING','events':[]}
    receipt['calls'].append(row)
    if gpu:
        assert receipt['gpu_submission_attempts']<2
        receipt['gpu_submission_attempts']+=1
    save();began=time.monotonic()
    response=client.post(BASE+'/call/'+name,json={'data':data,'session_hash':SID})
    row['post_http_status']=response.status_code;response.raise_for_status()
    row['event_id']=response.json()['event_id'];row['status']='AWAITING_RESULT';save()
    route=BASE+'/queue/data' if gpu else BASE+'/call/'+name+'/'+SID
    query={'session_hash':SID} if gpu else None
    with client.stream('GET',route,params=query,timeout=httpx.Timeout(30,read=20)) as stream:
        row['get_http_status']=stream.status_code;stream.raise_for_status();event=None
        for line in stream.iter_lines():
            if time.monotonic()-began>seconds:
                row['status']='WALL_TIMEOUT_UNKNOWN';save()
                raise TimeoutError('Submitted event wall limit reached; do not resubmit')
            if line.startswith('event: '):event=line[7:]
            if not line.startswith('data: '):continue
            value=json.loads(line[6:])
            if gpu:
                kind=value.get('msg');which=value.get('event_id')
                row['events'].append({'at_utc':now(),'msg':kind,'event_id':which});save()
                if which not in (None,row['event_id']):continue
                if kind=='process_completed':
                    row['wall_seconds']=time.monotonic()-began
                    if not value.get('success'):
                        row['status']='SERVER_REJECTED_OR_FAILED';row['server_error']=safe(value.get('output',{}));save()
                        raise RuntimeError('Provider rejected or failed this event; no GPU retry')
                    row['status']='COMPLETED';save();return value['output']['data']
                if kind=='unexpected_error':
                    row['status']='SERVER_ERROR';row['server_error']=safe(value);save()
                    raise RuntimeError('Submitted event failed; no GPU retry')
            else:
                row['events'].append({'at_utc':now(),'event':event});save()
                if event=='error':
                    row['status']='SERVER_ERROR';row['server_error']=safe(value);save()
                    raise RuntimeError('CPU preprocessing failed; no GPU submitted')
                if event=='complete':
                    row['status']='COMPLETED';row['wall_seconds']=time.monotonic()-began;save();return value
    row['status']='STREAM_ENDED_UNKNOWN';save()
    raise RuntimeError('Event stream ended without a final result; no resubmission')

save()
try:
    raw=args.input.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==args.sha256,'Input hash mismatch'
    assert raw[:8]==b'\x89PNG\r\n\x1a\n' and len(raw)<=5*1024*1024,'PNG/input budget mismatch'
    # Header colour type 6 is RGBA; actual alpha range is recorded separately by root.
    assert raw[25]==6,'Input must be RGBA so the separate background-removal model is not required'
    receipt['input']['bytes']=len(raw);receipt['input']['png_color_type']=6
    with httpx.Client(timeout=30,trust_env=True,follow_redirects=False,headers={'User-Agent':'YUGA-original-asset-pilot/2'}) as client:
        assert not any('authorization' in k.lower() or 'token' in k.lower() for k in client.headers)
        receipt['anonymous_headers_verified']=True
        call(client,'start_session',[],40)
        with args.input.open('rb') as image:
            upload=client.post(BASE+'/upload',files={'files':('original-asset.png',image,'image/png')})
        receipt['upload_http_status']=upload.status_code;upload.raise_for_status()
        remote=upload.json();assert isinstance(remote,list) and len(remote)==1
        filedata={'path':remote[0],'orig_name':'original-asset.png','mime_type':'image/png','meta':{'_type':'gradio.FileData'}}
        receipt['upload_result']=safe(remote);save()
        prepared=call(client,'preprocess_image',[filedata],60)
        assert isinstance(prepared,list) and len(prepared)==1
        (args.output/'preprocess-response.json').write_text(json.dumps(safe(prepared),indent=2)+'\n')
        receipt['generation_settings']={'seed':71,'resolution':'1024','steps_per_stage':8,'guidance':'Pinned source defaults'}
        receipt['status']='GENERATION_SUBMITTING';save()
        parameters=[prepared[0],71,'1024',7.5,0.7,8,5.0,7.5,0.5,8,3.0,1.0,0.0,8,3.0]
        result=call(client,'image_to_3d',parameters,180,True)
        previews=[v for v in result if isinstance(v,str) and 'data:image/jpeg;base64,' in v]
        assert len(previews)==1,'Successful event has no expected preview'
        preview=previews[0];(args.output/'preview.html').write_text(preview)
        shots=[]
        for i,encoded in enumerate(re.findall(r'src="data:image/jpeg;base64,([^\"]+)"',preview)):
            data=base64.b64decode(encoded,validate=True);assert len(data)<4*1024*1024
            p=args.output/f'preview-{i:02d}.jpg';p.write_bytes(data)
            shots.append({'path':p.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        receipt.update(status='GENERATION_COMPLETE',gpu_generation_verified=True,preview_snapshots=shots)
        receipt['export_settings']={'decimation_target':100000,'texture_size':1024};save()
        # A separate provider-enforced quota admission; never alter auth or retry rejection.
        result=call(client,'extract_glb',[None,100000,1024],180,True)
        files=[v for v in result if isinstance(v,dict) and v.get('url')]
        assert files,'Successful export contains no file'
        url=files[0]['url'];parsed=urlsplit(url)
        assert parsed.scheme=='https' and parsed.hostname=='microsoft-trellis-2.hf.space'
        assert not parsed.query and not parsed.fragment and not parsed.username and not parsed.password
        receipt['export_response']=safe(result);save()
        target=args.output/'original-asset.glb';total=0
        with client.stream('GET',url,timeout=httpx.Timeout(30,read=20)) as download:
            receipt['download_http_status']=download.status_code;download.raise_for_status()
            length=download.headers.get('content-length');assert length is None or int(length)<=MAX_GLB
            with target.open('xb') as file:
                for block in download.iter_bytes(65536):
                    total+=len(block);assert total<=MAX_GLB;file.write(block)
        data=target.read_bytes();magic,version,length=struct.unpack('<4sII',data[:12])
        assert magic==b'glTF' and version==2 and length==len(data)
        receipt.update(status='EXPORTED',glb_produced=True,glb={'path':str(target),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'header_length_matches':True})
except Exception as error:
    receipt.update(status='FAILED_OR_BLOCKED',error_type=type(error).__name__,error=safe(str(error))[:1200])
finally:
    receipt['finished_at_utc']=now();save()
    print(json.dumps({k:receipt.get(k) for k in ['status','gpu_submission_attempts','gpu_generation_verified','glb_produced','glb','error_type']}))
sys.exit(0 if receipt['glb_produced'] else 1)
