/** Device inputs share actions; touch does not depend on a player's keyboard layout. */
export type Binding = 'forward' | 'back' | 'left' | 'right' | 'interact' | 'vehicle';
export const DEFAULT_BINDINGS: Record<Binding, string> = { forward: 'KeyW', back: 'KeyS', left: 'KeyA', right: 'KeyD', interact: 'KeyE', vehicle: 'KeyF' };
const reserved = new Set(['KeyJ', 'KeyH', 'KeyC', 'Escape', 'Space', 'Tab', 'Enter', 'ShiftLeft', 'ShiftRight', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']);
export function bindingProblem(code: string, bindings: Record<Binding, string>, action: Binding): string | null {
  if (reserved.has(code)) return 'That key is reserved for menus, camera, horn, brake or accessibility. Choose another letter or number.';
  if (!/^(Key[A-Z]|Digit[0-9])$/.test(code)) return 'Choose a letter or number key. Escape cancels.';
  const used = (Object.keys(bindings) as Binding[]).find(key => key !== action && bindings[key] === code);
  return used ? `That key already controls ${used}. Choose a different key.` : null;
}
export function restoreBindings(value: unknown): Record<Binding, string> {
  const result = { ...DEFAULT_BINDINGS };
  if (!value || typeof value !== 'object') return result;
  const saved = value as Record<string, unknown>;
  // Validate the complete mapping so valid key swaps survive reload.
  const candidate = Object.fromEntries((Object.keys(result) as Binding[]).map(key => [key, saved[key] ?? result[key]])) as Record<Binding, string>;
  if ((Object.keys(candidate) as Binding[]).every(key => typeof candidate[key] === 'string' && !bindingProblem(candidate[key], candidate, key))) return candidate;
  return result;
}
export function keyLabel(code: string) { return code.replace(/^Key|^Digit/, ''); }
export function actionHeld(action: Binding, bindings: Record<Binding, string>, keyboard: ReadonlySet<string>, touch: ReadonlySet<string>): boolean {
  return keyboard.has(bindings[action]) || touch.has(action);
}
/** Assistance limits acceleration, never stopping force. Dedicated braking is server-owned. */
export function driveThrottle(axis: number, speed: number, assistance: boolean): number {
  return assistance && axis * speed >= 0 ? axis * .55 : axis;
}
