import { describe, expect, it } from 'vitest';
import { DAY_NIGHT_SECONDS, sampleDayNight, type DayNightSample } from '../client/environment-cycle.js';

const colorFields = ['ambient', 'fog', 'sunColor', 'fillColor', 'skyTint'] as const;
const lightValues = (sample: DayNightSample) => [sample.nightBlend, sample.sunIntensity, sample.fillIntensity, sample.sunPitch, sample.sunYaw, ...colorFields.flatMap(field => [...sample[field]])];
const luminance = (rgb: readonly number[]) => rgb[0]! * .2126 + rgb[1]! * .7152 + rgb[2]! * .0722;

describe('cosmetic authoritative-clock day/night cycle', () => {
  it('completes one cycle per480 game seconds and repeats at the seam without drifting', () => {
    expect(DAY_NIGHT_SECONDS).toBe(480);
    for (const time of [0, .25, 70, 120, 200, 240, 280, 320, 380, 400, 479.75]) {
      const sample = sampleDayNight(time);
      expect(sampleDayNight(time + 480)).toEqual(sample);
      expect(sampleDayNight(time + 480 * 1000)).toEqual(sample);
    }
    expect(sampleDayNight(480)).toEqual(sampleDayNight(0));
    expect(sampleDayNight(480).phase).toBe('Dawn');
  });

  it('holds fixed day or night independently of elapsed match time, pause or late join', () => {
    const day = sampleDayNight(120), night = sampleDayNight(320);
    expect(day.phase).toBe('Day'); expect(night.phase).toBe('Night');
    expect(day.nightBlend).toBe(0); expect(night.nightBlend).toBe(1);
    for (const time of [0, 319.5, 480, 99999, NaN, Infinity, -42]) {
      expect(sampleDayNight(time, 'day')).toEqual(day);
      expect(sampleDayNight(time, 'night')).toEqual(night);
    }
  });

  it('normalizes non-finite and negative time safely and keeps very large clocks finite', () => {
    for (const time of [NaN, Infinity, -Infinity, -1, -Number.MAX_VALUE]) expect(sampleDayNight(time)).toEqual(sampleDayNight(0));
    const huge = sampleDayNight(Number.MAX_VALUE);
    expect(huge.cycleSeconds).toBeGreaterThanOrEqual(0); expect(huge.cycleSeconds).toBeLessThan(480);
    expect(lightValues(huge).every(Number.isFinite)).toBe(true);
  });

  it('preserves explicit night readability floors and bounded colors through the entire cycle', () => {
    const phases = new Set<string>();
    for (let tick = 0; tick <= 4800; tick++) {
      const sample = sampleDayNight(tick / 10); phases.add(sample.phase);
      expect(lightValues(sample).every(Number.isFinite)).toBe(true);
      for (const field of colorFields) for (const channel of sample[field]) { expect(channel).toBeGreaterThanOrEqual(0); expect(channel).toBeLessThanOrEqual(1); }
      for (const channel of sample.ambient) expect(channel).toBeGreaterThanOrEqual(.28 - 1e-12);
      expect(sample.fillIntensity).toBeGreaterThanOrEqual(.48 - 1e-12);
      expect(sample.sunIntensity).toBeGreaterThanOrEqual(.52 - 1e-12); expect(sample.sunIntensity).toBeLessThanOrEqual(1.55 + 1e-12);
      expect(sample.nightBlend).toBeGreaterThanOrEqual(0); expect(sample.nightBlend).toBeLessThanOrEqual(1);
      expect(sample.sunPitch).toBeGreaterThanOrEqual(36); expect(sample.sunPitch).toBeLessThanOrEqual(60);
    }
    expect(phases).toEqual(new Set(['Dawn', 'Day', 'Dusk', 'Night', 'Predawn']));
  });

  it('changes visual values continuously at palette knots, phase labels and the cycle seam', () => {
    // Phase text may change at a boundary, but lights, fog, sky and shadows must not jump.
    for (const boundary of [70, 120, 200, 240, 280, 320, 380, 400, 480]) {
      const before = lightValues(sampleDayNight(boundary - .001)), after = lightValues(sampleDayNight(boundary + .001));
      before.forEach((value, index) => expect(Math.abs(after[index]! - value)).toBeLessThan(.001));
    }
  });

  it('eases palette transitions at each keyframe rather than abruptly changing brightness slope', () => {
    for (const boundary of [120, 240, 320, 400, 480]) {
      const centre = sampleDayNight(boundary), before = sampleDayNight(boundary - .01), after = sampleDayNight(boundary + .01);
      for (const field of ['nightBlend', 'sunIntensity', 'fillIntensity'] as const) {
        expect(Math.abs(centre[field] - before[field]) / .01).toBeLessThan(.0001);
        expect(Math.abs(after[field] - centre[field]) / .01).toBeLessThan(.0001);
      }
    }
  });

  it('distinguishes night from day while preserving a stronger night fill for readable silhouettes', () => {
    const day = sampleDayNight(120), night = sampleDayNight(320);
    expect(luminance(night.skyTint)).toBeLessThan(luminance(day.skyTint) * .4);
    expect(luminance(night.fog)).toBeLessThan(luminance(day.fog));
    expect(luminance(night.ambient)).toBeLessThan(luminance(day.ambient));
    expect(night.sunIntensity).toBeLessThan(day.sunIntensity); expect(night.fillIntensity).toBeGreaterThan(day.fillIntensity);
  });

  it('depends only on the supplied time and returns colors detached from the private palette', () => {
    const initial = sampleDayNight(320), expected = structuredClone(initial);
    Object.assign(initial.ambient, { 0: 99 }); Object.assign(initial.skyTint, { 1: 99 });
    sampleDayNight(3); sampleDayNight(479.9); sampleDayNight(120, 'day');
    expect(sampleDayNight(320)).toEqual(expected);
    expect(sampleDayNight(320)).toEqual(sampleDayNight(320));
  });
});
