import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def main():
    print("Building frontend...")
    pnpm = "pnpm.cmd" if sys.platform == "win32" else "pnpm"
    build = subprocess.run([pnpm, "run", "build"], cwd=FRONTEND)
    if build.returncode != 0:
        print("Frontend build failed.")
        return

    print("Starting TCP server on port 5000...")
    server = subprocess.Popen(
        [sys.executable, "backend/server/main.py", "--host", "0.0.0.0", "--port", "5000"],
        cwd=ROOT,
    )
    time.sleep(0.5)

    print("Starting web bridge on port 8000...")
    bridge = subprocess.Popen(
        [sys.executable, "backend/server/web_bridge.py", "--host", "0.0.0.0", "--port", "8000"],
        cwd=ROOT,
    )

    local_ip = get_local_ip()
    print()
    print("MBG running at https://localhost:8000")
    print(f"To access from other device on the same LAN: https://{local_ip}:8000")
    print("Press Ctrl+C to stop.")
    print()

    try:
        while server.poll() is None and bridge.poll() is None:
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass

    for p in [server, bridge]:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()


if __name__ == "__main__":
    main()
