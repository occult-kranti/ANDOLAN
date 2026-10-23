"""Bind research inputs and completed one-shot outputs; do not run jobs."""
from pathlib import Path
import datetime
import hashlib
import json
import re

b = Path(__file__).resolve().parent
def read(path):return json.loads((b/path).read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
repos, spaces, recheck = read('source-ledger.json'), read('space-ledger.json'), read('recheck1-ledger.json')
rows = [s for r in repos for s in r.get('sources',[])] + spaces + recheck['requests']
verified = []
for row in rows:
    if row.get('body') and row.get('sha256'):
        assert digest(b/row['body']) == row['sha256'], row['body']
        verified.append(row['body'])
for p in b.rglob('*.json'):
    if 'venv' not in p.relative_to(b).parts:
        json.loads(p.read_text())
generation, export = read('job/run2-direct/receipt.json'), read('job/run2-export/receipt.json')
assert generation['gpu_submission_attempts'] == export['gpu_submission_attempts'] == 1
assert generation['gpu_success_verified'] and export['glb_produced']
# Source app renders 6 modes x8 views, followed by six JPEG mode-selector icons.
assert len(generation['preview_snapshots']) == 54
for row in generation['preview_snapshots']:
    assert digest(b/'job/run2-direct'/row['path']) == row['sha256']
glb = b/'job/run2-export/original-diya.glb'
assert digest(glb) == export['glb']['sha256']
artifacts = ['job/trellis2_once.py','job/direct_cpu_probe.py','job/trellis2_direct_once.py',
             'job/trellis2_export_once.py','job/requirements.lock','job/resolve.json','job/installed.json',
             'job/run1/receipt.json','job/direct-cpu-probe.json','job/run2-direct/receipt.json',
             'job/run2-export/receipt.json','job/run2-export/structural-inspection.json',
             'spaces/trellis2-app.py','spaces/recheck1/trellis2-config.json','spaces/recheck1/trellis2-info.json']
stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
binding = {'checked_at_utc':stamp,
           'scope':'Post-run byte bindings; executed scripts were not modified after recorded runs. Original receipts retain their initial scope/results.',
           'files':{p:digest(b/p) for p in artifacts}, 'input_sha256':generation['input']['sha256'],
           'glb_sha256':export['glb']['sha256'], 'rendered_view_count':48,'mode_icon_count':6,
           'embedded_images':generation['preview_snapshots'],
           'excluded_from_handoff':['job/venv/','__pycache__/'],
           'actual_model_resident_revision':'not exposed by public service'}
(b/'experiment-binding.json').write_text(json.dumps(binding,indent=2)+'\n')
evidence = {
    'checked_at_utc':stamp,
    'scope':'Runtime capability/source research, fresh video/Space checks, and one authorized original-prop public GPU workflow.',
    'general_gpu_provider_tool_found':False,'configured_gpu_provider_account_found':False,'local_gpu_found':False,
    'managed_image_generation_tool_available':True,'requested_videos':4,'videos_with_content_recovered':0,
    'video_rechecks_after_restart':4,'public_spaces_checked':3,
    'public_space_with_running_metadata':'microsoft/TRELLIS.2','initial_runtime_host_access':'proxy_connect_403',
    'post_restart_runtime_host_access':'HTTP200config/APIinfo','gpu_function_submission_attempts':2,
    'image_to_3d_generations_completed':1,'glb_exports_completed':1,'gpu_resubmissions':0,'input_images_uploaded':1,
    'glb':{'path':'job/run2-export/original-diya.glb','bytes':export['glb']['bytes'],'sha256':export['glb']['sha256']},
    'rendered_views':48,'mode_selector_icons':6,
    'generation_wall_seconds':generation['calls'][-1]['wall_seconds'],'export_wall_seconds':export['export_wall_seconds'],
    'actual_gpu_seconds':'not exposed','remaining_daily_quota':'not exposed','gpu_hardware_identity':'not independently measured',
    'provider_resources_created':0,'account_or_token_used_for_demo':False,'paid_api_requests':0,'local_model_weights_downloaded':False,
    'client_installed':{'package':'gradio-client','version':'2.0.1','venv_allocated_mib_approx':46,'dependency_lock':'job/requirements.lock'},
    'source_body_hashes_verified':len(verified),
    'successful_response_body_bytes':sum(r.get('bytes',0) for r in rows if r.get('http_status')==200),
    'source_files_verified':verified,
    'remaining_prerequisites':['Blender/Godot acceptance of this original prop; root owns later review.',
                               'Owned GPUendpoint/account and explicitbudget for general-purpose provider allocation.',
                               'Activate/retest YouTube destinations or supply accessible video/captions.'],
    'artifacts':{'capabilities':'capabilities.json','tool_inventory':'tools-inventory.json','videos':'video-ledger.json',
                 'sources':'source-ledger.json','initial_spaces':'space-ledger.json','post_restart_recheck':'recheck1-ledger.json',
                 'experiment_byte_bindings':'experiment-binding.json','report':'README.md'}}
(b/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
items = []
for p in sorted(b.rglob('*')):
    rel = p.relative_to(b)
    if 'venv' in rel.parts or '__pycache__' in rel.parts or not p.is_file() or p.name=='SHA256SUMS':continue
    items.append(digest(p)+'  '+str(rel))
(b/'SHA256SUMS').write_text('\n'.join(items)+'\n')
links = 0
for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',(b/'README.md').read_text()):
    if '://' in target or target.startswith('#'):continue
    links += 1
    assert (b/target.split('#')[0]).exists(), target
print(json.dumps({'source_bodies_verified':len(verified),'report_links_verified':links,
                  'handoff_files_hashed':len(items),'gpu_calls':2,'glb_bytes':export['glb']['bytes']},indent=2))
