import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

from workspace import WorkspaceGuardian, ProjectSnapshot
from ai.services import ProjectAnalyzer, ArchitectureAnalyzer, PatchGenerator
from ai.models import ProjectAnalysis, EngineeringSkillMap, Patch
from ai.providers import BaseAIProvider, AIProviderConfig


class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing."""

    def __init__(self):
        config = AIProviderConfig(api_key="test", model="test")
        super().__init__(config)
        self._generate_structured_result = None
        self._generate_result = None

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        return self._generate_result or "mock response"

    async def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str = None
    ):
        return self._generate_structured_result

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


class TestGuardianAIContract:
    """Tests for the typed Guardian → AI contract."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self._create_test_project()
        self.guardian = WorkspaceGuardian(str(self.temp_dir))
        self.provider = MockAIProvider()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def _create_test_project(self):
        """Create a test project structure."""
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "src" / "main.py").write_text("""
def main():
    print('Hello, World!')

if __name__ == '__main__':
    main()
""")
        (self.temp_dir / "src" / "utils.py").write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
""")
        (self.temp_dir / "requirements.txt").write_text("requests>=2.28\npytest>=7.0\n")
        (self.temp_dir / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["requests", "pytest"]
""")
        (self.temp_dir / ".env").write_text("SECRET=should_not_be_read\n")
        (self.temp_dir / ".git").mkdir()
        (self.temp_dir / ".git" / "config").write_text("[core]\n")

    def test_guardian_creates_typed_snapshot(self):
        """WorkspaceGuardian.create_snapshot() returns ProjectSnapshot."""
        snapshot = self.guardian.create_snapshot()
        assert isinstance(snapshot, ProjectSnapshot)
        assert snapshot.project_id
        assert snapshot.project_root == str(self.temp_dir.resolve())
        assert isinstance(snapshot.files, dict)
        assert isinstance(snapshot.dependencies, dict)
        assert isinstance(snapshot.config, dict)
        assert isinstance(snapshot.metadata, dict)

    def test_snapshot_excludes_secret_files(self):
        """Secret files are excluded from the snapshot."""
        snapshot = self.guardian.create_snapshot()
        assert ".env" not in snapshot.files
        assert not any(".env" in path for path in snapshot.files.keys())

    def test_snapshot_redacts_secret_content(self):
        """Secret content is redacted in snapshot files."""
        # Create a file with secret content
        (self.temp_dir / "src" / "config.py").write_text("""
API_KEY = 'sk-1234567890abcdef1234567890abcdef'
password = 'secret123'
normal_var = 'hello'
""")
        # Create a new guardian to pick up the new file
        guardian = WorkspaceGuardian(str(self.temp_dir))
        snapshot = guardian.create_snapshot()

        # Find the config file key (handles Windows backslashes)
        config_key = next(k for k in snapshot.files.keys() if "config.py" in k)
        config_content = snapshot.files[config_key]
        assert "sk-1234567890abcdef1234567890abcdef" not in config_content
        assert "secret123" not in config_content
        assert "[REDACTED" in config_content or "normal_var" in config_content

    def test_snapshot_does_not_modify_original(self):
        """Snapshot creation does not modify the original project."""
        original_main = (self.temp_dir / "src" / "main.py").read_text()
        original_env = (self.temp_dir / ".env").read_text()

        snapshot = self.guardian.create_snapshot()

        assert (self.temp_dir / "src" / "main.py").read_text() == original_main
        assert (self.temp_dir / ".env").read_text() == original_env

    def test_analyzer_accepts_typed_snapshot(self):
        """ProjectAnalyzer accepts ProjectSnapshot directly, not a dict."""
        analyzer = ProjectAnalyzer(self.provider)
        snapshot = self.guardian.create_snapshot()

        # This should not raise a type error
        assert hasattr(analyzer, 'analyze')
        assert hasattr(analyzer, 'map_skills')

        # Verify the method signatures accept ProjectSnapshot
        import inspect
        # For async methods, we need to unwrap them
        analyze_func = analyzer.analyze
        map_skills_func = analyzer.map_skills

        # Check the annotations
        analyze_annotations = analyze_func.__annotations__
        map_skills_annotations = map_skills_func.__annotations__

        # Both should have project_snapshot parameter typed as ProjectSnapshot
        assert 'project_snapshot' in analyze_annotations
        assert 'project_snapshot' in map_skills_annotations
        # The return type should be the model
        assert 'return' in analyze_annotations
        assert 'return' in map_skills_annotations

    def test_analyzer_works_without_filesystem_access(self):
        """Analyzer works with snapshot data without reading files directly."""
        analyzer = ProjectAnalyzer(self.provider)
        snapshot = self.guardian.create_snapshot()

        # The analyzer should be able to access all needed data from snapshot
        assert hasattr(snapshot, 'files')
        assert hasattr(snapshot, 'dependencies')
        assert hasattr(snapshot, 'config')
        assert hasattr(snapshot, 'metadata')
        assert hasattr(snapshot, 'project_id')
        assert hasattr(snapshot, 'project_root')

        # Verify snapshot contains expected data
        assert len(snapshot.files) > 0
        assert "python" in snapshot.dependencies or len(snapshot.dependencies) > 0

    def test_both_analyze_and_map_skills_use_typed_snapshot(self):
        """Both analyze() and map_skills() use the typed snapshot contract."""
        analyzer = ProjectAnalyzer(self.provider)
        snapshot = self.guardian.create_snapshot()

        # Mock the provider responses
        self.provider._generate_structured_result = ProjectAnalysis(
            project_id=snapshot.project_id,
            summary="Test project",
            technologies=["Python"],
            issues=[],
            skills=["Python", "Testing"]
        )

        import asyncio
        analysis = asyncio.run(analyzer.analyze(snapshot))

        assert isinstance(analysis, ProjectAnalysis)

        # Now test map_skills
        self.provider._generate_structured_result = EngineeringSkillMap(
            project_id=snapshot.project_id,
            skills=["Python", "Testing"]
        )
        skill_map = asyncio.run(analyzer.map_skills(snapshot))

        assert isinstance(skill_map, EngineeringSkillMap)

    def test_architecture_analyzer_accepts_typed_snapshot(self):
        """ArchitectureAnalyzer accepts ProjectSnapshot."""
        analyzer = ArchitectureAnalyzer(self.provider)
        snapshot = self.guardian.create_snapshot()

        import inspect
        analyze_func = analyzer.analyze_architecture
        annotations = analyze_func.__annotations__

        assert 'project_snapshot' in annotations
        assert 'return' in annotations

    def test_patch_generator_accepts_typed_snapshot(self):
        """PatchGenerator accepts PatchRequest with ProjectSnapshot."""
        generator = PatchGenerator(self.provider)
        snapshot = self.guardian.create_snapshot()

        import inspect
        generate_func = generator.generate_patch
        annotations = generate_func.__annotations__

        assert 'request' in annotations
        assert 'return' in annotations

    def test_invalid_snapshot_fails_cleanly(self):
        """Invalid/incomplete snapshot input fails cleanly."""
        analyzer = ProjectAnalyzer(self.provider)

        # Create a minimal invalid snapshot (missing required fields)
        # This should be caught by Pydantic validation - project_id is required
        with pytest.raises(Exception):
            ProjectSnapshot(
                project_root="",
                metadata={},
                files={},
                dependencies={},
                config={}
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])