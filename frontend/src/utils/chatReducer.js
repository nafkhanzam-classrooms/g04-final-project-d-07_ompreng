import { isRoomMember, roomNameFor } from "./chatFormat.js";

export function handleUserOnline(prev, newUser) {
  if (!newUser || !newUser.username) return prev;
  if (prev.some((u) => u.username === newUser.username)) return prev;
  return [...prev, newUser].sort((a, b) => a.username.localeCompare(b.username));
}

export function handleUserOffline(prev, offlineUsername) {
  if (!offlineUsername) return prev;
  return prev.filter((u) => u.username !== offlineUsername);
}

export function handleRoomList(nextRooms) {
  return nextRooms || [];
}

export function handleServerLogs(current, logs, makeLog) {
  const nextLogs = logs || [];
  return [
    ...nextLogs.map((log) =>
      makeLog(
        [log.username, log.description || log.message, log.timestamp]
          .filter(Boolean)
          .join(" / "),
        log.event_type || log.type || "log"
      )
    ),
    ...current,
  ].slice(0, 200);
}
