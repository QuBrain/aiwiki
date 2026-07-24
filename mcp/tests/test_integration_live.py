"""Live integration tests against a running AIWiki instance (127.0.0.1:8001)."""

from __future__ import annotations

import json
import os

import httpx
import pytest
from aiwiki_mcp.client import AIWikiClient
from aiwiki_mcp.server import (
    aiwiki_get_article_blueprint,
    aiwiki_list_articles,
    aiwiki_search_articles,
    aiwiki_server_info,
)


def _wiki_up() -> bool:
    try:
        response = httpx.get("http://127.0.0.1:8001/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _wiki_up(), reason="AIWiki not running on 127.0.0.1:8001")


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("AIWIKI_BASE_URL", "http://127.0.0.1:8001")
    key = os.getenv("AIWIKI_API_KEY", "").strip()
    if key:
        monkeypatch.setenv("AIWIKI_API_KEY", key)


def test_server_info_live():
    payload = json.loads(aiwiki_server_info())
    assert payload["api_root"] == "http://127.0.0.1:8001/api/v1"
    assert payload["api_key_configured"] is bool(os.getenv("AIWIKI_API_KEY"))


def test_list_articles_live():
    payload = json.loads(aiwiki_list_articles())
    assert isinstance(payload, list)
    assert len(payload) >= 1


def test_search_live():
    payload = json.loads(aiwiki_search_articles("gibson", limit=5))
    assert payload["query"] == "gibson"
    assert isinstance(payload["results"], list)


def test_blueprint_live():
    payload = json.loads(aiwiki_get_article_blueprint())
    assert payload["reference_slug"] == "gibson_es_335"
    assert "schema" in payload


@pytest.mark.skipif(not os.getenv("AIWIKI_API_KEY"), reason="AIWIKI_API_KEY not set")
def test_authenticated_overview_live():
    client = AIWikiClient()
    overview = client.get_agent_overview()
    assert "slug" in overview
    assert overview["slug"].startswith("agent_")
