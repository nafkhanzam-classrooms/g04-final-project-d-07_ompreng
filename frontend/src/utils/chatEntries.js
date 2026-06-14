import { humanizeEventName } from "./chatFormat.js";

export const initialThreads = {
  notifications: {
    key: "notifications",
    label: "Notifications",
    section: "notifications",
    items: [],
  },
};

export function requestId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function makeLog(content, meta = "", tone = "normal") {
  return { id: requestId(), content, meta: humanizeEventName(meta), tone };
}

export function makeEntry(entry) {
  return { id: requestId(), ...entry };
}
