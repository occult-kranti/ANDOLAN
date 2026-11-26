"""Record the registered Blender cameras against the full Monsoon Exchange glTF with Mesa/EGL."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')
os.environ.setdefault('LP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')

import numpy as np
import pyrender
import trimesh
from OpenGL.GL import GL_RENDERER, glGetString
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MAP = HERE.parent
WIDTH, HEIGHT, FPS, SECONDS = 1280, 720, 24, 4
# Each shot starts and ends at a yaw in radians and a distance multiplier about its registered target.
SHOTS = [
    ('overview', 'Monsoon Exchange', 'YUGA  /  DISTRICT SURVEY', -0.145, 0.145, 0.94, 0.84),
    ('weavers-gate', 'Weavers’ Gate', 'MID  /  CENTRAL MARKET', -0.085, 0.065, 1.21, 1.06),
    ('sun-court', 'Sun Court', 'SITE A  /  COPPER QUARTER', -0.070, 0.065, 1.04, 0.88),
    ('indigo-cistern', 'Indigo Cistern', 'SITE B  /  DYERS’ QUARTER', 0.050, -0.045, 0.99, 0.87),
]


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def render_geometry(path):
    # Group the fixed scenery by original material. Bake transforms while retaining the source
    # triangles, normals, texture coordinates and PBR bindings at every instance.
    model = trimesh.load_scene(path, process=False, merge_primitives=False)
    groups = defaultdict(list)
    for node in model.graph.nodes_geometry:
        world, mesh_id = model.graph[node]
        mesh = model.geometry[mesh_id]
        groups[mesh.visual.material.name].append((mesh, world))
    batches, triangles = [], 0
    for pieces in groups.values():
        positions, normals, texcoords, indices = [], [], [], []
        offset = 0
        for mesh, world in pieces:
            linear = world[:3, :3]
            transformed = mesh.vertices @ linear.T + world[:3, 3]
            normal = mesh.vertex_normals @ np.linalg.inv(linear)
            normal /= np.maximum(1e-8, np.linalg.norm(normal, axis=1)[:, None])
            positions.append(transformed)
            normals.append(normal)
            uv = mesh.visual.uv
            texcoords.append(uv if uv is not None else np.zeros((len(transformed), 2)))
            face = mesh.faces if np.linalg.det(linear) > 0 else mesh.faces[:, ::-1]
            indices.append(face + offset)
            offset += len(transformed)
            triangles += len(face)
        sample = pieces[0][0]
        material = pyrender.Mesh.from_trimesh(sample, smooth=True).primitives[0].material
        material.alphaMode = sample.visual.material.alphaMode or 'OPAQUE'
        if material.alphaMode != 'OPAQUE':
            raise ValueError('This tour batches opaque district architecture. Review the draw order for new transparency.')
        batches.append(pyrender.Primitive(np.vstack(positions), np.vstack(normals),
                                         texcoord_0=np.vstack(texcoords), indices=np.vstack(indices), material=material))
    radius = np.linalg.norm(model.extents) * 0.5
    counts = {'source_primitive_instances': len(model.graph.nodes_geometry), 'material_batches': len(batches),
              'drawn_triangles': triangles}
    return pyrender.Mesh(batches), radius, counts


def look_at(eye, target):
    eye, target = np.asarray(eye, dtype=float), np.asarray(target, dtype=float)
    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 1, 0])
    right /= np.linalg.norm(right)
    pose = np.eye(4)
    pose[:3, :3] = np.stack([right, np.cross(right, forward), -forward], axis=1)
    pose[:3, 3] = eye
    return pose


def camera_at(shot, t, registered, radius):
    def gltf(v):
        return np.array([v[0], v[2], -v[1]])
    key, _, _, a, b, z0, z1 = shot
    record = registered[key]
    target = gltf(record['target'])
    offset = gltf(record['position']) - target
    if key == 'overview':
        fov = math.radians(42)
        span = max(radius * 0.76, record['ortho_scale_m'] * 0.5)
        offset = offset / np.linalg.norm(offset) * span / math.tan(fov * 0.5)
    else:
        fov = 2 * math.atan(36 / (2 * record['lens_mm'] * WIDTH / HEIGHT))
    s = 0.5 - 0.5 * math.cos(math.pi * t)
    yaw = a + (b - a) * s
    c, v = math.cos(yaw), math.sin(yaw)
    rotated = np.array([c * offset[0] + v * offset[2], offset[1], -v * offset[0] + c * offset[2]])
    return look_at(target + rotated * (z0 + (z1 - z0) * s), target), fov


def lower_third(title, category):
    overlay = Image.new('RGBA', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(overlay)
    serif, sans = ImageFont.truetype('DejaVuSerif.ttf', 41), ImageFont.truetype('DejaVuSans.ttf', 15)
    for x in range(570):
        strength = max(0, 1 - (x / 570) ** 1.7)
        for y in range(111):
            draw.point((x, HEIGHT - 111 + y), fill=(21, 28, 28, int(208 * strength * min(1, y / 35))))
    draw.rectangle((35, 643, 38, 696), fill='#dcab62')
    draw.text((52, 642), category, font=sans, fill='#ffdfa3', stroke_width=1, stroke_fill='#413b33')
    draw.text((50, 658), title, font=serif, fill='#fff7e8', stroke_width=1, stroke_fill='#34302e')
    return overlay


def sky_rows(pose, fov):
    ndc = (1 - 2 * (np.arange(HEIGHT) + 0.5) / HEIGHT) * math.tan(fov * 0.5)
    y = (-pose[1, 2] + ndc * pose[1, 1]) / np.sqrt(1 + ndc * ndc)
    level = [-1, -0.28, 0.035, 0.43, 1]
    colors = np.array([[133, 136, 114], [171, 163, 139], [232, 215, 182], [164, 190, 197], [111, 153, 172]])
    return np.stack([np.interp(y, level, colors[:, i]) for i in range(3)], axis=1).astype(np.uint8)


def capture(args, work):
    model = MAP / 'scene/monsoon-exchange.glb'
    src = digest(model)
    register = json.loads((MAP / 'scene/scene-register.json').read_text())
    if src != register['files'][model.name]['sha256']:
        raise ValueError('Source GLB differs from its camera register')
    mesh, radius, counts = render_geometry(model)
    scene = pyrender.Scene(ambient_light=[0.42, 0.44, 0.43])
    scene.add(mesh)
    scene.add(pyrender.DirectionalLight(color=[1, 0.88, 0.71], intensity=3.2),
              pose=look_at([-48, 96, 74], [0, 0, 0]))
    camera = pyrender.PerspectiveCamera(yfov=math.radians(42), znear=0.035, zfar=radius * 14)
    node = scene.add(camera)
    renderer = pyrender.OffscreenRenderer(WIDTH, HEIGHT)
    device = glGetString(GL_RENDERER).decode()
    print('Recording', counts, device, flush=True)
    tiles, chapter_motion = [], []
    per_shot = FPS * SECONDS
    try:
        for chapter, shot in enumerate(SHOTS):
            overlay = lower_third(shot[1], shot[2])
            indices = [0, per_shot // 2, per_shot - 1] if args.contact_sheet else range(per_shot)
            first = None
            for i in indices:
                pose, fov = camera_at(shot, i / (per_shot - 1), register['cameras'], radius)
                scene.set_pose(node, pose)
                camera.yfov = fov
                color, depth = renderer.render(scene, flags=pyrender.RenderFlags.SHADOWS_DIRECTIONAL)
                if chapter == i == 0:
                    # Fixed world and sun share one light-depth map across every viewpoint.
                    renderer._renderer._shadow_mapping_pass = lambda *a: None
                color = np.where((depth == 0)[:, :, None], sky_rows(pose, fov)[:, None, :], color)
                image = Image.fromarray(color)
                if i in (0, per_shot - 1):
                    sample = np.array(image.resize((160, 90), Image.Resampling.BOX), dtype=np.int16)
                    if first is None:
                        first = sample
                    else:
                        moving = np.abs(sample - first).max(axis=2) > 10
                        changed = float(moving.mean())
                        if changed < 0.035:
                            raise ValueError(f'Insufficient camera motion in {shot[0]}')
                        chapter_motion.append(round(changed, 4))
                frame = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
                if args.contact_sheet:
                    tiles.append(frame.resize((384, 216), Image.Resampling.LANCZOS))
                else:
                    frame.save(work / f'{chapter * per_shot + i:04d}.jpg', quality=95, subsampling=0)
            print(shot[1], flush=True)
    finally:
        renderer.delete()
    if digest(model) != src:
        raise ValueError('The source GLB changed during capture')
    if args.contact_sheet:
        board = Image.new('RGB', (3 * 384, len(SHOTS) * 216))
        for i, tile in enumerate(tiles):
            board.paste(tile, (384 * (i % 3), 216 * (i // 3)))
        board.save(args.contact_sheet)
        return
    out = args.output / 'district-tour.mp4'
    with tempfile.TemporaryDirectory(dir=args.output) as staging:
        product = Path(staging) / out.name
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(work / '%04d.jpg'),
                        '-c:v', 'libx264', '-threads', '2', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                        '-vf', 'scale=in_color_matrix=bt601:out_color_matrix=bt709:in_range=pc:out_range=tv',
                        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                        '-movflags', '+faststart', '-an', str(product)], check=True)
        probed = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(product)]))
        stream, = probed['streams']
        total = per_shot * len(SHOTS)
        if (stream['codec_name'], stream['width'], stream['height'], int(stream['nb_frames'])) != ('h264', WIDTH, HEIGHT, total):
            raise ValueError('Unexpected encoded video stream')
        product.replace(out)
    sources = {p: digest(MAP / p) for p in ['scene/monsoon-exchange.glb', 'scene/scene-register.json',
                                            'viewer/orbit.js', 'film/record.py']}
    receipt = {'schema': 1, 'file': out.name, 'bytes': out.stat().st_size, 'sha256': digest(out),
               'renderer': 'pyrender ' + pyrender.__version__ + ' via EGL / ' + device, 'trimesh': trimesh.__version__,
               'inputs_sha256': sources, 'geometry': counts, 'width': WIDTH, 'height': HEIGHT, 'fps': FPS,
               'camera_samples_per_second': FPS, 'frames': total, 'duration_s': float(stream['duration']),
               'video_codec': stream['codec_name'], 'audio_streams': 0,
               'chapters': [{'camera': s[0], 'name': s[1], 'start_s': i * SECONDS, 'duration_s': SECONDS,
                             'first_last_changed_fraction': chapter_motion[i]} for i, s in enumerate(SHOTS)]}
    (args.output / 'recording.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE)
    parser.add_argument('--frames-dir', type=Path, default=Path('/dev/shm') if Path('/dev/shm').is_dir() else None)
    parser.add_argument('--contact-sheet', type=Path, help='Inspect the first, middle and last pose per shot.')
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='monsoon-film-native-', dir=options.frames_dir) as temp:
        capture(options, Path(temp))
