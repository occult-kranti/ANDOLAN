#!/usr/bin/env python3
import json,os,pathlib,sys
if '--version' in sys.argv:
 print('4.6.3.stable.fixture');raise SystemExit(0)
r=pathlib.Path(next(a.split('=',1)[1] for a in sys.argv if a.startswith('--report=')))
mode=os.environ['YUGA_RUNNER_FIXTURE_MODE']
checks=[] if mode=='empty' else [{'name':'orchestration fixture only','passed':mode!='contradictory'}]
r.write_text(json.dumps({'passed':True,'checks':checks,'fixture_only':True,'xdg':{k:os.environ[k]for k in ['XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME']}}))
if mode=='engine-error':print('ERROR: intentional orchestration fixture')
raise SystemExit(1 if mode=='nonzero' else 0)
