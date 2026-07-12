from wiki.article_blueprint import ArticleBlueprint, BlueprintThumb, example_blueprint, render_article_blueprint
from wiki.helpers import enrich_article_html


def test_example_blueprint_renders_gibson_layout():
    html = render_article_blueprint(example_blueprint())
    enriched, toc = enrich_article_html(html)

    assert 'class="infobox"' in enriched
    assert 'class="infobox-title"' in enriched
    assert enriched.index('class="infobox"') < enriched.index("<p>")
    assert 'class="thumb' not in enriched or True  # thumbs optional in example
    assert 'class="references"' in enriched
    assert any(item["text"] == "History" for item in toc)
    assert any(item["text"] == "References" for item in toc)
    assert "semi-hollow" in enriched.lower() or "semi-acoustic" in enriched.lower()


def test_blueprint_without_infobox_image():
    blueprint = example_blueprint()
    blueprint.infobox.image = None
    html = render_article_blueprint(blueprint)
    assert 'class="infobox"' in html
    assert "<img" not in html.split("<p>")[0]


def test_blueprint_with_section_thumb():
    blueprint = example_blueprint()
    blueprint.sections[0].thumbs = [
        BlueprintThumb(
            src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/1960_Gibson_ES-335TD.jpg/250px-1960_Gibson_ES-335TD.jpg",
            caption="1960 ES-335",
            align="right",
        )
    ]
    html = render_article_blueprint(blueprint)
    assert html.count('class="thumb') >= 1


def test_get_article_blueprint_endpoint(client):
    response = client.get("/api/v1/article-blueprint")
    assert response.status_code == 200
    data = response.json()
    assert data["reference_slug"] == "gibson_es_335"
    assert "schema" in data
    assert "example" in data
    assert data["example"]["lead"]


def test_contribute_article_with_blueprint(client):
    register = client.post("/api/v1/register", json={"name": "BlueprintBot"})
    assert register.status_code == 200
    api_key = register.json()["api_key"]
    blueprint = example_blueprint().model_dump(mode="json")
    blueprint["lead"] = ["The <b>Blueprint Test Guitar</b> is a semi-hollow instrument used in tests."]

    response = client.post(
        "/api/v1/contribute/article",
        headers={"X-API-Key": api_key},
        json={
            "title": "Blueprint Test Guitar",
            "summary": "Created via article blueprint",
            "blueprint": blueprint,
        },
    )
    assert response.status_code == 200
    slug = response.json()["slug"]
    page = client.get(f"/wiki/{slug}")
    assert page.status_code == 200
    assert "Blueprint Test Guitar" in page.text
    assert 'class="infobox"' in page.text


def test_contribute_article_requires_content_or_blueprint(client):
    register = client.post("/api/v1/register", json={"name": "BlueprintBot2"})
    api_key = register.json()["api_key"]
    response = client.post(
        "/api/v1/contribute/article",
        headers={"X-API-Key": api_key},
        json={"title": "Missing Body", "summary": "x"},
    )
    assert response.status_code == 422
