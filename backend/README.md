# CodeProof local service

Requires Python 3.11+ (validated with Python 3.12) and Windows 10/11.
From the repository root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.venv\Scripts\python.exe -m backend
```

Keep that terminal running. Copy the generated **local pairing token** into the
desktop's **Connect your project** dialog. Enter an absolute project directory;
leave the directory blank to use the bundled sample with real backend services.
The token authenticates access to your local files; do not share it.

The initial analysis is local filename/type inspection. To enable AI, set
`OPENROUTER_API_KEY` and `CODEPROOF_MODEL` in the backend process environment before
starting it. Choose an available model on your OpenRouter account. Click
**Analyze with AI** in the app and review the content-sharing confirmation.
The backend does not automatically load `.env` files.

## Docker validation

Install and start Docker Desktop in Linux-container mode. Explicitly prepare
the trusted runner images (this build step downloads dependencies):

```powershell
docker build -t codeproof-python:1 -f sandbox/Dockerfile.python sandbox
docker build -t codeproof-node:1 -f sandbox/Dockerfile.node sandbox
```

Validation never installs dependencies or pulls an image automatically. The
Python image includes unittest and pytest. The Node image supports built-in
`node --test`. Projects needing additional packages need a reviewed runner image
prepared by the backend owner. Redacted source-only snapshots can be incomplete
for builds that depend on binaries, assets, ignored files, or secrets.

The app sends a runner identifier, never a command. The runner executes only
inside Docker with network disabled, read-only root and project mount, dropped
capabilities, no new privileges, a non-root user, and CPU/memory/PID/time limits.
Writable temporary space is limited to a 64 MiB tmpfs; output is capped at 64 KiB.
Containers use `--rm`, with forced cleanup attempted in every exit path.

Patch application accepts exact existing-file unified diffs against approved
targets. It rejects traversal, drive paths, reserved Windows names, renames,
deletions, hidden files, stale context, and new-file patches. Unsupported patches
fail visibly. Copy the reviewed diff for manual adoption; the service never
writes it into the original project.

## Verification

```powershell
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe scripts\verify_desktop_api.py
```

The second check uses the real Dart HTTP client against an ephemeral backend and
requires Flutter/Dart on PATH. It does not contact an AI provider. Docker tests
are attempted only through the constrained runner.

See `docs/DESKTOP_API_V1.md` for the additive API contract and session lifecycle.
