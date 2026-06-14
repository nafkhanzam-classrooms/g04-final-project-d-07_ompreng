import json
from typing import Any

DEFAULT_MAX_LINE_BYTES = 8 * 1024 * 1024

def encode_message(message: dict[str, Any]) -> bytes:
    return (json.dumps(message) + "\n").encode("utf-8")

def decode_message(line: str | bytes) -> dict[str, Any]:
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    try:
        decoded = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON") from exc
    if not isinstance(decoded, dict):
        raise ValueError("JSON message must be an object")
    return decoded

class JSONLineBuffer:
    def __init__(self, max_line_bytes: int = DEFAULT_MAX_LINE_BYTES) -> None:
        self._buffer = b""
        self._max_line_bytes = max_line_bytes

    def feed(self, data: bytes) -> list[dict[str, Any]]:
        self._buffer += data
        if len(self._buffer) > self._max_line_bytes and b"\n" not in self._buffer:
            self._buffer = b""
            raise ValueError("JSON message is too large")

        messages: list[dict[str, Any]] = []
        while b"\n" in self._buffer:
            raw_line, self._buffer = self._buffer.split(b"\n", 1)
            if not raw_line.strip():
                continue
            if len(raw_line) > self._max_line_bytes:
                raise ValueError("JSON message is too large")
            messages.append(decode_message(raw_line))
        return messages

def success_response(response_type: str, request_id: str | None, message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "type": response_type,
        "request_id": request_id,
        "success": True,
        "message": message,
        "payload": payload or {},
    }

def error_response(request_id: str | None, message: str, code: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    error_payload = {"code": code}
    if payload:
        error_payload.update(payload)
    return {
        "type": "error",
        "request_id": request_id,
        "success": False,
        "message": message,
        "payload": error_payload,
    }
