import re
from pathlib import Path
from typing import List, Pattern, Set


class SecretFilter:
    """Filters out files and content that may contain secrets."""

    # File patterns that commonly contain secrets
    SECRET_FILE_PATTERNS = [
        r"\.env(\..*)?$",
        r"\.env\.",
        r"credentials?\.",
        r"service-account",
        r"secret",
        r"private[_-]?key",
        r"\.pem$",
        r"\.key$",
        r"\.p12$",
        r"\.pfx$",
        r"\.cer$",
        r"\.crt$",
        r"id_rsa",
        r"id_ed25519",
        r"known_hosts",
        r"authorized_keys",
        r"\.kube/config",
        r"\.aws/credentials",
        r"\.docker/config\.json",
        r"\.npmrc",
        r"\.pypirc",
        r"\.gemrc",
        r"secrets?\.ya?ml",
        r"vault",
    ]

    # Content patterns that may indicate secrets
    SECRET_CONTENT_PATTERNS = [
        # API keys
        (re.compile(r"[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{20,}[\"']?"), "API key"),
        (re.compile(r"[Aa][Pp][Ii][_-]?[Ss][Ee][Cc][Rr][Ee][Tt]\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{20,}[\"']?"), "API secret"),
        # AWS
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
        (re.compile(r"[Aa][Ww][Ss][_-]?[Ss][Ee][Cc][Rr][Ee][Tt]\s*[=:]\s*[\"']?[A-Za-z0-9/+=]{40}[\"']?"), "AWS secret key"),
        # Generic secrets
        (re.compile(r"[Ss][Ee][Cc][Rr][Ee][Tt]\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{20,}[\"']?"), "Secret"),
        (re.compile(r"[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]\s*[=:]\s*[\"']?[^\s\"']{8,}[\"']?"), "Password"),
        (re.compile(r"[Tt][Oo][Kk][Ee][Nn]\s*[=:]\s*[\"']?[A-Za-z0-9_\-]{20,}[\"']?"), "Token"),
        # Private keys
        (re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "Private key"),
        # Database URLs
        (re.compile(r"(postgres|mysql|mongodb|redis)://[^:\s]+:[^@\s]+@"), "Database URL with credentials"),
    ]

    def __init__(self, custom_file_patterns: List[str] = None, custom_content_patterns: List[tuple] = None):
        self.file_patterns: List[Pattern] = [re.compile(p) for p in self.SECRET_FILE_PATTERNS]
        if custom_file_patterns:
            self.file_patterns.extend([re.compile(p) for p in custom_file_patterns])

        self.content_patterns: List[tuple] = self.SECRET_CONTENT_PATTERNS.copy()
        if custom_content_patterns:
            self.content_patterns.extend(custom_content_patterns)

    def is_secret_file(self, file_path: Path) -> bool:
        """Check if a file path matches secret file patterns."""
        name = file_path.name
        relative = str(file_path)

        for pattern in self.file_patterns:
            if pattern.search(name) or pattern.search(relative):
                return True
        return False

    def scan_content(self, content: str) -> List[dict]:
        """Scan content for potential secrets."""
        findings = []
        for pattern, description in self.content_patterns:
            matches = pattern.finditer(content)
            for match in matches:
                findings.append({
                    "type": description,
                    "match": match.group()[:50],  # Truncate for safety
                    "position": match.start(),
                })
        return findings

    def filter_file_list(self, files: List[Path]) -> List[Path]:
        """Filter out files that match secret patterns."""
        return [f for f in files if not self.is_secret_file(f)]

    def redact_content(self, content: str) -> str:
        """Redact potential secrets from content."""
        redacted = content
        for pattern, description in self.content_patterns:
            redacted = pattern.sub(f"[REDACTED {description.upper()}]", redacted)
        return redacted