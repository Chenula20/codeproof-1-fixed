import pytest
from ai.models import (
    ProjectAnalysis,
    EngineeringSkillMap,
    HintRequest,
    HintResponse,
    ExplanationEvaluation,
    ExplanationClassification,
    Patch,
)
from ai.providers import AIProviderConfig


class TestAIModels:
    """Tests for AI data models."""

    def test_project_analysis(self):
        """Test ProjectAnalysis model."""
        analysis = ProjectAnalysis(
            project_id="test-123",
            summary="A test project",
            technologies=["Python", "FastAPI"],
            issues=["Missing tests"],
            skills=["API design", "Testing"],
        )
        assert analysis.project_id == "test-123"
        assert analysis.summary == "A test project"
        assert "Python" in analysis.technologies
        assert "Missing tests" in analysis.issues
        assert "API design" in analysis.skills

    def test_engineering_skill_map(self):
        """Test EngineeringSkillMap model."""
        skill_map = EngineeringSkillMap(
            project_id="test-123",
            skills=["Python", "Testing", "CI/CD"],
        )
        assert skill_map.project_id == "test-123"
        assert len(skill_map.skills) == 3

    def test_hint_request(self):
        """Test HintRequest model."""
        from ai.models import ChallengeContext

        context = ChallengeContext(
            challenge_id="chal-1",
            title="Test Challenge",
            description="Test description",
            difficulty="easy",
            target_skill="Testing",
            problem_statement="Test problem",
        )

        request = HintRequest(
            challenge_id="chal-1",
            hint_level=2,
            challenge_context=context,
        )
        assert request.challenge_id == "chal-1"
        assert request.hint_level == 2
        assert request.challenge_context is not None

    def test_hint_request_invalid_level(self):
        """Test HintRequest rejects invalid hint level."""
        from pydantic import ValidationError
        from ai.models import ChallengeContext

        context = ChallengeContext(
            challenge_id="c1",
            title="Test Challenge",
            description="Test description",
            difficulty="easy",
            target_skill="Testing",
            problem_statement="Test problem",
        )

        with pytest.raises(ValidationError):
            HintRequest(challenge_id="c1", hint_level=0, challenge_context=context)
        with pytest.raises(ValidationError):
            HintRequest(challenge_id="c1", hint_level=5, challenge_context=context)

    def test_hint_response(self):
        """Test HintResponse model."""
        response = HintResponse(
            hint_level=1,
            hint_content="Think about edge cases",
            next_level_available=True,
        )
        assert response.hint_level == 1
        assert response.next_level_available is True

    def test_explanation_evaluation(self):
        """Test ExplanationEvaluation model."""
        eval = ExplanationEvaluation(
            user_explanation="This function adds two numbers",
            classification=ExplanationClassification.CORRECT,
            score=0.8,
            feedback="Good but missing edge cases",
            passed=True,
        )
        assert eval.score == 0.8
        assert eval.passed is True
        assert eval.classification == ExplanationClassification.CORRECT

    def test_explanation_evaluation_score_bounds(self):
        """Test score bounds."""
        with pytest.raises(ValueError):
            ExplanationEvaluation(
                user_explanation="test",
                score=1.5,
                feedback="test",
                passed=True,
            )
        with pytest.raises(ValueError):
            ExplanationEvaluation(
                user_explanation="test",
                score=-0.1,
                feedback="test",
                passed=True,
            )

    def test_patch(self):
        """Test Patch model."""
        patch = Patch(
            patch_id="patch-1",
            description="Fix bug in login",
            diff="--- a/auth.py\n+++ b/auth.py\n@@ -1,3 +1,4 @@\n+import logging\n def login():\n     pass",
            affected_files=["auth.py"],
            validation_warnings=["Test coverage low"],
            risk_level="medium",
        )
        assert patch.patch_id == "patch-1"
        assert patch.risk_level == "medium"
        assert len(patch.affected_files) == 1


class TestAIProviderConfig:
    """Tests for AIProviderConfig."""

    def test_valid_config(self):
        """Test valid provider config."""
        config = AIProviderConfig(
            api_key="test-key",
            model="gemini-1.5-pro",
            temperature=0.7,
            max_tokens=4096,
            timeout=60,
        )
        assert config.api_key == "test-key"
        assert config.model == "gemini-1.5-pro"

    def test_temperature_bounds(self):
        """Test temperature bounds."""
        with pytest.raises(ValueError):
            AIProviderConfig(api_key="key", model="m", temperature=-0.1)
        with pytest.raises(ValueError):
            AIProviderConfig(api_key="key", model="m", temperature=2.1)

    def test_max_tokens_positive(self):
        """Test max_tokens must be positive."""
        with pytest.raises(ValueError):
            AIProviderConfig(api_key="key", model="m", max_tokens=0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])