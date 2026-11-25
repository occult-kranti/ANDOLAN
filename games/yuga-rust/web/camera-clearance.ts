/** Camera obstruction tests for the base-centered boxes in the Confluence map. */
export type CameraPoint = { x: number; y: number; z: number };
type BoxSpec = { position: readonly number[]; size: readonly number[]; anchor: string };
type CameraMap = {
  authority_collision_boxes: readonly BoxSpec[];
  traversal: { native_collision_boxes: readonly BoxSpec[] };
};
export type CameraObstacle = { min: CameraPoint; max: CameraPoint };

/** Build once when the map loads. The Y coordinate in the map is the box base. */
export function cameraObstaclesFromMap(map: CameraMap): CameraObstacle[] {
  const specs = [...map.authority_collision_boxes, ...map.traversal.native_collision_boxes];
  return specs.map((box) => {
    const [x, y, z] = box.position;
    const [width, height, depth] = box.size;
    if (
      box.anchor !== 'base_center' ||
      ![x, y, z, width, height, depth].every(Number.isFinite) ||
      width <= 0 || height <= 0 || depth <= 0
    ) {
      throw new Error('Invalid camera obstruction in the Confluence map');
    }
    return {
      min: { x: x - width / 2, y, z: z - depth / 2 },
      max: { x: x + width / 2, y: y + height, z: z + depth / 2 }
    };
  });
}

/**
 * Radius containing the camera near plane at any orientation, plus 3 cm.
 * FOV is vertical and aspect is the actual viewport width divided by height.
 */
export function nearPlaneRadius(nearClip: number, verticalFovDegrees: number, aspect: number): number {
  if (
    !Number.isFinite(nearClip) || nearClip <= 0 ||
    !Number.isFinite(verticalFovDegrees) || verticalFovDegrees <= 0 || verticalFovDegrees >= 180 ||
    !Number.isFinite(aspect) || aspect <= 0
  ) return Infinity;
  const halfHeight = nearClip * Math.tan(verticalFovDegrees * Math.PI / 360);
  const halfWidth = halfHeight * aspect;
  return Math.hypot(nearClip, halfHeight, halfWidth) + 0.03;
}

/**
 * Largest clear prefix of the line from the look point to the desired camera.
 * A zero result means the look point lies inside an expanded obstruction.
 */
export function cameraSafeFraction(
  look: CameraPoint,
  desired: CameraPoint,
  obstacles: readonly CameraObstacle[],
  radius: number
): number {
  if (
    ![look.x, look.y, look.z, desired.x, desired.y, desired.z, radius].every(Number.isFinite) ||
    radius < 0
  ) return 0;
  let safe = 1;
  const axes = ['x', 'y', 'z'] as const;
  for (const box of obstacles) {
    let enter = 0;
    let exit = safe;
    let intersects = true;
    for (const axis of axes) {
      const start = look[axis];
      const direction = desired[axis] - start;
      const low = box.min[axis] - radius;
      const high = box.max[axis] + radius;
      if (direction === 0) {
        if (start < low || start > high) {
          intersects = false;
          break;
        }
        continue;
      }
      const first = (low - start) / direction;
      const last = (high - start) / direction;
      enter = Math.max(enter, Math.min(first, last));
      exit = Math.min(exit, Math.max(first, last));
      if (enter > exit) {
        intersects = false;
        break;
      }
    }
    if (intersects) safe = enter;
  }
  return safe;
}

/** Contract immediately; return towards the desired camera without exceeding the current bound. */
export function smoothCameraFraction(previous: number, safe: number, dt: number): number {
  const bound = Number.isFinite(safe) ? Math.max(0, Math.min(1, safe)) : 0;
  const current = Number.isFinite(previous) ? Math.max(0, Math.min(bound, previous)) : bound;
  const elapsed = Number.isFinite(dt) ? Math.max(0, dt) : 0;
  return Math.min(bound, current + elapsed * 1.8);
}

type ChaseCameraInput = {
  look: CameraPoint;
  desired: CameraPoint;
  feet: CameraPoint;
  height: number;
  obstacles: readonly CameraObstacle[];
  nearClip: number;
  aspect: number;
  previousFraction: number;
  previousFov: number;
  dt: number;
  /** Used by regression tests to inspect each lens and clearance candidate. */
  onIteration?: (candidate: {
    anchor: CameraPoint;
    position: CameraPoint;
    radius: number;
    fraction: number;
    fov: number;
  }) => void;
};

const BASE_FOV = 48;
const MAX_FOV = 75;
const FRAME_FRACTION = 0.9;

function cameraPosition(look: CameraPoint, desired: CameraPoint, fraction: number): CameraPoint {
  return {
    x: look.x + (desired.x - look.x) * fraction,
    y: look.y + (desired.y - look.y) * fraction,
    z: look.z + (desired.z - look.z) * fraction
  };
}

