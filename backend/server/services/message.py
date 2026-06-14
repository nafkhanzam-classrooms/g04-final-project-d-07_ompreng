from datetime import datetime
import hashlib
from pathlib import Path
import re
import secrets
import sqlite3
from threading import Lock
from typing import Callable
import uuid
from backend.server.core.security import ROLE_ADMIN

def default_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

ROOM_HISTORY_TYPES = {
    "room_message",
    "system_message",
    "announcement",
    "room_created",
    "room_deleted",
    "user_kicked",
    "room_request_submitted",
    "room_request_approved",
    "room_request_rejected",
}

FEED_EXCLUDED_TYPES = {"private_message"}
DELETABLE_MESSAGE_TYPES = {"room_message", "announcement"}
REACTION_CHOICES = ("agree", "disagree", "like", "funny", "confused")
ALLOWED_REACTIONS = set(REACTION_CHOICES)
DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024
DOWNLOAD_TOKEN_HASH_PREFIX = "sha256$"

class MessageService:
    def __init__(
        self,
        timestamp_provider: Callable[[], str] = default_timestamp,
        database_path: str | None = None,
        upload_dir: str = "data/uploads",
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    ) -> None:
        self._timestamp_provider = timestamp_provider
        self._database_path = database_path
        self._upload_dir = Path(upload_dir)
        self._max_file_size = max_file_size
        self._messages: list[dict] = []
        self._reactions: dict[str, dict[str, set[str]]] = {}
        self._attachments: dict[str, dict] = {}
        self._next_message_id = 1
        self._lock = Lock()
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def save_room_message(self, room_name: str, sender: str, content: str) -> dict:
        message = {
            "room_name": room_name,
            "sender": sender,
            "receiver": None,
            "message_type": "room_message",
            "content": content,
            "timestamp": self._timestamp_provider(),
        }
        return self._save(message)

    def save_private_message(self, sender: str, receiver: str, content: str) -> dict:
        message = {
            "room_name": None,
            "sender": sender,
            "receiver": receiver,
            "message_type": "private_message",
            "content": content,
            "timestamp": self._timestamp_provider(),
        }
        return self._save(message)

    def save_system_message(self, room_name: str, content: str) -> dict:
        message = {
            "room_name": room_name,
            "sender": "system",
            "receiver": None,
            "message_type": "system_message",
            "content": content,
            "timestamp": self._timestamp_provider(),
        }
        return self._save(message)

    def save_announcement(self, room_name: str, sender: str, content: str) -> dict:
        message = {
            "room_name": room_name,
            "sender": sender,
            "receiver": None,
            "message_type": "announcement",
            "content": content,
            "timestamp": self._timestamp_provider(),
        }
        return self._save(message)

    def save_feed_event(self, event_type: str, sender: str, content: str, room_name: str | None = None) -> dict:
        message = {
            "room_name": room_name,
            "sender": sender,
            "receiver": None,
            "message_type": event_type,
            "content": content,
            "timestamp": self._timestamp_provider(),
        }
        return self._save(message)

    def save_file_message(
        self,
        room_name: str | None,
        sender: str,
        content: str,
        attachment_id: str,
        receiver: str | None = None,
    ) -> tuple[bool, str, str, dict | None]:
        return self._save_uploaded_file_message(room_name, sender, content, receiver, attachment_id)

    def create_upload_ticket(self, uploaded_by: str, file_name: str, mime_type: str, file_size: int) -> tuple[bool, str, str, dict | None]:
        uploaded_by = str(uploaded_by or "").strip()
        clean_name = self._sanitize_file_name(file_name)
        try:
            expected_size = int(file_size)
        except (TypeError, ValueError):
            expected_size = 0
        if not uploaded_by:
            return False, "Uploader is required", "VALIDATION_ERROR", None
        if not clean_name:
            return False, "File name is required", "FILE_NAME_REQUIRED", None
        if expected_size <= 0:
            return False, "File data is invalid", "INVALID_FILE_DATA", None
        if expected_size > self._max_file_size:
            return False, "File is too large", "FILE_TOO_LARGE", None
        if not self._database_path:
            return False, "Upload tickets require database persistence", "UPLOAD_TICKET_UNAVAILABLE", None

        attachment_id = f"att-{uuid.uuid4().hex}"
        upload_token = secrets.token_urlsafe(32)
        created_at = self._timestamp_provider()
        with sqlite3.connect(self._database_path) as conn:
            conn.execute(
                """
                INSERT INTO pending_attachments (
                    attachment_id, uploaded_by, original_name, mime_type,
                    expected_size, upload_token, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attachment_id,
                    uploaded_by,
                    clean_name,
                    str(mime_type or "application/octet-stream"),
                    expected_size,
                    self._hash_download_token(upload_token),
                    created_at,
                ),
            )
        return True, "Upload ticket created", "OK", {
            "attachment_id": attachment_id,
            "upload_token": upload_token,
            "upload_url": "/attachments",
            "original_name": clean_name,
            "mime_type": str(mime_type or "application/octet-stream"),
            "max_file_size": self._max_file_size,
        }

    def save_uploaded_attachment(self, upload_token: str, file_name: str, mime_type: str, raw_bytes: bytes) -> tuple[bool, str, str, dict | None]:
        upload_token = str(upload_token or "").strip()
        raw_bytes = bytes(raw_bytes or b"")
        if not self._database_path:
            return False, "Upload tickets require database persistence", "UPLOAD_TICKET_UNAVAILABLE", None
        if not upload_token:
            return False, "Upload token is required", "VALIDATION_ERROR", None
        if not raw_bytes:
            return False, "File data is invalid", "INVALID_FILE_DATA", None
        if len(raw_bytes) > self._max_file_size:
            return False, "File is too large", "FILE_TOO_LARGE", None

        token_hash = self._hash_download_token(upload_token)
        with sqlite3.connect(self._database_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT attachment_id, uploaded_by, original_name, mime_type, expected_size, stored_name, used_at
                FROM pending_attachments
                WHERE upload_token = ?
                """,
                (token_hash,),
            ).fetchone()
            if row is None:
                return False, "Upload ticket not found", "UPLOAD_TICKET_NOT_FOUND", None
            if row["used_at"]:
                return False, "Attachment has already been used", "ATTACHMENT_ALREADY_USED", None
            if row["stored_name"]:
                return False, "Attachment has already been uploaded", "ATTACHMENT_ALREADY_UPLOADED", None
            if len(raw_bytes) != int(row["expected_size"]):
                return False, "Uploaded file size does not match ticket", "FILE_SIZE_MISMATCH", None

            clean_name = self._sanitize_file_name(file_name) or row["original_name"]
            suffix = Path(clean_name).suffix[:16]
            stored_name = f"{row['attachment_id']}{suffix}"
            path = self._upload_dir / stored_name
            path.write_bytes(raw_bytes)
            uploaded_at = self._timestamp_provider()
            conn.execute(
                """
                UPDATE pending_attachments
                SET original_name = ?, stored_name = ?, mime_type = ?, size = ?, uploaded_at = ?
                WHERE attachment_id = ?
                """,
                (
                    clean_name,
                    stored_name,
                    str(mime_type or row["mime_type"] or "application/octet-stream"),
                    len(raw_bytes),
                    uploaded_at,
                    row["attachment_id"],
                ),
            )

        return True, "Attachment uploaded", "OK", {
            "attachment_id": row["attachment_id"],
            "original_name": clean_name,
            "stored_name": stored_name,
            "mime_type": str(mime_type or row["mime_type"] or "application/octet-stream"),
            "size": len(raw_bytes),
            "uploaded_by": row["uploaded_by"],
        }

    def delete_message(self, message_id: str, deleted_by: str, role: str) -> tuple[bool, str, str, dict | None]:
        role = (role or "").strip().lower()
        if role != ROLE_ADMIN:
            return False, "Permission denied: only admin can delete messages", "PERMISSION_DENIED", None
        message_id = str(message_id or "").strip()
        if not message_id:
            return False, "Message id is required", "VALIDATION_ERROR", None
        if self._database_path:
            return self._delete_database_message(message_id, deleted_by)
        with self._lock:
            message = next((item for item in self._messages if item.get("message_id") == message_id), None)
            if message is None:
                return False, "Message not found", "MESSAGE_NOT_FOUND", None
            if message["message_type"] == "private_message":
                return False, "Private messages cannot be deleted by admin", "PRIVATE_MESSAGE_DELETE_DENIED", None
            if message["message_type"] not in DELETABLE_MESSAGE_TYPES:
                return False, "Only chat messages can be deleted", "MESSAGE_DELETE_NOT_ALLOWED", None
            if not message.get("deleted"):
                message["deleted"] = True
                message["deleted_by"] = deleted_by
                message["deleted_at"] = self._timestamp_provider()
                message["content"] = ""
            payload = self._sanitize_message(message)
        return True, "Message deleted", "OK", payload

    def _save_uploaded_file_message(
        self,
        room_name: str | None,
        sender: str,
        content: str,
        receiver: str | None,
        attachment_id: str,
    ) -> tuple[bool, str, str, dict | None]:
        if not self._database_path:
            return False, "Uploaded attachments require database persistence", "UPLOAD_TICKET_UNAVAILABLE", None
        pending = self._pending_attachment(attachment_id)
        if pending is None:
            return False, "Attachment not found", "ATTACHMENT_NOT_FOUND", None
        if pending["uploaded_by"] != sender:
            return False, "Permission denied: cannot use this attachment", "PERMISSION_DENIED", None
        if pending["used_at"]:
            return False, "Attachment has already been used", "ATTACHMENT_ALREADY_USED", None
        if not pending["stored_name"]:
            return False, "Attachment has not been uploaded", "ATTACHMENT_NOT_UPLOADED", None

        message = {
            "room_name": room_name,
            "sender": sender,
            "receiver": receiver,
            "message_type": "private_message" if receiver else "room_message",
            "content": str(content or "").strip(),
            "timestamp": self._timestamp_provider(),
        }
        saved = self._save(message)
        attachment = self._attach_pending_upload(saved["message_id"], pending)
        saved["attachment"] = attachment
        return True, "File message sent", "OK", saved

    def room_history(self, room_name: str, limit: int = 20) -> list[dict]:
        if self._database_path:
            placeholders = ",".join("?" for _ in ROOM_HISTORY_TYPES)
            return self._query_messages(
                f"room_name = ? AND message_type IN ({placeholders})",
                (room_name, *sorted(ROOM_HISTORY_TYPES)),
                limit,
            )
        with self._lock:
            room_messages = [
                self._with_reactions(message)
                for message in self._messages
                if message["room_name"] == room_name and message["message_type"] in ROOM_HISTORY_TYPES
            ]
        return room_messages[-limit:]

    def feed_history(self, limit: int = 50) -> list[dict]:
        if self._database_path:
            return self._query_messages("message_type != 'private_message'", (), limit)
        with self._lock:
            messages = [self._with_reactions(message) for message in self._messages if message["message_type"] not in FEED_EXCLUDED_TYPES]
        return messages[-limit:]

    def private_history(self, username_a: str, username_b: str, limit: int = 20) -> list[dict]:
        if self._database_path:
            return self._query_messages(
                "message_type = 'private_message' AND ((sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?))",
                (username_a, username_b, username_b, username_a),
                limit,
            )
        with self._lock:
            messages = [
                self._with_reactions(message)
                for message in self._messages
                if message["message_type"] == "private_message"
                and ((message["sender"] == username_a and message["receiver"] == username_b) or (message["sender"] == username_b and message["receiver"] == username_a))
            ]
        return messages[-limit:]

    def get_message(self, message_id: str) -> dict | None:
        message_id = str(message_id or "").strip()
        if not message_id:
            return None
        if self._database_path:
            with sqlite3.connect(self._database_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    """
                    SELECT id, message_id, room_name, sender, receiver, message_type, content, timestamp, deleted, deleted_by, deleted_at
                    FROM messages
                    WHERE message_id = ?
                    """,
                    (message_id,),
                ).fetchone()
            if row is None:
                return None
            return self._with_reactions(self._row_to_message(row))
        with self._lock:
            message = next((item for item in self._messages if item.get("message_id") == message_id), None)
            if message is None:
                return None
            return self._with_reactions(message)

    def toggle_reaction(self, message_id: str, username: str, emoji: str) -> tuple[bool, str, str, dict | None]:
        message_id = str(message_id or "").strip()
        username = str(username or "").strip()
        emoji = str(emoji or "").strip()
        if emoji not in ALLOWED_REACTIONS:
            return False, "Reaction is not available", "INVALID_REACTION", None
        message = self.get_message(message_id)
        if message is None:
            return False, "Message not found", "MESSAGE_NOT_FOUND", None
        if message.get("deleted"):
            return False, "Deleted messages cannot be reacted to", "MESSAGE_DELETED", None
        if self._database_path:
            return self._toggle_database_reaction(message_id, username, emoji)
        with self._lock:
            emoji_reactions = self._reactions.setdefault(message_id, {}).setdefault(emoji, set())
            if username in emoji_reactions:
                emoji_reactions.remove(username)
                active = False
            else:
                emoji_reactions.add(username)
                active = True
            if not emoji_reactions:
                self._reactions[message_id].pop(emoji, None)
            if not self._reactions.get(message_id):
                self._reactions.pop(message_id, None)
            reactions = self._reaction_summary(message_id)
        return True, "Reaction updated", "OK", {
            "message_id": message_id,
            "username": username,
            "emoji": emoji,
            "active": active,
            "reactions": reactions,
        }

    def attachment_download(self, attachment_id: str, token: str) -> tuple[bool, str, str, dict | None]:
        attachment_id = str(attachment_id or "").strip()
        token = str(token or "").strip()
        attachment = self._attachment_by_id(attachment_id)
        if attachment is None or not self._verify_download_token(token, attachment.get("download_token", "")):
            return False, "Attachment not found", "ATTACHMENT_FORBIDDEN", None
        message = self.get_message(attachment["message_id"])
        if message is None or message.get("deleted"):
            return False, "Attachment not found", "ATTACHMENT_FORBIDDEN", None
        path = (self._upload_dir / attachment["stored_name"]).resolve()
        try:
            path.relative_to(self._upload_dir.resolve())
        except ValueError:
            return False, "Attachment not found", "ATTACHMENT_FORBIDDEN", None
        if not path.is_file():
            return False, "Attachment not found", "ATTACHMENT_NOT_FOUND", None
        payload = attachment.copy()
        payload["path"] = str(path)
        return True, "Attachment ready", "OK", payload

    def _save(self, message: dict) -> dict:
        message.setdefault("deleted", False)
        message.setdefault("deleted_by", None)
        message.setdefault("deleted_at", None)
        with self._lock:
            if not self._database_path:
                message["message_id"] = f"msg-{self._next_message_id}"
                self._next_message_id += 1
                self._messages.append(message)
                return self._with_reactions(message)
        if self._database_path:
            with sqlite3.connect(self._database_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO messages (room_name, sender, receiver, message_type, content, timestamp, deleted, deleted_by, deleted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message["room_name"],
                        message["sender"],
                        message["receiver"],
                        message["message_type"],
                        message["content"],
                        message["timestamp"],
                        int(bool(message["deleted"])),
                        message["deleted_by"],
                        message["deleted_at"],
                    ),
                )
                message["message_id"] = f"msg-{cursor.lastrowid}"
                conn.execute("UPDATE messages SET message_id = ? WHERE id = ?", (message["message_id"], cursor.lastrowid))
        return self._with_reactions(message)

    def _query_messages(self, where_clause: str, params: tuple, limit: int) -> list[dict]:
        bounded_limit = max(1, min(int(limit), 200))
        with sqlite3.connect(self._database_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                SELECT id, message_id, room_name, sender, receiver, message_type, content, timestamp, deleted, deleted_by, deleted_at
                FROM messages
                WHERE {where_clause}
                ORDER BY id DESC
                LIMIT ?
                """,
                (*params, bounded_limit),
            ).fetchall()
        return [
            self._with_reactions(self._row_to_message(row))
            for row in reversed(rows)
        ]

    def _delete_database_message(self, message_id: str, deleted_by: str) -> tuple[bool, str, str, dict | None]:
        with sqlite3.connect(self._database_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, message_id, room_name, sender, receiver, message_type, content, timestamp, deleted, deleted_by, deleted_at
                FROM messages
                WHERE message_id = ?
                """,
                (message_id,),
            ).fetchone()
            if row is None:
                return False, "Message not found", "MESSAGE_NOT_FOUND", None
            message = self._row_to_message(row)
            if message["message_type"] == "private_message":
                return False, "Private messages cannot be deleted by admin", "PRIVATE_MESSAGE_DELETE_DENIED", None
            if message["message_type"] not in DELETABLE_MESSAGE_TYPES:
                return False, "Only chat messages can be deleted", "MESSAGE_DELETE_NOT_ALLOWED", None
            if not message["deleted"]:
                deleted_at = self._timestamp_provider()
                conn.execute(
                    """
                    UPDATE messages
                    SET deleted = 1, deleted_by = ?, deleted_at = ?, content = ''
                    WHERE message_id = ?
                    """,
                    (deleted_by, deleted_at, message_id),
                )
                message["deleted"] = True
                message["deleted_by"] = deleted_by
                message["deleted_at"] = deleted_at
                message["content"] = ""
        return True, "Message deleted", "OK", self._sanitize_message(message)

    def _toggle_database_reaction(self, message_id: str, username: str, emoji: str) -> tuple[bool, str, str, dict | None]:
        with sqlite3.connect(self._database_path) as conn:
            existing = conn.execute(
                """
                SELECT id
                FROM message_reactions
                WHERE message_id = ? AND username = ? AND emoji = ?
                """,
                (message_id, username, emoji),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    DELETE FROM message_reactions
                    WHERE message_id = ? AND username = ? AND emoji = ?
                    """,
                    (message_id, username, emoji),
                )
                active = False
            else:
                conn.execute(
                    """
                    INSERT INTO message_reactions (message_id, username, emoji, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (message_id, username, emoji, self._timestamp_provider()),
                )
                active = True
            reactions = self._database_reaction_summary(conn, message_id)
        return True, "Reaction updated", "OK", {
            "message_id": message_id,
            "username": username,
            "emoji": emoji,
            "active": active,
            "reactions": reactions,
        }

    def _row_to_message(self, row: sqlite3.Row) -> dict:
        return {
            "message_id": row["message_id"] or f"msg-{row['id']}",
            "room_name": row["room_name"],
            "sender": row["sender"],
            "receiver": row["receiver"],
            "message_type": row["message_type"],
            "content": row["content"],
            "timestamp": row["timestamp"],
            "deleted": bool(row["deleted"]),
            "deleted_by": row["deleted_by"],
            "deleted_at": row["deleted_at"],
        }

    def _sanitize_message(self, message: dict) -> dict:
        clean = message.copy()
        clean.setdefault("deleted", False)
        clean.setdefault("deleted_by", None)
        clean.setdefault("deleted_at", None)
        clean.setdefault("reactions", [])
        if clean.get("deleted"):
            clean["content"] = ""
        return clean

    def _with_reactions(self, message: dict) -> dict:
        clean = self._sanitize_message(message)
        clean["reactions"] = self._reaction_summary(clean["message_id"])
        clean["attachment"] = None if clean.get("deleted") else self._attachment_for_message(clean["message_id"])
        return clean

    def _sanitize_file_name(self, file_name: str) -> str:
        name = Path(str(file_name or "").replace("\\", "/")).name.strip()
        name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name)
        name = re.sub(r"\s+", "_", name).strip("._ ")
        return name[:120]

    def _pending_attachment(self, attachment_id: str) -> sqlite3.Row | None:
        if not self._database_path:
            return None
        with sqlite3.connect(self._database_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                """
                SELECT attachment_id, uploaded_by, original_name, stored_name, mime_type,
                       expected_size, size, created_at, uploaded_at, used_at
                FROM pending_attachments
                WHERE attachment_id = ?
                """,
                (str(attachment_id or "").strip(),),
            ).fetchone()

    def _attach_pending_upload(self, message_id: str, pending: sqlite3.Row) -> dict:
        token = secrets.token_urlsafe(24)
        token_hash = self._hash_download_token(token)
        created_at = self._timestamp_provider()
        with sqlite3.connect(self._database_path) as conn:
            conn.execute(
                """
                INSERT INTO message_attachments (
                    attachment_id, message_id, original_name, stored_name, mime_type,
                    size, uploaded_by, download_token, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pending["attachment_id"],
                    message_id,
                    pending["original_name"],
                    pending["stored_name"],
                    pending["mime_type"] or "application/octet-stream",
                    int(pending["size"]),
                    pending["uploaded_by"],
                    token_hash,
                    created_at,
                ),
            )
            conn.execute(
                "UPDATE pending_attachments SET used_at = ? WHERE attachment_id = ?",
                (created_at, pending["attachment_id"]),
            )
        return {
            "attachment_id": pending["attachment_id"],
            "message_id": message_id,
            "original_name": pending["original_name"],
            "stored_name": pending["stored_name"],
            "mime_type": pending["mime_type"] or "application/octet-stream",
            "size": int(pending["size"]),
            "uploaded_by": pending["uploaded_by"],
            "download_token": token_hash,
            "created_at": created_at,
            "download_url": f"/attachments/{pending['attachment_id']}?token={token}",
        }

    def _attachment_for_message(self, message_id: str) -> dict | None:
        if self._database_path:
            with sqlite3.connect(self._database_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    """
                    SELECT attachment_id, message_id, original_name, stored_name, mime_type,
                           size, uploaded_by, download_token, created_at
                    FROM message_attachments
                    WHERE message_id = ?
                    """,
                    (message_id,),
                ).fetchone()
            if row is None:
                return None
            return self._row_to_attachment(row)
        attachment = self._attachments.get(message_id)
        return attachment.copy() if attachment else None

    def _attachment_by_id(self, attachment_id: str) -> dict | None:
        if self._database_path:
            with sqlite3.connect(self._database_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    """
                    SELECT attachment_id, message_id, original_name, stored_name, mime_type,
                           size, uploaded_by, download_token, created_at
                    FROM message_attachments
                    WHERE attachment_id = ?
                    """,
                    (attachment_id,),
                ).fetchone()
            if row is None:
                return None
            return self._row_to_attachment(row)
        for attachment in self._attachments.values():
            if attachment.get("attachment_id") == attachment_id:
                return attachment.copy()
        return None

    def _row_to_attachment(self, row: sqlite3.Row) -> dict:
        return {
            "attachment_id": row["attachment_id"],
            "message_id": row["message_id"],
            "original_name": row["original_name"],
            "stored_name": row["stored_name"],
            "mime_type": row["mime_type"] or "application/octet-stream",
            "size": row["size"],
            "uploaded_by": row["uploaded_by"],
            "download_token": row["download_token"],
            "created_at": row["created_at"],
            "download_url": self._download_url_for_stored_token(row["attachment_id"], row["download_token"]),
        }

    def _hash_download_token(self, token: str) -> str:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"{DOWNLOAD_TOKEN_HASH_PREFIX}{digest}"

    def _verify_download_token(self, token: str, stored_token: str) -> bool:
        stored_token = str(stored_token or "")
        if stored_token.startswith(DOWNLOAD_TOKEN_HASH_PREFIX):
            return secrets.compare_digest(self._hash_download_token(token), stored_token)
        return secrets.compare_digest(stored_token, token)

    def _download_url_for_stored_token(self, attachment_id: str, stored_token: str) -> str | None:
        if str(stored_token or "").startswith(DOWNLOAD_TOKEN_HASH_PREFIX):
            return None
        return f"/attachments/{attachment_id}?token={stored_token}"

    def _reaction_summary(self, message_id: str) -> list[dict]:
        if self._database_path:
            with sqlite3.connect(self._database_path) as conn:
                return self._database_reaction_summary(conn, message_id)
        reactions = self._reactions.get(message_id, {})
        summary = []
        for emoji in REACTION_CHOICES:
            users = sorted(reactions.get(emoji, set()))
            if users:
                summary.append({"emoji": emoji, "count": len(users), "users": users})
        return summary

    def _database_reaction_summary(self, conn: sqlite3.Connection, message_id: str) -> list[dict]:
        rows = conn.execute(
            """
            SELECT emoji, username
            FROM message_reactions
            WHERE message_id = ?
            ORDER BY username ASC
            """,
            (message_id,),
        ).fetchall()
        grouped = {emoji: [] for emoji in REACTION_CHOICES}
        for emoji, username in rows:
            if emoji in grouped:
                grouped[emoji].append(username)
        return [
            {"emoji": emoji, "count": len(users), "users": users}
            for emoji, users in grouped.items()
            if users
        ]
