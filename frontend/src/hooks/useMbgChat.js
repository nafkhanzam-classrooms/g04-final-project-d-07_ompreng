import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  deletableMessageTypes,
  displayRoomName,
  friendlyErrorMessages,
  humanizeEventName,
  isRoomMember,
  reactableMessageTypes,
  roomNameFor,
  summarizeOutbound,
  summarizeResponse,
  threadLabelForKey,
  threadSectionForKey,
} from "../utils/chatFormat.js";
import { initialThreads, makeLog, requestId } from "../utils/chatEntries.js";
import {
  appendThreadEntry,
  clearThreadItems,
  markMessageDeleted,
  removeUnjoinedRoomThreads,
  replaceMessageReactions,
} from "../utils/chatThreadState.js";
import { uploadPreparedAttachment } from "../utils/attachments.js";
import { readStoredSession, writeStoredSession, clearStoredSession } from "../utils/sessionPersistence.js";
import { MbgTransport } from "../utils/mbgTransport.js";
import { handleUserOnline, handleUserOffline, handleRoomList, handleServerLogs } from "../utils/chatReducer.js";


const skipToastTypes = new Set([
  "pong",
  "online_users_response",
  "room_list_response",
  "chat_history_response",
  "private_history_response",
  "feed_history_response",
  "server_logs_response",
  "send_room_message_response",
  "send_private_message_response",
  "send_file_message_response",
  "toggle_reaction_response",
  "prepare_file_upload_response",
]);

const silentResponseTypes = new Set([
  "pong",
  "approve_room_request_response",
  "create_room_response",
  "delete_message_response",
  "delete_room_response",
  "join_room_response",
  "kick_user_response",
  "leave_room_response",
  "prepare_file_upload_response",
  "reject_room_request_response",
  "request_room_response",
  "send_announcement_response",
  "send_file_message_response",
  "send_global_announcement_response",
  "send_private_message_response",
  "send_room_message_response",
]);

const actionRequestTypes = new Set([
  "approve_room_request",
  "create_room",
  "delete_room",
  "join_room",
  "kick_user",
  "leave_room",
  "reject_room_request",
  "request_room",
  "send_announcement",
  "send_global_announcement",
]);

