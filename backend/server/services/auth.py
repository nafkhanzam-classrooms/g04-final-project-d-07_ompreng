from pathlib import Path
import re
import sqlite3
from backend.server.core.database import DEFAULT_DEMO_USERS, DemoUser as User
from backend.server.core.security import hash_password, verify_password, CLIENT_ROLES, ROLE_STUDENT

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,24}$")

class AuthService:
    def __init__(self, database_path: str | None = None) -> None:
        self.database_path = Path(database_path) if database_path else None
        self._users: dict[str, User] = {}
        self._load_registered_users()
        if not self._users:
            for u in DEFAULT_DEMO_USERS:
                self._users[u.username] = User(u.username, hash_password(u.password), u.role)

    def login(self, username: str, password: str) -> dict[str, str] | None:
        user = self._users.get(username)
        if not user or not verify_password(password, user.password):
            return None
        return {"username": user.username, "role": user.role}

    def register(self, username: str, password: str, role: str = ROLE_STUDENT) -> tuple[bool, str, str | None, dict[str, str]]:
        username = username.strip()
        role = (role or ROLE_STUDENT).strip().lower()
        if not USERNAME_PATTERN.fullmatch(username):
            return False, "Username must be 3-24 characters and use only letters, numbers, or underscores", "INVALID_USERNAME", {}
        if len(password) < 6:
            return False, "Password must be at least 6 characters", "INVALID_PASSWORD", {}
        if role not in CLIENT_ROLES:
            return False, "Role must be student or teacher", "INVALID_ROLE", {}
        if username in self._users:
            return False, "Username is already registered", "USERNAME_TAKEN", {}
        password_hash = hash_password(password)
        self._users[username] = User(username, password_hash, role)
        self._save_registered_user(username, password_hash, role)
        return True, "Registration successful", None, {"username": username, "role": role}

    def exists(self, username: str) -> bool:
        return username in self._users

    def role_for(self, username: str) -> str | None:
        user = self._users.get(username)
        return user.role if user else None

    def _load_registered_users(self) -> bool:
        if self.database_path is None or not self.database_path.exists():
            return False
        conn = None
        try:
            conn = sqlite3.connect(self.database_path)
            rows = conn.execute("SELECT username, password, role FROM users").fetchall()
        except sqlite3.Error:
            return False
        finally:
            if conn is not None:
                conn.close()
        for username, password, role in rows:
            self._users[username] = User(username, password, role)
        return True

    def _save_registered_user(self, username: str, password: str, role: str) -> None:
        if self.database_path is None:
            return
        conn = sqlite3.connect(self.database_path)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role),
            )
            conn.commit()
        finally:
            conn.close()
