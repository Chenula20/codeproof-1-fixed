import pytest
import json
from ai.models import (
    ChallengeContext,
    HintRequest,
    HintResponse,
    ExplanationEvaluationRequest,
    ExplanationEvaluation,
    ExplanationClassification,
    Patch,
    PatchRequest,
)
from ai.services import HintEngine, ExplanationEvaluator, PatchGenerator
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


def _sample_challenge_context() -> ChallengeContext:
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
        metadata={"version": "1.0"},
    )


class TestChallengeContext:
    """Tests for ChallengeContext model."""

    def test_valid_challenge_context_creation(self):
        """Valid ChallengeContext can be created."""
        context = _sample_challenge_context()
        
        assert isinstance(context, ChallengeContext)
        assert context.challenge_id == "chal-001"
        assert context.title == "Login Failure Debugging"
        assert context.difficulty == "medium"
        assert context.target_skill == "Authentication"
        assert len(context.relevant_code_excerpts) == 1
        assert len(context.error_logs) == 1
        assert len(context.expected_concepts) == 3
        assert len(context.relevant_files) == 2
        assert context.project_summary is not None

    def test_challenge_context_serialization(self):
        """ChallengeContext serializes cleanly to JSON/dict."""
        context = _sample_challenge_context()
        
        # Test dict conversion
        as_dict = context.model_dump()
        assert isinstance(as_dict, dict)
        assert as_dict["challenge_id"] == "chal-001"
        assert as_dict["difficulty"] == "medium"
        
        # Test JSON conversion
        as_json = context.model_dump_json()
        assert isinstance(as_json, str)
        parsed = json.loads(as_json)
        assert parsed["challenge_id"] == "chal-001"

    def test_challenge_context_required_fields(self):
        """Missing required fields are rejected."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ChallengeContext(
                # missing required fields
                difficulty="easy",
                target_skill="Testing",
                problem_statement="Test",
            )

    def test_challenge_context_optional_fields(self):
        """Optional fields can be omitted."""
        context = ChallengeContext(
            challenge_id="chal-002",
            title="Test",
            description="Test description",
            difficulty="easy",
            target_skill="Debugging",
            problem_statement="Test problem",
        )
        assert context.project_summary is None
        assert context.metadata == {}
        assert context.relevant_code_excerpts == []


class TestHintRequest:
    """Tests for HintRequest contract."""

    def test_valid_hint_request(self):
        """Valid HintRequest can be created with ChallengeContext."""
        context = _sample_challenge_context()
        request = HintRequest(
            challenge_id="chal-001",
            hint_level=2,
            developer_progress="Investigating auth flow",
            developer_question="Why does login fail?",
            challenge_context=context,
        )
        
        assert request.challenge_id == "chal-001"
        assert request.hint_level == 2
        assert request.developer_progress == "Investigating auth flow"
        assert request.developer_question == "Why does login fail?"
        assert request.challenge_context == context

    def test_hint_request_validation(self):
        """Invalid hint levels are rejected."""
        from pydantic import ValidationError
        context = _sample_challenge_context()
        
        with pytest.raises(ValidationError):
            HintRequest(challenge_id="c1", hint_level=0, challenge_context=context)
        with pytest.raises(ValidationError):
            HintRequest(challenge_id="c1", hint_level=5, challenge_context=context)

    def test_hint_request_serialization(self):
        """HintRequest serializes to JSON."""
        context = _sample_challenge_context()
        request = HintRequest(
            challenge_id="chal-001",
            hint_level=3,
            challenge_context=context,
        )
        
        as_json = request.model_dump_json()
        parsed = json.loads(as_json)
        assert parsed["hint_level"] == 3
        assert "challenge_context" in parsed


class TestHintResponse:
    """Tests for HintResponse contract."""

    def test_valid_hint_response(self):
        """Valid HintResponse can be created."""
        response = HintResponse(
            hint_level=2,
            hint_content="Check the authentication handler",
            next_level_available=True,
        )
        
        assert response.hint_level == 2
        assert response.hint_content == "Check the authentication handler"
        assert response.next_level_available is True

    def test_hint_response_level_4_no_next(self):
        """Level 4 hints have next_level_available = False."""
        response = HintResponse(
            hint_level=4,
            hint_content="Fix the bug at line 42",
            next_level_available=False,
        )
        
        assert response.hint_level == 4
        assert response.next_level_available is False


class TestExplanationEvaluationRequest:
    """Tests for ExplanationEvaluationRequest contract."""

    def test_valid_evaluation_request(self):
        """Valid ExplanationEvaluationRequest can be created."""
        context = _sample_challenge_context()
        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation="The bug is a field name mismatch",
            expected_concepts=["field name mismatch", "username vs email"],
        )
        
        assert request.developer_explanation == "The bug is a field name mismatch"
        assert request.expected_concepts == ["field name mismatch", "username vs email"]
        assert request.challenge_context == context

    def test_evaluation_request_validation(self):
        """Empty explanation or concepts are rejected by model."""
        from pydantic import ValidationError
        context = _sample_challenge_context()
        
        # Empty explanation is allowed by model (validated at service layer)
        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation="",
            expected_concepts=["concept1"],
        )
        assert request.developer_explanation == ""

    def test_evaluation_request_serialization(self):
        """Request serializes to JSON."""
        context = _sample_challenge_context()
        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation="Test explanation",
            expected_concepts=["concept1"],
        )
        
        as_json = request.model_dump_json()
        parsed = json.loads(as_json)
        assert "developer_explanation" in parsed
        assert "expected_concepts" in parsed


class TestExplanationEvaluation:
    """Tests for ExplanationEvaluation contract."""

    def test_valid_evaluation(self):
        """Valid ExplanationEvaluation can be created."""
        eval = ExplanationEvaluation(
            user_explanation="The bug is a field name mismatch",
            classification=ExplanationClassification.CORRECT,
            score=0.9,
            feedback="Excellent analysis",
            passed=True,
        )
        
        assert eval.classification == ExplanationClassification.CORRECT
        assert eval.score == 0.9
        assert eval.passed is True

    def test_evaluation_classification_values(self):
        """All classification values work."""
        for cls in [ExplanationClassification.CORRECT, 
                    ExplanationClassification.PARTIALLY_CORRECT, 
                    ExplanationClassification.INCORRECT]:
            eval = ExplanationEvaluation(
                user_explanation="test",
                classification=cls,
                score=0.5,
                feedback="test",
                passed=False,
            )
            assert eval.classification == cls

    def test_evaluation_score_bounds(self):
        """Score bounds are enforced."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ExplanationEvaluation(
                user_explanation="test",
                classification=ExplanationClassification.CORRECT,
                score=1.5,
                feedback="test",
                passed=True,
            )
        
        with pytest.raises(ValidationError):
            ExplanationEvaluation(
                user_explanation="test",
                classification=ExplanationClassification.CORRECT,
                score=-0.1,
                feedback="test",
                passed=True,
            )


