const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const validatorRoot = '/workspace/tooling/gltf-validator-mythic';
const validator = require(validatorRoot);
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
(async () => {
  const [candidate, output] = process.argv.slice(2);
  if (!candidate || !output || fs.existsSync(output)) throw new Error('candidate directory and fresh output required');
  const result = {schema:1, package:JSON.parse(fs.readFileSync(path.join(validatorRoot,'package.json'))),
    tool:{script_sha256:sha(fs.readFileSync(__filename)), validator_sha256:sha(fs.readFileSync(path.join(validatorRoot,'gltf_validator.dart.js')))},
    scope:'Exact stored review-only GLBs; no import or visual acceptance.', levels:{}};
  for(const name of ['rama-hero.glb','rama-hero-mid.glb','rama-hero-far.glb']) {
    const bytes=fs.readFileSync(path.join(candidate,name));
    const report=await validator.validateBytes(new Uint8Array(bytes),{uri:name,maxIssues:10000});
    result.levels[name]={sha256:sha(bytes),bytes:bytes.length,report};
    console.log(name,report.issues.numErrors,'errors',report.issues.numWarnings,'warnings');
  }
  result.passed=Object.values(result.levels).every(x=>x.report.issues.numErrors===0);
  fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
  process.exitCode=result.passed?0:1;
})().catch(error=>{console.error(error);process.exitCode=1;});
