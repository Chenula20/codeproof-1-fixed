# Workspace Guardian

The Workspace Guardian provides controlled, read-only access to user projects.

## Responsibilities

- Controlled project access
- Read-only project inspection
- File indexing
- Secret filtering
- Project snapshot preparation
- Providing safe project context to CodeProof

## Security Principle

> The Guardian must NEVER modify the user's original project.

## Structure

```
workspace/
├── __init__.py
├── models.py          # Data models (ProjectIndex, FileMetadata, ProjectSnapshot)
├── scanner.py         # ProjectScanner - walks and indexes project files
├── secret_filter.py   # SecretFilter - detects and redacts secrets
├── snapshot.py        # SnapshotBuilder - creates AI-ready snapshots
├── guardian.py        # WorkspaceGuardian - main entry point
└── README.md
```

## Usage

```python
from workspace import WorkspaceGuardian

guardian = WorkspaceGuardian("/path/to/user/project")

# Validate project
if guardian.validate_project():
    # Get project summary
    summary = guardian.get_project_summary()
    
    # List files
    files = guardian.list_files()
    
    # Read a file (ONLY way to read content)
    content = guardian.read_file("src/main.py")
    
    # Create snapshot for AI
    snapshot = guardian.create_snapshot()
```

## Key Features

1. **No write access** - The Guardian has no write, modify, or delete methods
2. **Secret filtering** - Automatically ignores .env files, keys, credentials
3. **Controlled reading** - All file reads go through `read_file()` with redaction
4. **Snapshots** - Creates structured snapshots for AI consumption
5. **Path validation** - Prevents directory traversal attacks