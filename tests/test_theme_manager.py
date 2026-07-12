from web.theme_manager import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    LAYOUT,
    client_config,
    render_css,
    theme_version,
)


def test_render_css_includes_light_and_dark_tokens():
    css = render_css()
    assert ":root {" in css
    assert '[data-theme="dark"] {' in css
    assert f"--bg-body: {LIGHT_TOKENS['bg-body']};" in css
    assert f"--bg-body: {DARK_TOKENS['bg-body']};" in css
    assert f"--layout-max-width: {LAYOUT['max_width']};" in css
    assert "--theme-transition-duration:" in css
    assert "html.theme-switching" in css
    assert "::view-transition-old(root)" in css


def test_client_config_exposes_storage_key_and_themes():
    config = client_config()
    assert config["storageKey"] == "aiwiki_theme"
    assert "light" in config["themes"]
    assert "dark" in config["themes"]
    assert config["layoutStorageKey"] == "aiwiki_layout"
    assert "normal" in config["layoutWidths"]
    assert "wide" in config["layoutWidths"]
    assert config["layout"]["max_width"] == LAYOUT["max_width"]
    assert config["transition"]["duration_ms"] == 250


def test_render_css_includes_wide_layout():
    css = render_css()
    assert 'html[data-layout="wide"]' in css
    assert "--layout-max-width: none;" in css


def test_theme_version_is_stable_for_same_css():
    first = theme_version()
    second = theme_version()
    assert first == second
    assert len(first) == 12
