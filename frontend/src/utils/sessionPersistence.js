const SESSION_STORAGE_KEY = "mbg.session";

export function readStoredSession() {
  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function writeStoredSession(user) {
  if (!user?.session_token) return;
  window.sessionStorage.setItem(
    SESSION_STORAGE_KEY,
    JSON.stringify({
      username: user.username,
      role: user.role,
      session_token: user.session_token,
    }),
  );
}

export function clearStoredSession() {
  window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
}
