from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """Metadata for a single file in the project."""
    path: str = Field(..., description="Relative path from project root")
    size: int = Field(..., description="File size in bytes")
    hash: str = Field(..., description="SHA256 hash of file content")
    mime_type: Optional[str] = Field(None, description="MIME type if detected")
    language: Optional[str] = Field(None, description="Programming language if detected")
    is_text: bool = Field(..., description="Whether file is text-based")
    modified_at: datetime = Field(..., description="Last modification time")


class ProjectIndex(BaseModel):
    """Index of all files in a project."""
    project_root: str = Field(..., description="Absolute path to project root")
    files: List[FileMetadata] = Field(default_factory=list, description="Indexed files")
    total_files: int = Field(default=0, description="Total number of files")
    total_size: int = Field(default=0, description="Total size in bytes")
    indexed_at: datetime = Field(default_factory=datetime.utcnow, description="Index timestamp")
    ignored_patterns: List[str] = Field(default_factory=list, description="Patterns that were ignored")


class ProjectSnapshot(BaseModel):
    """Snapshot of a project for AI consumption."""
    project_id: str = Field(..., description="Unique project identifier")
    project_root: str = Field(..., description="Project root path")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Project metadata")
    files: Dict[str, str] = Field(default_factory=dict, description="Selected file contents (path -> content)")
    dependencies: Dict[str, Any] = Field(default_factory=dict, description="Dependency information")
    config: Dict[str, Any] = Field(default_factory=dict, description="Relevant configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Snapshot creation time")