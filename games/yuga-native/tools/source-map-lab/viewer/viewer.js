import * as THREE from "three";
import { GLTFLoader } from "./vendor/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "./vendor/examples/jsm/controls/OrbitControls.js";

const get = (id) => document.getElementById(id);
const surface = get("surface");
const status = get("status");
const chooser = get("view");
const config = await fetch("./views.json").then((response) => {
  if (!response.ok) throw new Error("The local camera register is missing.");
  return response.json();
});
const coatings = new Map();
let finish = "jade";
let mode = "still";
let loading = false;
let renderer, scene, camera, orbit;

function redraw() {
  if (renderer && mode === "3d") renderer.render(scene, camera);
}
function resize() {
  if (!camera || mode !== "3d") return;
  const width = surface.clientWidth,
    height = surface.clientHeight;
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  const aspect = width / height;
  if (camera.isOrthographicCamera) {
    const half = config.views.overview.span / 2;
    camera.top = half / Math.min(1, aspect);
    camera.bottom = -camera.top;
    camera.right = camera.top * aspect;
    camera.left = -camera.right;
  } else {
    camera.aspect = aspect;
  }
  camera.updateProjectionMatrix();
  redraw();
}
function frame() {
  const shot = config.views[chooser.value];
  get("still").src = shot[finish];
  get("still").alt =
    `${shot.title} in the ${finish === "jade" ? "jade" : "original"} ground finish`;
  get("caption").textContent =
    mode === "3d"
      ? "Drag to orbit · scroll to zoom · right-drag to pan"
      : shot.title + " · matching Blender camera";
  if (mode !== "3d") return;
  orbit?.dispose();
  if (shot.span) {
    camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 700);
    camera.up.set(0, 0, -1);
  } else {
    const fov = THREE.MathUtils.radToDeg(
      2 * Math.atan(36 / (2 * 24 * (16 / 9))),
    );
    camera = new THREE.PerspectiveCamera(fov, 1, 0.1, 700);
  }
  camera.position.fromArray(shot.eye);
  orbit = new OrbitControls(camera, renderer.domElement);
  orbit.target.fromArray(shot.target);
  orbit.minDistance = 0.35;
  orbit.maxDistance = 450;
  orbit.minZoom = 0.5;
  orbit.maxZoom = 150;
  orbit.update();
  orbit.addEventListener("change", redraw);
  resize();
}
function paint() {
  for (const [material, original] of coatings) {
    material.color.copy(original);
    if (finish === "jade") {
      material.color.r *= config.gains[0];
      material.color.g *= config.gains[1];
      material.color.b *= config.gains[2];
    }
  }
  for (const button of document.querySelectorAll("[data-finish]")) {
    button.setAttribute("aria-pressed", button.dataset.finish === finish);
  }
  const shot = config.views[chooser.value];
  get("still").src = shot[finish];
  get("still").alt =
    `${shot.title} in the ${finish === "jade" ? "jade" : "original"} ground finish`;
  redraw();
}
async function enter() {
  if (loading) return;
  if (mode === "3d") {
    mode = "still";
    surface.hidden = true;
    get("mode").textContent = "Inspect in 3D";
    status.textContent = "";
    frame();
    return;
  }
  if (!renderer) {
    loading = true;
    get("mode").disabled = true;
    status.textContent = "Loading the complete local mesh…";
    let graphics;
    try {
      graphics = new THREE.WebGLRenderer({
        antialias: false,
        powerPreference: "high-performance",
      });
      graphics.setPixelRatio(Math.min(window.devicePixelRatio, 1.35));
      graphics.setClearColor(0x344643);
      const world = new THREE.Scene();
      world.add(new THREE.HemisphereLight(0xfff2d8, 0x839899, 2));
      const sun = new THREE.DirectionalLight(0xfff0cf, 2);
      sun.position.set(-65, 110, 30);
      world.add(sun);
      const { scene: level } = await new GLTFLoader().loadAsync(
        "./models/dust2-baseline.glb",
        (event) => {
          if (event.total)
            status.textContent =
              "Loading map · " +
              Math.round((event.loaded / event.total) * 100) +
              "%";
        },
      );
      level.traverse((object) => {
        if (!object.isMesh) return;
        for (const material of [].concat(object.material)) {
          if (material.userData.yugaGround && !coatings.has(material))
            coatings.set(material, material.color.clone());
        }
      });
      if (!coatings.size)
        throw new Error("The model has no registered ground materials.");
      world.add(level);
      surface.append(graphics.domElement);
      graphics.domElement.setAttribute(
        "aria-label",
        "Interactive 3D view of the local Dust II map",
      );
      renderer = graphics;
      scene = world;
    } catch (error) {
      graphics?.dispose();
      status.textContent =
        "3D could not open on this device. You can still compare the renders and download the model.";
      console.warn(error);
      return;
    } finally {
      loading = false;
      get("mode").disabled = false;
    }
  }
  mode = "3d";
  surface.hidden = false;
  get("mode").textContent = "Show renders";
  status.textContent = coatings.size + " ground materials · full local mesh";
  frame();
  paint();
}
for (const button of document.querySelectorAll("[data-finish]")) {
  button.addEventListener("click", () => {
    finish = button.dataset.finish;
    paint();
  });
}
chooser.addEventListener("change", frame);
get("mode").addEventListener("click", enter);
new ResizeObserver(resize).observe(get("stage"));
frame();
