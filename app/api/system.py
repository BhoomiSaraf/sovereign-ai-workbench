"""
app/api/system.py

Comprehensive system health endpoint for the Sovereign AI Workbench.

GET /system/health performs real, live checks against every
dependency and returns a single structured JSON response that
proves air-gapped operation for the SIH 2026 demo.

Every check is fully isolated — one failing dependency cannot
raise an unhandled exception or prevent other checks from running.
"""

from __future__ import annotations

import subprocess
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.security.network import NetworkMonitor

router = APIRouter(
    prefix="/system",
    tags=["system"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OLLAMA_BASE = "http://127.0.0.1:11434"
_OLLAMA_HEALTH_URL = f"{_OLLAMA_BASE}/api/tags"
_HTTP_TIMEOUT = 3  # seconds — tight enough for a localhost call


# ---------------------------------------------------------------------------
# Individual health-check helpers
# Each returns a dict and never raises.
# ---------------------------------------------------------------------------


def _check_backend() -> dict[str, Any]:
    """The backend is trivially healthy if this code is running."""
    return {"ok": True}


def _check_ollama() -> dict[str, Any]:
    """
    Hit GET /api/tags on the local Ollama daemon.

    Returns the list of downloaded models when reachable, otherwise
    returns ok=False with a human-readable error string.
    """
    try:
        req = urllib.request.Request(
            _OLLAMA_HEALTH_URL,
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            import json

            body: dict = json.loads(resp.read().decode())

        raw_models: list[dict] = body.get("models", [])

        # Normalise: keep only the name (and size if present).
        models = [
            {
                "name": m.get("name", "unknown"),
                "size_gb": (
                    round(m["size"] / 1_073_741_824, 2)
                    if m.get("size")
                    else None
                ),
            }
            for m in raw_models
        ]

        return {
            "ok": True,
            "endpoint": _OLLAMA_BASE,
            "models_available": len(models),
            "models": models,
        }

    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "endpoint": _OLLAMA_BASE,
            "error": f"Ollama unreachable: {exc.reason}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "endpoint": _OLLAMA_BASE,
            "error": str(exc),
        }


def _check_chromadb() -> dict[str, Any]:
    """
    Instantiate a ChromaStore and call .count().

    A successful count (even zero) proves the client and the
    on-disk collection are readable.
    """
    try:
        from app.rag.store import ChromaStore

        store = ChromaStore()
        count = store.count()

        return {
            "ok": True,
            "collection": "knowledge",
            "chunks_stored": count,
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
        }


def _check_docker() -> dict[str, Any]:
    """
    Verify the Docker daemon is reachable.

    Tries the Python SDK first; falls back to ``docker info`` via
    subprocess so the check works regardless of whether the SDK is
    installed.
    """
    # --- attempt 1: Python SDK ---
    try:
        import docker  # type: ignore[import]

        client = docker.from_env()
        client.ping()
        info = client.info()
        return {
            "ok": True,
            "driver": info.get("Driver", "unknown"),
            "containers_running": info.get("ContainersRunning", 0),
        }
    except ImportError:
        pass  # SDK not installed — fall through to subprocess
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
        }

    # --- attempt 2: subprocess fallback ---
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return {
                "ok": True,
                "server_version": result.stdout.strip(),
            }
        return {
            "ok": False,
            "error": result.stderr.strip() or "docker info returned non-zero exit",
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "Docker CLI not found in PATH",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "Docker daemon timed out",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
        }


def _check_tesseract() -> dict[str, Any]:
    """
    Run ``tesseract --version`` to confirm the OCR engine is installed.
    """
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # First line is e.g. "tesseract 5.3.1"
            version_line = (result.stdout or result.stderr).splitlines()[0].strip()
            return {
                "ok": True,
                "version": version_line,
            }
        return {
            "ok": False,
            "error": result.stderr.strip() or "tesseract returned non-zero exit",
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "Tesseract not found in PATH",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "tesseract --version timed out",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
        }


def _check_network() -> dict[str, Any]:
    """Return the live sovereignty snapshot from the singleton monitor."""
    try:
        return NetworkMonitor().snapshot()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/health")
def system_health() -> JSONResponse:
    """
    Comprehensive air-gapped system health check.

    Performs live status checks against every runtime dependency and
    returns a single JSON object.  The overall ``healthy`` flag is
    True only when the backend, Ollama, and ChromaDB are all up.
    Docker and Tesseract are reported but do not affect the flag —
    they may legitimately be absent in some deployment configurations.

    Response shape
    --------------
    {
        "healthy": true,
        "components": {
            "backend":   { "ok": true },
            "ollama":    { "ok": true, "models": [...], ... },
            "vector_db": { "ok": true, "chunks_stored": N },
            "docker":    { "ok": true | false, ... },
            "tesseract": { "ok": true, "version": "tesseract 5.x" },
            "network":   { "status": "AIR-GAPPED", ... }
        }
    }
    """
    backend = _check_backend()
    ollama = _check_ollama()
    vector_db = _check_chromadb()
    docker = _check_docker()
    tesseract = _check_tesseract()
    network = _check_network()

    # Core services that must be up for the workbench to be usable.
    core_ok = (
        backend.get("ok", False)
        and ollama.get("ok", False)
        and vector_db.get("ok", False)
    )

    payload: dict[str, Any] = {
        "healthy": core_ok,
        "components": {
            "backend": backend,
            "ollama": ollama,
            "vector_db": vector_db,
            "docker": docker,
            "tesseract": tesseract,
            "network": network,
        },
    }

    # Use 200 even when core_ok is False so the UI always receives a
    # parseable body rather than a 5xx that triggers generic error handling.
    return JSONResponse(content=payload, status_code=200)
