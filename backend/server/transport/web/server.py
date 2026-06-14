import os
import ssl
import socket
from socketserver import BaseRequestHandler, ThreadingTCPServer
from urllib.parse import urlparse
from backend.server.core.certificate import ensure_certificates
from backend.server.transport.web.config import config, ROOT
from backend.server.transport.web.router import read_http_request, send_response, send_json_response
from backend.server.transport.web.attachment import handle_attachment_upload, serve_attachment
from backend.server.transport.web.static import serve_static
from backend.server.transport.web.websocket import handle_websocket

class WebBridgeHandler(BaseRequestHandler):
    def setup(self) -> None:
        self.handshake_failed = False
        if config.use_ssl and config.ssl_context:
            self.request.settimeout(5.0)
            try:
                first_byte = self.request.recv(1, socket.MSG_PEEK)
                if first_byte and first_byte[0] != 22:
                    data = b""
                    while b"\r\n\r\n" not in data and len(data) < 4096:
                        chunk = self.request.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                    host = "127.0.0.1:8000"
                    path = "/"
                    if data:
                        lines = data.decode("iso-8859-1").split("\r\n")
                        if lines:
                            parts = lines[0].split()
                            if len(parts) >= 2:
                                path = parts[1]
                        for line in lines:
                            if ":" in line:
                                k, v = line.split(":", 1)
                                if k.strip().lower() == "host":
                                    host = v.strip()
                    redirect_url = f"https://{host}{path}"
                    body = f"Redirecting to {redirect_url}...".encode("utf-8")
                    response = (
                        "HTTP/1.1 301 Moved Permanently\r\n"
                        f"Location: {redirect_url}\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(body)}\r\n"
                        "Connection: close\r\n\r\n"
                    ).encode("ascii") + body
                    self.request.sendall(response)
                    self.handshake_failed = True
                    try:
                        self.request.close()
                    except OSError:
                        pass
                    return
            except OSError:
                pass
            try:
                self.request = config.ssl_context.wrap_socket(self.request, server_side=True)
                self.request.settimeout(None)
            except (ssl.SSLError, OSError):
                self.handshake_failed = True
                try:
                    self.request.close()
                except OSError:
                    pass
                return
        super().setup()

    def handle(self) -> None:
        if self.handshake_failed:
            return
        request = read_http_request(self.request, config.max_upload_body_size)
        if request is None:
            return
        method, target, headers, body = request
        if method == "POST" and urlparse(target).path == "/attachments":
            handle_attachment_upload(
                headers,
                body,
                config.database_path,
                config.upload_dir,
                lambda status, payload: send_json_response(self.request, status, payload)
            )
            return
        if method != "GET":
            send_response(self.request, 405, b"Method not allowed", "text/plain")
            return
        if target == "/ws":
            handle_websocket(
                self.request,
                headers,
                config.mbg_host,
                config.mbg_port,
                config.use_ssl,
                config.ssl_client_context,
                lambda status, body, ct: send_response(self.request, status, body, ct)
            )
            return
        if urlparse(target).path.startswith("/attachments/"):
            serve_attachment(
                target,
                config.database_path,
                config.upload_dir,
                lambda status, body, ct: send_response(self.request, status, body, ct)
            )
            return
        serve_static(
            target,
            lambda status, body, ct: send_response(self.request, status, body, ct)
        )

def start_server(host: str, port: int, mbg_host: str, mbg_port: int, no_ssl: bool) -> None:
    use_ssl = not no_ssl
    ssl_context = None
    ssl_client_context = None
    if use_ssl:
        certfile, keyfile = ensure_certificates("data/server.crt", "data/server.key")
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        ssl_client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_client_context.check_hostname = False
        ssl_client_context.verify_mode = ssl.CERT_NONE

    config.mbg_host = mbg_host
    config.mbg_port = mbg_port
    config.use_ssl = use_ssl
    config.ssl_context = ssl_context
    config.ssl_client_context = ssl_client_context

    os.chdir(ROOT)
    with ThreadingTCPServer((host, port), WebBridgeHandler) as server:
        server.daemon_threads = True
        scheme = "https" if use_ssl else "http"
        print(f"MBG web UI running at {scheme}://{host}:{port}")
        print(f"Forwarding browser clients to {mbg_host}:{mbg_port}")
        server.serve_forever()
