import sqlite3
from contextlib import closing
from pathlib import Path
from typing import NamedTuple
from backend.server.core.security import hash_password, ROLE_ADMIN, ROLE_STUDENT, ROLE_TEACHER

class DemoUser(NamedTuple):
    username: str
    password: str
    role: str

DEFAULT_DEMO_USERS = (
    DemoUser("admin", "admin123", ROLE_ADMIN),
    DemoUser("teacher1", "teacher123", ROLE_TEACHER),
    DemoUser("teacher2", "teacher123", ROLE_TEACHER),
    DemoUser("student1", "student123", ROLE_STUDENT),
    DemoUser("student2", "student123", ROLE_STUDENT),
)

class Database:
    def __init__(self, path: str = "data/mbg.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def initialize(self) -> None:
        with closing(self.connect()) as conn:
            with conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS rooms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room_name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_by TEXT,
                        managed_by TEXT,
                        source_request_id INTEGER,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS room_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room_name TEXT NOT NULL,
                        username TEXT NOT NULL,
                        role TEXT,
                        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(room_name, username)
                    );
                    CREATE TABLE IF NOT EXISTS room_requests (
                        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room_name TEXT NOT NULL,
                        description TEXT,
                        requested_by TEXT NOT NULL,
                        requester_role TEXT NOT NULL,
                        purpose TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        reviewed_by TEXT,
                        rejection_reason TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        reviewed_at TEXT
                    );
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id TEXT UNIQUE,
                        room_name TEXT,
                        sender TEXT NOT NULL,
                        receiver TEXT,
                        message_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        deleted INTEGER DEFAULT 0,
                        deleted_by TEXT,
                        deleted_at TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_messages_message_id
                        ON messages(message_id);
                    CREATE INDEX IF NOT EXISTS idx_messages_room_history
                        ON messages(room_name, message_type, id);
                    CREATE INDEX IF NOT EXISTS idx_messages_private_history
                        ON messages(message_type, sender, receiver, id);
                    CREATE INDEX IF NOT EXISTS idx_messages_feed_history
                        ON messages(message_type, id);
                    CREATE TABLE IF NOT EXISTS message_reactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        emoji TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(message_id, username, emoji)
                    );
                    CREATE INDEX IF NOT EXISTS idx_message_reactions_message
                        ON message_reactions(message_id);
                    CREATE TABLE IF NOT EXISTS message_attachments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        attachment_id TEXT UNIQUE NOT NULL,
                        message_id TEXT NOT NULL,
                        original_name TEXT NOT NULL,
                        stored_name TEXT NOT NULL,
                        mime_type TEXT,
                        size INTEGER NOT NULL,
                        uploaded_by TEXT NOT NULL,
                        download_token TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_message_attachments_message
                        ON message_attachments(message_id);
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_message_attachments_attachment
                        ON message_attachments(attachment_id);
                    CREATE TABLE IF NOT EXISTS pending_attachments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        attachment_id TEXT UNIQUE NOT NULL,
                        uploaded_by TEXT NOT NULL,
                        original_name TEXT NOT NULL,
                        stored_name TEXT,
                        mime_type TEXT,
                        expected_size INTEGER NOT NULL,
                        size INTEGER DEFAULT 0,
                        upload_token TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        uploaded_at TEXT,
                        used_at TEXT
                    );
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_attachments_attachment
                        ON pending_attachments(attachment_id);
                    CREATE INDEX IF NOT EXISTS idx_pending_attachments_token
                        ON pending_attachments(upload_token);
                    CREATE TABLE IF NOT EXISTS server_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        username TEXT,
                        description TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

    def seed(self) -> None:
        with closing(self.connect()) as conn:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        password = excluded.password,
                        role = excluded.role
                    """,
                    [
                        (user.username, hash_password(user.password), user.role)
                        for user in DEFAULT_DEMO_USERS
                    ],
                )
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO rooms (room_name, description, created_by)
                    VALUES (?, ?, ?)
                    """,
                    [
                        ("progjar", "Network Programming class", "teacher1"),
                        ("general", "General discussion", "admin"),
                    ],
                )
