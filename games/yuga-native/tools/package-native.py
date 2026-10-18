#!/usr/bin/env python3
"""Build auditable, portable native packages without editor export templates.

The selected MIT-licensed Godot runtime opens the exported project with --main-pack.
No downloaded tools or credentials are embedded. Windows packages are not treated
as executed merely because export and archive validation succeed on Linux.
"""
from __future__ import annotations

import argparse
import configparser
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
DEFAULT_LINUX = Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
DEFAULT_WINDOWS = Path('/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe')
EXPECTED_VERSION = '4.6.3'
PLATFORMS = {'linux': 'Linux x86_64', 'windows': 'Windows x86_64'}
# Match file names, not broad substrings such as the word "shader".
SECRET_NAME = re.compile(r'(^|[._-])(token|credential|credentials|secret|secrets|password|id_rsa|id_ed25519)([._-]|$)', re.I)
SECRET_CONTENT = re.compile(rb'(?:github_pat_[A-Za-z0-9_]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(part)
    return value.hexdigest()


def record(path: Path) -> dict:
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


PUBLIC_LINUX_RUNTIME = {
    'bytes': 85447128,
    'sha256': 'dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f',
    'version': '4.6.3.stable.custom_build',
}
PUBLIC_RUNTIME_EXPORTER_SHA = 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
PUBLIC_RUNTIME_EXPORTER_VERSION = '4.6.3.stable.official.7d41c59c4'
PUBLIC_RUNTIME_PROOF = 'docs/evidence/desktop-finish/G0/template-baseline-r1/finished-build-verification.json'
PUBLIC_RUNTIME_EVIDENCE = {
    PUBLIC_RUNTIME_PROOF: '70fc1633d8f29fed62a9d0db37103cc442bc7c066acda21ab78f2db560a16abd',
    'docs/evidence/desktop-finish/G0/template-baseline-r1/build-result.json': 'ef3611ef2f428dc36b1fc46b5784b8ec10ea1600fce0dce65d39aeb720def32c',
    'docs/evidence/desktop-finish/G0/template-build-preparation-r1/source-recovery.json': '33c58d013b84143be96e29f968fe26553a07e26e067fa61496506df79d1b5b20',
    'NOTICE/GODOT-LICENSE.txt': 'b0435e3b3e4e55238f05f4b306f30524a1b2e20147810d436eaa554fa6855c80',
    'NOTICE/GODOT-COPYRIGHT.txt': 'b3330849267d56ddd3d62a513817506606c2195034411fe05859f0140bff9d8a',
}


def public_runtime_provenance(proof_path: Path) -> dict:
    """Admit one reviewed unmodified build, never arbitrary self-attestation."""
    if not proof_path.is_file() or digest(proof_path) != PUBLIC_RUNTIME_EVIDENCE[PUBLIC_RUNTIME_PROOF]:
        raise ValueError('Linux runtime provenance is not the reviewed unmodified build proof')
    evidence = {}
    for relative, sha in PUBLIC_RUNTIME_EVIDENCE.items():
        path = PROJECT / relative
        if not path.is_file() or digest(path) != sha:
            raise ValueError('Public runtime evidence changed or is missing: ' + relative)
        evidence[relative] = record(path)
    proof = json.loads(proof_path.read_text())
    build = json.loads((PROJECT / 'docs/evidence/desktop-finish/G0/template-baseline-r1/build-result.json').read_text())
    recovery = json.loads((PROJECT / 'docs/evidence/desktop-finish/G0/template-build-preparation-r1/source-recovery.json').read_text())
    return {
        'kind': 'unmodified-public-source-template-debug',
        'source_commit': proof['source_commit'], 'source_patches': proof['source_patches'],
        'source_url': 'https://github.com/godotengine/godot/tree/' + proof['source_commit'],
        'source_archive': recovery['downloads']['godot-35e80b3a.tar.gz'],
        'source_archive_url': 'https://github.com/godotengine/godot/archive/' + proof['source_commit'] + '.tar.gz',
        'build_command': build['command'], 'target': 'template_debug',
        'evidence': evidence,
        'license': 'MIT; bundled GODOT-LICENSE.txt and GODOT-COPYRIGHT.txt include third-party attributions.',
        'scope': 'Build identity only. Archive validation does not establish execution or visual acceptance.',
    }


def linux_engine_selection(args: argparse.Namespace, expected: dict | None = None, *, probe_versions: bool = False) -> dict:
    """Bind exporter/font probe and Linux runtime independently across phases.

    An expected selection uses its already-probed versions only after matching
    binary bytes; this avoids executing a changed binary during final guards.
    """
    runtime = getattr(args, 'linux_runtime', None)
    proof = getattr(args, 'linux_runtime_provenance', None)
    if bool(runtime) != bool(proof):
        raise ValueError('--linux-runtime and --linux-runtime-provenance must be supplied together')
    exporter_record = record(args.linux_engine)
    runtime_record = record(runtime) if runtime else exporter_record
    provenance = None
    if runtime:
        if exporter_record['sha256'] != PUBLIC_RUNTIME_EXPORTER_SHA:
            raise ValueError('Public Linux runtime requires the reviewed official exporter')
        if runtime_record != {key: PUBLIC_LINUX_RUNTIME[key] for key in ('bytes', 'sha256')}:
            raise ValueError('Linux runtime is not the reviewed unmodified public binary')
        provenance = public_runtime_provenance(proof)
    if expected is not None:
        for key, actual in [('exporter', exporter_record), ('linux_runtime', runtime_record)]:
            if actual != {field: expected.get(key, {}).get(field) for field in ('bytes', 'sha256')}:
                raise ValueError('Linux engine identity changed since export: ' + key)
        version = expected['exporter']['version']
        runtime_version = expected['linux_runtime']['version']
    if expected is None or probe_versions:
        version = subprocess.check_output([str(args.linux_engine), '--version'], text=True, timeout=15).strip()
        runtime_version = (subprocess.check_output([str(runtime), '--version'], text=True, timeout=15).strip()
                           if runtime else version)
    if not version.startswith(EXPECTED_VERSION + '.'):
        raise ValueError(f'Expected Godot {EXPECTED_VERSION}; found {version}')
    if runtime and version != PUBLIC_RUNTIME_EXPORTER_VERSION:
        raise ValueError('Official exporter version differs from reviewed build')
    if runtime and runtime_version != PUBLIC_LINUX_RUNTIME['version']:
        raise ValueError('Public Linux runtime version differs from reviewed build')
    selected = {
        'exporter': {**exporter_record, 'version': version, 'role': 'PCK export and imported-font proof'},
        'linux_runtime': {**runtime_record, 'version': runtime_version,
                          'kind': 'unmodified-public-source-template-debug' if runtime else 'exporter-binary',
                          'provenance': provenance},
    }
    if record(args.linux_engine) != exporter_record or (runtime and record(runtime) != runtime_record):
        raise ValueError('Linux engine changed during identity validation')
    if expected is not None and selected != expected:
        raise ValueError('Linux exporter/runtime selection or provenance changed since export')
    return selected


def copy_public_runtime_notice(destination: Path, selection: dict) -> None:
    provenance = selection['linux_runtime']['provenance']
    if provenance is None:
        return
    notice = destination / 'NOTICE'
    for relative, pinned in provenance['evidence'].items():
        source = PROJECT / relative
        if record(source) != pinned:
            raise ValueError('Public runtime evidence changed before notice copy: ' + relative)
        if relative.startswith('NOTICE/'):
            if record(notice / Path(relative).name) != pinned:
                raise ValueError('Bundled public runtime attribution differs from reviewed source')
        else:
            target = notice / 'godot-public-runtime' / Path(relative).name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if record(target) != pinned:
                raise ValueError('Public runtime proof copy differs from reviewed source')
    json_write(notice / 'GODOT-RUNTIME-PROVENANCE.json', selection)
    (notice / 'GODOT-RUNTIME.txt').write_text(
        'Linux runtime: community-built, unmodified Godot public-source template_debug.\n'
        'It is not the official editor binary used to export and qualify fonts.\n'
        f"Runtime SHA-256: {selection['linux_runtime']['sha256']}\n"
        f"Exporter SHA-256: {selection['exporter']['sha256']}\n"
        f"Public source: {provenance['source_url']}\n"
        'Source patches: 0. Build command and archive hash: GODOT-RUNTIME-PROVENANCE.json.\n'
        'Original build/source verification records: godot-public-runtime/.\n'
        'License and third-party notices: GODOT-LICENSE.txt and GODOT-COPYRIGHT.txt.\n'
        'Package execution and visual qualification are separate from this build proof.\n', encoding='utf-8')


RAMA_HERO_STAGE_PATHS = (
    ('r7', 'art/hero-rama/history/r7-runtime/rama-hero.glb',
     'art/hero-rama/rama-hero.blend', 'art/hero-rama/build_hero.py',
     'art/hero-rama/history/r7-runtime/RAMA-HERO-PROVENANCE.json',
     ('art/hero-rama/rebind_dhoti.py', 'art/hero-rama/weight-correction.json')),
    ('q3', 'art/hero-rama-quality/rama-hero-quality.glb',
     'art/hero-rama-quality/rama-hero-quality.blend', 'art/hero-rama-quality/build_quality.py',
     'art/hero-rama-quality/provenance.json', ('art/hero-rama/build_hero.py',)),
    ('face', 'art/hero-rama-face/rama-hero-face.glb',
     'art/hero-rama-face/rama-hero-face.blend', 'art/hero-rama-face/build_native_face.py',
     'art/hero-rama-face/candidate.json',
     ('art/hero-rama-face/build_face.py', 'art/hero-rama-face/sources/face-poseunits.json',
      'art/hero-rama-face/sources/face-poseunits.bvh',
      'art/hero-rama-face/history/r4f-reviewed-before-tangents.glb')),
)
RAMA_FACE_REVIEWED_INPUT = {
    'path': 'art/hero-rama-face/history/r4f-reviewed-before-tangents.glb',
    'sha256': '1fdb01ccb894004a618a594cb41b2e955810c7bdc76855c42f7ce19b0516d92b',
    'bytes': 34322216,
}
RAMA_FACE_REVIEWED_GENERATOR_SHA256 = 'f872fa0da92d23a5f03866288c099c9bf7de29f99415b9fd3888d56a6452d036'
RAMA_FACE_POSE_REVISION = 'a8bc2d54ff0ac92e78ff71431b1023eda42bf482'
RAMA_FACE_POSE_FILES = (
    {'path': 'art/hero-rama-face/sources/face-poseunits.json',
     'upstream_path': 'makehuman/data/poseunits/face-poseunits.json',
     'sha256': 'e7224f76e9610049b79e5f9e8ac2985d1e9a367333395c07537919258cb42cc3', 'bytes': 1590},
    {'path': 'art/hero-rama-face/sources/face-poseunits.bvh',
     'upstream_path': 'makehuman/data/poseunits/face-poseunits.bvh',
     'sha256': '42a8e69692e30010371ee6993a6e5d3b468d35065559ec0953c936e31b8d903f', 'bytes': 310826},
)
RAMA_FORM_BASE = 'art/visual-rounds/face/principal-form-v1'
RAMA_FORM_HISTORICAL_NOTICE_SHA256 = 'eae9e6cb3701f7030af7ec4365f6a5bd7d7d43c785e53c4f3e19f2d00981421c'
RAMA_FORM_HELD_RING_SHA256 = '71cc40e8f5eb732382255cbb9ca2eca88f6306429c2c649f8223dbe5b4db0ccd'
RAMA_FORM_LOD_INPUTS = {
    'mid': '40737faf61e660f74dbb97b7a5a507869fdedd1a27cd964bb15e27e445a2d3cd',
    'far': 'd5888a452c2a8b711a7a5d8542652762d73c2608047b0399a2486c9ed650f9aa',
}
RAMA_FORM_DEPENDENCIES = (
    'art/hero-rama-lod/glb_lod.py', 'art/visual-rounds/face/import_editable.py',
    f'{RAMA_FORM_BASE}/reconstruction.inspection.json', f'{RAMA_FORM_BASE}/vertex-edits.json',
    'tools/visual-rounds/integration/transfer_form_lods.py', f'{RAMA_FORM_BASE}/lod-transfer-manifest.json',
    f'{RAMA_FORM_BASE}/rama-hero-mid.glb', f'{RAMA_FORM_BASE}/rama-hero-far.glb',
    f'{RAMA_FORM_BASE}/input/rama-hero-mid.glb', f'{RAMA_FORM_BASE}/input/rama-hero-far.glb',
    f'{RAMA_FORM_BASE}/input/RAMA-HERO-PROVENANCE.json', f'{RAMA_FORM_BASE}/NOTICE.md',
    'art/production/reconstruction-rama.blend',
    'art/visual-rounds/face/held-ring.json',
)


def _rama_source(project: Path, relative: str, expected_hash: str) -> dict:
    if not isinstance(expected_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_hash):
        raise ValueError(f'Rama hero provenance has invalid source hash: {relative}')
    if (not isinstance(relative, str) or relative.startswith('/') or '\\' in relative
            or '..' in PurePosixPath(relative).parts or not PurePosixPath(relative).parts):
        raise ValueError('Rama hero source path is unsafe')
    path = project / relative
    components = [project.joinpath(*PurePosixPath(relative).parts[:i])
                  for i in range(1, len(PurePosixPath(relative).parts) + 1)]
    if any(part.is_symlink() for part in components) or not path.resolve().is_relative_to(project) or not path.is_file():
        raise ValueError(f'Rama hero source is missing or unsafe: {relative}')
    actual = record(path)
    if actual['sha256'] != expected_hash:
        raise ValueError(f'Rama hero provenance differs from source: {relative}')
    return actual


def _validate_rama_schema1(project: Path, notice: dict, asset_relocation: str | None = None) -> dict:
    """Keep the original R7 identity/dependency contract, including archival use."""
    if not isinstance(notice, dict) or type(notice.get('schema')) is not int or notice['schema'] != 1:
        raise ValueError('Rama hero historical provenance must be a schema-1 object')
    expected = {
        'asset': ('assets/heroes/rama-hero.glb', 'sha256'),
        'editableSource': ('art/hero-rama/rama-hero.blend', 'editableSha256'),
        'generator': ('art/hero-rama/build_hero.py', 'generatorSha256'),
        'weightCorrectionGenerator': ('art/hero-rama/rebind_dhoti.py', 'weightCorrectionGeneratorSha256'),
        'weightCorrection': ('art/hero-rama/weight-correction.json', 'weightCorrectionSha256'),
    }
    sources = {}
    for field, (relative, hash_field) in expected.items():
        if notice.get(field) != relative:
            raise ValueError(f'Rama hero provenance has unexpected {field}')
        expected_hash = notice.get(hash_field)
        if not isinstance(expected_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_hash):
            raise ValueError(f'Rama hero provenance has invalid {hash_field}')
        stored_relative = asset_relocation if field == 'asset' and asset_relocation else relative
        sources[stored_relative] = _rama_source(project, stored_relative, expected_hash)
    dependencies = [{'path': notice['weightCorrectionGenerator'],
                     'sha256': notice['weightCorrectionGeneratorSha256']}]
    if notice.get('generatedDependencies') != dependencies:
        raise ValueError('Rama hero generated dependencies differ from the required weight correction source')
    return sources


def _validate_rama_form_stage(project: Path, stage: dict, historical: list, sources: dict,
                              runtime_bindings: bool = True) -> dict:
    """One bounded GLB form stage; editable data is imported from its output.

    This checks provenance identities, not the numerical or visual truth of an
    author's receipt. Those remain separate source-bound acceptance gates.
    """
    required = {'id', 'parent', 'asset', 'sha256', 'editableSource', 'editableSha256',
                'generator', 'generatorSha256', 'metadata', 'metadataSha256',
                'generatedDependencies', 'inputEditableSha256', 'inputAssetSha256',
                'editableOrigin', 'runtimeLods'}
    if not isinstance(stage, dict) or set(stage) != required:
        raise ValueError('Rama form stage is malformed')
    parent = historical[-1]
    if (stage['id'] != 'principal-facial-form-v1' or stage['parent'] != 'face'
            or stage['inputAssetSha256'] != parent['sha256']
            or stage['inputEditableSha256'] is not None
            or stage['editableOrigin'] != 'imported-stage-asset'):
        raise ValueError('Rama form stage must derive from the previous GLB; its editable is an imported companion')
    for field, relative, hash_field in (
            ('asset', f'{RAMA_FORM_BASE}/candidate.glb', 'sha256'),
            ('editableSource', f'{RAMA_FORM_BASE}/reconstruction.blend', 'editableSha256'),
            ('generator', 'art/visual-rounds/face/build_form_candidate.py', 'generatorSha256'),
            ('metadata', f'{RAMA_FORM_BASE}/edit-manifest.json', 'metadataSha256')):
        if stage.get(field) != relative:
            raise ValueError(f'Rama form stage has unexpected {field}')
        sources[relative] = _rama_source(project, relative, stage.get(hash_field))
    dependencies = stage['generatedDependencies']
    if not isinstance(dependencies, list) or len(dependencies) != len(RAMA_FORM_DEPENDENCIES):
        raise ValueError('Rama form stage requires the complete ordered authoring/LOD dependencies')
    for item, relative in zip(dependencies, RAMA_FORM_DEPENDENCIES):
        if not isinstance(item, dict) or set(item) != {'path', 'sha256'} or item.get('path') != relative:
            raise ValueError('Rama form stage dependency is malformed or unsafe')
        sources[relative] = _rama_source(project, relative, item.get('sha256'))
    archived = f'{RAMA_FORM_BASE}/input/RAMA-HERO-PROVENANCE.json'
    if sources[archived]['sha256'] != RAMA_FORM_HISTORICAL_NOTICE_SHA256:
        raise ValueError('Rama form immutable schema2 notice differs from the original historical bytes')
    old = json.loads((project / archived).read_text())
    if (old.get('schema') != 2 or old.get('authoringStages') != historical
            or old.get('sha256') != parent['sha256'] or old.get('editableSha256') != parent['editableSha256']):
        raise ValueError('Rama form stage rewrote historical authoring ancestry')
    if sources['art/visual-rounds/face/held-ring.json']['sha256'] != RAMA_FORM_HELD_RING_SHA256:
        raise ValueError('Rama form original 288-vertex held-ring source differs from frozen bytes')
    metadata = json.loads((project / stage['metadata']).read_text())
    identities = {'schema': 1, 'task': 'R2-08', 'stage': stage['id'],
                  'input_sha256': parent['sha256'], 'output_sha256': stage['sha256'],
                  'partition_sha256': parent['metadataSha256'], 'generator_sha256': stage['generatorSha256'],
                  'vertex_edits_sha256': sources[f'{RAMA_FORM_BASE}/vertex-edits.json']['sha256'],
                  'original_held_ring_sha256': RAMA_FORM_HELD_RING_SHA256, 'original_held_ring_vertices': 288,
                  'bytes': sources[stage['asset']]['bytes']}
    if (not isinstance(metadata, dict) or type(metadata.get('schema')) is not int
            or type(metadata.get('bytes')) is not int
            or any(metadata.get(k) != v for k, v in identities.items())):
        raise ValueError('Rama form authoring metadata identity/ancestry differs')
    inspection = json.loads((project / f'{RAMA_FORM_BASE}/reconstruction.inspection.json').read_text())
    expected = {'candidate_sha256': stage['sha256'], 'editable_sha256': stage['editableSha256'],
                'original_held_ring_sha256': RAMA_FORM_HELD_RING_SHA256,
                'generator_sha256': sources['art/visual-rounds/face/import_editable.py']['sha256']}
    if not isinstance(inspection, dict) or any(inspection.get(k) != v for k, v in expected.items()):
        raise ValueError('Rama form editable-import receipt identity differs')
    source_inspections = inspection.get('source_inspections')
    if (not isinstance(source_inspections, list) or len(source_inspections) != 2
            or [s.get('sha256') for s in source_inspections if isinstance(s, dict)] != [
                sources['art/production/reconstruction-rama.blend']['sha256'], parent['editableSha256']]):
        raise ValueError('Rama form inspected editable sources differ')
    lod = json.loads((project / f'{RAMA_FORM_BASE}/lod-transfer-manifest.json').read_text())
    expected = {'schema': 1, 'task': 'R2-14', 'stage': 'principal-facial-form-lod-transfer-v1',
                'original_held_ring_sha256': RAMA_FORM_HELD_RING_SHA256,
                'near_input_sha256': parent['sha256'], 'near_candidate_sha256': stage['sha256'],
                'generator_sha256': sources['tools/visual-rounds/integration/transfer_form_lods.py']['sha256']}
    if (not isinstance(lod, dict) or type(lod.get('schema')) is not int
            or any(lod.get(k) != v for k, v in expected.items())
            or not isinstance(lod.get('levels'), dict) or set(lod['levels']) != {'mid', 'far'}):
        raise ValueError('Rama form LOD receipt identity/ancestry differs')
    bindings = stage['runtimeLods']
    if not isinstance(bindings, list) or len(bindings) != 2:
        raise ValueError('Rama form requires both runtime body LOD bindings')
    for binding, (level, input_hash) in zip(bindings, RAMA_FORM_LOD_INPUTS.items()):
        asset, source = f'assets/heroes/rama-hero-{level}.glb', f'{RAMA_FORM_BASE}/rama-hero-{level}.glb'
        if (not isinstance(binding, dict) or set(binding) != {'asset', 'sha256'}
                or binding.get('asset') != asset or binding.get('sha256') != sources[source]['sha256']):
            raise ValueError('Rama form runtime LOD binding differs from its authored output')
        if runtime_bindings:
            sources[asset] = _rama_source(project, asset, binding['sha256'])
        if sources[f'{RAMA_FORM_BASE}/input/rama-hero-{level}.glb']['sha256'] != input_hash:
            raise ValueError('Rama form original LOD input differs from frozen historical bytes')
        receipt = lod['levels'][level]
        expected = {'input_sha256': input_hash, 'output_sha256': binding['sha256'], 'bytes': sources[source]['bytes']}
        if (not isinstance(receipt, dict) or type(receipt.get('bytes')) is not int
                or any(receipt.get(k) != v for k, v in expected.items())
                or receipt.get('all_other_binary_bytes_exact') is not True
                or receipt.get('json_exact_except_frame_bounds') is not True):
            raise ValueError('Rama form LOD output receipt differs from exact preserved-input contract')
    return {'id': stage['id'], 'parent': stage['parent'], 'asset': stage['asset'], 'sha256': stage['sha256'],
            'editableSource': stage['editableSource'], 'editableSha256': stage['editableSha256'],
            'editableOrigin': stage['editableOrigin'], 'runtimeLods': bindings}


# Schema4 is one frozen proposal, not an open-ended authoring-stage mechanism.
# A later art revision needs a separately reviewed contract and new pins.
RAMA_GROOM_BASE = 'art/visual-rounds/groom/principal-groom-v1'
RAMA_GROOM_PARENT_NOTICE = '754f81cef0da3d3fb03a21e083e0e3ab7a8b6feed7e0b95fcd47b88a99c33f58'
RAMA_GROOM_INPUTS = {
    'near': '140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a',
    'mid': '27d998d924d2732b13bc8e18c3e3ec1ce9d58f0408bf3fda1ff0613cf32cba9f',
    'far': 'ea9818e1464c9b6bc077ae83f8354a6357fb19d2a18fc84b2deb65c58aff901a',
}
RAMA_GROOM_OUTPUTS = {
    'near': '8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c',
    'mid': 'd95a061e2243477afc0227bf52564252fbcb20cb039d303ad10292ea5d85beed',
    'far': 'ee2e35278ce49efdda6751850fddbb8f1b4de99ad019e6992c10e7702dc6317c',
}
RAMA_GROOM_FILES = {
    f'{RAMA_GROOM_BASE}/rama-hero.glb': RAMA_GROOM_OUTPUTS['near'],
    f'{RAMA_GROOM_BASE}/reconstruction.blend': '940c8208d8f5ee8c2e8dd9e4bea2d9893450026189f1a4eb24cd0b1874378f25',
    'art/visual-rounds/groom/build_groom.py': '4bcdb1121a52c68f2cb3f35850ace8956fb0554d120a85ce292c4f4afa8f6044',
    f'{RAMA_GROOM_BASE}/groom-manifest.json': '948bed857f31609df81ea228663cb63055dd88148bda84a9fd5c04c48c30e6bc',
}
RAMA_GROOM_DEPENDENCIES = {
    'art/visual-rounds/groom/import_editable.py': '1f171a16886636726b1be71a799d5792dcf3834a48e50ab9a51e1ea196e5ae6d',
    'art/visual-rounds/groom/source-manifest-r7.json': '27bd394314e331c3d40d3c5fa88d06e0546e57e31dbe45a8c59eb1403f84114a',
    'art/visual-rounds/groom/NOTICE.md': '732c14adcb44d88cf88837dec040af9be29aab70daa3c4f2a8238e1c72d4aa4f',
    'art/hero-rama-lod/glb_lod.py': '83683afcfd3ce40b9e7193ef988793d37ff9b9107f16252c8cfe2715428a69e7',
    f'{RAMA_GROOM_BASE}/reconstruction.inspection.json': '9af85ce316cc3a270ef62bef98ad4b203218c6f29a5a27c81dc6d4af8d28e031',
    f'{RAMA_GROOM_BASE}/rama-hero-mid.glb': RAMA_GROOM_OUTPUTS['mid'],
    f'{RAMA_GROOM_BASE}/rama-hero-far.glb': RAMA_GROOM_OUTPUTS['far'],
    f'{RAMA_GROOM_BASE}/input/RAMA-HERO-PROVENANCE.json': RAMA_GROOM_PARENT_NOTICE,
}
RAMA_GROOM_RUNTIME_SOURCES = {
    # Separately approved lifecycle fix, already committed in 5bf8406. This is
    # a required runtime dependency, not part of the GLB authoring ancestry.
    'scripts/rama_secondary_motion.gd': '2b8e467df254dcda175694ab988071f24b41ddaa93275f5cbb9768abcb143f34',
}
RAMA_CLOTH_BASE = 'art/visual-rounds/cloth'
RAMA_CLOTH_ASSET = 'assets/materials/rama-finish/woven-roughness.png'
RAMA_CLOTH_SHA256 = 'eec110e598ac1a2fa95fb5899fac5fc314a191bff8e670547d79dfaf1468e500'
RAMA_CLOTH_IMPORT_SHA256 = '646c1b220662472d42a56884d8a1b51bddb625724b6de53d9f61cbf621109c24'
RAMA_CLOTH_DEPENDENCIES = {
    f'{RAMA_CLOTH_BASE}/textures/woven-roughness-r3.png': RAMA_CLOTH_SHA256,
    f'{RAMA_CLOTH_BASE}/build_candidate.py': '8f89cc177a3cb70f8f05b385f653533717d718b6cf0a949486cb019e1b14543a',
    f'{RAMA_CLOTH_BASE}/material-profile.json': 'f4ffe5e11364e1aa5905a93731063f24b4ca96036bceb963c84d26503caa299a',
    f'{RAMA_CLOTH_BASE}/source-manifest.json': 'd0c6ad6d7c82f721d3b4ebe749aee933b38caadd2af5cb7cc1a95da9b9c7c4d8',
    f'{RAMA_CLOTH_BASE}/NOTICE.md': '980a21ef68eda2db274528f10707746c5a496b0cf5bc02a4dbe1579aebe26a2f',
    f'{RAMA_CLOTH_BASE}/input/woven-roughness.png': '80f837f65096a4579e8b1de3c346f6f99f4d8b31d88c574fd5c18cd28889e4d3',
    f'{RAMA_CLOTH_BASE}/input/woven-roughness.png.import': 'c1fb4726ef765526cb67d2c5e78a85a0a8c49de6181a6e0b7e56286208ab3b8a',
    'scripts/rama_surface_finish.gd': '7936f28f29c4b96cb49742bb3309c96df962f95e3cec99d5a7b514ea03c369e1',
    'shaders/rama_secondary_cloth.gdshader': 'c1712f075af34b0e57dd7f70e5494c2060703e7f1ee68ff87c8a645cff95c6d7',
}


# Schema 5 preserves the exact schema 4 asset ancestry and adds one bounded
# original roughness stage. The old runtime binding stays in history; no prior
# receipt is rewritten to describe the new material profile.
RAMA_SURFACE_PARENT = 'art/hero-finish/history/schema4-notice.json'
RAMA_SURFACE_PARENT_SHA = '5026675c7af8b83412eb375b9883ffe52efd883e20c7fd9594bdf3fdd9c8f5d8'
RAMA_SURFACE_OLD_BINDING = 'art/hero-finish/history/schema4-surface-finish.gd'
RAMA_SURFACE_DEPENDENCIES = {
    'scripts/rama_surface_finish.gd':
        '6eb51ce8f34a3d5a33deb142ca92aaa20505516b0ee8fff3ca445bcab603078a',
    'art/hero-finish/build_g1_maps.py':
        '7082d83da791f1af16e61c082c40a0809321a57cfd024ec39ba34116ecfe0fbe',
    'assets/hero-finish/g1-manifest.json':
        '6e91c36db8fb785d5d8899adf3ad0d6d528b8d05189638269955121afec88134',
    'assets/hero-finish/NOTICE.md':
        'a58d301b021ac224dfc4af12e3d981f0cdb98da01e83871d8883757935851bd2',
    'assets/hero-finish/hair-bundle-roughness.png':
        '93c4d9655ee1309c5e427fa39d5ef4785422d5646ff7b1a8421c6a7803654fd4',
    'assets/hero-finish/hair-bundle-roughness.png.import':
        'f3386d36213c439b2128376097ff508fe73aab04d3d9c131455fb753d73a427c',
    'assets/hero-finish/forged-gold-roughness.png':
        'd2a3314a54bf1fe46bc8bfb9b9adbf3dadce42298221163b4b3c2865c5c36155',
    'assets/hero-finish/forged-gold-roughness.png.import':
        'fdb67effe9126ebac95782e31475af5e6bfb66381ece0aea5fc79a7d86553ed4',
    'art/hero-finish/build_s1_gold.py':
        'bae80fea52e6ad865abd430eea91dad2f78b0ec25fefedbc41bdf51ff3c457fd',
    'assets/hero-finish/s1-manifest.json':
        '34eb6de2ebf56cd5ab2f8ff7b3f68e928cb651e86c3efe8657df023e78386808',
    'assets/hero-finish/s1-hammered-gold-roughness.png':
        'f258ee24d260018ee3d566a428d9986efea557759bea4b907e083cb6912c942d',
    'assets/hero-finish/s1-hammered-gold-roughness.png.import':
        'cdfb8349abbf66ef4672b1a32f7edf8220e4cac2044050941a92a850c2abf197',
}


def _validate_rama_surface_stage(project, notice):
    stage = notice.get('surfaceStage')
    expected = {'id': 'original-hair-gold-roughness-v1', 'parentNotice': RAMA_SURFACE_PARENT,
                'parentNoticeSha256': RAMA_SURFACE_PARENT_SHA,
                'historicalBinding': RAMA_SURFACE_OLD_BINDING,
                'historicalBindingSha256': RAMA_CLOTH_DEPENDENCIES['scripts/rama_surface_finish.gd'],
                'generatedDependencies': [{'path': p, 'sha256': h} for p, h in RAMA_SURFACE_DEPENDENCIES.items()]}
    if stage != expected:
        raise ValueError('Rama schema5 surface stage differs from fixed reviewed sources')
    sources = {RAMA_SURFACE_PARENT: _rama_source(project, RAMA_SURFACE_PARENT, RAMA_SURFACE_PARENT_SHA),
               RAMA_SURFACE_OLD_BINDING: _rama_source(project, RAMA_SURFACE_OLD_BINDING, expected['historicalBindingSha256'])}
    parent = json.loads((project / RAMA_SURFACE_PARENT).read_text())
    base = copy.deepcopy(notice)
    base.pop('surfaceStage', None)
    base['schema'] = 4
    if base != parent:
        raise ValueError('Rama schema5 rewrites the preserved geometry/cloth ancestry')
    _rama_fixed_dependencies(project, stage['generatedDependencies'], RAMA_SURFACE_DEPENDENCIES, sources)
    return parent, sources, stage


def _rama_fixed_dependencies(project, declared, expected, sources, relocations=None):
    if declared != [{'path': p, 'sha256': h} for p, h in expected.items()]:
        raise ValueError('Rama dependencies differ from the frozen ordered source pins')
    for path, sha in expected.items():
        resolved = (relocations or {}).get(path, path)
        sources[resolved] = _rama_source(project, resolved, sha)


def _rama_glb(path):
    """Read the exact two-chunk GLB used by the finite schema4 contract."""
    data = path.read_bytes()
    if len(data) < 28 or struct.unpack_from('<III', data) != (0x46546c67, 2, len(data)):
        raise ValueError('Rama schema4 GLB header differs')
    length, kind = struct.unpack_from('<II', data, 12)
    end = 20 + length
    if kind != 0x4e4f534a or end + 8 > len(data):
        raise ValueError('Rama schema4 GLB JSON chunk differs')
    document = json.loads(data[20:end])
    length, kind = struct.unpack_from('<II', data, end)
    if kind != 0x004e4942 or end + 8 + length != len(data):
        raise ValueError('Rama schema4 GLB BIN chunk differs')
    return document, data[end + 8:]


def rama_groom_preservation(source, candidate):
    """Prove nonhair JSON/BIN preservation and report live versus stored cost."""
    old, prefix = _rama_glb(source)
    new, binary = _rama_glb(candidate)
    if binary[:len(prefix)] != prefix:
        raise ValueError('Rama groom changed its original binary prefix')
    restored = copy.deepcopy(new)
    restored['accessors'] = restored['accessors'][:len(old['accessors'])]
    restored['bufferViews'] = restored['bufferViews'][:len(old['bufferViews'])]
    restored['buffers'][0]['byteLength'] = old['buffers'][0]['byteLength']
    restored['meshes'][2]['primitives'][0] = old['meshes'][2]['primitives'][0]
    if restored != old:
        raise ValueError('Rama groom changed JSON beyond the single hair primitive and appended data')
    before, after = old['meshes'][2]['primitives'][0], new['meshes'][2]['primitives'][0]
    if (before['material'] != after['material'] or before.get('mode', 4) != after.get('mode', 4)
            or set(before['attributes']) != set(after['attributes'])):
        raise ValueError('Rama groom changed hair material, topology mode or attribute contract')
    # All original hair views are exclusive in these pinned inputs. Count them
    # once; their contents remain stored but are not referenced by live meshes.
    old_ids = set(before['attributes'].values()) | {before['indices']}
    old_views = {old['accessors'][i]['bufferView'] for i in old_ids}
    live_views = set()
    for mesh in new['meshes']:
        for primitive in mesh['primitives']:
            ids = set(primitive['attributes'].values()) | {primitive['indices']}
            ids.update(i for target in primitive.get('targets', []) for i in target.values())
            for i in ids:
                accessor = new['accessors'][i]
                if 'bufferView' in accessor:
                    live_views.add(accessor['bufferView'])
                for sparse in accessor.get('sparse', {}).values():
                    if isinstance(sparse, dict) and 'bufferView' in sparse:
                        live_views.add(sparse['bufferView'])
    if old_views & live_views:
        raise ValueError('Rama groom retained source hair views are unexpectedly live')
    triangles = lambda doc: sum(doc['accessors'][p['indices']]['count'] // 3
                               for m in doc['meshes'] for p in m['primitives'])
    return {'original_binary_prefix_exact': True, 'nonhair_json_exact': True,
            'source_file_bytes': source.stat().st_size, 'candidate_file_bytes': candidate.stat().st_size,
            'retained_binary_prefix_bytes': len(prefix), 'appended_binary_bytes': len(binary) - len(prefix),
            'retained_dead_hair_view_bytes': sum(old['bufferViews'][i]['byteLength'] for i in old_views),
            'source_active_triangles': triangles(old), 'candidate_active_triangles': triangles(new),
            'source_hair_triangles': old['accessors'][before['indices']]['count'] // 3,
            'candidate_hair_triangles': new['accessors'][after['indices']]['count'] // 3,
            'candidate_hair_vertices': new['accessors'][after['attributes']['POSITION']]['count']}


def _validate_rama_groom_stage(project, stage, historical, sources, runtime_relocations=None):
    required = {'id', 'parent', 'asset', 'sha256', 'editableSource', 'editableSha256',
                'generator', 'generatorSha256', 'metadata', 'metadataSha256',
                'generatedDependencies', 'inputEditableSha256', 'inputAssetSha256',
                'editableOrigin', 'runtimeLods', 'runtimeSources'}
    if not isinstance(stage, dict) or set(stage) != required:
        raise ValueError('Rama groom stage is malformed')
    if (stage['id'] != 'principal-groom-v1' or stage['parent'] != 'principal-facial-form-v1'
            or stage['inputAssetSha256'] != RAMA_GROOM_INPUTS['near']
            or stage['inputEditableSha256'] is not None or stage['editableOrigin'] != 'imported-stage-asset'):
        raise ValueError('Rama groom must derive from the frozen R2 GLB, with an imported editable companion')
    for (field, hash_field), (path, sha) in zip(
            (('asset', 'sha256'), ('editableSource', 'editableSha256'),
             ('generator', 'generatorSha256'), ('metadata', 'metadataSha256')), RAMA_GROOM_FILES.items()):
        if stage[field] != path or stage[hash_field] != sha:
            raise ValueError('Rama groom identity differs from the fixed r7 proposal')
        sources[path] = _rama_source(project, path, sha)
    _rama_fixed_dependencies(project, stage['generatedDependencies'], RAMA_GROOM_DEPENDENCIES, sources)
    _rama_fixed_dependencies(project, stage['runtimeSources'], RAMA_GROOM_RUNTIME_SOURCES, sources)
    archived = json.loads((project / f'{RAMA_GROOM_BASE}/input/RAMA-HERO-PROVENANCE.json').read_text())
    if archived['schema'] != 3 or archived['authoringStages'] != historical:
        raise ValueError('Rama groom rewrote the accepted R2 historical stages')
    expected_lods = [{'asset': f'assets/heroes/rama-hero-{level}.glb', 'sha256': RAMA_GROOM_OUTPUTS[level]}
                     for level in ('mid', 'far')]
    if stage['runtimeLods'] != expected_lods:
        raise ValueError('Rama groom runtime LOD bindings differ from r7')
    metadata = json.loads((project / stage['metadata']).read_text())
    costs = {}
    for level, input_sha in RAMA_GROOM_INPUTS.items():
        name = 'rama-hero.glb' if level == 'near' else f'rama-hero-{level}.glb'
        parent_path = f'{RAMA_FORM_BASE}/candidate.glb' if level == 'near' else f'{RAMA_FORM_BASE}/{name}'
        if sources[parent_path]['sha256'] != input_sha:
            raise ValueError('Rama groom parent LOD differs from corrected R2')
        runtime_path = (runtime_relocations or {}).get(f'assets/heroes/{name}', f'assets/heroes/{name}')
        sources[runtime_path] = _rama_source(project, runtime_path, RAMA_GROOM_OUTPUTS[level])
        receipt = metadata['levels'][level]
        if receipt['input_sha256'] != input_sha or receipt['output_sha256'] != RAMA_GROOM_OUTPUTS[level]:
            raise ValueError('Rama groom generator receipt lineage differs')
        costs[level] = rama_groom_preservation(project / parent_path, project / f'{RAMA_GROOM_BASE}/{name}')
    inspection = json.loads((project / f'{RAMA_GROOM_BASE}/reconstruction.inspection.json').read_text())
    if (inspection['candidate_sha256'] != stage['sha256'] or inspection['editable_sha256'] != stage['editableSha256']
            or inspection['native_source_sha256'] != historical[2]['editableSha256']
            or inspection['importer_sha256'] != RAMA_GROOM_DEPENDENCIES['art/visual-rounds/groom/import_editable.py']
            or inspection['candidate_import'] != inspection['reopened'] or inspection['guide_curves'] != 16
            or inspection['reopened']['bones'] != [164] or len(inspection['reopened']['actions']) != 9
            or len(inspection['reopened']['packed_images']) != 17):
        raise ValueError('Rama groom imported editable/reopen identity differs')
    return {key: stage[key] for key in ('id', 'parent', 'asset', 'sha256', 'editableSource',
                                       'editableSha256', 'editableOrigin', 'runtimeLods', 'runtimeSources')} | {'costs': costs}


def _validate_rama_cloth_stage(project, stage, sources, historical_binding=False):
    required = {'id', 'parentNoticeSha256', 'asset', 'sha256', 'importConfig', 'importConfigSha256',
                'generatedDependencies'}
    if not isinstance(stage, dict) or set(stage) != required:
        raise ValueError('Rama schema4 requires one separate finite cloth texture receipt')
    expected = {'id': 'smooth-woven-roughness-v1', 'parentNoticeSha256': RAMA_GROOM_PARENT_NOTICE,
                'asset': RAMA_CLOTH_ASSET, 'sha256': RAMA_CLOTH_SHA256,
                'importConfig': RAMA_CLOTH_ASSET + '.import', 'importConfigSha256': RAMA_CLOTH_IMPORT_SHA256}
    if any(stage[k] != v for k, v in expected.items()):
        raise ValueError('Rama cloth stage differs from the reviewed texture/import binding')
    _rama_fixed_dependencies(project, stage['generatedDependencies'], RAMA_CLOTH_DEPENDENCIES, sources,
                             {'scripts/rama_surface_finish.gd': RAMA_SURFACE_OLD_BINDING} if historical_binding else None)
    for path, sha in ((RAMA_CLOTH_ASSET, RAMA_CLOTH_SHA256), (RAMA_CLOTH_ASSET + '.import', RAMA_CLOTH_IMPORT_SHA256)):
        sources[path] = _rama_source(project, path, sha)
    old = (project / f'{RAMA_CLOTH_BASE}/input/woven-roughness.png.import').read_bytes()
    if (project / stage['importConfig']).read_bytes() != old.replace(b'mipmaps/generate=false', b'mipmaps/generate=true'):
        raise ValueError('Rama cloth import changed beyond mipmap generation')


def validate_rama_hero_notice(project: Path | None = None) -> dict:
    """Verify source identity and ordered authoring, not anatomy or art acceptance.

    Schema 1 preserves the R7 contract. Schema 2 records R7 -> Q3 -> final face
    authoring, so the R7 generator is never mislabeled as the final generator.
    Schema 3 appends one bounded form stage and its coherent mid/far body LODs,
    preserving the schema2 notice and all three historical stages exactly.
    Schema 4 appends the exact original groom-r7 and a separate cloth texture
    receipt; the optional secondary shader is expressly outside this contract.
    Schema 5 adds the fixed original roughness stage, retaining the exact schema 4
    notice and its own historical surface binding.
    Schema 6 preserves that exact schema5 notice and admits a finite ordered
    sequence of original diadem rail and selected sash UV edits. The original
    crown-only declaration remains an exact historical fixture.
    Historical rama.glb/rama-production.glb retain their separate checks.
    """
    project = (project or PROJECT).resolve()
    notice_path = project / 'NOTICE/RAMA-HERO-PROVENANCE.json'
    if notice_path.is_symlink() or not notice_path.resolve().is_relative_to(project):
        raise ValueError('Rama hero notice is unsafe')
    notice = json.loads(notice_path.read_text())
    if isinstance(notice, dict) and type(notice.get('schema')) is int and notice['schema'] == 6:
        if 'editStages' in notice:
            return _validate_rama_finish_notice(project, notice, notice_path)
        return _validate_rama_crown_notice(project, notice, notice_path)
    return _validate_rama_notice(project, notice, notice_path)


def _validate_rama_notice(project, notice, notice_path, runtime_relocations=None):
    """Keep schemas 1–5 exact; schema6 alone supplies fixed historical GLB locations."""
    if not isinstance(notice, dict) or type(notice.get('schema')) is not int:
        raise ValueError('Rama hero provenance must declare an integer schema')
    surface_sources, surface_stage = {}, None
    if notice['schema'] == 5:
        notice, surface_sources, surface_stage = _validate_rama_surface_stage(project, notice)
    if notice['schema'] == 1:
        return {'notice': record(notice_path), 'sources': _validate_rama_schema1(project, notice)}
    if notice['schema'] not in (2, 3, 4):
        raise ValueError('Rama hero provenance has an unknown schema')
    if notice['schema'] == 4 and set(notice) != {
            'schema', 'asset', 'sha256', 'bytes', 'editableSource', 'editableSha256',
            'authoringStages', 'limitations', 'clothStage'}:
        raise ValueError('Rama schema4 admits only the fixed groom stage and separate cloth receipt')
    obsolete = {'generator', 'generatorSha256', 'weightCorrectionGenerator',
                'weightCorrectionGeneratorSha256', 'weightCorrection',
                'weightCorrectionSha256', 'generatedDependencies'}
    if obsolete.intersection(notice):
        raise ValueError('Schema-2 generators/dependencies belong to their authoring stage')
    if notice.get('asset') != 'assets/heroes/rama-hero.glb':
        raise ValueError('Rama hero provenance has unexpected asset')
    asset_path = (runtime_relocations or {}).get(notice['asset'], notice['asset'])
    sources = {asset_path: _rama_source(project, asset_path, notice.get('sha256'))}
    sources.update(surface_sources)
    if type(notice.get('bytes')) is not int or notice['bytes'] != sources[asset_path]['bytes']:
        raise ValueError('Rama hero provenance byte count differs from active asset')
    stages = notice.get('authoringStages')
    stage_count = len(RAMA_HERO_STAGE_PATHS) + max(0, notice['schema'] - 2)
    if not isinstance(stages, list) or len(stages) != stage_count:
        raise ValueError('Rama hero requires the schema-specific ordered R7/Q3/face[/form] stages')
    required_keys = {'id', 'parent', 'asset', 'sha256', 'editableSource', 'editableSha256',
                     'generator', 'generatorSha256', 'metadata', 'metadataSha256',
                     'generatedDependencies', 'inputEditableSha256'}
    reviewed_stages = []
    previous = None
    for stage, (stage_id, asset, editable, generator, metadata_path, dependencies) in zip(stages, RAMA_HERO_STAGE_PATHS):
        face_keys = {'sourceLedger', 'sourceLedgerSha256', 'licenseNotice', 'licenseNoticeSha256',
                     'reviewedMetadata', 'reviewedMetadataSha256', 'reviewedGenerator', 'reviewedGeneratorSha256'}
        stage_keys = required_keys | (face_keys if stage_id == 'face' else set())
        if not isinstance(stage, dict) or set(stage) != stage_keys or stage.get('id') != stage_id:
            raise ValueError('Rama hero authoring stage is malformed or out of order')
        if stage.get('parent') != (previous['id'] if previous else None):
            raise ValueError('Rama hero authoring parent does not match its previous stage')
        if stage.get('inputEditableSha256') != (previous['editableSha256'] if previous else None):
            raise ValueError('Rama hero editable input does not match its previous stage')
        for field, relative, hash_field in (
                ('asset', asset, 'sha256'), ('editableSource', editable, 'editableSha256'),
                ('generator', generator, 'generatorSha256'), ('metadata', metadata_path, 'metadataSha256')):
            if stage.get(field) != relative:
                raise ValueError(f'Rama hero stage {stage_id} has unexpected {field}')
            sources[relative] = _rama_source(project, relative, stage.get(hash_field))
        ledger = stage.get('generatedDependencies')
        if not isinstance(ledger, list) or len(ledger) != len(dependencies):
            raise ValueError(f'Rama hero stage {stage_id} has missing/extra dependencies')
        for dependency, relative in zip(ledger, dependencies):
            if not isinstance(dependency, dict) or set(dependency) != {'path', 'sha256'} or dependency.get('path') != relative:
                raise ValueError(f'Rama hero stage {stage_id} dependency is malformed or unsafe')
            sources[relative] = _rama_source(project, relative, dependency.get('sha256'))
        if stage_id == 'face':
            reviewed_input = sources[RAMA_FACE_REVIEWED_INPUT['path']]
            if reviewed_input != {key: RAMA_FACE_REVIEWED_INPUT[key] for key in ('sha256', 'bytes')}:
                raise ValueError('Rama face repair input differs from the pinned reviewed R4f export')
            for field, relative, hash_field in (
                    ('sourceLedger', 'art/hero-rama-face/sources/source-ledger.json', 'sourceLedgerSha256'),
                    ('licenseNotice', 'art/hero-rama-face/NOTICE.md', 'licenseNoticeSha256'),
                    ('reviewedMetadata', 'art/hero-rama-face/history/r4f-reviewed/candidate.json', 'reviewedMetadataSha256'),
                    ('reviewedGenerator', 'art/hero-rama-face/history/r4f-reviewed/build_native_face.py', 'reviewedGeneratorSha256')):
                if stage.get(field) != relative:
                    raise ValueError(f'Rama face stage has unexpected {field}')
                sources[relative] = _rama_source(project, relative, stage.get(hash_field))
            if stage['reviewedGeneratorSha256'] != RAMA_FACE_REVIEWED_GENERATOR_SHA256:
                raise ValueError('Rama face original geometry generator differs from its reviewed identity')
            source_ledger = json.loads((project / stage['sourceLedger']).read_text())
            if (not isinstance(source_ledger, dict) or type(source_ledger.get('schema')) is not int
                    or source_ledger['schema'] != 1
                    or source_ledger.get('repository') != 'https://github.com/makehumancommunity/makehuman'
                    or source_ledger.get('revision') != RAMA_FACE_POSE_REVISION
                    or source_ledger.get('license') != 'CC0'
                    or source_ledger.get('files') != list(RAMA_FACE_POSE_FILES)):
                raise ValueError('Rama face pose source/license ledger differs from the pinned CC0 inputs')
            for entry in RAMA_FACE_POSE_FILES:
                if sources[entry['path']] != {key: entry[key] for key in ('sha256', 'bytes')}:
                    raise ValueError('Rama face pose data differs from its pinned upstream source')
            pose_metadata = json.loads((project / RAMA_FACE_POSE_FILES[0]['path']).read_text())
            license_text = (project / stage['licenseNotice']).read_text()
            if (not isinstance(pose_metadata, dict) or pose_metadata.get('license') != 'CC0'
                    or 'Data Collection AB, Joel Palmius, Jonas Hauquier' not in license_text
                    or 'License: CC0' not in license_text or RAMA_FACE_POSE_REVISION not in license_text):
                raise ValueError('Rama face pose CC0 attribution/evidence is missing')
        metadata = json.loads((project / metadata_path).read_text())
        if not isinstance(metadata, dict):
            raise ValueError(f'Rama hero stage {stage_id} metadata must be an object')
        if stage_id == 'r7':
            sources.update(_validate_rama_schema1(project, metadata, asset_relocation=asset))
            identities = {'sha256': stage['sha256'], 'editableSha256': stage['editableSha256'],
                          'generatorSha256': stage['generatorSha256']}
        elif stage_id == 'q3':
            identities = {'acceptedInputGlbSha256': previous['sha256'],
                          'acceptedInputEditableSha256': previous['editableSha256'],
                          'candidateGlbSha256': stage['sha256'],
                          'candidateEditableSha256': stage['editableSha256'],
                          'generatorSha256': stage['generatorSha256']}
        else:
            identities = {'inputBlendSha256': previous['editableSha256'],
                          'outputSha256': stage['sha256'], 'editableSha256': stage['editableSha256'],
                          'generatorSha256': stage['generatorSha256']}
            repair = metadata.get('zeroTangentRepair')
            if (not isinstance(repair, dict)
                    or repair.get('sourceSha256') != RAMA_FACE_REVIEWED_INPUT['sha256']
                    or repair.get('resultSha256') != stage['sha256']
                    or type(repair.get('allowedRecords')) is not int or repair['allowedRecords'] != 3
                    or type(repair.get('changedBytes')) is not int or not 1 <= repair['changedBytes'] <= 48
                    or repair.get('allOtherBytesIdentical') is not True
                    or repair.get('positionsNormalsUVsSkinMorphsFaceUnchanged') is not True):
                raise ValueError('Rama face tangent-repair metadata does not match its reviewed input/output contract')
            reviewed_metadata = json.loads((project / stage['reviewedMetadata']).read_text())
            original_identities = {'inputBlendSha256': previous['editableSha256'],
                                   'outputSha256': RAMA_FACE_REVIEWED_INPUT['sha256'],
                                   'editableSha256': stage['editableSha256'],
                                   'generatorSha256': stage['reviewedGeneratorSha256']}
            if (not isinstance(reviewed_metadata, dict) or type(reviewed_metadata.get('schema')) is not int
                    or reviewed_metadata['schema'] != 1
                    or any(reviewed_metadata.get(key) != value for key, value in original_identities.items())
                    or metadata.get('nativeGeometryGeneratorSha256') != stage['reviewedGeneratorSha256']
                    or metadata.get('postExportProcessorSha256') != stage['generatorSha256']):
                raise ValueError('Rama face reviewed authoring metadata/unchanged editable/repair ancestry differs')
        if any(metadata.get(key) != value for key, value in identities.items()):
            raise ValueError(f'Rama hero stage {stage_id} metadata identity/ancestry differs')
        reviewed_stages.append({'id': stage_id, 'parent': stage['parent'],
                                'asset': asset, 'sha256': stage['sha256'],
                                'editableSource': editable, 'editableSha256': stage['editableSha256']})
        previous = stage
    if notice['schema'] >= 3:
        reviewed_stages.append(_validate_rama_form_stage(project, stages[3], stages[:3], sources,
                                                        runtime_bindings=notice['schema'] == 3))
        previous = stages[3]
    if notice['schema'] == 4:
        reviewed_stages.append(_validate_rama_groom_stage(project, stages[4], stages[:4], sources,
                                                        runtime_relocations=runtime_relocations))
        _validate_rama_cloth_stage(project, notice.get('clothStage'), sources, historical_binding=surface_stage is not None)
        previous = stages[4]
    elif 'clothStage' in notice:
        raise ValueError('Rama cloth stage requires the exact schema4 groom/cloth proposal')
    if (notice.get('sha256') != previous['sha256']
            or notice.get('editableSource') != previous['editableSource']
            or notice.get('editableSha256') != previous['editableSha256']):
        raise ValueError('Rama hero active asset/editable differs from terminal authoring stage')
    result = {'notice': record(notice_path), 'sources': sources, 'authoringStages': reviewed_stages}
    if surface_stage is not None:
        result['surfaceStage'] = surface_stage
    return result


# Schema 6 changes only the original diadem rail's P/N/T records in three
# existing GLBs. The complete schema5 notice and its old runtime trio remain
# independently verifiable history, not rewritten as the crown's output.
RAMA_CROWN_BASE = 'art/hero-finish/s4-diadem-smooth'
RAMA_CROWN_PARENT = 'art/hero-finish/history/schema5-notice.json'
RAMA_CROWN_PARENT_SHA = 'c48713bc763522f2763b8d8e229a17c51981b51df60c28379e09547acf452d42'
RAMA_CROWN_OUTPUTS = {
    'near': ('rama-hero.glb', 'e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82', 36049948),
    'mid': ('rama-hero-mid.glb', 'dfa9a41adab7cfd5c60416a66d2b95c4d1ab06d081b64ee7a9f5ff5c7744474b', 25847144),
    'far': ('rama-hero-far.glb', '8b74504c07d38416032ea22e37061d69061baaf0b86e78dec27417c8927e39f9', 20901820),
}
RAMA_CROWN_DEPENDENCIES = {
    f'{RAMA_CROWN_BASE}/build_candidate.py': 'b81482a8021d35f19adb6e2ee548f28a4823a1c42dcd446f1f0d999873927564',
    f'{RAMA_CROWN_BASE}/candidate-r2/source-manifest.json': 'ae869c0d3a645ad3221b0427d8036976db2564d8f10c4a8786e2fa3acd2772b0',
    f'{RAMA_CROWN_BASE}/NOTICE.md': '37d06774f752aa2f8415faa073858b8e1cefa163d68ab1071a8f1f2cfeef89b5',
    'art/hero-finish/s4-diadem-fit/build_candidate.py': 'c785e858881f85aa3ed09f0b0dec0323a27ba1d2b209dd1224b681b0b22b8c58',
    'art/hero-rama-lod/glb_lod.py': '83683afcfd3ce40b9e7193ef988793d37ff9b9107f16252c8cfe2715428a69e7',
    'docs/evidence/visual-rounds/round3/role10/geometry_probe.py': '324c2f688dbefc6c3ac86f5b5ca346c069efd1f7b8916252ad9489fcf0ad532c',
    'assets/heroes/rama-hero.glb.import': 'c9480cdb1c83f72a5b3479d91402aa81a50ff7d8e62c2775405108784639151a',
    'assets/heroes/rama-hero-mid.glb.import': '893f150856eba4a372d0f24a7bbdd1e591f9f28c999f85a53c24de61562b6598',
    'assets/heroes/rama-hero-far.glb.import': '60c2d7585242b7e0130da031a9e98316d9f4ded36eb6c2ed437ab01c687a0c66',
}


def rama_crown_notice() -> dict:
    """Finite reviewed declaration; never derives trusted pins from mutable input."""
    return {
        'schema': 6, 'asset': 'assets/heroes/rama-hero.glb',
        'sha256': RAMA_CROWN_OUTPUTS['near'][1], 'bytes': RAMA_CROWN_OUTPUTS['near'][2],
        'parentNotice': RAMA_CROWN_PARENT, 'parentNoticeSha256': RAMA_CROWN_PARENT_SHA,
        'crownStage': {
            'id': 'smooth-diadem-rail-v1',
            'generatedDependencies': [{'path': p, 'sha256': h} for p, h in RAMA_CROWN_DEPENDENCIES.items()],
            'runtimeAssets': [
                {'asset': f'assets/heroes/{name}', 'sha256': sha, 'bytes': size,
                 'inputAsset': f'{RAMA_GROOM_BASE}/{name}', 'inputSha256': RAMA_GROOM_OUTPUTS[level],
                 'authoredAsset': f'{RAMA_CROWN_BASE}/candidate-r2/{name}'}
                for level, (name, sha, size) in RAMA_CROWN_OUTPUTS.items()],
            'editScope': {'mesh': 2, 'primitive': 2, 'attributes': ['POSITION', 'NORMAL', 'TANGENT'],
                          'allOtherBinaryBytesExact': True, 'jsonExact': True},
        },
        'limitations': [
            'One bounded original diadem rail correction; broader hero art and continuous contact quality remain open.',
            'The schema5 editable is historical parent geometry. The crown is a reproducible GLB postprocess, not a newly edited Blender source.',
            'Source/PCK identity is separate from imported-cache, native execution, Windows and physical-GPU acceptance.',
        ],
    }


def rama_crown_preservation(source: Path, candidate: Path, selected_ids: list) -> dict:
    """Independent finite BIN/JSON gate; only fixed-manifest rail P/N/T may differ."""
    old, old_bin = _rama_glb(source)
    new, new_bin = _rama_glb(candidate)
    def prefix(path):
        with path.open('rb') as stream:
            header = stream.read(20)
            return header + stream.read(struct.unpack_from('<I', header, 12)[0] + 8)
    if (old != new or prefix(source) != prefix(candidate) or len(old_bin) != len(new_bin)
            or source.stat().st_size != candidate.stat().st_size):
        raise ValueError('Rama crown changed GLB JSON, binary length or file size')
    primitive = old['meshes'][2]['primitives'][2]
    if old['materials'][primitive['material']]['name'] != 'Worked warm gold':
        raise ValueError('Rama crown selected a different material primitive')
    if (not isinstance(selected_ids, list) or not selected_ids
            or any(type(i) is not int or i < 0 for i in selected_ids)
            or sorted(set(selected_ids)) != selected_ids):
        raise ValueError('Rama crown rail vertex set is malformed')
    intervals = []
    for attribute, width in (('POSITION', 3), ('NORMAL', 3), ('TANGENT', 4)):
        accessor = old['accessors'][primitive['attributes'][attribute]]
        view = old['bufferViews'][accessor['bufferView']]
        size = 4 * width
        stride = view.get('byteStride', size)
        if (accessor['componentType'] != 5126 or accessor['type'] != f'VEC{width}'
                or 'sparse' in accessor or accessor.get('normalized', False)
                or selected_ids[-1] >= accessor['count'] or stride < size or stride % 4):
            raise ValueError('Rama crown rail accessor contract differs')
        base = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        for vertex in selected_ids:
            start = base + vertex * stride
            end = start + size
            if start < 0 or end > len(old_bin) or end > view.get('byteOffset', 0) + view['byteLength']:
                raise ValueError('Rama crown rail record is outside its binary view')
            intervals.append((start, end))
    intervals.sort()
    cursor, changed = 0, 0
    for start, end in intervals:
        if start < cursor:
            raise ValueError('Rama crown allowed records overlap')
        if old_bin[cursor:start] != new_bin[cursor:start]:
            raise ValueError('Rama crown changed nonrail binary payload')
        changed += sum(a != b for a, b in zip(old_bin[start:end], new_bin[start:end]))
        cursor = end
    if old_bin[cursor:] != new_bin[cursor:]:
        raise ValueError('Rama crown changed nonrail binary payload')
    return {'json_exact': True, 'outside_selected_records_exact': True,
            'selected_vertices': len(selected_ids), 'changed_binary_bytes': changed,
            'allowed_record_bytes': sum(end - start for start, end in intervals)}


def _validate_rama_crown_notice(project, notice, notice_path, historical_runtime=False):
    if json.dumps(notice, sort_keys=True) != json.dumps(rama_crown_notice(), sort_keys=True):
        raise ValueError('Rama schema6 crown declaration differs from the fixed reviewed stage')
    parent_record = _rama_source(project, RAMA_CROWN_PARENT, RAMA_CROWN_PARENT_SHA)
    parent = json.loads((project / RAMA_CROWN_PARENT).read_text())
    if type(parent.get('schema')) is not int or parent['schema'] != 5:
        raise ValueError('Rama schema6 requires the exact schema5 historical parent')
    relocations = {f'assets/heroes/{name}': f'{RAMA_GROOM_BASE}/{name}'
                   for name, _, _ in RAMA_CROWN_OUTPUTS.values()}
    history = _validate_rama_notice(project, parent, project / RAMA_CROWN_PARENT, relocations)
    sources = history['sources']
    sources[RAMA_CROWN_PARENT] = parent_record
    stage = notice['crownStage']
    _rama_fixed_dependencies(project, stage['generatedDependencies'], RAMA_CROWN_DEPENDENCIES, sources)
    metadata = json.loads((project / f'{RAMA_CROWN_BASE}/candidate-r2/source-manifest.json').read_text())
    if (type(metadata.get('schema')) is not int or metadata['schema'] != 1
            or set(metadata.get('levels', {})) != set(RAMA_CROWN_OUTPUTS)
            or metadata.get('generator_sha256') != RAMA_CROWN_DEPENDENCIES[f'{RAMA_CROWN_BASE}/build_candidate.py']
            or metadata.get('derived_builder_sha256') != RAMA_CROWN_DEPENDENCIES['art/hero-finish/s4-diadem-fit/build_candidate.py']):
        raise ValueError('Rama crown generator/metadata ancestry differs')
    costs = {}
    for (level, (name, sha, size)), binding in zip(RAMA_CROWN_OUTPUTS.items(), stage['runtimeAssets']):
        runtime_path = binding['authoredAsset'] if historical_runtime else binding['asset']
        for path in dict.fromkeys((runtime_path, binding['authoredAsset'])):
            sources[path] = _rama_source(project, path, sha)
            if sources[path]['bytes'] != size:
                raise ValueError('Rama crown GLB size differs')
        row = metadata['levels'][level]
        if (row.get('source') != binding['asset'] or row.get('source_sha256') != binding['inputSha256']
                or Path(row.get('output', '')).name != name or row.get('sha256') != sha
                or type(row.get('bytes')) is not int or row['bytes'] != size
                or row.get('json_exact') is not True or row.get('outside_selected_records_exact') is not True):
            raise ValueError('Rama crown LOD manifest differs from input/output bindings')
        proof = rama_crown_preservation(project / binding['inputAsset'], project / runtime_path,
                                       row.get('selected_vertex_ids'))
        if any(proof[key] != row.get(key) for key in proof):
            raise ValueError('Rama crown direct preservation differs from the reviewed manifest')
        costs[level] = proof
    return {'notice': record(notice_path), 'sources': sources,
            'authoringStages': history['authoringStages'], 'surfaceStage': history['surfaceStage'],
            'crownStage': stage, 'crownPreservation': costs,
            'historicalParent': {'path': RAMA_CROWN_PARENT, **parent_record}}


# The schema6 envelope has a finite ordered edit sequence. Its parent remains
# schema5; the crown-only declaration is an exact historical fixture, not a new
# nested parent for each subsequent asset edit.
RAMA_CROWN_NOTICE_HISTORY = 'art/hero-finish/history/schema6-crown-notice.json'
RAMA_CROWN_NOTICE_HISTORY_SHA = 'b5e27702835234e46ece84fc2840b719e40e0bae16c2fa5c37dde735a4a39f3c'
RAMA_SASH_BASE = 'art/hero-finish/sash-texel-r1'
RAMA_SASH_OUTPUTS = {
    'near': ('rama-hero.glb', 'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e', 36049948, 7716, 9789),
    'mid': ('rama-hero-mid.glb', 'b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005', 25847144, 2211, 3179),
    'far': ('rama-hero-far.glb', 'aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a', 20901820, 956, 1388),
}
RAMA_SASH_DEPENDENCIES = {
    f'{RAMA_SASH_BASE}/build_candidate.py': 'b3449399008ebae1fa38518306da16347237fccd35d1ad713e8c3ad1fa7e8fc4',
    f'{RAMA_SASH_BASE}/candidate-r2/manifest.json': 'ae3b0a6aac2803ff6121c05629abad1d050a2ca0e16777a11b631b29048fbb51',
    f'{RAMA_SASH_BASE}/README.md': '9f90da673cccfba7bf2090249fb8156d1d66cbe2d91905e4c044e809ee0832eb',
}


def rama_finish_notice() -> dict:
    crown = rama_crown_notice()
    return {
        'schema': 6, 'asset': 'assets/heroes/rama-hero.glb',
        'sha256': RAMA_SASH_OUTPUTS['near'][1], 'bytes': RAMA_SASH_OUTPUTS['near'][2],
        'parentNotice': RAMA_CROWN_PARENT, 'parentNoticeSha256': RAMA_CROWN_PARENT_SHA,
        'historicalCrownNotice': RAMA_CROWN_NOTICE_HISTORY,
        'historicalCrownNoticeSha256': RAMA_CROWN_NOTICE_HISTORY_SHA,
        'editStages': [crown['crownStage'], {
            'id': 'sash-textile-uv-v1', 'inputStage': crown['crownStage']['id'],
            'generatedDependencies': [{'path': p, 'sha256': h} for p, h in RAMA_SASH_DEPENDENCIES.items()],
            'runtimeAssets': [
                {'asset': f'assets/heroes/{name}', 'sha256': sha, 'bytes': size,
                 'inputAsset': f'{RAMA_CROWN_BASE}/candidate-r2/{name}',
                 'inputSha256': RAMA_CROWN_OUTPUTS[level][1],
                 'authoredAsset': f'{RAMA_SASH_BASE}/candidate-r2/{name}',
                 'selectedVertexRangeInclusive': [first, last]}
                for level, (name, sha, size, first, last) in RAMA_SASH_OUTPUTS.items()],
            'editScope': {'mesh': 2, 'primitive': 3, 'attributes': ['TEXCOORD_0'],
                          'scaleUV': [0.2, 0.95], 'allOtherBinaryBytesExact': True, 'jsonExact': True},
        }],
        'limitations': [
            'Two bounded accepted edits: original diadem rail and selected sash UV scale. Broader hero/contact quality remains open.',
            'Stage1 logical runtime names identify its immutable crown intermediates; only the final stage supplies active runtime outputs.',
            'Schema5 Blender editable remains historical parent geometry; both edits are reproducible original GLB postprocesses.',
            'Authoring manifest status records pre-promotion history. This active declaration binds the accepted outputs.',
            'Source/PCK identity is separate from imported-cache, native execution, Windows and physical-GPU acceptance.',
        ],
    }


def rama_sash_preservation(source: Path, candidate: Path, selected_range: list) -> dict:
    """Only fixed selected UV records may differ, each replayed as float32 scale."""
    old, old_bin = _rama_glb(source)
    new, new_bin = _rama_glb(candidate)
    def prefix(path):
        with path.open('rb') as stream:
            header = stream.read(20)
            return header + stream.read(struct.unpack_from('<I', header, 12)[0] + 8)
    if (old != new or prefix(source) != prefix(candidate) or len(old_bin) != len(new_bin)
            or source.stat().st_size != candidate.stat().st_size):
        raise ValueError('Rama sash changed GLB JSON, binary length or file size')
    primitive = old['meshes'][2]['primitives'][3]
    if old['materials'][primitive['material']]['name'] != 'Cobalt handwoven silk':
        raise ValueError('Rama sash selected a different material primitive')
    accessor = old['accessors'][primitive['attributes']['TEXCOORD_0']]
    view = old['bufferViews'][accessor['bufferView']]
    stride = view.get('byteStride', 8)
    if (not isinstance(selected_range, list) or len(selected_range) != 2
            or any(type(i) is not int for i in selected_range)
            or not 0 <= selected_range[0] <= selected_range[1] < accessor['count']
            or accessor['componentType'] != 5126 or accessor['type'] != 'VEC2'
            or 'sparse' in accessor or accessor.get('normalized', False) or stride < 8 or stride % 4):
        raise ValueError('Rama sash UV record contract differs')
    base = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    cursor, changed = 0, 0
    for vertex in range(selected_range[0], selected_range[1] + 1):
        start = base + vertex * stride
        end = start + 8
        if start < cursor or end > len(old_bin) or end > view.get('byteOffset', 0) + view['byteLength']:
            raise ValueError('Rama sash selected UV record is outside its binary view')
        if old_bin[cursor:start] != new_bin[cursor:start]:
            raise ValueError('Rama sash changed nonselected UV or non-UV payload')
        u, v = struct.unpack_from('<ff', old_bin, start)
        if new_bin[start:end] != struct.pack('<ff', u * 0.2, v * 0.95):
            raise ValueError('Rama sash selected UV differs from exact float32 scale replay')
        changed += sum(a != b for a, b in zip(old_bin[start:end], new_bin[start:end]))
        cursor = end
    if old_bin[cursor:] != new_bin[cursor:]:
        raise ValueError('Rama sash changed nonselected UV or non-UV payload')
    return {'json_exact': True, 'outside_selected_uv_bytes_exact': True, 'scale_replay_exact': True,
            'selected_vertices': selected_range[1] - selected_range[0] + 1, 'changed_bytes': changed}


def _validate_rama_finish_notice(project, notice, notice_path):
    if json.dumps(notice, sort_keys=True) != json.dumps(rama_finish_notice(), sort_keys=True):
        raise ValueError('Rama schema6 ordered edit declaration differs from the fixed reviewed stages')
    archived = _rama_source(project, RAMA_CROWN_NOTICE_HISTORY, RAMA_CROWN_NOTICE_HISTORY_SHA)
    crown = json.loads((project / RAMA_CROWN_NOTICE_HISTORY).read_text())
    history = _validate_rama_crown_notice(project, crown, project / RAMA_CROWN_NOTICE_HISTORY,
                                         historical_runtime=True)
    sources = history['sources']
    sources[RAMA_CROWN_NOTICE_HISTORY] = archived
    stage = notice['editStages'][1]
    _rama_fixed_dependencies(project, stage['generatedDependencies'], RAMA_SASH_DEPENDENCIES, sources)
    metadata = json.loads((project / f'{RAMA_SASH_BASE}/candidate-r2/manifest.json').read_text())
    if (type(metadata.get('schema')) is not int or metadata['schema'] != 1
            or metadata.get('generator_sha256') != RAMA_SASH_DEPENDENCIES[f'{RAMA_SASH_BASE}/build_candidate.py']
            or metadata.get('scale_uv') != [0.2, 0.95] or len(metadata.get('lods', [])) != 3):
        raise ValueError('Rama sash generator/metadata ancestry differs')
    costs = {}
    for (level, (name, sha, size, first, last)), binding, row in zip(
            RAMA_SASH_OUTPUTS.items(), stage['runtimeAssets'], metadata['lods']):
        if (row.get('file') != name or row.get('input_sha256') != binding['inputSha256']
                or row.get('output_sha256') != sha or row.get('mesh') != 2 or row.get('primitive') != 3):
            raise ValueError('Rama sash LOD manifest differs from input/output bindings')
        for path in (binding['asset'], binding['authoredAsset']):
            sources[path] = _rama_source(project, path, sha)
            if sources[path]['bytes'] != size:
                raise ValueError('Rama sash GLB size differs')
        proof = rama_sash_preservation(project / binding['inputAsset'], project / binding['asset'], [first, last])
        if any(proof[key] != row.get(key) for key in proof if key != 'scale_replay_exact'):
            raise ValueError('Rama sash direct preservation differs from the reviewed manifest')
        costs[level] = proof
    return {**history, 'notice': record(notice_path), 'sources': sources,
            'editStages': notice['editStages'], 'sashPreservation': costs,
            'historicalCrown': {'path': RAMA_CROWN_NOTICE_HISTORY, **archived}}


def json_write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


# Raw font/license identities are stable source pins. Imported resource hashes
# are deliberately measured for each export: Godot may generate cache metadata
# differently in a clean checkout, so those hashes are not permanent constants.
BUNDLED_FONT_FILES = {
    'assets/fonts/NotoSans-Regular.ttf': {'bytes': 512672, 'sha256': '89c3c497f618fdaa0b2d1e98fef93582f28c71debd2c4a8cdf41f190ced2909d'},
    'assets/fonts/NotoSerif-Regular.ttf': {'bytes': 588876, 'sha256': '9d7583b7dc9e812afd32a14280c5cac3160012efe50c8d08938f4fea266ff67f'},
    'assets/fonts/DejaVuSans.ttf': {'bytes': 759720, 'sha256': '57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e'},
}
BUNDLED_FONT_NOTICES = {
    'NOTICE/Noto-fonts/COPYRIGHT.txt': '075f91382875da1c4b491f1facf2586f55448705133264d98ce15cab6211b125',
    'NOTICE/Noto-fonts/manifest.json': 'ee39170795d70e44cb7af8fe36fe71996b9b54b511eb62603d71e85dfb38ac42',
    'NOTICE/Noto-fonts/README.md': 'bdc131e443fd2f312a28aab79a910f2bfcd910954b4fff40fda3ba19d42bee30',
    'NOTICE/DejaVu-font/COPYRIGHT.txt': '63d3ba759d12804c5b31a9d5940d855c1820d1f5999e6b0872eb1c7ff045fbc9',
    'NOTICE/DejaVu-font/manifest.json': 'b546663108a0d4f4eb052a13ea35d945572b1e551a426e9db0e7f8dbdce99508',
}


def validate_bundled_font_notices(project: Path) -> dict:
    return {path: _rama_source(project.resolve(), path, sha) for path, sha in BUNDLED_FONT_NOTICES.items()}


def validate_bundled_font_sources(project: Path | None = None) -> dict:
    project = (project or PROJECT).resolve()
    records = validate_bundled_font_notices(project)
    for path, expected in BUNDLED_FONT_FILES.items():
        records[path] = _rama_source(project, path, expected['sha256'])
        if records[path] != expected:
            raise ValueError('Bundled font byte count differs: ' + path)
    return records


def _font_resource_path(source: str, resource: str) -> str:
    expected = r'res://\.godot/imported/' + re.escape(Path(source).name) + r'-[0-9a-f]{32}\.fontdata'
    if not isinstance(resource, str) or re.fullmatch(expected, resource) is None:
        raise ValueError('Bundled font import resource path is malformed: ' + source)
    return resource.removeprefix('res://')


def _font_import_target(payload: bytes, source: str) -> str:
    """Validate the remap that Godot retains after trimming export descriptors."""
    text = payload.rstrip(b'\x00').decode('utf-8')
    config = configparser.ConfigParser(interpolation=None, strict=True, delimiters=('=',))
    config.optionxform = str
    try:
        config.read_string(text)
    except configparser.Error as error:
        raise ValueError('Bundled font descriptor has ambiguous sections/keys: ' + source) from error
    required = {'path', 'importer', 'type'}
    if (config.defaults() or not config.has_section('remap')
            or any(required.intersection(config[section]) for section in config.sections() if section != 'remap')
            or not required.issubset(config['remap'])):
        raise ValueError('Bundled font descriptor requires explicit [remap] keys: ' + source)
    values = {}
    for key in required:
        match = re.fullmatch(r'"([^"\r\n]+)"', config['remap'][key])
        if match is None:
            raise ValueError('Bundled font remap value is malformed: ' + source)
        values[key] = match[1]
    if values['importer'] != 'font_data_dynamic' or values['type'] != 'FontFile':
        raise ValueError('Bundled font import descriptor is malformed: ' + source)
    _font_resource_path(source, values['path'])
    return values['path']


def prove_imported_font_bindings(godot: Path, output: Path, project: Path | None = None) -> dict:
    """Load copies of this export's imported fonts in an isolated font-only tree.

    No import or world scene runs here. FontFile.data proves that each actual
    imported resource embeds its pinned raw TTF. The copied resource payloads
    must then appear byte-identically in the PCK made from this same export.
    """
    project = (project or PROJECT).resolve()
    sources = validate_bundled_font_sources(project)
    imports = {}
    for source in BUNDLED_FONT_FILES:
        config_path = source + '.import'
        config_record = _rama_source(project, config_path, digest(project / config_path))
        config = (project / config_path).read_text()
        resource_path = _font_import_target(config.encode(), source)
        source_files = re.findall(r'^source_file="([^"]+)"$', config, re.M)
        if source_files != ['res://' + source]:
            raise ValueError('Bundled font import does not bind the required source: ' + source)
        resource = _font_resource_path(source, resource_path)
        payload = _rama_source(project, resource, digest(project / resource))
        imports[source] = {'import_config': {'path': config_path, **config_record},
                           'resource': {'path': resource_path, **payload}}
    paths = json.dumps(['res://' + path for path in BUNDLED_FONT_FILES])
    script = '''extends SceneTree
func _initialize() -> void:
    var report_path := ""
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--report="):
            report_path = arg.trim_prefix("--report=")
    var result := {"schema": 1, "fonts": {}}
    var failed := false
    for path in FONT_PATHS:
        var font := load(path) as FontFile
        if font == null:
            failed = true
            continue
        var hash := HashingContext.new()
        hash.start(HashingContext.HASH_SHA256)
        hash.update(font.data)
        result.fonts[path] = {"bytes": font.data.size(), "sha256": hash.finish().hex_encode()}
    var file := FileAccess.open(report_path, FileAccess.WRITE)
    if file == null:
        quit(2)
        return
    file.store_string(JSON.stringify(result, "\\t") + "\\n")
    file.close()
    quit(1 if failed else 0)
'''.replace('FONT_PATHS', paths)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='font-bindings-', dir=output.parent) as folder:
        isolated = Path(folder)
        (isolated / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="Font binding proof"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        (isolated / 'font_probe.gd').write_text(script)
        for source, entry in imports.items():
            for relative in (source, entry['import_config']['path'], entry['resource']['path'].removeprefix('res://')):
                target = isolated / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(project / relative, target)
                if record(target) != record(project / relative):
                    raise ValueError('Font source changed while preparing isolated binding proof')
        command = [str(godot), '--headless', '--path', str(isolated), '--script', 'res://font_probe.gd', '--', '--report=' + str(output)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        output.with_suffix('.log').write_text(result.stdout + result.stderr)
        if result.returncode or 'SCRIPT ERROR:' in result.stdout + result.stderr or '\nERROR:' in result.stdout + result.stderr:
            raise ValueError('Actual FontFile binding proof failed; inspect ' + str(output.with_suffix('.log')))
    observed = json.loads(output.read_text())
    expected = {'schema': 1, 'fonts': {'res://' + path: record for path, record in BUNDLED_FONT_FILES.items()}}
    if observed != expected:
        raise ValueError('Imported FontFile.data differs from the exact bundled raw TTFs')
    if sources != validate_bundled_font_sources(project):
        raise ValueError('Bundled font sources or licenses changed during binding proof')
    for source, entry in imports.items():
        for kind in ('import_config', 'resource'):
            record_ = entry[kind]
            relative = record_['path'].removeprefix('res://')
            if _rama_source(project, relative, record_['sha256']) != {k: record_[k] for k in ('bytes', 'sha256')}:
                raise ValueError('Imported font changed during binding proof')
        entry['decoded_raw_ttf'] = observed['fonts']['res://' + source]
    return {'schema': 1, 'sources': sources, 'imports': imports,
            'probe_sha256': hashlib.sha256(script.encode()).hexdigest(), 'probe_result': record(output),
            'scope': 'Same-export imported resource bytes with actual FontFile.data SHA256 equal to pinned raw TTFs; no platform-independent cache hash assumption.'}


def qualify_bundled_font_package(pack: dict, bindings: dict, project: Path | None = None) -> dict:
    sources = validate_bundled_font_sources(project)
    if (not isinstance(bindings, dict) or type(bindings.get('schema')) is not int
            or bindings['schema'] != 1 or bindings.get('sources') != sources
            or not isinstance(bindings.get('imports'), dict) or set(bindings['imports']) != set(BUNDLED_FONT_FILES)):
        raise ValueError('Font package qualification lacks this export\'s verified complete source bindings')
    verified = {}
    for source, expected in BUNDLED_FONT_FILES.items():
        binding = bindings['imports'][source]
        resource = binding.get('resource', {})
        _font_resource_path(source, resource.get('path'))
        if binding.get('decoded_raw_ttf') != expected:
            raise ValueError('Font package binding decoded a substituted raw TTF: ' + source)
        matches = [entry for entry in pack.get('entries', [])
                   if entry.get('path', '').removeprefix('res://') == resource['path'].removeprefix('res://')]
        if (len(matches) != 1 or any(matches[0].get(k) != resource.get(k) for k in ('bytes', 'sha256'))
                or matches[0].get('stored_md5_verified') is not True):
            raise ValueError('Required exact font payload missing or substituted in PCK: ' + source)
        remaps = [entry for entry in pack.get('entries', [])
                  if entry.get('path', '').removeprefix('res://') == source + '.import']
        if (len(remaps) != 1 or remaps[0].get('font_import_target') != resource['path']
                or remaps[0].get('stored_md5_verified') is not True):
            raise ValueError('Required font runtime remap missing or substituted in PCK: ' + source)
        verified[source] = resource
    return {'sources': sources, 'packed_fonts': verified, 'all_three_exact_font_payloads_present': True,
            'notices_required_outside_pck': list(BUNDLED_FONT_NOTICES)}


def source_state() -> dict:
    files = []
    for directory in ('scripts', 'shaders', 'scenes', 'assets'):
        files.extend(p for p in (PROJECT / directory).rglob('*') if p.is_file())
    files.extend([PROJECT / 'project.godot', PROJECT / 'export_presets.cfg'])
    records = {str(p.relative_to(PROJECT)): record(p) for p in sorted(files)}
    signature = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return {'sha256': signature, 'files': records}


def git_context() -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(['git', *args], cwd=REPOSITORY, text=True).strip()
    return {'head': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
            'native_worktree_status': git('status', '--short', '--', 'games/yuga-native')}


FIRST_LOAD_RESOURCES = ('scenes/boot.tscn', 'scripts/boot.gd',
                        'scripts/scene_transition.gd', 'scripts/loading_presentation.gd', 'scripts/launch_shell.gd',
                        'scripts/hero_ui_theme.gd')
GRAPHICS_SCRIPT_RESOURCES = (
    'scripts/lane_infantry_art.gd', 'scripts/environment_surface_finish.gd',
    'scripts/rama_ability_glyph.gd', 'scripts/rama_surface_finish.gd',
    'scripts/world_roof_loggia.gd',
)
GRAPHICS_DIRECT_RESOURCES = ('assets/environment-finish/masonry.gdshader',
                             'assets/hero-finish/g1-manifest.json',
                             'assets/hero-finish/s1-manifest.json')
GRAPHICS_TEXTURE_RESOURCES = {
    'assets/hero-finish/hair-bundle-roughness.png':
        '.godot/imported/hair-bundle-roughness.png-72ae2ebe2b8005e106f441ea2c4cfa15.ctex',
    'assets/hero-finish/forged-gold-roughness.png':
        '.godot/imported/forged-gold-roughness.png-80aebbe05d54ced6709fe5d72aaa378a.ctex',
    'assets/hero-finish/s1-hammered-gold-roughness.png':
        '.godot/imported/s1-hammered-gold-roughness.png-c93c92f35fe086748d0140298caef508.ctex',
}
# The optional upper-hair helper is not activated by this package contract.


def _graphics_texture_target(payload: bytes, source: str) -> str:
    """Read the single exported texture remap; fixed source descriptors are pinned above."""
    section = None
    targets = []
    remap_sections = 0
    for raw in payload.rstrip(b'\x00').decode('utf-8').splitlines():
        line = raw.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            remap_sections += section == 'remap'
        if re.match(r'path\s*=', line):
            match = re.fullmatch(r'path\s*=\s*"(res://[^"\r\n]+)"', line)
            if section != 'remap' or match is None:
                raise ValueError('Graphics texture remap is malformed: ' + source)
            targets.append(match[1].removeprefix('res://'))
    if remap_sections != 1 or targets != [GRAPHICS_TEXTURE_RESOURCES[source]]:
        raise ValueError('Graphics texture remaps to an unexpected target: ' + source)
    return targets[0]


def _first_load_remap(payload: bytes, source: str) -> str:
    config = configparser.ConfigParser(interpolation=None, strict=True, delimiters=('=',))
    config.optionxform = str
    try:
        config.read_string(payload.rstrip(b'\x00').decode('utf-8'))
    except configparser.Error as error:
        raise ValueError('First-load resource remap is malformed: ' + source) from error
    if config.defaults() or config.sections() != ['remap'] or set(config['remap']) != {'path'}:
        raise ValueError('First-load resource requires one explicit remap path: ' + source)
    match = re.fullmatch(r'"(res://[^"\r\n]+)"', config['remap']['path'])
    if match is None:
        raise ValueError('First-load resource remap target is malformed: ' + source)
    target = match[1].removeprefix('res://')
    if source.endswith('.gd'):
        valid = target == source + 'c'
    else:
        valid = re.fullmatch(r'\.godot/exported/[0-9]+/export-[0-9a-f]{32}-'
                            + re.escape(Path(source).stem) + r'\.scn', target) is not None
    if not valid:
        raise ValueError('First-load resource remaps to an unexpected target: ' + source)
    return target


def _qualify_first_load_resources(entries: list, resources=FIRST_LOAD_RESOURCES) -> dict:
    result = {}
    for source in resources:
        matches = [entry for entry in entries
                   if entry['path'].removeprefix('res://') in (source, source + '.remap')]
        if len(matches) != 1:
            raise ValueError('Required first-load resource missing or ambiguous: ' + source)
        binding = matches[0]
        if binding['path'].endswith('.remap'):
            target = binding.get('first_load_remap_target')
            targets = [entry for entry in entries if entry['path'].removeprefix('res://') == target]
            if len(targets) != 1:
                raise ValueError('First-load remap destination missing or ambiguous: ' + source)
            binding = targets[0]
        result[source] = {key: binding[key] for key in ('path', 'bytes', 'sha256')}
    return result


def _qualify_graphics_resources(entries: list) -> dict:
    result = _qualify_first_load_resources(entries, GRAPHICS_SCRIPT_RESOURCES)
    by_path = {entry['path'].removeprefix('res://'): entry for entry in entries}
    for source in GRAPHICS_DIRECT_RESOURCES:
        if source not in by_path:
            raise ValueError('Required graphics resource missing: ' + source)
        result[source] = by_path[source]
    for source, target in GRAPHICS_TEXTURE_RESOURCES.items():
        descriptor = by_path.get(source + '.import', {})
        if descriptor.get('graphics_texture_target') != target or target not in by_path:
            raise ValueError('Required graphics texture import/payload missing: ' + source)
        result[source] = by_path[target]
    return result


def inspect_pack(path: Path) -> dict:
    """Read Godot v2/v3 PCK directory and verify every member's stored MD5.

    Layout reference: godotengine/godot 4.6-stable,
    core/io/file_access_pack.cpp PackedSourcePCK::try_open_pack.
    MD5 here verifies the engine's existing pack integrity field; SHA-256 also
    records every actual payload. It is not used as a security signature.
    """
    data = path.read_bytes()
    if len(data) < 100 or data[:4] != b'GDPC':
        raise ValueError('Missing Godot PCK magic/header')
    version, major, minor, patch, flags = struct.unpack_from('<5I', data, 4)
    file_base = struct.unpack_from('<Q', data, 24)[0]
    if version not in (2, 3) or (major, minor, patch) != (4, 6, 3):
        raise ValueError(f'Unexpected pack version/engine: {version}, {major}.{minor}.{patch}')
    if flags & ~2:  # 2 is relative file-base; encrypted or sparse not accepted.
        raise ValueError(f'Unsupported/encrypted pack flags: {flags}')
    position = struct.unpack_from('<Q', data, 32)[0] if version == 3 else 96
    if position + 4 > len(data):
        raise ValueError('Pack directory is outside file')
    count = struct.unpack_from('<I', data, position)[0]
    position += 4
    if count < 10 or count > 10000:
        raise ValueError(f'Unexpected packed resource count: {count}')
    entries = []
    seen = set()
    for _ in range(count):
        length = struct.unpack_from('<I', data, position)[0]
        position += 4
        if length > 4096 or position + length + 36 > len(data):
            raise ValueError('Invalid packed resource entry bounds')
        name = data[position:position + length].rstrip(b'\x00').decode('utf-8')
        position += length
        offset, size = struct.unpack_from('<QQ', data, position)
        expected_md5 = data[position + 16:position + 32]
        entry_flags = struct.unpack_from('<I', data, position + 32)[0]
        position += 36
        if entry_flags:
            raise ValueError(f'Encrypted/removal/delta entry is not allowed: {name}')
        relative = name.removeprefix('res://')
        canonical = PurePosixPath(relative)
        parts = canonical.parts
        if (not parts or '..' in parts or relative.startswith('/') or '\\' in relative
                or relative != canonical.as_posix() or relative in seen):
            raise ValueError(f'Unsafe or duplicate pack path: {name}')
        seen.add(relative)
        if parts[0] not in {'.godot', 'assets', 'scripts', 'shaders', 'scenes', 'project.binary'}:
            raise ValueError(f'Unexpected runtime resource directory: {name}')
        if parts[0] == '.godot' and len(parts) > 1 and parts[1] not in {
            'imported', 'exported', 'global_script_class_cache.cfg', 'uid_cache.bin'}:
            raise ValueError(f'Unexpected Godot cache resource: {name}')
        if any(SECRET_NAME.search(part) or part == '.env' for part in parts):
            raise ValueError(f'Potential credential filename in pack: {name}')
        start = file_base + offset
        if start < 0 or start + size > len(data):
            raise ValueError(f'Packed payload exceeds file bounds: {name}')
        payload = data[start:start + size]
        if hashlib.md5(payload).digest() != expected_md5:
            raise ValueError(f'Packed payload MD5 mismatch: {name}')
        if SECRET_CONTENT.search(payload):
            raise ValueError(f'Potential credential marker in payload: {name}')
        entry = {'path': name, 'bytes': size, 'sha256': hashlib.sha256(payload).hexdigest(),
                 'stored_md5_verified': True}
        if relative.endswith('.ttf.import') and relative[:-7] in BUNDLED_FONT_FILES:
            entry['font_import_target'] = _font_import_target(payload, relative[:-7])
        if relative.endswith('.remap') and relative[:-6] in FIRST_LOAD_RESOURCES + GRAPHICS_SCRIPT_RESOURCES:
            entry['first_load_remap_target'] = _first_load_remap(payload, relative[:-6])
        if relative.endswith('.import') and relative[:-7] in GRAPHICS_TEXTURE_RESOURCES:
            entry['graphics_texture_target'] = _graphics_texture_target(payload, relative[:-7])
        entries.append(entry)
    required = ('rama.glb-', 'rama-production.glb-', 'rama-hero.glb-', 'lanka_courtyard.glb-',
                'architecture.glb-', 'nature.glb-', 'assets/world/confluence-map.json',
                'production_water.gdshader', 'world_water.gdshader', 'project.binary',
                'world_ground.gdshader', 'world_ground_common.gdshaderinc',
                'courtyard.tscn', 'confluence_world.tscn', 'combat_film.tscn',
                'ravana-sentinel.glb-', 'duel-motion-rama', 'duel-motion-ravana',
                'assets/cinematics/confluence-duel.json', 'confluence-duel-mix.wav-',
                'duel_energy.gdshader', 'scripts/input_bindings.gd', 'scripts/controls_overlay.gd',
                'scripts/player_traversal.gd', 'scripts/traversal_pose.gd',
                'scripts/relay_control.gd', 'scripts/relay_session.gd', 'scripts/relay_art.gd',
                'scripts/traversal_landmarks.gd', 'scripts/traversal_stone.gdshader', 'scripts/lane_army.gd', 'scripts/lane_minion.gd',
                'scripts/lane_unit_art.gd', 'scripts/traversal_audio.gd', 'lane-procession-loop.wav-',
                'grapple_lock.wav-', 'grapple_release.wav-', 'flight_start.wav-',
                'flight_exhaust.wav-', 'flight_recharge.wav-', 'minion_hit.wav-', 'coin.wav-', 'scripts/lane_vehicle_art.gd', 'scripts/siege_effects.gd',
                'cannon_windup.wav-', 'cannon_impact.wav-',
                'chariot_windup.wav-', 'chariot_impact.wav-', 'assets/audio/siege/provenance.json',
                'scripts/ultimate_rules.gd', 'scripts/ultimate_session.gd', 'scripts/ultimate_effects.gd',
                'scripts/invocation_panel.gd', 'scripts/invocation_audio.gd',
                'scripts/rama_ability_kit.gd', 'scripts/rama_ability_effects.gd',
                'scripts/rama_hero_runtime.gd', 'scripts/rama_vitals.gd',
                'scripts/rama_motion.gd', 'assets/animations/rama_hero_motion.tres',
                'scripts/rama_hero_hud.gd', 'scripts/rama_hero_panel.gd',
                'scripts/hero_ui_theme.gd', 'scripts/rama_practice_army.gd',
                'scripts/rama_practice_target.gd', 'shaders/rama_ribbon.gdshader',
                'assets/design/rama-ability-kit.json',
                'assets/design/hero-codex.json', 'assets/design/native-ultimate-rules.json',
                'assets/audio/invocations/manifest.json',
                *[f'.godot/imported/{cue}.wav-' for cue in (
                    'windup', 'cancel', 'rama-release', 'ravana-release', 'arjuna-release',
                    'duryodhana-release', 'hanuman-release', 'karna-release', 'bhima-release',
                    'meghnad-release', 'sita-release', 'draupadi-release', 'subhadra-release',
                    'hidimbi-release', 'chitrangada-release', 'ulupi-release')])
    for item in required:
        if not any(item in entry['path'] for entry in entries):
            raise ValueError(f'Required runtime resource missing: {item}')
    return {'format': version, 'engine': f'{major}.{minor}.{patch}', 'entries': entries,
            'entry_count': count, 'all_entry_md5_verified': True,
            'first_load_resources': _qualify_first_load_resources(entries),
            'graphics_resources': _qualify_graphics_resources(entries),
            'no_tools_tests_documents_or_credential_markers': True, **record(path)}


def run_export(godot: Path, platform: str, pack: Path, log: Path) -> None:
    env = os.environ.copy()
    for name, suffix in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        env.setdefault(name, str(PROJECT / 'build' / 'xdg' / suffix))
        Path(env[name]).mkdir(parents=True, exist_ok=True)
    command = [str(godot), '--headless', '--path', str(PROJECT), '--export-pack', PLATFORMS[platform], str(pack)]
    with log.open('w') as stream:
        result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=240)
    if result.returncode:
        raise RuntimeError(f'{platform} PCK export failed; inspect {log}')
    text = log.read_text(errors='replace')
    if 'SCRIPT ERROR:' in text or '\nERROR:' in text:
        raise RuntimeError(f'{platform} export logged an error; inspect {log}')


def _native_contract_inputs(project: Path) -> dict:
    """Finite source closure used by the current contract checker, without Godot."""
    repository = project.parents[1]
    paths = {
        'games/yuga-native/tools/check-native-contracts.py',
        'games/yuga-native/tools/package-native.py',
        'games/yuga-native/assets/contracts/native-contracts-v1.json',
        'games/yuga-native/assets/contracts/native-envelope-v1.schema.json',
        'games/yuga-native/scripts/native_contracts.gd',
        'games/yuga/shared/map.ts', 'games/yuga/shared/types.ts',
        'games/yuga-native/assets/world/confluence-map.json',
        'games/yuga-native/docs/GAME_DESIGN_MASTER.md',
        'games/yuga-native/scripts/relay_control.gd',
        *[f'games/yuga-native/tests/fixtures/contracts/native-content{revision}-{kind}.json'
          for revision in (3, 4, 5) for kind in ('catalog', 'descriptor')],
    }
    catalog = json.loads((project / 'assets/contracts/native-contracts-v1.json').read_text())
    for profile in catalog['profiles']:
        paths.update(profile['content_sources'])
    result = {}
    for relative in sorted(paths):
        name = PurePosixPath(relative)
        path = repository / relative
        if (name.is_absolute() or '..' in name.parts or '\\' in relative
                or name.as_posix() != relative or path.is_symlink()
                or not path.resolve().is_relative_to(repository) or not path.is_file()):
            raise ValueError('Missing or unsafe native contract input: ' + relative)
        result[relative] = record(path)
    return result


def prove_native_contract_sources(output: Path, project: Path | None = None) -> dict:
    project = (project or PROJECT).resolve()
    before = _native_contract_inputs(project)
    output.parent.mkdir(parents=True, exist_ok=True)
    log = output.with_suffix('.log')
    if output.exists() or log.exists():
        raise ValueError('Native contract proof needs fresh report/log paths')
    with log.open('w') as stream:
        process = subprocess.run([sys.executable, str(project / 'tools/check-native-contracts.py'),
                                  '--report', str(output)], cwd=project.parents[1],
                                 stdout=stream, stderr=subprocess.STDOUT, timeout=60)
    if process.returncode or not output.is_file():
        raise ValueError('Native contract source check failed; inspect ' + str(log))
    report = json.loads(output.read_text())
    checks = report.get('checks')
    if (report.get('passed') is not True or not isinstance(checks, list) or not checks
            or any(not isinstance(item, dict) or item.get('passed') is not True
                   or not isinstance(item.get('name'), str) for item in checks)):
        raise ValueError('Native contract proof lacks nonempty successful checks')
    names = [item['name'] for item in checks]
    catalog = json.loads((project / 'assets/contracts/native-contracts-v1.json').read_text())
    required = {'three_exact_profiles', 'per_profile_content_revisions', 'wire_versions_unchanged'}
    for profile in catalog['profiles']:
        required.add(profile['id'] + '_content_aggregate')
        required.update(profile['id'] + '_content_' + path for path in profile['content_sources'])
    if len(set(names)) != len(names) or not required.issubset(names):
        raise ValueError('Native contract proof omits required source checks')
    report_sources = ('assets/contracts/native-contracts-v1.json', 'assets/contracts/native-envelope-v1.schema.json',
                      'tools/check-native-contracts.py', 'scripts/native_contracts.gd')
    expected = {'games/yuga-native/' + path: before['games/yuga-native/' + path]['sha256']
                for path in report_sources}
    if report.get('source_sha256') != expected or _native_contract_inputs(project) != before:
        raise ValueError('Native contract report/source bindings changed or differ')
    return {'schema': 1, 'sources': before, 'report': record(output), 'checks': len(checks),
            'scope': 'Actual source-pin checker, nonempty successful checks and exact stable catalog/tool/source/fixture bytes; no network or gameplay acceptance.'}


def validate_runtime_script_uids(project: Path | None = None) -> dict:
    """Reject missing runtime UID metadata before the editor can create it.

    Test/tool sidecars are generated non-runtime metadata and are outside this
    gate. The existing full runtime source-stability guard still runs at export.
    """
    project = (project or PROJECT).resolve()
    script_root = project / 'scripts'
    for path in [script_root, *script_root.rglob('*')]:
        if path.is_symlink():
            raise ValueError('Runtime scripts contain a symlink: ' + str(path.relative_to(project)))
    scripts = sorted(script_root.rglob('*.gd'))
    if not scripts:
        raise ValueError('Runtime UID preflight found no scripts')
    seen = {}
    records = {}
    for script in scripts:
        if not script.is_file():
            raise ValueError('Runtime script is not a regular file: ' + str(script.relative_to(project)))
        sidecar = script.with_suffix(script.suffix + '.uid')
        relative = str(sidecar.relative_to(project))
        if not sidecar.is_file() or sidecar.is_symlink():
            raise ValueError('Missing regular runtime UID sidecar: ' + relative)
        payload = sidecar.read_bytes()
        # Godot 4.6.3 ResourceUID::id_to_text uses canonical base34, no
        # leading zero ('a'), and a nonnegative signed-63-bit identifier.
        if not re.fullmatch(rb'uid://(?:a|[b-y0-8][a-y0-8]{0,12})\n', payload):
            raise ValueError('Malformed runtime UID sidecar: ' + relative)
        uid = payload.decode('ascii').strip()
        numeric_id = 0
        for character in uid.removeprefix('uid://'):
            numeric_id = numeric_id * 34 + 'abcdefghijklmnopqrstuvwxy012345678'.index(character)
        if numeric_id > 0x7FFFFFFFFFFFFFFF:
            raise ValueError('Out-of-range runtime UID sidecar: ' + relative)
        if numeric_id in seen:
            raise ValueError('Duplicate runtime UID: ' + relative + ' and ' + seen[numeric_id])
        seen[numeric_id] = relative
        records[relative] = {'uid': uid, **record(sidecar)}
    return {'scripts': len(scripts), 'sidecars': records,
            'scope': 'Runtime scripts only; format and uniqueness, not import or gameplay qualification.'}


def export_all(args: argparse.Namespace, build: Path) -> dict:
    runtime_uids = validate_runtime_script_uids()
    engines = linux_engine_selection(args)
    native_contracts = prove_native_contract_sources(build / 'native-contracts-export.json')
    subprocess.run([sys.executable, str(PROJECT / 'tools/stage-world.py'), '--check'], check=True)
    version = engines['exporter']['version']
    font_bindings = prove_imported_font_bindings(args.linux_engine, build / 'font-bindings-export.json')
    rama = PROJECT / 'assets/heroes/rama.glb'
    original_rama = REPOSITORY / 'games/yuga/client/assets/heroes/rama.glb'
    if digest(rama) != digest(original_rama):
        raise ValueError('Staged Rama asset differs from the existing YUGA source model')
    production = json.loads((PROJECT / 'NOTICE/RAMA-PRODUCTION-PROVENANCE.json').read_text())
    if digest(PROJECT / 'assets/heroes/rama-production.glb') != production['sha256']:
        raise ValueError('Production Rama notice differs from the active model')
    rama_hero_notice = validate_rama_hero_notice()
    world_notice = json.loads((PROJECT / 'NOTICE/CONFLUENCE-WORLD-PROVENANCE.json').read_text())
    for entry in world_notice['assets']:
        if digest(PROJECT / entry['asset']) != entry['sha256']:
            raise ValueError('Confluence world notice differs from the active asset')
    if digest(PROJECT / world_notice['map']['path']) != world_notice['map']['sha256']:
        raise ValueError('Confluence world notice differs from the runtime layout')
    film_notice = json.loads((PROJECT / 'NOTICE/CONFLUENCE-DUEL-PROVENANCE.json').read_text())
    for entry in film_notice['assets']:
        if digest(PROJECT / entry['asset']) != entry['sha256']:
            raise ValueError('Confluence duel notice differs from the active asset: ' + entry['asset'])
    audio_notice = json.loads((PROJECT / 'NOTICE/TRAVERSAL-AUDIO-PROVENANCE.json').read_text())
    if len(audio_notice['assets']) != 8:
        raise ValueError('Expected the original traversal loop and seven cues')
    for entry in audio_notice['assets']:
        if record(PROJECT / entry['asset']) != {key: entry[key] for key in ('bytes', 'sha256')}:
            raise ValueError('Traversal audio provenance differs from active asset: ' + entry['asset'])
    subprocess.run([sys.executable, str(PROJECT / "tools/audio/build-siege-audio.py"), "--check"], check=True)
    subprocess.run([sys.executable, str(PROJECT / "tools/audio/build-invocation-audio.py"), "--check"], check=True)
    before = source_state()
    packs = {}
    for platform in PLATFORMS:
        pack = build / f'yuga-native-{platform}.pck'
        run_export(args.linux_engine, platform, pack, build / f'export-{platform}.log')
        packs[platform] = inspect_pack(pack)
        packs[platform]['font_qualification'] = qualify_bundled_font_package(packs[platform], font_bindings)
    after = source_state()
    if before['sha256'] != after['sha256']:
        raise ValueError('Runtime source changed during export; rerun on a frozen/imported tree')
    if rama_hero_notice != validate_rama_hero_notice():
        raise ValueError('Rama hero provenance changed during export; rerun on a frozen tree')
    if native_contracts['sources'] != _native_contract_inputs(PROJECT):
        raise ValueError('Native contract inputs changed during export')
    linux_engine_selection(args, engines)
    manifest = {'schema': 1, 'kind': 'native-pck-export', 'godot_version': version,
                'engine_selection': engines,
                'git': git_context(), 'source': after, 'packs': packs,
                'rama_matches_existing_yuga_source': True,
                'rama_hero_provenance': rama_hero_notice,
                'native_contracts': native_contracts,
                'font_bindings': font_bindings, 'runtime_uids': runtime_uids,
                'limits': ['No Windows execution performed by this tool.',
                           'PCK and archive checks do not establish visual quality or gameplay acceptance.']}
    json_write(build / 'native-export-manifest.json', manifest)
    return manifest


def start_readme(platform: str, engines: dict | None = None) -> str:
    start = './launch.sh' if platform == 'linux' else 'launch.bat'
    runtime_text = ('The bundled official Godot 4.6.3\n'
                    'engine opens yuga-native.pck directly using --main-pack. This portable package\n'
                    'contains the full engine binary and is larger than a release-template export.')
    if platform == 'linux' and engines and engines['linux_runtime']['provenance'] is not None:
        runtime_text = ('This Linux package uses a community-built, unmodified Godot 4.6.3\n'
                        'public-source template-debug runtime to open yuga-native.pck with --main-pack.\n'
                        'The official Linux editor binary performed PCK export and font qualification;\n'
                        'it is not the bundled Linux runtime. See NOTICE/GODOT-RUNTIME.txt for exact\n'
                        'runtime/source/build/license identities. Archive checks do not prove execution.')
    return f'''YUGA — RAMA HERO PRACTICE\nOriginal Rama combat, Confluence exploration and animated film / {platform} x86_64\n\nExtract the ENTIRE ZIP to one folder, then run {start}.\nNo Godot editor installation is required. {runtime_text}\n\nDefault controls (keyboard actions are remappable)\nWASD / arrows: move; mouse: aim; LMB: Kodanda arrow; Space: jump;\nShift: sprint; R: reload; Q: Piercing Dawn; E: Measured Step;\nC: Guardian Circle; X: Dawn Volley; F: flight; G: tether;\nCtrl: descend in flight; Esc: pause/release cursor; F2: help/remap;\nF3: Rama ability sheet; F5: reset/respawn; N: Confluence day/night.\nSettings include aim sensitivity, sound, fullscreen, shadows and night.\n\nCompatibility fallback\nRun {start} --rendering-method gl_compatibility\nThe default Forward+ renderer needs Vulkan-capable graphics. The compatibility\nrenderer omits Forward+ glow and SSAO. A recent graphics driver is recommended.\n\nScope\nThe courtyard uses Rama's actual five-action kit against five 90-health\npractice targets. Cleared targets stay down until F5. Primary attacks use a\nshort timed draw; hold-to-charge is not implemented. Four distinct abilities\nprovide a piercing arrow, collision-limited step, a protective healing circle\nand a telegraphed three-arrow volley. Guardian Circle affects Rama and eligible\nfriendly troops. Hero damage/death/respawn uses explicit offline receivers.\n\nConfluence is an offline 140 x 260 m arena with paired army waves, five troop\nroles including cannon carts and chariots, last-hit gold, core outcomes, and\nthree capture/contest/supply relays. Flight and grappling use finite energy,\ncollision limits and landing platforms. Escape opens practice and travel\nactions; F5 restores ordinary waves and neutral relays. The retained fourteen\ninvocation catalogue is a legacy study system, separate from Rama's main kit.\n\nWatch duel opens a separate 24-second scripted Rama-versus-Ravana\nSentinel film with its own animation, camera, effects and synthesized soundtrack.\nNative online matches and the full production hero roster remain unfinished.\nThis package does not establish commercial-game visual parity, human balance\nacceptance, or physical-GPU performance. Windows is packaged and archive-validated\nfrom Linux; native Windows execution has not been verified here.\n\nLicenses and provenance\nSee NOTICE/ and PACKAGE-MANIFEST.json. Original project sources and evidence:\nhttps://github.com/occult-kranti/ANDOLAN/tree/game/yuga-native-production/games/yuga-native\n\nLinux desktop runtime dependencies\nA desktop X11/Wayland session, graphics/audio drivers and standard system\nlibraries are required. The ZIP does not bundle an operating system. On Linux,\nif your unzip tool drops executable bits, run: chmod +x launch.sh godot\n'''


def copy_rama_crown_companions(project: Path, destination: Path) -> dict:
    """Keep the schema6 parent/attribution references readable in a portable ZIP."""
    copied = {}
    companions = [(RAMA_CROWN_PARENT, RAMA_CROWN_PARENT_SHA),
                  (f'{RAMA_CROWN_BASE}/NOTICE.md', RAMA_CROWN_DEPENDENCIES[f'{RAMA_CROWN_BASE}/NOTICE.md'])]
    if 'editStages' in json.loads((project / 'NOTICE/RAMA-HERO-PROVENANCE.json').read_text()):
        companions += [(RAMA_CROWN_NOTICE_HISTORY, RAMA_CROWN_NOTICE_HISTORY_SHA),
                       (f'{RAMA_SASH_BASE}/README.md', RAMA_SASH_DEPENDENCIES[f'{RAMA_SASH_BASE}/README.md'])]
    for relative, sha in companions:
        copied[relative] = _rama_source(project, relative, sha)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / relative, target)
        if record(target) != copied[relative]:
            raise ValueError('Portable crown provenance companion differs from its exact source')
    return copied


