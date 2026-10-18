#!/usr/bin/env python3
"""Copy one verified current presentation into a motion-only pair. No engine."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

PINS = {'baseline': '119db2e65a40c148725813137340bc109f057d98ea82ef777ab7735c999c661c',
        'candidate': '8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'canonical', 'seed', 'output', 'receipt'):
        ap.add_argument('--'+name, type=Path, required=True)
    args = ap.parse_args()
    base, canonical, seed, output, receipt = [getattr(args, n).resolve() for n in ('base','canonical','seed','output','receipt')]
    if output.exists() or receipt.exists() or base in output.parents or canonical in output.parents:
        ap.error('Use fresh output/receipt outside input trees')
    if shutil.disk_usage(output.parent).free < 4*1024**3:
        ap.error('Need at least4GiB before preparing pair, retaining3GiB floor')
    spec = importlib.util.spec_from_file_location('snapshot', canonical/'tools/graphics-six/snapshot.py')
    snapshot = importlib.util.module_from_spec(spec); spec.loader.exec_module(snapshot)
    upstream = snapshot.verify(base)
    upstream_pin = sha(base/snapshot.MARKER)
    helper = Path(__file__).with_name('capture_transition.gd')
    focus = canonical/'tools/graphics-six/capture_focus.gd'
    if sha(focus) != '307edf74d143d0d8de2a2c7b2bb9f3b31ffb052bb370cf84bcb83dade02e1e74':
        ap.error('Corrected focus helper differs from reviewed input')
    motions = {'baseline': canonical/'docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd',
               'candidate': canonical/'scripts/rama_motion.gd'}
    if any(sha(motions[k]) != pin for k,pin in PINS.items()):
        ap.error('Motion identity changed')
    seed_files = {str(p.relative_to(seed)): {'sha256':sha(p),'bytes':p.stat().st_size}
                  for p in seed.rglob('*') if p.is_file()}
    if not seed_files or any(not name.endswith('.cache') for name in seed_files):
        ap.error('Only a nonempty recovered Godot shader-cache seed is admitted')
    output.mkdir()
    store = output/'import-store'; (store/'imports').mkdir(parents=True)
    stages = {}
    for role in PINS:
        stage = output/role/'project';stage.mkdir(parents=True)
        for name,item in upstream['files'].items():
            target = stage/name;target.parent.mkdir(parents=True,exist_ok=True)
            if name.startswith('.godot/imported/'):
                blob = store/'imports'/item['sha256']
                if not blob.exists():
                    shutil.copyfile(base/name,blob);blob.chmod(0o444)
                os.link(blob,target)
            else:
                shutil.copyfile(base/name,target)
        shutil.copyfile(motions[role],stage/'scripts/rama_motion.gd')
        shutil.copyfile(focus,stage/'tools/graphics-six/capture_focus.gd')
        shutil.copyfile(helper,stage/'tools/graphics-six/capture_transition.gd')
        files = snapshot.inventory(stage)
        record = dict(upstream)
        record.update(round='G2-S3-motion-'+role,source=str(base),project=str(stage),store=str(store),
                      previous_receipt_sha256=upstream_pin,files=files,canonical_files=upstream['files'],
                      changed_paths=sorted(k for k in files.keys()|upstream['files'].keys() if files.get(k)!=upstream['files'].get(k)),
                      validated_imports=snapshot.imports(stage),
                      source_bytes=sum(v['bytes'] for k,v in files.items() if not k.startswith('.godot/')),
                      compiled_bytes=sum(v['bytes'] for k,v in files.items() if k.startswith('.godot/imported/')),
                      scope='Verified current presentation successor copied into a motion-only pair. Imported bytes share a private readonly store; warm shader caches are private copies. No import/render.')
        (stage/snapshot.MARKER).write_text(json.dumps(record,indent=2)+'\n')
        snapshot.verify(stage)
        warm = output/role/'seed/godot'
        shutil.copytree(seed,warm)
        copied = {str(p.relative_to(warm)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in warm.rglob('*') if p.is_file()}
        if copied != seed_files:
            raise RuntimeError('Private cache copy differs')
        stages[role]={'project':str(stage),'seal_sha256':sha(stage/snapshot.MARKER),'motion_sha256':PINS[role],
                      'godot_seed':str(warm),'mesa_seed':None,'files':files,'import_count':len(record['validated_imports'])}
    differences = sorted(k for k in stages['baseline']['files'].keys()|stages['candidate']['files'].keys()
                         if stages['baseline']['files'].get(k)!=stages['candidate']['files'].get(k))
    if differences != ['scripts/rama_motion.gd']:
        raise RuntimeError('Unexpected pair difference '+str(differences))
    if sha(base/snapshot.MARKER)!=upstream_pin or snapshot.inventory(base)!=upstream['files']:
        raise RuntimeError('Shared upstream changed during copy')
    old = json.loads((canonical/'docs/evidence/desktop-finish/S2/W1/scene-anchors-r1/source/snapshot.json').read_text())
    ancestry = sorted(k for k in upstream['files'].keys()|old['files'].keys() if upstream['files'].get(k)!=old['files'].get(k))
    result={'complete':True,'upstream':str(base),'upstream_seal_sha256':upstream_pin,'current_presentation_changes_from_historical_S2':ancestry,
            'pair_differences':differences,'helper_sha256':sha(helper),'focus_sha256':sha(focus),'stages':stages,
            'godot_seed_source':str(seed),'godot_seed_files':seed_files,'mesa_seed_status':'No recovered Mesa seed; each run starts its own empty Mesa cache.',
            'disk_budget_bytes':2*1024**3,'required_free_floor_bytes':3*1024**3,
            'capture_status':'Not executed; actual render needs root lane authorization.'}
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    (output/'pair.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'complete':True,'pair':str(output),'differences':differences,'seed_files':len(seed_files),'projects':{k:v['project'] for k,v in stages.items()}}))


if __name__ == '__main__':
    main()
