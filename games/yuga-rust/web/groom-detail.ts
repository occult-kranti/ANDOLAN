/** Optional finishing mesh on the enhanced donor. The original silhouette is a separate surface. */
export const GROOM_MATERIAL = 'Hanuman | swept copper guard hair';

// Rest height from feet to the existing copper hair on the game's metre-scale rig.
const HANUMAN_HEIGHT = 2.1;
type Point3 = { x: number; y: number; z: number };

export function verticalFocalPixels(cssHeight: number, verticalFovDegrees: number): number {
  return cssHeight / (2 * Math.tan(verticalFovDegrees * Math.PI / 360));
}

/** Project both endpoints, preserving correct height for an offset or pitched perspective camera. */
export function projectedHanumanHeight(feet: Point3, eye: Point3, forward: Point3, up: Point3, focal: number): number {
  if (focal <= 0) return 0;
  const x = feet.x - eye.x, y = feet.y - eye.y, z = feet.z - eye.z;
  const feetDepth = x * forward.x + y * forward.y + z * forward.z;
  const headDepth = feetDepth + HANUMAN_HEIGHT * forward.y;
  if (feetDepth <= 0 && headDepth <= 0) return 0;
  if (feetDepth <= 0 || headDepth <= 0) return Infinity;
  const feetUp = x * up.x + y * up.y + z * up.z;
  const headUp = feetUp + HANUMAN_HEIGHT * up.y;
  return Math.abs(headUp / headDepth - feetUp / feetDepth) * focal;
}

export function groomVisible(wasVisible: boolean, projectedHeight: number): boolean {
  if (!Number.isFinite(projectedHeight)) return projectedHeight === Infinity || wasVisible;
  if (projectedHeight < 55) return false;
  if (projectedHeight > 70) return true;
  return wasVisible;
}
