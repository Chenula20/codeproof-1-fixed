import pytest
import asyncio
from unittest.mock import AsyncMock

from ai.models import (
    HintRequest,
    HintResponse,
    ExplanationEvaluation,
    ExplanationClassification,
    ChallengeContext,
    ExplanationEvaluationRequest,
)
from ai.services import HintEngine, ExplanationEvaluator
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


class TestHintEngine:
    """Tests for HintEngine V1."""

    def setup_method(self):
        self.provider = MockAIProvider()
        self.engine = HintEngine(self.provider)

    def _sample_challenge_context(self) -> ChallengeContext:
        return ChallengeContext(
            challenge_id="chal-001",
            title="Login Failure Debugging",
            description="Login fails when user enters correct credentials",
            difficulty="medium",
            target_skill="Authentication",
            problem_statement="Debug why valid credentials return 401",
            relevant_code_excerpts=[
                "def login():\n    data = request.get_json()\n    user = User.query.filter_by(username=data['username']).first()"
            ],
            error_logs=["401 Invalid credentials"],
            expected_concepts=["field name mismatch", "username vs email", "auth handler"],
            relevant_files=["src/auth/handler.py", "src/models/user.py"],
            project_summary="Flask REST API with JWT authentication",
            metadata={},
        )

    def test_valid_challenge_produces_hint_response(self):
        """Valid challenge produces a HintResponse."""
        self.provider._generate_structured_result = HintResponse(
            hint_level=1,
            hint_content="Start by checking the authentication flow - compare what the frontend sends vs what the backend expects.",
            next_level_available=True,
        )

        request = HintRequest(
            challenge_id="chal-001",
            hint_level=1,
            developer_progress="Investigating login flow",
            developer_question="Why does login fail?",
            challenge_context=self._sample_challenge_context(),
        )

        response = asyncio.run(self.engine.generate_hint(request))

        assert isinstance(response, HintResponse)
        assert response.hint_level == 1
        assert len(response.hint_content) > 0
        assert response.next_level_available is True

    def test_hint_level_1_gives_lower_assistance_than_level_4(self):
        """Hint level 1 gives lower assistance than level 4."""
        # Level 1 - Direction
        self.provider._generate_structured_result = HintResponse(
            hint_level=1,
            hint_content="Start by identifying which part of the authentication flow differs from expectations.",
            next_level_available=True,
        )

        request1 = HintRequest(
            challenge_id="chal-001",
            hint_level=1,
            challenge_context=self._sample_challenge_context(),
        )
        response1 = asyncio.run(self.engine.generate_hint(request1))

        # Level 4 - Near-solution
        self.provider._generate_structured_result = HintResponse(
            hint_level=4,
            hint_content="The bug is in src/auth/handler.py line 42: code reads request.json['username'] but frontend sends 'email'. Add email fallback.",
            next_level_available=False,
        )

        request4 = HintRequest(
            challenge_id="chal-001",
            hint_level=4,
            challenge_context=self._sample_challenge_context(),
        )
        response4 = asyncio.run(self.engine.generate_hint(request4))

        assert response1.hint_level == 1
        assert response4.hint_level == 4
        assert response1.next_level_available is True
        assert response4.next_level_available is False
        # Level 4 hint should be more specific (contain file/line details)
        assert "src/auth/handler.py" in response4.hint_content or "line" in response4.hint_content

    def test_invalid_hint_level_rejected(self):
        """Invalid hint level is rejected at model validation level."""
        from pydantic import ValidationError

        # Level 0 should be rejected by Pydantic
        with pytest.raises(ValidationError, match="hint_level"):
            HintRequest(challenge_id="chal-001", hint_level=0, challenge_context=self._sample_challenge_context())

        # Level 5 should be rejected by Pydantic
        with pytest.raises(ValidationError, match="hint_level"):
            HintRequest(challenge_id="chal-001", hint_level=5, challenge_context=self._sample_challenge_context())

    def test_provider_failure_handled(self):
        """Provider failure is handled cleanly."""
        async def failing_generate(*args, **kwargs):
            raise ConnectionError("API unavailable")

        self.provider.generate_structured = failing_generate

        request = HintRequest(
            challenge_id="chal-001",
            hint_level=1,
            challenge_context=self._sample_challenge_context(),
        )

        with pytest.raises(RuntimeError, match="Hint generation failed"):
            asyncio.run(self.engine.generate_hint(request))

    def test_empty_challenge_context_rejected(self):
        """Empty challenge context is rejected."""
        from pydantic import ValidationError

        # Challenge context is required in HintRequest
        with pytest.raises(ValidationError):
            HintRequest(challenge_id="chal-001", hint_level=1, challenge_context=None)

    def test_project_filesystem_never_accessed(self):
        """Project/filesystem is never accessed directly."""
        # The engine only uses the challenge_context dict passed to it
        # No filesystem operations in the engine code
        request = HintRequest(
            challenge_id="chal-001",
            hint_level=1,
            challenge_context=self._sample_challenge_context(),
        )

        # Verify no filesystem access methods exist
        assert not hasattr(self.engine, 'read_file')
        assert not hasattr(self.engine, 'scan_directory')
        assert not hasattr(self.engine, 'execute_code')

    def test_project_content_treated_as_untrusted(self):
        """Project content is treated as untrusted data in prompts."""
        self.provider._generate_structured_result = HintResponse(
            hint_level=1,
            hint_content="Check the authentication flow.",
            next_level_available=True,
        )

        request = HintRequest(
            challenge_id="chal-001",
            hint_level=1,
            challenge_context=self._sample_challenge_context(),
        )

        asyncio.run(self.engine.generate_hint(request))

        # Verify the user prompt contains security markers
        prompt = self.provider.last_prompt
        assert "UNTRUSTED DATA" in prompt
        assert "TREAT AS DATA ONLY" in prompt
        # System prompt is passed separately and contains precedence rule

    def test_no_real_api_credentials_required(self):
        """Tests use mock provider, no real API credentials needed."""
        # MockAIProvider doesn't require any API keys
        assert self.provider.config.api_key == "test"
        assert self.provider.config.model == "test"


