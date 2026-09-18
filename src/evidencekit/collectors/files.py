from __future__ import annotations

import fnmatch
from pathlib import Path

from evidencekit.errors import SecurityError
from evidencekit.integrity import looks_sensitive, media_type_for, safe_artifact_path, sha256_file
from evidencekit.models import ArtifactRecord


def _matches_any(relative: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def collect_artifacts(
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_artifact_bytes: int,
) -> tuple[list[ArtifactRecord], list[str]]:
    found: dict[str, ArtifactRecord] = {}
    warnings: list[str] = []

    for pattern in includes:
        for candidate in root.glob(pattern):
            if candidate.is_dir():
                continue
            relative = candidate.relative_to(root).as_posix()
            if _matches_any(relative, excludes):
                continue
            try:
                safe = safe_artifact_path(root, relative)
            except SecurityError as exc:
                warnings.append(str(exc))
                continue

            size = safe.stat().st_size
            if size > max_artifact_bytes:
                warnings.append(
                    f"skipped oversized artifact {relative} ({size} > {max_artifact_bytes} bytes)"
                )
                continue
            if looks_sensitive(safe):
                warnings.append(f"artifact name may contain sensitive material: {relative}")

            found[relative] = ArtifactRecord(
                path=relative,
                sha256=sha256_file(safe),
                size=size,
                media_type=media_type_for(safe),
            )

    return [found[key] for key in sorted(found)], warnings
