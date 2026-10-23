import * as pc from 'playcanvas';
import { createOriginalEnvironment } from '../../../../yuga/client/environment-light';
import './styles.css';

const canvas = document.querySelector<HTMLCanvasElement>('#viewer')!;
const status = document.querySelector<HTMLElement>('#status-text')!;
const state = document.querySelector<HTMLElement>('#state')!;
const retry = document.querySelector<HTMLButtonElement>('#retry')!;
const diagnostic = document.querySelector<HTMLElement>('#diagnostics')!;
const buttons = [...document.querySelectorAll<HTMLButtonElement>('.tools button')];
const report: Record<string, unknown> = { status: 'initializing', engine: 'PlayCanvas 2.23.3', source: '../media/rama-generated.glb', unrigged: true, animations: 0, renderedFrames: 0 };
(window as unknown as { __YUGA_ASSET_VIEWER__: typeof report }).__YUGA_ASSET_VIEWER__ = report;
let app: pc.Application | null = null;
let camera: pc.Entity;
let source: pc.Entity | null = null;
let sourceAsset: pc.Asset<'container'> | null = null;
let environment: ReturnType<typeof createOriginalEnvironment> | null = null;
let ready = false, disposed = false, request = 0, restoreContext = false;
let yaw = -12, pitch = 6, distance = 3.5, fittedDistance = 3.5, radius = 1;
let sourceHalf: pc.Vec3 | null = null;
const target = new pc.Vec3(0, .7, 0);
const abort = new AbortController();
let resizeObserver: ResizeObserver | null = null;

