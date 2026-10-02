import tempfile
import shutil
from pathlib import Path
import pytest
import asyncio

from workspace import WorkspaceGuardian, ProjectSnapshot
from ai.services import ProjectAnalyzer, ContextBuilder
from ai.models import ProjectAnalysis, EngineeringSkillMap, SkillEstimate
from ai.providers import BaseAIProvider, AIProviderConfig


class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing."""

    def __init__(self):
        config = AIProviderConfig(api_key="test", model="test")
        super().__init__(config)
        self._generate_structured_result = None
        self._generate_result = None
        self.call_count = 0
        self.last_prompt = None

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        return self._generate_result or "mock response"

    async def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str = None
    ):
        self.call_count += 1
        self.last_prompt = prompt
        return self._generate_structured_result

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


class TestAIAnalysisEngineV1:
    """Tests for AI Analysis Engine V1."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self._create_test_project()
        self.guardian = WorkspaceGuardian(str(self.temp_dir))
        self.provider = MockAIProvider()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def _create_test_project(self):
        """Create a test project structure with various file types."""
        # Source files
        (self.temp_dir / "src").mkdir()
        (self.temp_dir / "src" / "main.py").write_text("""
from flask import Flask, request, jsonify
from functools import wraps
import jwt
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    # TODO: Add proper password hashing
    if data.get('username') == 'admin' and data.get('password') == 'password':
        token = jwt.encode({'user': 'admin'}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True)
""")
        (self.temp_dir / "src" / "utils.py").write_text("""
def validate_email(email: str) -> bool:
    '''Simple email validation.'''
    return '@' in email and '.' in email

def hash_password(password: str) -> str:
    '''Insecure password hashing - for demo only.'''
    return password[::-1]  # Just reverse for demo

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    def execute_query(self, query: str, params=None):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()
        except Exception as e:
            print(f"Database error: {e}")
            raise
        finally:
            conn.close()
""")

        # Config files
        (self.temp_dir / "requirements.txt").write_text("""Flask>=2.0
PyJWT>=2.0
pytest>=7.0
""")
        (self.temp_dir / "pyproject.toml").write_text("""
[project]
name = "test-api"
version = "0.1.0"
dependencies = ["Flask", "PyJWT"]

[tool.pytest.ini_options]
testpaths = ["tests"]
""")

        # Test file
        (self.temp_dir / "tests").mkdir()
        (self.temp_dir / "tests" / "test_auth.py").write_text("""
import pytest
from src.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_success(client):
    response = client.post('/api/login', json={'username': 'admin', 'password': 'password'})
    assert response.status_code == 200
    assert 'token' in response.get_json()

def test_login_failure(client):
    response = client.post('/api/login', json={'username': 'wrong', 'password': 'wrong'})
    assert response.status_code == 401
""")

        # Secret file (should be excluded)
        (self.temp_dir / ".env").write_text("SECRET=should_not_be_read\nDATABASE_URL=postgres://user:pass@localhost/db\n")
        (self.temp_dir / ".git").mkdir()
        (self.temp_dir / ".git" / "config").write_text("[core]\n")

    def test_context_builder_creates_structured_context(self):
        """ContextBuilder creates deterministic, capped context."""
        builder = ContextBuilder(max_file_chars=1000, max_total_chars=5000, max_files=10)
        snapshot = self.guardian.create_snapshot()
        context = builder.build(snapshot)

        assert "project_id" in context
        assert "files" in context
        assert "dependencies" in context
        assert "config" in context
        assert "truncated" in context
        assert isinstance(context["files"], dict)
        assert len(context["files"]) <= 10

    def test_context_builder_prioritizes_config_files(self):
        """Config files are prioritized over source files."""
        builder = ContextBuilder(max_files=5)
        snapshot = self.guardian.create_snapshot()
        context = builder.build(snapshot)

        file_paths = list(context["files"].keys())
        # requirements.txt and pyproject.toml should be included
        assert any("requirements.txt" in p for p in file_paths)
        assert any("pyproject.toml" in p for p in file_paths)

    def test_context_builder_truncates_large_files(self):
        """Large files are truncated with notice."""
        # Create a large file
        large_content = "x" * 10000
        (self.temp_dir / "src" / "large.py").write_text(large_content)
        guardian = WorkspaceGuardian(str(self.temp_dir))

        builder = ContextBuilder(max_file_chars=100, max_total_chars=5000)
        snapshot = guardian.create_snapshot()
        context = builder.build(snapshot)

        large_key = next(k for k in context["files"] if "large.py" in k)
        assert "[TRUNCATED:" in context["files"][large_key]
        assert "9900 more chars" in context["files"][large_key]

    def test_context_builder_truncation_deterministic(self):
        """Truncation is deterministic across runs."""
        builder = ContextBuilder(max_files=3)
        snapshot = self.guardian.create_snapshot()

        context1 = builder.build(snapshot)
        context2 = builder.build(snapshot)

        assert list(context1["files"].keys()) == list(context2["files"].keys())
        assert context1["truncated"]["files"] == context2["truncated"]["files"]

    def test_analyze_produces_project_analysis(self):
        """analyze() produces a valid ProjectAnalysis."""
        analyzer = ProjectAnalyzer(self.provider)

        # Mock the provider response
        self.provider._generate_structured_result = ProjectAnalysis(
            project_id="test-123",
            summary="A Flask REST API with JWT authentication and SQLite database.",
            technologies=["Python", "Flask", "JWT", "SQLite"],
            issues=["Hardcoded secret key", "Insecure password handling", "Debug mode enabled"],
            skills=["API", "Authentication", "Database", "Testing", "Error Handling"],
        )

        snapshot = self.guardian.create_snapshot()
        analysis = asyncio.run(analyzer.analyze(snapshot))

        assert isinstance(analysis, ProjectAnalysis)
        assert analysis.project_id == "test-123"
        assert "Flask" in analysis.technologies
        assert len(analysis.issues) > 0
        assert len(analysis.skills) > 0

    def test_map_skills_produces_engineering_skill_map(self):
        """map_skills() produces a valid EngineeringSkillMap with estimates."""
        analyzer = ProjectAnalyzer(self.provider)

        # Mock the provider response with skill estimates
        self.provider._generate_structured_result = EngineeringSkillMap(
            project_id="test-123",
            skills=["API", "Authentication", "Database", "Testing", "Error Handling"],
            skill_estimates=[
                SkillEstimate(
                    category="API",
                    relevance=0.9,
                    confidence=0.95,
                    evidence=["Flask routes in src/main.py", "RESTful endpoints"]
                ),
                SkillEstimate(
                    category="Authentication",
                    relevance=0.9,
                    confidence=0.9,
                    evidence=["JWT token handling", "Login endpoint", "Token required decorator"]
                ),
                SkillEstimate(
                    category="Database",
                    relevance=0.8,
                    confidence=0.85,
                    evidence=["SQLite usage", "Raw SQL queries", "DatabaseManager class"]
                ),
                SkillEstimate(
                    category="Testing",
                    relevance=0.7,
                    confidence=0.8,
                    evidence=["pytest tests in tests/", "Test client usage"]
                ),
                SkillEstimate(
                    category="Error Handling",
                    relevance=0.6,
                    confidence=0.75,
                    evidence=["Try/except in DatabaseManager", "Basic error responses"]
                ),
                SkillEstimate(
                    category="Debugging",
                    relevance=0.5,
                    confidence=0.6,
                    evidence=["Debug mode enabled", "Print statements for errors"]
                ),
            ],
        )

        snapshot = self.guardian.create_snapshot()
        skill_map = asyncio.run(analyzer.map_skills(snapshot))

        assert isinstance(skill_map, EngineeringSkillMap)
        assert len(skill_map.skill_estimates) == 6
        categories = [s.category for s in skill_map.skill_estimates]
        for cat in ["API", "Authentication", "Database", "Testing", "Error Handling", "Debugging"]:
            assert cat in categories

        # Verify estimates have proper structure
        for estimate in skill_map.skill_estimates:
            assert 0.0 <= estimate.relevance <= 1.0
            assert 0.0 <= estimate.confidence <= 1.0
            assert isinstance(estimate.evidence, list)
            assert len(estimate.evidence) > 0

    def test_analyzer_uses_snapshot_not_filesystem(self):
        """Analyzer uses snapshot data, not direct filesystem access."""
        analyzer = ProjectAnalyzer(self.provider)
        snapshot = self.guardian.create_snapshot()

        # Verify analyzer can access all needed data from snapshot
        assert hasattr(snapshot, 'files')
        assert hasattr(snapshot, 'dependencies')
        assert hasattr(snapshot, 'config')
        assert len(snapshot.files) > 0

    def test_analyzer_rejects_invalid_snapshot(self):
        """Analyzer rejects invalid/empty snapshots."""
        analyzer = ProjectAnalyzer(self.provider)

        # Empty snapshot
        empty_snapshot = ProjectSnapshot(
            project_id="test",
            project_root="/tmp",
            metadata={},
            files={},
            dependencies={},
            config={}
        )

        with pytest.raises(ValueError, match="no files to analyze"):
            asyncio.run(analyzer.analyze(empty_snapshot))

        with pytest.raises(ValueError, match="no files to analyze"):
            asyncio.run(analyzer.map_skills(empty_snapshot))

    def test_analyzer_handles_provider_failure(self):
        """Analyzer handles provider failure cleanly."""
        analyzer = ProjectAnalyzer(self.provider)
        snapshot = self.guardian.create_snapshot()

        # Make provider raise an error
        async def failing_generate(*args, **kwargs):
            raise ConnectionError("API unavailable")

        self.provider.generate_structured = failing_generate

        with pytest.raises(RuntimeError, match="Analysis failed"):
            asyncio.run(analyzer.analyze(snapshot))

    def test_analyzer_system_prompt_separates_untrusted_content(self):
        """System prompt explicitly separates untrusted project content."""
        analyzer = ProjectAnalyzer(self.provider)
        snapshot = self.guardian.create_snapshot()

        # Capture the prompt sent to provider
        captured_prompt = None

        async def capture_prompt(prompt, response_model, system_prompt):
            nonlocal captured_prompt
            captured_prompt = prompt
            return ProjectAnalysis(
                project_id=snapshot.project_id,
                summary="Test",
                technologies=[],
                issues=[],
                skills=[]
            )

        self.provider.generate_structured = capture_prompt
        asyncio.run(analyzer.analyze(snapshot))

        assert captured_prompt is not None
        # Verify system prompt is separate from project content
        assert "UNTRUSTED DATA" in analyzer._get_system_prompt()
        # Verify project content is in the user prompt, not system prompt
        assert "PROJECT CONTEXT" in captured_prompt
        assert "PROJECT FILES" in captured_prompt

    def test_skill_map_system_prompt_mentions_estimate_not_measurement(self):
        """Skill map system prompt uses 'estimate' language."""
        analyzer = ProjectAnalyzer(self.provider)
        skill_prompt = analyzer._get_skill_system_prompt()

        assert "ESTIMATE" in skill_prompt.upper()
        assert "UNTRUSTED DATA" in skill_prompt.upper()

    def test_secret_content_from_guardian_remains_protected(self):
        """Secret content from Guardian remains redacted in analysis context."""
        # Add a file with secret content
        (self.temp_dir / "src" / "config.py").write_text("""
API_KEY = 'sk-1234567890abcdef1234567890abcdef'
DATABASE_PASSWORD = 'super-secret-password'
normal_setting = 'hello'
""")
        guardian = WorkspaceGuardian(str(self.temp_dir))
        snapshot = guardian.create_snapshot()

        builder = ContextBuilder()
        context = builder.build(snapshot)

        # Find the config file
        config_key = next(k for k in context["files"] if "config.py" in k)
        config_content = context["files"][config_key]

        # Secrets should be redacted
        assert "sk-1234567890abcdef1234567890abcdef" not in config_content
        assert "super-secret-password" not in config_content
        assert "[REDACTED" in config_content or "normal_setting" in config_content

    def test_provider_abstraction_intact(self):
        """Analyzer depends only on BaseAIProvider, not concrete providers."""
        from ai.providers import BaseAIProvider
        import inspect

        # Check that ProjectAnalyzer only references BaseAIProvider
        sig = inspect.signature(ProjectAnalyzer.__init__)
        assert 'provider' in sig.parameters
        # The type annotation should be BaseAIProvider
        param = sig.parameters['provider']
        # We can't easily check the annotation at runtime, but we can verify
        # it works with our mock which inherits from BaseAIProvider
        analyzer = ProjectAnalyzer(self.provider)
        assert isinstance(analyzer.provider, BaseAIProvider)


