import { expect } from 'vitest';
import { CONTRACTS } from '../packages/content/src/contracts.js';
import type { CommandAction, CommandMessage } from '../packages/protocol/src/index.js';
import { Simulation, WORLD } from '../packages/sim/src/index.js';

let serial = 0;
export const command = (action: CommandAction, target?: string, value?: string): CommandMessage => ({ type: 'command', id: `city-fixture-${++serial}`, action, target, value });
export function walkAt(sim: Simulation, playerId: string, targetId: string): void {
  const player = sim.players.get(playerId)!;
  if (player.vehicleId) {
    sim.vehicles.get(player.vehicleId)!.speed = 0;
    expect(sim.command(playerId, command('exit')).ok).toBe(true);
  }
  const target = WORLD.landmarks.find(place => place.id === targetId)!;
  player.x = target.x; player.z = target.z;
}

/** Authoritative position fixtures exercise transactions; separate browser QA drives the physical routes. */
export function completeJob(sim: Simulation, playerId: string, jobId: string) {
  expect(sim.command(playerId, command('job_start', jobId)).code).toBe('JOB_STARTED');
  const job = CONTRACTS.find(definition => definition.id === jobId)!;
  let last: CommandMessage | null = null;
  for (let guard = 0; sim.contracts.active && guard < 30; guard++) {
    const active = sim.contracts.active, stage = job.stages[active.stageIndex]!;
    const player = sim.players.get(playerId)!;
    if (player.vehicleId) {
      sim.vehicles.get(player.vehicleId)!.speed = 0;
      expect(sim.command(playerId, command('exit')).ok).toBe(true);
    }
    const target = stage.targetVehicleId ? sim.vehicles.get(stage.targetVehicleId)! : WORLD.landmarks.find(place => place.id === stage.targetId)!;
    player.x = target.x; player.z = target.z;
    const vehicleId = active.vehicleId ?? (stage.vehicle === 'van' ? 'van-01' : 'compact-01');
    if ((stage.vehicle ?? 'none') !== 'none') {
      const vehicle = sim.vehicles.get(vehicleId)!;
      vehicle.x = target.x; vehicle.z = target.z; vehicle.speed = 0;
      expect(sim.command(playerId, command('enter', vehicleId)).ok).toBe(true);
    } else if (active.vehicleId && !stage.targetVehicleId) {
      const vehicle = sim.vehicles.get(active.vehicleId)!;
      vehicle.x = target.x; vehicle.z = target.z; vehicle.speed = 0;
    }
    while (sim.time - active.stageStartedAt < (stage.minimumSeconds ?? 0)) sim.step();
    if (stage.action === 'checkpoint') sim.step();
    else {
      last = command('job_interact', active.instanceId, active.stageId);
      expect(sim.command(playerId, last).ok).toBe(true);
    }
  }
  expect(sim.contracts.active).toBeNull();
  return last!;
}

export function completeCity(sim: Simulation, playerId: string): void {
  for (const job of CONTRACTS.filter(definition => definition.once)) completeJob(sim, playerId, job.id);
}
