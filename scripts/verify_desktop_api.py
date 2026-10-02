"""Development smoke test: run the actual Dart client against an ephemeral API."""
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

root = Path(__file__).resolve().parent.parent
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
env = os.environ.copy()
env["CODEPROOF_TOKEN"] = secrets.token_urlsafe(32)
env["CODEPROOF_TEST_PORT"] = str(port)
dart = shutil.which("dart")
if not dart:
    raise SystemExit("Dart SDK must be on PATH")
native_dart = Path(dart).parent / "cache" / "dart-sdk" / "bin" / "dart.exe"
if native_dart.exists():
    dart = str(native_dart)
flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
server = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app:create_app", "--factory",
    "--host", "127.0.0.1", "--port", str(port), "--no-access-log"], cwd=root, env=env,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
try:
    for attempt in range(50):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(.1)
    else:
        raise RuntimeError("Test backend failed to start")
    result = subprocess.run([dart, "--suppress-analytics", "run", "tool/smoke_backend.dart"], cwd=root / "desktop", env=env,
                            timeout=180, creationflags=flags, capture_output=True, text=True)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
finally:
    server.terminate()
    server.wait(timeout=10)
