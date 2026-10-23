"""One anonymous quota-enforced export of the already generated session state."""
from pathlib import Path
from urllib.parse import urlsplit
import datetime
import hashlib
import json
import re
import struct
import sys
import time
import httpx

BASE = Path(__file__).resolve().parent
GENERATION = BASE/'run2-direct/receipt.json'
prior = json.loads(GENERATION.read_text())
assert prior['gpu_success_verified'] is True and prior['gpu_submission_attempts'] == 1
SID = prior['session_hash']
ROOT = 'https://microsoft-trellis-2.hf.space/gradio_api'
OUT = BASE/'run2-export'
OUT.mkdir(exist_ok=False)
MAX_FILE = 80 * 1024 * 1024

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def safe(value):
    if isinstance(value,list):return [safe(x) for x in value]
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
    if isinstance(value,str):return re.sub(r'(https?://[^\s<>\"\'?]+)\?[^\s<>\"\']*',r'\1',value)
    return value

receipt = {'started_at_utc':now(),'status':'PREPARED','session_hash':SID,
           'generation_receipt':str(GENERATION),'generation_receipt_sha256':hashlib.sha256(GENERATION.read_bytes()).hexdigest(),
           'anonymous':True,'account_or_token_used':False,'max_paid_cost':0,
           'scope':'One revised-budget, provider-quota-enforced anonymous export attempt; no quota availability promise.',
           'parameters':{'state':'Existing server-side gr.State','decimation_target':100000,'texture_size':1024},
           'gpu_submission_attempts':0,'total_pipeline_gpu_submissions_max':2,'events':[],
           'max_wall_seconds':180,'max_glb_bytes':MAX_FILE,'glb_produced':False}

def save(): (OUT/'receipt.json').write_text(json.dumps(safe(receipt),indent=2)+'\n')
save()
try:
    with httpx.Client(timeout=30,trust_env=True,follow_redirects=False,
                      headers={'User-Agent':'YUGA-public-demo-qualification/1'}) as client:
        assert not any('authorization' in key.lower() or 'token' in key.lower() for key in client.headers)
        receipt['anonymous_headers_verified']=True
        receipt['gpu_submission_attempts']=1;receipt['status']='POSTING';save()
        before=time.monotonic()
        response=client.post(ROOT+'/call/extract_glb',json={'data':[None,100000,1024],'session_hash':SID})
        receipt['post_http_status']=response.status_code;response.raise_for_status()
        receipt['event_id']=response.json()['event_id'];receipt['status']='AWAITING_RESULT';save()
        final=None
        # Read the full standard queue messages for this same session so any
        # provider quota/error description is retained rather than reduced to null.
        with client.stream('GET',ROOT+'/queue/data',params={'session_hash':SID},
                           timeout=httpx.Timeout(30,read=20)) as stream:
            receipt['stream_http_status']=stream.status_code;stream.raise_for_status()
            for line in stream.iter_lines():
                if time.monotonic()-before>180:
                    receipt['status']='WALL_TIMEOUT_UNKNOWN';save()
                    raise TimeoutError('Existing export event exceeded wall limit; no resubmission')
                if not line.startswith('data: '):continue
                message=json.loads(line[6:]);kind=message.get('msg')
                receipt['events'].append({'at_utc':now(),'msg':kind,'event_id':message.get('event_id')})
                save()
                if kind=='process_completed':
                    receipt['server_success']=message.get('success')
                    output=message.get('output',{})
                    if not message.get('success'):
                        receipt['server_error']=safe(output);receipt['status']='SERVER_REJECTED_OR_FAILED';save()
                        raise RuntimeError('Provider rejected or failed the existing export; no retry')
                    final=output.get('data');break
                if kind=='unexpected_error':
                    receipt['server_error']=safe(message);save()
                    raise RuntimeError('Existing export stream reported unexpected_error; no retry')
        receipt['export_wall_seconds']=time.monotonic()-before;save()
        assert isinstance(final,list) and final
        receipt['export_response']=safe(final);save()
        files=[x for x in final if isinstance(x,dict) and x.get('url')]
        assert files,'No file in successful export result'
        url=files[0]['url'];p=urlsplit(url)
        assert p.scheme=='https' and p.hostname=='microsoft-trellis-2.hf.space'
        assert not p.username and not p.password and not p.query and not p.fragment
        target=OUT/'original-diya.glb';total=0
        with client.stream('GET',url,timeout=httpx.Timeout(30,read=20)) as download:
            receipt['download_http_status']=download.status_code;download.raise_for_status()
            length=download.headers.get('content-length')
            assert length is None or int(length)<=MAX_FILE,'Declared file exceeds budget'
            with target.open('xb') as output:
                for block in download.iter_bytes(65536):
                    total+=len(block);assert total<=MAX_FILE,'File exceeded byte budget'
                    output.write(block)
        raw=target.read_bytes();magic,version,length=struct.unpack('<4sII',raw[:12])
        assert magic==b'glTF' and version==2 and length==len(raw)
        receipt.update(status='EXPORT_AND_DOWNLOAD_COMPLETE',glb_produced=True,
                       glb={'path':str(target),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                            'glb_version':version,'header_length_matches':True})
except Exception as error:
    if receipt['status'] not in ('SERVER_REJECTED_OR_FAILED','WALL_TIMEOUT_UNKNOWN'):
        receipt['status']='FAILED_OR_BLOCKED'
    receipt['error_type']=type(error).__name__;receipt['error']=safe(str(error))[:1500]
finally:
    receipt['finished_at_utc']=now();save()
    print(json.dumps({k:receipt.get(k) for k in ['status','gpu_submission_attempts','glb_produced','glb','server_error']},indent=2))
sys.exit(0 if receipt['glb_produced'] else 1)