function render() { if (app && !document.hidden) app.renderNextFrame = true; }
function refit(preserveZoom = true) {
  if (!sourceHalf) return;
  const ratio = preserveZoom ? distance / fittedDistance : 1;
  const aspect = canvas.clientWidth / Math.max(1, canvas.clientHeight);
  const tan = Math.tan(36 * Math.PI / 360);
  fittedDistance = Math.max(sourceHalf.y / tan, sourceHalf.x / (tan * aspect)) * 1.25 + sourceHalf.z;
  distance = fittedDistance * ratio;
}
function publishCamera() { report.camera = { yaw, pitch, distance }; }
function updateCamera() {
  if (!app || !camera) return;
  const a = yaw * Math.PI / 180, b = pitch * Math.PI / 180;
  camera.setPosition(target.x + distance * Math.sin(a) * Math.cos(b), target.y + distance * Math.sin(b), target.z + distance * Math.cos(a) * Math.cos(b));
  camera.lookAt(target);
  publishCamera(); render();
}
function orbit(x: number, y = 0) { if (!ready) return; yaw += x; pitch = pc.math.clamp(pitch + y, -35, 70); updateCamera(); }
function zoom(amount: number) { if (!ready) return; distance = pc.math.clamp(distance * amount, fittedDistance * .4, fittedDistance * 2.8); updateCamera(); }
function reset() { if (!ready) return; yaw = -12; pitch = 6; distance = fittedDistance; updateCamera(); }
function showError(message: string) {
  ready = false; report.status = 'failed'; report.error = message;
  buttons.forEach(button => button.disabled = true);
  state.hidden = false; status.textContent = message; retry.hidden = false;
  diagnostic.textContent = 'No source-model acceptance is implied by a failed preview.';
}
function fit(root: pc.Entity, resource: pc.ContainerResource) {
  const meshes = new Set<pc.Mesh>(); const materials = new Set<pc.Material>();
  let instances = 0, skins = 0, triangles = 0;
  let bounds: pc.BoundingBox | null = null;
  for (const component of root.findComponents('render') as pc.RenderComponent[]) {
    for (const instance of component.meshInstances) {
      if (!instance.mesh) continue;
      instances++; meshes.add(instance.mesh);
      if (instance.material) materials.add(instance.material);
      if (instance.skinInstance) skins++;
      if (bounds) bounds.add(instance.aabb); else bounds = instance.aabb.clone();
    }
  }
  if (!bounds || !instances) throw new Error('The GLB opened without a renderable mesh.');
  for (const mesh of meshes) for (const primitive of mesh.primitive) if (primitive.type === pc.PRIMITIVE_TRIANGLES) triangles += primitive.count / 3;
  const center = bounds.center.clone(), half = bounds.halfExtents.clone();
  if (![center.x, center.y, center.z, half.x, half.y, half.z].every(Number.isFinite) || half.length() < 1e-6) throw new Error('The mesh has invalid bounds.');
  root.setPosition(-center.x, -(center.y - half.y), -center.z);
  radius = half.length(); target.set(0, half.y, 0);
  sourceHalf = half; refit(false);
  camera.camera!.nearClip = Math.max(.001, radius / 1000);
  camera.camera!.farClip = Math.max(30, radius * 50);
  const floor = app!.root.findByName('inspection floor');
  floor?.setLocalScale(radius * 5, Math.max(.005, radius * .01), radius * 5);
  floor?.setPosition(0, -Math.max(.005, radius * .01), 0);
  Object.assign(report, { unrigged: skins === 0, meshes: meshes.size, meshInstances: instances, triangles: Math.round(triangles), materials: materials.size,
    skinnedPrimitives: skins, animations: resource.animations.length,
    bounds: { width: half.x * 2, height: half.y * 2, depth: half.z * 2 } });
  diagnostic.textContent = `${meshes.size} mesh${meshes.size === 1 ? '' : 'es'} · ${Math.round(triangles).toLocaleString()} triangles · ${materials.size} material${materials.size === 1 ? '' : 's'} · ${skins} skinned primitives · ${resource.animations.length} animations`;
}
function load() {
  if (!app || disposed) return;
  if (restoreContext) { location.reload(); return; }
  const serial = ++request;
  ready = false; report.status = 'loading'; delete report.error;
  buttons.forEach(button => button.disabled = true); retry.hidden = true; state.hidden = false;
  status.textContent = 'Loading the actual Rama mesh and embedded textures…';
  source?.destroy(); source = null;
  if (sourceAsset) { sourceAsset.unload(); app.assets.remove(sourceAsset); sourceAsset = null; }
  const timeout = window.setTimeout(() => { if (serial === request) { request++; showError('The model did not finish loading. Retry the model or return to production.'); } }, 60000);
  const url = new URL('../media/rama-generated.glb', document.baseURI).href;
  app.assets.loadFromUrl(url, 'container', (error, asset) => {
    window.clearTimeout(timeout);
    if (disposed || serial !== request) { if (asset) { asset.unload(); app?.assets.remove(asset); } return; }
    if (error || !asset?.resource) { if (asset) { asset.unload(); app!.assets.remove(asset); } showError('The Rama GLB could not load. Check that the source file is published, then retry.'); return; }
    try {
      sourceAsset = asset;
      source = asset.resource.instantiateRenderEntity({ castShadows: true, receiveShadows: true });
      source.name = 'generated Rama source; no rig or animation'; app!.root.addChild(source);
      fit(source, asset.resource);
      ready = true; report.status = 'ready'; buttons.forEach(button => button.disabled = false);
      state.hidden = true; status.textContent = 'Source model loaded.';
      updateCamera();
    } catch (failure) { showError(failure instanceof Error ? failure.message : 'The model could not be inspected.'); }
  });
}
function start() {
  try {
    app = new pc.Application(canvas, { graphicsDeviceOptions: { alpha: false, antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: true } });
    app.graphicsDevice.maxPixelRatio = Math.min(devicePixelRatio, 1.5);
    app.setCanvasFillMode(pc.FILLMODE_NONE); app.setCanvasResolution(pc.RESOLUTION_AUTO);
    app.scene.ambientLight = new pc.Color(.35, .39, .40); app.scene.exposure = 1.0;
    environment = createOriginalEnvironment(app);
    camera = new pc.Entity('source inspection camera', app);
    camera.addComponent('camera', { fov: 36, nearClip: .01, farClip: 40, clearColor: new pc.Color(.106, .13, .118) });
    camera.camera!.layers = camera.camera!.layers.filter(id => id !== pc.LAYERID_SKYBOX);
    app.root.addChild(camera);
    const lights: { name: string; angles: [number, number, number]; color: [number, number, number]; intensity: number; shadows: boolean }[] = [
      { name: 'neutral warm key', angles: [40, -30, 0], color: [1, .91, .78], intensity: 1.35, shadows: true },
      { name: 'cool fill', angles: [20, 125, 0], color: [.72, .83, 1], intensity: .5, shadows: false },
      { name: 'soft rim', angles: [-18, 155, 0], color: [1, .83, .61], intensity: .65, shadows: false },
    ];
    for (const light of lights) {
      const entity = new pc.Entity(light.name, app);
      entity.addComponent('light', { type: 'directional', color: new pc.Color(...light.color), intensity: light.intensity, castShadows: light.shadows,
        shadowResolution: 1024, shadowDistance: 12, normalOffsetBias: .02, shadowBias: .02 });
      entity.setEulerAngles(...light.angles); app.root.addChild(entity);
    }
    const floor = new pc.Entity('inspection floor', app);
    floor.addComponent('render', { type: 'box', castShadows: false, receiveShadows: true });
    const mat = new pc.StandardMaterial(); mat.diffuse.set(.095, .12, .103); mat.gloss = .12; mat.update();
    floor.render!.material = mat; app.root.addChild(floor);
    app.autoRender = false; app.on('postrender', () => { report.renderedFrames = Number(report.renderedFrames) + 1; });
    const resize = () => { if (!app || !canvas.clientWidth || !canvas.clientHeight) return; app.resizeCanvas(canvas.clientWidth, canvas.clientHeight); refit(); updateCamera(); };
    resizeObserver = new ResizeObserver(resize); resizeObserver.observe(canvas); resize(); app.start();
    load();
  } catch { showError('A WebGL 2 graphics context could not open. Enable browser graphics support and reload this viewer.'); retry.textContent = 'Reload viewer'; restoreContext = true; }
}
let drag: { id: number, x: number, y: number } | null = null;
canvas.addEventListener('pointerdown', event => { if (!ready) return; canvas.focus(); drag = { id: event.pointerId, x: event.clientX, y: event.clientY }; canvas.setPointerCapture(event.pointerId); }, { signal: abort.signal });
canvas.addEventListener('pointermove', event => { if (!drag || event.pointerId !== drag.id) return; orbit(-(event.clientX - drag.x) * .35, (event.clientY - drag.y) * .25); drag.x = event.clientX; drag.y = event.clientY; }, { signal: abort.signal });
for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(name, () => { drag = null; }, { signal: abort.signal });
canvas.addEventListener('wheel', event => { if (!ready) return; event.preventDefault(); zoom(event.deltaY > 0 ? 1.08 : .92); }, { passive: false, signal: abort.signal });
canvas.addEventListener('keydown', event => {
  if (!ready) return;
  const handlers: Record<string, () => void> = { ArrowLeft: () => orbit(-12), ArrowRight: () => orbit(12), ArrowUp: () => orbit(0, 8), ArrowDown: () => orbit(0, -8), '+': () => zoom(.85), '=': () => zoom(.85), '-': () => zoom(1.15), Home: reset };
  if (handlers[event.key]) { event.preventDefault(); handlers[event.key](); }
}, { signal: abort.signal });
document.querySelector('#left')!.addEventListener('click', () => orbit(-15), { signal: abort.signal });
document.querySelector('#right')!.addEventListener('click', () => orbit(15), { signal: abort.signal });
document.querySelector('#zoom-in')!.addEventListener('click', () => zoom(.85), { signal: abort.signal });
document.querySelector('#zoom-out')!.addEventListener('click', () => zoom(1.15), { signal: abort.signal });
document.querySelector('#reset')!.addEventListener('click', reset, { signal: abort.signal });
retry.addEventListener('click', () => { if (restoreContext) location.reload(); else load(); }, { signal: abort.signal });
canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); restoreContext = true; showError('The browser graphics context was lost. Reload the viewer to recover.'); retry.textContent = 'Reload viewer'; }, { signal: abort.signal });
document.addEventListener('visibilitychange', () => { if (!document.hidden) render(); }, { signal: abort.signal });
window.addEventListener('pagehide', () => { disposed = true; request++; abort.abort(); resizeObserver?.disconnect(); source?.destroy(); if (sourceAsset) sourceAsset.unload(); environment?.destroy(); app?.destroy(); app = null; }, { once: true });
start();
