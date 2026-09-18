from __future__ import annotations

import fnmatch
from pathlib import Path

from evidencekit.errors import SecurityError
from evidencekit.integrity import looks_sensitive, media_type_for, safe_artifact_path, sha256_file
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
            if candidate.is_symlink():
                warnings.append(f"symlink artifacts are not allowed: {relative}")
                continue
            if candidate.is_dir():
                continue

            try:
                safe = safe_artifact_path(root, relative)
                if not safe.is_file():
                    warnings.append(f"skipped non-regular artifact: {relative}")
                    continue
                size = safe.stat().st_size
                if size > max_artifact_bytes:
                    warnings.append(
                        f"skipped oversized artifact {relative} "
                        f"({size} > {max_artifact_bytes} bytes)"
                    )
                    continue
                digest = sha256_file(safe)
            except (OSError, SecurityError) as exc:
                warnings.append(str(exc))
                continue

            if looks_sensitive(safe):
                warnings.append(f"artifact name may contain sensitive material: {relative}")

            found[relative] = ArtifactRecord(
                path=relative,
                sha256=digest,
                size=size,
                media_type=media_type_for(safe),
            )

    return [found[key] for key in sorted(found)], warnings
