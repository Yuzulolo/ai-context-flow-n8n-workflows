#!/usr/bin/env python3
"""Start the Claude writer bridge with its local token from the ignored .env."""

import os
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text().splitlines():
    if line.startswith("CLAUDE_BRIDGE_TOKEN="):
        os.environ["CLAUDE_BRIDGE_TOKEN"] = line.split("=", 1)[1]
        break
else:
    raise SystemExit("CLAUDE_BRIDGE_TOKEN is missing from .env")

runpy.run_path(str(ROOT / "scripts" / "claude_writer_bridge.py"), run_name="__main__")
