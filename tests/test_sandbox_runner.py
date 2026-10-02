import io
import subprocess
from pathlib import Path

from sandbox.runner import run_validation


def test_docker_arguments_are_isolated_and_cleanup_runs(monkeypatch, tmp_path):
    calls = []

    class Process:
        returncode = 0
        stdout = io.BytesIO(b"Ran 5 tests in 0.01s\nOK\n")
        def wait(self, timeout):
            return 0

    def launch(args, **kwargs):
        calls.append(args)
        assert "shell" not in kwargs
        return Process()

    monkeypatch.setattr("sandbox.runner.shutil.which", lambda _: "docker")
    monkeypatch.setattr("sandbox.runner.subprocess.Popen", launch)
    monkeypatch.setattr("sandbox.runner.subprocess.run", lambda args, **kwargs: calls.append(args))
    result = run_validation(tmp_path, "python-unittest")
    assert result.status == "passed"
    command = calls[0]
    for flag in ["--network=none", "--read-only", "--pull=never", "--cap-drop=ALL", "--memory=256m", "--pids-limit=64", "--user=65534:65534"]:
        assert flag in command
    assert any("target=/workspace,readonly" in arg for arg in command)
    assert calls[-1][1:3] == ["rm", "-f"]


def test_timeout_output_cap_and_container_cleanup(monkeypatch, tmp_path):
    calls = []

    class Process:
        returncode = -1
        stdout = io.BytesIO(b"x" * 200000)
        killed = False
        def wait(self, timeout):
            if not self.killed:
                raise subprocess.TimeoutExpired("docker", timeout)
        def kill(self):
            self.killed = True

    monkeypatch.setattr("sandbox.runner.shutil.which", lambda _: "docker")
    monkeypatch.setattr("sandbox.runner.subprocess.Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr("sandbox.runner.subprocess.run", lambda args, **kwargs: calls.append(args))
    result = run_validation(tmp_path, "python-unittest", timeout=1)
    assert result.status == "timeout"
    assert len(result.output) < 66000
    assert calls[-1][1:3] == ["rm", "-f"]
