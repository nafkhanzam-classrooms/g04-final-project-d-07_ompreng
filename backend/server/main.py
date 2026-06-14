import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.server.services.auth import AuthService
from backend.server.core.certificate import ensure_certificates
from backend.server.core.database import Database
from backend.server.services.message import MessageService
from backend.server.transport.tcp.server import MBGServer

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MBG TCP chat server.")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host.")
    parser.add_argument("--port", default=5000, type=int, help="Server port.")
    parser.add_argument("--stats-interval", default=5.0, type=float, help="Seconds between performance stat lines. Use 0 to disable.")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL/TLS and run in plaintext.")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    database = Database()
    database.initialize()
    database.seed()
    auth = AuthService(str(database.path))
    messages = MessageService(database_path=str(database.path))
    server = MBGServer(auth=auth, messages=messages, database_path=str(database.path))
    use_ssl = not args.no_ssl
    certfile = keyfile = None
    if use_ssl:
        certfile, keyfile = ensure_certificates("data/server.crt", "data/server.key")
    server.serve_forever(args.host, args.port, args.stats_interval, use_ssl=use_ssl, certfile=certfile, keyfile=keyfile)

if __name__ == "__main__":
    main()

