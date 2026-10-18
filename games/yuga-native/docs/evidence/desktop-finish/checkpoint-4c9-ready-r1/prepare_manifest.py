#!/usr/bin/env python3
"""Produce a file-only checkpoint allowlist from explicitly sealed owner packets."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[6]
PROJECT = ROOT / 'games/yuga-native'
DEST = PROJECT / 'docs/evidence/desktop-finish/checkpoint-4c9-ready-r1'
chosen = {}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def add(path, owner):
    path = Path(path)
    if not path.is_absolute():
        path = PROJECT / path
    if '__pycache__' in path.parts or path.suffix == '.pyc':
        return
    if path.is_symlink() or not path.is_file() or not path.is_relative_to(ROOT):
        raise ValueError(f'Invalid sealed path: {path}')
    if path.suffix == '.uid':
        raise ValueError(f'Unexpected generated UID in new packet: {path}')
    chosen[str(path.relative_to(ROOT))] = owner

def closed_dir(name, owner):
    path = PROJECT / name
    assert path.is_dir(), path
    for f in sorted(path.rglob('*')):
        if f.is_file():
            add(f, owner)

def owner_receipt(name, key, scope, repository_paths=False):
    path = PROJECT / name
    data = json.loads(path.read_text())
    for name, pin in data[key].items():
        file = ROOT / name if repository_paths else path.parent / name
        checksum = pin if isinstance(pin, str) else pin['sha256']
        assert sha(file) == checksum, file
        if isinstance(pin, dict) and 'bytes' in pin:
            assert file.stat().st_size == pin['bytes'], file
        add(file, scope)
    add(path, scope)

for name in ['README.md','docs/START_HERE.md','docs/WORKSPACE_AND_CLEANUP.md',
             'docs/evidence/desktop-finish-historical-public-cleanup.json',
             'docs/evidence/desktop-finish-historical-public-cleanup-W6.json']:
    add(ROOT / name, 'lead-docs-and-bounded-historical-cleanup')
for name in ['README.md','docs/ACTIVE_DESKTOP_HANDOFF.md','docs/DESKTOP_FINISH_CAMPAIGN.json',
             'docs/DESKTOP_FINISH_CAMPAIGN.md']:
    add(name, 'lead-docs-ledger')
for name in ['scripts/confluence_world.gd','scripts/launch_shell.gd','scripts/rama_ability_effects.gd',
             'tests/desktop_d01_title_identity_cases.gd','tests/desktop_i02_volley_feedback_cases.gd',
             'tests/desktop_world_compact_first_entry_cases.gd','tests/visual_catalog_cases.py',
             'tests/ui_campaign_capture_tool_cases.py','tools/graphics-six/run_focus.py',
             'tools/run-visual-checks.py','tools/ui-campaign/README.md','tools/ui-campaign/observer.gd',
             'tools/ui-campaign/run.py','tools/ui-campaign/desktop-journey-plan.json',
             'tools/ui-campaign/preflight_journey.gd']:
    add(name, 'sealed-runtime-tests-capture-catalog')
for name in ['D01/W2.md','S4/W2-diadem-review-r1.json','S4/W2-diadem-review-r1.md']:
    add('docs/evidence/desktop-finish/' + name, 'sealed-independent-review')
for name in [
    'D01/W2','D01/lead-title-review-r1','D04-I02/W5',
    'D09/W1-current-screens-r1','D09/W1-current-screens-r2',
    'G0/template-baseline-cold-600-r1','G0/paving-pair-staging-r1',
    'G0/title-floor-normal-staging-r1','G0/W1-paving-pair-r1','G0/W1-title-floor-normal-r1','S3/W1-landing-sampled-review-r1',
    'S3/W5-actual-motion-r1','S4/W1-diadem-r1','journey-preparation/W1',
    'journey-preparation/W6','journey-successor/W6','journey-successor/W6-native',
    'journey-successor/W1-native-r1','D02/W1-boot-recovery-r1',
    'world-first-compact-entry/W4','world-first-compact-entry/W4-native-r2']:
    closed_dir('docs/evidence/desktop-finish/' + name, 'sealed-evidence:' + name)
owner_receipt('docs/evidence/desktop-finish/S4/W2-smooth-r1/receipt.json','files',
              'inactive-smooth-crown-source-only',True)
owner_receipt('art/hero-finish/s5-shoulder-armour/receipt.json','files',
              'inactive-shoulder-r4-source-only-action-clearance-failed')
for name in ['slab-distance-filter-r1','title-floor-stipple-r1','roof-loggia-r1']:
    owner_receipt('art/world-finish/' + name + '/receipt.json','artifacts',
                  'inactive-art-candidate:' + name)
add(Path(__file__), 'W6-exact-allowlist-preparation')
for name, expected in {
    'scripts/confluence_world.gd':'6e9d88657b5b3a69b67e0bc93e4f45988faa65d5206d9cabdaea45543e2d19bf',
    'scripts/launch_shell.gd':'794266aa6b559e128b0eb1d61b4a019d65dd5f46593fa275a0ed48cda31a858e',
    'scripts/rama_ability_effects.gd':'119353e71e5ad1eee61360d52db036075a6be60ec30c4c2ee228b5656243db66',
    'tools/graphics-six/run_focus.py':'6c7dab63f58ce339de569dcb4f9f7b33bafc94842f069e470fa9c32b92c432aa',
    'tools/ui-campaign/run.py':'322e919185825c5b6bd49911fbe2b64b70a2149ffbb0199958e98c45ce22763d',
    'tools/run-visual-checks.py':'399bc03ca195d3000a72fb3c59231cbb30b2d5b02ab7b7ca08f213c30bd0cc5a',
    'docs/evidence/desktop-finish/journey-successor/W1-native-r1/receipt.json':'483956a910d5ff96370bffdb62773d754c49f84eb33632d407ecc7e2cb29f7db',
    'docs/evidence/desktop-finish/D02/W1-boot-recovery-r1/receipt.json':'0f6e141ab78897ae0809adb6042215b0d0ee23e611451c85796c1148e3d4021e',
    'docs/evidence/desktop-finish/G0/W1-paving-pair-r1/receipt.json':'86360980fd192dd587b7e44a56829ab4dc0364769d90c65f1d86deb5032d485d',
    'docs/evidence/desktop-finish/G0/W1-title-floor-normal-r1/receipt.json':'67005f2bb172e0c29745afb9c9291f54c96b12936be7ef48fa74d3e090601d9e',
}.items():
    assert sha(PROJECT / name) == expected, name

tracked = set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines())
changed = set(subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).splitlines())
ready = sorted(name for name in chosen if name not in tracked or name in changed)
ignored = set(subprocess.run(['git','check-ignore','--stdin'],input='\n'.join(ready)+'\n',
                             cwd=ROOT,text=True,capture_output=True,check=False).stdout.splitlines())
files = {}
for name in ready:
    f = ROOT / name
    assert f.stat().st_size < 100_000_000, f
    files[name] = dict(sha256=sha(f),bytes=f.stat().st_size,mode=oct(f.stat().st_mode & 0o777),
                       owner_scope=chosen[name],requires_scoped_force_add=name in ignored)
report = dict(schema=1,base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              scope='Exact completed working-tree delta only. No staging/commit, source activation or whole-round acceptance. '
                    'Raw images kept once per central archive; inactive art candidates retain limits.',
              files=files,unchanged_selected_files_omitted=sorted(set(chosen)-set(ready)),
              count=len(files),bytes=sum(v['bytes'] for v in files.values()),
              ignored_paths=sorted(ignored),
              exclusions=['.design','scratch','canonical generated .uid','__pycache__','old ready-manifest-draft.json',
                          'new hair experiment','shoulder articulated-r5','new W5 motion experiment',
                          'unsealed art imports/raster'],
              self_metadata=['ready-manifest.json','README.md','ready-paths.txt','link-audit.json'])
(DEST/'ready-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
metadata=[str((DEST/name).relative_to(ROOT)) for name in report['self_metadata']]
(DEST/'ready-paths.txt').write_text('\n'.join(ready+metadata)+'\n')
print(json.dumps(dict(files=len(files),bytes=report['bytes'],ignored=len(ignored),
                      manifest_sha256=sha(DEST/'ready-manifest.json'))))
