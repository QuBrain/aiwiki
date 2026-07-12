from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from starlette.requests import Request

from core import config
from web.static_assets import static_url
from web.theme_manager import client_config_json, theme_css_url
from wiki.code_blocks import normalize_language, pygments_css_url, render_code_block

templates = Jinja2Templates(directory="templates")
templates.env.globals["wiki_edit_enabled"] = config.WIKI_EDIT_ENABLED
templates.env.globals["static_url"] = static_url
templates.env.globals["public_base_url"] = config.PUBLIC_BASE_URL.rstrip("/")
templates.env.globals["app_version"] = config.APP_VERSION
templates.env.globals["donation_url"] = config.DONATION_URL
templates.env.globals["theme_css_url"] = theme_css_url
templates.env.globals["pygments_css_url"] = pygments_css_url
templates.env.globals["theme_client_config_json"] = client_config_json


def _highlight_code_filter(code: str, language: str = "") -> Markup:
    return Markup(render_code_block(code, normalize_language(language)))


templates.env.filters["highlight_code"] = _highlight_code_filter


def render_template(request: Request, name: str, context: dict | None = None, **kwargs):
    ctx = {k: v for k, v in (context or {}).items() if k != "request"}
    return templates.TemplateResponse(request, name, ctx, **kwargs)
