#!/usr/bin/env python3
"""Start the Claude writer bridge with local settings from the ignored .env."""

import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"CLAUDE_BRIDGE_TOKEN", "CLAUDE_BRIDGE_HOST", "CLAUDE_BRIDGE_PORT", "CLAUDE_BIN"}
for line in (ROOT / ".env").read_text().splitlines():
    if "=" not in line or line.lstrip().startswith("#"):
        continue
    key, value = line.split("=", 1)
    if key in ALLOWED:
        os.environ[key] = value

if not os.environ.get("CLAUDE_BRIDGE_TOKEN"):
    raise SystemExit("CLAUDE_BRIDGE_TOKEN is missing from .env")

runpy.run_path(str(ROOT / "scripts" / "claude_writer_bridge.py"), run_name="__main__")
