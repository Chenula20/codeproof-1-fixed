from typing import List, Optional
from pydantic import BaseModel, Field
from workspace.models import ProjectSnapshot


class ChallengeContext(BaseModel):
    """Structured context for a coding challenge.
    
    This model represents the challenge information that the backend
    sends to the AI Engine. It contains only structured data that has
    been prepared by the backend from Guardian-provided project context.
    
    No filesystem paths or direct project access is included.
    """
    challenge_id: str = Field(..., description="Unique identifier for the challenge")
    title: str = Field(..., description="Human-readable challenge title")
    description: str = Field(..., description="Detailed problem description")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, hard")
    target_skill: str = Field(..., description="Primary engineering skill being tested")
    problem_statement: str = Field(..., description="Clear statement of the problem to solve")
    relevant_code_excerpts: List[str] = Field(default_factory=list, description="Code excerpts relevant to the challenge (from Guardian)")
    error_logs: List[str] = Field(default_factory=list, description="Error messages or log excerpts")
    expected_concepts: List[str] = Field(default_factory=list, description="Key concepts the developer should identify")
    relevant_files: List[str] = Field(default_factory=list, description="Relevant file paths (from Guardian snapshot)")
    project_summary: Optional[str] = Field(None, description="High-level project summary")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class ExplanationEvaluationRequest(BaseModel):
    """Request for evaluating a developer's explanation."""
    challenge_context: "ChallengeContext" = Field(..., description="Full challenge context")
    developer_explanation: str = Field(..., description="The developer's explanation text")
    expected_concepts: List[str] = Field(..., description="Key concepts the explanation should cover")


class PatchRequest(BaseModel):
    """Request for generating a patch from the AI engine."""
    issue_description: str = Field(..., description="Description of the issue to fix")
    project_snapshot: ProjectSnapshot = Field(..., description="Project snapshot from Guardian")
    target_files: List[str] = Field(..., description="List of target file paths to modify")


# Re-export existing models for compatibility
class ExplanationEvaluationRequest_Legacy(BaseModel):
    """Legacy request format for explanation evaluation (deprecated)."""
    user_explanation: str
    expected_concepts: List[str]
    challenge_context: dict


# Forward reference resolution
ChallengeContext.model_rebuild()