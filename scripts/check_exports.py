#!/usr/bin/env python3
"""Validate importable n8n exports and reject common private data patterns."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "seo-discovery.json",
    "content-strategy-v1.json",
    "content-production.json",
}
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
SECRET_PATTERNS = [
    re.compile(r"plur_pat_[A-Za-z0-9_-]+"),
    re.compile(r"sk-or-[A-Za-z0-9_-]+"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]+"),
    re.compile(r"eyJhbGci[A-Za-z0-9_-]+"),
    re.compile(r"/Users/[^/\s\"']+"),
    re.compile(r"docs\.google\.com/(?:spreadsheets|document)/d/[A-Za-z0-9_-]{20,}"),
]


def fail(message):
    raise SystemExit(message)


def check_strings(value, label, key=None):
    if isinstance(value, dict):
        for child_key, child in value.items():
            check_strings(child, f"{label}.{child_key}", child_key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            check_strings(child, f"{label}[{i}]", key)
    elif isinstance(value, str):
        if key not in {"id"} and UUID.search(value):
            fail(f"Account-like UUID in {label}; use a placeholder")
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                fail(f"Private-looking string in {label}: {pattern.pattern}")


def check_workflow(path):
    workflow = json.loads(path.read_text())
    if workflow.get("active") is not False:
        fail(f"{path}: export must be inactive")
    nodes = workflow.get("nodes", [])
    names = [node.get("name") for node in nodes]
    ids = [node.get("id") for node in nodes]
    if not nodes or len(names) != len(set(names)) or len(ids) != len(set(ids)):
        fail(f"{path}: missing or duplicate nodes")
    for node in nodes:
        if "credentials" in node:
            fail(f"{path}: credentials object on {node['name']}")
        params = node.get("parameters", {})
        if node.get("type") == "n8n-nodes-base.googleSheets":
            for field in ("documentId", "sheetName"):
                if field in params and params[field].get("value") not in ("", None):
                    fail(f"{path}: {node['name']} has an account-specific {field}")
        if node.get("type") == "n8n-nodes-base.googleDocs" and params.get("folderId"):
            fail(f"{path}: {node['name']} has an account-specific folderId")
        check_strings(params, f"{path.name}:{node['name']}")
    known = set(names)
    for source, outputs in workflow.get("connections", {}).items():
        if source not in known:
            fail(f"{path}: unknown connection source {source}")
        for group in outputs.get("main", []):
            for target in group:
                if target.get("node") not in known:
                    fail(f"{path}: unknown connection target {target.get('node')}")
    return len(nodes)


def main():
    paths = {path.name: path for path in (ROOT / "workflows").glob("*.json")}
    if set(paths) != FILES:
        fail(f"Expected {sorted(FILES)}, got {sorted(paths)}")
    for name in sorted(paths):
        print(f"{name}: {check_workflow(paths[name])} nodes OK")
    for directory in (ROOT / "scripts", ROOT / "prompts", ROOT / "assets", ROOT / "src"):
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix == ".pyc" or path.name == "check_exports.py":
                continue
            content = path.read_text(errors="ignore")
            for pattern in SECRET_PATTERNS:
                if pattern.search(content):
                    fail(f"Private-looking string in {path.relative_to(ROOT)}: {pattern.pattern}")
    print("No credentials or account-specific IDs found in the share package")


if __name__ == "__main__":
    main()
