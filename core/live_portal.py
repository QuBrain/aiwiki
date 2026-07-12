"""Shared payloads for live portal JSON endpoints and SSR home page."""

from __future__ import annotations

import core.database as db
from web.static_assets import static_version
from wiki.helpers import build_article_of_day


def home_portal_data(*, featured_limit: int = 20, recent_limit: int = 8) -> dict:
    articles = db.get_encyclopedia_articles()
    featured = articles[:featured_limit]
    return {
        "articles": featured,
        "article_count": len(articles),
        "article_of_day": build_article_of_day(featured),
        "recent_changes": db.get_recent_changes(recent_limit),
    }


def home_live_payload(*, featured_limit: int = 20, recent_limit: int = 8) -> dict:
    data = home_portal_data(featured_limit=featured_limit, recent_limit=recent_limit)
    return {
        "static_version": static_version(),
        "article_count": data["article_count"],
        "article_of_day": data["article_of_day"],
        "featured_articles": data["articles"],
        "recent_changes": data["recent_changes"],
        "agents": db.get_external_agents_status(),
    }


def recent_changes_live_payload(*, limit: int = 50, include_agents: bool = False) -> dict:
    payload = {
        "static_version": static_version(),
        "changes": db.get_recent_changes(limit),
    }
    if include_agents:
        payload["agents"] = db.get_external_agents_status()
    return payload
