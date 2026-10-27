#!/usr/bin/env python3
"""A small, authenticated HTTP bridge from Dockerized n8n to Claude Code.

Claude Code must be signed in to a Claude subscription on this Mac. The bridge
never accepts shell commands from a request and never uses an Anthropic API key.
"""

import json
import os
import subprocess
import shutil
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_FILE = ROOT / "prompts" / "article-writer-system.txt"
MAX_REQUEST_BYTES = 512_000
ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "meta_description": {"type": "string"},
        "article_markdown": {"type": "string"},
        "sources_used": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_url": {"type": "string"},
                    "used_for": {"type": "string"},
                },
                "required": ["source_url", "used_for"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "meta_description", "article_markdown", "sources_used"],
    "additionalProperties": False,
}


def validate_article(article):
    if not isinstance(article, dict):
        raise ValueError("Claude returned no article object")
    if not isinstance(article.get("title"), str) or not article["title"].strip():
        raise ValueError("Claude article is missing a title")
    if not isinstance(article.get("article_markdown"), str) or not article["article_markdown"].strip():
        raise ValueError("Claude article is missing article_markdown")
    if not isinstance(article.get("meta_description"), str):
        raise ValueError("Claude article is missing meta_description")
    if not isinstance(article.get("sources_used"), list):
        raise ValueError("Claude article is missing sources_used")
    for source in article["sources_used"]:
        if not isinstance(source, dict) or not all(
            isinstance(source.get(key), str) for key in ("source_url", "used_for")
        ):
            raise ValueError("Claude article has an invalid sources_used item")
    return {key: article[key] for key in ARTICLE_SCHEMA["required"]}


def parse_claude_result(payload):
    if not isinstance(payload, dict) or payload.get("is_error"):
        raise ValueError("Claude did not complete successfully")
    article = payload.get("structured_output")
    if article is None:
        result = payload.get("result")
        if not isinstance(result, str):
            raise ValueError("Claude returned no result")
        article = json.loads(result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
    article = validate_article(article)
    usage = payload.get("usage") or {}
    total_tokens = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
    return {
        "choices": [{"message": {"content": json.dumps(article, ensure_ascii=False)}}],
        "model": "claude-subscription/opus",
        "usage": {"total_tokens": total_tokens or None, "cost": None},
    }


def write_article(prepared):
    if not isinstance(prepared, dict) or not all(
        isinstance(prepared.get(key), dict)
        for key in ("article_strategy", "outline", "writer_guardrails")
    ):
        raise ValueError("Expected article_strategy, outline, and writer_guardrails objects")
    if not prepared["outline"].get("sections"):
        raise ValueError("Outline has no sections")

    prompt = (
        "Write the complete article using the following approved strategy, "
        "outline, evidence, and guardrails. Return only the requested JSON.\n\n"
        + json.dumps(prepared, ensure_ascii=False, indent=2)
    )
    env = os.environ.copy()
    for key in (
        "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
    ):
        env.pop(key, None)
    claude_bin = os.environ.get("CLAUDE_BIN") or shutil.which("claude")
    if not claude_bin:
        raise RuntimeError("Claude CLI not found; set CLAUDE_BIN to its absolute path")
    auth = subprocess.run(
        [claude_bin, "auth", "status"], text=True, capture_output=True,
        timeout=15, cwd=ROOT, env=env, check=False,
    )
    try:
        auth_state = json.loads(auth.stdout)
    except json.JSONDecodeError:
        auth_state = {}
    if auth.returncode or not auth_state.get("loggedIn"):
        raise RuntimeError("Claude CLI is not signed in to a subscription")
    if auth_state.get("authMethod") != "claude.ai" or not auth_state.get("subscriptionType"):
        raise RuntimeError("Claude CLI is not using a Claude subscription")
    args = [
        claude_bin,
        "--print", "--output-format", "json", "--json-schema", json.dumps(ARTICLE_SCHEMA),
        "--model", "opus", "--system-prompt", PROMPT_FILE.read_text(),
        "--tools", "", "--strict-mcp-config", "--disable-slash-commands",
        "--no-session-persistence", "--restricted",
    ]
    result = subprocess.run(
        args, input=prompt, text=True, capture_output=True, timeout=540,
        cwd=ROOT, env=env, check=False,
    )
    if result.returncode:
        # Do not put Claude's stderr into n8n execution logs: it can contain context.
        raise RuntimeError(f"Claude exited with status {result.returncode}; check bridge console")
    return parse_claude_result(json.loads(result.stdout))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        # Article bodies, authorization headers, and Claude output stay out of logs.
        sys.stderr.write("Claude writer bridge: request completed\n")

    def respond(self, status, body):
        encoded = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == "/health":
            self.respond(200, {"ok": True})
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        import hmac
        token = os.environ["CLAUDE_BRIDGE_TOKEN"]
        supplied = self.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied, "Bearer " + token):
            self.respond(401, {"error": "Unauthorized"})
            return
        if self.path != "/write-article":
            self.respond(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                self.respond(413, {"error": "Invalid request length"})
                return
            prepared = json.loads(self.rfile.read(length))
            response = write_article(prepared)
        except (ValueError, json.JSONDecodeError) as exc:
            self.respond(422, {"error": str(exc)})
            return
        except subprocess.TimeoutExpired:
            self.respond(504, {"error": "Claude writer timed out"})
            return
        except Exception as exc:
            sys.stderr.write(f"Claude writer bridge error: {type(exc).__name__}: {exc}\n")
            self.respond(502, {"error": "Claude writer failed; check bridge console"})
            return
        self.respond(200, response)


if __name__ == "__main__":
    if not os.environ.get("CLAUDE_BRIDGE_TOKEN"):
        raise SystemExit("CLAUDE_BRIDGE_TOKEN is required")
    host = os.environ.get("CLAUDE_BRIDGE_HOST", "127.0.0.1")
    port = int(os.environ.get("CLAUDE_BRIDGE_PORT", "8765"))
    print(f"Claude writer bridge listening on {host}:{port}", flush=True)
    HTTPServer((host, port), Handler).serve_forever()