def safe_notice_copy(destination: Path) -> None:
    notices = PROJECT / 'NOTICE'
    required = ['GODOT-LICENSE.txt', 'GODOT-COPYRIGHT.txt', 'MAKEHUMAN-ASSET-LICENSE.md',
                'HERO-PROVENANCE.json', 'RAMA-PRODUCTION-PROVENANCE.json', 'RAMA-HERO-PROVENANCE.json',
                'CONFLUENCE-WORLD-PROVENANCE.json', 'CONFLUENCE-DUEL-PROVENANCE.json',
                'TPS-MOTION-NOTICE.txt', 'GODOT-TPS-UPSTREAM-LICENSE.md',
                'TRAVERSAL-AUDIO-PROVENANCE.json', 'TRAVERSAL-ARMIES.txt', 'SIEGE-VEHICLES.txt', 'MYTHIC-INVOCATIONS.txt']
    for name in required:
        if not (notices / name).is_file():
            raise ValueError(f'Required package notice is missing: NOTICE/{name}')
    for item in notices.rglob('*'):
        if item.is_symlink():
            raise ValueError('Symlinks are not allowed in package notices')
        if item.is_file():
            payload = item.read_bytes()
            if SECRET_NAME.search(item.name) or SECRET_CONTENT.search(payload):
                raise ValueError('Potential credential marker in package notices')
            target = destination / 'NOTICE' / item.relative_to(notices)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)
    validate_bundled_font_notices(destination)
    if json.loads((notices / 'RAMA-HERO-PROVENANCE.json').read_text()).get('schema') == 6:
        copy_rama_crown_companions(PROJECT, destination)


