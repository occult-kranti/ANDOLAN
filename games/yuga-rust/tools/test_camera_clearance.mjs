import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { build } from 'esbuild';

const modulePath = fileURLToPath(new URL('../web/camera-clearance.ts', import.meta.url));
const mapPath = fileURLToPath(new URL('../../yuga-native/assets/world/confluence-map.json', import.meta.url));
const { outputFiles } = await build({ entryPoints: [modulePath], bundle: true, format: 'esm', write: false });
const sourceUrl = 'data:text/javascript;base64,' + Buffer.from(outputFiles[0].contents).toString('base64');
const { cameraObstaclesFromMap, cameraSafeFraction, nearPlaneRadius, smoothCameraFraction,
  resolveChaseCamera } = await import(sourceUrl);
const map = JSON.parse(await readFile(mapPath, 'utf8'));
const obstacles = cameraObstaclesFromMap(map);
assert.equal(obstacles.length, 16);

function close(actual, expected, tolerance = 1e-9) {
  assert.ok(Math.abs(actual - expected) <= tolerance, `expected ${expected}, got ${actual}`);
}
function between(a, b, t) {
  return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z: a.z + (b.z - a.z) * t };
}
function inside(point, obstacle, margin = 0) {
  return ['x', 'y', 'z'].every((axis) =>
    point[axis] >= obstacle.min[axis] - margin && point[axis] <= obstacle.max[axis] + margin
  );
}
function unit(vector) {
  const length = Math.hypot(...vector);
  return vector.map((value) => value / length);
}
function cross(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}
function dot(a, b) {
  return a.reduce((sum, value, index) => sum + value * b[index], 0);
}
function projectionFrame(camera, look) {
  const forward = unit([look.x - camera.x, look.y - camera.y, look.z - camera.z]);
  const right = unit(cross(forward, [0, 1, 0]));
  return { forward, right, up: cross(right, forward) };
}
function project(point, camera, frame, width, height, fov) {
  const relative = [point.x - camera.x, point.y - camera.y, point.z - camera.z];
  const depth = dot(relative, frame.forward);
  const focal = height / (2 * Math.tan(fov * Math.PI / 360));
  return { x: width / 2 + focal * dot(relative, frame.right) / depth,
    y: height / 2 - focal * dot(relative, frame.up) / depth, depth };
}

// The manifest's Y coordinate is a base, while X and Z describe the center.
assert.deepEqual(obstacles[4], { min: { x: -69, y: 0, z: -28 }, max: { x: -57, y: 8, z: -8 } });
assert.deepEqual(obstacles[8], { min: { x: -24, y: 0, z: -92 }, max: { x: -16, y: 8, z: -84 } });
const near = .12;
const fov = 48;
const aspect = 1.6;
const radius = nearPlaneRadius(near, fov, aspect);
const halfHeight = near * Math.tan(fov * Math.PI / 360);
const halfWidth = halfHeight * aspect;
close(radius, Math.hypot(near, halfHeight, halfWidth) + .03);
assert.ok(nearPlaneRadius(near, fov, 3.2) > radius);

// The recorded Sun match places the desired camera inside authority-solid-4.
const sunLook = { x: -59.85, y: .85, z: -5.199994 };
const sunDesired = { x: -58.65, y: 4.4, z: -13.799994 };
assert.ok(inside(sunDesired, obstacles[4]));
const sunSafe = cameraSafeFraction(sunLook, sunDesired, obstacles, radius);
assert.ok(sunSafe > 0 && sunSafe < 1);
close(sunSafe, (obstacles[4].max.z + radius - sunLook.z) / (sunDesired.z - sunLook.z));
assert.ok(inside(between(sunLook, sunDesired, sunSafe + 1e-5), obstacles[4], radius));
const sunInput = {
  look: sunLook, desired: sunDesired, feet: { x: -60, y: 0, z: -5.399994 },
  height: 2.1, obstacles, nearClip: near, aspect, previousFraction: 1, previousFov: fov, dt: .016
};
let iterations = 0;
const sun = resolveChaseCamera({ ...sunInput, onIteration(candidate) {
  iterations++;
  if (candidate.fraction > 0)
    close(cameraSafeFraction(candidate.anchor, candidate.position, obstacles, candidate.radius), 1, 1e-8);
} });
assert.ok(iterations >= 2, 'the wider FOV must trigger another clearance check');
assert.ok(sun.fov > fov && sun.fov <= 75);
assert.ok(sun.fullyFramed);
assert.ok(sun.safeFraction < 1 && sun.fraction <= sun.safeFraction);
assert.ok(sun.look.y > sunLook.y && sun.look.y - sunLook.y <= .2);
close(sun.safeDistance, Math.hypot(sunDesired.x - sun.look.x, sunDesired.y - sun.look.y,
  sunDesired.z - sun.look.z) * sun.safeFraction);
