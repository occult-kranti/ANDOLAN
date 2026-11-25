/** Compare the shipped rig and the finished asset with the Khronos glTF Validator. */
const { createHash } = require('node:crypto');
const { readFileSync, writeFileSync } = require('node:fs');
const { resolve, basename } = require('node:path');
const { parseArgs } = require('node:util');

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { validator: { type: 'string' }, output: { type: 'string' } }
});
if (!positionals.length) throw new Error('Pass one or more GLB paths');
const validator = values.validator ? require(resolve(values.validator)) : require('gltf-validator');

async function inspect(file) {
  const bytes = readFileSync(file);
  const result = await validator.validateBytes(new Uint8Array(bytes), {
    uri: basename(file), writeTimestamp: false, maxIssues: 0
  });
  const details = {};
  for (const { code, severity, pointer, message } of result.issues.messages) {
    const group = details[code] ??= { severity, count: 0, first: { pointer, message } };
    group.count++;
  }
  const { numErrors, numWarnings, numInfos, numHints, truncated } = result.issues;
  return {
    file: basename(file), bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex'),
    validator: result.validatorVersion, numErrors, numWarnings, numInfos, numHints,
    truncated, issueCodes: details,
    rendererInfo: Object.fromEntries(Object.entries(result.info).filter(([key]) =>
      ['animationCount','materialCount','drawCallCount','totalVertexCount','totalTriangleCount','maxInfluences','maxAttributes'].includes(key)))
  };
}
(async () => {
  const assets = [];
  for (const file of positionals) assets.push(await inspect(file));
  const report = { tool: 'KhronosGroup/glTF-Validator', npm: 'gltf-validator@2.0.0-dev.3.10', assets };
  const json = JSON.stringify(report, null, 2) + '\n';
  if (values.output) writeFileSync(values.output,json); else process.stdout.write(json);
  for (const row of assets) {
    console.error(row.file, row.numErrors + ' errors,', row.numWarnings + ' warnings,', row.rendererInfo.totalTriangleCount + ' triangles');
  }
  if (assets.length > 1 && Object.entries(assets.at(-1).issueCodes).some(([code, group]) =>
    group.severity < 2 && group.count > (assets[0].issueCodes[code]?.count ?? 0))) {
    process.exitCode = 1;
  }
})().catch(err=>{console.error(err);process.exitCode=1;});
