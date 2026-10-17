#!/usr/bin/env python3
"""Freeze exact Git runtime blobs plus explicitly named diagnostic harnesses."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--commit', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--harness', type=Path, required=True)
    a = p.parse_args()
    repo, output = a.repo.resolve(), a.output.resolve()
    assert a.output.is_absolute() and not output.exists(), 'Fresh absolute output required'
    prefix = 'games/yuga-native/'
    commit = subprocess.check_output(['git','rev-parse',a.commit], cwd=repo, text=True).strip()
    paths = subprocess.check_output(['git','ls-tree','-rz','--name-only',commit], cwd=repo).split(b'\0')
    sources = {}
    for raw in paths:
        name = raw.decode()
        if not name.startswith(prefix): continue
        relative = name[len(prefix):]
        if relative != 'project.godot' and not relative.startswith(('assets/','scripts/','shaders/','scenes/','tools/','art/world/')): continue
        if 'node_modules' in Path(relative).parts: continue
        data = subprocess.check_output(['git','show',f'{commit}:{name}'], cwd=repo)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        sources[relative] = hashlib.sha256(data).hexdigest()
    assert sources and all(sha(output/k) == v for k,v in sources.items())
    native = repo / prefix
    cache = native / '.godot'
    assert cache.is_dir(), 'A validated existing import cache is required'
    before = {str(p.relative_to(cache)):sha(p) for p in cache.rglob('*') if p.is_file()}
    shutil.copytree(cache, output/'.godot')
    assert before == {str(p.relative_to(cache)):sha(p) for p in cache.rglob('*') if p.is_file()}, 'Cache changed during copy'
    assert before == {str(p.relative_to(output/'.godot')):sha(p) for p in (output/'.godot').rglob('*') if p.is_file()}
    imports = []
    for path in output.rglob('*.import'):
        if '.godot' in path.parts: continue
        txt = path.read_text()
        match = re.search(r'^path="res://(.*?)"', txt, re.M)
        source = path.with_suffix('')
        if not match or not source.is_file(): continue
        imported = output / match[1]
        md5 = imported.with_suffix('.md5')
        if not md5.is_file():
            candidates = list(imported.parent.glob(imported.stem.split('.')[0]+'.md5'))
            md5 = candidates[0] if len(candidates)==1 else md5
        assert imported.is_file() and md5.is_file(), f'Missing imported output: {path}'
        match_md5 = re.search(r'source_md5="([0-9a-f]+)"', md5.read_text())
        assert match_md5 and match_md5[1] == hashlib.md5(source.read_bytes()).hexdigest(), f'Stale import: {source}'
        imports.append({'source':str(source.relative_to(output)), 'imported':match[1], 'source_md5':match_md5[1]})
    harness = {}
    for src in sorted(a.harness.resolve().glob('*')):
        if src.is_file() and src.suffix in ('.py','.gd','.md','.json'):
            relative = 'tools/visual-rounds/'+src.name
            dst = output/relative; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
            harness[relative] = sha(dst)
    manifest = {'complete':True,'base_commit':commit,'origin_project':str(native),'source_sha256':sources,'harness_sha256':harness,'cache_files':len(before),'validated_imports':imports,'scope':'Exact Git runtime snapshot; declared diagnostic tools are the only additions. No credentials, evidence or user saves copied.'}
    (output/'candidate-origin.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'complete':True,'source_files':len(sources),'cache_files':len(before),'validated_imports':len(imports),'output':str(output)}))

if __name__ == '__main__': main()
