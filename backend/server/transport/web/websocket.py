import base64
import hashlib
import json
import socket
import struct
from threading import Event, Thread
from typing import Any
from backend.server.transport.web.config import GUID

def handle_websocket(client_sock: socket.socket, headers: dict[str, str], mbg_host: str, mbg_port: int, use_ssl: bool, ssl_client_context: Any, send_response_func: Any) -> None:
    key = headers.get("sec-websocket-key")
    if not key:
        send_response_func(400, b"Missing WebSocket key", "text/plain")
        return
    accept = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest()).decode("ascii")
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    )
    client_sock.sendall(response.encode("ascii"))

    stop = Event()
    try:
        raw = socket.create_connection((mbg_host, mbg_port), timeout=5)
        if use_ssl and ssl_client_context:
            upstream = ssl_client_context.wrap_socket(raw, server_hostname=mbg_host)
        else:
            upstream = raw
        with upstream:
            upstream.settimeout(0.25)
            reader = Thread(target=tcp_to_ws, args=(client_sock, upstream, stop), daemon=True)
            reader.start()
            ws_to_tcp(client_sock, upstream, stop)
    except OSError as exc:
        send_ws_text(client_sock, {"type": "error", "success": False, "message": f"Cannot reach MBG server: {exc}", "payload": {"code": "BRIDGE_CONNECT_FAILED"}})
    finally:
        stop.set()

def tcp_to_ws(client_sock: socket.socket, upstream: socket.socket, stop: Event) -> None:
    buffer = b""
    while not stop.is_set():
        try:
            chunk = upstream.recv(4096)
        except socket.timeout:
            continue
        except OSError:
            break
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            if line.strip():
                send_ws_bytes(client_sock, line)
    stop.set()

def ws_to_tcp(client_sock: socket.socket, upstream: socket.socket, stop: Event) -> None:
    while not stop.is_set():
        frame = read_ws_message(client_sock)
        if frame is None:
            break
        opcode, payload = frame
        if opcode == 0x8:
            break
        if opcode == 0x9:
            send_ws_frame(client_sock, payload, 0xA)
            continue
        if opcode != 0x1:
            continue
        try:
            json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            send_ws_text(client_sock, {"type": "error", "success": False, "message": "Invalid JSON", "payload": {"code": "INVALID_JSON"}})
            continue
        upstream.sendall(payload + b"\n")
    stop.set()

def read_ws_message(client_sock: socket.socket) -> tuple[int, bytes] | None:
    frame = read_ws_frame(client_sock)
    if frame is None:
        return None
    final, opcode, payload = frame
    if opcode in {0x8, 0x9, 0xA} or final:
        return opcode, payload
    if opcode != 0x1:
        return opcode, payload

    chunks = [payload]
    while True:
        frame = read_ws_frame(client_sock)
        if frame is None:
            return None
        final, opcode, payload = frame
        if opcode == 0x9:
            send_ws_frame(client_sock, payload, 0xA)
            continue
        if opcode == 0x8:
            return opcode, payload
        if opcode != 0x0:
            return opcode, payload
        chunks.append(payload)
        if final:
            return 0x1, b"".join(chunks)

def read_ws_frame(client_sock: socket.socket) -> tuple[bool, int, bytes] | None:
    header = recv_exact(client_sock, 2)
    if not header:
        return None
    first, second = header
    final = bool(first & 0x80)
    opcode = first & 0x0F
    masked = second & 0x80
    length = second & 0x7F
    if length == 126:
        length_bytes = recv_exact(client_sock, 2)
        if not length_bytes:
            return None
        length = struct.unpack("!H", length_bytes)[0]
    elif length == 127:
        length_bytes = recv_exact(client_sock, 8)
        if not length_bytes:
            return None
        length = struct.unpack("!Q", length_bytes)[0]
    mask = recv_exact(client_sock, 4) if masked else b""
    if masked and not mask:
        return None
    payload = recv_exact(client_sock, length)
    if payload is None:
        return None
    if masked:
        payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return final, opcode, payload

def recv_exact(client_sock: socket.socket, size: int) -> bytes | None:
    data = b""
    while len(data) < size:
        try:
            chunk = client_sock.recv(size - len(data))
        except OSError:
            return None
        if not chunk:
            return None
        data += chunk
    return data

def send_ws_text(client_sock: socket.socket, message: dict[str, Any]) -> None:
    send_ws_bytes(client_sock, json.dumps(message).encode("utf-8"))

def send_ws_bytes(client_sock: socket.socket, payload: bytes) -> None:
    send_ws_frame(client_sock, payload, 0x1)

def send_ws_frame(client_sock: socket.socket, payload: bytes, opcode: int) -> None:
    try:
        if len(payload) < 126:
            header = struct.pack("!BB", 0x80 | opcode, len(payload))
        elif len(payload) <= 65535:
            header = struct.pack("!BBH", 0x80 | opcode, 126, len(payload))
        else:
            header = struct.pack("!BBQ", 0x80 | opcode, 127, len(payload))
        client_sock.sendall(header + payload)
    except OSError:
        pass
