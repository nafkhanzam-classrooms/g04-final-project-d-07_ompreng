import socket
from typing import Any
from threading import Lock
from backend.server.transport.tcp.protocol import encode_message

class Broadcaster:
    def __init__(self, server) -> None:
        self.server = server

    def send(self, client, message: dict[str, Any]) -> None:
        try:
            encoded = encode_message(message)
            self.send_safe(client, encoded)
            self.server.stats_reporter.record_bytes_sent(len(encoded))
        except OSError:
            self.server.disconnect(client)

    def send_safe(self, client_socket: socket.socket, data: bytes) -> None:
        with self.server.socket_locks_lock:
            if client_socket not in self.server.socket_locks:
                self.server.socket_locks[client_socket] = Lock()
            lock = self.server.socket_locks[client_socket]
        with lock:
            client_socket.sendall(data)

    def broadcast_room(self, room_name: str, event: dict[str, Any]) -> None:
        for username in self.server.rooms.members(room_name):
            with self.server.state_lock:
                data = self.server.online_users.get(username)
            if data:
                self.send(data["socket"], event)

    def send_private_participants(self, message: dict, event: dict[str, Any]) -> None:
        participants = {message.get("sender"), message.get("receiver")}
        with self.server.state_lock:
            clients = [
                data["socket"]
                for username, data in self.server.online_users.items()
                if username in participants
            ]
        for client in clients:
            self.send(client, event)

    def broadcast_all(self, event: dict[str, Any]) -> None:
        with self.server.state_lock:
            clients = [data["socket"] for data in self.server.online_users.values()]
        for client in clients:
            self.send(client, event)

    def broadcast_admins(self, event: dict[str, Any]) -> None:
        with self.server.state_lock:
            clients = [data["socket"] for data in self.server.online_users.values() if data["role"] == "admin"]
        for client in clients:
            self.send(client, event)

    def broadcast_user_online(self, username: str, role: str) -> None:
        self.broadcast_all({"type": "user_online", "payload": {"username": username, "role": role}})

    def broadcast_user_offline(self, username: str) -> None:
        self.broadcast_all({"type": "user_offline", "payload": {"username": username}})

    def broadcast_room_list(self) -> None:
        self.broadcast_all({"type": "room_list_updated", "payload": {"rooms": self.server.room_list_snapshot()}})