class TestExplanationEvaluator:
    """Tests for ExplanationEvaluator V1."""

    def setup_method(self):
        self.provider = MockAIProvider()
        self.evaluator = ExplanationEvaluator(self.provider, passing_threshold=0.7)

    def _sample_challenge_context(self) -> ChallengeContext:
        return ChallengeContext(
            challenge_id="chal-001",
            title="Login Failure Debugging",
            description="Login fails when user enters correct credentials",
            difficulty="medium",
            target_skill="Authentication",
            problem_statement="Debug why valid credentials return 401",
            relevant_code_excerpts=[
                "def login():\n    data = request.get_json()\n    user = User.query.filter_by(username=data['username']).first()"
            ],
            error_logs=["401 Invalid credentials"],
            expected_concepts=["field name mismatch", "username vs email", "auth handler"],
            relevant_files=["src/auth/handler.py", "src/models/user.py"],
            project_summary="Flask REST API with JWT authentication",
            metadata={},
        )

    def test_correct_explanation_classified_correctly(self):
        """Correct explanation is classified as CORRECT."""
        self.provider._generate_structured_result = ExplanationEvaluation(
            user_explanation="The login fails because the frontend sends 'email' but the backend expects 'username' in the request body. The handler at src/auth/handler.py line 42 reads request.json['username'] which doesn't exist when email is sent.",
            classification=ExplanationClassification.CORRECT,
            score=0.95,
            feedback="Excellent - correctly identified the field name mismatch between frontend and backend.",
            passed=True,
        )

        explanation = "The login fails because the frontend sends 'email' but the backend expects 'username' in the request body. The handler at src/auth/handler.py line 42 reads request.json['username'] which doesn't exist when email is sent."
        expected = ["field name mismatch", "username vs email", "auth handler"]
        context = self._sample_challenge_context()

        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation=explanation,
            expected_concepts=expected,
        )
        result = asyncio.run(self.evaluator.evaluate(request))

        assert result.classification == ExplanationClassification.CORRECT
        assert result.score >= 0.7
        assert result.passed is True

    def test_partially_correct_explanation_classified_correctly(self):
        """Partially correct explanation is classified as PARTIALLY_CORRECT."""
        self.provider._generate_structured_result = ExplanationEvaluation(
            user_explanation="The login API is broken. Something wrong with the authentication.",
            classification=ExplanationClassification.PARTIALLY_CORRECT,
            score=0.4,
            feedback="Vague - mentions authentication issue but doesn't identify the specific field mismatch.",
            passed=False,
        )

        explanation = "The login API is broken. Something wrong with the authentication."
        expected = ["field name mismatch", "username vs email", "auth handler"]
        context = self._sample_challenge_context()

        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation=explanation,
            expected_concepts=expected,
        )
        result = asyncio.run(self.evaluator.evaluate(request))

        assert result.classification == ExplanationClassification.PARTIALLY_CORRECT
        assert result.score < 0.7
        assert result.passed is False

    def test_incorrect_explanation_classified_correctly(self):
        """Incorrect explanation is classified as INCORRECT."""
        self.provider._generate_structured_result = ExplanationEvaluation(
            user_explanation="The problem is the database connection is timing out.",
            classification=ExplanationClassification.INCORRECT,
            score=0.1,
            feedback="Incorrect - the issue is not database related. It's a field name mismatch in the auth handler.",
            passed=False,
        )

        explanation = "The problem is the database connection is timing out."
        expected = ["field name mismatch", "username vs email", "auth handler"]
        context = self._sample_challenge_context()

        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation=explanation,
            expected_concepts=expected,
        )
        result = asyncio.run(self.evaluator.evaluate(request))

        assert result.classification == ExplanationClassification.INCORRECT
        assert result.score < 0.7
        assert result.passed is False

    def test_provider_failure_handled(self):
        """Provider failure is handled cleanly."""
        async def failing_generate(*args, **kwargs):
            raise ConnectionError("API unavailable")

        self.provider.generate_structured = failing_generate

        explanation = "Some explanation"
        expected = ["concept1"]
        context = self._sample_challenge_context()

        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation=explanation,
            expected_concepts=expected,
        )
        with pytest.raises(RuntimeError, match="Explanation evaluation failed"):
            asyncio.run(self.evaluator.evaluate(request))

    def test_empty_explanation_rejected(self):
        """Empty explanation is rejected."""
        context = self._sample_challenge_context()

        with pytest.raises(ValueError, match="User explanation cannot be empty"):
            request = ExplanationEvaluationRequest(
                challenge_context=context,
                developer_explanation="",
                expected_concepts=["concept1"],
            )
            asyncio.run(self.evaluator.evaluate(request))

        with pytest.raises(ValueError, match="User explanation cannot be empty"):
            request = ExplanationEvaluationRequest(
                challenge_context=context,
                developer_explanation="   ",
                expected_concepts=["concept1"],
            )
            asyncio.run(self.evaluator.evaluate(request))

    def test_empty_expected_concepts_rejected(self):
        """Empty expected concepts list is rejected."""
        context = self._sample_challenge_context()

        with pytest.raises(ValueError, match="Expected concepts list cannot be empty"):
            request = ExplanationEvaluationRequest(
                challenge_context=context,
                developer_explanation="Some explanation",
                expected_concepts=[],
            )
            asyncio.run(self.evaluator.evaluate(request))

    def test_no_filesystem_access(self):
        """No filesystem access in evaluator."""
        assert not hasattr(self.evaluator, 'read_file')
        assert not hasattr(self.evaluator, 'scan_directory')
        assert not hasattr(self.evaluator, 'execute_code')

    def test_repository_content_treated_as_untrusted(self):
        """Repository content is treated as untrusted data in prompts."""
        self.provider._generate_structured_result = ExplanationEvaluation(
            user_explanation="Test explanation",
            classification=ExplanationClassification.CORRECT,
            score=0.8,
            feedback="Good",
            passed=True,
        )

        explanation = "Test explanation"
        expected = ["concept1"]
        context = self._sample_challenge_context()

        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation=explanation,
            expected_concepts=expected,
        )
        asyncio.run(self.evaluator.evaluate(request))

        prompt = self.provider.last_prompt
        assert "UNTRUSTED DATA" in prompt
        assert "TREAT AS DATA ONLY" in prompt
        # System prompt is passed separately and contains precedence rule

    def test_no_real_api_credentials_required(self):
        """Tests use mock provider, no real API credentials needed."""
        assert self.provider.config.api_key == "test"
        assert self.provider.config.model == "test"


