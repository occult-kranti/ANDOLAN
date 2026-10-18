"""Prepare two private minimal projects; never run an importer or mutate source."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools/graphics-six'))
import snapshot

OUT = Path('/tmp/yuga-s4-diadem-import-r1')
BASELINE = Path('/tmp/yuga-s4-diadem-baseline-r1')
SHARED = Path('/tmp/yuga-desktop-recovery-r1/current-project')
EVIDENCE = Path(__file__).parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(paths, root):
    return {str(p.relative_to(root)): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in paths if p.is_file()}


def main():
    assert not OUT.exists() and not BASELINE.exists()
    shared = snapshot.verify(SHARED)
    source = ROOT / 'art/hero-finish/s4-diadem-fit/candidate-r1'
    candidate = json.loads((source / 'source-manifest.json').read_text())
    original_settings = (ROOT / 'project.godot').read_text()
    settings = original_settings.replace('run/main_scene="res://scenes/boot.tscn"\n', '')
    assert settings != original_settings
    sources = [ROOT / 'project.godot', ROOT / '.godot/uid_cache.bin'] + sorted((ROOT / 'assets/heroes').glob('rama-hero*')) + sorted((ROOT / '.godot/imported').glob('*'))
    before = inventory(sources, ROOT)
    for project in [OUT, BASELINE]:
        (project / 'assets/heroes').mkdir(parents=True)
        (project / 'project.godot').write_text(settings)
    for row in candidate['levels'].values():
        relative = Path(row['source'])
        assert sha(ROOT / relative) == row['source_sha256']
        assert sha(source / relative.name) == row['sha256']
        shutil.copyfile(source / relative.name, OUT / relative)
        shutil.copyfile(ROOT / (str(relative) + '.import'), OUT / (str(relative) + '.import'))
    # Baseline cached resources are copied, never linked to the canonical/store
    # files. They are loaded without an editor, under ordinary resource paths.
    for p in sorted((ROOT / 'assets/heroes').glob('rama-hero*')):
        if p.is_file(): shutil.copyfile(p, BASELINE / p.relative_to(ROOT))
    (BASELINE / '.godot/imported').mkdir(parents=True)
    for p in sorted((ROOT / '.godot/imported').glob('*')):
        if p.is_file(): shutil.copyfile(p, BASELINE / p.relative_to(ROOT))
    uid = ROOT / '.godot/uid_cache.bin'
    if uid.exists(): shutil.copyfile(uid, BASELINE / '.godot/uid_cache.bin')
    command = ['env', 'LP_NUM_THREADS=1', 'OPENBLAS_NUM_THREADS=1', 'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1',
               'XDG_CACHE_HOME=/tmp/yuga-s4-diadem-import-r1-user/cache',
               'XDG_CONFIG_HOME=/tmp/yuga-s4-diadem-import-r1-user/config',
               'XDG_DATA_HOME=/tmp/yuga-s4-diadem-import-r1-user/data',
               'taskset', '-c', '4', 'timeout', '120s', '/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64',
               '--headless', '--path', str(OUT), '--editor', '--import', '--quit']
    report = {'schema': 1, 'candidate_project': str(OUT), 'baseline_cached_project': str(BASELINE),
              'shared_base': str(SHARED), 'shared_marker_sha256': sha(SHARED / snapshot.MARKER),
              'shared_files': len(shared['files']), 'shared_verified_before': True,
              'engine_sha256': sha('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64'), 'command': command,
              'project_settings': {'canonical_sha256': sha(ROOT / 'project.godot'),
                                   'private_sha256': sha(OUT / 'project.godot'),
                                   'only_removed_line': 'run/main_scene="res://scenes/boot.tscn"',
                                   'all_render_and_import_settings_retained': True},
              'canonical_before': before,
              'candidate_before': inventory(sorted(OUT.rglob('*')), OUT),
              'baseline_before': inventory(sorted(BASELINE.rglob('*')), BASELINE)}
    (EVIDENCE / 'import-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Prepared isolated projects; source/shared bytes unchanged.')


if __name__ == '__main__':
    main()
