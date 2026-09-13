#!/usr/bin/env python3
"""Fail-closed RAPP/1 conformance checks for this static API."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    failures = []
    registry = load("registry.json")
    status = load("api/v1/status.json")
    if registry.get("schema") != "rapp-static-api/1.0":
        failures.append("registry schema")
    if not registry.get("raw_base", "").startswith("https://raw.githubusercontent.com/"):
        failures.append("raw base")
    if not ISO_Z.match(registry.get("generated", "")):
        failures.append("registry timestamp")
    if status.get("schema") != "rapp-d365-business-processes-status/1.0":
        failures.append("status schema")
    if not (ROOT / ".nojekyll").exists():
        failures.append(".nojekyll")
    for entry in registry.get("entries", []):
        endpoint = ROOT / "api" / "v1" / f"{entry['name']}.json"
        version = ROOT / "versions" / entry["name"] / f"{entry['sha8']}.json"
        digest = hashlib.sha256(endpoint.read_bytes()).hexdigest()
        if digest != entry["sha256"] or entry["sha8"] != digest[:12]:
            failures.append(f"hash {entry['name']}")
        if not version.exists() or version.read_bytes() != endpoint.read_bytes():
            failures.append(f"version {entry['name']}")
    tracked = [
        "registry.json",
        "api/v1/status.json",
        "api/v1/badge.json",
        ".well-known/mcp.json",
        ".well-known/agent-protocol.json",
        "llms.txt",
    ]
    before = {name: (ROOT / name).read_bytes() for name in tracked}
    subprocess.run(
        [sys.executable, "build.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=120,
    )
    if any((ROOT / name).read_bytes() != value for name, value in before.items()):
        failures.append("idempotent build")
    for failure in failures:
        print(f"FAIL {failure}")
    if not failures:
        print("PASS rapp-static-api/1.0")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
