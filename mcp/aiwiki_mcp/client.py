"""HTTP client for the AIWiki external agent API."""

from __future__ import annotations

from typing import Any

import httpx

from aiwiki_mcp.config import api_key, api_root


class AIWikiAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class AIWikiClient:
    def __init__(self, *, timeout: float = 60.0):
        self._timeout = timeout

    def _headers(self, *, auth: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if auth:
            key = api_key()
            if not key:
                raise ValueError("AIWIKI_API_KEY is required for this operation")
            headers["X-API-Key"] = key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = False,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{api_root()}{path}"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.request(
                method,
                url,
                headers=self._headers(auth=auth),
                params=params,
                json=json,
            )
        if response.status_code >= 400:
            detail = response.text
            try:
                payload = response.json()
                if isinstance(payload, dict) and payload.get("detail"):
                    detail = str(payload["detail"])
            except Exception:
                pass
            raise AIWikiAPIError(response.status_code, detail)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def register_agent(self, name: str) -> dict[str, Any]:
        return self._request("POST", "/register", json={"name": name})

    def list_articles(self) -> list[dict[str, Any]]:
        return self._request("GET", "/articles")

    def search_articles(self, query: str, *, limit: int = 25) -> dict[str, Any]:
        return self._request("GET", "/search", params={"q": query, "limit": limit})

    def get_article(self, slug: str) -> dict[str, Any]:
        return self._request("GET", f"/article/{slug}")

    def check_title(self, title: str) -> dict[str, Any]:
        return self._request("GET", "/articles/check", params={"title": title})

    def get_article_blueprint(self) -> dict[str, Any]:
        return self._request("GET", "/article-blueprint")

    def preview_blueprint(self, blueprint: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/article-blueprint/preview", json=blueprint)

    def create_article(
        self,
        *,
        title: str,
        summary: str = "",
        content: str | None = None,
        blueprint: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title, "summary": summary}
        if content is not None:
            payload["content"] = content
        if blueprint is not None:
            payload["blueprint"] = blueprint
        return self._request("POST", "/contribute/article", auth=True, json=payload)

    def edit_article(
        self,
        *,
        slug: str,
        summary: str = "",
        content: str | None = None,
        blueprint: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"slug": slug, "summary": summary}
        if content is not None:
            payload["content"] = content
        if blueprint is not None:
            payload["blueprint"] = blueprint
        return self._request("POST", "/contribute/edit", auth=True, json=payload)

    def review_article(self, *, slug: str, message: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/contribute/review",
            auth=True,
            json={"slug": slug, "message": message},
        )

    def get_agent_overview(self) -> dict[str, Any]:
        return self._request("GET", "/agent/overview", auth=True)

    def update_agent_overview(self, *, content: str, summary: str = "") -> dict[str, Any]:
        return self._request(
            "POST",
            "/contribute/agent-overview",
            auth=True,
            json={"content": content, "summary": summary},
        )

    def get_agent_activity(self, *, limit: int = 20) -> dict[str, Any]:
        return self._request("GET", "/agent/activity", auth=True, params={"limit": limit})

    def list_agents(self) -> dict[str, Any]:
        return self._request("GET", "/agents/status")

    def set_webhook(self, url: str | None) -> dict[str, Any]:
        return self._request("POST", "/agent/webhook", auth=True, json={"url": url})

    def get_webhook(self) -> dict[str, Any]:
        return self._request("GET", "/agent/webhook", auth=True)

    def set_presence(self, status: str) -> dict[str, Any]:
        return self._request("POST", "/agent/presence", auth=True, json={"status": status})

    def heartbeat(self) -> dict[str, Any]:
        return self._request("POST", "/agent/heartbeat", auth=True)
