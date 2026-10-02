import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set
from .models import ProjectIndex, FileMetadata, ProjectSnapshot
from .scanner import ProjectScanner
from .secret_filter import SecretFilter
from .security import contained_file


class SnapshotBuilder:
    """Builds project snapshots for AI consumption."""

    def __init__(
        self,
        scanner: ProjectScanner,
        secret_filter: Optional[SecretFilter] = None,
        max_file_size: int = 100_000,  # 100KB
        max_total_size: int = 5_000_000,  # 5MB
    ):
        self.scanner = scanner
        self.secret_filter = secret_filter or SecretFilter()
        self.max_file_size = max_file_size
        self.max_total_size = max_total_size

    def build_snapshot(
        self,
        project_id: Optional[str] = None,
        include_files: Optional[List[str]] = None,
        exclude_patterns: Optional[Set[str]] = None,
    ) -> ProjectSnapshot:
        """Build a project snapshot."""
        # Scan the project
        index = self.scanner.scan()

        # Filter files
        files_to_include = self._select_files(index, include_files, exclude_patterns)

        # Read file contents
        file_contents = {}
        total_size = 0
        metadata = {
            "total_files_scanned": index.total_files,
            "total_size_scanned": index.total_size,
            "files_included": len(files_to_include),
        }

        for file_meta in files_to_include:
            if total_size >= self.max_total_size:
                break

            content = self._read_file_safely(file_meta)
            if content is not None:
                if total_size + len(content.encode("utf-8")) > self.max_total_size:
                    continue
                file_contents[file_meta.path] = content
                total_size += len(content.encode("utf-8"))

        metadata["total_snapshot_size"] = total_size

        # Extract dependencies and config
        dependencies = self._extract_dependencies(index, file_contents)
        config = self._extract_config(index, file_contents)

        return ProjectSnapshot(
            project_id=project_id or str(uuid.uuid4())[:8],
            project_root=index.project_root,
            metadata=metadata,
            files=file_contents,
            dependencies=dependencies,
            config=config,
        )

    def _select_files(
        self,
        index: ProjectIndex,
        include_files: Optional[List[str]],
        exclude_patterns: Optional[Set[str]],
    ) -> List[FileMetadata]:
        """Select which files to include in the snapshot."""
        selected = []

        for file_meta in index.files:
            # Check exclude patterns
            if exclude_patterns:
                excluded = False
                for pattern in exclude_patterns:
                    if pattern in file_meta.path:
                        excluded = True
                        break
                if excluded:
                    continue

            # Check include list
            if include_files and file_meta.path not in include_files:
                continue

            # Check secret filter
            if self.secret_filter.is_secret_file(Path(file_meta.path)):
                continue

            # Check file size
            if file_meta.size > self.max_file_size:
                continue

            selected.append(file_meta)

        # Sort by importance (config files first, then source, then others)
        selected.sort(key=self._file_priority)
        return selected

    def _file_priority(self, file_meta: FileMetadata) -> tuple:
        """Determine file priority for inclusion."""
        path = file_meta.path.lower()
        name = Path(path).name.lower()

        # Config files - highest priority
        if name in {
            "package.json", "pyproject.toml", "setup.py", "requirements.txt",
            "cargo.toml", "go.mod", "pom.xml", "build.gradle", "gradle.kts",
            "dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".gitignore", ".dockerignore", "makefile", "cmake",
        }:
            return (0, path)

        # Source files
        if file_meta.language in {"python", "javascript", "typescript", "go", "rust", "java", "csharp"}:
            return (1, path)

        # Documentation
        if file_meta.language == "markdown":
            return (2, path)

        # Config files (other)
        if file_meta.language in {"json", "yaml", "toml", "ini"}:
            return (3, path)

        # Everything else
        return (4, path)

    def _read_file_safely(self, file_meta: FileMetadata) -> Optional[str]:
        """Read file content safely with secret redaction."""
        try:
            file_path = contained_file(self.scanner.project_root, file_meta.path)
            with file_path.open(encoding="utf-8", errors="replace") as stream:
                content = stream.read(self.max_file_size + 1)
            if len(content.encode("utf-8")) > self.max_file_size:
                return None
            # Redact potential secrets
            return self.secret_filter.redact_content(content)
        except (OSError, PermissionError, UnicodeDecodeError, ValueError):
            return None

    def _extract_dependencies(self, index: ProjectIndex, files: Dict[str, str]) -> Dict:
        """Extract dependency information from project files."""
        deps = {}

        # Python
        if "requirements.txt" in files:
            deps["python"] = self._parse_requirements(files["requirements.txt"])
        if "pyproject.toml" in files:
            deps["python"] = {**deps.get("python", {}), **self._parse_pyproject(files["pyproject.toml"])}

        # Node.js
        if "package.json" in files:
            deps["node"] = self._parse_package_json(files["package.json"])

        # Rust
        if "Cargo.toml" in files:
            deps["rust"] = self._parse_cargo_toml(files["Cargo.toml"])

        # Go
        if "go.mod" in files:
            deps["go"] = self._parse_go_mod(files["go.mod"])

        return deps

    def _extract_config(self, index: ProjectIndex, files: Dict[str, str]) -> Dict:
        """Extract relevant configuration."""
        config = {}

        # Git config
        if ".git/config" in files:
            config["git"] = files[".git/config"][:1000]

        # Docker
        if "Dockerfile" in files:
            config["dockerfile"] = files["Dockerfile"][:2000]

        # CI/CD
        for path in files:
            if path.startswith(".github/workflows/") or path.startswith(".gitlab-ci"):
                config["ci"] = config.get("ci", {})
                config["ci"][path] = files[path][:2000]

        return config

    def _parse_requirements(self, content: str) -> Dict:
        """Parse requirements.txt."""
        deps = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                deps[line.split("==")[0].split(">=")[0].split("<=")[0].strip()] = line
        return deps

    def _parse_pyproject(self, content: str) -> Dict:
        """Parse pyproject.toml (simplified)."""
        try:
            import tomllib
            data = tomllib.loads(content)
            return {
                "project": data.get("project", {}),
                "dependencies": data.get("project", {}).get("dependencies", []),
            }
        except Exception:
            return {}

    def _parse_package_json(self, content: str) -> Dict:
        """Parse package.json."""
        try:
            data = json.loads(content)
            return {
                "dependencies": data.get("dependencies", {}),
                "devDependencies": data.get("devDependencies", {}),
                "scripts": data.get("scripts", {}),
            }
        except Exception:
            return {}

    def _parse_cargo_toml(self, content: str) -> Dict:
        """Parse Cargo.toml (simplified)."""
        try:
            import tomllib
            data = tomllib.loads(content)
            return {
                "dependencies": data.get("dependencies", {}),
                "dev-dependencies": data.get("dev-dependencies", {}),
            }
        except Exception:
            return {}

    def _parse_go_mod(self, content: str) -> Dict:
        """Parse go.mod (simplified)."""
        deps = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("module") and not line.startswith("go "):
                parts = line.split()
                if len(parts) >= 2:
                    deps[parts[0]] = parts[1]
        return deps
