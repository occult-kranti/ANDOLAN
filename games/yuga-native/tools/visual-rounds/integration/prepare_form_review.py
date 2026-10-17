#!/usr/bin/env python3
"""Assemble complete schema3 provenance in a fresh external review directory.

This makes an inspectable promotion proposal. It never promotes runtime sources,
imports, exports, or represents source validation as visual acceptance.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('native_packaging', PROJECT / 'tools/package-native.py')
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)


def prepare(candidate, lods, output):
    candidate, lods, output = candidate.resolve(strict=True), lods.resolve(strict=True), output.resolve()
    if output.exists() or output.is_relative_to(PROJECT.parents[1]) or output.is_relative_to(candidate) or output.is_relative_to(lods):
        raise ValueError('Fresh external review output is required')
    current = packaging.validate_rama_hero_notice(PROJECT)
    original = json.loads((PROJECT / 'NOTICE/RAMA-HERO-PROVENANCE.json').read_text())
    if original['schema'] != 2:
        raise ValueError('Review proposal requires the frozen schema2 parent')
    base = packaging.RAMA_FORM_BASE
    files = {p: PROJECT / p for p in current['sources']}
    files.update({
        f'{base}/candidate.glb': candidate / 'candidate.glb',
        f'{base}/reconstruction.blend': candidate / 'reconstruction.blend',
        f'{base}/reconstruction.inspection.json': candidate / 'reconstruction.inspection.json',
        f'{base}/edit-manifest.json': candidate / 'edit-manifest.json',
        f'{base}/vertex-edits.json': candidate / 'vertex-edits.json',
        f'{base}/lod-transfer-manifest.json': lods / 'lod-transfer-manifest.json',
        f'{base}/input/RAMA-HERO-PROVENANCE.json': PROJECT / 'NOTICE/RAMA-HERO-PROVENANCE.json',
    })
    for path in ('art/hero-rama-lod/glb_lod.py', 'art/visual-rounds/face/import_editable.py',
                 'art/visual-rounds/face/held-ring.json',
                 'art/visual-rounds/face/build_form_candidate.py', 'art/production/reconstruction-rama.blend',
                 'tools/visual-rounds/integration/transfer_form_lods.py'):
        files[path] = PROJECT / path
    for level in ('mid', 'far'):
        name = f'rama-hero-{level}.glb'
        files[f'{base}/input/{name}'] = PROJECT / 'assets/heroes' / name
        files[f'{base}/{name}'] = lods / 'overlay/assets/heroes' / name
        files[f'assets/heroes/{name}'] = files[f'{base}/{name}']
    files['assets/heroes/rama-hero.glb'] = candidate / 'candidate.glb'
    for relative, source in files.items():
        if not source.is_file() or source.is_symlink():
            raise ValueError(f'Missing/unsafe proposal input: {source}')
    output.mkdir(parents=True)
    for relative, source in files.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    notice = output / base / 'NOTICE.md'
    notice.write_text('''# Rama principal facial form — proposed source stage

Original local form displacement and LOD transfer authored for YUGA, October 2026.
License: CC0-1.0 for the local displacement authoring and inherited original YUGA
costume, hair, jewelry, bow and procedural material work as identified by the
retained per-source notices. MakeHuman anatomy and pinned face pose data remain
CC0; retain art/hero-rama/NOTICE.md and art/hero-rama-face/NOTICE.md attribution.

This stage derives from the preserved face GLB, not from recovered original
modeling history. reconstruction.blend is an editable import of candidate.glb;
it was reopened and inspected, but no Blender roundtrip GLB equivalence is claimed.
The form generator changes bounded rest POSITION/NORMAL/TANGENT data; exact LOD
row transfer preserves original topology, UVs, weights, rigs, morphs, images and
animations. Already-declared bounds on edited POSITION/NORMAL/TANGENT attributes
are updated to actual stored extrema; this includes optional LOD frame bounds.
The frozen original 288-vertex held-ring source receipt is retained as
art/visual-rounds/face/held-ring.json (SHA256 71cc40e8f5eb732382255cbb9ca2eca88f6306429c2c649f8223dbe5b4db0ccd).
Its exact position matches are excluded from every form position/frame edit.

Source identity and numerical evidence do not establish art acceptance or
production/GPU performance. Runtime promotion requires root's reviewed decision.
''')
    def sha(relative): return packaging.digest(output / relative)
    parent = original['authoringStages'][-1]
    stage = {'id': 'principal-facial-form-v1', 'parent': 'face',
             'asset': f'{base}/candidate.glb', 'sha256': sha(f'{base}/candidate.glb'),
             'editableSource': f'{base}/reconstruction.blend', 'editableSha256': sha(f'{base}/reconstruction.blend'),
             'generator': 'art/visual-rounds/face/build_form_candidate.py',
             'generatorSha256': sha('art/visual-rounds/face/build_form_candidate.py'),
             'metadata': f'{base}/edit-manifest.json', 'metadataSha256': sha(f'{base}/edit-manifest.json'),
             'inputEditableSha256': None, 'inputAssetSha256': parent['sha256'], 'editableOrigin': 'imported-stage-asset',
             'generatedDependencies': [{'path': p, 'sha256': sha(p)} for p in packaging.RAMA_FORM_DEPENDENCIES],
             'runtimeLods': [{'asset': f'assets/heroes/rama-hero-{level}.glb',
                              'sha256': sha(f'{base}/rama-hero-{level}.glb')} for level in ('mid', 'far')]}
    proposed = copy.deepcopy(original)
    proposed.update(schema=3, sha256=stage['sha256'], bytes=(output / stage['asset']).stat().st_size,
                    editableSource=stage['editableSource'], editableSha256=stage['editableSha256'])
    proposed['authoringStages'].append(stage)
    proposed['limitations'].append('Bounded principal form and coherent LOD source proposal; root/art acceptance remains pending. Editable companion is an import of the stage output.')
    path = output / 'NOTICE/RAMA-HERO-PROVENANCE.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(proposed, indent=2) + '\n')
    validated = packaging.validate_rama_hero_notice(output)
    promotion = [f'{base}/{p}' for p in ('candidate.glb', 'reconstruction.blend', 'reconstruction.inspection.json',
                  'edit-manifest.json', 'vertex-edits.json', 'NOTICE.md', 'lod-transfer-manifest.json',
                  'rama-hero-mid.glb', 'rama-hero-far.glb', 'input/rama-hero-mid.glb', 'input/rama-hero-far.glb',
                  'input/RAMA-HERO-PROVENANCE.json')]
    promotion += ['assets/heroes/rama-hero.glb', 'assets/heroes/rama-hero-mid.glb', 'assets/heroes/rama-hero-far.glb',
                  'art/visual-rounds/face/held-ring.json',
                  'NOTICE/RAMA-HERO-PROVENANCE.json']
    manifest = {'schema': 1, 'task': 'R2-14', 'status': 'review-proposal-not-promoted',
                'parent_notice_sha256': packaging.RAMA_FORM_HISTORICAL_NOTICE_SHA256,
                'validated_provenance': validated, 'promotion_files': {p: packaging.record(output / p) for p in promotion},
                'source_tool_sha256': {str(Path(__file__).relative_to(PROJECT)): packaging.digest(Path(__file__)),
                                      'tools/package-native.py': packaging.digest(PROJECT / 'tools/package-native.py')},
                'next': 'Root reviews actual pixels/deformation/resources, copies only promotion_files from this tree if accepted, retains already reviewed generators and package support, imports serially, reruns affected checks and freezes complete runtime source. No PCK or release was exported.'}
    (output / 'promotion-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'passed': True, 'authoring_stages': [s['id'] for s in validated['authoringStages']],
            'provenance_sources': len(validated['sources']), 'promotion_files': len(promotion), 'output': str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--lods', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.lods, args.output), indent=2))
