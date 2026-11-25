/** Render offline 3D frames through the same PBR and skeletal animation stack as YUGA. */
import { chromium } from 'playwright';
import { buildSync } from 'esbuild';
import { createServer } from 'node:http';
import { createReadStream, existsSync } from 'node:fs';
import { readFile, writeFile, mkdir, rm, mkdtemp, stat, rename } from 'node:fs/promises';
import { execFileSync, spawn } from 'node:child_process';
import { once } from 'node:events';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import path from 'node:path';
import os from 'node:os';

const here = path.dirname(fileURLToPath(import.meta.url)),
  pack = path.resolve(here, '../..'),
  repo = path.resolve(here, '../../../../../..');
const native = path.join(repo, 'games/yuga-native'),
  rust = path.join(repo, 'games/yuga-rust');
const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    input: { type: 'string' },
    output: { type: 'string' },
    stills: { type: 'string' },
    pilot: { type: 'boolean' },
    pick: { type: 'string' },
    gpu: { type: 'string', default: 'auto' },
  },
});
const specs = JSON.parse(await readFile(path.join(here, 'shots.json'), 'utf8'));
if (!['auto', 'software'].includes(values.gpu)) throw Error('--gpu must be auto or software');
const heroes = positionals.length ? positionals : Object.keys(specs.heroes);
const picks = values.pick?.split(',').map((name) => name.trim());
if (
  picks &&
  (heroes.length !== 1 ||
    !values.output ||
    !picks.every((clip) => specs.heroes[heroes[0]]?.shots.some((s) => s.clip === clip)))
) {
  throw Error('Select known clips from one hero and provide an alternate --output directory.');
}
if (heroes.some((h) => !specs.heroes[h]) || (values.input && heroes.length !== 1))
  throw Error('Choose named heroes. --input takes one hero.');
const output = path.resolve(values.output || path.join(pack, 'media/video'));
await mkdir(output, { recursive: true });
if (values.stills) await mkdir(values.stills, { recursive: true });
const temp = await mkdtemp(path.join(os.tmpdir(), 'yuga-four-hero-film-'));
const digest = (b) => createHash('sha256').update(b).digest('hex');
const court = path.join(native, 'assets/environment/lanka_courtyard.glb');
const client = path.join(temp, 'client.js');
buildSync({
  entryPoints: [path.join(here, 'scene.ts')],
  bundle: true,
  format: 'iife',
  globalName: 'filmRenderer',
  target: 'es2022',
  outfile: client,
});
async function actorPath(hero) {
  if (values.input) return path.resolve(values.input);
  if (hero === 'krishna' || hero === 'shiva') return path.join(pack, 'models', hero + '.glb');
  const dest = path.join(temp, hero + '.glb');
  if (hero === 'rama')
    execFileSync('python3', [path.join(rust, 'tools/pack_rama.py'), '--lod', 'near', dest], {
      stdio: 'inherit',
    });
  else {
    const exporter = path.join(rust, 'target/release/hero_export');
    const args = [
      path.join(native, 'assets/heroes/hanuman/hanuman.glb'),
      path.join(native, 'assets/heroes/hanuman/hanuman-ability-motion.tres'),
      dest,
    ];
    if (existsSync(exporter)) execFileSync(exporter, args, { cwd: rust, stdio: 'inherit' });
    else
      execFileSync('cargo', ['run', '--release', '--locked', '--bin', 'hero_export', '--', ...args], {
        cwd: rust,
        stdio: 'inherit',
      });
  }
  return dest;
}
let actor;
const html =
  '<!doctype html><meta charset="utf-8"><style>*{margin:0}canvas{display:block}</style><canvas id="scene"></canvas><canvas id="film" hidden></canvas><script src="./client.js"></script>';
