import { makeEntry } from "./chatEntries.js";
import { threadLabelForKey, threadSectionForKey } from "./chatFormat.js";

export function appendThreadEntry(current, key, entry) {
  const existing = current[key] || {
    key,
    label: entry.threadLabel || threadLabelForKey(key),
    section: threadSectionForKey(key),
    items: [],
  };
  if (entry.messageId && existing.items.some((item) => item.messageId === entry.messageId)) {
    return current;
  }
  return {
    ...current,
    [key]: {
      ...existing,
      label: entry.threadLabel || existing.label,
      items: [...existing.items, makeEntry(entry)].slice(-250),
    },
  };
}

export function clearThreadItems(current, key, fallbackThread) {
  return {
    ...current,
    [key]: {
      ...(current[key] || fallbackThread),
      items: [],
    },
  };
}

export function removeUnjoinedRoomThreads(current, joinedRoomNames) {
  const next = { ...current };
  Object.keys(next).forEach((key) => {
    if (key.startsWith("room:") && !joinedRoomNames.has(key.slice(5))) {
      delete next[key];
    }
  });
  return next;
}

export function markMessageDeleted(current, messageId) {
  return mapThreadItems(current, (item) =>
    item.messageId === messageId
      ? { ...item, content: "This message was deleted by an admin", deleted: true, tone: "deleted" }
      : item,
  );
}

export function replaceMessageReactions(current, messageId, reactions) {
  return mapThreadItems(current, (item) => (item.messageId === messageId ? { ...item, reactions: reactions || [] } : item));
}

function mapThreadItems(current, mapItem) {
  const next = {};
  Object.entries(current).forEach(([key, thread]) => {
    next[key] = {
      ...thread,
      items: thread.items.map(mapItem),
    };
  });
  return next;
}
