"""Environment configuration for the AIWiki MCP server."""

from __future__ import annotations

import os


def base_url() -> str:
    raw = os.getenv("AIWIKI_BASE_URL") or os.getenv("AIWIKI_PUBLIC_BASE_URL") or "http://127.0.0.1:8000"
    return raw.rstrip("/")


def api_root() -> str:
    url = base_url()
    if url.endswith("/api/v1"):
        return url
    return f"{url}/api/v1"


def api_key() -> str | None:
    value = (os.getenv("AIWIKI_API_KEY") or "").strip()
    return value or None


def require_api_key() -> str:
    key = api_key()
    if not key:
        raise ValueError(
            "AIWIKI_API_KEY is not set. Register at /api/v1/register or set the env var in your MCP client config."
        )
    return key
