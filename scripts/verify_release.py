from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REQUIRED = [
    "README.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "MAINTAINERS.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "schemas/evidence-manifest-v1.schema.json",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [path for path in REQUIRED if not (root / path).exists()]
    if missing:
        print("missing required release files:", *missing, sep="\n- ", file=sys.stderr)
        return 2

    schema = json.loads((root / "schemas/evidence-manifest-v1.schema.json").read_text(encoding="utf-8"))
    if schema.get("properties", {}).get("schema_version", {}).get("const") != "1.0":
        print("unexpected schema version", file=sys.stderr)
        return 2

    commands = [
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "-m", "build"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode:
            return result.returncode

    print("release verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
