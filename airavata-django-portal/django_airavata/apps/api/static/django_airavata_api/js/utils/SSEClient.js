/**
 * SSE Client — singleton EventSource wrapper with typed event dispatch.
 *
 * Usage:
 *   import SSEClient from "./utils/SSEClient";
 *   SSEClient.connect();
 *   SSEClient.on("ssh_prompt", (event) => { ... });
 *   SSEClient.off("ssh_prompt", handler);
 */

class _SSEClient {
  constructor() {
    this._listeners = {};
    this._source = null;
    this._retryDelay = 1000;
    this._maxRetryDelay = 30000;
    this._connected = false;
  }

  connect() {
    if (this._source) return;
    // Lazy connect: skip opening an EventSource on pages where nothing
    // listens for real-time events. Every open EventSource counts against
    // the browser's 6-concurrent-connections-per-origin HTTP/1 limit, and
    // under rapid navbar clicking the accumulating stale connections (the
    // previous page's EventSource doesn't always tear down in time) push
    // later navigations past the limit — the next request queues until one
    // frees up, which looks like the portal being "stuck".
    if (!this._hasListeners()) {
      return;
    }

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
      this._source.close();
      this._source = null;
      // Reconnect with exponential backoff, but only if someone's still
      // listening — avoids silent retry storms on pages that no longer need
      // the stream.
      setTimeout(() => {
        if (this._hasListeners()) this.connect();
      }, this._retryDelay);
      this._retryDelay = Math.min(this._retryDelay * 2, this._maxRetryDelay);
    };
  }

  _hasListeners() {
    return Object.values(this._listeners).some((arr) => arr && arr.length > 0);
  }

  disconnect() {
    if (this._source) {
      this._source.close();
      this._source = null;
      this._connected = false;
    }
  }

  on(type, callback) {
    if (!this._listeners[type]) {
      this._listeners[type] = [];
    }
    this._listeners[type].push(callback);
    // A late listener registration after connect() was already a no-op
    // should still open the stream now that someone's interested.
    if (!this._source) {
      this.connect();
    }
  }

  off(type, callback) {
    if (!this._listeners[type]) return;
    this._listeners[type] = this._listeners[type].filter((cb) => cb !== callback);
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
