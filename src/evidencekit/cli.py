from __future__ import annotations

import argparse
import sys
from pathlib import Path

from evidencekit.collect import build_manifest
from evidencekit.config import write_default_config
from evidencekit.errors import EvidenceKitError
from evidencekit.report import render_json, render_markdown
from evidencekit.validate import load_and_validate
from evidencekit.verify import verify_manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evidencekit", description="Reproducible evidence packages")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create .evidencekit/config.yml")
    init.add_argument("--force", action="store_true")

    collect = sub.add_parser("collect", help="collect artifacts and create an Evidence Manifest")
    collect.add_argument("--config", default=".evidencekit/config.yml")

    validate = sub.add_parser("validate", help="validate schema and manifest digest")
    validate.add_argument("manifest")

    verify = sub.add_parser("verify", help="verify manifest and artifact integrity")
    verify.add_argument("manifest")
    verify.add_argument("--workspace")

    report = sub.add_parser("report", help="render a report")
    report.add_argument("manifest")
    report.add_argument("--format", choices=["markdown", "json"], default="markdown")
    report.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            print(write_default_config(Path.cwd(), force=args.force))
            return 0
        if args.command == "collect":
            manifest, path = build_manifest(Path(args.config))
            print(f"wrote {path} ({len(manifest['artifacts'])} artifacts)")
            return 0
        if args.command == "validate":
            load_and_validate(Path(args.manifest))
            print("valid")
            return 0
        if args.command == "verify":
            _, problems = verify_manifest(
                Path(args.manifest),
                Path(args.workspace) if args.workspace else None,
            )
            if problems:
                for problem in problems:
                    print(problem, file=sys.stderr)
                return 2
            print("verified")
            return 0
        if args.command == "report":
            manifest = load_and_validate(Path(args.manifest))
            rendered = render_markdown(manifest) if args.format == "markdown" else render_json(manifest)
            if args.output:
                Path(args.output).write_text(rendered, encoding="utf-8")
                print(args.output)
            else:
                print(rendered, end="")
            return 0
    except EvidenceKitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1
