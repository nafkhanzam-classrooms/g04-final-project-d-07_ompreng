import time
from collections import deque
from threading import Event, Lock, Thread

class StatsReporter:
    def __init__(self) -> None:
        self.stats_lock = Lock()
        self.stats_stop = Event()
        self.stats = {
            "started_at": time.monotonic(),
            "active_connections": 0,
            "total_connections": 0,
            "total_requests": 0,
            "total_errors": 0,
            "total_response_time_ms": 0.0,
            "max_response_time_ms": 0.0,
            "bytes_received": 0,
            "bytes_sent": 0,
        }
        self.recent_requests = deque()

    def start(self, interval: float) -> None:
        if interval <= 0:
            return
        thread = Thread(target=self._stats_reporter, args=(interval,), daemon=True)
        thread.start()

    def _stats_reporter(self, interval: float) -> None:
        while not self.stats_stop.wait(interval):
            snapshot = self.performance_snapshot()
            print(
                "[PERF] "
                f"uptime={snapshot['uptime_seconds']:.0f}s "
                f"active={snapshot['active_connections']} "
                f"conn_total={snapshot['total_connections']} "
                f"requests={snapshot['total_requests']} "
                f"rps={snapshot['requests_per_second']:.2f} "
                f"recent_rps={snapshot['recent_requests_per_second']:.2f} "
                f"error_rate={snapshot['error_rate_percent']:.2f}% "
                f"recent_error_rate={snapshot['recent_error_rate_percent']:.2f}% "
                f"avg_rt={snapshot['average_response_time_ms']:.2f}ms "
                f"max_rt={snapshot['max_response_time_ms']:.2f}ms "
                f"in={snapshot['bytes_received']}B "
                f"out={snapshot['bytes_sent']}B",
                flush=True,
            )

    def performance_snapshot(self) -> dict:
        now = time.monotonic()
        with self.stats_lock:
            uptime = max(now - float(self.stats["started_at"]), 0.001)
            total_requests = int(self.stats["total_requests"])
            total_errors = int(self.stats["total_errors"])
            while self.recent_requests and now - self.recent_requests[0][0] > 10:
                self.recent_requests.popleft()
            recent_requests = len(self.recent_requests)
            recent_errors = sum(1 for _, failed in self.recent_requests if failed)
            average_response_time = (
                float(self.stats["total_response_time_ms"]) / total_requests
                if total_requests
                else 0.0
            )
            return {
                "uptime_seconds": uptime,
                "active_connections": int(self.stats["active_connections"]),
                "total_connections": int(self.stats["total_connections"]),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate_percent": (total_errors / total_requests * 100) if total_requests else 0.0,
                "requests_per_second": total_requests / uptime,
                "recent_requests_per_second": recent_requests / 10,
                "recent_error_rate_percent": (recent_errors / recent_requests * 100) if recent_requests else 0.0,
                "average_response_time_ms": average_response_time,
                "max_response_time_ms": float(self.stats["max_response_time_ms"]),
                "bytes_received": int(self.stats["bytes_received"]),
                "bytes_sent": int(self.stats["bytes_sent"]),
            }

    def record_connection_opened(self) -> None:
        with self.stats_lock:
            self.stats["active_connections"] += 1
            self.stats["total_connections"] += 1

    def record_connection_closed(self) -> None:
        with self.stats_lock:
            self.stats["active_connections"] = max(0, int(self.stats["active_connections"]) - 1)

    def record_bytes_received(self, size: int) -> None:
        with self.stats_lock:
            self.stats["bytes_received"] += size

    def record_bytes_sent(self, size: int) -> None:
        with self.stats_lock:
            self.stats["bytes_sent"] += size

    def record_request(self, elapsed_ms: float, failed: bool) -> None:
        now = time.monotonic()
        with self.stats_lock:
            self.stats["total_requests"] += 1
            if failed:
                self.stats["total_errors"] += 1
            self.stats["total_response_time_ms"] += elapsed_ms
            self.stats["max_response_time_ms"] = max(float(self.stats["max_response_time_ms"]), elapsed_ms)
            self.recent_requests.append((now, failed))

    def stop(self) -> None:
        self.stats_stop.set()
