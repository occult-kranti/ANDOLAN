import {
  ACESFilmicToneMapping,
  Box3,
  CanvasTexture,
  DirectionalLight,
  EquirectangularReflectionMapping,
  GLTFLoader,
  HemisphereLight,
  MathUtils,
  OrbitControls,
  PerspectiveCamera,
  PMREMGenerator,
  RoomEnvironment,
  Scene,
  Spherical,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from './three.bundle.mjs';

// The .blend and metric survey express ENU. glTF exports horizontal north as negative Z.
const gltf = ([east, north, up]) => new Vector3(east, up, -north);

function districtSky() {
  const strip = document.createElement('canvas');
  strip.width = 128;
  strip.height = 64;
  const ctx = strip.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 64);
  for (const [at, color] of [
    [0, '#7295a6'],
    [0.27, '#a1bcc2'],
    [0.47, '#e8d7b4'],
    [0.52, '#d6c9aa'],
    [0.67, '#aaa38d'],
    [1, '#868872'],
  ])
    gradient.addColorStop(at, color);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 128, 64);
  const sky = new CanvasTexture(strip);
  sky.mapping = EquirectangularReflectionMapping;
  sky.colorSpace = SRGBColorSpace;
  return sky;
}

export async function createOrbit(surface, modelURL, register, onProgress, onUnavailable) {
  const renderer = new WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  let model, controls, environment, sky, sun;
  try {
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    renderer.toneMapping = ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.02;
    const scene = new Scene();
    sky = districtSky();
    scene.background = sky;
    scene.add(new HemisphereLight(0xffecd0, 0x8b9f9e, 1.05));
    sun = new DirectionalLight(0xffe8bd, 2.25);
    scene.add(sun, sun.target);
    // A small offline environment map gives the copper and glazed indigo a readable reflection.
    const room = new RoomEnvironment();
    const pmrem = new PMREMGenerator(renderer);
    try {
      environment = pmrem.fromScene(room, 0.045);
      scene.environment = environment.texture;
      scene.environmentIntensity = 0.56;
    } finally {
      room.dispose();
      pmrem.dispose();
    }
    const loaded = await new GLTFLoader().loadAsync(modelURL, (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total);
    });
    model = loaded.scene;
    scene.add(model);
    const bounds = new Box3().setFromObject(model);
    if (bounds.isEmpty()) throw new Error('The district contains no visible model bounds.');
    const center = bounds.getCenter(new Vector3());
    const radius = Math.max(1, bounds.getSize(new Vector3()).length() * 0.5);
    // Architecture is static. Bake the directional shadow map once per context.
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.autoUpdate = false;
    renderer.shadowMap.needsUpdate = true;
    sun.position.copy(center).add(new Vector3(-48, 96, 74).normalize().multiplyScalar(radius * 2));
    sun.target.position.copy(center);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, {
      left: -radius,
      right: radius,
      top: radius,
      bottom: -radius,
      near: radius * 0.5,
      far: radius * 4,
    });
    sun.shadow.camera.updateProjectionMatrix();
    sun.shadow.normalBias = 0.04;
    sun.shadow.bias = -0.00012;
    model.traverse((node) => {
      if (!node.isMesh) return;
      node.receiveShadow = true;
      node.castShadow = ![].concat(node.material).every((material) => material?.transparent);
    });
    const canvas = renderer.domElement;
    canvas.tabIndex = 0;
    canvas.setAttribute('aria-label', 'Orbitable Monsoon Exchange district model');
    canvas.setAttribute('aria-describedby', 'orbit-help');
    surface.replaceChildren(canvas);
    const camera = new PerspectiveCamera(42, 1, Math.max(0.035, radius / 4000), radius * 14);
    controls = new OrbitControls(camera, canvas);
    controls.enableDamping = false;
    controls.minDistance = 0.8;
    controls.maxDistance = radius * 4.5;
    let landmark = 'overview';
    let enabled = false;
    let scheduled = 0;
    let lost = false;
    let walk;
    let pristine = true;
    let lastWidth = 0,
      lastHeight = 0;
    function render() {
      if (enabled && !lost && !scheduled) {
        scheduled = requestAnimationFrame(() => {
          scheduled = 0;
          if (enabled && !lost) renderer.render(scene, camera);
        });
      }
    }
    function resize(reframe = false) {
      const w = surface.clientWidth,
        h = surface.clientHeight;
      if (!enabled || !w || !h || (w === lastWidth && h === lastHeight)) return;
      lastWidth = w;
      lastHeight = h;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
      if (reframe && pristine && !walk) aim(landmark);
      else render();
    }
    function fitDistrict(target, axis) {
      const right = new Vector3().crossVectors(camera.up, axis).normalize();
      const up = new Vector3().crossVectors(axis, right);
      const tanV = Math.tan(MathUtils.degToRad(camera.fov * 0.5));
      const corner = new Vector3();
      let fit = controls.minDistance;
      for (const x of [bounds.min.x, bounds.max.x]) {
        for (const y of [bounds.min.y, bounds.max.y]) {
          for (const z of [bounds.min.z, bounds.max.z]) {
            corner.set(x, y, z).sub(target);
            const planar = Math.max(
              Math.abs(corner.dot(right)) / (tanV * camera.aspect),
              Math.abs(corner.dot(up)) / tanV,
            );
            fit = Math.max(fit, corner.dot(axis) + planar);
          }
        }
      }
      camera.position.copy(target).addScaledVector(axis, fit * 1.08);
    }
    function aim(key = landmark) {
      landmark = key;
      pristine = true;
      controls.maxPolarAngle = Math.PI * (key === 'overview' ? 0.498 : 0.93);
      resize();
      const shot = register.cameras?.[key];
      if (shot?.position && shot?.target) {
        const eye = gltf(shot.position),
          target = gltf(shot.target);
        controls.target.copy(target);
        if (key === 'overview') {
          camera.fov = 42;
          fitDistrict(target, eye.sub(target).normalize());
        } else {
          camera.position.copy(eye);
          camera.fov = MathUtils.radToDeg(
            2 * Math.atan(36 / (2 * (shot.lens_mm || 29) * Math.max(camera.aspect, 1))),
          );
        }
      } else {
        controls.target.copy(center);
        camera.fov = 42;
        fitDistrict(center, new Vector3(0.64, 0.8, 1).normalize());
      }
      camera.updateProjectionMatrix();
      controls.update();
      canvas.dataset.landmark = key;
      render();
    }
    function move(horizontal = 0, vertical = 0, zoom = 1) {
      if (walk) return;
      pristine = false;
      const sphere = new Spherical().setFromVector3(camera.position.clone().sub(controls.target));
      sphere.theta += horizontal;
      sphere.phi = MathUtils.clamp(sphere.phi + vertical, 0.05, controls.maxPolarAngle);
      sphere.radius = MathUtils.clamp(sphere.radius * zoom, controls.minDistance, controls.maxDistance);
      camera.position.copy(controls.target).add(new Vector3().setFromSpherical(sphere));
      controls.update();
      render();
    }
    canvas.addEventListener('keydown', (event) => {
      if (walk || event.altKey || event.ctrlKey || event.metaKey) return;
      const actions = {
        ArrowLeft: [-0.16],
        ArrowRight: [0.16],
        ArrowUp: [0, -0.12],
        ArrowDown: [0, 0.12],
        '+': [0, 0, 0.83],
        '=': [0, 0, 0.83],
        '-': [0, 0, 1.2],
      };
      if (event.key === 'Home') aim();
      else if (actions[event.key]) move(...actions[event.key]);
      else return;
      event.preventDefault();
    });
    function activate(value) {
      if (lost) return;
      enabled = value;
      controls.enabled = value && !walk;
      if (!value && scheduled) {
        cancelAnimationFrame(scheduled);
        scheduled = 0;
      }
      if (value) resize();
    }
    function beginWalk(route, eye) {
      const points = route.witness.map(gltf);
      const lengths = [0];
      for (let i = 1; i < points.length; i++) {
        lengths.push(lengths[i - 1] + points[i - 1].distanceTo(points[i]));
      }
      walk = { points, lengths, eye, total: lengths.at(-1) };
      controls.enabled = false;
      canvas.style.touchAction = 'pan-y';
      canvas.dataset.route = route.id;
      canvas.setAttribute('aria-label', `Eye-height walk along ${route.name}`);
      canvas.setAttribute('aria-describedby', 'walk-help');
      camera.fov = 66;
      camera.updateProjectionMatrix();
      seekWalk(0);
    }
    function walkPoint(distance, out) {
      const { points, lengths } = walk;
      let i = 1;
      while (i < lengths.length - 1 && lengths[i] < distance) i++;
      const span = lengths[i] - lengths[i - 1];
      return out.lerpVectors(
        points[i - 1],
        points[i],
        span > 0 ? (distance - lengths[i - 1]) / span : 0,
      );
    }
    const ahead = new Vector3(),
      behind = new Vector3();
    function seekWalk(fraction) {
      if (!walk) return;
      const d = MathUtils.clamp(fraction, 0, 1) * walk.total;
      walkPoint(d, camera.position);
      camera.position.y += walk.eye;
      // Look through corners without cutting the capsule-tested path or adding camera bob.
      walkPoint(Math.max(0, d - 1.6), behind);
      walkPoint(Math.min(walk.total, d + 3.8), ahead)
        .sub(behind)
        .normalize();
      ahead.y = ahead.y * 0.65 - 0.045;
      camera.lookAt(ahead.add(camera.position));
      render();
    }
    function endWalk() {
      if (!walk) return;
      walk = null;
      delete canvas.dataset.route;
      canvas.style.touchAction = 'none';
      canvas.setAttribute('aria-label', 'Orbitable Monsoon Exchange district model');
      canvas.setAttribute('aria-describedby', 'orbit-help');
      controls.enabled = enabled;
    }
    const observer = new ResizeObserver(() => resize(true));
    observer.observe(surface);
    controls.addEventListener('start', () => {
      pristine = false;
    });
    controls.addEventListener('change', render);
    canvas.addEventListener(
      'webglcontextlost',
      (event) => {
        event.preventDefault();
        lost = true;
        controls.dispose();
        observer.disconnect();
        release();
        canvas.remove();
        onUnavailable();
      },
      { once: true },
    );
    return { activate, aim, move, beginWalk, seekWalk, endWalk };
  } catch (error) {
    release();
    throw error;
  }
  function release() {
    const geometries = new Set(),
      materials = new Set(),
      textures = new Set();
    model?.traverse((node) => {
      if (!node.isMesh) return;
      geometries.add(node.geometry);
      for (const material of [].concat(node.material)) {
        if (!material) continue;
        materials.add(material);
        for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
      }
    });
    for (const item of [...geometries, ...materials, ...textures]) item.dispose();
    environment?.dispose();
    sky?.dispose();
    sun?.shadow.dispose();
    renderer.dispose();
  }
}
