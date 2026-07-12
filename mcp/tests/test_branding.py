from aiwiki_mcp.branding import server_icons


def test_server_icons_load_logo():
    icons = server_icons()
    assert len(icons) == 1
    assert icons[0].mimeType == "image/png"
    assert icons[0].src.startswith("data:image/png;base64,")
    assert len(icons[0].src) > 100
