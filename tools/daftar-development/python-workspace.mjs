#!/usr/bin/env node
/** Explicit local Python environment for the checked-in Yuga development tasks.
 * No activation, package index, model, engine or folder-open work is performed. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const directory = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(directory, '../..');
const atlas = 'games/yuga-native/docs/design/ember-rite-5v5/atlas';
const tasks = {
  routes: [atlas + '/audit.py', '--check'],
  balance: [atlas + '/balance.py', '--check'],
  'test-balance': [atlas + '/test_balance.py'],
  'build-web': ['games/yuga-rust/tools/build_web.py'],
};
const proof = `import json,os,site,sys
normal=lambda value:os.path.normcase(os.path.realpath(value))
base_sites={normal(value) for value in site.getsitepackages([sys.base_prefix])}
print(json.dumps({"version":list(sys.version_info[:3]),"prefixMatches":normal(sys.prefix)==normal(sys.argv[1]),"isolatedPrefix":normal(sys.prefix)!=normal(sys.base_prefix),"isolatedMode":sys.flags.isolated==1,"userSiteDisabled":site.ENABLE_USER_SITE is False,"baseSitePackagesExcluded":not any(normal(value) in base_sites for value in sys.path)}))`;
// -I excludes the current directory. Add only this reviewed script's own source
// directory so sibling modules such as audit and ritual_rules remain importable.
const runScript = `import pathlib,runpy,sys
script=pathlib.Path(sys.argv[1]).resolve()
sys.argv=[str(script),*sys.argv[2:]]
sys.path.insert(0,str(script.parent))
runpy.run_path(str(script),run_name="__main__")`;

function options(argv) {
  const result = { action: argv[0], venv: path.join(directory, '.venv'), python: null };
  if (!['create', 'check', ...Object.keys(tasks)].includes(result.action)) {
    throw new Error('Choose create, check, routes, balance, test-balance or build-web.');
  }
  for (let index = 1; index < argv.length; index += 2) {
    const flag = argv[index], value = argv[index + 1];
    if (!['--venv', '--python'].includes(flag) || !value || !path.isAbsolute(value) || value.includes('\0')) {
      throw new Error('Use --venv or --python with an explicit absolute path.');
    }
    if (flag === '--venv') result.venv = value;
    else result.python = value;
  }
  if (result.action === 'create' && !result.python) throw new Error('Creation requires --python with a trusted absolute bootstrap interpreter that includes venv and ensurepip.');
  if (result.action !== 'create' && result.python) throw new Error('--python selects the bootstrap interpreter only for create; other tasks use the verified venv interpreter.');
  return result;
}

function environment(venv) {
  const env = { ...process.env };
  for (const name of Object.keys(env)) if (/^(?:PYTHON|PIP_)/i.test(name)) delete env[name];
  return { ...env, VIRTUAL_ENV: venv, PYTHONNOUSERSITE: '1', PIP_REQUIRE_VIRTUALENV: 'true',
    PIP_DISABLE_PIP_VERSION_CHECK: '1', PIP_CONFIG_FILE: process.platform === 'win32' ? 'nul' : '/dev/null' };
}

function execute(command, args, venv, timeout = 60000) {
  const result = spawnSync(command, args, { cwd: root, env: environment(venv), shell: false,
    windowsHide: true, encoding: 'utf8', timeout, maxBuffer: 2 * 1024 * 1024 });
  if (result.error || result.status !== 0) {
    throw new Error((result.error?.message ?? result.stderr.trim() ?? '') ||
      'Python task failed with exit status ' + result.status);
  }
  return result;
}

function inspect(venv) {
  const config = path.join(venv, 'pyvenv.cfg');
  if (!fs.existsSync(venv) || fs.lstatSync(venv).isSymbolicLink() ||
      !fs.existsSync(config) || !fs.lstatSync(config).isFile() || fs.lstatSync(config).isSymbolicLink()) {
    throw new Error('A regular local venv is required. Run the explicit create task first; existing non-venv paths are never overwritten.');
  }
  const flags = fs.readFileSync(config, 'utf8').split(/\r?\n/)
    .map(line => /^\s*include-system-site-packages\s*=\s*(.*?)\s*$/i.exec(line))
    .filter(Boolean);
  if (flags.length !== 1 || flags[0][1].toLowerCase() !== 'false') {
    throw new Error('The venv must have exactly one include-system-site-packages = false entry.');
  }
  const python = path.join(venv, process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const result = JSON.parse(execute(python, ['-I', '-c', proof, venv], venv).stdout);
  if (!result.prefixMatches || !result.isolatedPrefix || !result.isolatedMode ||
      !result.userSiteDisabled || !result.baseSitePackagesExcluded || result.version[0] !== 3 || result.version[1] < 10) {
    throw new Error('The selected interpreter did not prove Python 3.10+ and isolated venv execution.');
  }
  const pip = execute(python, ['-I', '-m', 'pip', '--isolated', '--require-virtualenv', '--version'], venv).stdout.trim();
  if (!/^pip \d/.test(pip)) throw new Error('The venv requires its own pip; use a bootstrap Python with ensurepip.');
  return { schemaVersion: 1, venv, python, ...result, pipVersion: pip.split(/\s+/)[1],
    pythonPackageIndexRequests: 0, engineStartedByHelper: false };
}

export function runPythonWorkspace(argv) {
  const selected = options(argv);
  if (selected.action === 'create' && !fs.existsSync(selected.venv)) {
    if (!fs.statSync(selected.python).isFile()) throw new Error('The bootstrap Python must be a file.');
    execute(selected.python, ['-I', '-m', 'venv', selected.venv], selected.venv);
  }
  const receipt = inspect(selected.venv);
  const task = tasks[selected.action];
  if (task) {
    const [relative, ...args] = task;
    const result = execute(receipt.python, ['-I', '-c', runScript, path.join(root, relative), ...args],
      selected.venv, selected.action === 'build-web' ? 15 * 60 * 1000 : 60000);
    process.stdout.write(result.stdout);
    process.stderr.write(result.stderr);
  }
  return { ...receipt, action: selected.action, taskCompleted: !!task };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { console.log(JSON.stringify(runPythonWorkspace(process.argv.slice(2)), null, 2)); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
