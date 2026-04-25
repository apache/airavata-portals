// Stubs + polyfills shared by every workspace's Vitest suite.

// The `api` workspace's Session module reads `window.AiravataPortalSessionData`
// at import time; provide a benign default so test-file imports don't crash.
if (typeof window !== "undefined") {
  (window as unknown as { AiravataPortalSessionData?: object }).AiravataPortalSessionData ??= {
    authenticated: false,
  };
}

// Silence the `ResizeObserver is not defined` errors Vue 3 components can
// hit when mounted in jsdom.
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// Node 25 ships a built-in `localStorage` stub that lacks the full Storage API
// (e.g. `.clear()` is missing).  Replace it with a simple in-memory
// implementation so tests that rely on localStorage work correctly in jsdom.
(function installLocalStorage() {
  const store: Record<string, string> = {};
  const impl = {
    get length() { return Object.keys(store).length; },
    getItem(k: string) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
    setItem(k: string, v: string) { store[k] = String(v); },
    removeItem(k: string) { delete store[k]; },
    clear() { for (const k of Object.keys(store)) delete store[k]; },
    key(n: number) { return Object.keys(store)[n] ?? null; },
  };
  Object.defineProperty(globalThis, "localStorage", { value: impl, writable: true, configurable: true });
})();
