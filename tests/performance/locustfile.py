import json
import os
import socket
import ssl
import time
import uuid
from itertools import count

from locust import User, between, events, task

try:
    import psutil
except ImportError:
    psutil = None


MBG_HOST = os.getenv("MBG_HOST", "127.0.0.1")
MBG_PORT = int(os.getenv("MBG_PORT", "5000"))
MBG_USE_SSL = os.getenv("MBG_USE_SSL", "1").lower() not in {"0", "false", "no"}
MBG_ROOM = os.getenv("MBG_ROOM", "general")
REQUEST_TIMEOUT = float(os.getenv("MBG_LOCUST_TIMEOUT", "5"))

class MbgTcpClient:
    def __init__(self, host: str, port: int, use_ssl: bool = False) -> None:
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.sock: socket.socket | None = None
        self.buffer = b""
        self.request_counter = count(1)

    def connect(self) -> None:
        raw = socket.create_connection((self.host, self.port), timeout=REQUEST_TIMEOUT)
        raw.settimeout(REQUEST_TIMEOUT)
        if self.use_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.sock = context.wrap_socket(raw, server_hostname=self.host)
        else:
            self.sock = raw

    def close(self) -> None:
        if self.sock is None:
            return
        try:
            self.sock.close()
        finally:
            self.sock = None

    def request(self, command_type: str, payload: dict | None = None) -> dict:
        if self.sock is None:
            self.connect()

        request_id = f"locust-{next(self.request_counter)}"
        message = {
            "type": command_type,
            "request_id": request_id,
            "payload": payload or {},
        }
        encoded = (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")
        started_at = time.perf_counter()
        response_length = 0

        try:
            assert self.sock is not None
            self.sock.sendall(encoded)
            while True:
                response = self._read_json_line()
                response_length += len(json.dumps(response, separators=(",", ":")))
                if response.get("request_id") != request_id:
                    continue

                elapsed_ms = (time.perf_counter() - started_at) * 1000
                success = response.get("success") is not False and response.get("type") != "error"
                events.request.fire(
                    request_type="TCP",
                    name=command_type,
                    response_time=elapsed_ms,
                    response_length=response_length,
                    exception=None if success else RuntimeError(response.get("message", "Request failed")),
                )
                return response
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            events.request.fire(
                request_type="TCP",
                name=command_type,
                response_time=elapsed_ms,
                response_length=response_length,
                exception=exc,
            )
            self.close()
            raise

    def _read_json_line(self) -> dict:
        while b"\n" not in self.buffer:
            assert self.sock is not None
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("MBG server closed the connection")
            self.buffer += chunk

        line, self.buffer = self.buffer.split(b"\n", 1)
        if not line.strip():
            return {}
        return json.loads(line.decode("utf-8"))


class MbgTcpUser(User):
    wait_time = between(0.15, 1.0)

    def on_start(self) -> None:
        self.username = f"load_{uuid.uuid4().hex[:18]}"
        self.password = "load123"
        self.client = MbgTcpClient(MBG_HOST, MBG_PORT, MBG_USE_SSL)
        self.client.connect()

        self._safe_request("register", {
            "username": self.username,
            "password": self.password,
            "role": "student",
        })
        login = self._safe_request("login", {
            "username": self.username,
            "password": self.password,
        })
        if login.get("success") is False:
            raise RuntimeError(login.get("message", "Login failed"))

        self._safe_request("join_room", {"room_name": MBG_ROOM})

    def on_stop(self) -> None:
        try:
            self._safe_request("logout")
        finally:
            self.client.close()

    def _safe_request(self, command_type: str, payload: dict | None = None) -> dict:
        try:
            return self.client.request(command_type, payload)
        except Exception:
            return {"success": False}

    @task(8)
    def ping(self) -> None:
        self.client.request("ping")

    @task(5)
    def room_list(self) -> None:
        self.client.request("room_list")

    @task(4)
    def online_users(self) -> None:
        self.client.request("online_users")

    @task(3)
    def feed_history(self) -> None:
        self.client.request("feed_history", {"limit": 20})

    @task(2)
    def chat_history(self) -> None:
        self.client.request("chat_history", {"room_name": MBG_ROOM, "limit": 20})

    @task(1)
    def send_room_message(self) -> None:
        self.client.request("send_room_message", {
            "room_name": MBG_ROOM,
            "content": f"load test message from {self.username}",
        })


@events.quitting.add_listener
def print_mbg_summary(environment, **kwargs) -> None:
    stats = environment.stats.total
    total = max(stats.num_requests, 1)
    failures = stats.num_failures
    error_rate = failures / total * 100

    print()
    print("=== MBG Locust Summary ===")
    print(f"Target: {MBG_HOST}:{MBG_PORT}")
    print(f"Users: {environment.runner.user_count if environment.runner else 0}")
    print(f"Requests: {stats.num_requests}")
    print(f"Failures: {failures}")
    print(f"Error rate: {error_rate:.2f}%")
    print(f"Average response time: {stats.avg_response_time:.2f} ms")
    print(f"P95 response time: {stats.get_response_time_percentile(0.95):.2f} ms")
    print(f"P99 response time: {stats.get_response_time_percentile(0.99):.2f} ms")
    print(f"Throughput: {stats.total_rps:.2f} req/s")
    if psutil is not None:
        process = psutil.Process(os.getpid())
        print(f"Locust CPU: {process.cpu_percent(interval=0.1):.2f}%")
        print(f"Locust memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
