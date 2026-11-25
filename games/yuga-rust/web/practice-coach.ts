type Receipt = { unit: number; damage: number; heal: number; shield_after: number };
type CastEvent = {
  id: string;
  kind: string;
  origin: readonly number[];
  target: readonly number[];
  receipts: readonly Receipt[];
};

const techniques = [
  ['vajra_gada', 'Land a frontal gada strike'],
  ['vajra_kavacha', 'Shield an ally in front of you'],
  ['maruti_udayana', 'Vault to clear ground'],
  ['lanka_dahan', 'Catch a pursuer in your rear embers'],
  ['mountain_pulse', 'Heal an ally or hit a guard with Mountain Pulse'],
] as const;

/** Per-run feedback reads Rust results. Players can demonstrate techniques in any order. */
export class PracticeCoach {
  private readonly shown = new Set<string>();

  reset() {
    this.shown.clear();
  }

  observe(event: CastEvent) {
    if (this.shown.has(event.id)) return;
    const impact = event.kind === 'impact';
    let demonstrated = false;
    switch (event.id) {
      case 'vajra_gada':
        demonstrated = impact && event.receipts.some(r => r.damage > 0);
        break;
      case 'vajra_kavacha':
        demonstrated = impact && event.receipts.some(r => r.unit !== 0 && r.shield_after > 0);
        break;
      case 'maruti_udayana':
        demonstrated = event.kind === 'recovery' &&
          Math.hypot(event.origin[0] - event.target[0], event.origin[1] - event.target[1]) > 0.05;
        break;
      case 'lanka_dahan':
        demonstrated = (impact || event.kind === 'tick') && event.receipts.some(r => r.damage > 0);
        break;
      case 'mountain_pulse':
        demonstrated = impact && event.receipts.some(r => r.damage > 0 || (r.unit !== 0 && r.heal > 0));
        break;
    }
    if (demonstrated) this.shown.add(event.id);
  }

  get score() {
    return this.shown.size + '/' + techniques.length + ' techniques';
  }

  hint(keys: readonly string[]) {
    const next = techniques.findIndex(([id]) => !this.shown.has(id));
    return next < 0 ? this.score + ' demonstrated' : this.score + ' · ' + keys[next] + ' · ' + techniques[next][1];
  }
}
