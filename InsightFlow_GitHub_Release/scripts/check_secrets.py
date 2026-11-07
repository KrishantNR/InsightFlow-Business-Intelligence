"""Lightweight pre-push scan for accidentally committed credentials.

This is a guardrail, not a replacement for GitHub secret scanning.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
MAX_BYTES = 2_000_000
PATTERNS = [
    re.compile(rb"sk-(?:proj-|live_)?[A-Za-z0-9_-]{24,}"),
    re.compile(rb"ghp_[A-Za-z0-9]{30,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
]


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in {"secrets.toml", ".env"}:
            findings.append(f"{path.relative_to(ROOT)}: local secret/config file must not be committed")
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            content = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in content[:4096]:
            continue
        for pattern in PATTERNS:
            if pattern.search(content):
                findings.append(f"{path.relative_to(ROOT)}: possible credential pattern detected")
                break
    if findings:
        print("Possible secrets were found. Remove them and rotate any exposed credentials:")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("Secret scan passed: no matching credential patterns or local secret files found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
