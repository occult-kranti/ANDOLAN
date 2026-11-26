import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const directory = path.dirname(fileURLToPath(import.meta.url));
const script = path.join(directory, 'python-workspace.mjs');
function run(args) {
  return spawnSync(process.execPath, [script, ...args], { encoding: 'utf8', shell: false, timeout: 60000 });
}
function temporary(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'yuga-python-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

test('requires explicit absolute bootstrap and refuses unknown tasks without creating anything', t => {
  const venv = path.join(temporary(t), 'environment');
  for (const args of [['create'], ['create', '--python', 'python3'], ['unknown'], ['check', '--python', process.execPath]]) {
    const result = run([...args, '--venv', venv]);
    assert.equal(result.status, 1);
    assert.equal(fs.existsSync(venv), false);
  }
});

test('never overwrites an existing non-venv directory or follows its config symlink', t => {
  const root = temporary(t), venv = path.join(root, 'environment');
  fs.mkdirSync(venv); fs.writeFileSync(path.join(venv, 'owner.txt'), 'preserve');
  let result = run(['create', '--python', process.execPath, '--venv', venv]);
  assert.equal(result.status, 1); assert.match(result.stderr, /regular local venv/);
  assert.equal(fs.readFileSync(path.join(venv, 'owner.txt'), 'utf8'), 'preserve');
  if (process.platform !== 'win32') {
    const external = path.join(root, 'external.cfg');
    fs.writeFileSync(external, 'include-system-site-packages = false\n');
    fs.symlinkSync(external, path.join(venv, 'pyvenv.cfg'));
    result = run(['check', '--venv', venv]);
    assert.equal(result.status, 1); assert.match(result.stderr, /regular local venv/);
  }
});

test('rejects enabled or ambiguous global site-packages before starting an interpreter', t => {
  const venv = temporary(t);
  for (const config of ['include-system-site-packages = true\n',
    'include-system-site-packages = false\ninclude-system-site-packages = false\n']) {
    fs.writeFileSync(path.join(venv, 'pyvenv.cfg'), config);
    const result = run(['check', '--venv', venv]);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /exactly one include-system-site-packages = false/);
  }
});

test('creates a real offline venv and runs the current route and balance checks inside it',
  { skip: !process.env.DAFTAR_TEST_PYTHON }, t => {
    const venv = path.join(temporary(t), 'environment');
    const created = run(['create', '--python', process.env.DAFTAR_TEST_PYTHON, '--venv', venv]);
    assert.equal(created.status, 0, created.stderr);
    const receipt = JSON.parse(created.stdout);
    assert.equal(receipt.prefixMatches, true); assert.equal(receipt.isolatedPrefix, true);
    assert.equal(receipt.isolatedMode, true); assert.equal(receipt.userSiteDisabled, true);
    assert.equal(receipt.baseSitePackagesExcluded, true); assert.equal(receipt.pythonPackageIndexRequests, 0);
    for (const action of ['routes', 'balance', 'test-balance']) {
      const result = run([action, '--venv', venv]);
      assert.equal(result.status, 0, result.stderr + result.stdout);
      assert.match(result.stdout, /"taskCompleted": true/);
    }
    const config = path.join(venv, 'pyvenv.cfg');
    fs.writeFileSync(config, fs.readFileSync(config, 'utf8').replace('include-system-site-packages = false', 'include-system-site-packages = true'));
    const rejected = run(['routes', '--venv', venv]);
    assert.equal(rejected.status, 1); assert.match(rejected.stderr, /include-system-site-packages/);
  });
