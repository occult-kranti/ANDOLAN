#!/usr/bin/env node
/** Original offline adapter; upstream library notices are in NOTICE.md. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const canonical = (value) => JSON.stringify(value, (_, v) => v && !Array.isArray(v) && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v);
const equal = (a, b, label) => { if (canonical(a) !== canonical(b)) throw Error(`${label} changed`); };
let runtime;
export async function libraries(dependencyRoot = process.env.YUGA_REUSE_DEPENDENCIES || fileURLToPath(new URL('../reuse-art/', import.meta.url))) {
  const root = await fs.realpath(dependencyRoot);
  const expected = { '@gltf-transform/core': '4.3.0', '@gltf-transform/extensions': '4.3.0', '@gltf-transform/functions': '4.3.0', meshoptimizer: '0.24.0' };
  const sourceLock = await fs.readFile(fileURLToPath(new URL('../reuse-art/package-lock.json', import.meta.url)));
  const lock = await fs.readFile(path.join(root, 'package-lock.json'));
  if (sha(lock) !== sha(sourceLock)) throw Error('Dependency lock must match the existing canonical lock exactly');
  const resolve = createRequire(path.join(root, 'package.json'));
  const modules = {}, entries = {};
  for (const [name, version] of Object.entries(expected)) {
    let folder = path.dirname(resolve.resolve(name)), manifest;
    while (folder !== path.dirname(folder)) {
      try { const parsed = JSON.parse(await fs.readFile(path.join(folder, 'package.json'))); if (parsed.name === name) { manifest = parsed; break; } } catch {}
      folder = path.dirname(folder);
    }
    if (!manifest || manifest.version !== version) throw Error(`Installed version mismatch: ${name}`);
    const entry = path.join(folder, manifest.module || manifest.main);
    modules[name] = await import(pathToFileURL(entry).href);
    entries[name] = { version, entry: path.relative(root, entry), sha256: sha(await fs.readFile(entry)) };
  }
  const { NodeIO } = modules['@gltf-transform/core'];
  const { KHRMaterialsEmissiveStrength, EXTTextureWebP } = modules['@gltf-transform/extensions'];
  return { io: new NodeIO().setAllowNetwork(false).registerExtensions([KHRMaterialsEmissiveStrength, EXTTextureWebP]),
    weld: modules['@gltf-transform/functions'].weld, reorder: modules['@gltf-transform/functions'].reorder,
    MeshoptEncoder: modules.meshoptimizer.MeshoptEncoder, sourceLockSha256: sha(lock), entries, Document: modules['@gltf-transform/core'].Document, EXTTextureWebP };
}
export async function initialize(dependencyRoot) { runtime = await libraries(dependencyRoot); return runtime; }
const current = () => { if (!runtime) throw Error('Call initialize() with the existing locked dependency installation first'); return runtime; };

export function inspectContainer(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.length < 28 || bytes.length > 64 * 1024 * 1024 || bytes.readUInt32LE(0) !== 0x46546c67 || bytes.readUInt32LE(4) !== 2 || bytes.readUInt32LE(8) !== bytes.length) throw Error('Expected bounded complete GLB v2');
  const chunks = [];
  for (let offset = 12; offset < bytes.length;) {
    if (offset + 8 > bytes.length) throw Error('Truncated chunk header');
    const length = bytes.readUInt32LE(offset), type = bytes.readUInt32LE(offset + 4);
    if (length % 4 || offset + 8 + length > bytes.length) throw Error('Invalid chunk bounds/alignment');
    chunks.push({ type, bytes: bytes.subarray(offset + 8, offset + 8 + length) });
    offset += 8 + length;
  }
  if (chunks.length !== 2 || chunks[0].type !== 0x4e4f534a || chunks[1].type !== 0x004e4942 || chunks[0].bytes.length > 4 * 1024 * 1024) throw Error('Expected one bounded JSON then one embedded BIN chunk');
  const json = JSON.parse(chunks[0].bytes.toString('utf8'));
  if (!json || typeof json !== 'object' || Array.isArray(json) || json.asset?.version !== '2.0') throw Error('Expected glTF 2.0 object');
  if (json.skins?.length || json.animations?.length) throw Error('Static meshes only: skins/animations refused');
  if (json.cameras?.length) throw Error('Cameras are outside this static mesh contract');
  const supported = new Set(['KHR_materials_emissive_strength', 'EXT_texture_webp']);
  for (const [kind, limit] of Object.entries({ meshes: 256, nodes: 4096, materials: 256, textures: 256, images: 256, accessors: 4096, bufferViews: 4096 })) {
    if (json[kind] !== undefined && (!Array.isArray(json[kind]) || json[kind].length > limit)) throw Error(`Invalid or oversized ${kind}`);
  }
  for (const kind of ['extensionsUsed', 'extensionsRequired']) if (json[kind] !== undefined && (!Array.isArray(json[kind]) || json[kind].some(v => typeof v !== 'string') || new Set(json[kind]).size !== json[kind].length)) throw Error('Invalid extension list');
  for (const ext of [...(json.extensionsUsed || []), ...(json.extensionsRequired || [])]) if (!supported.has(ext)) throw Error(`Unsupported extension: ${ext}`);
  for (const ext of json.extensionsRequired || []) if (!json.extensionsUsed?.includes(ext)) throw Error(`Required extension missing from extensionsUsed: ${ext}`);
  const visit = (value, trail = []) => {
    if (!value || typeof value !== 'object') return;
    if (Object.hasOwn(value, 'extensions')) {
      if (!value.extensions || typeof value.extensions !== 'object' || Array.isArray(value.extensions)) throw Error('Invalid extensions object');
      for (const ext of Object.keys(value.extensions)) {
        if (!supported.has(ext)) throw Error(`Unsupported extension: ${ext}`);
        if (!json.extensionsUsed?.includes(ext)) throw Error(`Undeclared extension: ${ext}`);
        const owner = ext === 'EXT_texture_webp' ? 'textures' : 'materials';
        if (trail.length !== 2 || trail[0] !== owner || !/^\d+$/.test(trail[1])) throw Error(`Unsupported extension placement: ${ext}`);
        const data = value.extensions[ext];
        if (!data || typeof data !== 'object' || Array.isArray(data)) throw Error(`Invalid extension payload: ${ext}`);
        if (ext === 'KHR_materials_emissive_strength' && (Object.keys(data).some(k => k !== 'emissiveStrength') || !Number.isFinite(data.emissiveStrength) || data.emissiveStrength < 0)) throw Error('Invalid emissive strength extension');
        if (ext === 'EXT_texture_webp' && Object.keys(data).some(k => k !== 'source')) throw Error('Unsupported WebP extension metadata');
      }
    }
    for (const [key, child] of Object.entries(value)) visit(child, [...trail, key]);
  };
  visit(json);
  for (const material of json.materials || []) if (material.alphaMode === 'BLEND') throw Error('Transparent BLEND ordering requires rendered review; refused');
  for (const mesh of json.meshes || []) for (const prim of mesh.primitives || []) {
    if ((prim.mode ?? 4) !== 4 || prim.targets?.length) throw Error('Only triangle primitives without morph targets are supported');
    if (!Object.hasOwn(prim.attributes || {}, 'POSITION')) throw Error('Missing POSITION');
    if (Object.keys(prim.attributes).some(k => k.startsWith('JOINTS_') || k.startsWith('WEIGHTS_'))) throw Error('Skin attributes refused');
    if (Object.keys(prim.attributes).length > 16) throw Error('Vertex semantic budget exceeded');
  }
  if ((json.buffers || []).some(x => Object.hasOwn(x, 'uri')) || (json.images || []).some(x => Object.hasOwn(x, 'uri'))) throw Error('Only embedded buffers/images are supported');
  const integer = (value, label, min = 0) => { if (!Number.isSafeInteger(value) || value < min) throw Error(`Invalid ${label}`); return value; };
  if (!Array.isArray(json.buffers) || json.buffers.length !== 1) throw Error('Expected one embedded buffer');
  const binaryLength = integer(json.buffers[0].byteLength, 'buffer length', 1);
  if (binaryLength > chunks[1].bytes.length || chunks[1].bytes.length - binaryLength > 3) throw Error('Buffer length does not match BIN chunk');
  for (const view of json.bufferViews || []) {
    if (!view || view.buffer !== 0) throw Error('Invalid bufferView buffer');
    const offset = integer(view.byteOffset ?? 0, 'bufferView offset'), length = integer(view.byteLength, 'bufferView length', 1);
    if (offset + length > binaryLength) throw Error('bufferView exceeds embedded buffer');
    if (view.byteStride !== undefined && (integer(view.byteStride, 'byteStride', 4) > 252 || view.byteStride % 4)) throw Error('Invalid bufferView stride');
  }
  const widths = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 }, sizes = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 };
  let decoded = 0;
  for (const accessor of json.accessors || []) {
    if (!accessor || accessor.sparse) throw Error('Sparse accessors are outside this preservation contract');
    const index = integer(accessor.bufferView, 'accessor bufferView'), view = json.bufferViews?.[index];
    if (!view || !widths[accessor.componentType] || !sizes[accessor.type]) throw Error('Invalid accessor layout');
    const count = integer(accessor.count, 'accessor count', 1), offset = integer(accessor.byteOffset ?? 0, 'accessor offset');
    const element = widths[accessor.componentType] * sizes[accessor.type], stride = view.byteStride ?? element;
    if (count > 2_000_000 || stride < element || offset % widths[accessor.componentType] || offset + (count - 1) * stride + element > view.byteLength) throw Error('Accessor exceeds bufferView or count budget');
    decoded += count * element;
    if (decoded > 256 * 1024 * 1024) throw Error('Decoded accessor budget exceeded');
  }
  for (const mesh of json.meshes || []) for (const prim of mesh.primitives || []) {
    const position = json.accessors?.[prim.attributes.POSITION];
    if (!position || position.type !== 'VEC3' || position.componentType !== 5126) throw Error('Expected float VEC3 POSITION');
    for (const index of Object.values(prim.attributes)) {
      const a = json.accessors?.[integer(index, 'attribute accessor')];
      if (!a || a.count !== position.count) throw Error('Mismatched vertex stream count');
    }
    if (prim.indices !== undefined) {
      const a = json.accessors?.[integer(prim.indices, 'indices accessor')];
      if (!a || a.type !== 'SCALAR' || ![5121,5123,5125].includes(a.componentType) || a.normalized || a.count % 3) throw Error('Invalid triangle index accessor');
    } else if (position.count % 3) throw Error('Non-triangle unindexed vertex count');
  }
  for (const image of json.images || []) {
    const view = json.bufferViews?.[integer(image.bufferView, 'image bufferView')];
    if (!view || !['image/webp', 'image/png', 'image/jpeg'].includes(image.mimeType)) throw Error('Unsupported image payload');
    if (image.mimeType === 'image/webp') {
      if (!json.extensionsUsed?.includes('EXT_texture_webp') || !json.extensionsRequired?.includes('EXT_texture_webp')) throw Error('Embedded WebP must declare required EXT_texture_webp');
      const data = chunks[1].bytes.subarray(view.byteOffset ?? 0, (view.byteOffset ?? 0) + view.byteLength);
      const riffLength = data.length >= 12 ? data.readUInt32LE(4) + 8 : 0;
      if (data.length < 20 || data.toString('ascii', 0, 4) !== 'RIFF' || data.toString('ascii', 8, 12) !== 'WEBP' || riffLength < 20 || riffLength > data.length || data.length - riffLength > 3 || data.subarray(riffLength).some(v => v !== 0 && v !== 32)) throw Error('Invalid embedded WebP container');
    }
  }
  for (const texture of json.textures || []) if (texture.extensions?.EXT_texture_webp) {
    const index = integer(texture.extensions.EXT_texture_webp.source, 'WebP texture source');
    if (texture.source !== undefined || json.images?.[index]?.mimeType !== 'image/webp') throw Error('Optional WebP fallback/source is outside this contract');
  }
  // Index/accessor repacking can discard these fields. Refuse rather than
  // silently dropping provenance that this deliberately narrow adapter cannot verify.
  if (Object.keys(json.asset || {}).some(k => !['version', 'generator'].includes(k))) throw Error('Asset metadata beyond version/generator is unsupported');
  for (const kind of ['accessors', 'bufferViews', 'buffers']) for (const item of json[kind] || []) {
    if (item.name || item.extras || item.extensions) throw Error(`Unsupported ${kind} metadata`);
  }
  for (const item of json.images || []) if (item.extras || item.extensions) throw Error('Unsupported image metadata');
  return json;
}

function rawImages(bytes, json) {
  const binaryStart = 28 + bytes.readUInt32LE(12);
  return (json.images || []).map(image => {
    const view = json.bufferViews[image.bufferView], start = binaryStart + (view.byteOffset || 0);
    return { mime: image.mimeType, bytes: view.byteLength, sha256: sha(bytes.subarray(start, start + view.byteLength)) };
  }).sort((a,b) => canonical(a).localeCompare(canonical(b)));
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
  const { io } = current();
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
  const { io, MeshoptEncoder, weld, reorder } = current();
  const sourceJSON = inspectContainer(bytes), sourceImages = rawImages(bytes, sourceJSON);
  const document = await io.readBinary(new Uint8Array(bytes));
  const before = await snapshot(document);
  await MeshoptEncoder.ready;
  await document.transform(weld(), reorder({ encoder: MeshoptEncoder, target: 'performance', cleanup: true }));
  const candidate = Buffer.from(await io.writeBinary(document));
  const candidateJSON = inspectContainer(candidate), candidateImages = rawImages(candidate, candidateJSON);
  equal(sourceImages, candidateImages, 'Raw original embedded image payloads (including publisher padding)');
  const reloaded = await io.readBinary(new Uint8Array(candidate));
  const after = await snapshot(reloaded);
  equal(before.stable, after.stable, 'Scenes, nodes, materials, samplers or metadata');
  equal(before.meshes, after.meshes, 'Mesh/primitive metadata');
  equal(before.textures, after.textures, 'Embedded image bytes or metadata');
  equal(before.geometry.primitives, after.geometry.primitives, 'Oriented triangles or any vertex attribute');
  return { candidate, before: before.geometry, after: after.geometry, textures: after.textures.length, rawImages: candidateImages, webpRequired: candidateJSON.extensionsRequired?.includes('EXT_texture_webp') ?? false };
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
    libraries: current().entries, dependencyLockSha256: current().sourceLockSha256,
    operations: ['bitwise-identical weld', 'index/vertex reorder: performance', 'unused accessor cleanup'],
    before: { vertices: result.before.vertices, triangles: result.before.triangles, primitives: result.before.primitives.length },
    after: { vertices: result.after.vertices, triangles: result.after.triangles, primitives: result.after.primitives.length },
    preserved: { orientedTrianglesAndAllVertexAttributes: true, normalizedSceneNodeMaterialMeshMetadata: true, embeddedImageCount: result.textures, inputUnchanged: true, requiredWebpExtension: result.webpRequired },
    embeddedImages: result.rawImages,
    geometry: result.after.primitives, elapsedMs: Math.round(performance.now() - start),
  };
  await fs.mkdir(output); // Exclusive fresh directory; no runtime replacement.
  await fs.writeFile(path.join(output, 'candidate.glb'), result.candidate, { flag: 'wx' });
  await fs.writeFile(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  return report;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  if (![4,6].includes(process.argv.length) || (process.argv.length === 6 && process.argv[4] !== '--dependencies')) { console.error('Usage: node webp-static-preflight.mjs INPUT.glb /absolute/fresh/output [--dependencies EXISTING_LOCKED_TOOL_DIR]'); process.exitCode = 2; }
  else try { await initialize(process.argv[5]); const r = await run(process.argv[2], process.argv[3]); console.log(JSON.stringify({ report: path.join(path.resolve(process.argv[3]), 'report.json'), before: r.before, after: r.after, bytes: [r.input.bytes, r.candidate.bytes] })); }
  catch (e) { console.error(e.message); process.exitCode = 1; }
}
