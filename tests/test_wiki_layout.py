from wiki.helpers import enrich_article_html


def test_enrich_article_html_adds_ids_and_toc():
    html = "<p>Intro</p><h2>First Section</h2><p>Text</p><h3>Sub</h3>"
    enriched, toc = enrich_article_html(html)
    assert 'id="first-section"' in enriched
    assert 'class="mw-headline"' in enriched
    assert len(toc) == 2
    assert toc[0]["text"] == "First Section"
    assert toc[0]["level"] == 2
    assert toc[1]["text"] == "Sub"
    assert toc[1]["level"] == 3


def test_enrich_article_html_uses_existing_heading_ids():
    html = '<h2 id="konstruktionsweise">Konstruktionsweise</h2>'
    enriched, toc = enrich_article_html(html)
    assert toc == [{"level": 2, "id": "konstruktionsweise", "text": "Konstruktionsweise"}]
    assert 'class="mw-headline"' in enriched


def test_wiki_article_page_has_toc_and_toolbar(client):
    create = client.post(
        "/api/v1/contribute/article",
        json={
            "title": "Wiki Layout Test",
            "content": "## First Section\n\nBody text.\n\n### Subsection\n\nMore text.",
            "summary": "Layout test article",
        },
        headers={"X-API-Key": client.post("/api/v1/register", json={"name": "LayoutBot"}).json()["api_key"]},
    )
    assert create.status_code == 200
    slug = create.json()["slug"]
    response = client.get(f"/wiki/{slug}")
    assert response.status_code == 200
    assert 'class="page-wiki"' in response.text
    assert 'class="mw-page-toolbar"' in response.text
    assert 'class="mw-namespace-tabs"' in response.text
    assert 'class="mw-views-tabs"' in response.text
    assert 'id="mw-toc"' in response.text
    assert "Contents" in response.text
    assert 'id="first-section"' in response.text
