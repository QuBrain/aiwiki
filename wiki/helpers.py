"""Small helpers for wiki page rendering."""

from __future__ import annotations

import html
import re
from typing import TypedDict

import core.database as db


class TocEntry(TypedDict):
    level: int
    id: str
    text: str


_HEADING_RE = re.compile(r"<h([23])(\s[^>]*)?>(.*?)</h\1>", re.DOTALL | re.IGNORECASE)


def article_excerpt(content: str, max_len: int = 320) -> str:
    text = (content or "").strip()
    text = re.sub(
        r'<div class="infobox">.*?</div>',
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r'<div class="ambox[^"]*".*?</div>',
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"^#+\s*.+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rsplit(" ", 1)[0]
    return cut + "…"


def slugify_heading(text: str, used: dict[str, int] | None = None) -> str:
    bucket: dict[str, int] = used if used is not None else {}
    return _slugify_heading(text, bucket)


def _slugify_heading(text: str, used: dict[str, int]) -> str:
    plain = re.sub(r"<[^>]+>", "", text)
    plain = html.unescape(plain).strip()
    slug = re.sub(r"[^\w\s-]", "", plain, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug.strip().lower())
    slug = slug or "section"
    if slug in used:
        used[slug] += 1
        slug = f"{slug}-{used[slug]}"
    else:
        used[slug] = 0
    return slug


def enrich_article_html(content_html: str) -> tuple[str, list[TocEntry]]:
    if not content_html:
        return "", []

    toc: list[TocEntry] = []
    used: dict[str, int] = {}

    def repl(match: re.Match[str]) -> str:
        level = int(match.group(1))
        attrs = match.group(2) or ""
        inner = match.group(3)
        plain = re.sub(r"<[^>]+>", "", inner)
        text = html.unescape(plain).strip()
        id_match = re.search(r'\bid="([^"]+)"', attrs)
        if id_match:
            hid = id_match.group(1)
            toc.append({"level": level, "id": hid, "text": text})
            if 'class="mw-headline"' in inner:
                return match.group(0)
            return f'<h{level}{attrs}><span class="mw-headline">{inner}</span></h{level}>'
        hid = _slugify_heading(inner, used)
        toc.append({"level": level, "id": hid, "text": text})
        return f'<h{level} id="{hid}"><span class="mw-headline">{inner}</span></h{level}>'

    enriched = _HEADING_RE.sub(repl, content_html)
    return enriched, toc


def build_article_of_day(articles: list[dict]) -> dict | None:
    if not articles:
        return None
    full = db.get_article(articles[0]["slug"])
    if not full:
        return None
    return {
        "title": full["title"],
        "slug": full["slug"],
        "excerpt": article_excerpt(full.get("content") or ""),
    }
