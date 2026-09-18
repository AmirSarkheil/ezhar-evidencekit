from __future__ import annotations

import json
from pathlib import Path

from evidencekit.schema import EVIDENCE_MANIFEST_V1


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "schemas" / "evidence-manifest-v1.schema.json"
    target.write_text(json.dumps(EVIDENCE_MANIFEST_V1, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
