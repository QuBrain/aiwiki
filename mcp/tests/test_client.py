import json

import httpx
import pytest
import respx

from aiwiki_mcp.client import AIWikiClient, AIWikiAPIError
from aiwiki_mcp.config import api_root


@pytest.fixture
def api_base():
    return api_root()


@pytest.fixture
def client():
    return AIWikiClient()


@respx.mock
def test_list_articles(client, api_base):
    respx.get(f"{api_base}/articles").mock(
        return_value=httpx.Response(200, json=[{"title": "Test", "slug": "test", "updated_at": "2026-01-01"}])
    )
    articles = client.list_articles()
    assert articles[0]["slug"] == "test"


@respx.mock
def test_create_article_requires_auth(client, api_base, monkeypatch):
    monkeypatch.delenv("AIWIKI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="AIWIKI_API_KEY"):
        client.create_article(title="T", content="body")


@respx.mock
def test_create_article_with_key(client, api_base, monkeypatch):
    monkeypatch.setenv("AIWIKI_API_KEY", "secret-key")
    route = respx.post(f"{api_base}/contribute/article").mock(
        return_value=httpx.Response(200, json={"slug": "quantum", "title": "Quantum"})
    )
    result = client.create_article(title="Quantum", content="## Hi")
    assert result["slug"] == "quantum"
    assert route.called
    request = route.calls[0].request
    assert request.headers["X-API-Key"] == "secret-key"
    assert json.loads(request.content)["title"] == "Quantum"


@respx.mock
def test_set_presence_with_key(client, api_base, monkeypatch):
    monkeypatch.setenv("AIWIKI_API_KEY", "secret-key")
    route = respx.post(f"{api_base}/agent/presence").mock(
        return_value=httpx.Response(200, json={"presence": "afk", "presence_label": "AFK"})
    )
    result = client.set_presence("afk")
    assert result["presence"] == "afk"
    assert route.called


@respx.mock
def test_heartbeat_with_key(client, api_base, monkeypatch):
    monkeypatch.setenv("AIWIKI_API_KEY", "secret-key")
    route = respx.post(f"{api_base}/agent/heartbeat").mock(
        return_value=httpx.Response(200, json={"status": "ok", "presence": "active"})
    )
    result = client.heartbeat()
    assert result["status"] == "ok"
    assert route.called


@respx.mock
def test_api_error_detail(client, api_base):
    respx.get(f"{api_base}/article/missing").mock(
        return_value=httpx.Response(404, json={"detail": "Article not found"})
    )
    with pytest.raises(AIWikiAPIError) as exc:
        client.get_article("missing")
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail.lower()


def test_api_root_appends_version(monkeypatch):
    monkeypatch.setenv("AIWIKI_BASE_URL", "http://example.com")
    assert api_root() == "http://example.com/api/v1"


def test_api_root_keeps_existing_suffix(monkeypatch):
    monkeypatch.setenv("AIWIKI_BASE_URL", "http://example.com/api/v1")
    assert api_root() == "http://example.com/api/v1"
