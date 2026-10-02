import tempfile
import shutil
from pathlib import Path
import pytest

from workspace import (
    WorkspaceGuardian,
    ProjectScanner,
    SecretFilter,
    SnapshotBuilder,
    ProjectIndex,
    FileMetadata,
    ProjectSnapshot,
)


class TestProjectScanner:
    """Tests for ProjectScanner."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self._create_test_project()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def _create_test_project(self):
        """Create a test project structure."""
        # Source files
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "src" / "main.py").write_text("print('hello')\n")
        (self.temp_dir / "src" / "utils.py").write_text("def helper():\n    return 42\n")

        # Config files
        (self.temp_dir / "requirements.txt").write_text("requests>=2.28\n")
        (self.temp_dir / "pyproject.toml").write_text('[project]\nname = "test"\n')

        # Ignored directories
        (self.temp_dir / "node_modules").mkdir()
        (self.temp_dir / "node_modules" / "package.json").write_text('{}')
        (self.temp_dir / "__pycache__").mkdir()
        (self.temp_dir / "__pycache__" / "main.cpython-311.pyc").write_text("binary")
        (self.temp_dir / ".git").mkdir()
        (self.temp_dir / ".git" / "config").write_text("[core]\n")

        # Secret files (should be ignored)
        (self.temp_dir / ".env").write_text("SECRET=abc123\n")
        (self.temp_dir / ".env.local").write_text("API_KEY=xyz\n")
        (self.temp_dir / "private.key").write_text("-----BEGIN PRIVATE KEY-----\n")

    def test_scanner_creates_index(self):
        """Test that scanner creates a valid project index."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        assert isinstance(index, ProjectIndex)
        assert index.project_root == str(self.temp_dir.resolve())
        assert index.total_files > 0

    def test_scanner_ignores_git_folder(self):
        """Test that .git folder is ignored."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        git_files = [f for f in index.files if f.path.startswith(".git")]
        assert len(git_files) == 0

    def test_scanner_ignores_node_modules(self):
        """Test that node_modules is ignored."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        nm_files = [f for f in index.files if f.path.startswith("node_modules")]
        assert len(nm_files) == 0

    def test_scanner_ignores_pycache(self):
        """Test that __pycache__ is ignored."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        pycache_files = [f for f in index.files if f.path.startswith("__pycache__")]
        assert len(pycache_files) == 0

    def test_scanner_ignores_env_files(self):
        """Test that .env files are ignored."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        env_files = [f for f in index.files if f.path.startswith(".env")]
        assert len(env_files) == 0

    def test_scanner_ignores_key_files(self):
        """Test that .key files are ignored."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        key_files = [f for f in index.files if f.path.endswith(".key")]
        assert len(key_files) == 0

    def test_scanner_includes_source_files(self):
        """Test that source files are included."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        source_files = [f.path for f in index.files if f.path.startswith("src") and ("main.py" in f.path or "utils.py" in f.path)]
        assert any("main.py" in p for p in source_files)
        assert any("utils.py" in p for p in source_files)

    def test_scanner_includes_config_files(self):
        """Test that config files are included."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        config_files = [f.path for f in index.files]
        assert "requirements.txt" in config_files
        assert "pyproject.toml" in config_files

    def test_scanner_calculates_hashes(self):
        """Test that file hashes are calculated."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        for file_meta in index.files:
            assert file_meta.hash
            assert len(file_meta.hash) == 64  # SHA256

    def test_scanner_detects_language(self):
        """Test that language detection works."""
        scanner = ProjectScanner(str(self.temp_dir))
        index = scanner.scan()

        main_py = next(f for f in index.files if "main.py" in f.path)
        assert main_py.language == "python"

    def test_invalid_project_path_raises(self):
        """Test that invalid project path raises ValueError."""
        # Use a path that definitely doesn't exist on any platform
        import tempfile
        nonexistent = Path(tempfile.gettempdir()) / "codeproof_nonexistent_abcdef_12345"
        scanner = ProjectScanner(str(nonexistent))
        with pytest.raises(ValueError, match="does not exist"):
            scanner.scan()

    def test_file_not_directory_raises(self):
        """Test that file path raises ValueError."""
        file_path = self.temp_dir / "src" / "main.py"
        scanner = ProjectScanner(str(file_path))
        with pytest.raises(ValueError, match="not a directory"):
            scanner.scan()


class TestSecretFilter:
    """Tests for SecretFilter."""

    def setup_method(self):
        self.filter = SecretFilter()

    def test_detects_env_files(self):
        """Test detection of .env files."""
        assert self.filter.is_secret_file(Path(".env")) is True
        assert self.filter.is_secret_file(Path(".env.local")) is True
        assert self.filter.is_secret_file(Path(".env.production")) is True

    def test_detects_key_files(self):
        """Test detection of key files."""
        assert self.filter.is_secret_file(Path("private.key")) is True
        assert self.filter.is_secret_file(Path("id_rsa")) is True
        assert self.filter.is_secret_file(Path("id_ed25519")) is True

    def test_detects_pem_files(self):
        """Test detection of .pem files."""
        assert self.filter.is_secret_file(Path("cert.pem")) is True

    def test_detects_credentials_files(self):
        """Test detection of credentials files."""
        assert self.filter.is_secret_file(Path("credentials.json")) is True
        assert self.filter.is_secret_file(Path("service-account.json")) is True

    def test_allows_normal_files(self):
        """Test that normal files are allowed."""
        assert self.filter.is_secret_file(Path("main.py")) is False
        assert self.filter.is_secret_file(Path("config.json")) is False
        assert self.filter.is_secret_file(Path("README.md")) is False

    def test_scans_content_for_secrets(self):
        """Test content scanning for secrets."""
        content = "API_KEY = 'sk-1234567890abcdef1234567890abcdef'"
        findings = self.filter.scan_content(content)
        assert len(findings) > 0
        assert any(f["type"] == "API key" for f in findings)

    def test_redacts_secrets(self):
        """Test secret redaction."""
        content = "password = 'secret123'\nAPI_KEY = 'sk-abc1234567890abcdef1234567890abcdef'"
        redacted = self.filter.redact_content(content)
        assert "secret123" not in redacted
        assert "sk-abc1234567890abcdef1234567890abcdef" not in redacted
        assert "[REDACTED" in redacted


