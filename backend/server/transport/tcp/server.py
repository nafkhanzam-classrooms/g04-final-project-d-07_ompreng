import socket
import ssl
import time
from threading import Lock, Thread
from typing import Any, Callable
from backend.server.services.auth import AuthService
from backend.server.core.logger import configure_logger
from backend.server.services.message import MessageService, default_timestamp
from backend.server.transport.tcp.protocol import JSONLineBuffer, encode_message, error_response, success_response
from backend.server.core.security import ROLE_ADMIN, ROLE_STUDENT
from backend.server.services.room import RoomService, ServiceResult
from backend.server.transport.tcp.stats import StatsReporter
from backend.server.transport.tcp.session import SessionManager
from backend.server.transport.tcp.broadcaster import Broadcaster
from backend.server.transport.tcp.commands import CommandRouter

PUBLIC_COMMANDS = {"ping", "login", "register", "resume_session"}

class MBGServer:
    def __init__(
        self,
        timestamp_provider: Callable[[], str] | None = None,
        logger=None,
        auth: AuthService | None = None,
        messages: MessageService | None = None,
        database_path: str | None = None,
    ) -> None:
        self.auth = auth or AuthService(database_path)
        self.rooms = RoomService(database_path)
        self.timestamp_provider = timestamp_provider or default_timestamp
        self.messages = messages or MessageService(self.timestamp_provider, database_path=database_path)
        self.logger = logger or configure_logger()
        self.sessions: dict[Any, dict[str, str]] = {}
        self.session_tokens: dict[str, dict[str, str]] = {}
        self.online_users: dict[str, dict[str, Any]] = {}
        self.activity_logs: list[dict[str, str | None]] = []
        self.state_lock = Lock()
        self.socket_locks: dict[Any, Lock] = {}
        self.socket_locks_lock = Lock()

        self.stats_reporter = StatsReporter()
        self.session_manager = SessionManager(self)
        self.broadcaster = Broadcaster(self)
        self.router = CommandRouter(self)

    @property
    def stats(self) -> dict:
        return self.stats_reporter.stats

    def handle_message(self, client, address, message: dict[str, Any]) -> list[dict[str, Any]]:
        request_type = message.get("type")
        request_id = message.get("request_id")
        payload = message.get("payload") or {}
        if not isinstance(payload, dict):
            return [error_response(request_id, "Payload must be an object", "INVALID_PAYLOAD")]

        if request_type not in PUBLIC_COMMANDS and not self.session_manager.session_for(client):
            return [error_response(request_id, "Please login before using this command", "NOT_AUTHENTICATED")]

        return [self.router.handle(client, address, request_type, request_id, payload)]

    def serve_forever(self, host: str = "0.0.0.0", port: int = 5000, stats_interval: float = 5.0, use_ssl: bool = False, certfile: str | None = None, keyfile: str | None = None) -> None:
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_socket.bind((host, port))
        raw_socket.listen()

        ssl_ctx = None
        if use_ssl and certfile and keyfile:
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)

        with raw_socket as server_socket:
            self.logger.info("server_started host=%s port=%s", host, port)
            print(f"Server started on {host}:{port}")
            print("Waiting for clients...")
            self.stats_reporter.start(stats_interval)

            while True:
                try:
                    client_socket, address = server_socket.accept()
                except OSError:
                    continue
                thread = Thread(target=self.handle_client, args=(client_socket, address, ssl_ctx), daemon=True)
                thread.start()

    def handle_client(self, client_socket: socket.socket, address, ssl_ctx: ssl.SSLContext | None = None) -> None:
        if ssl_ctx:
            client_socket.settimeout(5.0)
            try:
                client_socket = ssl_ctx.wrap_socket(client_socket, server_side=True)
            except (ssl.SSLError, OSError):
                try:
                    client_socket.close()
                except OSError:
                    pass
                return
        client_socket.settimeout(None)
        self.stats_reporter.record_connection_opened()
        self.logger.info("client_connected address=%s", address)
        buffer = JSONLineBuffer()
        try:
            with client_socket:
                while True:
                    try:
                        data = client_socket.recv(4096)
                    except OSError:
                        break
                    if not data:
                        break
                    self.stats_reporter.record_bytes_received(len(data))
                    try:
                        messages = buffer.feed(data)
                    except ValueError:
                        response = encode_message(error_response(None, "Invalid JSON", "INVALID_JSON"))
                        self.broadcaster.send_safe(client_socket, response)
                        self.stats_reporter.record_bytes_sent(len(response))
                        self.stats_reporter.record_request(0.0, True)
                        self.logger.info("invalid_json address=%s", address)
                        continue
                    for message in messages:
                        started_at = time.perf_counter()
                        responses = self.handle_message(client_socket, address, message)
                        failed = any(response.get("success") is False or response.get("type") == "error" for response in responses)
                        for response in responses:
                            encoded = encode_message(response)
                            self.broadcaster.send_safe(client_socket, encoded)
                            self.stats_reporter.record_bytes_sent(len(encoded))
                        elapsed_ms = (time.perf_counter() - started_at) * 1000
                        self.stats_reporter.record_request(elapsed_ms, failed)
        finally:
            self.disconnect(client_socket)
            self.stats_reporter.record_connection_closed()
            self.logger.info("client_disconnected address=%s", address)

    def disconnect(self, client) -> None:
        username = None
        removed = False
        with self.state_lock:
            session = self.sessions.pop(client, None)
            if not session:
                return
            username = session["username"]
            if self.online_users.get(username, {}).get("socket") is client:
                self.online_users.pop(username, None)
                removed = True
        with self.socket_locks_lock:
            self.socket_locks.pop(client, None)
        if username and removed:
            self.broadcaster.broadcast_user_offline(username)

    def _online_user_snapshot(self) -> list[dict[str, str]]:
        return self.online_user_snapshot()

    def online_user_snapshot(self) -> list[dict[str, str]]:
        with self.state_lock:
            return [
                {"username": username, "role": data["role"]}
                for username, data in sorted(self.online_users.items())
            ]

    def _room_list_snapshot(self) -> list[dict[str, Any]]:
        return self.room_list_snapshot()

    def room_list_snapshot(self) -> list[dict[str, Any]]:
        rooms = self.rooms.list_rooms(include_members=True)
        for room in rooms:
            members = room.get("members") or []
            room["member_roles"] = {
                username: self.auth.role_for(username) or "unknown"
                for username in members
            }
        return rooms

    def login_payload(self, user: dict[str, str], session_token: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "username": user["username"],
            "role": user["role"],
            "session_token": session_token,
            "bootstrap": {
                "users": self.online_user_snapshot(),
                "rooms": self.room_list_snapshot(),
                "feed_messages": self.messages.feed_history(50),
            },
        }
        if user["role"] == "admin":
            with self.state_lock:
                logs = self.activity_logs[-50:]
            payload["bootstrap"]["pending_requests"] = self.rooms.pending_requests()
            payload["bootstrap"]["server_logs"] = logs
        return payload

    def _login_payload(self, user: dict[str, str], session_token: str | None = None) -> dict[str, Any]:
        return self.login_payload(user, session_token)

    def record_activity(self, event_type: str, username: str | None, description: str) -> None:
        log_entry = {
            "event_type": event_type,
            "username": username,
            "description": description,
            "timestamp": self.timestamp_provider(),
        }
        with self.state_lock:
            self.activity_logs.append(log_entry)
            if len(self.activity_logs) > 1000:
                self.activity_logs.pop(0)
            logs = self.activity_logs[-50:]
        self.broadcaster.broadcast_admins({"type": "server_logs_updated", "payload": {"logs": logs}})

    def _record_activity(self, event_type: str, username: str | None, description: str) -> None:
        self.record_activity(event_type, username, description)

    def result_response(self, response_type: str, request_id: str | None, result: ServiceResult) -> dict:
        if result.success:
            return success_response(response_type, request_id, result.message, result.payload or {})
        return error_response(request_id, result.message, result.code)

    def _result_response(self, response_type: str, request_id: str | None, result: ServiceResult) -> dict:
        return self.result_response(response_type, request_id, result)

    def can_react_to_message(self, session: dict, message: dict) -> bool:
        username = session["username"]
        if message.get("message_type") not in {"room_message", "private_message", "announcement"}:
            return False
        if message.get("message_type") == "private_message":
            return username in {message.get("sender"), message.get("receiver")}
        room_name = message.get("room_name")
        if room_name and self.rooms.room_exists(room_name):
            return session.get("role") == "admin" or self.rooms.is_member(room_name, username)
        return True

    def _can_react_to_message(self, session: dict, message: dict) -> bool:
        return self.can_react_to_message(session, message)

    def _send(self, client, message: dict[str, Any]) -> None:
        self.broadcaster.send(client, message)

    def _send_safe(self, client_socket: socket.socket, data: bytes) -> None:
        self.broadcaster.send_safe(client_socket, data)

    def _broadcast_user_online(self, username: str, role: str) -> None:
        self.broadcaster.broadcast_user_online(username, role)

    def _broadcast_user_offline(self, username: str) -> None:
        self.broadcaster.broadcast_user_offline(username)

    def _broadcast_room_list(self) -> None:
        self.broadcaster.broadcast_room_list()

    def _broadcast_room(self, room_name: str, event: dict[str, Any]) -> None:
        self.broadcaster.broadcast_room(room_name, event)

    def _broadcast_all(self, event: dict[str, Any]) -> None:
        self.broadcaster.broadcast_all(event)

    def _broadcast_admins(self, event: dict[str, Any]) -> None:
        self.broadcaster.broadcast_admins(event)

    def _send_private_participants(self, message: dict, event: dict[str, Any]) -> None:
        self.broadcaster.send_private_participants(message, event)

    def _session_for(self, client) -> dict[str, str] | None:
        return self.session_manager.session_for(client)
