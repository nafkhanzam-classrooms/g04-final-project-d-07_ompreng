import json
import socket
from urllib.parse import urlparse

def send_response(sock: socket.socket, status: int, body: bytes, content_type: str) -> None:
    reason = {
        200: "OK",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        413: "Payload Too Large",
        500: "Internal Server Error",
    }.get(status, "OK")
    headers = (
        f"HTTP/1.1 {status} {reason}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    )
    try:
        sock.sendall(headers.encode("ascii") + body)
    except OSError:
        pass

def send_json_response(sock: socket.socket, status: int, payload: dict) -> None:
    send_response(sock, status, json.dumps(payload).encode("utf-8"), "application/json")

def read_http_request(sock: socket.socket, max_upload_body_size: int) -> tuple[str, str, dict[str, str], bytes] | None:
    data = b""
    while b"\r\n\r\n" not in data and len(data) < 16384:
        try:
            chunk = sock.recv(1024)
        except OSError:
            return None
        if not chunk:
            return None
        data += chunk
    head = data.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")
    lines = head.split("\r\n")
    if not lines:
        return None
    parts = lines[0].split()
    if len(parts) < 2:
        return None
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    body = data.split(b"\r\n\r\n", 1)[1]
    try:
        content_length = int(headers.get("content-length", "0"))
    except ValueError:
        content_length = 0
    if parts[0] == "POST" and urlparse(parts[1]).path == "/attachments" and content_length > max_upload_body_size:
        send_json_response(sock, 413, {"success": False, "message": "File is too large", "payload": {"code": "FILE_TOO_LARGE"}})
        return None
    while len(body) < content_length:
        try:
            chunk = sock.recv(min(65536, content_length - len(body)))
        except OSError:
            break
        if not chunk:
            break
        body += chunk
    return parts[0], parts[1], headers, body