const host = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/') {
    res.writeHead(200, { 'content-type': 'text/html' }).end(html);
    return;
  }
  const files = { '/actor.glb': actor, '/court.glb': court, '/client.js': client };
  const f = files[url.pathname];
  if (!f) {
    res.writeHead(404).end();
    return;
  }
  const type = f.endsWith('.glb') ? 'model/gltf-binary' : 'application/javascript';
  res.writeHead(200, {
    'content-type': type,
    'cache-control': 'no-store',
    'content-length': (await stat(f)).size,
  });
  createReadStream(f).pipe(res);
});
await new Promise((r) => host.listen(0, '127.0.0.1', r));
let browser;
try {
  browser = await chromium.launch({
    headless: true,
    executablePath:
      process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ||
      (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined),
    args: [
      ...(values.gpu === 'software' ? ['--use-angle=swiftshader'] : []),
      '--enable-unsafe-swiftshader',
      '--disable-dev-shm-usage',
      '--no-sandbox',
    ],
  });
  for (const hero of heroes) {
    actor = await actorPath(hero);
    const spec = specs.heroes[hero],
      { width, height, fps } = specs;
    const page = await browser.newPage({ viewport: { width, height } });
    page.on('pageerror', (e) => console.error(e));
    await page.goto('http://127.0.0.1:' + host.address().port + '/', { waitUntil: 'load' });
    const info = await page.evaluate(
      async ({ hero, spec, width, height }) => {
        window.player = await filmRenderer.prepare(hero, spec, width, height);
        return window.player.info;
      },
      { hero, spec, width, height },
    );
    const video = path.join(temp, hero + '.mp4');
    const ff = values.pilot
      ? null
      : spawn(
          'ffmpeg',
          [
            '-hide_banner',
            '-loglevel',
            'error',
            '-y',
            '-f',
            'image2pipe',
            '-c:v',
            'mjpeg',
            '-framerate',
            String(fps),
            '-i',
            'pipe:0',
            '-an',
            '-vf',
            'scale=in_range=full:out_range=tv',
            '-c:v',
            'libx264',
            '-preset',
            'fast',
            '-threads',
            '1',
            '-crf',
            '17',
            '-pix_fmt',
            'yuv420p',
            '-movflags',
            '+faststart',
            video,
          ],
          { stdio: ['pipe', 'inherit', 'inherit'] },
        );
    const completion = ff ? once(ff, 'exit') : null;
    const report = {
      hero,
      renderer: info.engine,
      graphics_device: info.renderer ?? 'WebGL2',
      width,
      height,
      fps,
      source_sha256: digest(await readFile(actor)),
      source:
        hero === 'rama'
          ? 'Original near-detail Rama GLB with solved Godot controller poses baked by pack_rama.py --lod near'
          : hero === 'hanuman'
            ? 'Original Hanuman GLB overlaid with native Hanuman ability tracks by hero_export'
            : 'models/' + hero + '.glb',
      environment: 'games/yuga-native/assets/environment/lanka_courtyard.glb',
      environment_sha256: digest(await readFile(court)),
      joint_count: info.joints,
      skinned_mesh_instances: info.modelMeshes,
      coordinate_system:
        'Y up, meters. Sample bones [x,y,z,qw,qx,qy,qz] in scene world space; camera matrix column-major. Shots sample native clips over edited display durations.',
      shots: [],
      total_frames: 0,
    };
    try {
      for (const [index, shot] of spec.shots.entries()) {
        if (picks && !picks.includes(shot.clip)) continue;
        const source = info.clips.find((c) => c.clip === shot.clip);
        if (!source) throw Error('Missing ' + shot.clip);
        const receipt = {
          ...shot,
          source_clip_seconds: source.duration,
          start_frame: report.total_frames,
          end_frame: report.total_frames + shot.frames - 1,
          poses: [],
        };
        const keys = new Set([
          0,
          Math.floor(shot.frames * 0.33),
          Math.floor(shot.frames * 0.67),
          shot.frames - 1,
        ]);
        const frames = values.pilot
          ? [Math.floor(shot.frames * 0.5)]
          : Array.from({ length: shot.frames }, (_, i) => i);
        for (const i of frames) {
          const item = await page.evaluate(({ index, i, sample }) => window.player.frame(index, i, sample), {
            index,
            i,
            sample: keys.has(i),
          });
          const image = Buffer.from(item.image, 'base64');
          if (item.pose) receipt.poses.push({ frame: report.total_frames + i, ...item.pose });
          if (values.stills && (values.pilot || i === Math.floor(shot.frames * 0.5)))
            await writeFile(
              path.join(
                values.stills,
                hero + '-' + String(index).padStart(2, '0') + '-' + shot.clip + '.jpg',
              ),
              image,
            );
          if (ff && !ff.stdin.write(image)) await once(ff.stdin, 'drain');
        }
        report.shots.push(receipt);
        report.total_frames += shot.frames;
        console.log(hero, shot.clip, report.total_frames);
      }
      if (ff) {
        ff.stdin.end();
        const [code] = await completion;
        if (code !== 0) throw Error('FFmpeg failed ' + code);
        const encoded = await readFile(video);
        report.media_sha256 = digest(encoded);
        const dest = path.join(output, hero + '.mp4');
        const trace = path.join(output, hero + '.json');
        const staging = await mkdtemp(path.join(output, '.publish-' + hero + '-'));
        try {
          await writeFile(path.join(staging, 'video'), encoded);
          await writeFile(path.join(staging, 'trace'), JSON.stringify(report, null, 2) + '\n');
          await rename(path.join(staging, 'video'), dest);
          await rename(path.join(staging, 'trace'), trace);
        } finally {
          await rm(staging, { recursive: true, force: true });
        }
      }
    } finally {
      if (ff && ff.exitCode === null) ff.kill();
      await page.close();
    }
  }
} finally {
  await browser?.close();
  host.closeAllConnections();
  await new Promise((r) => host.close(r));
  await rm(temp, { recursive: true, force: true });
}
