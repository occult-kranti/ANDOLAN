/** Check the released GLB with Khronos glTF Validator and print a portable receipt. */
const fs = require("node:fs");
const path = require("node:path");
const { createHash } = require("node:crypto");

async function verify() {
  const validator = require(process.env.GLTF_VALIDATOR || "gltf-validator");
  const filename = process.argv[2] || path.join(__dirname, "monsoon-exchange.glb");
  const bytes = fs.readFileSync(filename);
  const result = await validator.validateBytes(bytes, { maxIssues: 10000 });
  const { numErrors, numWarnings, numInfos, messages } = result.issues;
  const counts = {};
  for (const { code } of messages) counts[code] = (counts[code] || 0) + 1;
  const receipt = {
    model: path.basename(filename),
    sha256: createHash("sha256").update(bytes).digest("hex"),
    package: "gltf-validator",
    version: result.validatorVersion,
    errors: numErrors,
    warnings: numWarnings,
    information: numInfos,
    reportedCodes: counts,
    triangles: result.info.totalTriangleCount,
    vertices: result.info.totalVertexCount,
    materials: result.info.materialCount,
    meshPrimitives: result.info.drawCallCount,
  };
  process.stdout.write(JSON.stringify(receipt, null, 2) + "\n");
  if (numErrors || numWarnings) process.exitCode = 1;
}

verify().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
