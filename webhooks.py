import logging
from threading import Thread

import httpx

import database as db

logger = logging.getLogger("aiwiki.webhooks")


def dispatch(agent_id: int, event: str, payload: dict) -> None:
    url = db.get_agent_webhook_url(agent_id)
    if not url:
        return

    body = {"event": event, "data": payload}

    def _send() -> None:
        try:
            httpx.post(url, json=body, timeout=10.0)
        except Exception as exc:
            logger.warning("Webhook delivery failed for agent %s (%s): %s", agent_id, event, exc)

    Thread(target=_send, daemon=True).start()
