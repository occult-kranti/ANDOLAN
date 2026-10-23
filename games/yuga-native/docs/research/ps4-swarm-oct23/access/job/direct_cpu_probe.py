"""One CPU-only probe of Gradio's source-verified public call protocol."""
import json
import time
import uuid
from pathlib import Path
import httpx

out = Path(__file__).resolve().parent/'direct-cpu-probe.json'
sid = uuid.uuid4().hex
root = 'https://microsoft-trellis-2.hf.space/gradio_api'
record = {'gpu_calls': 0, 'session_hash': sid, 'events': [], 'status': 'STARTING'}
event_id = None
try:
    with httpx.Client(timeout=20, headers={'User-Agent':'YUGA-public-demo-qualification/1'},
                      trust_env=True, follow_redirects=False) as client:
        assert not any('authorization' in k.lower() or 'token' in k.lower() for k in client.headers)
        before = time.monotonic()
        r = client.post(root+'/call/start_session', json={'data':[], 'session_hash':sid})
        record['post_status'] = r.status_code
        r.raise_for_status()
        event_id = r.json()['event_id']
        record['event_id'] = event_id
        out.write_text(json.dumps(record,indent=2)+'\n')
        with client.stream('GET',root+'/call/start_session/'+sid) as response:
            record['get_status'] = response.status_code
            response.raise_for_status()
            event = None
            for line in response.iter_lines():
                if time.monotonic()-before > 25:
                    raise TimeoutError('CPU-only probe wall limit')
                if line.startswith('event: '):event=line[7:]
                elif line.startswith('data: '):
                    data=json.loads(line[6:])
                    record['events'].append({'event':event,'data':data})
                    out.write_text(json.dumps(record,indent=2)+'\n')
                    if event == 'complete':
                        record['status']='COMPLETED';break
                    if event == 'error':
                        record['status']='SERVER_ERROR';break
        record['wall_seconds'] = time.monotonic()-before
        if record['status'] != 'COMPLETED' and event_id:
            cancel=client.post(root+'/cancel',json={'session_hash':sid,'event_id':event_id,'fn_index':2})
            record['cancel_status']=cancel.status_code
except Exception as error:
    record['error_type']=type(error).__name__
    record['error']=str(error)[:1000]
    record['status']='FAILED_OR_BLOCKED'
finally:
    out.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
