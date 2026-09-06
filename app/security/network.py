from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkStatus:
    sovereign_mode: bool
    external_network_allowed: bool
    external_connections_detected: int
    message: str


class NetworkMonitor:
    """
    Application-level sovereignty monitor.

    The MVP runs in sovereign mode and rejects attempts by
    application components to resolve/connect to external hosts
    through this controlled interface.

    This complements OS/firewall isolation; it is not a replacement
    for an actual air-gapped network.
    """

    def __init__(self, sovereign_mode: bool = True):
        self.sovereign_mode = sovereign_mode
        self.external_connections_detected = 0

    def status(self) -> NetworkStatus:
        return NetworkStatus(
            sovereign_mode=self.sovereign_mode,
            external_network_allowed=not self.sovereign_mode,
            external_connections_detected=self.external_connections_detected,
            message=(
                "External network access disabled."
                if self.sovereign_mode
                else "External network access permitted."
            ),
        )

    def assert_local_host(self, host: str) -> None:
        if not self.sovereign_mode:
            return

        normalized = host.lower().strip()

        allowed = {
            "localhost",
            "127.0.0.1",
            "::1",
        }

        if normalized in allowed:
            return

        # Ollama and other explicitly local services may use localhost
        # only in sovereign mode.
        self.external_connections_detected += 1

        raise ConnectionError(
            f"Sovereign mode blocked non-local network host: {host}"
        )

    def check_ollama_host(self, host: str) -> None:
        self.assert_local_host(host)

    def snapshot(self) -> dict:
        result = self.status()

        return {
            "sovereign_mode": result.sovereign_mode,
            "external_network_allowed": result.external_network_allowed,
            "external_connections_detected": (
                result.external_connections_detected
            ),
            "message": result.message,
        }