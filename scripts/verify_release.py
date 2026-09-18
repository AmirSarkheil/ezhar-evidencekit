from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
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


def _venv_python(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _run(command: list[str], root: Path) -> int:
    print("+", " ".join(command))
    return subprocess.run(command, cwd=root, check=False).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    missing = [path for path in REQUIRED if not (root / path).exists()]
    if missing:
        print("missing required release files:", *missing, sep="\n- ", file=sys.stderr)
        return 2

    try:
        schema = json.loads(
            (root / "schemas/evidence-manifest-v1.schema.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"unable to read schema: {exc}", file=sys.stderr)
        return 2

    if schema.get("properties", {}).get("schema_version", {}).get("const") != "1.0":
        print("unexpected schema version", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="evidencekit-release-") as temp:
        environment = Path(temp) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = _venv_python(environment)

        commands = [
            [str(python), "-m", "pip", "install", "--upgrade", "pip"],
            [str(python), "-m", "pip", "install", "-e", f"{root}[dev]"],
            [str(python), "-m", "ruff", "check", "."],
            [str(python), "-m", "mypy", "src/evidencekit"],
            [str(python), "-m", "pytest", "-q"],
            [str(python), "-m", "build"],
        ]
        for command in commands:
            result = _run(command, root)
            if result:
                return result

    print("release verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
