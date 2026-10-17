#!/usr/bin/env node
/** Original offline adapter; upstream library notices are in NOTICE.md. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { NodeIO } from '@gltf-transform/core';
import { KHRMaterialsEmissiveStrength } from '@gltf-transform/extensions';
import { weld, reorder } from '@gltf-transform/functions';
import { MeshoptEncoder } from 'meshoptimizer';

const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const canonical = (value) => JSON.stringify(value, (_, v) => v && !Array.isArray(v) && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v);
const equal = (a, b, label) => { if (canonical(a) !== canonical(b)) throw Error(`${label} changed`); };
const io = new NodeIO().registerExtensions([KHRMaterialsEmissiveStrength]);

export function inspectContainer(bytes) {
  if (bytes.length < 20 || bytes.readUInt32LE(0) !== 0x46546c67 || bytes.readUInt32LE(4) !== 2 || bytes.readUInt32LE(8) !== bytes.length) throw Error('Expected complete GLB v2');
  if (bytes.readUInt32LE(16) !== 0x4e4f534a) throw Error('Expected leading JSON chunk');
  const json = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)).toString('utf8'));
  if (json.skins?.length || json.animations?.length) throw Error('Static meshes only: skins/animations refused');
  if (json.cameras?.length) throw Error('Cameras are outside this static mesh contract');
  const supported = new Set(['KHR_materials_emissive_strength']);
  for (const ext of [...(json.extensionsUsed || []), ...(json.extensionsRequired || [])]) if (!supported.has(ext)) throw Error(`Unsupported extension: ${ext}`);
  const visit = value => { if (!value || typeof value !== 'object') return; if (value.extensions) for (const ext of Object.keys(value.extensions)) if (!supported.has(ext)) throw Error(`Unsupported extension: ${ext}`); for (const child of Object.values(value)) visit(child); };
  visit(json);
  for (const material of json.materials || []) if (material.alphaMode === 'BLEND') throw Error('Transparent BLEND ordering requires rendered review; refused');
  for (const mesh of json.meshes || []) for (const prim of mesh.primitives || []) {
    if ((prim.mode ?? 4) !== 4 || prim.targets?.length) throw Error('Only triangle primitives without morph targets are supported');
    if (!Object.hasOwn(prim.attributes || {}, 'POSITION')) throw Error('Missing POSITION');
    if (Object.keys(prim.attributes).some(k => k.startsWith('JOINTS_') || k.startsWith('WEIGHTS_'))) throw Error('Skin attributes refused');
  }
  if ((json.buffers || []).some(x => x.uri) || (json.images || []).some(x => x.uri)) throw Error('Only embedded buffers/images are supported');
  // Index/accessor repacking can discard these fields. Refuse rather than
  // silently dropping provenance that this deliberately narrow adapter cannot verify.
  if (Object.keys(json.asset || {}).some(k => !['version', 'generator'].includes(k))) throw Error('Asset metadata beyond version/generator is unsupported');
  for (const kind of ['accessors', 'bufferViews', 'buffers']) for (const item of json[kind] || []) {
    if (item.name || item.extras || item.extensions) throw Error(`Unsupported ${kind} metadata`);
  }
  for (const item of json.images || []) if (item.extras || item.extensions) throw Error('Unsupported image metadata');
  return json;
}

function geometry(document) {
  let vertices = 0, triangles = 0;
  const primitives = [];
  for (const mesh of document.getRoot().listMeshes()) for (const prim of mesh.listPrimitives()) {
    const semantics = prim.listSemantics().sort();
    const accessors = semantics.map(s => prim.getAttribute(s));
    const count = prim.getAttribute('POSITION').getCount();
    const schema = accessors.map((a, i) => [semantics[i], a.getType(), a.getComponentType(), a.getNormalized()]);
    if (accessors.some(a => a.getCount() !== count || !a.getArray())) throw Error('Invalid vertex streams');
    const index = prim.getIndices()?.getArray() || Uint32Array.from({ length: count }, (_, i) => i);
    if (index.length % 3) throw Error('Non-triangle index count');
    const vertexHashes = Array.from({ length: count }, (_, i) => {
      const h = createHash('sha256');
      for (const a of accessors) {
        const array = a.getArray(), size = a.getElementSize(), stride = size * array.BYTES_PER_ELEMENT;
        for (let c = 0; c < size; c++) if (!Number.isFinite(array[i * size + c])) throw Error('Nonfinite vertex attribute');
        h.update(Buffer.from(array.buffer, array.byteOffset + i * stride, stride));
      }
      return h.digest('hex');
    });
    const faces = [];
    for (let i = 0; i < index.length; i += 3) {
      const v = [index[i], index[i + 1], index[i + 2]].map(j => { if (j >= count) throw Error('Out-of-range index'); return vertexHashes[j]; });
      // Cyclic rotations retain winding. Sorting all three corners would miss reversed faces.
      faces.push(sha([v.join(''), [v[1], v[2], v[0]].join(''), [v[2], v[0], v[1]].join('')].sort()[0]));
    }
    faces.sort(); vertices += count; triangles += faces.length;
    primitives.push({ mesh: mesh.getName(), material: document.getRoot().listMaterials().indexOf(prim.getMaterial()), schema, triangles: faces.length, orientedAttributeTriangles: sha(faces.join('')) });
  }
  return { vertices, triangles, primitives };
}

async function snapshot(document) {
  const { json } = await io.writeJSON(document);
  const stable = Object.fromEntries(Object.entries(json).filter(([k]) => !['asset', 'buffers', 'bufferViews', 'accessors', 'meshes', 'images'].includes(k)));
  return {
    stable,
    meshes: json.meshes?.map(m => ({ ...m, primitives: m.primitives.map(p => Object.fromEntries(Object.entries(p).filter(([k]) => !['attributes', 'indices'].includes(k)))) })),
    textures: document.getRoot().listTextures().map(t => ({ name: t.getName(), mime: t.getMimeType(), extras: t.getExtras(), sha256: sha(t.getImage() || new Uint8Array()) })),
    geometry: geometry(document),
  };
}

export async function transformStatic(bytes) {
  inspectContainer(bytes);
  const document = await io.readBinary(new Uint8Array(bytes));
  const before = await snapshot(document);
  await MeshoptEncoder.ready;
  await document.transform(weld(), reorder({ encoder: MeshoptEncoder, target: 'performance', cleanup: true }));
  const candidate = Buffer.from(await io.writeBinary(document));
  inspectContainer(candidate);
  const reloaded = await io.readBinary(new Uint8Array(candidate));
  const after = await snapshot(reloaded);
  equal(before.stable, after.stable, 'Scenes, nodes, materials, samplers or metadata');
  equal(before.meshes, after.meshes, 'Mesh/primitive metadata');
  equal(before.textures, after.textures, 'Embedded image bytes or metadata');
  equal(before.geometry.primitives, after.geometry.primitives, 'Oriented triangles or any vertex attribute');
  return { candidate, before: before.geometry, after: after.geometry, textures: after.textures.length };
}

export async function run(inputPath, outputPath) {
  const input = await fs.realpath(inputPath);
  const output = path.resolve(outputPath);
  const parent = await fs.realpath(path.dirname(output));
  if (path.join(parent, path.basename(output)) !== output) throw Error('Output parent must be canonical (no symlinks)');
  // When installed in the repository, prevent writes anywhere inside its checkout.
  let cursor = path.dirname(fileURLToPath(import.meta.url)), repository = null;
  while (cursor !== path.dirname(cursor)) {
    try { await fs.access(path.join(cursor, '.git')); repository = cursor; break; } catch { cursor = path.dirname(cursor); }
  }
  if (repository && (output === repository || output.startsWith(repository + path.sep))) throw Error('Output must be outside the repository');
  if (input === output || input.startsWith(output + path.sep)) throw Error('Output may not contain the source');
  const stat = await fs.stat(input);
  if (stat.size > 64 * 1024 * 1024) throw Error('Input exceeds the 64 MiB inspection budget');
  try { await fs.lstat(output); throw Error('Output directory already exists; use a fresh path'); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const bytes = await fs.readFile(input), inputSha = sha(bytes);
  const start = performance.now();
  const result = await transformStatic(bytes);
  if (sha(await fs.readFile(input)) !== inputSha) throw Error('Input changed during inspection');
  const report = {
    schema: 1, scope: 'Offline static geometry identity and size; no rendered or GPU acceptance',
    input: { path: input, sha256: inputSha, bytes: bytes.length },
    candidate: { name: 'candidate.glb', sha256: sha(result.candidate), bytes: result.candidate.length },
    libraries: { '@gltf-transform/core': '4.3.0', '@gltf-transform/extensions': '4.3.0', '@gltf-transform/functions': '4.3.0', meshoptimizer: '0.24.0' },
    operations: ['bitwise-identical weld', 'index/vertex reorder: performance', 'unused accessor cleanup'],
    before: { vertices: result.before.vertices, triangles: result.before.triangles, primitives: result.before.primitives.length },
    after: { vertices: result.after.vertices, triangles: result.after.triangles, primitives: result.after.primitives.length },
    preserved: { orientedTrianglesAndAllVertexAttributes: true, normalizedSceneNodeMaterialMeshMetadata: true, embeddedImageCount: result.textures, inputUnchanged: true },
    geometry: result.after.primitives, elapsedMs: Math.round(performance.now() - start),
  };
  await fs.mkdir(output); // Exclusive fresh directory; no runtime replacement.
  await fs.writeFile(path.join(output, 'candidate.glb'), result.candidate, { flag: 'wx' });
  await fs.writeFile(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  return report;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  if (process.argv.length !== 4) { console.error('Usage: node static-world-preflight.mjs INPUT.glb /absolute/fresh/output'); process.exitCode = 2; }
  else try { const r = await run(process.argv[2], process.argv[3]); console.log(JSON.stringify({ report: path.join(path.resolve(process.argv[3]), 'report.json'), before: r.before, after: r.after, bytes: [r.input.bytes, r.candidate.bytes] })); }
  catch (e) { console.error(e.message); process.exitCode = 1; }
}
