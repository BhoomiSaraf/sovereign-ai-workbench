from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    success: bool
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False


class PythonSandbox:
    """
    Executes generated Python inside a Docker container.

    Security properties for the MVP:
    - network disabled
    - read-only container filesystem
    - temporary working directory
    - memory limit
    - CPU limit
    - execution timeout
    """

    def __init__(
        self,
        image: str = "python:3.11-slim",
        timeout_seconds: int = 10,
        memory: str = "512m",
        cpus: str = "1.0",
    ):
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.memory = memory
        self.cpus = cpus

    def execute(self, code: str) -> SandboxResult:
        if not code or not code.strip():
            raise ValueError("Code cannot be empty.")

        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            script = workdir / "main.py"
            script.write_text(code, encoding="utf-8")

            command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--memory",
                self.memory,
                "--cpus",
                self.cpus,
                "--pids-limit",
                "64",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "-v",
                f"{workdir}:/workspace:rw",
                "-w",
                "/workspace",
                self.image,
                "python",
                "main.py",
            ]

            try:
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )

                return SandboxResult(
                    success=process.returncode == 0,
                    stdout=process.stdout,
                    stderr=process.stderr,
                    return_code=process.returncode,
                )

            except subprocess.TimeoutExpired as exc:
                return SandboxResult(
                    success=False,
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                    return_code=-1,
                    timed_out=True,
                )