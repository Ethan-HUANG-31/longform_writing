#!/usr/bin/env python3
"""Minimal DeepSeek API connectivity test.

Reads:
  DEEPSEEK_API_KEY   required
  DEEPSEEK_BASE_URL  optional, default https://api.deepseek.com
  DEEPSEEK_MODEL     optional, default deepseek-chat

This script intentionally uses only Python stdlib so it can run before the
longform writing skill has any dependency setup.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request


def endpoint_from_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY is not set.", file=sys.stderr)
        print(
            "Set it for one command, for example:\n"
            "  DEEPSEEK_API_KEY='sk-...' python3 scripts/test_deepseek_api.py",
            file=sys.stderr,
        )
        return 2

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    endpoint = endpoint_from_base_url(base_url)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise connectivity test assistant.",
            },
            {
                "role": "user",
                "content": "Reply with exactly: deepseek-ok",
            },
        ],
        "temperature": 0,
        "max_tokens": 16,
        "stream": False,
    }

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"ERROR: HTTP {exc.code} from {endpoint}", file=sys.stderr)
        print(body[:1000], file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"ERROR: request failed: {exc}", file=sys.stderr)
        return 1

    elapsed = time.monotonic() - started
    try:
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: unexpected response shape: {exc}", file=sys.stderr)
        print(raw[:1000], file=sys.stderr)
        return 1

    print("DeepSeek connectivity test passed.")
    print(f"status: {status}")
    print(f"endpoint: {endpoint}")
    print(f"model: {data.get('model', model)}")
    print(f"elapsed_sec: {elapsed:.2f}")
    print(f"content: {content.strip()[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
