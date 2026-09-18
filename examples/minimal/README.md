# Minimal example

From this directory after installing EvidenceKit:

```bash
mkdir -p artifacts
printf "hello evidence\n" > artifacts/example.txt
evidencekit collect --config .evidencekit/config.yml
evidencekit validate evidence.json
evidencekit verify evidence.json
evidencekit report evidence.json --output evidence-report.md
```

Modify `artifacts/example.txt` after collection and run `verify` again to observe tamper detection.
