def test_search_articles(client):
    import uuid

    title = f"SearchTarget{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": f"SearchBot{uuid.uuid4().hex[:8]}"})
    api_key = reg.json()["api_key"]
    client.post(
        "/api/v1/contribute/article",
        headers={"X-API-Key": api_key},
        json={"title": title, "content": "Unique searchable phrase xyzzy", "summary": "s"},
    )

    api = client.get("/api/v1/search", params={"q": "xyzzy"})
    assert api.status_code == 200
    assert len(api.json()["results"]) >= 1

    page = client.get("/search", params={"q": "xyzzy"})
    assert page.status_code == 200
    assert "xyzzy" in page.text.lower()


def test_check_article_title(client):
    import uuid

    title = f"CheckTitle{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": f"CheckBot{uuid.uuid4().hex[:8]}"})
    api_key = reg.json()["api_key"]
    client.post(
        "/api/v1/contribute/article",
        headers={"X-API-Key": api_key},
        json={"title": title, "content": "Body", "summary": "s"},
    )

    missing = client.get("/api/v1/articles/check", params={"title": f"Other{uuid.uuid4().hex[:8]}"})
    assert missing.status_code == 200
    assert missing.json()["exists"] is False

    exists = client.get("/api/v1/articles/check", params={"title": title})
    assert exists.status_code == 200
    assert exists.json()["exists"] is True


def test_agent_activity_and_webhook(client, monkeypatch):
    import uuid

    events = []

    def fake_dispatch(agent_id, event, payload):
        events.append({"agent_id": agent_id, "event": event, "payload": payload})

    monkeypatch.setattr("core.webhooks.dispatch", fake_dispatch)

    name = f"HookBot{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": name})
    data = reg.json()
    api_key = data["api_key"]
    assert any(e["event"] == "agent.registered" for e in events)

    client.post(
        "/api/v1/agent/webhook",
        headers={"X-API-Key": api_key},
        json={"url": "https://example.com/hook"},
    )
    hook = client.get("/api/v1/agent/webhook", headers={"X-API-Key": api_key})
    assert hook.json()["webhook_url"] == "https://example.com/hook"

    client.post(
        "/api/v1/contribute/article",
        headers={"X-API-Key": api_key},
        json={"title": f"HookArt{uuid.uuid4().hex[:8]}", "content": "Hook test", "summary": "s"},
    )
    assert any(e["event"] == "article.created" for e in events)

    activity = client.get(f"/api/v1/agents/{name}/activity")
    assert activity.status_code == 200
    assert len(activity.json()["activity"]) >= 1

    own = client.get("/api/v1/agent/activity", headers={"X-API-Key": api_key})
    assert own.status_code == 200


def test_health_extended(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "database_latency_ms" in data
    assert data.get("version") == "0.5.2"
    assert "rate_limit_backend" in data
    assert data["rate_limit_backend"] in ("memory", "redis")
    assert "agent_loop" in data
    assert data["agent_loop"]["enabled"] is False


def test_encyclopedia_articles_exclude_overviews(client):
    import uuid

    import core.database as db

    name = f"IndexBot{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": name})
    overview_slug = reg.json()["overview_slug"]

    slugs = [a["slug"] for a in db.get_encyclopedia_articles()]
    assert overview_slug not in slugs

    page = client.get("/")
    assert page.status_code == 200
    overview_page = client.get(f"/wiki/{overview_slug}")
    assert overview_page.status_code == 200
    assert name in overview_page.text


def test_static_cache_headers(client):
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "max-age=" in response.headers.get("cache-control", "")


def test_static_asset_cache_busting(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "no-store" in response.headers["cache-control"]
    assert "/static/style.css?v=" in response.text
    assert "/static/theme_manager.js?v=" in response.text
    assert "/theme.css?v=" in response.text
    assert "/static/live_updates.js?v=" in response.text
    assert 'name="aiwiki-static-version"' in response.text
    assert 'name="aiwiki-theme-config"' in response.text


def test_theme_stylesheet(client):
    response = client.get("/theme.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")
    assert "no-store" in response.headers.get("cache-control", "")
    assert "--bg-body:" in response.text
    assert "--layout-max-width:" in response.text
    assert '[data-theme="dark"]' in response.text


def test_live_version_endpoint(client):
    response = client.get("/api/v1/live/version")
    assert response.status_code == 200
    assert "no-store" in response.headers.get("cache-control", "")
    data = response.json()
    assert data["static_version"]


def test_live_home_endpoint(client):
    response = client.get("/api/v1/live/home")
    assert response.status_code == 200
    data = response.json()
    assert "static_version" in data
    assert "featured_articles" in data
    assert "recent_changes" in data
    assert "article_count" in data
    assert "agents" in data


def test_live_recent_changes_includes_agents(client):
    response = client.get("/api/v1/live/recent-changes")
    assert response.status_code == 200
    data = response.json()
    assert "changes" in data
    assert "agents" in data


def test_csp_nonce_on_page(client):
    response = client.get("/")
    csp = response.headers.get("content-security-policy", "")
    assert "nonce-" in csp
    assert 'nonce="' in response.text or "nonce='" in response.text
