import json,pathlib,importlib.util,copy,hashlib
root=pathlib.Path('/workspace/scratch/yuga-frontage-review-r1');out=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('cmp',out/'compare_frontage.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a=json.loads((root/'baseline-preflight-r4/preflight.json').read_text());b=json.loads((root/'candidate-preflight-r4/preflight.json').read_text())
def first(x):return next(v for v in x['shots'][0]['materials'].values() if m.OWNER_KEY in v.get('properties',{}))
cases=[]
for label,mutation,expected in [
 ('real metadata-only witness',lambda x:None,True),
 ('mixed owner rejected',lambda x:first(x)['properties'].__setitem__(m.OWNER_KEY,first(x)['properties'][m.OWNER_KEY]+1),False),
 ('boolean owner rejected',lambda x:first(x)['properties'].__setitem__(m.OWNER_KEY,True),False),
 ('actual material property change rejected',lambda x:first(x)['properties'].__setitem__('render_priority',1),False),
 ('other metadata change rejected',lambda x:first(x)['properties'].__setitem__('metadata/unapproved',1),False),
 ('wrong named material rejected',lambda x:first(x)['properties'].__setitem__('resource_name','Unapproved'),False),
]:
 c=copy.deepcopy(b);mutation(c);r=m.compare(a,c);cases.append({'case':label,'expected':expected,'actual':r['passed'],'passed':r['passed'] is expected,'errors':r['errors'],'shot_errors':[z['errors'] for z in r['shots']]})
report={'checks':cases,'passed':all(c['passed'] for c in cases),'comparator_sha256':hashlib.sha256((out/'compare_frontage.py').read_bytes()).hexdigest(),'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'baseline-preflight-r4/preflight.json',root/'candidate-preflight-r4/preflight.json']}}
(out/'controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':len(cases)}));assert report['passed']
