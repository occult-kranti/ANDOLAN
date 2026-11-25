import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { build } from 'esbuild';

const entry = fileURLToPath(new URL('../web/groom-detail.ts', import.meta.url));
const { outputFiles } = await build({ entryPoints: [entry], bundle: true, format: 'esm', write: false });
const url = 'data:text/javascript;base64,' + Buffer.from(outputFiles[0].contents).toString('base64');
const { GROOM_MATERIAL, groomVisible, projectedHanumanHeight, verticalFocalPixels } = await import(url);

assert.equal(GROOM_MATERIAL, 'Hanuman | swept copper guard hair');
const heights = [72, 70, 60, 55, 54.99, 55, 65, 70, 70.01, 56];
let visible = true;
assert.deepEqual(heights.map(height => (visible = groomVisible(visible, height))),
  [true, true, true, true, false, false, false, false, true, true]);
assert.equal(groomVisible(false, Infinity), true);
assert.equal(groomVisible(true, NaN), true);
assert.equal(groomVisible(false, NaN), false);

const eye = { x: 0, y: 2, z: 0 };
const forward = { x: 0, y: 0, z: 1 };
const up = { x: 0, y: 1, z: 0 };
const heightAt = (x, z, h = 800, fov = 90) =>
  projectedHanumanHeight({ x, y: 0, z }, eye, forward, up, verticalFocalPixels(h, fov));
function close(actual, expected) {
  assert.ok(Math.abs(actual - expected) < 1e-8, `expected ${expected}, got ${actual}`);
}
// A level camera with an 800 CSS-pixel viewport and 90° vertical FOV has 400 px focal length.
close(heightAt(0, 10), 84);
close(heightAt(15, 10), 84); // lateral displacement alone leaves the projected height intact
close(heightAt(0, 20), 42);
close(heightAt(0, 10, 400), 42);
assert.ok(heightAt(0, 10, 800, 60) > heightAt(0, 10, 800, 90));
assert.equal(heightAt(0, -3), 0);
assert.equal(heightAt(0, 10, 0), 0);
// In a pitched camera the head and foot have different depths. Compare their normalized coordinates.
const pitched = { x: 0, y: -.5, z: Math.sqrt(.75) };
const tiltedUp = { x: 0, y: Math.sqrt(.75), z: .5 };
const height = projectedHanumanHeight({ x: 3, y: 0, z: 9 }, eye, pitched, tiltedUp, 400);
const footNdc = (-2 * Math.sqrt(.75) + 4.5) / (1 + 9 * Math.sqrt(.75));
const headNdc = (.1 * Math.sqrt(.75) + 4.5) / (-.05 + 9 * Math.sqrt(.75));
close(height, (headNdc - footNdc) * 400);
assert.equal(projectedHanumanHeight({ x: 0, y: 0, z: .01 }, eye, pitched, tiltedUp, 400), Infinity);

console.log('Hanuman guard-hair projection and 55/70 CSS-pixel hysteresis checks passed.');
