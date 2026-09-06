import time
import docker

class DockerSandbox:
    """
    Air-gapped execution sandbox using Docker.
    Runs Python code strictly isolated from the host OS and network.
    """

    def __init__(self, image: str = "python:3.13-slim"):
        self.image = image
        try:
            self.client = docker.from_env()
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Docker client. Is Docker running? Error: {exc}")

    def execute_code(self, code: str, timeout: int = 10) -> str:
        """
        Executes the provided Python code in a secure Docker container.
        
        Args:
            code (str): The Python code to run.
            timeout (int): Maximum execution time in seconds.
            
        Returns:
            str: The stdout/stderr output or error trace.
        """
        container = None
        try:
            # Launch container in detached mode to allow timeout monitoring
            container = self.client.containers.run(
                image=self.image,
                command=["python", "-c", code],
                network_disabled=True,      # Strict network isolation
                mem_limit="512m",           # Prevent memory exhaustion
                detach=True,
            )
            
            # Wait for execution to finish or enforce timeout
            start_time = time.time()
            while True:
                container.reload()
                if container.status == "exited":
                    break
                
                if time.time() - start_time > timeout:
                    container.kill()
                    return f"ExecutionTimeoutError: Code execution exceeded {timeout} seconds and was killed."
                
                time.sleep(0.1)

            # Capture logs (both stdout and stderr)
            logs = container.logs(stdout=True, stderr=True)
            return logs.decode("utf-8").strip()

        except Exception as exc:
            # Return the error trace gracefully instead of crashing the backend
            return f"SandboxExecutionError: {str(exc)}"
            
        finally:
            # Ensure container is destroyed even if errors occur
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
