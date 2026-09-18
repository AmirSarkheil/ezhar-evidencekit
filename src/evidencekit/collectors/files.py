from __future__ import annotations

import fnmatch
from pathlib import Path

from evidencekit.errors import SecurityError
from evidencekit.integrity import hash_artifact, looks_sensitive, media_type_for
from evidencekit.models import ArtifactRecord


_PROTECTED_PARTS = {".git", ".evidencekit"}


def _matches_any(relative: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatch(relative, pattern)
        or (
            pattern.startswith("**/")
            and fnmatch.fnmatch(relative, pattern.removeprefix("**/"))
        )
        for pattern in patterns
    )


def _is_protected(relative: str) -> bool:
    return any(part.lower() in _PROTECTED_PARTS for part in Path(relative).parts)


def collect_artifacts(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_artifact_bytes: int,
    *,
    excluded_paths: set[str] | None = None,
) -> tuple[list[ArtifactRecord], list[str]]:
    found: dict[str, ArtifactRecord] = {}
    warnings: list[str] = []
    explicitly_excluded = excluded_paths or set()

    for pattern in includes:
        for candidate in root.glob(pattern):
            try:
                relative = candidate.relative_to(root).as_posix()
            except ValueError:
                warnings.append(f"skipped artifact outside workspace: {candidate}")
                continue

            if relative in explicitly_excluded or _is_protected(relative):
                continue
            if _matches_any(relative, excludes):
                continue

            # Directory/symlink probes are only a convenience to keep broad globs quiet.
            # The actual read below re-opens the path safely and independently.
            try:
                if candidate.is_symlink():
                    warnings.append(f"symlink artifacts are not allowed: {relative}")
                    continue
                if candidate.is_dir():
                    continue
            except OSError as exc:
                warnings.append(f"unable to inspect artifact {relative}: {exc}")
                continue

            try:
                display_path, size, digest = hash_artifact(
                    root,
                    relative,
                    max_bytes=max_artifact_bytes,
                )
            except (OSError, SecurityError) as exc:
                warnings.append(str(exc))
                continue

            if looks_sensitive(display_path):
                warnings.append(f"artifact name may contain sensitive material: {relative}")

            found[relative] = ArtifactRecord(
                path=relative,
                sha256=digest,
                size=size,
                media_type=media_type_for(display_path),
            )

    return [found[key] for key in sorted(found)], warnings
