import { requestId } from "./chatEntries.js";

export class MbgTransport {
  constructor(callbacks = {}) {
    this.socket = null;
    this.reconnectTimeout = null;
    this.pendingResponses = new Map();
    this.pendingActionRequests = new Map();
    this.callbacks = {
      onConnectStatus: () => {},
      onMessage: () => {},
      onLog: () => {},
      onFeed: () => {},
      onActionPending: () => {},
      onActionNotice: () => {},
      ...callbacks,
    };
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);
    this.socket = socket;

    socket.addEventListener("open", () => {
      window.clearTimeout(this.reconnectTimeout);
      this.callbacks.onConnectStatus(true, "Connected");
      this.callbacks.onLog("Bridge connected", "Connection", "success");
      
      const stored = window.sessionStorage.getItem("mbg.session");
      if (stored) {
        try {
          const storedSession = JSON.parse(stored);
          if (storedSession?.session_token) {
            this.send("resume_session", { session_token: storedSession.session_token });
            this.callbacks.onLog("session resume submitted", "resume_session", "sent");
          }
        } catch {}
      }
    });

    socket.addEventListener("close", () => {
      this.callbacks.onConnectStatus(false, "Disconnected");
      this.callbacks.onLog("Bridge disconnected. Reconnecting...", "Connection", "error");
      this.reconnectTimeout = window.setTimeout(() => this.connect(), 1500);
    });

    socket.addEventListener("error", () => {
      this.callbacks.onConnectStatus(false, "Connection error");
    });

    socket.addEventListener("message", (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleIncomingMessage(message);
      } catch {
        this.callbacks.onFeed("Received invalid JSON from bridge", "error", "Invalid JSON");
      }
    });
  }

  handleIncomingMessage(message) {
    const pending = message.request_id ? this.pendingResponses.get(message.request_id) : null;
    const pendingActionType = message.request_id ? this.pendingActionRequests.get(message.request_id) : null;
    if (pendingActionType) {
      this.pendingActionRequests.delete(message.request_id);
      this.callbacks.onActionPending(pendingActionType, false);
    }
    if (pending) {
      window.clearTimeout(pending.timeout);
      this.pendingResponses.delete(message.request_id);
      if (message.success === false || message.type === "error") {
        pending.reject(new Error(message.message || "Request failed"));
      } else {
        pending.resolve(message);
      }
    }
    this.callbacks.onMessage(message);
  }

  send(type, payload = {}) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.callbacks.onFeed("Web UI is not connected to the bridge", "error", type);
      return false;
    }
    this.socket.send(JSON.stringify({ type, request_id: requestId(), payload }));
    return true;
  }

  sendWithResponse(type, payload = {}) {
    return new Promise((resolve, reject) => {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
        this.callbacks.onFeed("Web UI is not connected to the bridge", "error", type);
        reject(new Error("Web UI is not connected to the bridge"));
        return;
      }
      const id = requestId();
      const timeout = window.setTimeout(() => {
        this.pendingResponses.delete(id);
        this.pendingActionRequests.delete(id);
        this.callbacks.onActionPending(type, false);
        this.callbacks.onActionNotice(`${type} timed out`, "error", "Timeout");
        reject(new Error("Request timed out"));
      }, 30000);
      this.pendingResponses.set(id, { resolve, reject, timeout });
      if (type !== "ping" && type !== "logout" && type !== "online_users" && type !== "room_list" && type !== "feed_history") {
        this.callbacks.onActionPending(type, true);
        this.pendingActionRequests.set(id, type);
        this.callbacks.onActionNotice(`${type} submitted`, "system", "Waiting for response");
      }
      this.socket.send(JSON.stringify({ type, request_id: id, payload }));
    });
  }

  close() {
    window.clearTimeout(this.reconnectTimeout);
    this.pendingResponses.forEach((pending) => window.clearTimeout(pending.timeout));
    this.pendingResponses.clear();
    this.pendingActionRequests.clear();
    if (this.socket) {
      this.socket.close();
    }
  }
}
