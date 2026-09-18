class EvidenceKitError(Exception):
    """Base error for expected EvidenceKit failures."""


class ConfigError(EvidenceKitError):
    """Configuration is invalid or unsafe."""


class SecurityError(EvidenceKitError):
    """A path or input violates the workspace security boundary."""


class ValidationFailure(EvidenceKitError):
    """An Evidence Manifest failed validation."""
