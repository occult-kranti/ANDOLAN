#!/usr/bin/env python3
"""Assemble the exact groom-r7 + cloth proposal outside the repository.

This copies immutable ancestors and an honest imported editable companion. It
does not promote, import, render, export, or accept the optional shader change.
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


def prepare(candidate, output):
    candidate, output = candidate.resolve(strict=True), output.resolve()
    if output.exists() or output.is_relative_to(PROJECT.parents[1]) or output.is_relative_to(candidate):
        raise ValueError('A fresh external review output is required')
    current = packaging.validate_rama_hero_notice(PROJECT)
    notice_path = PROJECT / 'NOTICE/RAMA-HERO-PROVENANCE.json'
    if packaging.digest(notice_path) != packaging.RAMA_GROOM_PARENT_NOTICE:
        raise ValueError('Review requires the exact accepted R2 parent notice')
    original = json.loads(notice_path.read_text())
    base = packaging.RAMA_GROOM_BASE
    files = {path: PROJECT / path for path in current['sources']}
    for path in dict(packaging.RAMA_GROOM_FILES, **packaging.RAMA_GROOM_DEPENDENCIES):
        if path == f'{base}/input/RAMA-HERO-PROVENANCE.json':
            files[path] = notice_path
        elif path.startswith(base + '/'):
            files[path] = candidate / Path(path).name
        else:
            files[path] = PROJECT / path
    for path in packaging.RAMA_CLOTH_DEPENDENCIES:
        files[path] = PROJECT / path
    for path in packaging.RAMA_GROOM_RUNTIME_SOURCES:
        files[path] = PROJECT / path
    cloth = packaging.RAMA_CLOTH_ASSET
    files[f'{packaging.RAMA_CLOTH_BASE}/input/woven-roughness.png'] = PROJECT / cloth
    files[f'{packaging.RAMA_CLOTH_BASE}/input/woven-roughness.png.import'] = PROJECT / (cloth + '.import')
    files[cloth] = PROJECT / f'{packaging.RAMA_CLOTH_BASE}/textures/woven-roughness-r3.png'
    for level in packaging.RAMA_GROOM_OUTPUTS:
        name = 'rama-hero.glb' if level == 'near' else f'rama-hero-{level}.glb'
        files[f'assets/heroes/{name}'] = candidate / name
    for path, source in files.items():
        if not source.is_file() or source.is_symlink():
            raise ValueError(f'Missing/unsafe review input {path}: {source}')
    output.mkdir(parents=True)
    for path, source in files.items():
        destination = output / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    old_import = (PROJECT / (cloth + '.import')).read_bytes()
    (output / (cloth + '.import')).write_bytes(old_import.replace(b'mipmaps/generate=false', b'mipmaps/generate=true'))
    pinned = packaging.RAMA_GROOM_FILES
    deps = lambda mapping: [{'path': path, 'sha256': sha} for path, sha in mapping.items()]
    stage = {
        'id': 'principal-groom-v1', 'parent': 'principal-facial-form-v1',
        'asset': f'{base}/rama-hero.glb', 'sha256': pinned[f'{base}/rama-hero.glb'],
        'editableSource': f'{base}/reconstruction.blend', 'editableSha256': pinned[f'{base}/reconstruction.blend'],
        'generator': 'art/visual-rounds/groom/build_groom.py',
        'generatorSha256': pinned['art/visual-rounds/groom/build_groom.py'],
        'metadata': f'{base}/groom-manifest.json', 'metadataSha256': pinned[f'{base}/groom-manifest.json'],
        'inputAssetSha256': packaging.RAMA_GROOM_INPUTS['near'], 'inputEditableSha256': None,
        'editableOrigin': 'imported-stage-asset', 'generatedDependencies': deps(packaging.RAMA_GROOM_DEPENDENCIES),
        'runtimeSources': deps(packaging.RAMA_GROOM_RUNTIME_SOURCES),
        'runtimeLods': [{'asset': f'assets/heroes/rama-hero-{level}.glb', 'sha256': packaging.RAMA_GROOM_OUTPUTS[level]}
                        for level in ('mid', 'far')],
    }
    proposed = copy.deepcopy(original)
    proposed.update(schema=4, sha256=stage['sha256'], bytes=(output / stage['asset']).stat().st_size,
                    editableSource=stage['editableSource'], editableSha256=stage['editableSha256'])
    proposed['authoringStages'].append(stage)
    proposed['clothStage'] = {
        'id': 'smooth-woven-roughness-v1', 'parentNoticeSha256': packaging.RAMA_GROOM_PARENT_NOTICE,
        'asset': cloth, 'sha256': packaging.RAMA_CLOTH_SHA256,
        'importConfig': cloth + '.import', 'importConfigSha256': packaging.RAMA_CLOTH_IMPORT_SHA256,
        'generatedDependencies': deps(packaging.RAMA_CLOTH_DEPENDENCIES),
    }
    proposed['limitations'].append(
        'Exact original groom-r7 plus independent scalar cloth texture stage. Imported editable is a saved/reopened GLB import, not a recovered modeling stack. Retained dead original hair data increases file size despite fewer active triangles. The rest nape correction clears the measured collar region; measured_step_recoil and bounded secondary stress contacts remain open. Diagnostic art review authorized full comparison, not default promotion. The separately approved lifecycle script is an explicit runtime dependency. Optional secondary frame shader is excluded.')
    (output / 'NOTICE').mkdir(exist_ok=True)
    (output / 'NOTICE/RAMA-HERO-PROVENANCE.json').write_text(json.dumps(proposed, indent=2) + '\n')
    validated = packaging.validate_rama_hero_notice(output)
    changed = []
    for path in sorted(set(files) | {cloth + '.import', 'NOTICE/RAMA-HERO-PROVENANCE.json'}):
        original_path = PROJECT / path
        if not original_path.is_file() or packaging.digest(original_path) != packaging.digest(output / path):
            changed.append(path)
    # These sources are already in the workspace but must be included in the
    # reviewable promotion set if the stage is accepted, not assumed committed.
    retained_source = [path for path in list(packaging.RAMA_GROOM_FILES) + list(packaging.RAMA_GROOM_DEPENDENCIES)
                       + list(packaging.RAMA_CLOTH_DEPENDENCIES) if path.startswith('art/visual-rounds/')]
    promotion = sorted(set(changed) | set(retained_source))
    tool_paths = ('tools/package-native.py', 'tools/visual-rounds/integration/prepare_groom_review.py',
                  'tests/rama_package_cases.py')
    manifest = {
        'schema': 1, 'task': 'R3-14', 'status': 'review-proposal-not-promoted',
        'parent_notice_sha256': packaging.RAMA_GROOM_PARENT_NOTICE,
        'validated_provenance': validated,
        'promotion_files': {path: packaging.record(output / path) for path in promotion},
        'package_support': {path: packaging.record(PROJECT / path) for path in tool_paths},
        'preserved_runtime_sources': {path: packaging.record(output / path) for path in
                                     ('scripts/rama_surface_finish.gd', 'shaders/rama_secondary_cloth.gdshader',
                                      'scripts/rama_secondary_motion.gd')},
        'optional_shader': {'included': False, 'required_unchanged_sha256': packaging.RAMA_CLOTH_DEPENDENCIES['shaders/rama_secondary_cloth.gdshader']},
        'asset_metadata_changes': {
            'glb_bytes_changed_from_rendered_r7': False,
            'glb_retag_or_reexport': False,
            'cloth_import_only_change': 'mipmaps/generate=false -> true',
            'other_asset_import_settings_changed': False,
            'notice_change': 'schema3 -> fixed schema4 source ancestry and independent cloth receipt',
        },
        'costs': validated['authoringStages'][-1]['costs'],
        'next': 'Root reviews actual pixels/action clearance, independent verifier and import/resource evidence; if accepted, promote only exact promotion_files and reviewed package support, then rerun affected checks serially. No runtime assets, canonical NOTICE, PCK or release changed by this tool.',
    }
    (output / 'promotion-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'passed': True, 'authoring_stages': [s['id'] for s in validated['authoringStages']],
            'provenance_sources': len(validated['sources']), 'promotion_files': len(promotion), 'output': str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.output), indent=2))
