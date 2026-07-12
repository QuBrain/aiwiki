"""Run live MCP smoke tests using local .cursor/mcp.json env (no secrets printed)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def load_cursor_env() -> dict[str, str]:
    config_path = Path(__file__).resolve().parents[2] / ".cursor" / "mcp.json"
    if not config_path.exists():
        return {}
    data = json.loads(config_path.read_text(encoding="utf-8"))
    server = data.get("mcpServers", {}).get("aiwiki", {})
    return dict(server.get("env") or {})


def main() -> int:
    env = {**os.environ, **load_cursor_env()}
    for key in ("AIWIKI_BASE_URL", "AIWIKI_API_KEY"):
        if key in env:
            os.environ[key] = env[key]

    from aiwiki_mcp.server import (
        aiwiki_get_agent_overview,
        aiwiki_get_article_blueprint,
        aiwiki_list_articles,
        aiwiki_search_articles,
        aiwiki_server_info,
    )

    checks: list[tuple[str, callable]] = [
        ("server_info", aiwiki_server_info),
        ("list_articles", aiwiki_list_articles),
        ("search", lambda: aiwiki_search_articles("gibson", 3)),
        ("blueprint", aiwiki_get_article_blueprint),
    ]
    if env.get("AIWIKI_API_KEY"):
        checks.append(("agent_overview", aiwiki_get_agent_overview))

    failed = 0
    for name, fn in checks:
        try:
            raw = fn()
            payload = json.loads(raw)
            if isinstance(payload, dict) and payload.get("error"):
                raise RuntimeError(payload["error"])
            print(f"OK  {name}")
        except Exception as exc:
            print(f"FAIL {name}: {exc}", file=sys.stderr)
            failed += 1

    # stdio subprocess starts cleanly (initialize + list_tools via MCP SDK)
    mcp_dir = Path(__file__).resolve().parent
    probe = """
import asyncio, os, json
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

async def main():
    params = StdioServerParameters(
        command="uv",
        args=["run", "aiwiki-mcp"],
        env={k: v for k, v in os.environ.items() if k.startswith("AIWIKI_")},
        cwd=r"%s",
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            print(json.dumps({"tool_count": len(names), "sample": names[:5]}))

asyncio.run(main())
""" % str(mcp_dir).replace("\\", "\\\\")

    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=mcp_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode == 0:
        info = json.loads(result.stdout.strip().splitlines()[-1])
        print(f"OK  stdio_mcp ({info['tool_count']} tools)")
    else:
        print(f"FAIL stdio_mcp: {result.stderr.strip() or result.stdout.strip()}", file=sys.stderr)
        failed += 1

    from aiwiki_mcp.branding import server_icons

    icons = server_icons()
    if icons and icons[0].src.startswith("data:image/png;base64,"):
        print("OK  server_icon")
    else:
        print("FAIL server_icon: logo not loaded", file=sys.stderr)
        failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
