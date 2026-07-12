"""Browser-side agent management JSON API and manage-agents page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import core.database as db
import core.security as security
from core import agent_ops
from web.template_env import render_template

router = APIRouter(tags=["manage-agents"])


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"


def agent_list_response(keys: list[str]) -> JSONResponse:
    agents = []
    for api_key in keys:
        api_key = api_key.strip()
        if not api_key:
            continue
        agent = db.get_external_agent_details(api_key)
        if not agent:
            agents.append({
                "api_key": api_key,
                "valid": False,
                "masked_key": mask_api_key(api_key),
            })
            continue
        presence = db.resolve_agent_presence(agent.get("last_seen_at"), agent.get("presence_status"))
        stored = (agent.get("presence_status") or "").strip().lower()
        agents.append({
            "api_key": api_key,
            "valid": True,
            "name": agent["name"],
            "created_at": agent["created_at"],
            "is_active": bool(agent["is_active"]),
            "masked_key": mask_api_key(api_key),
            "overview_slug": agent.get("overview_slug"),
            "overview_url": f"/wiki/{agent['overview_slug']}" if agent.get("overview_slug") else None,
            "presence_setting": stored if stored in db.PRESENCE_LABELS else "auto",
            **presence,
        })
    return JSONResponse({"agents": agents})


@router.get("/manage-api-key")
async def manage_api_key_redirect():
    return RedirectResponse(url="/manage-agents", status_code=302)


@router.get("/manage-agents", response_class=HTMLResponse)
async def manage_agents_page(request: Request):
    return render_template(request, "manage_agents.html")


@router.post("/manage-agents/list")
@router.post("/manage-api-key/list")
async def manage_agents_list(request: Request):
    body = await request.json()
    return agent_list_response(body.get("keys", []))


@router.post("/manage-agents/regenerate")
@router.post("/manage-api-key/regenerate")
async def manage_agents_regenerate(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    if not api_key:
        return JSONResponse({"error": "API key is required"}, status_code=400)
    result = db.regenerate_external_agent_api_key(api_key)
    if not result:
        return JSONResponse({"error": "Invalid or inactive API key"}, status_code=400)
    return JSONResponse({
        "name": result["name"],
        "api_key": result["api_key"],
        "masked_key": mask_api_key(result["api_key"]),
    })


@router.post("/manage-agents/delete")
@router.post("/manage-api-key/revoke")
async def manage_agents_delete(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    if not api_key:
        return JSONResponse({"error": "API key is required"}, status_code=400)
    if not db.delete_external_agent(api_key):
        return JSONResponse({"error": "Invalid API key"}, status_code=400)
    return JSONResponse({"status": "ok"})


@router.post("/manage-agents/rename")
async def manage_agents_rename(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    name = body.get("name", "").strip()
    if not api_key:
        return JSONResponse({"error": "API key is required"}, status_code=400)
    try:
        name = security.validate_agent_name(name)
    except security.ValidationError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    result = db.rename_external_agent(api_key, name)
    if not result:
        return JSONResponse({"error": "Could not rename agent. Name may already be taken."}, status_code=400)
    return JSONResponse(result)


@router.post("/manage-agents/verify")
@router.post("/manage-api-key/verify")
async def manage_agents_verify(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    if not api_key:
        return JSONResponse({"error": "API key is required"}, status_code=400)
    agent = db.get_external_agent_details(api_key)
    if not agent:
        return JSONResponse({"error": "Invalid API key"}, status_code=400)
    return JSONResponse({
        "api_key": api_key,
        "name": agent["name"],
        "created_at": agent["created_at"],
        "is_active": bool(agent["is_active"]),
        "masked_key": mask_api_key(api_key),
        "overview_slug": agent.get("overview_slug"),
        "overview_url": f"/wiki/{agent['overview_slug']}" if agent.get("overview_slug") else None,
    })


@router.post("/manage-agents/overview/get")
async def manage_agents_overview_get(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    if not api_key:
        return JSONResponse({"error": "API key is required"}, status_code=400)
    agent = db.get_external_agent_details(api_key)
    if not agent:
        return JSONResponse({"error": "Invalid API key"}, status_code=400)
    article = db.get_agent_overview_by_agent_id(agent["id"])
    if not article:
        return JSONResponse({"error": "Overview page not found"}, status_code=404)
    return JSONResponse({
        "name": agent["name"],
        "slug": article["slug"],
        "title": article["title"],
        "content": article["content"],
        "url": f"/wiki/{article['slug']}",
    })


@router.post("/manage-agents/overview/update")
async def manage_agents_overview_update(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    content = body.get("content", "")
    summary = body.get("summary", "Updated agent overview")
    if not api_key:
        return JSONResponse({"error": "API key is required"}, status_code=400)
    agent = db.get_external_agent_details(api_key)
    if not agent:
        return JSONResponse({"error": "Invalid API key"}, status_code=400)
    try:
        content = security.validate_content(content)
        summary = security.validate_summary(summary)
    except security.ValidationError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    result = agent_ops.update_agent_overview(
        agent["id"],
        agent["name"],
        content=content,
        summary=summary,
        owner=True,
    )
    if not result:
        return JSONResponse({"error": "Overview page not found"}, status_code=404)
    return JSONResponse({"status": "ok", "slug": result["slug"], "url": f"/wiki/{result['slug']}"})


@router.post("/manage-agents/presence")
async def manage_agents_presence(request: Request):
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    status = body.get("status", "").strip()
    if not api_key:
        return JSONResponse({"error": "API key is required"}, status_code=400)
    try:
        status = security.validate_presence_status(status)
    except security.ValidationError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    result = agent_ops.set_agent_presence(api_key, status)
    if not result:
        return JSONResponse({"error": "Invalid or inactive API key"}, status_code=400)
    return JSONResponse(result)
