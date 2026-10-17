#!/usr/bin/env python3
"""Exercise actual publish title selection using mocked local-only transport."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,importlib.util,json,shutil,subprocess,tempfile
PROJECT=Path('/workspace/ANDOLAN/games/yuga-native')
spec=importlib.util.spec_from_file_location('release_title_under_test',PROJECT/'tools/release-native.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
checks=[]
for suffix,title in [('yuga-traversal-armies-fixture-mythic','YUGA mythic invocations — native preview'),('yuga-traversal-armies-fixture','YUGA traversal and lane armies — native preview'),('yuga-traversal-armies-fixture-siege','YUGA traversal and lane armies — native preview'),('yuga-traversal-armies-fixture-triad','YUGA traversal and lane armies — native preview'),('yuga-confluence-duel-fixture','YUGA Confluence duel — native preview')]:
 with tempfile.TemporaryDirectory(prefix='yuga-release-title-fixture-') as tmp:
  directory=Path(tmp);(directory/'RELEASE-NOTES.md').write_text('Synthetic local title fixture.');calls=[]
  def run(argv,**kwargs):
   calls.append(argv)
   if argv[:2]==['gh','api']:return subprocess.CompletedProcess(argv,1,stdout='',stderr='HTTP 404')
   if argv[:3]==['gh','release','download']:
    target=Path(argv[argv.index('--dir')+1]);shutil.copy2(directory/'RELEASE-NOTES.md',target/'RELEASE-NOTES.md')
   return subprocess.CompletedProcess(argv,0,stdout='',stderr='')
  with patch.object(release,'verify',return_value={'passed':True}),patch.object(release,'git',return_value='a'*40),patch.object(release,'verify_remote_tag'),patch.object(release.subprocess,'run',side_effect=run):
   result=release.publish(SimpleNamespace(directory=directory,tag=suffix,commit='a'*40,repository='fixture/repository'))
  creates=[argv for argv in calls if argv[:3]==['gh','release','create']]
  actual=creates[0][creates[0].index('--title')+1] if len(creates)==1 else None
  checks.append({'tag':suffix,'passed':result['published'] and actual==title,'expected_title':title,'actual_title':actual})
report={'passed':all(c['passed'] for c in checks),'checks':checks,'validator_sha256':hashlib.sha256((PROJECT/'tools/release-native.py').read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Actual publish control flow and title selection exercised with mocked Git, archive verification and subprocess transport. No GitHub request, release, upload or publication was performed.'}
Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
