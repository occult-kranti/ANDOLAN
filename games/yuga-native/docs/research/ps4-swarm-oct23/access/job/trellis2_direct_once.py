"""One original-image GPU request over Gradio's verified finite-call API."""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import base64
import datetime
import hashlib
import json
import re
import sys
import time
import uuid
import httpx

ROOT = 'https://microsoft-trellis-2.hf.space/gradio_api'
IMAGE = Path('/workspace/generated_images/exec-551faaad-fc73-4cbb-97ff-31b86fbe165c.png')
SHA = '0e26e3719a4f90064c48582d8eac59749ecf35dc18cc2a5a1b10a23ee04b023b'
OUT = Path(__file__).resolve().parent/'run2-direct'
OUT.mkdir(exist_ok=False)
SID = uuid.uuid4().hex

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sanitized(value):
    if isinstance(value, dict):return {k:sanitized(v) for k,v in value.items()}
    if isinstance(value, list):return [sanitized(v) for v in value]
    if isinstance(value, str):
        def strip(match):
            p=urlsplit(match.group());return urlunsplit((p.scheme,p.netloc,p.path,'',''))
        return re.sub(r'https?://[^\s<>\"\']+',strip,value)
    return value

receipt = {'started_at_utc':now(),'status':'STARTING','session_hash':SID,
           'anonymous_transport':'Plain httpx; no HF SDK/token/login/cached account is used.',
           'max_paid_cost':0,'max_gpu_function_submissions':1,'max_declared_gpu_seconds':120,
           'gpu_submission_attempts':0,'gpu_success_verified':False,'glb_produced':False,
           'input':{'path':str(IMAGE),'sha256':SHA},'calls':[],
           'export':'HELD: fixed120s export cannot be justified by a qualified remaining quota value.'}

def save():
    (OUT/'receipt.json').write_text(json.dumps(sanitized(receipt),indent=2)+'\n')

def call(client,name,data,seconds,gpu=False):
    if gpu:
        assert receipt['gpu_submission_attempts']==0
        receipt['gpu_submission_attempts']+=1
    row={'api_name':name,'gpu_function':gpu,'started_at_utc':now(),'status':'POSTING','events':[]}
    receipt['calls'].append(row);save()
    started=time.monotonic()
    response=client.post(ROOT+'/call/'+name,json={'data':data,'session_hash':SID})
    row['post_status']=response.status_code;response.raise_for_status()
    row['event_id']=response.json()['event_id'];row['status']='AWAITING_RESULT';save()
    result=None
    # Gradio6.1's GET handler uses this path component as the session queue key.
    with client.stream('GET',ROOT+'/call/'+name+'/'+SID,timeout=httpx.Timeout(30,read=20)) as stream:
        row['get_status']=stream.status_code;stream.raise_for_status()
        event=None
        for line in stream.iter_lines():
            if time.monotonic()-started>seconds:
                row['status']='WALL_TIMEOUT_UNKNOWN';save()
                raise TimeoutError('Existing event exceeded wall limit; no resubmission')
            if line.startswith('event: '):event=line[7:]
            elif line.startswith('data: '):
                payload=json.loads(line[6:]);row['events'].append({'at_utc':now(),'event':event})
                save()
                if event=='error':
                    row['server_error_data']=sanitized(payload);row['status']='SERVER_ERROR';save()
                    raise RuntimeError('Public Space returned an error; no GPU retry')
                if event=='complete':
                    result=payload;row['status']='COMPLETED';break
    row['wall_seconds']=time.monotonic()-started;save()
    if row['status']!='COMPLETED':raise RuntimeError('Stream ended without a final result; no GPU retry')
    return result

save()
try:
    raw=IMAGE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
    assert raw[:8]==b'\x89PNG\r\n\x1a\n' and len(raw)<5*1024*1024
    with httpx.Client(timeout=30,trust_env=True,follow_redirects=False,
                      headers={'User-Agent':'YUGA-public-demo-qualification/1'}) as client:
        assert not any('authorization' in k.lower() or 'token' in k.lower() for k in client.headers)
        receipt['anonymous_headers_verified']=True
        call(client,'start_session',[],30)
        with IMAGE.open('rb') as stream:
            upload=client.post(ROOT+'/upload',files={'files':('original-diya.png',stream,'image/png')})
        receipt['upload_http_status']=upload.status_code;upload.raise_for_status()
        remote=upload.json();assert isinstance(remote,list) and len(remote)==1
        receipt['upload_result']=remote;save()
        filedata={'path':remote[0],'orig_name':'original-diya.png','mime_type':'image/png',
                  'meta':{'_type':'gradio.FileData'}}
        preprocessed=call(client,'preprocess_image',[filedata],45)
        assert isinstance(preprocessed,list) and len(preprocessed)==1
        (OUT/'preprocess-response.json').write_text(json.dumps(sanitized(preprocessed),indent=2)+'\n')
        parameters=[preprocessed[0],23,'512',7.5,0.7,8,5.0,7.5,0.5,8,3.0,1.0,0.0,8,3.0]
        receipt['generation_settings']={'seed':23,'resolution':'512','sampling_steps_per_stage':8,
                                        'remaining_guidance_values':'Pinned app defaults'};save()
        outputs=call(client,'image_to_3d',parameters,180,gpu=True)
        assert isinstance(outputs,list)
        previews=[value for value in outputs if isinstance(value,str) and 'data:image/jpeg;base64,' in value]
        assert len(previews)==1
        preview=previews[0];(OUT/'preview.html').write_text(preview)
        snapshots=[]
        for index,encoded in enumerate(re.findall(r'src="data:image/jpeg;base64,([^\"]+)"',preview)):
            body=base64.b64decode(encoded,validate=True);assert len(body)<4*1024*1024
            p=OUT/f'preview-{index:02d}.jpg';p.write_bytes(body)
            snapshots.append({'path':p.name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
        receipt.update(status='GENERATION_COMPLETE_EXPORT_HELD',gpu_success_verified=True,
                       preview_snapshots=snapshots)
except Exception as error:
    receipt.update(status='FAILED_OR_BLOCKED',error_type=type(error).__name__,
                   error=sanitized(str(error))[:1500])
finally:
    receipt['finished_at_utc']=now();save()
    print(json.dumps({k:receipt[k] for k in ['status','gpu_submission_attempts','gpu_success_verified','glb_produced']},indent=2))
sys.exit(0 if receipt['gpu_success_verified'] else 1)
