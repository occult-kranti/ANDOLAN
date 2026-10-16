/** Cosmetic lighting only. The authoritative arena clock is the sole cycle input. */
export type LightingMode = 'cycle' | 'day' | 'night';
export type RGB = readonly [number, number, number];
export type DayPhase = 'Dawn' | 'Day' | 'Dusk' | 'Night' | 'Predawn';
export interface DayNightSample {
  cycleSeconds: number; phase: DayPhase; nightBlend: number;
  ambient: RGB; fog: RGB; sunColor: RGB; fillColor: RGB; skyTint: RGB;
  sunIntensity: number; fillIntensity: number; sunPitch: number; sunYaw: number;
}

export const DAY_NIGHT_SECONDS = 480;
interface Keyframe {
  time: number; night: number; ambient: RGB; fog: RGB; sun: RGB; sky: RGB; intensity: number; fill: number;
}
const DAWN: Keyframe = { time: 0, night: .12, ambient: [.46, .49, .56], fog: [.69, .65, .59], sun: [1, .79, .57], sky: [.97, .85, .75], intensity: 1.25, fill: .54 };
const FRAMES: readonly Keyframe[] = [
  DAWN,
  { time: 120, night: 0, ambient: [.47, .57, .61], fog: [.72, .75, .69], sun: [1, .91, .76], sky: [1, 1, 1], intensity: 1.55, fill: .48 },
  { time: 240, night: .48, ambient: [.38, .42, .53], fog: [.43, .38, .46], sun: [1, .59, .35], sky: [.81, .57, .58], intensity: 1.05, fill: .6 },
  { time: 320, night: 1, ambient: [.28, .36, .49], fog: [.12, .19, .29], sun: [.65, .77, 1], sky: [.12, .21, .37], intensity: .52, fill: .72 },
  { time: 400, night: .82, ambient: [.31, .37, .49], fog: [.24, .26, .38], sun: [.86, .76, .91], sky: [.36, .32, .48], intensity: .66, fill: .66 },
  { ...DAWN, time: DAY_NIGHT_SECONDS },
];
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const color = (a: RGB, b: RGB, t: number): RGB => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];

/** Fixed modes never change gameplay or the saved match clock. Invalid/negative time starts at dawn. */
export function sampleDayNight(time: number, mode: LightingMode = 'cycle'): DayNightSample {
  const cycleSeconds = mode === 'day' ? 120 : mode === 'night' ? 320 : (Number.isFinite(time) && time >= 0 ? time : 0) % DAY_NIGHT_SECONDS;
  let index = 0;
  while (index < FRAMES.length - 2 && cycleSeconds >= FRAMES[index + 1]!.time) index++;
  const a = FRAMES[index]!, b = FRAMES[index + 1]!;
  const linear = (cycleSeconds - a.time) / (b.time - a.time), t = linear * linear * (3 - 2 * linear);
  const phase: DayPhase = cycleSeconds < 70 ? 'Dawn' : cycleSeconds < 200 ? 'Day' : cycleSeconds < 280 ? 'Dusk' : cycleSeconds < 380 ? 'Night' : 'Predawn';
  const orbit = cycleSeconds / DAY_NIGHT_SECONDS * Math.PI * 2;
  return {
    cycleSeconds, phase, nightBlend: lerp(a.night, b.night, t), ambient: color(a.ambient, b.ambient, t), fog: color(a.fog, b.fog, t),
    sunColor: color(a.sun, b.sun, t), fillColor: [.56, .72, .94], skyTint: color(a.sky, b.sky, t),
    sunIntensity: lerp(a.intensity, b.intensity, t), fillIntensity: lerp(a.fill, b.fill, t),
    // Periodic angles avoid a discontinuous shadow jump when a replay reaches the clock seam.
    sunPitch: 48 + Math.sin(orbit) * 12, sunYaw: -36 + Math.sin(orbit - .4) * 28,
  };
}
