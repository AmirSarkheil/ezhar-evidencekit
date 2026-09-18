from __future__ import annotations

import json
from typing import Any


def render_markdown(manifest: dict[str, Any]) -> str:
    run = manifest["run"]
    env = manifest["environment"]
    lines = [
        "# EvidenceKit Report",
        "",
        f"- **Schema:** {manifest['schema_version']}",
        f"- **Run ID:** {run['id']}",
        f"- **Started:** {run['started_at']}",
        f"- **Source revision:** {run.get('source_revision') or 'not captured'}",
        f"- **Environment:** {env['os']} / {env['runtime']}",
        f"- **Manifest SHA-256:** {manifest['manifest_sha256']}",
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
                f"| {check['name']} | {check['status']} | {check.get('evidence_ref', '')} |"
            )

    lines.extend(["", "## Artifacts", ""])
    artifacts = manifest.get("artifacts", [])
    if not artifacts:
        lines.append("_No artifacts recorded._")
    else:
        lines.extend(["| Path | Bytes | SHA-256 |", "|---|---:|---|"])
        for artifact in artifacts:
            lines.append(
                f"| {artifact['path']} | {artifact['size']} | {artifact['sha256']} |"
            )

    warnings = manifest.get("warnings", [])
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    lines.extend([
        "",
        "## Scope",
        "",
        "This report describes captured engineering evidence and integrity metadata. "
        "It is not a certification, compliance attestation, or proof of real-world outcome.",
        "",
    ])
    return "\n".join(lines)


def render_json(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"