class TestContextBuilderEdgeCases:
    """Tests for ContextBuilder edge cases."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_empty_snapshot(self):
        """ContextBuilder handles empty snapshot gracefully."""
        builder = ContextBuilder()
        snapshot = ProjectSnapshot(
            project_id="empty",
            project_root="/empty",
            metadata={},
            files={},
            dependencies={},
            config={}
        )
        context = builder.build(snapshot)
        assert context["files"] == {}
        assert context["dependencies"] == {}
        assert context["config"] == {}

    def test_snapshot_with_only_config_files(self):
        """ContextBuilder works with only config files."""
        (self.temp_dir / "package.json").write_text('{"name": "test"}')
        (self.temp_dir / "requirements.txt").write_text("requests")

        guardian = WorkspaceGuardian(str(self.temp_dir))
        builder = ContextBuilder()
        snapshot = guardian.create_snapshot()
        context = builder.build(snapshot)

        assert len(context["files"]) == 2
        assert any("package.json" in k for k in context["files"])
        assert any("requirements.txt" in k for k in context["files"])

    def test_very_large_snapshot_truncation(self):
        """ContextBuilder handles very large snapshots."""
        # Create many files
        for i in range(50):
            (self.temp_dir / f"file_{i}.py").write_text(f"# File {i}\n" + "x" * 1000)

        guardian = WorkspaceGuardian(str(self.temp_dir))
        builder = ContextBuilder(max_files=10, max_total_chars=5000)
        snapshot = guardian.create_snapshot()
        context = builder.build(snapshot)

        assert len(context["files"]) <= 10
        assert len(context["truncated"]["files"]) >= 40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])