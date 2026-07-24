"""Fetch and convert Wikipedia articles for AIWiki mirrors."""

from __future__ import annotations

import html
import re

import httpx

import core.database as db
import core.security as security

USER_AGENT = "AIWikiMirror/1.0 (https://github.com/aiwiki; educational mirror)"
DEFAULT_LANG = "en"

_LANG_NAMES = {
    "de": "deutschsprachigen",
    "en": "English",
}


def fetch_parsed_html(title: str, *, lang: str = DEFAULT_LANG) -> str:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(headers=headers, timeout=60.0, follow_redirects=True) as client:
        response = client.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "disabletoc": "1",
            },
        )
        response.raise_for_status()
        return response.json()["parse"]["text"]["*"]


def _fix_image_urls(text: str) -> str:
    text = re.sub(r'src="//upload\.wikimedia\.org', 'src="https://upload.wikimedia.org', text)
    text = re.sub(r'srcset="//upload\.wikimedia\.org', 'srcset="https://upload.wikimedia.org', text)
    return text


def _fix_wiki_links(text: str, *, lang: str = DEFAULT_LANG) -> str:
    def repl(match: re.Match[str]) -> str:
        href = match.group(1)
        label = match.group(2)
        if href.startswith("#"):
            return match.group(0)
        if href.startswith("http") or href.startswith("//"):
            return match.group(0)
        full = f"https://{lang}.wikipedia.org{href}"
        return f'<a href="{html.escape(full, quote=True)}" rel="nofollow">{label}</a>'

    return re.sub(
        r'<a\s+[^>]*href="(/wiki/[^"]+)"[^>]*>(.*?)</a>',
        repl,
        text,
        flags=re.DOTALL,
    )


def _strip_edit_sections(text: str) -> str:
    return re.sub(
        r'<span class="mw-editsection">.*?</span>',
        "",
        text,
        flags=re.DOTALL,
    )


def _normalize_headings(text: str) -> str:
    return re.sub(
        r'<div class="mw-heading mw-heading(\d)"><h(\d)\s+id="([^"]+)">(.*?)</h\d>.*?</div>',
        lambda m: f'<h{m.group(2)} id="{m.group(3)}"><span class="mw-headline">{m.group(4)}</span></h{m.group(2)}>',
        text,
        flags=re.DOTALL,
    )


def _simplify_infobox_image_cell(match: re.Match[str]) -> str:
    block = match.group(1)
    src_match = re.search(r'src="([^"]+)"', block)
    cap_match = re.search(r'<div class="infobox-caption">(.*?)</div>', block, flags=re.DOTALL)
    img = f'<img src="{src_match.group(1)}" alt="" />' if src_match else ""
    if cap_match:
        caption = cap_match.group(1).strip()
        return f'<td colspan="2">{img}<br />{caption}</td>'
    return f'<td colspan="2">{img}</td>'


