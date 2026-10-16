import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { waitForRenderedFrames } from '../client/render-warmup';

class Visibility extends EventTarget {
  hidden = false;
  setHidden(hidden: boolean) { this.hidden = hidden; this.dispatchEvent(new Event('visibilitychange')); }
}
let visibility: Visibility;
let render: () => void;
let release: Mock<() => void>;
let subscribe: Mock<(callback: () => void) => () => void>;
let abort: AbortController;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'performance'] });
  visibility = new Visibility(); abort = new AbortController(); release = vi.fn();
  subscribe = vi.fn((callback: () => void) => { render = callback; return release; });
  vi.stubGlobal('document', visibility);
  vi.stubGlobal('window', { setTimeout: globalThis.setTimeout, clearTimeout: globalThis.clearTimeout });
});
afterEach(() => { abort.abort(); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers(); });

describe('initial engine render gate', () => {
  it('needs two real callbacks and releases all listeners/timers after success', async () => {
    const remove = vi.spyOn(visibility, 'removeEventListener'), progress = vi.fn(), done = vi.fn();
    const result = waitForRenderedFrames(subscribe, abort.signal, progress).then(done);
    await vi.advanceTimersByTimeAsync(200); expect(done).not.toHaveBeenCalled();
    render(); await Promise.resolve(); expect(done).not.toHaveBeenCalled();
    render(); await result;
    expect(progress.mock.calls).toEqual([[1], [2]]);
    expect(release).toHaveBeenCalledTimes(1); expect(vi.getTimerCount()).toBe(0);
    expect(remove).toHaveBeenCalledWith('visibilitychange', expect.any(Function));
    render(); abort.abort(); expect(progress).toHaveBeenCalledTimes(2); expect(release).toHaveBeenCalledTimes(1);
  });

  it('does not count hidden renders or consume hidden time, then resumes the remaining budget', async () => {
    const progress = vi.fn();
    const result = waitForRenderedFrames(subscribe, abort.signal, progress);
    await vi.advanceTimersByTimeAsync(12_000); visibility.setHidden(true);
    expect(vi.getTimerCount()).toBe(0);
    render(); await vi.advanceTimersByTimeAsync(120_000); render();
    expect(progress).not.toHaveBeenCalled(); expect(release).not.toHaveBeenCalled();
    visibility.setHidden(false); await vi.advanceTimersByTimeAsync(7_999);
    render(); render(); await result; expect(progress.mock.calls).toEqual([[1], [2]]);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('fails closed on accumulated visible timeout and ignores late rendered frames', async () => {
    const progress = vi.fn(), remove = vi.spyOn(visibility, 'removeEventListener');
    const result = waitForRenderedFrames(subscribe, abort.signal, progress);
    const rejection = expect(result).rejects.toThrow('did not render within 20 seconds');
    await vi.advanceTimersByTimeAsync(10_000); render(); visibility.setHidden(true);
    await vi.advanceTimersByTimeAsync(60_000); visibility.setHidden(false);
    await vi.advanceTimersByTimeAsync(10_000); await rejection;
    expect(release).toHaveBeenCalledTimes(1); expect(vi.getTimerCount()).toBe(0);
    expect(remove).toHaveBeenCalledWith('visibilitychange', expect.any(Function));
    render(); expect(progress.mock.calls).toEqual([[1]]);
  });

  it('starts hidden without a timeout and cleans up an abort without waiting for visibility', async () => {
    visibility.hidden = true;
    const result = waitForRenderedFrames(subscribe, abort.signal);
    const rejection = expect(result).rejects.toMatchObject({ name: 'AbortError' });
    expect(vi.getTimerCount()).toBe(0); abort.abort(); await rejection;
    visibility.setHidden(false); render();
    expect(release).toHaveBeenCalledTimes(1); expect(vi.getTimerCount()).toBe(0);
  });

  it('never subscribes an already aborted request and preserves its cancellation reason', async () => {
    const reason = new Error('Superseded match'); abort.abort(reason);
    await expect(waitForRenderedFrames(subscribe, abort.signal)).rejects.toBe(reason);
    expect(subscribe).not.toHaveBeenCalled(); expect(vi.getTimerCount()).toBe(0);
  });

  it('handles synchronous subscriber completion and progress-triggered cancellation exactly once', async () => {
    const immediateRelease = vi.fn();
    await waitForRenderedFrames(callback => { callback(); callback(); return immediateRelease; }, abort.signal);
    expect(immediateRelease).toHaveBeenCalledTimes(1); expect(vi.getTimerCount()).toBe(0);
    const result = waitForRenderedFrames(subscribe, abort.signal, () => abort.abort());
    const rejection = expect(result).rejects.toMatchObject({ name: 'AbortError' });
    render(); await rejection; expect(release).toHaveBeenCalledTimes(1); expect(vi.getTimerCount()).toBe(0);
  });

  it('cleans up when render subscription or progress reporting throws', async () => {
    const remove = vi.spyOn(visibility, 'removeEventListener');
    await expect(waitForRenderedFrames(() => { throw new Error('Renderer destroyed'); }, abort.signal)).rejects.toThrow('Renderer destroyed');
    expect(remove).toHaveBeenCalledTimes(1); expect(vi.getTimerCount()).toBe(0);
    const result = waitForRenderedFrames(subscribe, abort.signal, () => { throw new Error('Progress failed'); });
    const rejection = expect(result).rejects.toThrow('Progress failed'); render(); await rejection;
    expect(release).toHaveBeenCalledTimes(1); expect(vi.getTimerCount()).toBe(0);
  });
});
