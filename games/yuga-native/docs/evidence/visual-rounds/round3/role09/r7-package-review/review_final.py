from pathlib import Path
import copy,hashlib,importlib.util,json,tempfile,sys
root=Path('/workspace/ANDOLAN/games/yuga-native');proposal=Path(sys.argv[1]);out=Path(__file__).parent
spec=importlib.util.spec_from_file_location('independent_pack',root/'tools/package-native.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
checks=[]
def ck(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
def rejects(name,fn):
 try:fn();ck(name,False,'accepted')
 except (ValueError,OSError,KeyError) as e:ck(name,True,str(e))
v=p.validate_rama_hero_notice(proposal);m=json.loads((proposal/'promotion-manifest.json').read_text());n=json.loads((proposal/'NOTICE/RAMA-HERO-PROVENANCE.json').read_text())
ck('five-stage exact proposal validates',len(v['authoringStages'])==5)
ck('66 exact sources',len(v['sources'])==66)
ck('review status and optional shader exclusions remain',m['status']=='review-proposal-not-promoted' and m['optional_shader']['included'] is False)
ck('all promotion bytes match manifest',all(p.record(proposal/path)==r for path,r in m['promotion_files'].items()))
ck('approved lifecycle dependency exact',v['sources']['scripts/rama_secondary_motion.gd']['sha256']=='2b8e467df254dcda175694ab988071f24b41ddaa93275f5cbb9768abcb143f34')
ck('preserved runtime dependencies excluded from promotion',not set(m['preserved_runtime_sources']).intersection(m['promotion_files']))
ck('original asset proposal package support remains pinned to pre-fix review',m['package_support']['tools/package-native.py']['sha256']=='3552b25fe37453ffa7ad129d90eca8dabf37928027a691aa9e3abf8c17fe2cbd')
ck('separate corrected package support exact',p.digest(root/'tools/package-native.py')=='6dac20395c4e274f752b3d50d452dccf4c69522b88a9cdbfa2cf7a7474073d84')
for level in ('near','mid','far'):
 cost=v['authoringStages'][-1]['costs'][level];ck(level+' original binary prefix and nonhair exact',cost['original_binary_prefix_exact'] and cost['nonhair_json_exact'])
base=n['authoringStages'][-1]
for name,mutate in [('missing approved lifecycle dependency',lambda s:s.update(runtimeSources=[])),('wrong lifecycle identity',lambda s:s['runtimeSources'][0].update(sha256='0'*64)),('wrong R2 parent',lambda s:s.update(inputAssetSha256='0'*64)),('invented editable modeling ancestry',lambda s:s.update(editableOrigin='native-modeling-stack')),('rebound far LOD',lambda s:s['runtimeLods'][-1].update(sha256='0'*64))]:
 changed=copy.deepcopy(base);mutate(changed);rejects(name,lambda:p._validate_rama_groom_stage(proposal,changed,n['authoringStages'][:-1],dict(v['sources'])))
with tempfile.TemporaryDirectory(prefix='r7-independent-paths-') as folder:
 t=Path(folder);r=t/'root';r.mkdir();o=t/'outside';o.mkdir();data=b'independent source witness';(o/'same').write_bytes(data);sha=hashlib.sha256(data).hexdigest();(r/'escape').symlink_to(o,target_is_directory=True)
 for path in ['escape/same','../outside/same',str(o/'same'),'..\\outside\\same']:rejects('matching bytes reject unsafe path '+path,lambda path=path:p._rama_source(r,path,sha))
 (r/'inside').write_bytes(data);ck('direct internal path accepts',p._rama_source(r,'inside',sha)['sha256']==sha)
font='assets/fonts/NotoSans-Regular.ttf';target='res://.godot/imported/NotoSans-Regular.ttf-'+'a'*32+'.fontdata';keys=f'importer="font_data_dynamic"\ntype="FontFile"\npath="{target}"\n'
ck('valid remap control accepts',p._font_import_target(('[remap]\n'+keys).encode(),font)==target)
for name,data in [('all keys in deps','[deps]\n'+keys),('path in deps','[remap]\nimporter="font_data_dynamic"\ntype="FontFile"\n[deps]\npath="'+target+'"\n'),('duplicate remap sections','[remap]\n'+keys+'[remap]\n'),('default-only keys','[DEFAULT]\n'+keys+'[remap]\n'),('other-section duplicate path','[remap]\n'+keys+'[deps]\npath="'+target+'"\n'),('no section',keys)]:rejects('font descriptor rejects '+name,lambda data=data:p._font_import_target(data.encode(),font))
f=Path('/workspace/scratch/visual-round3/role-14/font-export-r2');bindings=json.loads((f/'font-bindings.json').read_text());pack=p.inspect_pack(f/'structural-native-with-real-fonts.pck');ck('real cold-export payloads qualify',p.qualify_bundled_font_package(pack,bindings)['all_three_exact_font_payloads_present'])
for name,mutate in [('forged decoded TTF',lambda b:b['imports'][font]['decoded_raw_ttf'].update(sha256='0'*64)),('wrong resource basename',lambda b:b['imports'][font]['resource'].update(path=b['imports'][font]['resource']['path'].replace('NotoSans','NotoSerif')))]:
 b=copy.deepcopy(bindings);mutate(b);rejects(name,lambda:p.qualify_bundled_font_package(pack,b))
result={'task':'R3-09 independent final R3-14 package review','passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'proposal':str(proposal),'proposal_sha256':p.digest(proposal/'promotion-manifest.json'),'notice_sha256':p.digest(proposal/'NOTICE/RAMA-HERO-PROVENANCE.json'),'package_sha256':p.digest(root/'tools/package-native.py'),'probe_sha256':p.digest(Path(__file__)),'scope':'Independent exact proposal/source preservation, ancestry/path and font descriptor/runtime identity adversaries. Actual cold export is author evidence, read and independently qualified here; no import or export performed by this probe. Art and motion decisions separate.'}
(out/sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks),'failures':[c for c in checks if not c['passed']]}))
