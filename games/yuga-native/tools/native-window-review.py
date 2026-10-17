#!/usr/bin/env python3
"""Own one X11 server/game process and record actual window/input review.

This is a Linux review aid, not a GPU benchmark or an automatic visual pass.
Commands on stdin are JSON: capture, key, click, or quit. All input goes to the
single YUGA window on the owned display. No simulation state is injected.
"""
import argparse
import ctypes as C
import ctypes.util
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from PIL import ImageGrab


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', required=True)
    parser.add_argument('--pack', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--xvfb', default=shutil.which('Xvfb'))
    parser.add_argument('--display', default=':107')
    parser.add_argument('--renderer', choices=['forward_plus', 'gl_compatibility'], default='forward_plus')
    parser.add_argument('--shader-cache-seed', type=Path)
    args = parser.parse_args()
    if not args.xvfb:
        parser.error('Xvfb is required; supply --xvfb for a task-local installation.')
    engine, pack, out = Path(args.engine).resolve(), Path(args.pack).resolve(), Path(args.output).resolve()
    assert engine.is_file() and pack.is_file()
    out.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env['DISPLAY'] = args.display
    for name, folder in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        env[name] = str(out / 'user' / folder)
        Path(env[name]).mkdir(parents=True)
    env['MESA_SHADER_CACHE_DIR'] = str(out / 'user' / 'cache' / 'mesa')
    record = {
        'scope': 'Actual Linux native window screenshots and XTest keyboard/mouse events. Human visual review is separate. Software rendering is not hardware-performance evidence.',
        'engine': {'file': engine.name, 'sha256': hashlib.sha256(engine.read_bytes()).hexdigest()},
        'pack': {'file': pack.name, 'sha256': hashlib.sha256(pack.read_bytes()).hexdigest()},
        'rendererRequested': args.renderer, 'events': [], 'startedAtUnix': time.time(),
    }
    if args.shader_cache_seed:
        helper_path = Path(__file__).with_name('run-traversal-capture.py')
        spec = importlib.util.spec_from_file_location('traversal_capture_cache', helper_path)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        record['shaderCacheSeed'] = helper.seed_shader_cache(args.shader_cache_seed, out / 'user/cache/mesa')
    log = (out / 'game.log').open('w')
    xlog = (out / 'xvfb.log').open('w')
    server = subprocess.Popen([args.xvfb, args.display, '-screen', '0', '960x600x24', '-nolisten', 'tcp', '-extension', 'MIT-SHM', '-ac'], env=env, stdout=xlog, stderr=subprocess.STDOUT)
    game = None
    display = None
    x = C.CDLL(ctypes.util.find_library('X11'))
    xt = C.CDLL(ctypes.util.find_library('Xtst'))
    x.XOpenDisplay.argtypes = [C.c_char_p]; x.XOpenDisplay.restype = C.c_void_p
    x.XDefaultRootWindow.argtypes = [C.c_void_p]; x.XDefaultRootWindow.restype = C.c_ulong
    x.XQueryTree.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_ulong), C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_uint)]
    x.XFetchName.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_char_p)]
    x.XFree.argtypes = [C.c_void_p]
    x.XSetInputFocus.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_ulong]
    x.XStringToKeysym.argtypes = [C.c_char_p]; x.XStringToKeysym.restype = C.c_ulong
    x.XKeysymToKeycode.argtypes = [C.c_void_p, C.c_ulong]; x.XKeysymToKeycode.restype = C.c_uint
    x.XFlush.argtypes = [C.c_void_p]
    x.XCloseDisplay.argtypes = [C.c_void_p]
    xt.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
    xt.XTestFakeButtonEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
    xt.XTestFakeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_ulong]
    xt.XTestFakeRelativeMotionEvent.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_ulong]

    def window():
        root, parent = C.c_ulong(), C.c_ulong()
        children = C.POINTER(C.c_ulong)(); count = C.c_uint()
        x.XQueryTree(display, x.XDefaultRootWindow(display), C.byref(root), C.byref(parent), C.byref(children), C.byref(count))
        found = None
        for i in range(count.value):
            name = C.c_char_p()
            if x.XFetchName(display, children[i], C.byref(name)) and name.value:
                title = name.value.decode(errors='replace')
                if title.startswith('YUGA'):
                    found = children[i]
                x.XFree(name)
        if children:
            x.XFree(children)
        if found is None:
            raise RuntimeError('Owned YUGA window has not opened.')
        return found

    try:
        time.sleep(1)
        if server.poll() is not None:
            raise RuntimeError('Owned Xvfb failed to start.')
        display = x.XOpenDisplay(args.display.encode())
        if not display:
            raise RuntimeError('Cannot open owned X display.')
        game = subprocess.Popen([str(engine), '--main-pack', str(pack), '--display-driver', 'x11', '--rendering-method', args.renderer, '--audio-driver', 'Dummy', '--resolution', '960x600', '--position', '0,0', '--disable-vsync', '--max-fps', '30'], env=env, cwd=out, stdout=log, stderr=subprocess.STDOUT)
        print(json.dumps({'readyForCommands': True, 'output': str(out), 'gamePid': game.pid}), flush=True)
        for line in sys.stdin:
            command = json.loads(line)
            action = command['action']
            if action == 'quit':
                break
            if game.poll() is not None:
                raise RuntimeError(f'Game exited with {game.returncode}.')
            target = window()
            x.XSetInputFocus(display, target, 2, 0)
            x.XFlush(display)
            if action == 'capture':
                name = command['name']
                if not name.replace('-', '').replace('_', '').isalnum():
                    raise ValueError('Capture name must be an ordinary basename.')
                path = out / (name + '.png')
                if path.exists():
                    raise ValueError('Do not overwrite earlier review frames.')
                ImageGrab.grab(xdisplay=args.display).save(path)
                record['events'].append({'action': action, 'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'time': time.time()})
            elif action == 'key':
                name = command['key']
                if name not in ['w', 'a', 's', 'd', 'q', 'e', 'r', 'n', 'Escape', 'Return', 'Tab', 'space', 'Left', 'Right', 'F1', 'F2', 'F5', 'f', 'g', 'j', 'x', 'v', 'b', 'F3', 'Up', 'Down', 'Control_L', 'Shift_L']:
                    raise ValueError('Unsupported review key.')
                duration = max(0.05, min(5.0, float(command.get('seconds', 0.15))))
                code = x.XKeysymToKeycode(display, x.XStringToKeysym(name.encode()))
                xt.XTestFakeKeyEvent(display, code, 1, 0); x.XFlush(display)
                time.sleep(duration)
                xt.XTestFakeKeyEvent(display, code, 0, 0); x.XFlush(display)
                record['events'].append({'action': action, 'key': name, 'heldWallSeconds': duration, 'time': time.time()})
            elif action == 'motion':
                dx, dy = command['dx'], command['dy']
                if type(dx) is not int or type(dy) is not int or abs(dx) > 720 or abs(dy) > 480:
                    raise ValueError('Relative mouse motion must be bounded integer pixels.')
                xt.XTestFakeRelativeMotionEvent(display, dx, dy, 0)
                x.XFlush(display)
                record['events'].append({'action': action, 'dx': dx, 'dy': dy, 'time': time.time()})
            elif action == 'click':
                move = command.get('move', True)
                if not isinstance(move, bool):
                    raise ValueError('Click move must be true or false.')
                duration = float(command.get('seconds', 0.15))
                if not math.isfinite(duration):
                    raise ValueError('Click duration must be finite.')
                duration = max(0.05, min(5.0, duration))
                px, py = None, None
                if move:
                    px, py = int(command['x']), int(command['y'])
                    if not (0 <= px < 960 and 0 <= py < 600):
                        raise ValueError('Click outside owned window.')
                    xt.XTestFakeMotionEvent(display, -1, px, py, 0)
                xt.XTestFakeButtonEvent(display, 1, 1, 0); x.XFlush(display)
                time.sleep(duration)
                xt.XTestFakeButtonEvent(display, 1, 0, 0); x.XFlush(display)
                record['events'].append({'action': action, 'x': px, 'y': py, 'movedPointer': move, 'heldWallSeconds': duration, 'time': time.time()})
            else:
                raise ValueError('Unknown command.')
            (out / 'input-review.json').write_text(json.dumps(record, indent=2) + '\n')
            print(json.dumps({'recorded': record['events'][-1]}), flush=True)
    finally:
        if game and game.poll() is None:
            game.terminate()
            try: game.wait(timeout=8)
            except subprocess.TimeoutExpired: game.kill(); game.wait()
        if display: x.XCloseDisplay(display)
        if server.poll() is None: server.terminate()
        server.wait(timeout=5)
        log.close(); xlog.close()
        record['finishedAtUnix'] = time.time()
        record['gameExitAfterReviewCleanup'] = game.returncode if game else None
        record['automatedVisualPassClaimed'] = False
        (out / 'input-review.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
