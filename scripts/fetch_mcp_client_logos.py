"""Refresh MCP client logos (Lobe Icons PNG + VS Code Icons8 + Zed wordmark)."""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "mcp-clients"

LOBE_LIGHT = (
    "https://raw.githubusercontent.com/lobehub/lobe-icons/refs/heads/master/packages/static-png/light"
)
LOBE_DARK = (
    "https://raw.githubusercontent.com/lobehub/lobe-icons/refs/heads/master/packages/static-png/dark"
)

DOWNLOADS: dict[str, str] = {
    # Fixed (same in light and dark UI)
    "claude-code.png": f"{LOBE_DARK}/claudecode-color.png",
    "claude-desktop.png": f"{LOBE_LIGHT}/claude-color.png",
    "openclaw.png": f"{LOBE_LIGHT}/openclaw-color.png",
    "antigravity.png": f"{LOBE_LIGHT}/antigravity-color.png",
    "vscode.png": "https://img.icons8.com/?size=100&id=9OGIyU8hrxW5&format=png&color=000000",
    "continue.png": "https://continue.dev/favicon.png",
    # Theme-aware pairs
    "codex-light.png": f"{LOBE_LIGHT}/codex.png",
    "codex-dark.png": f"{LOBE_DARK}/codex.png",
    "cursor-light.png": f"{LOBE_LIGHT}/cursor.png",
    "cursor-dark.png": f"{LOBE_DARK}/cursor.png",
    "ollama-light.png": f"{LOBE_LIGHT}/ollama.png",
    "ollama-dark.png": f"{LOBE_DARK}/ollama.png",
    "windsurf-light.png": f"{LOBE_LIGHT}/windsurf.png",
    "windsurf-dark.png": f"{LOBE_DARK}/windsurf.png",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, url in DOWNLOADS.items():
        data = urllib.request.urlopen(url, timeout=30).read()
        if len(data) < 200:
            raise RuntimeError(f"{filename}: download too small ({len(data)} bytes) from {url}")
        (OUT / filename).write_bytes(data)
        print(f"OK  {filename} ({len(data)} bytes)")
    for name in ("zed-light.svg", "zed-dark.svg"):
        path = OUT / name
        if not path.is_file():
            raise RuntimeError(f"Missing {name} — commit the Zed wordmark SVGs in static/mcp-clients/")
        print(f"OK  {name} (local, {path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
