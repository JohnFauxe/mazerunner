"""Append-only JSON Lines result store; resumable by trial seed. Phase 1."""

import json
from pathlib import Path


def append(path: Path, row: dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(row, default=str) + "\n")


def load(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
