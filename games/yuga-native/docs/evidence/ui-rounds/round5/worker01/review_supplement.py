"""Evidence checks for originals independently opened in the U5 supplement."""
from pathlib import Path
from PIL import Image
import hashlib,json,shutil
OUT=Path(__file__).parent
CAP=Path('/tmp/yuga-u5-integrated-window-r2')
FREEZE=Path('/tmp/yuga-u5-source-r2/ANDOLAN/games/yuga-native')
SEEN=['01-repaired-source-title','02-guide-save-status-visible','03-help-fresh-header','05-help-reopened-header','06-settings-fixed-done','07-night-world-pause','14-training-before-duel','15-training-selection-after-duel']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=json.loads((CAP/'run.json').read_text());shots={};records={};checks=[]
def ck(name,ok):checks.append({'name':name,'passed':bool(ok)})
(OUT/'supplement-originals').mkdir(exist_ok=True)
for name in SEEN:
    shots[name]=json.loads((CAP/(name+'.json')).read_text())
    records[name]={'png_sha256':sha(CAP/(name+'.png')),'metadata_sha256':sha(CAP/(name+'.json')),'pixels':list(Image.open(CAP/(name+'.png')).size)}
    for extension in ['.png','.json']:shutil.copyfile(CAP/(name+extension),OUT/'supplement-originals'/(name+extension))
ck('supplement exact final U5 freeze',sha(FREEZE/'ui-source-freeze.json')=='0f4871dd0b09cca7f240454f33016bbe154567f0840fc15d6e7f164c3871666f')
ck('complete native Quit0 supplement with stable source',run['complete'] and run['verified_exit_code']==0 and run['source_unchanged'])
ck('eight opened originals retain exact recorded SHA and 960x540 content pixels',all(records[n]['png_sha256']==shots[n]['sha256'] and records[n]['pixels']==[960,540] for n in SEEN))
ck('Help fresh and reopened entries return scroll to zero',all(shots[n]['modal_scroll']['help_panel']==0 and shots[n]['focus_text']=='BACK' for n in ['03-help-fresh-header','05-help-reopened-header']))
ck('native film round trip preserves selected training and returns primary focus',shots['14-training-before-duel']['launch']['selected_mode']==shots['15-training-selection-after-duel']['launch']['selected_mode']=='train' and shots['15-training-selection-after-duel']['focus_text']=='Begin bow training  →')
ck('returned title has no active transition owner and one idle loader',shots['15-training-selection-after-duel']['loader_count']==1 and not shots['15-training-selection-after-duel']['transition_owner_present'] and not shots['15-training-selection-after-duel']['transition']['busy'])
result={'passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'opened':SEEN,'originals':records,'run_sha256':sha(CAP/'run.json'),'freeze_sha256':sha(FREEZE/'ui-source-freeze.json'),'sources':run['source_sha256'],'scope':'Six grouped evidence checks on eight actually opened supplemental originals. Native window960x600; raw image960x540. Pixels establish bounded visibility, not accessibility semantics or overview clock behavior.'}
(OUT/'capture-audit-r2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks)}))
