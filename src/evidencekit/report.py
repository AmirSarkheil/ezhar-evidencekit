from __future__ import annotations

import html
import json
from typing import Any


_MARKDOWN_SPECIAL = "\\*_{}[]()#+!|" + chr(96)


def _markdown_text(value: Any) -> str:
    safe_text = str(value).encode("utf-8", errors="backslashreplace").decode("utf-8")
    text = html.escape(safe_text, quote=False)
    text = text.replace("\r", " ").replace("\n", " ")
    for char in _MARKDOWN_SPECIAL:
        text = text.replace(char, f"\\{char}")
    return text


def render_markdown(manifest: dict[str, Any]) -> str:
    run = manifest["run"]
    env = manifest["environment"]
    lines = [
        "# EvidenceKit Report",
        "",
        f"- **Schema:** {_markdown_text(manifest['schema_version'])}",
        f"- **Run ID:** {_markdown_text(run['id'])}",
        f"- **Started:** {_markdown_text(run['started_at'])}",
        f"- **Source revision:** {_markdown_text(run.get('source_revision') or 'not captured')}",
        (
            f"- **Environment:** {_markdown_text(env['os'])} / "
            f"{_markdown_text(env['runtime'])}"
        ),
        f"- **Manifest SHA-256:** {_markdown_text(manifest['manifest_sha256'])}",
        "",
        "## Checks",
        "",
    ]

    checks = manifest.get("checks", [])
    if not checks:
        lines.append("_No checks recorded._")
    else:
        lines.extend(["| Check | Status | Evidence |", "|---|---|---|"])
        for check in checks:
            lines.append(
                "| "
                f"{_markdown_text(check['name'])} | "
                f"{_markdown_text(check['status'])} | "
                f"{_markdown_text(check.get('evidence_ref', ''))} |"
            )

    lines.extend(["", "## Artifacts", ""])
    artifacts = manifest.get("artifacts", [])
    if not artifacts:
        lines.append("_No artifacts recorded._")
    else:
        lines.extend(["| Path | Bytes | SHA-256 |", "|---|---:|---|"])
        for artifact in artifacts:
            lines.append(
                "| "
                f"{_markdown_text(artifact['path'])} | "
                f"{_markdown_text(artifact['size'])} | "
                f"{_markdown_text(artifact['sha256'])} |"
            )

    warnings = manifest.get("warnings", [])
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {_markdown_text(warning)}" for warning in warnings)

    lines.extend(
        [
            "",
            "## Scope",
            "",
            "This report describes captured engineering evidence and integrity metadata. "
            "It is not a certification, compliance attestation, or proof of real-world outcome.",
            "",
        ]
    )
    return "\n".join(lines)


def render_json(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
