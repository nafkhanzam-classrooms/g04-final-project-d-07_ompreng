import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse
from backend.server.transport.web.config import WEB_ROOT

def serve_static(target: str, send_response_func: any) -> None:
    target = urlparse(target).path
    if target == "/":
        target = "/index.html"
    path = (WEB_ROOT / unquote(target.lstrip("/"))).resolve()
    if WEB_ROOT not in path.parents and path != WEB_ROOT:
        send_response_func(403, b"Forbidden", "text/plain")
        return
    if not path.is_file():
        send_response_func(404, b"Not found", "text/plain")
        return
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    send_response_func(200, path.read_bytes(), content_type)
