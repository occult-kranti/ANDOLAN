const REQUIRED_FRAMES = 2;
const VISIBLE_TIMEOUT_MS = 20_000;

/** Subscribe after instantiating the initial scene. These are engine postrenders,
 * not animation frames or a guarantee that every later effect shader is warm. */
export function waitForRenderedFrames(
  subscribe: (callback: () => void) => () => void,
  signal: AbortSignal,
  onFrame?: (count: number) => void,
): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    if (signal.aborted) { reject(signal.reason ?? new DOMException('Rendering canceled', 'AbortError')); return; }
    let settled = false, visible = !document.hidden, elapsed = 0, previous = performance.now(), frames = 0;
    let timer: number | undefined, unsubscribe: (() => void) | undefined;
    const account = () => {
      const now = performance.now();
      if (visible) elapsed += Math.max(0, now - previous);
      previous = now;
    };
    const cleanup = () => {
      if (timer !== undefined) { window.clearTimeout(timer); timer = undefined; }
      document.removeEventListener('visibilitychange', visibilityChanged);
      signal.removeEventListener('abort', aborted);
      const release = unsubscribe; unsubscribe = undefined; release?.();
    };
    const finish = (error?: unknown) => {
      if (settled) return; settled = true;
      try { cleanup(); } catch (cleanupError) { reject(error ?? cleanupError); return; }
      if (error !== undefined) reject(error); else resolve();
    };
    const expired = () => {
      if (elapsed < VISIBLE_TIMEOUT_MS) return false;
      finish(new Error('The arena did not render within 20 seconds. Return to the lobby and retry.'));
      return true;
    };
    const schedule = () => {
      if (timer !== undefined) { window.clearTimeout(timer); timer = undefined; }
      if (settled || !visible) return;
      timer = window.setTimeout(() => {
        timer = undefined; account();
        if (!expired()) schedule();
      }, Math.max(1, Math.ceil(VISIBLE_TIMEOUT_MS - elapsed)));
    };
    function aborted() { finish(signal.reason ?? new DOMException('Rendering canceled', 'AbortError')); }
    function visibilityChanged() {
      if (settled) return;
      account(); visible = !document.hidden;
      if (!expired()) schedule();
    }
    const rendered = () => {
      if (settled) return;
      account();
      if (expired() || !visible || document.hidden) return;
      frames++;
      try { onFrame?.(frames); } catch (error) { finish(error); return; }
      if (frames >= REQUIRED_FRAMES) finish();
    };
    signal.addEventListener('abort', aborted, { once: true });
    document.addEventListener('visibilitychange', visibilityChanged);
    try {
      const release = subscribe(rendered);
      // A subscriber may emit synchronously before returning its disposer.
      if (settled) release(); else unsubscribe = release;
    } catch (error) { finish(error); }
    schedule();
  });
}
