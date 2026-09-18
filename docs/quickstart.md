# Quickstart

## 1. Install

For development from this repository:

```bash
python -m pip install -e .
```

## 2. Initialize

From the repository you want to describe with evidence:

```bash
evidencekit init
```

This creates `.evidencekit/config.yml`.

## 3. Produce an artifact

For example, place a test output in `artifacts/`.

```bash
mkdir -p artifacts
printf "example evidence\n" > artifacts/example.txt
```

## 4. Collect and validate

```bash
evidencekit collect --config .evidencekit/config.yml
evidencekit validate evidence.json
evidencekit verify evidence.json
```

## 5. Render a report

```bash
evidencekit report evidence.json --format markdown --output evidence-report.md
```

If an artifact changes after collection, `verify` returns a non-zero exit code and reports the mismatch.

The manifest proves only what it records. It does not certify the software or prove a real-world outcome.
