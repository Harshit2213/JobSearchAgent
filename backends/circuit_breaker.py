import threading
import time


class CircuitBreaker:
    """
    Three-state machine: CLOSED → OPEN → HALF_OPEN → CLOSED.

    CLOSED    Normal operation — requests go through.
    OPEN      Too many failures — requests are blocked, fallback is used.
    HALF_OPEN Recovery probe — one request is allowed through to test the primary.
    """

    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self._state     = self.CLOSED
        self._failures  = 0
        self._opened_at: float | None = None
        self._lock      = threading.Lock()

    # ── state property (handles OPEN → HALF_OPEN transition) ─────────────────

    @property
    def state(self) -> str:
        with self._lock:
            if (
                self._state == self.OPEN
                and self._opened_at is not None
                and time.monotonic() - self._opened_at >= self.recovery_timeout
            ):
                self._state = self.HALF_OPEN
            return self._state

    @property
    def allows_request(self) -> bool:
        return self.state in (self.CLOSED, self.HALF_OPEN)

    # ── outcome recording ─────────────────────────────────────────────────────

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state    = self.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold or self._state == self.HALF_OPEN:
                self._state     = self.OPEN
                self._opened_at = time.monotonic()
