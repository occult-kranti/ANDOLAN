#!/usr/bin/env python3
"""Private motion-only runtime overlay; no import or engine launch."""
from pathlib import Path
import importlib.util,json,os,shutil
repo=Path('/workspace/ANDOLAN');native=repo/'games/yuga-native'
owner=Path(__file__).resolve().parent
prep=owner.parent/'W5-locomotion-current-r1'
base=Path('/workspace/scratch/yuga-locomotion-current-r1/project')
root=Path('/workspace/scratch/yuga-landing-preparation-candidate-r2')
assert not root.exists()
spec=importlib.util.spec_from_file_location('snapshot',prep/'snapshot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
parent=m.verify(base)
assert m.digest(base/m.MARKER)=='32341fc8d983081ce56298d3ef721724c96d7c01391ccd02564715fdf9b39953'
assert shutil.disk_usage(root.parent).free>=(500+96)*1024**2
project=root/'project';project.mkdir(parents=True)
overlays={'scripts/rama_motion.gd':owner/'rama_motion.gd'}
expected=dict(parent['files']);expected.update({n:m.metadata(p) for n,p in overlays.items()})
for name in sorted(expected):
    target=project/name;target.parent.mkdir(parents=True,exist_ok=True)
    if name in overlays or name in m.AUX_FILES:shutil.copyfile(overlays.get(name,base/name),target)
    else:os.link(base/name,target)
record=dict(parent)
record.update(project=str(project),files=expected,round='private-landing-prepare-r1',previous_marker_sha256=m.digest(base/m.MARKER),source_bytes=sum(v['bytes'] for n,v in expected.items() if not n.startswith('.godot/')))
record['common_harness_overlay']=dict(parent.get('common_harness_overlay',{}));record['common_harness_overlay'].update({n:expected[n] for n in overlays})
(project/m.MARKER).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
m.verify(project);m.verify(base)
pair=json.load(open(base.parent/'stage.json'));pair['stages']['current']={'project':str(project),'seal_sha256':m.digest(project/m.MARKER)}
pair['scope']='Private candidate changes only motion; natural helper/inputs and authority identical to parent.'
(root/'stage.json').write_text(json.dumps(pair,indent=2,sort_keys=True)+'\n')
inputs=json.load(open(base.parent/'render-inputs.json'));inputs['pair_sha256']=m.digest(root/'stage.json')
(root/'render-inputs.json').write_text(json.dumps(inputs,indent=2,sort_keys=True)+'\n')
receipt={'parent_marker':m.digest(base/m.MARKER),'candidate_marker':m.digest(project/m.MARKER),'changed_files':{n:expected[n] for n in overlays},'runtime_change_only':'scripts/rama_motion.gd','helper_and_inputs_unchanged':True,'private_hardlinked_stage':str(project),'free_bytes':shutil.disk_usage(project).free,'source_before':m.digest(native/'scripts/rama_motion.gd')}
(owner/'stage.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