const sunCamera = sun.position;
assert.ok(!inside(sunCamera, obstacles[4]));

// Check the actual perspective near-plane corners and Hanuman's head and feet.
const frame = projectionFrame(sunCamera, sun.look);
const finalHalfHeight = near * Math.tan(sun.fov * Math.PI / 360);
const finalHalfWidth = finalHalfHeight * aspect;
for (const side of [-1, 1]) {
  for (const height of [-1, 1]) {
    const corner = {
      x: sunCamera.x + near * frame.forward[0] + side * finalHalfWidth * frame.right[0] + height * finalHalfHeight * frame.up[0],
      y: sunCamera.y + near * frame.forward[1] + side * finalHalfWidth * frame.right[1] + height * finalHalfHeight * frame.up[1],
      z: sunCamera.z + near * frame.forward[2] + side * finalHalfWidth * frame.right[2] + height * finalHalfHeight * frame.up[2]
    };
    assert.ok(obstacles.every((box) => !inside(corner, box)), 'near-plane corner entered a building');
  }
}
for (const y of [0, 2.1]) {
  const screen = project({ x: -60, y, z: -5.399994 }, sunCamera, frame, 1280, 800, sun.fov);
  assert.ok(screen.depth > near && screen.x >= 64 - 1e-5 && screen.x <= 1216 + 1e-5 &&
    screen.y >= 40 - 1e-5 && screen.y <= 760 + 1e-5);
}
const groundRayT = -sunCamera.y / frame.forward[1];
assert.ok(Number.isFinite(groundRayT) && groundRayT > 0);
assert.ok([sunCamera.x + frame.forward[0] * groundRayT, sunCamera.z + frame.forward[2] * groundRayT]
  .every(Number.isFinite));

// The mirrored Moon view approaches the neighboring northern side of solid 5.
const moonLook = { x: -60.15, y: .85, z: 9.4 };
const moonDesired = { x: -61.35, y: 4.4, z: 18 };
const moonSafe = cameraSafeFraction(moonLook, moonDesired, obstacles, radius);
assert.ok(moonSafe > 0 && moonSafe < 1);
close(moonSafe, (obstacles[5].min.z - radius - moonLook.z) / (moonDesired.z - moonLook.z));
assert.ok(!inside(between(moonLook, moonDesired, moonSafe), obstacles[5]));
const moon = resolveChaseCamera({ ...sunInput, look: moonLook, desired: moonDesired,
  feet: { x: -60, y: 0, z: 9.6 }, onIteration(candidate) {
    if (candidate.fraction > 0)
      close(cameraSafeFraction(candidate.anchor, candidate.position, obstacles, candidate.radius), 1, 1e-8);
  } });
assert.ok(moon.fraction < 1 && moon.fov <= 75 && moon.fullyFramed);
const moonFrame = projectionFrame(moon.position, moon.look);
for (const y of [0, 2.1]) {
  const screen = project({ x: -60, y, z: 9.6 }, moon.position, moonFrame, 1280, 800, moon.fov);
  assert.ok(screen.depth > near && screen.x >= 64 - 1e-5 && screen.x <= 1216 + 1e-5 &&
    screen.y >= 40 - 1e-5 && screen.y <= 760 + 1e-5);
}
// Native deck boxes participate in the same physical camera check.
assert.ok(cameraSafeFraction({ x: -19.85, y: .85, z: -79.8 },
  { x: -18.65, y: 4.4, z: -88.4 }, obstacles, radius) < 1);

// Unobstructed views retain the exact desired position. Height stays three-dimensional.
assert.equal(cameraSafeFraction({ x: 0, y: 1, z: 0 }, { x: 1, y: 5, z: -8 }, obstacles, radius), 1);
assert.equal(cameraSafeFraction({ x: -60, y: 9, z: -5 }, { x: -60, y: 9, z: -18 }, obstacles, radius), 1);
const still = { x: 0, y: 1, z: 0 };
assert.equal(cameraSafeFraction(still, still, obstacles, radius), 1);
const embedded = { x: -60, y: 1, z: -18 };
assert.equal(cameraSafeFraction(embedded, embedded, obstacles, radius), 0);
assert.equal(cameraSafeFraction(embedded, { x: -60, y: 1, z: -5 }, obstacles, radius), 0);
const insideView = resolveChaseCamera({ ...sunInput, look: embedded, desired: { x: -60, y: 1, z: -5 } });
assert.equal(insideView.fraction, 0);
assert.equal(insideView.fullyFramed, false);
assert.ok(Math.hypot(insideView.position.x - insideView.look.x,
  insideView.position.y - insideView.look.y, insideView.position.z - insideView.look.z) > 0);
