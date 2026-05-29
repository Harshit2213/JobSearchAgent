import logging

from fastapi import HTTPException

from backends.circuit_breaker import CircuitBreaker
from utils.config import settings

logger = logging.getLogger(__name__)

# HTTP status codes that indicate Anthropic is unavailable and should trip the circuit.
_TRIP_CODES = {401, 402, 429, 503, 502}


class BackendRouter:
    """
    Strategy + Circuit Breaker.

    quality="high"  → AnthropicBackend (primary), GroqBackend (fallback when circuit open)
    quality="fast"  → GroqBackend directly, no circuit breaker
    """

    def __init__(self) -> None:
        from backends.anthropic_backend import AnthropicBackend
        from backends.groq_backend import GroqBackend

        self._anthropic = AnthropicBackend() if settings.anthropic_api_key else None
        self._groq      = GroqBackend()      if settings.groq_api_key      else None

        if not self._anthropic and not self._groq:
            raise RuntimeError("At least one LLM backend must be configured (ANTHROPIC_API_KEY or GROQ_API_KEY).")

        self._circuit = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_threshold,
            recovery_timeout=settings.circuit_breaker_timeout,
        )

    # ── internal ──────────────────────────────────────────────────────────────

    def _fast_backend(self):
        """Return the fast backend, falling back to Anthropic if Groq isn't configured."""
        return self._groq or self._anthropic

    def _high_backend(self):
        """Return the high-quality backend, falling back to Groq if Anthropic isn't configured."""
        return self._anthropic or self._groq

    def _should_fallback(self, exc: HTTPException) -> bool:
        return exc.status_code in _TRIP_CODES and self._groq is not None

    # ── public interface ──────────────────────────────────────────────────────

    def complete(self, quality: str, **kwargs) -> dict:
        if quality == "fast" or not self._circuit.allows_request:
            return self._fast_backend().complete(**kwargs)

        try:
            result = self._high_backend().complete(**kwargs)
            self._circuit.record_success()
            return result
        except HTTPException as exc:
            if self._should_fallback(exc):
                self._circuit.record_failure()
                logger.warning(
                    "Anthropic unavailable (HTTP %s), circuit=%s — falling back to Groq: %s",
                    exc.status_code, self._circuit.state, exc.detail,
                )
                return self._fast_backend().complete(**kwargs)
            raise

    async def acomplete(self, quality: str, **kwargs) -> dict:
        if quality == "fast" or not self._circuit.allows_request:
            return await self._fast_backend().acomplete(**kwargs)

        try:
            result = await self._high_backend().acomplete(**kwargs)
            self._circuit.record_success()
            return result
        except HTTPException as exc:
            if self._should_fallback(exc):
                self._circuit.record_failure()
                logger.warning(
                    "Anthropic unavailable (HTTP %s), circuit=%s — falling back to Groq: %s",
                    exc.status_code, self._circuit.state, exc.detail,
                )
                return await self._fast_backend().acomplete(**kwargs)
            raise


# ── module-level singleton ────────────────────────────────────────────────────
_router: BackendRouter | None = None


def get_router() -> BackendRouter:
    global _router
    if _router is None:
        _router = BackendRouter()
    return _router
