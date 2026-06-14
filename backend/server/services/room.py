from dataclasses import dataclass
from pathlib import Path
import sqlite3
from threading import Lock
from backend.server.core.security import ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER

@dataclass
class ServiceResult:
    success: bool
    message: str
    code: str = "OK"
    payload: dict | None = None

class RoomService:
    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = Path(database_path) if database_path else None
        self._rooms: dict[str, dict] = {}
        self._requests: dict[int, dict] = {}
        self._next_request_id = 1
        self._lock = Lock()
        self._load_from_database()

    def _connect(self) -> sqlite3.Connection:
        if self.database_path is None:
            raise RuntimeError("RoomService database is not configured")
        return sqlite3.connect(self.database_path)

    def _load_from_database(self) -> None:
        if self.database_path is None or not self.database_path.exists():
            return
        with self._connect() as conn:
            room_rows = conn.execute(
                """
                SELECT room_name, description, created_by, managed_by, source_request_id, is_active
                FROM rooms
                """
            ).fetchall()
            member_rows = conn.execute("SELECT room_name, username FROM room_members").fetchall()
            request_rows = conn.execute(
                """
                SELECT request_id, room_name, description, requested_by, requester_role,
                       purpose, status, reviewed_by, rejection_reason
                FROM room_requests
                ORDER BY request_id
                """
            ).fetchall()
        for room_name, description, created_by, managed_by, source_request_id, is_active in room_rows:
            self._rooms[room_name] = {
                "description": description or "",
                "created_by": created_by or "",
                "managed_by": managed_by or created_by or "",
                "source_request_id": source_request_id,
                "is_active": bool(is_active),
                "members": set(),
            }
        for room_name, username in member_rows:
            room = self._rooms.get(room_name)
            if room and room.get("is_active", True):
                room["members"].add(username)
        for request_id, room_name, description, requested_by, requester_role, purpose, status, reviewed_by, rejection_reason in request_rows:
            self._requests[request_id] = {
                "request_id": request_id,
                "room_name": room_name,
                "description": description or "",
                "requested_by": requested_by,
                "requester_role": requester_role,
                "purpose": purpose or "",
                "status": status,
                "reviewed_by": reviewed_by,
                "rejection_reason": rejection_reason,
            }
        if self._requests:
            self._next_request_id = max(self._requests) + 1

    def _persist_room(self, room_name: str, room: dict) -> None:
        if self.database_path is None:
            return
        with self._connect() as conn:
            updated = conn.execute(
                """
                UPDATE rooms
                SET description = ?, created_by = ?, managed_by = ?,
                    source_request_id = ?, is_active = ?
                WHERE room_name = ?
                """,
                (
                    room["description"],
                    room["created_by"],
                    room["managed_by"],
                    room["source_request_id"],
                    1 if room.get("is_active", True) else 0,
                    room_name,
                ),
            ).rowcount
            if updated == 0:
                conn.execute(
                    """
                    INSERT INTO rooms (room_name, description, created_by, managed_by, source_request_id, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        room_name,
                        room["description"],
                        room["created_by"],
                        room["managed_by"],
                        room["source_request_id"],
                        1 if room.get("is_active", True) else 0,
                    ),
                )

    def _persist_room_deleted(self, room_name: str) -> None:
        if self.database_path is None:
            return
        with self._connect() as conn:
            conn.execute("UPDATE rooms SET is_active = 0 WHERE room_name = ?", (room_name,))
            conn.execute("DELETE FROM room_members WHERE room_name = ?", (room_name,))

    def _persist_member_joined(self, room_name: str, username: str, role: str | None) -> None:
        if self.database_path is None:
            return
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO room_members (room_name, username, role) VALUES (?, ?, ?)",
                (room_name, username, role),
            )

    def _persist_member_left(self, room_name: str, username: str) -> None:
        if self.database_path is None:
            return
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM room_members WHERE room_name = ? AND username = ?",
                (room_name, username),
            )

    def _persist_request(self, request: dict) -> None:
        if self.database_path is None:
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO room_requests (
                    request_id, room_name, description, requested_by, requester_role,
                    purpose, status, reviewed_by, rejection_reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    room_name = excluded.room_name,
                    description = excluded.description,
                    requested_by = excluded.requested_by,
                    requester_role = excluded.requester_role,
                    purpose = excluded.purpose,
                    status = excluded.status,
                    reviewed_by = excluded.reviewed_by,
                    rejection_reason = excluded.rejection_reason,
                    reviewed_at = CASE
                        WHEN excluded.status != 'pending' THEN CURRENT_TIMESTAMP
                        ELSE room_requests.reviewed_at
                    END
                """,
                (
                    request["request_id"],
                    request["room_name"],
                    request["description"],
                    request["requested_by"],
                    request["requester_role"],
                    request["purpose"],
                    request["status"],
                    request["reviewed_by"],
                    request["rejection_reason"],
                ),
            )

    def create_room(
        self,
        room_name: str,
        description: str,
        created_by: str,
        role: str,
        managed_by: str | None = None,
        source_request_id: int | None = None,
    ) -> ServiceResult:
        room_name = room_name.strip()
        role = (role or "").strip().lower()
        if role != ROLE_ADMIN:
            return ServiceResult(False, "Permission denied: only admin can create room", "PERMISSION_DENIED")
        if not room_name:
            return ServiceResult(False, "Room name is required", "VALIDATION_ERROR")
        with self._lock:
            if room_name in self._rooms and self._rooms[room_name].get("is_active", True):
                return ServiceResult(False, "Room already exists", "ROOM_ALREADY_EXISTS")
            self._rooms[room_name] = {
                "description": description.strip(),
                "created_by": created_by,
                "managed_by": managed_by or created_by,
                "source_request_id": source_request_id,
                "is_active": True,
                "members": set(),
            }
            self._persist_room(room_name, self._rooms[room_name])
        return ServiceResult(True, "Room created successfully", payload={"room_name": room_name})

    def request_room(self, room_name: str, description: str, requested_by: str, requester_role: str, purpose: str) -> ServiceResult:
        room_name = room_name.strip()
        description = description.strip()
        purpose = purpose.strip()
        requester_role = (requester_role or "").strip().lower()
        if requester_role not in {ROLE_TEACHER, ROLE_STUDENT}:
            return ServiceResult(False, "Only teacher or student can request rooms", "PERMISSION_DENIED")
        if not room_name:
            return ServiceResult(False, "Room name is required", "VALIDATION_ERROR")
        with self._lock:
            if room_name in self._rooms and self._rooms[room_name].get("is_active", True):
                return ServiceResult(False, "Room already exists", "ROOM_ALREADY_EXISTS")
            for existing in self._requests.values():
                if (
                    existing["status"] == "pending"
                    and existing["room_name"].lower() == room_name.lower()
                    and existing["requested_by"] == requested_by
                ):
                    return ServiceResult(False, "You already have a pending request for this room", "ROOM_REQUEST_ALREADY_PENDING")
            request_id = self._next_request_id
            self._next_request_id += 1
            request = {
                "request_id": request_id,
                "room_name": room_name,
                "description": description,
                "requested_by": requested_by,
                "requester_role": requester_role,
                "purpose": purpose,
                "status": "pending",
                "reviewed_by": None,
                "rejection_reason": None,
            }
            self._requests[request_id] = request
            self._persist_request(request)
        return ServiceResult(True, "Room request submitted", payload=request.copy())

    def pending_requests(self) -> list[dict]:
        with self._lock:
            return [
                request.copy()
                for request in sorted(self._requests.values(), key=lambda item: item["request_id"])
                if request["status"] == "pending"
            ]

    def approve_request(self, request_id: int, reviewed_by: str, role: str) -> ServiceResult:
        role = (role or "").strip().lower()
        if role != ROLE_ADMIN:
            return ServiceResult(False, "Permission denied: only admin can approve room requests", "PERMISSION_DENIED")
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                return ServiceResult(False, "Room request not found", "ROOM_REQUEST_NOT_FOUND")
            if request["status"] != "pending":
                return ServiceResult(False, "Room request has already been reviewed", "ROOM_REQUEST_ALREADY_REVIEWED")
            room_name = request["room_name"]
            if room_name in self._rooms and self._rooms[room_name].get("is_active", True):
                return ServiceResult(False, "Room already exists", "ROOM_ALREADY_EXISTS")
            request["status"] = "approved"
            request["reviewed_by"] = reviewed_by
            self._rooms[room_name] = {
                "description": request["description"],
                "created_by": reviewed_by,
                "managed_by": request["requested_by"],
                "source_request_id": request_id,
                "is_active": True,
                "members": set(),
            }
            self._persist_room(room_name, self._rooms[room_name])
            self._persist_request(request)
            payload = request.copy()
            payload["room_name"] = room_name
        return ServiceResult(True, "Room request approved", payload=payload)

    def reject_request(self, request_id: int, reviewed_by: str, role: str, reason: str = "") -> ServiceResult:
        role = (role or "").strip().lower()
        if role != ROLE_ADMIN:
            return ServiceResult(False, "Permission denied: only admin can reject room requests", "PERMISSION_DENIED")
        reason = reason.strip()
        if not reason:
            return ServiceResult(False, "Rejection reason is required", "REJECTION_REASON_REQUIRED")
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                return ServiceResult(False, "Room request not found", "ROOM_REQUEST_NOT_FOUND")
            if request["status"] != "pending":
                return ServiceResult(False, "Room request has already been reviewed", "ROOM_REQUEST_ALREADY_REVIEWED")
            request["status"] = "rejected"
            request["reviewed_by"] = reviewed_by
            request["rejection_reason"] = reason
            self._persist_request(request)
            payload = request.copy()
        return ServiceResult(True, "Room request rejected", payload=payload)

    def delete_room(self, room_name: str, username: str, role: str) -> ServiceResult:
        role = (role or "").strip().lower()
        if role != ROLE_ADMIN:
            return ServiceResult(False, "Permission denied: only admin can delete rooms", "PERMISSION_DENIED")
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None or not room.get("is_active", True):
                return ServiceResult(False, "Room not found", "ROOM_NOT_FOUND")
            room["is_active"] = False
            room["members"].clear()
            self._persist_room_deleted(room_name)
        return ServiceResult(True, "Room deleted successfully", payload={"room_name": room_name, "deleted_by": username})

    def list_rooms(self, include_members: bool = False) -> list[dict]:
        with self._lock:
            rooms = []
            for name, data in sorted(self._rooms.items()):
                if not data.get("is_active", True):
                    continue
                room = {
                    "room_name": name,
                    "description": data["description"],
                    "created_by": data["created_by"],
                    "managed_by": data["managed_by"],
                    "member_count": len(data["members"]),
                    "status": "active" if data.get("is_active", True) else "inactive",
                }
                if include_members:
                    room["members"] = sorted(data["members"])
                rooms.append(room)
            return rooms

    def join_room(self, room_name: str, username: str, role: str | None = None) -> ServiceResult:
        role = role.strip().lower() if role is not None else None
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None or not room.get("is_active", True):
                return ServiceResult(False, "Room not found", "ROOM_NOT_FOUND")
            if username in room["members"]:
                return ServiceResult(False, "User already in room", "USER_ALREADY_IN_ROOM")
            room["members"].add(username)
            self._persist_member_joined(room_name, username, role)
        return ServiceResult(True, "Joined room successfully", payload={"room_name": room_name})

    def leave_room(self, room_name: str, username: str) -> ServiceResult:
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None or not room.get("is_active", True):
                return ServiceResult(False, "Room not found", "ROOM_NOT_FOUND")
            if username not in room["members"]:
                return ServiceResult(False, "User not in room", "USER_NOT_IN_ROOM")
            room["members"].remove(username)
            self._persist_member_left(room_name, username)
        return ServiceResult(True, "Left room successfully", payload={"room_name": room_name})

    def can_announce(self, room_name: str, username: str, role: str) -> bool:
        role = (role or "").strip().lower()
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None or not room.get("is_active", True):
                return False
            return username in room["members"] and role in {ROLE_ADMIN, ROLE_TEACHER}

    def kick_user(self, room_name: str, kicker: str, kicker_role: str, target: str, target_role: str | None) -> ServiceResult:
        kicker_role = (kicker_role or "").strip().lower()
        target_role = target_role.strip().lower() if target_role is not None else None
        with self._lock:
            room = self._rooms.get(room_name)
            if room is None or not room.get("is_active", True):
                return ServiceResult(False, "Room not found", "ROOM_NOT_FOUND")
            if target not in room["members"]:
                return ServiceResult(False, "User not in room", "USER_NOT_IN_ROOM")
            allowed = kicker_role == ROLE_ADMIN or (
                kicker_role == ROLE_TEACHER
                and kicker in room["members"]
                and room["managed_by"] == kicker
                and target_role == ROLE_STUDENT
            )
            if not allowed:
                return ServiceResult(False, "Permission denied: cannot kick this user", "PERMISSION_DENIED")
            room["members"].remove(target)
            self._persist_member_left(room_name, target)
        return ServiceResult(True, "User kicked from room", payload={"room_name": room_name, "target_username": target})

    def is_member(self, room_name: str, username: str) -> bool:
        with self._lock:
            room = self._rooms.get(room_name)
            return bool(room and room.get("is_active", True) and username in room["members"])

    def members(self, room_name: str) -> list[str]:
        with self._lock:
            room = self._rooms.get(room_name)
            if not room or not room.get("is_active", True):
                return []
            return list(room["members"])

    def room_exists(self, room_name: str) -> bool:
        with self._lock:
            room = self._rooms.get(room_name)
            return bool(room and room.get("is_active", True))
