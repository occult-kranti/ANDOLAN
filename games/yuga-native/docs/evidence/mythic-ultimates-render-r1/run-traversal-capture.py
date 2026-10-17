#!/usr/bin/env python3
"""Capture actual native traversal inputs on an owned software Vulkan display.

The full take is 180 consecutive 1280x720 frames at a simulated 30 fps with
60 Hz physics. It produces a silent six-second MP4; it does not measure realtime
performance. Use --preview for 24 frames at 960x540 and three stills without video.
Every image records actual renderer draw calls, object and primitive counts.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def write_new_json(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def verify_image(output: Path, image: dict, dimensions: tuple[int, int]) -> None:
    name = image['file']
    if Path(name).name != name:
        raise ValueError('Image path must be a direct child of the evidence directory')
    path = output / name
    with path.open('rb') as source:
        header = source.read(24)
    if header[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', header[16:24]) != dimensions:
        raise ValueError(f'Invalid actual PNG dimensions: {name}')
    if (image['width'], image['height']) != dimensions:
        raise ValueError(f'Image metadata does not match actual dimensions: {name}')
    if sha256(path) != image['sha256']:
        raise ValueError(f'Image checksum mismatch: {name}')
    for key in ('draw_calls', 'rendered_objects', 'rendered_primitives'):
        if not isinstance(image.get(key), int) or image[key] <= 0:
            raise ValueError(f'Missing actual renderer counter {key}: {name}')


def validate_capture(report: dict, output: Path, project: Path, preview: bool) -> None:
    expected = 24 if preview else 180
    dimensions = (960, 540) if preview else (1280, 720)
    if not report.get('complete') or report.get('failure'):
        raise ValueError('Capture did not pass: ' + str(report.get('failure')))
    if report.get('renderer') != 'forward_plus' or report.get('display') == 'headless':
        raise ValueError('A genuine Forward+ display capture is required')
    if report.get('physics_hz') != 60 or report.get('fps') != 30:
        raise ValueError('Unexpected simulation clock configuration')
    if (report.get('width'), report.get('height')) != dimensions:
        raise ValueError('Capture resolution does not match preview/full mode')
    frames = report['frames']
    if len(frames) != expected or report.get('take_physics_ticks') != 2 * expected:
        raise ValueError('Frame count or measured physics advancement is wrong')
    previous_tick = report['take_start_tick']
    previous_draw = None
    for index, frame in enumerate(frames):
        if frame['index'] != index or frame['physics_tick_delta'] != 2 or frame['physics_tick'] - previous_tick != 2:
            raise ValueError(f'Physics sequence is not continuous at frame {index}')
        if not frame['finite'] or len(frame['pose_sha256']) != 64:
            raise ValueError(f'Actual skeletal pose is missing/invalid at frame {index}')
        if previous_draw is not None and frame['render_frame'] <= previous_draw:
            raise ValueError('Rendered frame counter did not advance')
        if frame['image']['file'] != f'frame-{index:05d}.png':
            raise ValueError('Unexpected frame filename/order')
        verify_image(output, frame['image'], dimensions)
        previous_tick, previous_draw = frame['physics_tick'], frame['render_frame']
    if len(list(output.glob('frame-*.png'))) != expected:
        raise ValueError('Extra or missing frame files')
    if len(report['stills']) != (3 if preview else 5):
        raise ValueError('Expected three preview stills or five full review stills')
    for still in report['stills']:
        verify_image(output, still['image'], dimensions)
    for resource, expected_hash in report['source_sha256'].items():
        if not resource.startswith('res://'):
            raise ValueError('Invalid source resource path')
        path = project / resource.removeprefix('res://')
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f'Runtime source changed or is missing: {resource}')
    for imported in report['imports'].values():
        path = project / imported['imported'].removeprefix('res://')
        if not imported['fresh'] or sha256(path) != imported['sha256']:
            raise ValueError('Imported asset changed during capture')
    outcomes = report['outcomes']
    if not all(outcomes.get(key) for key in ('grapple', 'visible_rope', 'pose_overlay', 'pose_finite')):
        raise ValueError('Required traversal behavior was not observed')
    if not preview and not outcomes.get('flight'):
        raise ValueError('Full take did not demonstrate flight')


def encode_video(output: Path, report_path: Path, ffmpeg: str, ffprobe: str) -> dict:
    video = output / 'yuga-traversal-preview.mp4'
    command = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
               '-framerate', '30', '-i', str(output / 'frame-%05d.png'),
               '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'medium',
               '-crf', '18', '-pix_fmt', 'yuv420p', '-frames:v', '180',
               '-movflags', '+faststart', str(video)]
    subprocess.run(command, check=True, timeout=300)
    probe_command = [ffprobe, '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(video)]
    probe = json.loads(subprocess.check_output(probe_command, timeout=30))
    streams = probe['streams']
    if len(streams) != 1 or streams[0]['codec_type'] != 'video':
        raise ValueError('The preview must contain exactly one silent video stream')
    stream = streams[0]
    if (stream['width'], stream['height']) != (1280, 720) or int(stream['nb_read_frames']) != 180:
        raise ValueError('Encoded video frame count or dimensions are wrong')
    if Fraction(stream['avg_frame_rate']) != 30 or abs(float(probe['format']['duration']) - 6.0) > .02:
        raise ValueError('Encoded video must be exactly six seconds at 30 fps')
    result = {'schema': 1, 'complete': True, 'file': video.name, 'bytes': video.stat().st_size,
              'sha256': sha256(video), 'capture_report_sha256': sha256(report_path),
              'encode_command': command, 'probe_command': probe_command, 'probe': probe,
              'scope': 'Silent video of 180 consecutive actual software-rendered input-driven frames. '
                       'The 30 fps playback rate is simulated time, not measured realtime rendering speed. '
                       'Separate staged army and overview stills are not spliced into this take.'}
    write_new_json(output / 'traversal-video.json', result)
    return result


def seed_shader_cache(source: Path | None, destination: Path) -> dict:
    """Copy only regular cache files into a new isolated cache; never reuse settings."""
    if source is None:
        return {'seeded': False}
    source = source.resolve()
    if not source.is_dir():
        raise ValueError('Shader cache seed must be an existing directory')
    paths = sorted(source.rglob('*'))
    if any(path.is_symlink() for path in paths):
        raise ValueError('Shader cache seed must not contain symbolic links')
    files = [path for path in paths if path.is_file()]
    total_bytes = sum(path.stat().st_size for path in files)
    if total_bytes > 512 * 1024 * 1024 or len(files) > 100000:
        raise ValueError('Shader cache seed exceeds the bounded copy budget')
    destination.mkdir()
    entries = {}
    for path in files:
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = sha256(path)
        shutil.copyfile(path, target)
        if sha256(target) != expected:
            raise ValueError('Shader cache seed changed during copy')
        entries[str(relative)] = expected
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    return {'seeded': True, 'source': str(source), 'files': len(files), 'bytes': total_bytes,
            'file_hash_manifest_sha256': digest,
            'scope': 'Copied shader compilation cache only; Mesa validates compatibility. No gameplay assets or user preferences are copied.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New absolute evidence directory; never overwritten')
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--runtime', type=Path, default=Path('/workspace/tooling/native-render/runtime'))
    parser.add_argument('--godot', default=shutil.which('godot'))
    parser.add_argument('--display', type=int, default=117, help='Unused owned Xvfb display [90,199]')
    parser.add_argument('--preview', action='store_true', help='24 frames at 960x540 plus three stills; full mode is 1280x720')
    parser.add_argument('--shader-cache-seed', type=Path, help='Optional prior Mesa cache directory, copied and hash-checked into the fresh isolated cache')
    parser.add_argument('--dry-run', action='store_true', help='Print the exact renderer command without starting processes')
    args = parser.parse_args()
    if not args.output.is_absolute():
        parser.error('--output must be absolute')
    output, runtime, project = args.output.resolve(), args.runtime.resolve(), args.project.resolve()
    user = output.parent / (output.name + '-user')
    xlog_path, log_path = Path(str(output) + '.xvfb.log'), Path(str(output) + '.godot.log')
    if any(path.exists() for path in (output, user, xlog_path, log_path)):
        parser.error('Choose a new output name; evidence, logs, and isolated settings are never overwritten')
    if not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        parser.error('Choose an unused display in [90,199]')
    if not args.godot:
        parser.error('Godot is missing')
    command = [args.godot, '--path', str(project), '--display-driver', 'x11',
               '--rendering-method', 'forward_plus', '--audio-driver', 'Dummy', '--disable-vsync',
               '--fixed-fps', '30', '--script', 'res://tools/capture-traversal.gd', '--', '--output=' + str(output)]
    if args.preview:
        command.append('--preview')
    dimensions = (960, 540) if args.preview else (1280, 720)
    screen = f'{dimensions[0]}x{dimensions[1]}x24'
    if args.dry_run:
        print(json.dumps({'command': command, 'output': str(output), 'dimensions': dimensions,
                          'xvfb_screen': screen, 'shader_cache_seed': str(args.shader_cache_seed) if args.shader_cache_seed else None,
                          'starts_renderer': False}, indent=2))
        return
    xvfb = runtime / 'usr/bin/Xvfb'
    icd = runtime / 'usr/share/vulkan/icd.d/lvp_icd.json'
    if not xvfb.is_file() or not icd.is_file():
        parser.error('Run tools/setup-render-runtime.py first')
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not args.preview and (not ffmpeg or not ffprobe):
        parser.error('FFmpeg and ffprobe are required for a full capture')
    output.parent.mkdir(parents=True, exist_ok=True)
    user.mkdir()
    environment = os.environ.copy()
    environment.update(DISPLAY=f':{args.display}',
                       LD_LIBRARY_PATH=str(runtime / 'usr/lib/x86_64-linux-gnu') +
                       (':' + environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else ''),
                       VK_ICD_FILENAMES=str(icd), LP_NUM_THREADS='2')
    for variable, folder in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        environment[variable] = str(user / folder)
        Path(environment[variable]).mkdir()
    environment['MESA_SHADER_CACHE_DIR'] = str(user / 'cache/mesa')
    cache_seed = seed_shader_cache(args.shader_cache_seed, user / 'cache/mesa')
    with xlog_path.open('x') as xlog, log_path.open('x') as log:
        server = subprocess.Popen([str(xvfb), environment['DISPLAY'], '-screen', '0', screen,
                                   '-nolisten', 'tcp', '-extension', 'MIT-SHM', '-ac'],
                                  env=environment, stdout=xlog, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None:
                    raise RuntimeError('Owned Xvfb failed to start')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists():
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('Owned Xvfb did not create its socket')
            result = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=2400)
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    report_path = output / 'traversal-render-review.json'
    if not report_path.is_file():
        raise RuntimeError(f'No renderer report; preserve and inspect {log_path}')
    report = json.loads(report_path.read_text())
    log_text = log_path.read_text()
    if result.returncode or 'SCRIPT ERROR:' in log_text or '\nERROR:' in log_text:
        raise RuntimeError(f'Renderer failed; preserve and inspect {report_path} and {log_path}')
    validate_capture(report, output, project, args.preview)
    video = None if args.preview else encode_video(output, report_path, ffmpeg, ffprobe)
    write_new_json(output / 'capture-run.json', {
        'complete': True, 'command': command, 'preview': args.preview,
        'capture_report_sha256': sha256(report_path), 'runner_sha256': sha256(Path(__file__)),
        'godot_log_sha256': sha256(log_path), 'frames': len(report['frames']),
        'physics_ticks': report['take_physics_ticks'], 'video_sha256': video['sha256'] if video else None,
        'dimensions': dimensions, 'shader_cache_seed': cache_seed,
        'settings_scope': 'Fresh isolated XDG data/config/cache; existing user preferences were not read or written.'})
    print(json.dumps({'complete': True, 'frames': len(report['frames']), 'stills': len(report['stills']),
                      'physics_ticks': report['take_physics_ticks'], 'output': str(output),
                      'video': video['file'] if video else None}))


if __name__ == '__main__':
    main()
