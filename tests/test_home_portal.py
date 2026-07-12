def test_home_page_welcome_and_mcp_section(client):
    response = client.get("/")
    assert response.status_code == 200
    text = response.text
    assert "portal-welcome-header" in text
    assert "Welcome to AIWiki" in text
    assert "home-article-count" in text
    assert "portal-announcements" in text
    assert "portal-badge-new" in text
    assert "Version 0.5.2" in text
    assert "AIWiki MCP server" in text
    assert text.index("portal-welcome") < text.index("portal-announcements")
    assert text.index("portal-announcements") < text.index("portal-grid")
    assert "mcp-clients/claude-code.png" in text
    assert "mcp-clients/codex-light.png" in text
    assert "mcp-clients/codex-dark.png" in text
    assert "mcp-clients/zed-light.svg" in text
    assert "mcp-logo-dark" in text
    assert "OpenClaw" in text
    assert "Codex" in text
