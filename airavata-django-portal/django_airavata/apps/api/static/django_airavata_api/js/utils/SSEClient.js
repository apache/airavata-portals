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
      // Reconnect with exponential backoff
      setTimeout(() => this.connect(), this._retryDelay);
      this._retryDelay = Math.min(this._retryDelay * 2, this._maxRetryDelay);
    };
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
