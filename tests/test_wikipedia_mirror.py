from mirrors.wikipedia_mirror import convert_wikipedia_html, fetch_parsed_html
import core.security as security
from wiki.helpers import article_excerpt, enrich_article_html


def test_gibson_mirror_has_infobox_headings_and_thumbs():
    raw = fetch_parsed_html("Gibson ES-335", lang="en")
    content = convert_wikipedia_html(
        raw,
        source_title="Gibson ES-335",
        source_url="https://en.wikipedia.org/wiki/Gibson_ES-335",
        lang="en",
    )
    html = security.render_markdown(content)
    html, toc = enrich_article_html(html)
    assert 'class="infobox"' in html
    infobox_at = html.index('class="infobox"')
    first_para_at = html.index("<p>")
    notice_at = html.index("mirror-notice")
    assert infobox_at < first_para_at < notice_at
    assert '<img src="https://upload.wikimedia.org' in html
    assert html.count('class="thumb') >= 4
    assert html.count('<img src="https://upload.wikimedia.org') >= 5
    assert len(toc) >= 5
    assert any(item["text"] == "History" for item in toc)
    assert "semi-hollow" in html.lower() or "semi-acoustic" in html.lower()
    assert "english wikipedia" in html.lower()


def test_mirror_excerpt_skips_infobox_html():
    raw = fetch_parsed_html("Gibson ES-335", lang="en")
    content = convert_wikipedia_html(
        raw,
        source_title="Gibson ES-335",
        source_url="https://en.wikipedia.org/wiki/Gibson_ES-335",
        lang="en",
    )
    excerpt = article_excerpt(content)
    assert "<div" not in excerpt
    assert "Gibson ES-335" in excerpt
    assert "semi-hollow" in excerpt.lower() or "semi-acoustic" in excerpt.lower()
