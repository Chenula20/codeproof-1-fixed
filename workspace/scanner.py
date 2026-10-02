import hashlib
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
from .models import FileMetadata, ProjectIndex
from .security import contained_file


class ProjectScanner:
    """Scans a project directory and builds a file index."""

    # Common patterns to ignore
    DEFAULT_IGNORE_PATTERNS = {
        # Version control
        ".git",
        ".svn",
        ".hg",
        # Dependencies
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "venv",
        "env",
        ".venv",
        "virtualenv",
        # Build outputs
        "build",
        "dist",
        "target",
        "out",
        "bin",
        "obj",
        # IDE
        ".vscode",
        ".idea",
        "*.swp",
        "*.swo",
        # OS
        ".DS_Store",
        "Thumbs.db",
        # Logs
        "*.log",
        "logs",
        # Temp
        "tmp",
        "temp",
        "*.tmp",
        # Secrets (will also be caught by SecretFilter)
        ".env",
        ".env.*",
        "*.pem",
        "*.key",
        "id_rsa*",
        "id_ed25519*",
        "*.pfx",
        "*.p12",
    }

    # Text file extensions to index
    TEXT_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
        ".toml", ".ini", ".cfg", ".conf", ".config",
        ".md", ".txt", ".rst", ".adoc",
        ".html", ".htm", ".css", ".scss", ".sass", ".less",
        ".sql", ".sh", ".bash", ".zsh", ".fish",
        ".dockerfile", ".dockerignore",
        ".gitignore", ".gitattributes",
        ".env.example", ".env.template",
        ".csv", ".tsv",
        ".xml", ".xsd",
        ".proto",
        ".go", ".rs", ".java", ".kt", ".scala",
        ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
        ".cs", ".vb",
        ".rb", ".php", ".pl", ".pm",
        ".swift", ".m", ".mm",
        ".dart", ".lua", ".r",
        ".gradle", ".maven",
        ".tf", ".tfvars",
        ".helm", ".yaml",
    }

    def __init__(self, project_root: str, ignore_patterns: Optional[Set[str]] = None):
        self.project_root = Path(project_root).resolve()
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS.copy()

    def scan(self) -> ProjectIndex:
        """Scan the project and return a ProjectIndex."""
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")
        if not self.project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {self.project_root}")

        files: List[FileMetadata] = []
        total_size = 0

        for file_path in self._walk_files():
            try:
                metadata = self._get_file_metadata(file_path)
                if metadata:
                    files.append(metadata)
                    total_size += metadata.size
            except (OSError, PermissionError):
                # Skip files we can't read
                continue

        return ProjectIndex(
            project_root=str(self.project_root),
            files=files,
            total_files=len(files),
            total_size=total_size,
            ignored_patterns=list(self.ignore_patterns),
        )

    def _walk_files(self) -> List[Path]:
        """Walk the project directory and return all file paths."""
        files = []
        for root, dirs, filenames in os.walk(self.project_root):
            # Filter directories in-place to avoid traversing ignored dirs
            dirs[:] = [d for d in dirs if not self._is_ignored(Path(root) / d)
                       and not (Path(root) / d).is_symlink()
                       and not getattr(Path(root) / d, "is_junction", lambda: False)()]

            for filename in filenames:
                file_path = Path(root) / filename
                if not self._is_ignored(file_path):
                    try:
                        contained_file(self.project_root, str(file_path.relative_to(self.project_root)))
                    except ValueError:
                        continue
                    if file_path.stat().st_size <= 5_000_000:
                        files.append(file_path)
                    if len(files) >= 10000:
                        return files
        return files

    def _is_ignored(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        relative = path.relative_to(self.project_root)
        relative_str = str(relative)
        name = path.name

        # Check exact name matches
        if name in self.ignore_patterns:
            return True

        # Check pattern matches
        for pattern in self.ignore_patterns:
            if pattern.startswith("*") and name.endswith(pattern[1:]):
                return True
            if pattern in relative_str:
                return True

        return False

    def _get_file_metadata(self, file_path: Path) -> Optional[FileMetadata]:
        """Get metadata for a single file."""
        try:
            stat = file_path.stat()
        except (OSError, PermissionError):
            return None

        # Check if it's a text file we should index
        if not self._is_text_file(file_path):
            return None

        # Calculate hash
        file_hash = self._calculate_hash(file_path)

        # Detect mime type and language
        mime_type, _ = mimetypes.guess_type(str(file_path))
        language = self._detect_language(file_path)

        return FileMetadata(
            path=str(file_path.relative_to(self.project_root)),
            size=stat.st_size,
            hash=file_hash,
            mime_type=mime_type,
            language=language,
            is_text=True,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file should be treated as text."""
        # Check extension
        if file_path.suffix.lower() in self.TEXT_EXTENSIONS:
            return True

        # Check if filename matches known text files
        name = file_path.name.lower()
        if name in {"dockerfile", "makefile", "rakefile", "gemfile", "vagrantfile"}:
            return True
        if name.startswith(".") and name.endswith((".ignore", ".attributes", ".example", ".template")):
            return True

        # Try to detect by reading first few bytes
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                # Check for null bytes (binary indicator)
                if b"\x00" in chunk:
                    return False
                # Check if mostly printable ASCII/UTF-8
                try:
                    chunk.decode("utf-8")
                    return True
                except UnicodeDecodeError:
                    return False
        except (OSError, PermissionError):
            return False

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".md": "markdown",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "zsh",
            ".dockerfile": "dockerfile",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".kt": "kotlin",
            ".scala": "scala",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".dart": "dart",
            ".lua": "lua",
            ".r": "r",
            ".tf": "terraform",
            ".tfvars": "terraform",
        }
        return ext_map.get(file_path.suffix.lower())