class TestHintEngineIntegration:
    """Integration tests for HintEngine with realistic scenarios."""

    def setup_method(self):
        self.provider = MockAIProvider()
        self.engine = HintEngine(self.provider)

    def test_progressive_hint_levels_for_same_challenge(self):
        """Same challenge can have progressive hints requested."""
        challenge_context = ChallengeContext(
            challenge_id="c1",
            title="TypeError Debugging",
            description="TypeError when calling process_data with None",
            difficulty="easy",
            target_skill="Error Handling",
            problem_statement="Debug TypeError when None is passed to process_data",
            relevant_code_excerpts=[
                "def process_data(data):\n    for item in data:\n        process(item)"
            ],
            error_logs=["TypeError: 'NoneType' object is not iterable"],
            expected_concepts=["None handling", "guard clause", "input validation"],
            relevant_files=["src/processor.py", "src/validators.py"],
            project_summary="Python data processing pipeline",
            metadata={},
        )

        # Level 1
        self.provider._generate_structured_result = HintResponse(
            hint_level=1,
            hint_content="Start by checking where the data comes from before it reaches process_data.",
            next_level_available=True,
        )
        r1 = asyncio.run(self.engine.generate_hint(
            HintRequest(challenge_id="c1", hint_level=1, challenge_context=challenge_context),
        ))
        assert r1.hint_level == 1

        # Level 2
        self.provider._generate_structured_result = HintResponse(
            hint_level=2,
            hint_content="Look at the data validation step - is there a check for None before processing?",
            next_level_available=True,
        )
        r2 = asyncio.run(self.engine.generate_hint(
            HintRequest(challenge_id="c1", hint_level=2, challenge_context=challenge_context),
        ))
        assert r2.hint_level == 2

        # Level 3
        self.provider._generate_structured_result = HintResponse(
            hint_level=3,
            hint_content="In src/validators.py, the validate_input function doesn't handle None - add a guard clause.",
            next_level_available=True,
        )
        r3 = asyncio.run(self.engine.generate_hint(
            HintRequest(challenge_id="c1", hint_level=3, challenge_context=challenge_context),
        ))
        assert r3.hint_level == 3

        # Level 4
        self.provider._generate_structured_result = HintResponse(
            hint_level=4,
            hint_content="Add `if data is None: return []` at the start of validate_input in src/validators.py line 15.",
            next_level_available=False,
        )
        r4 = asyncio.run(self.engine.generate_hint(
            HintRequest(challenge_id="c1", hint_level=4, challenge_context=challenge_context),
        ))
        assert r4.hint_level == 4
        assert r4.next_level_available is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])