/**
 * SSE Client — singleton EventSource wrapper with typed event dispatch.
 *
 * Prefers a SharedWorker-backed EventSource so that every page in the tab
 * group shares a single upstream connection, instead of each page opening
 * its own. Falls back to a direct EventSource if SharedWorker is
 * unavailable (very old browsers, some embedded contexts).
 *
 * Usage:
 *   import SSEClient from "./utils/SSEClient";
 *   SSEClient.on("ssh_prompt", (event) => { ... });
 *   SSEClient.off("ssh_prompt", handler);
 *
 * `SSEClient.connect()` is kept as a no-op-safe entry point for legacy
 * callers; the stream is actually opened lazily the first time a
 * listener is registered.
 */

// Django AppDirectoriesFinder serves per-app static files at
// `/static/<app_label>/…` — the worker source sits under
// django_airavata/apps/api/static/django_airavata_api/js/utils/.
const WORKER_URL = "/static/django_airavata_api/js/utils/sseSharedWorker.js";

class _SSEClient {
  constructor() {
    this._listeners = {};
    this._connected = false;
    this._worker = null;
    this._workerPort = null;
    this._source = null; // fallback direct EventSource
    this._retryDelay = 1000;
    this._maxRetryDelay = 30000;
    this._opened = false;

    // Best-effort cleanup so the SharedWorker can close the upstream
    // connection when the last page unloads.
    if (typeof window !== "undefined") {
      window.addEventListener("pagehide", () => this._disconnectWorker());
    }
  }

  connect() {
    // Lazy: only open upstream when someone's actually listening. Rapid
    // navbar navigation otherwise piles up stale EventSources against the
    // browser's 6-concurrent-per-origin HTTP/1 connection limit.
    if (this._opened) return;
    if (!this._hasListeners()) return;
    this._opened = true;

    if (this._tryWorker()) return;
    this._tryDirect();
  }

  _tryWorker() {
    if (typeof SharedWorker === "undefined") return false;
    try {
      this._worker = new SharedWorker(WORKER_URL, { name: "airavata-sse" });
    } catch (e) {
      // Some sandboxed contexts throw; fall back to a direct EventSource.
      this._worker = null;
      return false;
    }
    this._workerPort = this._worker.port;
    this._workerPort.onmessage = (msg) => {
      const data = msg.data || {};
      if (data.kind === "event" && data.event) {
        this._dispatch(data.event.type, data.event);
      } else if (data.kind === "status") {
        this._connected = !!data.connected;
      }
    };
    this._workerPort.start();
    this._workerPort.postMessage({ type: "ensure" });
    this._connected = true;
    return true;
  }

  _tryDirect() {
    this._source = new EventSource("/api/events/");
    this._retryDelay = 1000;

    this._source.onopen = () => {
      this._connected = true;
      this._retryDelay = 1000;
    };

    this._source.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        this._dispatch(event.type, event);
      } catch (err) {
        // Ignore parse errors (e.g. heartbeat comments)
      }
    };

    this._source.onerror = () => {
      this._connected = false;
      try { this._source.close(); } catch {}
      this._source = null;
      setTimeout(() => {
        if (this._hasListeners()) this._tryDirect();
      }, this._retryDelay);
      this._retryDelay = Math.min(this._retryDelay * 2, this._maxRetryDelay);
    };
  }

  _disconnectWorker() {
    if (this._workerPort) {
      try { this._workerPort.postMessage({ type: "disconnect" }); } catch {}
      try { this._workerPort.close(); } catch {}
      this._workerPort = null;
    }
    this._worker = null;
  }

  disconnect() {
    this._opened = false;
    this._connected = false;
    this._disconnectWorker();
    if (this._source) {
      try { this._source.close(); } catch {}
      this._source = null;
    }
  }

  on(type, callback) {
    if (!this._listeners[type]) {
      this._listeners[type] = [];
    }
    this._listeners[type].push(callback);
    if (!this._opened) this.connect();
  }

  off(type, callback) {
    if (!this._listeners[type]) return;
    this._listeners[type] = this._listeners[type].filter((cb) => cb !== callback);
  }

  _hasListeners() {
    return Object.values(this._listeners).some((arr) => arr && arr.length > 0);
  }

  _dispatch(type, event) {
    const handlers = this._listeners[type];
    if (handlers) {
      handlers.forEach((cb) => {
        try {
          cb(event);
        } catch (err) {
          console.error(`SSE handler error for ${type}:`, err);
        }
      });
    }
  }

  get connected() {
    return this._connected;
  }
}

const SSEClient = new _SSEClient();
export default SSEClient;
