from typing import Any
from backend.server.transport.tcp.protocol import error_response, success_response
from backend.server.core.security import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER
from backend.server.services.room import ServiceResult

REACTABLE_MESSAGE_TYPES = {"room_message", "private_message", "announcement"}

class CommandRouter:
    def __init__(self, server) -> None:
        self.server = server
        self.handlers = {
            "ping": self._handle_ping,
            "login": self._handle_login,
            "resume_session": self._handle_resume_session,
            "logout": self._handle_logout,
            "register": self._handle_register,
            "online_users": self._handle_online_users,
            "room_list": self._handle_room_list,
            "request_room": self._handle_request_room,
            "pending_room_requests": self._handle_pending_room_requests,
            "approve_room_request": self._handle_approve_room_request,
            "reject_room_request": self._handle_reject_room_request,
            "create_room": self._handle_create_room,
            "delete_room": self._handle_delete_room,
            "join_room": self._handle_join_room,
            "leave_room": self._handle_leave_room,
            "send_room_message": self._handle_room_message,
            "send_announcement": self._handle_announcement,
            "send_global_announcement": self._handle_global_announcement,
            "send_private_message": self._handle_private_message,
            "prepare_file_upload": self._handle_prepare_file_upload,
            "send_file_message": self._handle_file_message,
            "kick_user": self._handle_kick_user,
            "delete_message": self._handle_delete_message,
            "toggle_reaction": self._handle_toggle_reaction,
            "chat_history": self._handle_chat_history,
            "private_history": self._handle_private_history,
            "feed_history": self._handle_feed_history,
            "server_logs": self._handle_server_logs,
        }

    def handle(self, client, address, request_type, request_id, payload) -> dict:
        handler = self.handlers.get(request_type)
        if handler is None:
            self.server.logger.info("invalid_command type=%s", request_type)
            return error_response(request_id, "Unknown command", "UNKNOWN_COMMAND")
        return handler(client, address, request_id, payload)

    def _handle_ping(self, client, address, request_id, payload) -> dict:
        self.server.logger.info("ping address=%s", address)
        return success_response("pong", request_id, "Server received your message")

    def _handle_login(self, client, address, request_id, payload) -> dict:
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))
        user = self.server.auth.login(username, password)
        if user is None:
            self.server.logger.info("login_failed username=%s address=%s", username, address)
            return error_response(request_id, "Invalid username or password", "INVALID_CREDENTIALS")
        with self.server.state_lock:
            if username in self.server.online_users:
                return error_response(request_id, "User is already online", "DUPLICATE_LOGIN")
            token = self.server.session_manager.issue_session_token(user)
            self.server.session_manager.attach_session(client, address, user, token)
        self.server.logger.info("login_success username=%s role=%s", username, user["role"])
        self.server.record_activity("login_success", username, f"{username} logged in as {user['role']}")
        self.server.broadcaster.broadcast_user_online(username, user["role"])
        self.server.broadcaster.send(client, {"type": "room_list_updated", "payload": {"rooms": self.server.room_list_snapshot()}})
        self.server.broadcaster.send(client, {"type": "feed_history_response", "payload": {"messages": self.server.messages.feed_history(50)}})
        if user["role"] == "admin":
            self.server.broadcaster.send(client, {"type": "pending_room_requests_updated", "payload": {"requests": self.server.rooms.pending_requests()}})
        return success_response("login_response", request_id, "Login successful", self.server.login_payload(user, token))

    def _handle_resume_session(self, client, address, request_id, payload) -> dict:
        token = str(payload.get("session_token", "")).strip()
        with self.server.state_lock:
            user = self.server.session_tokens.get(token)
            if not user:
                return error_response(request_id, "Session token is invalid or expired", "SESSION_EXPIRED")
            self.server.session_manager.attach_session(client, address, user, token)
        self.server.logger.info("session_resumed username=%s role=%s", user["username"], user["role"])
        self.server.record_activity("session_resumed", user["username"], f"{user['username']} resumed session as {user['role']}")
        self.server.broadcaster.broadcast_user_online(user["username"], user["role"])
        self.server.broadcaster.send(client, {"type": "room_list_updated", "payload": {"rooms": self.server.room_list_snapshot()}})
        self.server.broadcaster.send(client, {"type": "feed_history_response", "payload": {"messages": self.server.messages.feed_history(50)}})
        if user["role"] == "admin":
            self.server.broadcaster.send(client, {"type": "pending_room_requests_updated", "payload": {"requests": self.server.rooms.pending_requests()}})
        return success_response("resume_session_response", request_id, "Session resumed", self.server.login_payload(user, token))

    def _handle_register(self, client, address, request_id, payload) -> dict:
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))
        role = str(payload.get("role", "student")).strip()
        success, message, code, user = self.server.auth.register(username, password, role)
        if not success:
            self.server.logger.info("register_failed username=%s role=%s message=%s", username, role, message)
            return error_response(request_id, message, code)
        self.server.logger.info("register_success username=%s role=%s", username, role)
        self.server.record_activity("register_success", username, f"{username} registered with role {role}")
        return success_response("register_response", request_id, message, user)

    def _handle_logout(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        username = session["username"]
        token = session.get("session_token", "")
        with self.server.state_lock:
            self.server.sessions.pop(client, None)
            self.server.online_users.pop(username, None)
            if token:
                self.server.session_tokens.pop(token, None)
        with self.server.socket_locks_lock:
            self.server.socket_locks.pop(client, None)
        self.server.logger.info("logout username=%s address=%s", username, address)
        self.server.record_activity("logout", username, f"{username} logged out")
        self.server.broadcaster.broadcast_user_offline(username)
        return success_response("logout_response", request_id, "Logged out successfully", {"username": username})

    def _handle_online_users(self, client, address, request_id, payload) -> dict:
        return success_response("online_users_response", request_id, "Online users list retrieved", {"users": self.server.online_user_snapshot()})

    def _handle_room_list(self, client, address, request_id, payload) -> dict:
        return success_response("room_list_response", request_id, "Room list retrieved", {"rooms": self.server.room_list_snapshot()})

    def _handle_request_room(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        description = str(payload.get("description", ""))
        purpose = str(payload.get("purpose", ""))
        result = self.server.rooms.request_room(
            room_name,
            description,
            session["username"],
            session["role"],
            purpose,
        )
        if result.success:
            self.server.record_activity("room_request_submitted", session["username"], f"requested room {result.payload['room_name']}")
            event = self.server.messages.save_feed_event("room_request_submitted", session["username"], f"{session['username']} requested room {result.payload['room_name']}", result.payload["room_name"])
            self.server.broadcaster.broadcast_all({"type": "room_request_submitted", "payload": event})
            self.server.broadcaster.broadcast_admins({"type": "pending_room_requests_updated", "payload": {"requests": self.server.rooms.pending_requests()}})
        return self.server.result_response("request_room_response", request_id, result)

    def _handle_pending_room_requests(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        if session["role"] != "admin":
            return error_response(request_id, "Permission denied: only admin can view pending requests", "PERMISSION_DENIED")
        requests = self.server.rooms.pending_requests()
        return success_response("pending_room_requests_response", request_id, "Pending requests retrieved", {"requests": requests})

    def _handle_approve_room_request(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        try:
            request_number = int(payload.get("request_id", 0))
        except (TypeError, ValueError):
            return error_response(request_id, "Invalid request_id", "VALIDATION_ERROR")
        result = self.server.rooms.approve_request(request_number, session["username"], session["role"])
        if result.success:
            room_name = result.payload.get("room_name")
            self.server.record_activity("room_request_approved", session["username"], f"approved room request {request_number}")
            event = self.server.messages.save_feed_event("room_request_approved", session["username"], f"Room request {request_number} approved for {room_name}", room_name)
            self.server.broadcaster.broadcast_all({"type": "room_request_approved", "payload": event})
            self.server.broadcaster.broadcast_all({"type": "room_created", "payload": {"room_name": room_name}})
            self.server.broadcaster.broadcast_room_list()
            self.server.broadcaster.broadcast_admins({"type": "pending_room_requests_updated", "payload": {"requests": self.server.rooms.pending_requests()}})
        return self.server.result_response("approve_room_request_response", request_id, result)

    def _handle_reject_room_request(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        try:
            request_number = int(payload.get("request_id", 0))
        except (TypeError, ValueError):
            return error_response(request_id, "Invalid request_id", "VALIDATION_ERROR")
        reason = str(payload.get("reason", ""))
        result = self.server.rooms.reject_request(
            request_number,
            session["username"],
            session["role"],
            reason,
        )
        if result.success:
            room_name = result.payload.get("room_name")
            self.server.record_activity("room_request_rejected", session["username"], f"rejected room request {request_number}")
            event = self.server.messages.save_feed_event(
                "room_request_rejected",
                session["username"],
                f"Room request {request_number} rejected for {room_name}: {reason}",
                room_name,
            )
            event["request_id"] = request_number
            event["requested_by"] = result.payload.get("requested_by")
            event["room_name"] = result.payload.get("room_name")
            event["rejection_reason"] = reason
            self.server.broadcaster.broadcast_all({"type": "room_request_rejected", "payload": event})
            self.server.broadcaster.broadcast_admins({"type": "pending_room_requests_updated", "payload": {"requests": self.server.rooms.pending_requests()}})
        return self.server.result_response("reject_room_request_response", request_id, result)

    def _handle_create_room(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        description = str(payload.get("description", ""))
        result = self.server.rooms.create_room(room_name, description, session["username"], session["role"])
        if result.success:
            self.server.logger.info("room_created username=%s", session["username"])
            self.server.record_activity("room_created", session["username"], f"created room {result.payload['room_name']}")
            event = self.server.messages.save_feed_event("room_created", session["username"], f"Room {result.payload['room_name']} created", result.payload["room_name"])
            self.server.broadcaster.broadcast_all({"type": "room_created", "payload": event})
            self.server.broadcaster.broadcast_room_list()
        else:
            self.server.logger.info("permission_denied username=%s message=%s", session["username"], result.message)
        return self.server.result_response("create_room_response", request_id, result)

    def _handle_delete_room(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        result = self.server.rooms.delete_room(room_name, session["username"], session["role"])
        if result.success:
            feed_event = self.server.messages.save_feed_event("room_deleted", session["username"], f"Room {room_name} deleted", room_name)
            event = {"type": "room_deleted", "payload": feed_event}
            self.server.record_activity("room_deleted", session["username"], f"deleted room {room_name}")
            self.server.broadcaster.broadcast_all(event)
            self.server.broadcaster.broadcast_room_list()
        return self.server.result_response("delete_room_response", request_id, result)

    def _handle_join_room(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        result = self.server.rooms.join_room(room_name, session["username"], session["role"])
        if result.success:
            event = self.server.messages.save_system_message(room_name, f"{session['username']} joined the room")
            self.server.broadcaster.broadcast_room(room_name, {"type": "system_message", "payload": event})
            self.server.logger.info("user_joined_room room=%s username=%s", room_name, session["username"])
            self.server.record_activity("user_joined_room", session["username"], f"joined room {room_name}")
            self.server.broadcaster.broadcast_room_list()
        return self.server.result_response("join_room_response", request_id, result)

    def _handle_leave_room(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        result = self.server.rooms.leave_room(room_name, session["username"])
        if result.success:
            event = self.server.messages.save_system_message(room_name, f"{session['username']} left the room")
            self.server.broadcaster.broadcast_room(room_name, {"type": "system_message", "payload": event})
            self.server.logger.info("user_left_room room=%s username=%s", room_name, session["username"])
            self.server.record_activity("user_left_room", session["username"], f"left room {room_name}")
            self.server.broadcaster.broadcast_room_list()
        return self.server.result_response("leave_room_response", request_id, result)

    def _handle_room_message(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        content = str(payload.get("content", "")).strip()
        if not content:
            return error_response(request_id, "Message cannot be empty", "EMPTY_MESSAGE")
        if not self.server.rooms.is_member(room_name, session["username"]):
            return error_response(request_id, "User is not in room", "USER_NOT_IN_ROOM")
        message = self.server.messages.save_room_message(room_name, session["username"], content)
        self.server.broadcaster.broadcast_room(room_name, {"type": "room_message", "payload": message})
        self.server.logger.info("room_message room=%s sender=%s", room_name, session["username"])
        self.server.record_activity("room_message", session["username"], f"sent room message in {room_name}")
        return success_response("send_room_message_response", request_id, "Room message sent", {"room_name": room_name})

    def _handle_announcement(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        content = str(payload.get("content", "")).strip()
        if not content:
            return error_response(request_id, "Announcement cannot be empty", "EMPTY_MESSAGE")
        if not self.server.rooms.room_exists(room_name):
            return error_response(request_id, "Room not found", "ROOM_NOT_FOUND")
        if not self.server.rooms.can_announce(room_name, session["username"], session["role"]):
            return error_response(request_id, "Permission denied: cannot announce in this room", "PERMISSION_DENIED")
        announcement = self.server.messages.save_announcement(room_name, session["username"], content)
        self.server.broadcaster.broadcast_room(room_name, {"type": "announcement", "payload": announcement})
        self.server.logger.info("announcement room=%s sender=%s", room_name, session["username"])
        self.server.record_activity("announcement_sent", session["username"], f"sent announcement in {room_name}")
        return success_response("send_announcement_response", request_id, "Announcement sent", {"room_name": room_name})

    def _handle_global_announcement(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        content = str(payload.get("content", "")).strip()
        if session["role"] != "admin":
            return error_response(request_id, "Permission denied: only admin can send global announcements", "PERMISSION_DENIED")
        if not content:
            return error_response(request_id, "Announcement cannot be empty", "EMPTY_MESSAGE")
        announcement = self.server.messages.save_feed_event("global_announcement", session["username"], content)
        self.server.broadcaster.broadcast_all({"type": "global_announcement", "payload": announcement})
        self.server.logger.info("global_announcement sender=%s", session["username"])
        self.server.record_activity("global_announcement_sent", session["username"], "sent a global announcement")
        return success_response("send_global_announcement_response", request_id, "Global announcement sent", {})

    def _handle_private_message(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        target = str(payload.get("target_username", "")).strip()
        content = str(payload.get("content", "")).strip()
        if not content:
            return error_response(request_id, "Message cannot be empty", "EMPTY_MESSAGE")
        if target == session["username"]:
            return error_response(request_id, "Cannot send private message to yourself", "INVALID_TARGET")
        if not self.server.auth.exists(target):
            return error_response(request_id, "Target user not found", "TARGET_NOT_FOUND")
        with self.server.state_lock:
            target_data = self.server.online_users.get(target)
        if not target_data:
            return error_response(request_id, "Target user is offline", "TARGET_OFFLINE")
        private_message = self.server.messages.save_private_message(session["username"], target, content)
        self.server.broadcaster.send(target_data["socket"], {"type": "private_message", "payload": private_message})
        self.server.broadcaster.send(client, {"type": "private_message", "payload": private_message})
        self.server.logger.info("private_message sender=%s receiver=%s", session["username"], target)
        self.server.record_activity("private_message", session["username"], f"sent private message to {target}")
        return success_response("send_private_message_response", request_id, "Private message sent", {"target_username": target})

    def _handle_prepare_file_upload(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        try:
            file_size = int(payload.get("file_size", 0))
        except (TypeError, ValueError):
            file_size = 0
        success, message, code, ticket = self.server.messages.create_upload_ticket(
            session["username"],
            str(payload.get("file_name", "")),
            str(payload.get("mime_type", "application/octet-stream")),
            file_size,
        )
        if not success:
            return error_response(request_id, message, code)
        return success_response("prepare_file_upload_response", request_id, message, ticket)

    def _handle_file_message(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", "")).strip()
        target = str(payload.get("target_username", "")).strip()
        content = str(payload.get("content", "")).strip()
        attachment_id = str(payload.get("attachment_id", "")).strip()
        if not attachment_id:
            return error_response(request_id, "Attachment id is required", "ATTACHMENT_ID_REQUIRED")

        if target:
            if target == session["username"]:
                return error_response(request_id, "Cannot send private message to yourself", "INVALID_TARGET")
            if not self.server.auth.exists(target):
                return error_response(request_id, "Target user not found", "TARGET_NOT_FOUND")
            with self.server.state_lock:
                target_data = self.server.online_users.get(target)
            if not target_data:
                return error_response(request_id, "Target user is offline", "TARGET_OFFLINE")
            success, message, code, file_message = self.server.messages.save_file_message(
                None,
                session["username"],
                content,
                attachment_id,
                receiver=target,
            )
            if not success:
                return error_response(request_id, message, code)
            self.server.broadcaster.send(target_data["socket"], {"type": "private_message", "payload": file_message})
            self.server.broadcaster.send(client, {"type": "private_message", "payload": file_message})
            self.server.logger.info("file_message sender=%s receiver=%s", session["username"], target)
            self.server.record_activity("file_message", session["username"], f"sent file message to {target}")
            return success_response("send_file_message_response", request_id, message, {"target_username": target})

        if not self.server.rooms.is_member(room_name, session["username"]):
            return error_response(request_id, "User is not in room", "USER_NOT_IN_ROOM")
        success, message, code, file_message = self.server.messages.save_file_message(
            room_name,
            session["username"],
            content,
            attachment_id,
        )
        if not success:
            return error_response(request_id, message, code)
        self.server.broadcaster.broadcast_room(room_name, {"type": "room_message", "payload": file_message})
        self.server.logger.info("file_message room=%s sender=%s", room_name, session["username"])
        self.server.record_activity("file_message", session["username"], f"sent file message in {room_name}")
        return success_response("send_file_message_response", request_id, message, {"room_name": room_name})

    def _handle_delete_message(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        success, message, code, deleted_message = self.server.messages.delete_message(
            str(payload.get("message_id", "")),
            session["username"],
            session["role"],
        )
        if not success:
            return error_response(request_id, message, code)
        self.server.record_activity("message_deleted", session["username"], f"deleted message {deleted_message['message_id']}")
        event = {"type": "message_deleted", "payload": deleted_message}
        room_name = deleted_message.get("room_name")
        if room_name and self.server.rooms.room_exists(room_name):
            self.server.broadcaster.broadcast_room(room_name, event)
        else:
            self.server.broadcaster.broadcast_all(event)
        return success_response("delete_message_response", request_id, message, deleted_message)

    def _handle_toggle_reaction(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        message_id = str(payload.get("message_id", "")).strip()
        emoji = str(payload.get("emoji", "")).strip()
        message = self.server.messages.get_message(message_id)
        if message is None:
            return error_response(request_id, "Message not found", "MESSAGE_NOT_FOUND")
        if message.get("deleted"):
            return error_response(request_id, "Deleted messages cannot be reacted to", "MESSAGE_DELETED")
        if message.get("message_type") not in REACTABLE_MESSAGE_TYPES:
            return error_response(request_id, "Reactions are only available for chat messages", "REACTION_NOT_ALLOWED")
        if not self.server.can_react_to_message(session, message):
            return error_response(request_id, "Permission denied: cannot react to this message", "PERMISSION_DENIED")

        success, result_message, code, reaction = self.server.messages.toggle_reaction(message_id, session["username"], emoji)
        if not success:
            return error_response(request_id, result_message, code)

        event = {"type": "message_reactions_updated", "payload": reaction}
        if message["message_type"] == "private_message":
            self.server.broadcaster.send_private_participants(message, event)
        elif message.get("room_name") and self.server.rooms.room_exists(message["room_name"]):
            self.server.broadcaster.broadcast_room(message["room_name"], event)
        else:
            self.server.broadcaster.broadcast_all(event)
        self.server.record_activity("message_reaction", session["username"], f"reacted {emoji} to {message_id}")
        return success_response("toggle_reaction_response", request_id, result_message, reaction)

    def _handle_kick_user(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        target = str(payload.get("target_username", "")).strip()
        target_role = self.server.auth.role_for(target)
        if not target or target_role is None:
            return error_response(request_id, "Target user not found", "TARGET_NOT_FOUND")
        result = self.server.rooms.kick_user(room_name, session["username"], session["role"], target, target_role)
        if result.success:
            with self.server.state_lock:
                target_data = self.server.online_users.get(target)
            event = {"type": "user_kicked", "payload": result.payload}
            if target_data:
                self.server.broadcaster.send(target_data["socket"], event)
            self.server.broadcaster.broadcast_room(room_name, {"type": "system_message", "payload": self.server.messages.save_system_message(room_name, f"{target} was kicked from the room")})
            self.server.record_activity("user_kicked", session["username"], f"kicked {target} from {room_name}")
            self.server.broadcaster.broadcast_room_list()
        return self.server.result_response("kick_user_response", request_id, result)

    def _handle_chat_history(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        room_name = str(payload.get("room_name", ""))
        try:
            limit = int(payload.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        if not self.server.rooms.is_member(room_name, session["username"]):
            return error_response(request_id, "User is not in room", "USER_NOT_IN_ROOM")
        history = self.server.messages.room_history(room_name, max(1, min(limit, 100)))
        return success_response("chat_history_response", request_id, "Chat history retrieved", {"messages": history})

    def _handle_private_history(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        target = str(payload.get("target_username", "")).strip()
        if not target:
            return error_response(request_id, "Target user is required", "VALIDATION_ERROR")
        if not self.server.auth.exists(target):
            return error_response(request_id, "Target user not found", "TARGET_NOT_FOUND")
        try:
            limit = int(payload.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        history = self.server.messages.private_history(session["username"], target, max(1, min(limit, 100)))
        return success_response("private_history_response", request_id, "Private history retrieved", {
            "messages": history,
            "target_username": target,
        })

    def _handle_feed_history(self, client, address, request_id, payload) -> dict:
        try:
            limit = int(payload.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50
        return success_response("feed_history_response", request_id, "Feed history retrieved", {"messages": self.server.messages.feed_history(limit)})

    def _handle_server_logs(self, client, address, request_id, payload) -> dict:
        session = self.server.session_manager.session_for(client)
        if session["role"] != "admin":
            return error_response(request_id, "Permission denied: only admin can view server logs", "PERMISSION_DENIED")
        try:
            limit = int(payload.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50
        with self.server.state_lock:
            logs = self.server.activity_logs[-max(1, min(limit, 200)):]
        return success_response("server_logs_response", request_id, "Server logs retrieved", {"logs": logs})
