/** Fixed20Hz game time. At most1s is caught up after a stall; longer pauses suspend excess game time. */
export class ArenaStepClock {
  private previous: number;
  private remainder = 0;
  constructor(now: number) { this.previous = now; }
  advance(now: number, step: (dt: number) => void): number {
    if (!Number.isFinite(now)) return 0;
    const elapsed = Math.max(0, now - this.previous); this.previous = now;
    this.remainder += Math.min(1000, elapsed);
    let steps = 0;
    while (this.remainder + 1e-7 >= 50 && steps < 20) { this.remainder -= 50; step(.05); steps++; }
    this.remainder = Math.max(0, this.remainder);
    return steps;
  }
}