def zip_directory(staging: Path, output: Path) -> dict:
    files = sorted(p for p in staging.rglob('*') if p.is_file())
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            name = str(path.relative_to(staging.parent))
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = path.name in {'godot', 'launch.sh'}
            info.external_attr = ((0o100755 if executable else 0o100644) << 16)
            with path.open('rb') as source, archive.open(info, 'w') as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
    expected = {str(p.relative_to(staging.parent)): p for p in files}
    with zipfile.ZipFile(output) as archive:
        if set(archive.namelist()) != set(expected) or len(archive.namelist()) != len(expected):
            raise ValueError('ZIP entry set differs from staging set')
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f'ZIP CRC failure: {bad}')
        for name, source in expected.items():
            with archive.open(name) as stream:
                value = hashlib.sha256()
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    value.update(block)
            if value.hexdigest() != digest(source):
                raise ValueError(f'ZIP payload mismatch: {name}')
    return {**record(output), 'entry_count': len(files), 'all_crc_and_payload_sha256_verified': True}


def package_all(args: argparse.Namespace, build: Path, exported: dict) -> dict:
    if 'engine_selection' not in exported:
        raise ValueError('Export manifest lacks exporter/runtime identity; export with this tool before packaging')
    engines = linux_engine_selection(args, exported['engine_selection'], probe_versions=True)
    if exported.get('godot_version') != engines['exporter']['version']:
        raise ValueError('Export manifest Godot version contradicts its exporter identity')
    native_contracts = prove_native_contract_sources(build / 'native-contracts-package.json')
    if native_contracts != exported.get('native_contracts'):
        raise ValueError('Native contract sources or proof changed since export; export again before packaging')
    if source_state()['sha256'] != exported['source']['sha256']:
        raise ValueError('Runtime sources changed since PCK export; export again before packaging')
    if exported.get('rama_hero_provenance') != validate_rama_hero_notice():
        raise ValueError('Rama hero provenance changed since PCK export; export again before packaging')
    font_bindings = prove_imported_font_bindings(args.linux_engine, build / 'font-bindings-package.json')
    if font_bindings != exported.get('font_bindings'):
        raise ValueError('Font source/import bindings changed since PCK export; export again before packaging')
    results = {}
    windows_provenance = args.windows_engine.parent / 'godot-windows-provenance.json'
    verified_windows = json.loads(windows_provenance.read_text())
    windows_entry = next(entry for entry in verified_windows['files'] if entry['name'] == args.windows_engine.name)
    if digest(args.windows_engine) != windows_entry['sha256']:
        raise ValueError('Windows engine differs from its independently downloaded provenance')
    for platform in PLATFORMS:
        staging = build / f'yuga-native-{platform}-x86_64'
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        engine = (getattr(args, 'linux_runtime', None) or args.linux_engine) if platform == 'linux' else args.windows_engine
        shutil.copyfile(engine, staging / ('godot' if platform == 'linux' else 'godot.exe'))
        if platform == 'linux' and record(staging / 'godot') != {key: engines['linux_runtime'][key] for key in ('bytes', 'sha256')}:
            raise ValueError('Copied Linux runtime differs from selected identity')
        pack = build / f'yuga-native-{platform}.pck'
        actual_pack = inspect_pack(pack)
        actual_pack['font_qualification'] = qualify_bundled_font_package(actual_pack, font_bindings)
        if actual_pack['sha256'] != exported['packs'][platform]['sha256']:
            raise ValueError('PCK changed after export manifest validation')
        shutil.copyfile(pack, staging / 'yuga-native.pck')
        if platform == 'linux':
            launcher = '#!/bin/sh\nset -eu\nPACKAGE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec "$PACKAGE_DIR/godot" --main-pack "$PACKAGE_DIR/yuga-native.pck" "$@"\n'
            (staging / 'launch.sh').write_text(launcher)
            (staging / 'launch.sh').chmod(0o755)
            (staging / 'godot').chmod(0o755)
        else:
            launcher = '@echo off\r\n"%~dp0godot.exe" --main-pack "%~dp0yuga-native.pck" %*\r\n'
            (staging / 'launch.bat').write_bytes(launcher.encode())
        (staging / 'START-HERE.txt').write_text(start_readme(platform, engines), encoding='utf-8')
        safe_notice_copy(staging)
        if platform == 'linux':
            copy_public_runtime_notice(staging, engines)
        payloads = {str(p.relative_to(staging)): record(p) for p in sorted(staging.rglob('*')) if p.is_file()}
        manifest = {'schema': 1, 'platform': f'{platform}-x86_64', 'godot_version': exported['godot_version'],
                    'packaging': ('unmodified-public-template-debug-with-official-exported-pck'
                                  if platform == 'linux' and engines['linux_runtime']['provenance'] is not None
                                  else 'official-full-engine-with-exported-pck'), 'git': exported['git'],
                    'exporter': engines['exporter'],
                    'runtime': engines['linux_runtime'] if platform == 'linux' else {**record(engine), 'provenance': verified_windows},
                    'runtime_source': exported['source'], 'payloads': payloads,
                    'pck': actual_pack, 'execution_status': 'not_executed_by_packager',
                    'font_bindings': font_bindings,
                    'native_contracts': native_contracts,
                    'windows_engine_provenance': verified_windows if platform == 'windows' else None}
        json_write(staging / 'PACKAGE-MANIFEST.json', manifest)
        archive = build / f'yuga-native-{platform}-x86_64.zip'
        results[platform] = {'filename': archive.name, **zip_directory(staging, archive),
                             'engine': record(engine), 'pck': {k: actual_pack[k] for k in ['bytes', 'sha256', 'entry_count']},
                             'execution_status': 'not_executed_by_packager'}
    if native_contracts['sources'] != _native_contract_inputs(PROJECT):
        raise ValueError('Native contract inputs changed during packaging')
    linux_engine_selection(args, engines)
    aggregate = {'schema': 1, 'kind': 'native-portable-packages', 'git': exported['git'],
                 'engine_selection': engines,
                 'runtime_source_sha256': exported['source']['sha256'], 'packages': results,
                 'packaging_script': record(Path(__file__)),
                 'native_contracts': native_contracts,
                 'limits': ['Archive/PCK validation is not runtime acceptance.', 'Windows has not been executed here.']}
    json_write(build / 'native-package-manifest.json', aggregate)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--linux-engine', type=Path, default=DEFAULT_LINUX)
    parser.add_argument('--linux-runtime', type=Path, help='Optional exact reviewed public-source Linux runtime; exporter remains --linux-engine')
    parser.add_argument('--linux-runtime-provenance', type=Path, help='Required with --linux-runtime: reviewed unmodified finished-build-verification.json')
    parser.add_argument('--windows-engine', type=Path, default=DEFAULT_WINDOWS)
    parser.add_argument('--build-dir', type=Path, default=PROJECT / 'build')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--export-only', action='store_true')
    modes.add_argument('--package-only', action='store_true')
    args = parser.parse_args()
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=True)
    if args.package_only:
        exported = json.loads((build / 'native-export-manifest.json').read_text())
    else:
        exported = export_all(args, build)
    if args.export_only:
        print(json.dumps({'exported': {k: {f: v[f] for f in ['sha256', 'bytes', 'entry_count']} for k, v in exported['packs'].items()}}))
    else:
        result = package_all(args, build, exported)
        print(json.dumps({'packages': result['packages']}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'Native packaging failed: {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(1)
