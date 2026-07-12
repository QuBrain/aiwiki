"""Central theme and layout tokens for AIWiki."""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

STORAGE_KEY = "aiwiki_theme"
LAYOUT_STORAGE_KEY = "aiwiki_layout"
THEMES = ("light", "dark")
LAYOUT_WIDTHS = ("normal", "wide")
DEFAULT_THEME = "light"
DEFAULT_LAYOUT_WIDTH = "normal"

LAYOUT = {
    "max_width": "1480px",
    "gutter": "28px",
    "gutter_mobile": "16px",
    "sidebar_width": "220px",
    "content_padding_x": "24px",
    "wiki_content_padding_x": "20px",
    "wiki_toc_width": "13.5em",
    "header_search_max_width": "420px",
    "wide_header_search_max_width": "720px",
    "wide_search_form_max_width": "960px",
    "infobox_width": "22em",
}

TRANSITION = {
    "duration": "0.25s",
    "duration_ms": 250,
    "easing": "ease",
}

LIGHT_TOKENS: dict[str, str] = {
    "bg-body": "#f6f6f6",
    "bg-surface": "#fff",
    "bg-header": "#fff",
    "bg-sidebar": "#f8f9fa",
    "bg-muted": "#f8f9fa",
    "bg-table-head": "#eaecf0",
    "bg-hover": "#f8f9fa",
    "bg-input": "#fff",
    "bg-btn": "#f8f9fa",
    "bg-btn-hover": "#fff",
    "bg-code": "#f8f9fa",
    "bg-overlay": "rgba(0, 0, 0, 0.35)",
    "text-primary": "#202122",
    "text-secondary": "#54595d",
    "text-link": "#0645ad",
    "border": "#a2a9b1",
    "border-light": "#c8ccd1",
    "border-accent": "#a7d7f9",
    "border-subtle": "#eaecf0",
    "shadow": "rgba(0, 0, 0, 0.1)",
    "shadow-dialog": "rgba(0, 0, 0, 0.15)",
    "success-bg": "#eaf3e6",
    "success-border": "#14866d",
    "warning-bg": "#fef6e7",
    "warning-border": "#fc3",
    "error-bg": "#fcebeb",
    "error-border": "#cc3333",
    "notice-border": "#3366cc",
    "ambox-bg": "#fbfbfb",
    "diff-added-bg": "#eaf3e6",
    "diff-added-text": "#14866d",
    "diff-removed-bg": "#fcebeb",
    "diff-removed-text": "#cc3333",
    "dialog-primary-bg": "#eaf3ff",
    "dialog-warning-primary-bg": "#fef6e7",
    "online": "#00af89",
    "offline": "#a2a9b1",
    "afk": "#dbab09",
}

DARK_TOKENS: dict[str, str] = {
    "bg-body": "#0d1117",
    "bg-surface": "#161b22",
    "bg-header": "#000",
    "bg-sidebar": "#0d1117",
    "bg-muted": "#21262d",
    "bg-table-head": "#21262d",
    "bg-hover": "#21262d",
    "bg-input": "#0d1117",
    "bg-btn": "#21262d",
    "bg-btn-hover": "#30363d",
    "bg-code": "#21262d",
    "bg-overlay": "rgba(0, 0, 0, 0.6)",
    "text-primary": "#e6edf3",
    "text-secondary": "#8b949e",
    "text-link": "#58a6ff",
    "border": "#30363d",
    "border-light": "#30363d",
    "border-accent": "#388bfd",
    "border-subtle": "#30363d",
    "shadow": "rgba(0, 0, 0, 0.4)",
    "shadow-dialog": "rgba(0, 0, 0, 0.5)",
    "success-bg": "#12261e",
    "success-border": "#3fb950",
    "warning-bg": "#2a2008",
    "warning-border": "#d29922",
    "error-bg": "#2d1214",
    "error-border": "#f85149",
    "notice-border": "#388bfd",
    "ambox-bg": "#161b22",
    "diff-added-bg": "#12261e",
    "diff-added-text": "#3fb950",
    "diff-removed-bg": "#2d1214",
    "diff-removed-text": "#f85149",
    "dialog-primary-bg": "#132d52",
    "dialog-warning-primary-bg": "#2a2008",
    "online": "#3fb950",
    "offline": "#6e7681",
    "afk": "#d29922",
}

