import ssl
from dataclasses import dataclass
from pathlib import Path
from backend.server.services.message import DEFAULT_MAX_FILE_SIZE

ROOT = Path(__file__).resolve().parents[4]
WEB_ROOT = ROOT / "frontend" / "dist"
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MULTIPART_OVERHEAD_LIMIT = 1024 * 1024

@dataclass
class BridgeConfig:
    mbg_host: str = "127.0.0.1"
    mbg_port: int = 5000
    database_path: str = "data/mbg.db"
    upload_dir: str = "data/uploads"
    max_upload_body_size: int = DEFAULT_MAX_FILE_SIZE + MULTIPART_OVERHEAD_LIMIT
    use_ssl: bool = False
    ssl_context: ssl.SSLContext | None = None
    ssl_client_context: ssl.SSLContext | None = None

config = BridgeConfig()
