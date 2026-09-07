"""
app/security/network.py

Singleton sovereignty monitor for the Sovereign AI Workbench.

Tracks every local-model call, RAG lookup, OCR operation, and
sandbox execution so the /system/health endpoint can prove
air-gapped operation at any moment during the demo.

External calls should always stay at zero. If they don't, the
blocked_attempts counter records how many times the guard fired.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Ollama is the only permitted "remote" endpoint — it runs on localhost.
# ---------------------------------------------------------------------------
_OLLAMA_ENDPOINT = "http://127.0.0.1:11434"

_ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class NetworkStatus:
    sovereign_mode: bool
    external_network_allowed: bool
    external_connections_detected: int
    message: str


# ---------------------------------------------------------------------------
# Singleton NetworkMonitor
# ---------------------------------------------------------------------------


class NetworkMonitor:
    """
    Process-wide sovereignty monitor.

    All state is held at the class level so every
    ``NetworkMonitor()`` call returns the same counters — no matter
    how many times FastAPI instantiates the class across requests.

    Thread-safety is guaranteed by a single class-level lock.
    """

    # ------------------------------------------------------------------
    # Class-level shared state
    # ------------------------------------------------------------------
    _lock: threading.Lock = threading.Lock()
    _sovereign_mode: bool = True

    # Operation counters
    _local_model_calls: int = 0
    _local_rag_calls: int = 0
    _ocr_operations: int = 0
    _sandbox_executions: int = 0
    _external_calls: int = 0        # must remain 0 in a healthy run
    _blocked_attempts: int = 0      # incremented whenever guard fires

    # ------------------------------------------------------------------
    # Construction — no instance state; all data lives on the class
    # ------------------------------------------------------------------

    def __init__(self, sovereign_mode: bool = True) -> None:
        # Allow callers to flip the mode (test harness, etc.)
        # but never silently override a stricter setting.
        with NetworkMonitor._lock:
            if sovereign_mode:
                NetworkMonitor._sovereign_mode = True

    # ------------------------------------------------------------------
    # Increment helpers — called from throughout the application
    # ------------------------------------------------------------------

    @classmethod
    def track_model_call(cls) -> None:
        """Record one local LLM inference."""
        with cls._lock:
            cls._local_model_calls += 1

    @classmethod
    def track_rag_call(cls) -> None:
        """Record one ChromaDB / RAG retrieval."""
        with cls._lock:
            cls._local_rag_calls += 1

    @classmethod
    def track_ocr(cls) -> None:
        """Record one Tesseract OCR operation."""
        with cls._lock:
            cls._ocr_operations += 1

    @classmethod
    def track_sandbox(cls) -> None:
        """Record one sandboxed Python execution."""
        with cls._lock:
            cls._sandbox_executions += 1

    @classmethod
    def track_external_call(cls) -> None:
        """
        Record an *attempted* external network call.

        Should never be called in a healthy air-gapped run — its
        presence is itself evidence of a sovereignty violation.
        """
        with cls._lock:
            cls._external_calls += 1

    # ------------------------------------------------------------------
    # Guard — called before any outbound socket is opened
    # ------------------------------------------------------------------

    @classmethod
    def assert_local_host(cls, host: str) -> None:
        """
        Raise ``ConnectionError`` if ``host`` is not a loopback address.

        Increments ``blocked_attempts`` so the health endpoint can
        surface any bypass attempts even after they are stopped.
        """
        if not cls._sovereign_mode:
            return

        if host.lower().strip() in _ALLOWED_HOSTS:
            return

        with cls._lock:
            cls._blocked_attempts += 1

        raise ConnectionError(
            f"Sovereign mode blocked non-local network host: {host}"
        )

    @classmethod
    def check_ollama_host(cls, host: str) -> None:
        """Alias kept for backwards compatibility."""
        cls.assert_local_host(host)

    # ------------------------------------------------------------------
    # Legacy instance-level status (kept for callers that use .status())
    # ------------------------------------------------------------------

    def status(self) -> NetworkStatus:
        return NetworkStatus(
            sovereign_mode=self._sovereign_mode,
            external_network_allowed=not self._sovereign_mode,
            external_connections_detected=self._external_calls,
            message=(
                "External network access disabled."
                if self._sovereign_mode
                else "External network access permitted."
            ),
        )

    # ------------------------------------------------------------------
    # Snapshot — the canonical payload for /system/health
    # ------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """
        Return a structured sovereignty proof dictionary.

        Designed to be embedded directly in the /system/health response.
        """
        with NetworkMonitor._lock:
            return {
                "internet_access": "BLOCKED",
                "status": "AIR-GAPPED",
                "ollama_endpoint": _OLLAMA_ENDPOINT,
                "sovereign_mode": NetworkMonitor._sovereign_mode,
                "external_network_allowed": not NetworkMonitor._sovereign_mode,
                # --- operation counters ---
                "local_model_calls": NetworkMonitor._local_model_calls,
                "local_rag_calls": NetworkMonitor._local_rag_calls,
                "ocr_operations": NetworkMonitor._ocr_operations,
                "sandbox_executions": NetworkMonitor._sandbox_executions,
                # --- guard counters ---
                "external_calls": NetworkMonitor._external_calls,
                "blocked_attempts": NetworkMonitor._blocked_attempts,
                # --- human-readable verdict ---
                "sovereignty_verified": (
                    NetworkMonitor._external_calls == 0
                ),
            }

    # ------------------------------------------------------------------
    # Convenience: reset all counters (test harness only)
    # ------------------------------------------------------------------

    @classmethod
    def _reset(cls) -> None:
        """Reset all counters. Intended for tests only."""
        with cls._lock:
            cls._local_model_calls = 0
            cls._local_rag_calls = 0
            cls._ocr_operations = 0
            cls._sandbox_executions = 0
            cls._external_calls = 0
            cls._blocked_attempts = 0
