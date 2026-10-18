import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/workspace/ANDOLAN/games/yuga-native')
out=root/'docs/evidence/desktop-finish/D04-I02/W5'
fx=root/'scripts/rama_ability_effects.gd'
test='res://tests/desktop_i02_volley_feedback_cases.gd'
baseline=(out/'source-r1/rama_ability_effects.gd').read_bytes()
candidate=fx.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(baseline)=='b77f68aeeb57ab5e7be8b84385505d1f7078cb90ef1cedc33c7e4d894ec9d8be'
assert sha(candidate)=='119353e71e5ad1eee61360d52db036075a6be60ec30c4c2ee228b5656243db66'
names=['baseline-r4','candidate-r2','candidate-zero-r2','effects-adversarial-r1']
assert not any((out/(n+'.json')).exists() for n in names)
runs=[]
def run(name,script,extras,expected):
    env=os.environ.copy()
    env.update({k:'1' for k in ['LP_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']})
    for k,s in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:env[k]='/tmp/yuga-i02-'+name+'/'+s
    command=['timeout','60s','taskset','-c','4','godot','--headless','--path','.', '--script',script,'--',*extras,'--report='+str(out/(name+'.json'))]
    before=sha(fx.read_bytes());t=time.monotonic()
    with (out/(name+'.log')).open('wb') as log:p=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    report=json.loads((out/(name+'.json')).read_text()) if (out/(name+'.json')).exists() else {}
    record={'name':name,'command':command,'cwd':str(root),'environment':{k:env[k] for k in ['LP_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME']},'exit_code':p.returncode,'expected_exit_code':expected,'seconds':time.monotonic()-t,'effects_before':before,'effects_after':sha(fx.read_bytes()),'report_sha256':sha((out/(name+'.json')).read_bytes()) if report else None,'log_sha256':sha((out/(name+'.log')).read_bytes())}
    runs.append(record);print(json.dumps(record),flush=True)
    assert p.returncode==expected and before==record['effects_after']
try:
    fx.write_bytes(baseline)
    run('baseline-r4',test,[],1)
finally:
    assert fx.read_bytes()==baseline, 'unexpected concurrent effects writer; refusing restore'
    fx.write_bytes(candidate)
    (out/'execution-final.json').write_text(json.dumps({'runs':runs,'restored_candidate_sha256':sha(fx.read_bytes())},indent=2)+'\n')
try:
    run('candidate-r2',test,[],0)
    run('candidate-zero-r2',test,['--warmup-ticks=0'],0)
    run('effects-adversarial-r1','res://tests/rama_effect_adversarial_cases.gd',[],0)
finally:
    (out/'execution-final.json').write_text(json.dumps({'runs':runs,'restored_candidate_sha256':sha(fx.read_bytes()),'scope':'CPU4 affinity; LP/OMP/BLAS/MKL1; engine worker pool not capped. No raster/import/listening.'},indent=2)+'\n')
