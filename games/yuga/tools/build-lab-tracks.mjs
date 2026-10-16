import { spawnSync } from 'node:child_process';

for (const track of ['all', 'lane', 'control']) {
  const build = spawnSync(process.execPath, ['node_modules/vite/bin/vite.js', 'build', '--config', 'vite.yuga-lab.config.ts'], {
    stdio: 'inherit', env: { ...process.env, YUGA_LAB_TRACK: track, YUGA_LAB_FLAVOR_OUTPUT: '1' },
  });
  if (build.status !== 0) process.exit(build.status || 1);
  const directory = track === 'all' ? 'yuga-lab' : `yuga-${track}-lab`;
  const notices = spawnSync(process.execPath, ['games/yuga/tools/attach-notices.mjs', `dist/${directory}/index.html`], { stdio: 'inherit' });
  if (notices.status !== 0) process.exit(notices.status || 1);
}
