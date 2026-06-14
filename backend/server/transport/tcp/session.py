import secrets

class SessionManager:
    def __init__(self, server) -> None:
        self.server = server

    def session_for(self, client) -> dict | None:
        with self.server.state_lock:
            return self.server.sessions.get(client)

    def issue_session_token(self, user: dict[str, str]) -> str:
        token = secrets.token_urlsafe(32)
        self.server.session_tokens[token] = {"username": user["username"], "role": user["role"]}
        return token

    def attach_session(self, client, address, user: dict[str, str], token: str) -> None:
        for existing_client, session in list(self.server.sessions.items()):
            if existing_client is not client and session.get("username") == user["username"]:
                self.server.sessions.pop(existing_client, None)
        self.server.sessions[client] = {"username": user["username"], "role": user["role"], "session_token": token}
        self.server.online_users[user["username"]] = {"socket": client, "address": address, "role": user["role"]}
