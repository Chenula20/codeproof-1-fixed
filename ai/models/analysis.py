from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SkillEstimate(BaseModel):
    """Estimate of a specific engineering skill relevance/strength."""
    category: str = Field(..., description="Skill category name")
    relevance: float = Field(..., ge=0.0, le=1.0, description="How relevant this skill is to the project (0.0-1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this estimate (0.0-1.0)")
    evidence: List[str] = Field(default_factory=list, description="Observed evidence from the project")


class ProjectAnalysis(BaseModel):
    """Represents the analysis of a user's project."""
    project_id: str = Field(..., description="Unique identifier for the project")
    summary: str = Field(..., description="High-level summary of the project")
    technologies: List[str] = Field(default_factory=list, description="Technologies detected in the project")
    issues: List[str] = Field(default_factory=list, description="Issues identified during analysis")
    skills: List[str] = Field(default_factory=list, description="Engineering skills relevant to the project")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of analysis")


class EngineeringSkillMap(BaseModel):
    """Maps engineering skills required for a project."""
    project_id: str = Field(..., description="Unique identifier for the project")
    skills: List[str] = Field(default_factory=list, description="Required engineering skills (legacy)")
    skill_estimates: List[SkillEstimate] = Field(default_factory=list, description="Detailed skill estimates per category")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of skill map generation")