_cache_lock = threading.Lock()
_cache: dict[str, object] = {"mtime": 0.0, "version": "1", "css": ""}


def _layout_tokens() -> dict[str, str]:
    return {
        "layout-max-width": LAYOUT["max_width"],
        "layout-gutter": LAYOUT["gutter"],
        "sidebar-width": LAYOUT["sidebar_width"],
        "layout-column-left": "calc((100vw - min(var(--layout-max-width), 100vw)) / 2)",
        "content-padding-x": LAYOUT["content_padding_x"],
        "wiki-content-padding-x": LAYOUT["wiki_content_padding_x"],
        "wiki-toc-width": LAYOUT["wiki_toc_width"],
        "infobox-width": LAYOUT["infobox_width"],
        "header-search-max-width": LAYOUT["header_search_max_width"],
        "theme-transition-duration": TRANSITION["duration"],
        "theme-transition-easing": TRANSITION["easing"],
    }


def _transition_css() -> str:
    duration = TRANSITION["duration"]
    easing = TRANSITION["easing"]
    return f"""
::view-transition-old(root),
::view-transition-new(root) {{
  animation-duration: {duration};
  animation-timing-function: {easing};
}}

@media (prefers-reduced-motion: no-preference) {{
  html.theme-switching,
  html.theme-switching *,
  html.theme-switching *::before,
  html.theme-switching *::after {{
    transition-property: background-color, color, border-color, box-shadow, outline-color, text-decoration-color, fill, stroke !important;
    transition-duration: {duration} !important;
    transition-timing-function: {easing} !important;
  }}

  html.theme-switching .theme-toggle-icons,
  html.theme-switching .theme-icon,
  html.theme-switching .theme-icon * {{
    transition-property: transform, opacity !important;
  }}
}}
"""


def _wide_layout_css() -> str:
    wide_search = LAYOUT["wide_header_search_max_width"]
    wide_form = LAYOUT["wide_search_form_max_width"]
    return f"""
html[data-layout="wide"] {{
  --layout-max-width: none;
  --layout-column-left: var(--layout-gutter);
  --header-search-max-width: min({wide_search}, 42vw);
}}

html[data-layout="wide"] .search-form {{
  max-width: min({wide_form}, 100%);
}}
"""


def _css_block(selector: str, tokens: dict[str, str], *, color_scheme: str | None = None) -> list[str]:
    lines = [f"{selector} {{"]
    if color_scheme:
        lines.append(f"  color-scheme: {color_scheme};")
    for key, value in tokens.items():
        lines.append(f"  --{key}: {value};")
    lines.append("}")
    return lines


def render_css() -> str:
    root_tokens = {**LIGHT_TOKENS, **_layout_tokens()}
    lines = _css_block(":root", root_tokens, color_scheme="light")
    lines.extend(_css_block('[data-theme="dark"]', DARK_TOKENS, color_scheme="dark"))
    lines.append(_wide_layout_css().strip())
    lines.append(_transition_css().strip())
    return "\n".join(lines) + "\n"


def theme_version() -> str:
    path = Path(__file__)
    mtime = path.stat().st_mtime
    with _cache_lock:
        if mtime != _cache["mtime"]:
            css = render_css()
            _cache["css"] = css
            _cache["version"] = hashlib.sha256(css.encode()).hexdigest()[:12]
            _cache["mtime"] = mtime
        return str(_cache["version"])


def get_theme_css() -> str:
    theme_version()
    return str(_cache["css"])


def client_config() -> dict[str, object]:
    return {
        "storageKey": STORAGE_KEY,
        "themes": list(THEMES),
        "defaultTheme": DEFAULT_THEME,
        "layoutStorageKey": LAYOUT_STORAGE_KEY,
        "layoutWidths": list(LAYOUT_WIDTHS),
        "defaultLayoutWidth": DEFAULT_LAYOUT_WIDTH,
        "layout": LAYOUT,
        "transition": TRANSITION,
    }


def client_config_json() -> str:
    return json.dumps(client_config(), separators=(",", ":"))


def theme_css_url() -> str:
    return f"/theme.css?v={theme_version()}"