const closeWall = cameraObstaclesFromMap({ authority_collision_boxes: [
  { anchor: 'base_center', position: [0, 0, -2], size: [4, 4, 3] }
], traversal: { native_collision_boxes: [] } });
const constrained = resolveChaseCamera({ ...sunInput, look: { x: 0, y: .85, z: .2 },
  desired: { x: 1.35, y: 4.4, z: -8.4 }, feet: { x: 0, y: 0, z: 0 }, obstacles: closeWall });
assert.ok(constrained.safeFraction > 0 && constrained.safeFraction < .1);
assert.equal(constrained.fov, 75);
assert.equal(constrained.fullyFramed, false);

// A tangent contact, a face-parallel near miss, and a first hit through two boxes.
const simple = cameraObstaclesFromMap({
  authority_collision_boxes: [{ anchor: 'base_center', position: [0, 0, 0], size: [2, 2, 2] }],
  traversal: { native_collision_boxes: [] }
});
close(cameraSafeFraction({ x: -2, y: 1, z: .5 }, { x: -.5, y: 1, z: 2 }, simple, .25), .5);
assert.equal(cameraSafeFraction({ x: 1.251, y: 1, z: -3 }, { x: 1.251, y: 1, z: 3 }, simple, .25), 1);
close(cameraSafeFraction({ x: 1.25, y: 1, z: -3 }, { x: 1.25, y: 1, z: 3 }, simple, .25), 1.75 / 6);
assert.equal(cameraSafeFraction(still, still, [], Infinity), 0);
assert.equal(nearPlaneRadius(near, fov, 0), Infinity);
assert.throws(() => cameraObstaclesFromMap({ authority_collision_boxes: [
  { anchor: 'base_center', position: [0, 0, 0], size: [-2, 2, 2] }
], traversal: { native_collision_boxes: [] } }));

// Smoothing cannot cross a closer obstacle, and grows monotonically after it clears.
close(smoothCameraFraction(1, .3, .016), .3);
close(smoothCameraFraction(.3, 1, .1), .48);
close(smoothCameraFraction(.3, .4, 1), .4);
close(smoothCameraFraction(.3, 1, 0), .3);
assert.equal(smoothCameraFraction(NaN, .4, .1), .4);
const openInput = { ...sunInput, look: { x: 0, y: .85, z: .2 }, desired: { x: 1.35, y: 4.4, z: -8.4 },
  feet: { x: 0, y: 0, z: 0 }, obstacles: [] };
const open = resolveChaseCamera(openInput);
assert.equal(open.fraction, 1);
assert.equal(open.fov, 48);
assert.deepEqual(open.position, openInput.desired);
assert.deepEqual(open.look, openInput.look);
const openHighActor = resolveChaseCamera({ ...openInput, feet: { x: 0, y: 12, z: 0 } });
assert.deepEqual(openHighActor.position, openInput.desired);
assert.equal(openHighActor.fov, 48);
assert.equal(openHighActor.fullyFramed, false);
const recovering = resolveChaseCamera({ ...openInput, previousFraction: .4, previousFov: 75, dt: .1 });
assert.ok(recovering.fraction > .4 && recovering.fraction < 1);
assert.ok(recovering.fov >= 48 && recovering.fov < 75);

// Sample the whole returned path against each expanded map box while moving
// around the actual map. Verify every intermediate FOV, not just the last one.
let randomState = 198427;
function random() {
  randomState = (Math.imul(randomState, 1664525) + 1013904223) >>> 0;
  return randomState / 2 ** 32;
}
for (let i = 0; i < 300; i++) {
  const x = random() * 134 - 67, z = random() * 250 - 125;
  const sign = i % 2 ? -1 : 1;
  const view = resolveChaseCamera({
    ...sunInput,
    look: { x: x + sign * .15, y: .85, z: z + sign * .2 },
    desired: { x: x + sign * 1.35, y: 4.4, z: z - sign * 8.4 },
    feet: { x, y: 0, z },
    aspect: .6 + random() * 2.5,
    previousFraction: random(),
    previousFov: 48 + random() * 27,
    dt: random() * .2,
    onIteration(candidate) {
      if (candidate.fraction === 0) return;
      close(cameraSafeFraction(candidate.anchor, candidate.position, obstacles, candidate.radius), 1, 1e-7);
      for (let step = 0; step <= 10; step++) {
        const p = between(candidate.anchor, candidate.position, step / 10 * .99999);
        assert.ok(obstacles.every((box) => !inside(p, box, candidate.radius)), 'path entered an expanded box');
      }
    }
  });
  assert.ok(view.fraction >= 0 && view.fraction <= view.safeFraction && view.safeFraction <= 1);
  assert.ok(view.fov >= 48 && view.fov <= 75);
}

console.log('Camera clearance passed both teams, perspective, tangencies and 300 sampled map views.');
