const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const validatorRoot = '/workspace/tooling/gltf-validator-mythic';
const validator = require(validatorRoot);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

(async () => {
  const root = process.cwd();
  const candidate = path.join(root, 'art/hero-finish/s4-diadem-fit/candidate-r1');
  const result = {schema: 1, package: JSON.parse(fs.readFileSync(path.join(validatorRoot, 'package.json'))),
    tool: {script_sha256: sha(fs.readFileSync(__filename)), validator_sha256: sha(fs.readFileSync(path.join(validatorRoot, 'gltf_validator.dart.js')))},
    scope: 'Exact stored review-only candidate bytes; no import or visual acceptance.', levels: {}};
  for (const name of ['rama-hero.glb', 'rama-hero-mid.glb', 'rama-hero-far.glb']) {
    const bytes = fs.readFileSync(path.join(candidate, name));
    const report = await validator.validateBytes(new Uint8Array(bytes), {uri: name, maxIssues: 10000});
    result.levels[name] = {sha256: sha(bytes), bytes: bytes.length, report};
    console.log(name, report.issues.numErrors, 'errors', report.issues.numWarnings, 'warnings');
  }
  result.passed = Object.values(result.levels).every(x => x.report.issues.numErrors === 0);
  fs.writeFileSync(path.join(__dirname, 'khronos-r1.json'), JSON.stringify(result, null, 2) + '\n');
  process.exitCode = result.passed ? 0 : 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
