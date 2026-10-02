import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

from backend.models import Validation
from workspace.secret_filter import SecretFilter


RUNNERS = {
    "python-unittest": ("codeproof-python:1", ["python", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]),
    "python-pytest": ("codeproof-python:1", ["python", "-B", "-m", "pytest", "-p", "no:cacheprovider", "-v"]),
    "node-test": ("codeproof-node:1", ["node", "--test"]),
}


def run_validation(copy: Path, runner: str, timeout: int = 60) -> Validation:
    docker = shutil.which("docker")
    if not docker:
        return Validation(status="unavailable", output="Docker is not installed or is not on PATH. No code was executed.")
    image, command = RUNNERS[runner]
    name = "codeproof-" + uuid.uuid4().hex
    # There is no writable bind mount, host shell, network, socket, or implicit pull.
    args = [docker, "run", "--rm", "--pull=never", "--name", name,
            "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--pids-limit=64",
            "--memory=256m", "--memory-swap=256m", "--cpus=1",
            "--user=65534:65534", "--log-driver=none",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
            "--mount", f"type=bind,source={copy.resolve()},target=/workspace,readonly",
            "--workdir=/workspace", "--env=HOME=/tmp", "--env=PYTHONDONTWRITEBYTECODE=1",
            image, *command]
    chunks: list[bytes] = []
    retained = 0
    started = time.monotonic()
    process = None
    reader = None
    timed_out = False
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        def drain():
            nonlocal retained
            while data := process.stdout.read(4096):
                if retained < 65536:
                    part = data[:65536 - retained]
                    chunks.append(part)
                    retained += len(part)

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait(timeout=5)
    except OSError:
        return Validation(status="unavailable", output="Docker could not start. Check Docker Desktop and the prepared runner image.")
    finally:
        # Always remove the named container, including when docker's client times out.
        try:
            subprocess.run([docker, "rm", "-f", name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, subprocess.TimeoutExpired):
            pass
        if reader:
            reader.join(timeout=2)
    output = SecretFilter().redact_content(b"".join(chunks).decode("utf-8", errors="replace"))
    if retained >= 65536:
        output += "\n[Output capped at 64 KiB]"
    status = "timeout" if timed_out else "passed" if process.returncode == 0 else "failed"
    # A successful process with no tests is not evidence of passing tests.
    if status == "passed" and ("Ran 0 tests" in output or "# tests 0" in output or not output.strip()):
        status = "failed"
        output += "\nNo test evidence was collected."
    return Validation(status=status, output=output or "Runner produced no output.",
                      duration_ms=round((time.monotonic() - started) * 1000),
                      checks=["Network disabled", "Read-only filesystem", "CPU / memory / PID limits", "Temporary copy only"])