/** Minimum vertical FOV to keep the subject's feet and head within a 5% viewport margin. */
function subjectFov(
  position: CameraPoint, look: CameraPoint, feet: CameraPoint, height: number, aspect: number, nearClip: number
): number {
  const dx = look.x - position.x, dy = look.y - position.y, dz = look.z - position.z;
  const length = Math.hypot(dx, dy, dz);
  const horizontal = Math.hypot(dx, dz);
  if (!Number.isFinite(length) || length === 0 || horizontal === 0 || !Number.isFinite(aspect) ||
      aspect <= 0 || !Number.isFinite(height) || height <= 0) return Infinity;
  const fx = dx / length, fy = dy / length, fz = dz / length;
  const rx = -dz / horizontal, rz = dx / horizontal;
  const ux = -fx * fy * length / horizontal;
  const uy = horizontal / length;
  const uz = -fz * fy * length / horizontal;
  let extent = 0;
  for (const subjectY of [feet.y, feet.y + height]) {
    const x = feet.x - position.x, y = subjectY - position.y, z = feet.z - position.z;
    const depth = fx * x + fy * y + fz * z;
    if (!Number.isFinite(depth) || depth <= nearClip) return Infinity;
    const vertical = Math.abs(ux * x + uy * y + uz * z) / depth;
    const horizontalExtent = Math.abs(rx * x + rz * z) / (depth * aspect);
    extent = Math.max(extent, vertical, horizontalExtent);
  }
  return 2 * Math.atan(extent / FRAME_FRACTION) * 180 / Math.PI;
}

/**
 * Resolve the chase camera against the map, then fit the subject as the camera
 * approaches a wall. The FOV and its near-plane radius are solved together.
 */
export function resolveChaseCamera(input: ChaseCameraInput) {
  const { look, desired, feet, height, obstacles, nearClip, aspect, previousFraction,
    previousFov, dt, onIteration } = input;
  const elapsed = Number.isFinite(dt) ? Math.max(0, dt) : 0;
  const baseRadius = nearPlaneRadius(nearClip, BASE_FOV, aspect);
  const baseSafe = cameraSafeFraction(look, desired, obstacles, baseRadius);
  const anchor = { ...look, y: look.y + 0.2 * (1 - baseSafe) };
  const priorFov = Number.isFinite(previousFov) ? previousFov : BASE_FOV;
  let fov = Math.max(BASE_FOV, Math.min(MAX_FOV, priorFov - elapsed * 90));
  let position = anchor;
  let safeFraction = 0;
  let fraction = 0;
  let required = Infinity;
  let settled = false;
  for (let i = 0; i < 8; i++) {
    const radius = nearPlaneRadius(nearClip, fov, aspect);
    safeFraction = cameraSafeFraction(anchor, desired, obstacles, radius);
    fraction = smoothCameraFraction(previousFraction, safeFraction, elapsed);
    position = cameraPosition(anchor, desired, fraction);
    required = subjectFov(position, anchor, feet, height, aspect, nearClip);
    if (onIteration) onIteration({ anchor, position, radius, fraction, fov });
    const unobstructed = baseSafe === 1 && fraction === 1;
    const nextFov = unobstructed ? BASE_FOV : Math.min(MAX_FOV, Math.max(BASE_FOV, required));
    if (nextFov <= fov + 1e-6) {
      settled = true;
      break;
    }
    fov = nextFov;
  }
  if (!settled) {
    fov = MAX_FOV;
    const radius = nearPlaneRadius(nearClip, fov, aspect);
    safeFraction = cameraSafeFraction(anchor, desired, obstacles, radius);
    fraction = smoothCameraFraction(previousFraction, safeFraction, elapsed);
    position = cameraPosition(anchor, desired, fraction);
    required = subjectFov(position, anchor, feet, height, aspect, nearClip);
    if (onIteration) onIteration({ anchor, position, radius, fraction, fov });
  }
  // A zero-length lookAt has no orientation. Preserve the intended ray's
  // direction even when the anchor itself lies inside a blocker.
  let viewTarget = anchor;
  if (fraction === 0) {
    viewTarget = {
      x: 2 * anchor.x - desired.x,
      y: 2 * anchor.y - desired.y,
      z: 2 * anchor.z - desired.z
    };
    if (viewTarget.x === position.x && viewTarget.y === position.y && viewTarget.z === position.z)
      viewTarget = { ...position, z: position.z + 1 };
  }
  return {
    position, look: viewTarget, fov, fraction, safeFraction,
    safeDistance: Math.hypot(desired.x - anchor.x, desired.y - anchor.y, desired.z - anchor.z) * safeFraction,
    fullyFramed: required <= fov + 1e-6
  };
}