def _convert_infobox(text: str) -> str:
    match = re.search(
        r'<table class="[^"]*\binfobox[^"]*"[^>]*>(.*?)</table>',
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return text

    table_inner = match.group(1)
    table_inner = re.sub(r"\sstyle=\"[^\"]*\"", "", table_inner)
    table_inner = re.sub(r"\ssummary=\"[^\"]*\"", "", table_inner)
    table_inner = re.sub(r"\scellpadding=\"[^\"]*\"", "", table_inner)
    table_inner = re.sub(r'\sscope="[^"]*"', "", table_inner)
    table_inner = re.sub(
        r'<th colspan="2" class="infobox-header"[^>]*>', '<th colspan="2" class="infobox-section">', table_inner
    )
    table_inner = re.sub(
        r'<th colspan="2">(Allgemeines|Konstruktion und Materialien|Tonabnehmer und Elektronik)</th>',
        r'<th colspan="2" class="infobox-section">\1</th>',
        table_inner,
    )
    table_inner = re.sub(
        r'(<tr>\s*)<th colspan="2" class="infobox-above"[^>]*>(.*?)</th>',
        r'\1<th colspan="2" class="infobox-title">\2</th>',
        table_inner,
        count=1,
        flags=re.DOTALL,
    )
    table_inner = re.sub(r'<span class="fn">(.*?)</span>', r"\1", table_inner, flags=re.DOTALL)
    table_inner = re.sub(
        r"<td[^>]*><b>(.*?)</b>\s*</td>",
        r"<th>\1</th>",
        table_inner,
        flags=re.DOTALL,
    )
    table_inner = re.sub(
        r'<td colspan="2" class="infobox-image"[^>]*>(.*?)</td>',
        _simplify_infobox_image_cell,
        table_inner,
        count=1,
        flags=re.DOTALL,
    )
    table_inner = re.sub(
        r"<span[^>]*>\s*<a[^>]*>\s*<img src=\"([^\"]+)\"[^>]*/>\s*</a>\s*</span>\s*<br\s*/?>\s*",
        r'<img src="\1" alt="" /><br />',
        table_inner,
        count=1,
        flags=re.DOTALL,
    )
    if 'class="infobox-title"' not in table_inner:
        table_inner = re.sub(
            r'(<tr>\s*)<th colspan="2">',
            r'\1<th colspan="2" class="infobox-title">',
            table_inner,
            count=1,
        )

    replacement = f'<div class="infobox"><table>{table_inner}</table></div>'
    return text[: match.start()] + replacement + text[match.end() :]


def _convert_figures(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        align = "left" if "mw-halign-left" in match.group(1) else "right"
        caption = match.group(2)
        src_match = re.search(r'src="([^"]+)"', block)
        if not src_match:
            return block
        src = src_match.group(1)
        if src.startswith("//"):
            src = "https:" + src
        width_match = re.search(r'width="(\d+)"', block)
        width_attr = f' width="{width_match.group(1)}"' if width_match else ""
        alt_match = re.search(r'alt="([^"]*)"', block)
        alt = html.escape(alt_match.group(1)) if alt_match else ""
        alt_attr = f' alt="{alt}"' if alt else ' alt=""'
        return (
            f'<div class="thumb thumb-{align}">'
            f'<div class="thumbinner">'
            f'<img src="{html.escape(src, quote=True)}"{width_attr}{alt_attr} />'
            f'<div class="thumbcaption">{caption}</div>'
            f"</div></div>"
        )

    return re.sub(
        r'<figure class="([^"]*)"[^>]*>.*?<img[^>]+/?>.*?<figcaption>(.*?)</figcaption></figure>',
        repl,
        text,
        flags=re.DOTALL,
    )


def _convert_see_also(text: str, *, lang: str = DEFAULT_LANG) -> str:
    if lang == "de":
        return re.sub(
            r'<div class="sieheauch"[^>]*>.*?<a href="(/wiki/[^"]+)"[^>]*>(.*?)</a></div>',
            lambda m: (
                f'<p class="mw-see-also"><em>Siehe auch:</em> '
                f'<a href="https://{lang}.wikipedia.org{m.group(1)}" rel="nofollow">{m.group(2)}</a></p>'
            ),
            text,
            flags=re.DOTALL,
        )
    return re.sub(
        r'<div role="note" class="hatnote[^"]*">See also:\s*<a href="(/wiki/[^"]+)"[^>]*>(.*?)</a></div>',
        lambda m: (
            f'<p class="mw-see-also"><em>See also:</em> '
            f'<a href="https://{lang}.wikipedia.org{m.group(1)}" rel="nofollow">{m.group(2)}</a></p>'
        ),
        text,
        flags=re.DOTALL,
    )


def _trim_tail(text: str) -> str:
    for marker in (
        '<div class="klappleiste',
        '<div class="hintergrundfarbe1 rahmenfarbe1 navigation-not-searchable noprint"',
        '<div role="navigation" aria-label="Categories"',
        '<div id="mw-normal-catlinks"',
        "<!-- \nNewPP limit report",
    ):
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
    return text.strip()


def _clean_misc(text: str) -> str:
    text = re.sub(r'<div class="shortdescription[^"]*"[^>]*>.*?</div>', "", text, flags=re.DOTALL)
    text = re.sub(r"<link rel=\"mw-deduplicated-inline-style\"[^>]*/>", "", text)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(
        r'\s(?:typeof|role|aria-[a-z-]+|data-mw-[a-z-]+|decoding|srcset|data-file-[^=]*)="[^"]*"',
        "",
        text,
    )
    text = re.sub(r'<span class="cite-bracket">\[</span>', "[", text)
    text = re.sub(r'<span class="cite-bracket">\]</span>', "]", text)
    text = re.sub(r'<span class="mw-cite-backlink">.*?</span>\s*', "", text, flags=re.DOTALL)
    text = re.sub(r'<span class="reference-text">', "", text)
    text = re.sub(r"</span>\s*(?=</li>)", "", text)
    return text.strip()


def _unwrap_parser_root(text: str) -> str:
    text = text.strip()
    match = re.match(
        r'<div class="mw-content-ltr mw-parser-output"[^>]*>(.*)</div>\s*$',
        text,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else text


def _mirror_notice(*, source_title: str, source_url: str, lang: str) -> str:
    if lang == "de":
        body = (
            f'Spiegel von <a href="{html.escape(source_url)}" rel="nofollow">'
            f"{html.escape(source_title)}</a> in der deutschsprachigen Wikipedia "
            f"(CC BY-SA 4.0, Wikimedia Foundation)."
        )
    else:
        lang_label = _LANG_NAMES.get(lang, lang)
        body = (
            f'Mirror of <a href="{html.escape(source_url)}" rel="nofollow">'
            f"{html.escape(source_title)}</a> on the {lang_label} Wikipedia "
            f"(CC BY-SA 4.0, Wikimedia Foundation)."
        )
    return f'<div class="ambox ambox-notice mirror-notice"><p>{body}</p></div>\n'


def convert_wikipedia_html(
    raw_html: str,
    *,
    source_title: str,
    source_url: str,
    lang: str = DEFAULT_LANG,
) -> str:
    text = _unwrap_parser_root(raw_html)
    text = _trim_tail(text)
    text = _strip_edit_sections(text)
    text = _normalize_headings(text)
    text = _convert_infobox(text)
    text = _convert_figures(text)
    text = _convert_see_also(text, lang=lang)
    text = _fix_image_urls(text)
    text = _fix_wiki_links(text, lang=lang)
    text = _clean_misc(text)

    notice = _mirror_notice(source_title=source_title, source_url=source_url, lang=lang)
    return text + "\n" + notice


def import_wikipedia_mirror(
    title: str,
    *,
    slug: str | None = None,
    lang: str = DEFAULT_LANG,
    agent_name: str = "Wikipedia Mirror",
) -> dict:
    source_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
    parsed = fetch_parsed_html(title, lang=lang)
    content = convert_wikipedia_html(
        parsed,
        source_title=title,
        source_url=source_url,
        lang=lang,
    )
    security.validate_content(content)

    article_slug = slug or db.slugify(title)
    existing = db.get_article(article_slug) or db.get_article(db.slugify(title))
    summary = f"Mirror of {source_url}"

    if existing:
        db.update_article(existing["id"], content, agent_name, summary)
        return {"slug": existing["slug"], "title": title, "updated": True}

    result = db.create_article(title, content, agent_name, summary)
    if result is None:
        existing = db.get_article(db.slugify(title))
        if not existing:
            raise RuntimeError(f"Failed to import mirror article {title!r}")
        db.update_article(existing["id"], content, agent_name, summary)
        return {"slug": existing["slug"], "title": title, "updated": True}
    return {"slug": result["slug"], "title": title, "updated": False}


if __name__ == "__main__":
    info = import_wikipedia_mirror("Gibson ES-335", slug="gibson_es_335", lang="en")
    print(info)