class TestWorkspaceGuardian:
    """Tests for WorkspaceGuardian."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self._create_test_project()
        self.guardian = WorkspaceGuardian(str(self.temp_dir))

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def _create_test_project(self):
        """Create a test project structure."""
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "src" / "main.py").write_text("print('hello world')\n")
        (self.temp_dir / "src" / "utils.py").write_text("def add(a, b):\n    return a + b\n")
        (self.temp_dir / "requirements.txt").write_text("requests>=2.28\n")
        (self.temp_dir / ".env").write_text("SECRET=should_not_be_read\n")
        (self.temp_dir / ".git").mkdir()
        (self.temp_dir / ".git" / "config").write_text("[core]\n")

    def test_guardian_validates_project(self):
        """Test project validation."""
        assert self.guardian.validate_project() is True

    def test_guardian_rejects_invalid_path(self):
        """Test that invalid path is rejected."""
        import tempfile
        nonexistent = Path(tempfile.gettempdir()) / "codeproof_nonexistent_abcdef_12345"
        bad_guardian = WorkspaceGuardian(str(nonexistent))
        assert bad_guardian.validate_project() is False

    def test_guardian_lists_files(self):
        """Test file listing."""
        files = self.guardian.list_files()
        paths = [f.path for f in files]
        assert any("main.py" in p for p in paths)
        assert any("utils.py" in p for p in paths)
        assert any("requirements.txt" in p for p in paths)

    def test_guardian_reads_allowed_files(self):
        """Test reading allowed files."""
        content = self.guardian.read_file("src/main.py")
        assert content is not None
        assert "hello world" in content

    def test_guardian_ignores_env_files(self):
        """Test that .env files cannot be read."""
        content = self.guardian.read_file(".env")
        assert content is None

    def test_guardian_rejects_outside_paths(self):
        """Test that paths outside project root are rejected."""
        with pytest.raises(ValueError, match="outside project root"):
            self.guardian.read_file("../../etc/passwd")

    def test_guardian_no_write_methods(self):
        """Test that guardian has no write methods."""
        assert self.guardian.verify_no_write_access() is True

    def test_guardian_creates_snapshot(self):
        """Test snapshot creation."""
        snapshot = self.guardian.create_snapshot()
        assert isinstance(snapshot, ProjectSnapshot)
        assert snapshot.project_id
        assert snapshot.project_root == str(self.temp_dir.resolve())
        assert any("main.py" in p for p in snapshot.files)
        assert any("requirements.txt" in p for p in snapshot.files)

    def test_guardian_snapshot_excludes_secrets(self):
        """Test that snapshot excludes secret files."""
        snapshot = self.guardian.create_snapshot()
        assert ".env" not in snapshot.files

    def test_guardian_snapshot_does_not_modify_original(self):
        """Test that snapshot creation doesn't modify original project."""
        # Record original state
        original_main = (self.temp_dir / "src" / "main.py").read_text()
        original_env = (self.temp_dir / ".env").read_text()

        # Create snapshot
        snapshot = self.guardian.create_snapshot()

        # Verify original files unchanged
        assert (self.temp_dir / "src" / "main.py").read_text() == original_main
        assert (self.temp_dir / ".env").read_text() == original_env

    def test_guardian_gets_file_metadata(self):
        """Test getting file metadata."""
        # Find the correct path (handles Windows backslashes)
        files = self.guardian.list_files()
        main_py = next(f for f in files if "main.py" in f.path)
        meta = self.guardian.get_file_metadata(main_py.path)
        assert meta is not None
        assert "main.py" in meta.path
        assert meta.size > 0
        assert meta.hash

    def test_guardian_gets_project_summary(self):
        """Test project summary."""
        summary = self.guardian.get_project_summary()
        assert summary["project_root"] == str(self.temp_dir.resolve())
        assert summary["total_files"] > 0
        assert "python" in summary["languages"]


class TestSnapshotBuilder:
    """Tests for SnapshotBuilder."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self._create_test_project()
        self.scanner = ProjectScanner(str(self.temp_dir))
        self.builder = SnapshotBuilder(self.scanner)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def _create_test_project(self):
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "src" / "main.py").write_text("print('hello')\n")
        (self.temp_dir / "requirements.txt").write_text("requests>=2.28\n")
        (self.temp_dir / "package.json").write_text('{"dependencies": {"express": "^4.18"}}')
        (self.temp_dir / ".env").write_text("SECRET=abc\n")

    def test_builder_creates_snapshot(self):
        """Test snapshot creation."""
        snapshot = self.builder.build_snapshot()
        assert isinstance(snapshot, ProjectSnapshot)
        assert snapshot.project_id
        assert len(snapshot.files) > 0

    def test_builder_includes_dependencies(self):
        """Test dependency extraction."""
        snapshot = self.builder.build_snapshot()
        assert "python" in snapshot.dependencies
        assert "node" in snapshot.dependencies

    def test_builder_respects_size_limits(self):
        """Test that size limits are respected."""
        # Create a large file
        large_file = self.temp_dir / "large.txt"
        large_file.write_text("x" * 200_000)  # 200KB > 100KB limit

        snapshot = self.builder.build_snapshot()
        assert "large.txt" not in snapshot.files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])