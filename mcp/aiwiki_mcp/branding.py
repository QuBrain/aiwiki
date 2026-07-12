"""Server branding assets for MCP clients."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from mcp.types import Icon

_LOGO_PATH = Path(__file__).resolve().parents[1] / "MCP_Logo.png"


@lru_cache(maxsize=1)
def server_icons() -> list[Icon]:
    if not _LOGO_PATH.is_file():
        return []
    encoded = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
    return [
        Icon(
            src=f"data:image/png;base64,{encoded}",
            mimeType="image/png",
            sizes=["512x512"],
        )
    ]
