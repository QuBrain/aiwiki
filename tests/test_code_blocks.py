import core.security as security
from wiki.article_blueprint import ArticleBlueprint, BlueprintCodeBlock, BlueprintSection, render_article_blueprint
from wiki.code_blocks import get_pygments_css, render_code_block


def test_render_code_block_python_tokens():
    html = render_code_block('print("hello")', "python")
    assert 'class="codehilite"' in html
    assert 'class="nb"' in html or 'class="k"' in html
    assert "print" in html


def test_render_markdown_fenced_code():
    md = """## Demo

```python
def greet(name):
    return name
```
"""
    html = security.render_markdown(md)
    assert 'class="codehilite"' in html
    assert 'class="nf"' in html or 'class="k"' in html
    assert "greet" in html
    assert "<script>" not in html


def test_blueprint_section_code_blocks():
    blueprint = ArticleBlueprint(
        lead=["Lead paragraph."],
        sections=[
            BlueprintSection(
                title="Examples",
                paragraphs=["Sample code:"],
                code_blocks=[
                    BlueprintCodeBlock(language="python", code='print("wiki")'),
                ],
            )
        ],
    )
    html = render_article_blueprint(blueprint)
    assert 'class="codehilite"' in html
    assert 'class="nb"' in html or 'class="k"' in html
    assert "print" in html


def test_stored_html_article_keeps_code_tokens():
    blueprint = ArticleBlueprint(
        lead=["Lead."],
        sections=[
            BlueprintSection(
                title="Code",
                paragraphs=["Example:"],
                code_blocks=[BlueprintCodeBlock(language="python", code="x = 1")],
            )
        ],
    )
    stored = render_article_blueprint(blueprint)
    rendered = security.render_markdown(stored)
    assert 'class="codehilite"' in rendered
    assert 'class="mi"' in rendered or 'class="n"' in rendered


def test_pygments_css_includes_token_rules():
    css = get_pygments_css()
    assert ".codehilite .k" in css
    assert '[data-theme="dark"] .codehilite' in css


def test_codehilite_stylesheet_route(client):
    response = client.get("/codehilite.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert ".codehilite .k" in response.text


def test_api_docs_page(client):
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    text = response.text
    assert "page-api-docs" in text
    assert "Article blueprint" in text
    assert "code-panel-highlight" in text
    assert 'class="codehilite"' in text
    assert "/api/v1/contribute/article" in text
    assert "pygments_css_url" not in text
    assert "codehilite.css" in text
    assert "api_docs.js" in text
    assert "MCP server" in text
    assert 'id="mcp"' in text
    assert "aiwiki_create_article" in text
    assert "${workspaceFolder}/mcp" in text


def test_wiki_article_renders_markdown_code(client):
    register = client.post("/api/v1/register", json={"name": "SyntaxBot"})
    api_key = register.json()["api_key"]
    response = client.post(
        "/api/v1/contribute/article",
        headers={"X-API-Key": api_key},
        json={
            "title": "Syntax Highlight Demo",
            "summary": "Code sample",
            "content": "## Example\n\n```python\nprint('syntax')\n```",
        },
    )
    assert response.status_code == 200
    slug = response.json()["slug"]
    page = client.get(f"/wiki/{slug}")
    assert page.status_code == 200
    assert 'class="codehilite"' in page.text
    assert "codehilite.css" in page.text
