#!/usr/bin/env python3
"""Publish only the exact qualified held polish draft after root's explicit flag."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
R=Path('/workspace/ANDOLAN');HERE=Path(__file__).resolve().parent
BASE=R/'games/yuga-native/docs/evidence/desktop-finish/continuation-oct18'
SOURCE='79e5c15d8a3657e16fda67acb277b2406120dcd1';TAG='yuga-desktop-polish-2026-10-18';ID=416542426
BRANCH='transport/yuga-desktop-polish-2026-10-18-r2'
ASSETS=Path('/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2/build')
PINS={'W6-package-r2/qualification-receipt-uid-reviewed.json':'e924d90af27dad48c96fcb99ad9bbbe2cfd84ac01899b2221491199baf00f400','W1-actual-r1/package-successor-r2/receipt.json':'b7a3f90433247072d68b34ee7f3b03a73edca69ded4cb561d144591f687533d3','W2-package-successor-r2/receipt.json':'7f07078258afcf4eb4fbde40b383db3f01b7473b79fef428c2377e20a148b3bd','W6-integration-r1/package-native-independent-r2.json':'bab4255a670a864d8ad76e1ded101139d5b9c1a2379c2d82e3f760c1cf48afb6'}
def require(value,message):
 if not value:raise ValueError(message)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def api(path,*args):return subprocess.check_output(['gh','api',path,*args],cwd=R)
def save(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
def identity(d,expected,draft):
 require(d['id']==ID and d['tag_name']==TAG and d['target_commitish']==SOURCE and d['draft'] is draft and d['prerelease'],'Exact release identity/state')
 require(len(d['assets'])==5 and {a['name'] for a in d['assets']}==set(expected),'Exact five asset names')
 for a in d['assets']:
  p=expected[a['name']];require(a['state']=='uploaded' and a['size']==p['bytes'] and a['digest']=='sha256:'+p['sha256'],'Exact uploaded asset '+a['name'])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--publish-qualified-draft',action='store_true');p.add_argument('--upload-run',type=int);p.add_argument('--transport-commit');a=p.parse_args()
 require(a.publish_qualified_draft and a.upload_run and re.fullmatch('[0-9a-f]{40}',a.transport_commit or ''),'Explicit publication and exact upload-run/transport-commit required')
 require(not (HERE/'publication-response.json').exists(),'Do not repeat publication')
 require(subprocess.check_output(['git','--no-optional-locks','rev-parse','HEAD'],cwd=R,text=True).strip()==SOURCE,'Frozen qualified source HEAD')
 for rel,digest in PINS.items():require(sha(BASE/rel)==digest,'Exact qualification receipt '+rel)
 q=json.loads((BASE/'W6-package-r2/qualification-receipt-uid-reviewed.json').read_text());require(q['passed'] and q['source_commit']==SOURCE and len(q['checks'])==40 and all(c['passed'] for c in q['checks']),'40 archive gates')
 owner=json.loads((BASE/'W1-actual-r1/package-successor-r2/receipt.json').read_text());require(owner['source']==SOURCE and owner['disposition'].startswith('PASS') and owner['originals']['total']==28,'Native owner scope')
 for phase,record in owner['phase_receipts'].items():
  f=BASE/'W1-actual-r1/package-successor-r2'/record['path'];require(sha(f)==record['sha256'],'Bound native phase');d=json.loads(f.read_text());require(d['passed'] and d['native_exit']==0 and all(d['validation_checks'].values()),'Actual native phase pass')
 independent=json.loads((BASE/'W2-package-successor-r2/receipt.json').read_text());require(independent['status']=='SCOPED_EXACT_LINUX_PACKAGE_INDEPENDENT_VISUAL_PASS' and independent['source_commit']==SOURCE and independent['direct_full_original_count']==28 and not independent['correction_required'],'Independent all-original acceptance')
 ci=json.loads(api('repos/occult-kranti/ANDOLAN/actions/runs/39139568524'));require(ci['head_sha']==SOURCE and ci['status']=='completed' and ci['conclusion']=='success','Exact source CI success');save('source-ci-final.json',ci)
 expected=q['five_assets'];require(len(expected)==5,'Five independently qualified assets')
 for n,v in expected.items():require((ASSETS/n).stat().st_size==v['bytes'] and sha(ASSETS/n)==v['sha256'],'Unchanged local qualified asset '+n)
 workflow=json.loads(api('repos/occult-kranti/ANDOLAN/actions/runs/'+str(a.upload_run)));require(workflow['status']=='completed' and workflow['conclusion']=='success' and workflow['head_sha']==a.transport_commit and workflow['head_branch']==BRANCH and workflow['event']=='push','Exact successful upload workflow');save('upload-run-final.json',workflow)
 endpoint='repos/occult-kranti/ANDOLAN/releases/'+str(ID);draft=json.loads(api(endpoint));identity(draft,expected,True);save('draft-before-publication.json',draft)
 body=(HERE/'release-notes.md').read_text();require('must pass before' not in body and '{{' not in body,'Final release notes')
 request={'tag_name':TAG,'target_commitish':SOURCE,'name':'YUGA desktop polish preview','body':body,'draft':False,'prerelease':True,'make_latest':'false'};save('publication-request.json',request)
 raw=api(endpoint,'--method','PATCH','--input',str(HERE/'publication-request.json'));(HERE/'publication-response.json').write_bytes(raw);published=json.loads(raw);identity(published,expected,False);require(published['published_at'],'Public timestamp')
 save('publication-receipt.json',{'passed':True,'source_commit':SOURCE,'tag':TAG,'release_id':ID,'url':published['html_url'],'published_at':published['published_at'],'upload_run':a.upload_run,'transport_commit':a.transport_commit,'qualification_pins':PINS,'assets':expected,'independent_public_download':'Pending separate W3 verification; no public bytes inferred from metadata'})
 print(json.dumps({k:published[k] for k in ['id','html_url','tag_name','target_commitish','draft','published_at']},indent=2))
if __name__=='__main__':main()
