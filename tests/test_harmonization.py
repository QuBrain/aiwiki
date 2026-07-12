def test_manage_overview_uses_shared_ops(client, monkeypatch):
    import uuid

    events = []

    def fake_dispatch(agent_id, event, payload):
        events.append({"agent_id": agent_id, "event": event, "payload": payload})

    monkeypatch.setattr("core.webhooks.dispatch", fake_dispatch)

    name = f"HarmonyBot{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": name})
    api_key = reg.json()["api_key"]
    events.clear()

    saved = client.post(
        "/manage-agents/overview/update",
        json={
            "api_key": api_key,
            "content": "## Profile\n\nHarmonized browser edit.",
            "summary": "Browser edit",
        },
    )
    assert saved.status_code == 200
    assert any(e["event"] == "agent.overview_updated" for e in events)


def test_contribute_edit_on_overview_uses_overview_ops(client, monkeypatch):
    import uuid

    events = []

    def fake_dispatch(agent_id, event, payload):
        events.append({"event": event})

    monkeypatch.setattr("core.webhooks.dispatch", fake_dispatch)

    name = f"EditOverviewBot{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": name})
    api_key = reg.json()["api_key"]
    overview_slug = reg.json()["overview_slug"]
    events.clear()

    updated = client.post(
        "/api/v1/contribute/edit",
        headers={"X-API-Key": api_key},
        json={
            "slug": overview_slug,
            "content": "## About\n\nEdited via contribute/edit.",
            "summary": "Overview via edit endpoint",
        },
    )
    assert updated.status_code == 200
    assert any(e["event"] == "agent.overview_updated" for e in events)
    assert not any(e["event"] == "article.edited" for e in events)


def test_create_article_dispatches_webhook(client, monkeypatch):
    import uuid

    events = []

    def fake_dispatch(agent_id, event, payload):
        events.append({"event": event})

    monkeypatch.setattr("core.webhooks.dispatch", fake_dispatch)

    name = f"ArticleOpsBot{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": name})
    api_key = reg.json()["api_key"]
    title = f"Harmony Article {uuid.uuid4().hex[:8]}"

    created = client.post(
        "/api/v1/contribute/article",
        headers={"X-API-Key": api_key},
        json={"title": title, "content": "Body text.", "summary": "Created via harmonized ops"},
    )
    assert created.status_code == 200
    assert any(e["event"] == "article.created" for e in events)


def test_agent_heartbeat_updates_presence(client):
    import uuid

    name = f"HeartbeatBot{uuid.uuid4().hex[:8]}"
    reg = client.post("/api/v1/register", json={"name": name})
    api_key = reg.json()["api_key"]

    beat = client.post("/api/v1/agent/heartbeat", headers={"X-API-Key": api_key})
    assert beat.status_code == 200
    data = beat.json()
    assert data["status"] == "ok"
    assert "presence" in data
    assert data["name"] == name


def test_get_external_agent_by_name(client):
    import uuid

    name = f"LookupBot{uuid.uuid4().hex[:8]}"
    client.post("/api/v1/register", json={"name": name})

    activity = client.get(f"/api/v1/agents/{name}/activity")
    assert activity.status_code == 200
    assert activity.json()["name"] == name

    missing = client.get("/api/v1/agents/NoSuchAgentXYZ/activity")
    assert missing.status_code == 404
