import { describe, expect, it } from 'vitest';
import { Simulation } from '../packages/sim/src/index.js';
import { parseClientMessage, type InputMessage } from '../packages/protocol/src/index.js';

const input = (seq: number, fields: Partial<InputMessage> = {}): InputMessage => ({ type: 'input', seq, moveX: 0, moveZ: 0, forward: 0, turn: 0, ...fields });
function driving(speed: number) {
  const sim = new Simulation('BRAKE-TEST', 'private', undefined, 'freeroam');
  const driver = sim.addPlayer('driver', 'Aadi'), car = sim.vehicles.get('compact-01')!;
  car.x = driver.x = 0; car.z = driver.z = 0;
  expect(sim.command(driver.id, { type: 'command', id: 'enter', action: 'enter', target: car.id }).ok).toBe(true);
  car.speed = speed;
  return { sim, driver, car };
}

describe('authoritative dedicated brake', () => {
  it('validates an optional boolean brake without accepting forged analog brake values', () => {
    expect(parseClientMessage(input(1))).not.toBeNull();
    expect(parseClientMessage(input(1, { brake: true }))).not.toBeNull();
    expect(parseClientMessage(input(1, { brake: false }))).not.toBeNull();
    for (const brake of [1, -1, 'true', null]) expect(parseClientMessage({ ...input(1), brake })).toBeNull();
    const { sim, driver } = driving(0);
    expect(sim.input(driver.id, { ...input(1), brake: 'true' } as unknown as InputMessage)).toBe(false);
    expect(driver.lastInputSeq).toBe(-1);
  });

  it.each([0.6, -0.6, 0])('stops speed %s without oscillation or reverse acceleration while a packet remains held', speed => {
    const { sim, driver, car } = driving(speed);
    expect(sim.input(driver.id, input(1, { forward: speed < 0 ? -1 : 1, brake: true }))).toBe(true);
    for (let tick = 0; tick < 12; tick++) { sim.step(); expect(car.speed).toBe(0); }
    expect(car.x).toBe(0); expect(car.z).toBe(0);
  });

  it.each([8, -6])('reduces speed %s monotonically while overriding throttle and allowing steering', speed => {
    const { sim, driver, car } = driving(speed);
    const heading = car.heading; let previous = Math.abs(speed);
    for (let tick = 0; tick < 12; tick++) {
      sim.input(driver.id, input(tick + 1, { forward: Math.sign(speed), turn: 1, brake: true })); sim.step();
      expect(Math.abs(car.speed)).toBeLessThanOrEqual(previous);
      expect(car.speed * speed).toBeGreaterThanOrEqual(0);
      previous = Math.abs(car.speed);
    }
    expect(car.speed).toBe(0); expect(car.heading).not.toBe(heading);
  });

  it('keeps delayed and repeated brake packets stopped, then permits deliberate forward or reverse after release', () => {
    const { sim, driver, car } = driving(0.6);
    sim.input(driver.id, input(1, { forward: -1, brake: true })); sim.step();
    for (let tick = 0; tick < 20; tick++) {
      sim.input(driver.id, input(tick + 2, { forward: tick % 2 ? -1 : 1, brake: true }));
      expect(sim.input(driver.id, input(1, { forward: -1, brake: true }))).toBe(false);
      sim.step(); expect(car.speed).toBe(0);
    }
    sim.input(driver.id, input(30, { forward: 1, brake: false })); sim.step(); expect(car.speed).toBeCloseTo(0.6);
    sim.input(driver.id, input(31, { forward: -1, brake: true })); sim.step(); expect(car.speed).toBe(0);
    sim.input(driver.id, input(32, { forward: -1, brake: false })); sim.step(); expect(car.speed).toBeCloseTo(-0.6);
  });
});
