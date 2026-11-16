#!/usr/bin/env python3
"""Archive the exact exported runtime sources and original Sangam authoring files."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot-root',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args = parser.parse_args()
    root = args.snapshot_root.resolve()
    native = root/'games/yuga-native'
    exported = json.loads((args.build_dir/'native-export-manifest.json').read_text())
    source = exported['source']
    paths = [native/p for p in source['files']]
    paths += [p for p in (native/'NOTICE').rglob('*') if p.is_file()]
    paths += [native/'art/.gdignore']
    paths += [native/'art/sangam-district'/n for n in ['sangam-district.blend','manifest.json','coplanar-audit.json']]
    paths += [root/'tools/studio/build_sangam_district.py']
    records = {str(p.relative_to(root)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in paths}
    if not all(records['games/yuga-native/'+p]==v for p,v in source['files'].items()):
        raise ValueError('Runtime source differs from the exported source identity')
    identity = {'scope':'Runnable Godot4.6.3 project and original Sangam Blender source, retaining repository layout. Canonical audited package regeneration additionally needs existing historical art/provenance closure retained in frozen snapshot.','baseline_commit':exported['git']['head'],'runtime_source_sha256':source['sha256'],'files':records,'run':'godot --path games/yuga-native','authoring':'blender4.3 --background --threads 8 --python tools/studio/build_sangam_district.py','note':'Isolated candidate; parallel live worker files were not overwritten.'}
    with zipfile.ZipFile(args.output,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(paths): archive.write(path,str(path.relative_to(root)))
        archive.writestr('SOURCE-IDENTITY.json',json.dumps(identity,indent=2)+'\n')
        archive.writestr('START-HERE.txt','YUGA native video-panel source checkpoint\nGodot4.6.3: godot --path games/yuga-native\nOffline Confluence and bow training. LMB/Q/E/C/X; R reload; F4 field shop at Sun base; F3 guide; F2 keys; Escape pause; F5 reset.\nOriginal Blender source: games/yuga-native/art/sangam-district/sangam-district.blend\nArt stays excluded from Godot imports; runtime uses the provided original GLB.\nNative online/roster, final art/motion, human playtests and hardware qualification remain open. See bundled notices.\n')
    with zipfile.ZipFile(args.output) as archive:
        if archive.testzip() is not None: raise ValueError('Archive CRC mismatch')
        for path,record in records.items():
            if hashlib.sha256(archive.read(path)).hexdigest()!=record['sha256']: raise ValueError('Source archive payload mismatch: '+path)
    if not all(digest(root/path)==record['sha256'] for path,record in records.items()): raise ValueError('Source changed during archiving')
    receipt = {'file':str(args.output),'bytes':args.output.stat().st_size,'sha256':digest(args.output),'runtime_source_sha256':source['sha256'],'all_source_payloads_verified':True,'source_records':len(records),'tool_sha256':digest(Path(__file__))}
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':
    main()
