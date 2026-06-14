import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(ROOT))

from backend.server.transport.web.server import start_server

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the MBG browser UI and WebSocket bridge.")
    parser.add_argument("--host", default="127.0.0.1", help="Web UI bind host.")
    parser.add_argument("--port", default=8000, type=int, help="Web UI port.")
    parser.add_argument("--mbg-host", default="127.0.0.1", help="MBG TCP server host.")
    parser.add_argument("--mbg-port", default=5000, type=int, help="MBG TCP server port.")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL/TLS and run in plaintext.")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    start_server(
        host=args.host,
        port=args.port,
        mbg_host=args.mbg_host,
        mbg_port=args.mbg_port,
        no_ssl=args.no_ssl
    )

if __name__ == "__main__":
    main()


