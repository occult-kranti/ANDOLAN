#!/usr/bin/env node
/** Validate actual GLB bytes with an isolated, integrity-pinned Khronos package.
 * Run preparation first; all vendor modules are checked before require().
 * A format pass is not visual, animation, collision or gameplay acceptance.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const VERSION = '2.0.0-dev.3.10';
const INTEGRITY = 'sha512-odJ4k0tRkGXiDGn78yDBg+fBbAIvBnXxh3RwAta0emSxGtyagFE8B4xELB1oYe3S5RD8Ci3uZAsZaascH2LAEQ==';
const ARCHIVE_SHA256 = '4e03dbdc3bc0d1342afd5d2d7ae341a7e3474502ccb872b02dbbaddaee0fdec6';
const EXECUTABLE_FILES = {
  'index.js': '78deff9ea85743e86461c2d14fae76e7fc3ca0432e652f62948066b55fa16f0d',
  'gltf_validator.dart.js': 'b73a7b2d455ac217567725138b46d826a13d7d1bb0c88c15f7c571bfb349298c',
  'package.json': '3578d16153fa237c72784588da2e8fcccc9cd3c1c58ef34c7912f0732d2f5fa6',
};
const sha256 = data => crypto.createHash('sha256').update(data).digest('hex');
const args = process.argv.slice(2);
const value = key => {
  const index = args.indexOf(key);
  if (index < 0 || !args[index + 1]) throw new Error(`Required argument: ${key}`);
  return args[index + 1];
};
const validatorDir = path.resolve(value('--validator-dir'));
const reportPath = path.resolve(value('--report'));
const assets = args.flatMap((argument, index) => argument === '--asset' ? [args[index + 1]] : []);
if (!assets.length || assets.some(asset => !asset)) throw new Error('Pass at least one --asset path');
const provenance = JSON.parse(fs.readFileSync(path.join(validatorDir, 'yuga-package-provenance.json'), 'utf8'));
if (provenance.package !== 'gltf-validator' || provenance.version !== VERSION || provenance.integrity !== INTEGRITY || provenance.archive_sha256 !== ARCHIVE_SHA256) {
  throw new Error('Unexpected validator provenance');
}
for (const [name, expectedHash] of Object.entries(provenance.files)) {
  const filename = path.resolve(validatorDir, name);
  if (!filename.startsWith(validatorDir + path.sep)) throw new Error('Invalid manifest path');
  if (sha256(fs.readFileSync(filename)) !== expectedHash) throw new Error(`Validator file changed: ${name}`);
}
for (const [name, expectedHash] of Object.entries(EXECUTABLE_FILES)) {
  if (sha256(fs.readFileSync(path.join(validatorDir, name))) !== expectedHash) throw new Error(`Pinned executable file changed: ${name}`);
}
const require = createRequire(import.meta.url);
const validator = require(path.join(validatorDir, 'index.js'));
const packageJson = JSON.parse(fs.readFileSync(path.join(validatorDir, 'package.json'), 'utf8'));
if (packageJson.version !== VERSION) throw new Error('Unexpected installed package version');
const results = [];
for (const asset of assets) {
  const filename = path.resolve(asset);
  const bytes = fs.readFileSync(filename);
  if (bytes.readUInt32LE(0) !== 0x46546c67) throw new Error(`Expected binary glTF: ${filename}`);
  const digest = sha256(bytes);
  const result = await validator.validateBytes(new Uint8Array(bytes), {
    uri: path.basename(filename),
    maxIssues: 10000,
    writeTimestamp: false,
    externalResourceFunction: async uri => { throw new Error(`External resource not allowed in this GLB gate: ${uri}`); },
  });
  const unchanged = sha256(fs.readFileSync(filename)) === digest;
  const passed = unchanged && result.issues.numErrors === 0 && result.issues.truncated !== true;
  results.push({ asset: asset.replaceAll(path.sep, '/'), bytes: bytes.length, sha256: digest,
    source_unchanged: unchanged, passed, validation: result });
}
const report = {
  schema: 1, package: packageJson.name, package_version: packageJson.version,
  validator_version: validator.version(), package_integrity: INTEGRITY,
  package_archive_sha256: provenance.archive_sha256,
  node_version: process.version, script_sha256: sha256(fs.readFileSync(fileURLToPath(import.meta.url))),
  scope: 'glTF format validation of these exact bytes; not an art, motion, collision, performance or game-quality result.',
  passed: results.every(result => result.passed), results,
};
fs.mkdirSync(path.dirname(reportPath), { recursive: true });
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ passed: report.passed, report: reportPath,
  assets: results.map(result => ({asset: result.asset, errors: result.validation.issues.numErrors,
    warnings: result.validation.issues.numWarnings, infos: result.validation.issues.numInfos})) }));
process.exitCode = report.passed ? 0 : 1;
