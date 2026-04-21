/**
 * SSE SharedWorker — owns a single EventSource on behalf of every open
 * page in the tab group. Each page connects via MessagePort; the worker
 * fans out server events to all connected ports.
 *
 * Why: Django runserver speaks HTTP/1.1, which Chrome limits to 6
 * concurrent connections per origin. Under rapid navbar navigation the
 * prior page's EventSource hasn't finished tearing down by the time the
 * new page opens its own, so within 5-6 navigations all 6 slots are
 * occupied by stale SSE streams and the next page's initial request
 * queues behind them. Centralising the EventSource in a SharedWorker
 * keeps the connection count at exactly 1 regardless of how many pages
 * are open, leaving the rest of the browser's per-origin pool free for
 * actual HTML/CSS/API requests.
 */

const ENDPOINT = "/api/events/";
const HEARTBEAT_GRACE_MS = 45_000; // allow ~3 missed 15s server heartbeats

let source = null;
let ports = new Set();
let reconnectTimer = null;
let retryDelay = 1000;
const MAX_RETRY_DELAY = 30_000;
let lastEventAt = 0;
let watchdog = null;

function broadcast(msg) {
  for (const port of ports) {
    try {
      port.postMessage(msg);
    } catch (e) {
      // Port closed; drop it.
      ports.delete(port);
    }
  }
}

function ensureSource() {
  if (source) return;
  source = new EventSource(ENDPOINT);
  retryDelay = 1000;
  lastEventAt = Date.now();

  source.onopen = () => {
    lastEventAt = Date.now();
    broadcast({ kind: "status", connected: true });
  };
  source.onmessage = (e) => {
    lastEventAt = Date.now();
    try {
      const event = JSON.parse(e.data);
      broadcast({ kind: "event", event });
    } catch {
      // Ignore heartbeat comments and malformed lines.
    }
  };
  source.onerror = () => {
    broadcast({ kind: "status", connected: false });
    try { source.close(); } catch {}
    source = null;
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      if (ports.size > 0) ensureSource();
    }, retryDelay);
    retryDelay = Math.min(retryDelay * 2, MAX_RETRY_DELAY);
  };

  // Watchdog: if the connection hangs silently (no events, no heartbeat),
  // force a reconnect. Server sends "heartbeat" every 15s; if we haven't
  // seen anything for HEARTBEAT_GRACE_MS the socket is probably dead.
  if (watchdog) clearInterval(watchdog);
  watchdog = setInterval(() => {
    if (!source) return;
    if (Date.now() - lastEventAt > HEARTBEAT_GRACE_MS) {
      try { source.close(); } catch {}
      source = null;
      if (ports.size > 0) ensureSource();
    }
  }, 10_000);
}

function maybeClose() {
  if (ports.size > 0) return;
  if (source) {
    try { source.close(); } catch {}
    source = null;
  }
  if (watchdog) { clearInterval(watchdog); watchdog = null; }
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
}

// SharedWorker entrypoint.
self.onconnect = (e) => {
  const port = e.ports[0];
  ports.add(port);

  port.onmessage = (msg) => {
    if (!msg || !msg.data) return;
    switch (msg.data.type) {
      case "ensure":
        ensureSource();
        break;
      case "disconnect":
        ports.delete(port);
        try { port.close(); } catch {}
        maybeClose();
        break;
    }
  };
  // The Port activates when first postMessage or onmessage is set; trigger it.
  port.start();
  port.postMessage({ kind: "hello" });
};
