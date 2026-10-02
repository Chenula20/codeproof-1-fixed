from pathlib import Path
from typing import Dict, List, Optional, Set
from .models import ProjectIndex, FileMetadata, ProjectSnapshot
from .scanner import ProjectScanner
from .secret_filter import SecretFilter
from .snapshot import SnapshotBuilder
from .security import contained_file


class WorkspaceGuardian:
    """
    Workspace Guardian - Controls access to user projects.
    
    The Guardian provides read-only, controlled access to project files.
    It NEVER modifies the original project.
    """

    def __init__(
        self,
        project_root: str,
        ignore_patterns: Optional[Set[str]] = None,
        secret_filter: Optional[SecretFilter] = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.scanner = ProjectScanner(str(self.project_root), ignore_patterns)
        self.secret_filter = secret_filter or SecretFilter()
        self.snapshot_builder = SnapshotBuilder(self.scanner, self.secret_filter)
        self._index: Optional[ProjectIndex] = None

    def validate_project(self) -> bool:
        """Validate that the project root exists and is a directory."""
        return self.project_root.exists() and self.project_root.is_dir()

    def get_index(self, force_refresh: bool = False) -> ProjectIndex:
        """Get the project index, scanning if necessary."""
        if self._index is None or force_refresh:
            self._index = self.scanner.scan()
        return self._index

    def list_files(self, force_refresh: bool = False) -> List[FileMetadata]:
        """List all indexed files in the project."""
        return self.get_index(force_refresh).files

    def read_file(self, relative_path: str) -> Optional[str]:
        """
        Read a file through Guardian-controlled access.
        
        This is the ONLY way to read file content - no direct filesystem access.
        """
        # Validate path is within project root
        try:
            file_path = contained_file(self.project_root, relative_path)
        except ValueError:
            if not (self.project_root / relative_path).exists() and ".." not in Path(relative_path).parts:
                return None
            raise

        # Check if file is ignored/secret
        if self.secret_filter.is_secret_file(Path(relative_path)):
            return None

        # Read and redact
        try:
            if file_path.stat().st_size > 5_000_000:
                return None
            with file_path.open(encoding="utf-8", errors="replace") as stream:
                content = stream.read(5_000_001)
            if len(content) > 5_000_000:
                return None
            return self.secret_filter.redact_content(content)
        except (OSError, PermissionError, UnicodeDecodeError):
            return None

    def get_file_metadata(self, relative_path: str) -> Optional[FileMetadata]:
        """Get metadata for a specific file."""
        index = self.get_index()
        for file_meta in index.files:
            if file_meta.path == relative_path:
                return file_meta
        return None

    def create_snapshot(
        self,
        project_id: Optional[str] = None,
        include_files: Optional[List[str]] = None,
        exclude_patterns: Optional[Set[str]] = None,
    ) -> ProjectSnapshot:
        """Create a project snapshot for AI consumption."""
        return self.snapshot_builder.build_snapshot(
            project_id=project_id,
            include_files=include_files,
            exclude_patterns=exclude_patterns,
        )

    def get_project_summary(self) -> Dict:
        """Get a summary of the project."""
        index = self.get_index()
        languages = {}
        for f in index.files:
            if f.language:
                languages[f.language] = languages.get(f.language, 0) + 1

        return {
            "project_root": str(self.project_root),
            "total_files": index.total_files,
            "total_size": index.total_size,
            "languages": languages,
            "indexed_at": index.indexed_at.isoformat() if index.indexed_at else None,
        }

    def verify_no_write_access(self) -> bool:
        """
        Verify that this Guardian instance has no write methods.
        
        This is a runtime check to ensure the Guardian never exposes write functionality.
        """
        write_methods = [
            "write_file", "modify_file", "save_file", "create_file",
            "delete_file", "remove_file", "write", "save", "create",
            "delete", "remove", "mkdir", "rmdir",
        ]
        for method in write_methods:
            if hasattr(self, method):
                return False
        return True