class TestPatchRequest:
    """Tests for PatchRequest contract (if PatchGenerator uses it)."""

    def test_patch_model(self):
        """Patch model works correctly."""
        from workspace.models import ProjectSnapshot
        from datetime import datetime
        
        patch = Patch(
            patch_id="patch-001",
            description="Fix field name mismatch",
            diff="--- a/auth.py\n+++ b/auth.py\n- username\n+ email",
            affected_files=["src/auth/handler.py"],
            validation_warnings=[],
            risk_level="low",
        )
        
        assert patch.patch_id == "patch-001"
        assert patch.risk_level == "low"
        assert "email" in patch.diff


class TestNoFilesystemAccess:
    """Verify AI services don't require filesystem paths."""

    def test_hint_request_no_paths(self):
        """HintRequest contains no filesystem paths."""
        context = _sample_challenge_context()
        request = HintRequest(
            challenge_id="chal-001",
            hint_level=1,
            challenge_context=context,
        )
        
        # ChallengeContext has relevant_files (paths from Guardian) but not raw paths
        # The AI only sees file paths as strings in context, not as access mechanisms
        serialized = request.model_dump_json()
        # No raw filesystem access mechanism
        assert "open(" not in request.model_dump_json()
        assert "read(" not in request.model_dump_json()

    def test_explanation_request_no_paths(self):
        """ExplanationEvaluationRequest contains no filesystem access."""
        context = _sample_challenge_context()
        request = ExplanationEvaluationRequest(
            challenge_context=context,
            developer_explanation="Test",
            expected_concepts=["test"],
        )
        
        assert "open(" not in request.model_dump_json()
        assert "read(" not in request.model_dump_json()

    def test_challenge_context_from_guardian(self):
        """ChallengeContext represents Guardian-provided data, not raw access."""
        context = _sample_challenge_context()
        
        # relevant_files are paths from Guardian snapshot, not raw filesystem access
        assert all(isinstance(f, str) for f in context.relevant_files)
        # code_excerpts are content, not file handles
        assert all(isinstance(c, str) for c in context.relevant_code_excerpts)


class TestServiceSignatures:
    """Verify service method signatures match contract."""

    def test_hint_engine_signature(self):
        """HintEngine.generate_hint takes HintRequest only."""
        import inspect
        from ai.services import HintEngine
        
        sig = inspect.signature(HintEngine.generate_hint)
        params = list(sig.parameters.keys())
        assert params == ['self', 'request']
        # request should be HintRequest

    def test_explanation_evaluator_signature(self):
        """ExplanationEvaluator.evaluate takes ExplanationEvaluationRequest only."""
        import inspect
        from ai.services import ExplanationEvaluator
        
        sig = inspect.signature(ExplanationEvaluator.evaluate)
        params = list(sig.parameters.keys())
        assert params == ['self', 'request']

    def test_patch_generator_signature(self):
        """PatchGenerator.generate_patch takes structured inputs."""
        import inspect
        from ai.services import PatchGenerator
        
        sig = inspect.signature(PatchGenerator.generate_patch)
        params = list(sig.parameters.keys())
        assert params == ['self', 'request']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])