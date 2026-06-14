export const reactionChoices = ["agree", "disagree", "like", "funny", "confused"];

export const reactableMessageTypes = new Set(["room_message", "private_message", "announcement"]);
export const deletableMessageTypes = new Set(["room_message", "announcement"]);

export const friendlyErrorMessages = {
  REJECTION_REASON_REQUIRED: "A rejection reason is required.",
  ROOM_REQUEST_ALREADY_REVIEWED: "This request has already been processed.",
  ROOM_REQUEST_ALREADY_PENDING: "You already have a pending request for this room.",
  ROOM_ALREADY_EXISTS: "That room already exists.",
  MESSAGE_NOT_FOUND: "Message not found.",
  MESSAGE_DELETED: "A deleted message cannot be reacted to.",
  INVALID_REACTION: "This reaction is not available.",
  PERMISSION_DENIED: "You don't have permission for this action.",
  MESSAGE_DELETE_NOT_ALLOWED: "Only chat messages can be deleted.",
  PRIVATE_MESSAGE_DELETE_DENIED: "Private messages cannot be deleted by an Admin.",
  USER_NOT_IN_ROOM: "That user is not in this room.",
  TARGET_OFFLINE: "The target is offline.",
  TARGET_NOT_FOUND: "Target user not found.",
  EMPTY_MESSAGE: "A message cannot be empty.",
  INVALID_TARGET: "Invalid target.",
  FILE_NAME_REQUIRED: "A file name is required.",
  INVALID_FILE_DATA: "The file could not be read.",
  FILE_TOO_LARGE: "Maximum file size is 5 MB.",
  REACTION_NOT_ALLOWED: "Notifications cannot be reacted to.",
  SESSION_EXPIRED: "Your session expired. Please sign in again.",
};

export function displayRoomName(roomName) {
  if (!roomName) return "";
  if (/^rt_room_\d+$/i.test(roomName)) return "room request";
  return `room ${roomName}`;
}

export function formatDisplayText(value) {
  return String(value || "")
    .replace(/\brt_room_\d+\b/gi, "room request")
    .replace(/\broom=([A-Za-z0-9_-]+)/g, (_, roomName) => `room=${displayRoomName(roomName)}`);
}

export function humanizeEventName(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatFileSize(size) {
  const bytes = Number(size) || 0;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function roomNameFor(room) {
  return room?.room_name || room?.name || "";
}

export function isRoomMember(room, username) {
  return Boolean(username && Array.isArray(room?.members) && room.members.includes(username));
}

export function threadLabelForKey(key) {
  if (key.startsWith("room:")) return displayRoomName(key.slice(5));
  if (key.startsWith("dm:")) return `@ ${key.slice(3)}`;
  return "Notifications";
}

export function threadSectionForKey(key) {
  if (key.startsWith("room:")) return "rooms";
  if (key.startsWith("dm:")) return "direct";
  return "notifications";
}

export function summarizeOutbound(type, payload = {}) {
  const room = payload.room_name ? ` ${displayRoomName(payload.room_name)}` : "";
  const target = payload.target_username ? ` target=${payload.target_username}` : "";
  const request = payload.request_id ? ` request_id=${payload.request_id}` : "";
  const username = payload.username ? ` user=${payload.username}` : "";

  switch (type) {
    case "login":
      return `login submitted${username}`;
    case "logout":
      return "logout submitted";
    case "register":
      return `registration submitted${username} role=${payload.role || "student"}`;
    case "send_room_message":
      return `room message submitted${room}`;
    case "send_private_message":
      return `private message submitted${target}`;
    case "send_announcement":
      return `announcement submitted${room}`;
    case "request_room":
      return `room request submitted${room}`;
    case "approve_room_request":
      return `room request approval submitted${request}`;
    case "reject_room_request":
      return `room request rejection submitted${request}`;
    case "kick_user":
      return `kick submitted${room}${target}`;
    case "server_logs":
      return "server logs requested";
    default:
      return `${type} submitted${room}${target}${request}`;
  }
}

export function summarizeResponse(message) {
  const payload = message.payload || {};
  const room = payload.room_name ? ` ${displayRoomName(payload.room_name)}` : "";
  const target = payload.target_username ? ` target=${payload.target_username}` : "";
  const request = payload.request_id ? ` request_id=${payload.request_id}` : "";
  const status = payload.status ? ` status=${payload.status}` : "";
  return `${message.message || message.type || "response"}${room}${target}${request}${status}`;
}