export function useMbgChat() {
  const reconnectRef = useRef(null);
  const sessionRef = useRef(null);
  const roomsRef = useRef([]);
  const activeThreadRef = useRef("notifications");
  const loadedHistoryRef = useRef(new Set());
  const notifiedResponseTextsRef = useRef(new Set());

  const [connected, setConnected] = useState(false);
  const [statusText, setStatusText] = useState("Disconnected");
  const [lastRequest, setLastRequest] = useState("Login required");
  const [session, setSessionState] = useState(null);
  const [authMode, setAuthModeState] = useState("login");
  const [authNotice, setAuthNotice] = useState("");
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [serverLogs, setServerLogs] = useState([]);
  const [actionNotice, setActionNotice] = useState(null);
  const [pendingActions, setPendingActions] = useState({});
  const [requestedRoomNames, setRequestedRoomNames] = useState(new Set());
  const [threads, setThreads] = useState(initialThreads);
  const [activeThreadKey, setActiveThreadKey] = useState("notifications");
  const [selectedRoom, setSelectedRoom] = useState("");
  const [pendingRejectRequest, setPendingRejectRequest] = useState(null);

  const setSession = useCallback((user) => {
    sessionRef.current = user;
    setSessionState(user);
    if (!user) setLastRequest("Login required");
  }, []);

  const addLog = useCallback((content, meta = "", tone = "normal") => {
    setServerLogs((current) => [makeLog(content, meta, tone), ...current].slice(0, 200));
  }, []);

  const addThreadEntry = useCallback((key, entry) => {
    setThreads((current) => appendThreadEntry(current, key, entry));
  }, []);

  const appendFeed = useCallback(
    (content, tone = "normal", meta = "") => {
      addThreadEntry(activeThreadRef.current, { content, tone, meta });
    },
    [addThreadEntry],
  );

  const setActionPending = useCallback((type, pending) => {
    if (!actionRequestTypes.has(type)) return;
    setPendingActions((current) => {
      if (pending) return { ...current, [type]: (current[type] || 0) + 1 };
      const nextCount = Math.max((current[type] || 0) - 1, 0);
      if (nextCount) return { ...current, [type]: nextCount };
      const { [type]: _removed, ...rest } = current;
      return rest;
    });
  }, []);

  const publishActionNotice = useCallback((message, tone = "success", meta = "") => {
    setActionNotice({
      id: requestId(),
      content: message || "Action completed",
      tone,
      meta,
    });
  }, []);

  const dismissActionNotice = useCallback(() => {
    setActionNotice(null);
  }, []);

  useEffect(() => {
    if (!actionNotice) return undefined;
    const timeout = window.setTimeout(() => {
      setActionNotice((current) => (current?.id === actionNotice.id ? null : current));
    }, 4000);
    return () => window.clearTimeout(timeout);
  }, [actionNotice]);

  const addNotificationOnce = useCallback(
    (content, tone = "system", meta = "") => {
      const key = `${content} / ${meta}`;
      if (notifiedResponseTextsRef.current.has(key)) return;
      notifiedResponseTextsRef.current.add(key);
      addThreadEntry("notifications", { content, tone, meta });
    },
    [addThreadEntry],
  );

  const ensureThread = useCallback((key, label = threadLabelForKey(key), section = threadSectionForKey(key)) => {
    setThreads((current) => {
      if (current[key]) return current;
      return { ...current, [key]: { key, label, section, items: [] } };
    });
  }, []);

  const selectThread = useCallback((key) => {
    const nextKey = key || "notifications";
    activeThreadRef.current = nextKey;
    setActiveThreadKey(nextKey);
    if (nextKey.startsWith("room:")) {
      setSelectedRoom(nextKey.slice(5));
    }
  }, []);

  const canUseRoomThread = useCallback((roomName) => {
    const room = roomsRef.current.find((item) => roomNameFor(item) === roomName);
    return isRoomMember(room, sessionRef.current?.username);
  }, []);

  const routeThreadMessage = useCallback(
    (message, tone = "normal") => {
      const payload = message.payload || {};
      let key = "notifications";
      let label = "Notifications";

      if (message.type === "private_message") {
        const otherUser = payload.sender === sessionRef.current?.username ? payload.receiver : payload.sender;
        key = `dm:${otherUser || "unknown"}`;
        label = `@ ${otherUser || "unknown"}`;
      } else if (payload.room_name && ["room_message", "announcement", "system_message", "user_kicked"].includes(message.type)) {
        if (canUseRoomThread(payload.room_name)) {
          key = `room:${payload.room_name}`;
          label = displayRoomName(payload.room_name);
        }
      }

      const isDeleted = Boolean(payload.deleted);
      addThreadEntry(key, {
        content: isDeleted ? "This message was deleted by an admin" : payload.content || payload.message || message.message || "",
        tone: isDeleted ? "deleted" : tone,
        meta: [displayRoomName(payload.room_name), payload.sender, payload.timestamp].filter(Boolean).join(" / ") || humanizeEventName(message.type),
        messageId: payload.message_id,
        reactions: payload.reactions || [],
        attachment: payload.attachment || null,
        deleted: isDeleted,
        canDelete: deletableMessageTypes.has(message.type),
        canReact: reactableMessageTypes.has(message.type),
        threadLabel: label,
      });
    },
    [addThreadEntry, canUseRoomThread],
  );

  const renderBootstrap = useCallback(
    (bootstrap) => {
      if (Array.isArray(bootstrap.users)) setOnlineUsers(bootstrap.users);
      if (Array.isArray(bootstrap.rooms)) {
        roomsRef.current = bootstrap.rooms;
        setRooms(bootstrap.rooms);
      }
      if (Array.isArray(bootstrap.pending_requests)) setPendingRequests(bootstrap.pending_requests);
      if (Array.isArray(bootstrap.server_logs)) {
        setServerLogs(bootstrap.server_logs.map((log) => makeLog([log.username, log.description || log.message, log.timestamp].filter(Boolean).join(" / "), log.event_type || log.type || "log")));
      }
      if (Array.isArray(bootstrap.feed_messages)) {
        bootstrap.feed_messages.forEach((item) => {
          routeThreadMessage({ type: item.message_type || item.type || "system_message", payload: item }, "system");
        });
      }
    },
    [routeThreadMessage],
  );

  const handleMessage = useCallback(
    (message) => {
      if (message.success === false || message.type === "error") {
        const code = message.payload?.code || "Error";
        const friendly = friendlyErrorMessages[code] || message.message || "Request failed";
        publishActionNotice(friendly, "error", code);
        if (code === "SESSION_EXPIRED") clearStoredSession();
        if (!sessionRef.current) {
          setAuthNotice(friendly);
          addThreadEntry("notifications", { content: friendly, tone: "error", meta: code });
        } else {
          appendFeed(friendly, "error", code);
        }
        addLog(friendly, message.type || "error", "error");
        return;
      }

      if (message.request_id && message.message && !skipToastTypes.has(message.type)) {
        publishActionNotice(message.message, "success", humanizeEventName(message.type));
      }

      switch (message.type) {
        case "login_response":
        case "resume_session_response": {
          const user = message.payload || {};
          setAuthNotice("");
          writeStoredSession(user);
          setSession(user);
          renderBootstrap(user.bootstrap || {});
          addThreadEntry("notifications", { content: message.message || "Login successful", tone: "success", meta: `${user.username || "user"} / ${user.role || "role"}` });
          selectThread("notifications");
          break;
        }
        case "logout_response": {
          const username = message.payload?.username || sessionRef.current?.username || "user";
          clearStoredSession();
          setSession(null);
          addThreadEntry("notifications", { content: message.message || "Logout successful", tone: "success", meta: username });
          selectThread("notifications");
          break;
        }
        case "online_users_response":
        case "online_users_updated":
          setOnlineUsers(handleRoomList(message.payload?.users));
          break;
        case "user_online": {
          const newUser = message.payload;
          setOnlineUsers((prev) => handleUserOnline(prev, newUser));
          break;
        }
        case "user_offline": {
          const offlineUsername = message.payload?.username;
          setOnlineUsers((prev) => handleUserOffline(prev, offlineUsername));
          break;
        }
        case "room_list_response":
        case "room_list_updated": {
          const nextRooms = handleRoomList(message.payload?.rooms);
          roomsRef.current = nextRooms;
          setRooms(nextRooms);
          const joinedNames = new Set(nextRooms.filter((room) => isRoomMember(room, sessionRef.current?.username)).map(roomNameFor));
          setThreads((current) => removeUnjoinedRoomThreads(current, joinedNames));
          if (activeThreadRef.current.startsWith("room:") && !joinedNames.has(activeThreadRef.current.slice(5))) selectThread("notifications");
          break;
        }
        case "pending_room_requests_response":
        case "pending_room_requests_updated":
          setPendingRequests(message.payload?.requests || message.payload?.room_requests || []);
          break;
        case "request_room_response": {
          const roomName = roomNameFor(message.payload || {});
          if (roomName) {
            setRequestedRoomNames((current) => new Set([...current, roomName.toLowerCase()]));
          }
          addNotificationOnce(message.message || "Room request submitted", "success", message.type);
          break;
        }
        case "server_logs_response":
        case "server_logs_updated": {
          const logs = message.payload?.logs || message.payload?.server_logs || [];
          setServerLogs((current) => handleServerLogs(current, logs, makeLog));
          break;
        }
        case "chat_history_response":
        case "feed_history_response":
          (message.payload?.messages || []).forEach((item) => routeThreadMessage({ type: item.message_type || item.type || "room_message", payload: item }));
          break;
        case "private_history_response":
          (message.payload?.messages || []).forEach((item) => routeThreadMessage({ type: item.message_type || item.type || "private_message", payload: item }, "private"));
          break;
        case "room_message":
          routeThreadMessage(message, "normal");
          break;
        case "private_message":
          routeThreadMessage(message, "private");
          break;
        case "announcement":
          routeThreadMessage(message, "announcement");
          break;
        case "system_message":
        case "user_joined_room":
        case "user_left_room":
        case "user_kicked":
        case "room_created":
        case "room_deleted":
        case "room_request_submitted":
        case "room_request_approved":
        case "room_request_rejected":
        case "global_announcement":
          routeThreadMessage(message, "system");
          break;
        case "message_deleted": {
          const payload = message.payload || {};
          setThreads((current) => markMessageDeleted(current, payload.message_id));
          break;
        }
        case "message_reactions_updated": {
          const payload = message.payload || {};
          setThreads((current) => replaceMessageReactions(current, payload.message_id, payload.reactions));
          break;
        }
        case "toggle_reaction_response":
          addNotificationOnce(message.message || "Reaction updated", "system", message.type);
          break;
        case "register_response":
          addNotificationOnce(message.message || "Registration successful", "success", message.type);
          break;
        default:
          if (silentResponseTypes.has(message.type)) {
            addLog(summarizeResponse(message), message.type, "normal");
            break;
          }
          appendFeed(message.message || JSON.stringify(message), "system", message.type || "Response");
          addLog(summarizeResponse(message), message.type || "Response", "normal");
      }
    },
    [addLog, addNotificationOnce, addThreadEntry, appendFeed, publishActionNotice, renderBootstrap, routeThreadMessage, selectThread, setSession],
  );

  const transport = useMemo(() => {
    return new MbgTransport();
  }, []);

  useEffect(() => {
    transport.callbacks = {
      onConnectStatus: (conn, text) => {
        setConnected(conn);
        setStatusText(text);
      },
      onLog: addLog,
      onFeed: appendFeed,
      onActionPending: setActionPending,
      onActionNotice: publishActionNotice,
      onMessage: handleMessage,
    };
  }, [transport, addLog, appendFeed, setActionPending, publishActionNotice, handleMessage]);

  useEffect(() => {
    transport.connect();
    return () => {
      transport.close();
    };
  }, [transport]);

  const send = useCallback(
    (type, payload = {}) => {
      const success = transport.send(type, payload);
      if (success) {
        setLastRequest(humanizeEventName(type));
        addLog(summarizeOutbound(type, payload), type, "sent");
      }
      return success;
    },
    [transport, addLog],
  );

  const sendWithResponse = useCallback(
    (type, payload = {}) => {
      setLastRequest(humanizeEventName(type));
      addLog(summarizeOutbound(type, payload), type, "sent");
      return transport.sendWithResponse(type, payload);
    },
    [transport, addLog],
  );

  const joinedRooms = useMemo(() => rooms.filter((room) => isRoomMember(room, session?.username)), [rooms, session?.username]);
  const roomOptions = useMemo(() => rooms.map(roomNameFor).filter(Boolean), [rooms]);
  const joinedRoomOptions = useMemo(() => joinedRooms.map(roomNameFor).filter(Boolean), [joinedRooms]);
  const onlineTargets = useMemo(() => onlineUsers.filter((user) => user.username !== session?.username), [onlineUsers, session?.username]);
  const currentUser = useMemo(() => onlineUsers.find((user) => user.username === session?.username) || session, [onlineUsers, session]);
  const activeThread = threads[activeThreadKey] || threads.notifications;
  const activeMode = activeThreadKey.startsWith("room:") ? "room" : activeThreadKey.startsWith("dm:") ? "direct" : "notifications";

  const isActionPending = useCallback(
    (type) => Boolean(pendingActions[type]),
    [pendingActions],
  );

  const hasPendingRoomRequest = useCallback(
    (roomName) => {
      const normalized = String(roomName || "").trim().toLowerCase();
      if (!normalized) return false;
      if (requestedRoomNames.has(normalized)) return true;
      return pendingRequests.some((request) =>
        String(request.room_name || "").trim().toLowerCase() === normalized
        && request.status === "pending"
        && request.requested_by === session?.username
      );
    },
    [pendingRequests, requestedRoomNames, session?.username],
  );

  const selectRoom = useCallback(
    (roomName) => {
      setSelectedRoom(roomName);
      if (roomName && joinedRoomOptions.includes(roomName)) {
        ensureThread(`room:${roomName}`, displayRoomName(roomName), "rooms");
      }
    },
    [ensureThread, joinedRoomOptions],
  );

  const startDirectMessage = useCallback(
    (username) => {
      if (!username) return;
      ensureThread(`dm:${username}`, `@ ${username}`, "direct");
      selectThread(`dm:${username}`);
    },
    [ensureThread, selectThread],
  );

  const clearActiveThread = useCallback(() => {
    setThreads((current) => clearThreadItems(current, activeThreadRef.current, initialThreads.notifications));
  }, []);

  const openThread = useCallback(
    (key) => {
      selectThread(key);
      if (!loadedHistoryRef.current.has(key)) {
        loadedHistoryRef.current.add(key);
        if (key.startsWith("room:")) {
          send("chat_history", { room_name: key.slice(5), limit: 50 });
        } else if (key.startsWith("dm:")) {
          send("private_history", { target_username: key.slice(3), limit: 50 });
        }
      }
    },
    [selectThread, send],
  );

  const submitAuth = useCallback(
    ({ username, password, role }) => {
      setAuthNotice("");
      clearStoredSession();
      const payload = { username: username.trim(), password };
      if (authMode === "register") payload.role = role;
      send(authMode, payload);
    },
    [authMode, send],
  );

  const setAuthMode = useCallback(
    (mode) => {
      if (!sessionRef.current) {
        setAuthNotice("");
        setAuthModeState(mode);
      }
    },
    [],
  );

  const sendComposerMessage = useCallback(
    async ({ content, attachment, target }) => {
      const text = content.trim();
      if (!text && !attachment) {
        appendFeed("Message is required", "error", "Validation");
        return false;
      }
      let attachmentPayload = null;
      if (attachment) {
        try {
          const ticket = await sendWithResponse("prepare_file_upload", {
            file_name: attachment.name,
            mime_type: attachment.type || "application/octet-stream",
            file_size: attachment.size,
          });
          const uploaded = await uploadPreparedAttachment(attachment, ticket.payload?.upload_token);
          attachmentPayload = { attachment_id: uploaded.attachment_id };
        } catch (error) {
          appendFeed(error.message || "The file could not be uploaded", "error", "Attachment");
          return false;
        }
      }
      if (activeMode === "room") {
        const roomName = selectedRoom || activeThreadKey.slice(5);
        if (!roomName) {
          appendFeed("Room name is required", "error", "Validation");
          return false;
        }
        return send(attachmentPayload ? "send_file_message" : "send_room_message", { room_name: roomName, content: text, ...(attachmentPayload || {}) });
      }
      if (activeMode === "direct") {
        const targetUsername = target || activeThreadKey.slice(3);
        if (!targetUsername) {
          appendFeed("Target user is required", "error", "Validation");
          return false;
        }
        ensureThread(`dm:${targetUsername}`, `@ ${targetUsername}`, "direct");
        return send(attachmentPayload ? "send_file_message" : "send_private_message", { target_username: targetUsername, content: text, ...(attachmentPayload || {}) });
      }
      appendFeed("Select a room or direct message thread first", "error", "Composer");
      return false;
    },
    [activeMode, activeThreadKey, appendFeed, ensureThread, selectedRoom, send, sendWithResponse],
  );

  const announce = useCallback(
    (content) => {
      if (!selectedRoom || !content.trim()) {
        appendFeed("Room name and message are required", "error", "Validation");
        return false;
      }
      return send("send_announcement", { room_name: selectedRoom, content: content.trim() });
    },
    [appendFeed, selectedRoom, send],
  );

  const globalAnnounce = useCallback(
    (content) => {
      if (!content.trim()) {
        appendFeed("Announcement message is required", "error", "Validation");
        return false;
      }
      return send("send_global_announcement", { content: content.trim() });
    },
    [appendFeed, send],
  );

  const moderationTargets = useMemo(() => {
    const room = rooms.find((item) => roomNameFor(item) === selectedRoom);
    const members = Array.isArray(room?.members) ? room.members : onlineUsers.map((user) => user.username);
    const memberRoles = room?.member_roles || {};
    return members
      .filter((username) => username && username !== session?.username)
      .map((username) => {
        const user = onlineUsers.find((item) => item.username === username);
        return { username, role: user?.role || memberRoles[username] || "room member" };
      })
      .filter((user) => session?.role !== "teacher" || user.role === "student");
  }, [onlineUsers, rooms, selectedRoom, session?.role, session?.username]);

  return {
    activeMode,
    activeThread,
    activeThreadKey,
    actionNotice,
    announce,
    authMode,
    authNotice,
    clearActiveThread,
    connected,
    currentUser,
    dismissActionNotice,
    ensureThread,
    globalAnnounce,
    joinedRooms,
    joinedRoomOptions,
    hasPendingRoomRequest,
    isActionPending,
    lastRequest,
    moderationTargets,
    onlineTargets,
    onlineUsers,
    openThread,
    pendingRejectRequest,
    pendingRequests,
    roomOptions,
    rooms,
    selectRoom,
    selectThread,
    selectedRoom,
    send,
    sendComposerMessage,
    serverLogs,
    session,
    setAuthMode,
    setPendingRejectRequest,
    startDirectMessage,
    statusText,
    submitAuth,
    threads,
  };
}
