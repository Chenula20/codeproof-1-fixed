import asyncio
import difflib
import hashlib
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from workspace import WorkspaceGuardian
from workspace.models import ProjectSnapshot
from .models import Evaluation, PatchView, SessionView, Skill, Validation
from .patching import apply_diff, safe_path

SAMPLE = Path(__file__).resolve().parent.parent / "demo-project"
LOGIN = "src/frontend/login.js"
GOOD = "{ username: username, password }"
BAD = "{ email: username, password }"
HINTS = [
    "Trace the data crossing the login boundary. Does validation fail before the password is checked?",
    "Compare the browser login request with the authentication handler that receives it.",
    "The handler reads username. Inspect the key in the JSON request body in login.js.",
    "The challenge sends email while the handler requires username. Restore the username key and test valid, invalid, and missing credentials.",
]


@dataclass
class Session:
    guardian: WorkspaceGuardian
    snapshot: ProjectSnapshot
    view: SessionView
    temp: tempfile.TemporaryDirectory
    original_hashes: dict[str, str]
    created: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    use_ai: bool = False

    @property
    def copy(self) -> Path:
        return Path(self.temp.name) / "project"

    def write_copy(self, files: dict[str, str]):
        for name, content in files.items():
            target = self.copy / safe_path(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            # Contents came through Guardian and are intentionally redacted.
            target.write_text(content, encoding="utf-8", newline="")

    def original_unchanged(self) -> bool:
        # Re-index original files through Guardian; compare hashes, never write.
        current = {f.path.replace("\\", "/"): f.hash for f in self.guardian.list_files(force_refresh=True)}
        return current == self.original_hashes

    def close(self):
        self.temp.cleanup()


def inspect_snapshot(snapshot: ProjectSnapshot) -> tuple[list[str], list[Skill], list[str]]:
    files = list(snapshot.files)
    extensions = {Path(p).suffix for p in files}
    technologies = [name for extension, name in [(".py", "Python"), (".js", "JavaScript"),
                    (".ts", "TypeScript"), (".dart", "Dart / Flutter"), (".rs", "Rust"), (".go", "Go")]
                    if extension in extensions]
    skills = []
    for category, words in [("Debugging", ["handler", "error", "main"]), ("API", ["api", "route", "http"]),
                            ("Database", ["database", "repository", "model"]),
                            ("Authentication", ["auth", "login"]), ("Testing", ["test", "spec"]),
                            ("Error Handling", ["error", "handler", "exception"])]:
        evidence = [p for p in files if any(word in p.lower() for word in words)][:4]
        skills.append(Skill(category=category, relevance=min(.95, .35 + .15 * len(evidence)) if evidence else .1,
                            confidence=.65 if evidence else .2, evidence=evidence))
    issues = ["Review request validation, error paths, and test coverage.",
              "Local inspection uses filenames and file types; it does not certify correctness.",
              "Temporary copies exclude secrets, large files, dependencies, and binary assets."]
    if not any("test" in p.lower() for p in files):
        issues.insert(0, "No test files were found in this snapshot.")
    return technologies, skills, issues


def open_session(path: str) -> Session:
    root = Path(path).expanduser().resolve() if path else SAMPLE
    if not root.is_dir() or root == Path(root.anchor):
        raise ValueError("Select an existing project directory, not a drive root")
    guardian = WorkspaceGuardian(str(root))
    snapshot = guardian.create_snapshot()
    # Exclude hidden paths from writable copies; normalize Windows paths for the API.
    normalized = {}
    for name, content in snapshot.files.items():
        name = name.replace("\\", "/")
        try:
            safe_path(name)
        except ValueError:
            continue
        if len(normalized) >= 1000:
            break
        normalized[name] = content
    if not normalized:
        raise ValueError("No supported, non-secret text files were found")
    snapshot.files = normalized
    # Do not disclose a local absolute project root to an external AI provider.
    snapshot.project_root = "guardian-snapshot"
    tech, skills, issues = inspect_snapshot(snapshot)
    sample = root == SAMPLE
    view = SessionView(id=uuid.uuid4().hex, name="Student Event Management" if sample else root.name,
                       sample=sample, files=normalized.copy(),
                       summary="A student event application with a browser login client, a Python credential validator, an event repository, and regression tests." if sample else
                       f"Read-only snapshot of {root.name}: {len(normalized)} text files. Inspect the code, describe a problem, and review a proposed fix in a temporary copy.",
                       technologies=tech, skills=skills, issues=issues,
                       activity=["Guardian created a redacted, read-only snapshot."])
    hashes = {f.path.replace("\\", "/"): f.hash for f in guardian.list_files()}
    temp = tempfile.TemporaryDirectory(prefix="codeproof-")
    session = Session(guardian, snapshot, view, temp, hashes)
    try:
        session.write_copy(normalized)
    except Exception:
        session.close()
        raise
    return session


def start_challenge(session: Session, issue: str, target: str):
    view = session.view
    if view.phase != "analyzed":
        raise ValueError("Close this session and reopen the project to start another challenge")
    if view.sample:
        view.challenge_title = "Authentication Failure"
        view.challenge_description = "Valid users cannot sign in. The request fails validation with HTTP 422 before authentication completes. Trace the request and explain the root cause."
        view.relevant_files = [LOGIN, "src/auth/handler.py"]
        if GOOD not in view.files[LOGIN]:
            raise ValueError("The sample no longer matches the challenge template")
        view.files = dict(view.files)
        view.files[LOGIN] = view.files[LOGIN].replace(GOOD, BAD, 1)
        session.write_copy(view.files)
    else:
        if not issue.strip() or target not in view.files:
            raise ValueError("Describe an observed problem and choose a snapshot file")
        view.challenge_title = "Project investigation"
        view.challenge_description = issue
        view.relevant_files = [target]
    view.phase = "investigating"
    view.activity.append("Created a temporary challenge copy. Original files were not changed.")


def sample_evaluation(explanation: str) -> Evaluation:
    text = explanation.lower()
    passed = ("username" in text and "email" in text and
              any(word in text for word in ["expect", "key", "field", "mismatch", "instead", "send"]))
    return Evaluation(passed=passed, score=.95 if passed else .35,
                      feedback="You identified the request field mismatch. The handler requires username but the client sends email. Review the proposed change, then validate all three credential cases." if passed else
                      "Compare the credential key sent by the client with the key required by the handler. Explain how that mismatch causes validation to fail. This is a keyword-based practice check, not an AI assessment.")


def propose_sample_patch(view: SessionView) -> PatchView:
    before = view.files[LOGIN]
    after = before.replace(BAD, GOOD, 1)
    diff = "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                      fromfile="a/" + LOGIN, tofile="b/" + LOGIN))
    return PatchView(description="Align the login request credential key with the handler contract.",
                     diff=diff, affected_files=[LOGIN], risk_level="low",
                     validation_warnings=["Validate valid, invalid, and missing credentials before adopting this patch."])


def commit_patch(session: Session):
    view = session.view
    if view.phase != "review" or not view.patch or not view.evaluation or not view.evaluation.passed:
        raise ValueError("An accepted explanation and a reviewed patch are required")
    updated = apply_diff(view.files, view.patch.diff, view.relevant_files)
    # Validate every hunk before any temporary file is changed.
    try:
        session.write_copy(updated)
    except OSError:
        session.write_copy(view.files)
        raise ValueError("Temporary patch write failed; restored the previous copy")
    view.files = updated
    view.phase = "applied"
    view.validation = Validation()
    view.activity.append("Reviewed patch applied to the temporary copy.")


def fingerprint(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{p}\0{c}\0" for p, c in sorted(files.items())).encode()).hexdigest()
