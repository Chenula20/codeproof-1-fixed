from typing import Literal

from pydantic import BaseModel, Field


class OpenProject(BaseModel):
    path: str = Field(default="", max_length=4096)


class AnalysisRequest(BaseModel):
    use_ai: bool = False


class ChallengeRequest(BaseModel):
    issue: str = Field(default="", max_length=4000)
    target_file: str = Field(default="", max_length=512)


class ExplanationRequest(BaseModel):
    explanation: str = Field(min_length=10, max_length=8000)


class RunRequest(BaseModel):
    runner: Literal["python-unittest", "python-pytest", "node-test"] = "python-unittest"


class Skill(BaseModel):
    category: str
    relevance: float
    confidence: float
    evidence: list[str]


class Evaluation(BaseModel):
    passed: bool
    feedback: str
    score: float


class PatchView(BaseModel):
    description: str
    diff: str
    affected_files: list[str]
    risk_level: str = "medium"
    validation_warnings: list[str] = Field(default_factory=list)


class Validation(BaseModel):
    status: Literal["passed", "failed", "unavailable", "timeout", "not_run"] = "not_run"
    output: str = "Validation has not run."
    duration_ms: int = 0
    original_unchanged: bool | None = None
    checks: list[str] = Field(default_factory=list)


class SessionView(BaseModel):
    id: str
    name: str
    sample: bool
    mode: str = "Local backend"
    provider: str = "Local inspection"
    phase: str = "analyzed"
    files: dict[str, str]
    summary: str
    technologies: list[str]
    issues: list[str]
    skills: list[Skill]
    challenge_title: str = ""
    challenge_description: str = ""
    relevant_files: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    evaluation: Evaluation | None = None
    patch: PatchView | None = None
    validation: Validation = Field(default_factory=Validation)
    activity: list[str] = Field(default_factory=list)
