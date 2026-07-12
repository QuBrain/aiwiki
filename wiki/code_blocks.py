"""Syntax-highlighted code blocks for wiki articles."""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer

_LANG_ALIASES = {
    "env": "properties",
    "shell": "bash",
    "sh": "bash",
    "yml": "yaml",
}

_pygments_cache_lock = threading.Lock()
_pygments_cache: dict[str, object] = {"mtime": 0.0, "version": "1", "css": ""}


def normalize_language(language: str) -> str:
    lang = (language or "").strip().lower()
    return _LANG_ALIASES.get(lang, lang)


def render_code_block(code: str, language: str = "") -> str:
    text = code.rstrip("\n") + "\n"
    lexer = _pick_lexer(text, language)
    formatter = HtmlFormatter(cssclass="codehilite")
    return highlight(text, lexer, formatter)


def render_pygments_css() -> str:
    light = HtmlFormatter(style="default").get_style_defs(".codehilite")
    dark = HtmlFormatter(style="monokai").get_style_defs('[data-theme="dark"] .codehilite')
    overrides = """
.codehilite { background: var(--bg-code) !important; }
[data-theme="dark"] .codehilite { background: var(--bg-code) !important; }
.codehilite pre { background: transparent !important; }
"""
    return f"{light}\n{dark}\n{overrides.strip()}\n"


def pygments_css_version() -> str:
    path = Path(__file__)
    mtime = path.stat().st_mtime
    with _pygments_cache_lock:
        if mtime != _pygments_cache["mtime"]:
            css = render_pygments_css()
            _pygments_cache["css"] = css
            _pygments_cache["version"] = hashlib.sha256(css.encode()).hexdigest()[:12]
            _pygments_cache["mtime"] = mtime
        return str(_pygments_cache["version"])


def get_pygments_css() -> str:
    pygments_css_version()
    return str(_pygments_cache["css"])


def pygments_css_url() -> str:
    return f"/codehilite.css?v={pygments_css_version()}"


def _pick_lexer(code: str, language: str):
    language = normalize_language(language)
    if language:
        try:
            return get_lexer_by_name(language, stripall=True)
        except Exception:
            pass
    try:
        return guess_lexer(code)
    except Exception:
        return TextLexer()
