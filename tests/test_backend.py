import difflib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.models import Validation
from backend.patching import apply_diff, safe_path
from backend.service import SAMPLE, LOGIN, GOOD, BAD
from workspace import WorkspaceGuardian

TOKEN = "test-pairing-token-for-local-api-only-000000"


@pytest.fixture
def client():
    with TestClient(create_app(TOKEN)) as value:
        value.headers["Authorization"] = "Bearer " + TOKEN
        yield value


def open_sample(client):
    response = client.post("/v1/sessions", json={})
    assert response.status_code == 200, response.text
    return response.json()


def test_authentication_and_browser_origin_rejected(client):
    assert client.post("/v1/sessions", json={}, headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.post("/v1/sessions", json={}, headers={"Origin": "https://attacker.example"}).status_code == 403
    assert client.get("/health", headers={"Host": "attacker.example"}).status_code == 400


def test_full_sample_flow_preserves_original_and_cleans_copy(client, monkeypatch):
    before = (SAMPLE / LOGIN).read_bytes()
    opened = open_sample(client)
    base = "/v1/sessions/" + opened["id"]
    assert client.post(base + "/patch", json={}).status_code == 400
    challenge = client.post(base + "/challenge", json={}).json()
    assert BAD in challenge["files"][LOGIN]
    assert client.post(base + "/challenge", json={}).status_code == 400
    for level in range(1, 5):
        assert len(client.post(base + "/hint", json={}).json()["hints"]) == level
    assert client.post(base + "/hint", json={}).status_code == 409
    rejected = client.post(base + "/explanation", json={"explanation": "The database might be slow."}).json()
    assert not rejected["evaluation"]["passed"]
    assert rejected["patch"] is None
    explained = client.post(base + "/explanation", json={"explanation": "The client sends email but the handler expects username, a field mismatch."}).json()
    assert explained["phase"] == "review"
    assert "+    body: JSON.stringify({ username" in explained["patch"]["diff"]
    applied = client.post(base + "/patch", json={}).json()
    assert GOOD in applied["files"][LOGIN]
    assert applied["phase"] == "applied"
    assert client.post(base + "/patch", json={}).status_code == 400
    copied_paths = []

    def validate(copy, runner):
        copied_paths.append(copy)
        assert copy.resolve() != SAMPLE.resolve()
        assert GOOD in (copy / LOGIN).read_text()
        return Validation(status="passed", output="5 tests passed")

    monkeypatch.setattr("backend.app.run_validation", validate)
    validated = client.post(base + "/validation", json={"runner": "python-unittest"}).json()
    assert validated["phase"] == "validated"
    assert validated["validation"]["original_unchanged"] is True
    assert client.get(base + "/report").json()["validation"]["status"] == "passed"
    assert (SAMPLE / LOGIN).read_bytes() == before
    assert client.delete(base).status_code == 200
    assert not copied_paths[0].exists()
    assert client.get(base + "/report").status_code == 404


def test_local_project_filters_secrets_and_ai_is_opt_in(client, tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("print('hello')\n")
    (tmp_path / ".env").write_text("API_KEY=private\n")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    state = client.post("/v1/sessions", json={"path": str(tmp_path)}).json()
    assert state["files"] == {"main.py": "print('hello')\n"}
    assert state["provider"] == "Local inspection"
    base = "/v1/sessions/" + state["id"]
    assert client.post(base + "/analysis", json={"use_ai": True}).status_code == 503
    assert client.post(base + "/challenge", json={"issue": "Crashes", "target_file": "../outside.py"}).status_code == 400
    assert client.post(base + "/validation", json={"runner": "cmd /c whoami"}).status_code == 422


def test_unavailable_docker_is_never_a_pass(client, monkeypatch):
    monkeypatch.setattr("sandbox.runner.shutil.which", lambda _: None)
    state = open_sample(client)
    result = client.post(f'/v1/sessions/{state["id"]}/validation', json={}).json()
    assert result["validation"]["status"] == "unavailable"
    assert result["phase"] != "validated"


def test_external_change_blocks_readiness(client, tmp_path, monkeypatch):
    source = tmp_path / "main.py"
    source.write_text("print('before')\n")
    state = client.post("/v1/sessions", json={"path": str(tmp_path)}).json()
    source.write_text("print('external change')\n")
    monkeypatch.setattr("backend.app.run_validation", lambda *args: Validation(status="passed", output="1 test passed"))
    result = client.post(f'/v1/sessions/{state["id"]}/validation', json={}).json()
    assert result["validation"]["original_unchanged"] is False


@pytest.mark.parametrize("path", ["../outside.py", "/etc/passwd", "C:/file.py", "a\\b", ".env", "a/../b", "a//b", "CON.py", "a.", "NUL"])
def test_unsafe_patch_paths_rejected(path):
    with pytest.raises(ValueError):
        safe_path(path)


def test_patch_is_atomic_and_rejects_stale_context():
    files = {"a.py": "one\ntwo\n", "b.py": "old\n"}
    diff = "".join(difflib.unified_diff(files["a.py"].splitlines(True), "one\nthree\n".splitlines(True), fromfile="a/a.py", tofile="b/a.py"))
    assert apply_diff(files, diff, ["a.py"])["a.py"] == "one\nthree\n"
    with pytest.raises(ValueError):
        apply_diff(files, diff.replace("-two", "-stale"), ["a.py"])
    with pytest.raises(ValueError):
        apply_diff(files, diff, ["b.py"])
    assert files["a.py"] == "one\ntwo\n"


def test_linked_files_are_not_read(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("private outside content")
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").write_text("print('safe')")
    try:
        (project / "link.py").symlink_to(outside)
    except OSError:
        pytest.skip("Windows symlink permission not enabled")
    guardian = WorkspaceGuardian(str(project))
    assert "link.py" not in guardian.create_snapshot().files
    with pytest.raises(ValueError):
        guardian.read_file("link.py")


def test_session_limit_and_input_bounds(client):
    for _ in range(8):
        open_sample(client)
    assert client.post("/v1/sessions", json={}).status_code == 409
    assert client.post("/v1/sessions", json={"path": "x" * 5000}).status_code == 422
