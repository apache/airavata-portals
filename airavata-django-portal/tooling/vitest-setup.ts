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
