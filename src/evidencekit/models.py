from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    sha256: str
    size: int
    media_type: str | None = None

    def to_dict(self) -> dict[str, str | int]:
        data: dict[str, str | int] = {
            "path": self.path,
            "sha256": self.sha256,
            "size": self.size,
        }
        if self.media_type:
            data["media_type"] = self.media_type
        return data


@dataclass(frozen=True)
class CheckRecord:
    name: str
    status: str
    evidence_ref: str | None = None
    summary: str | None = None

    def to_dict(self) -> dict[str, str]:
        return {key: value for key, value in asdict(self).items() if value is not None}
