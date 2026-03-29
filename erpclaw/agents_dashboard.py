"""Agent management dashboard — n8n-style visual editor.

Routes:
    GET  /agents/          → dashboard UI
    GET  /agents/api/config → current config as JSON
    PUT  /agents/api/config → update config (deep merge)
    POST /agents/api/reload → reload agent team from config
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from erpclaw.agent_config import get_config, update_config

router = APIRouter(prefix="/agents")
templates = Jinja2Templates(directory="erpclaw/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    config = get_config()
    return templates.TemplateResponse(request, "agents/dashboard.html", {"config": config})


@router.get("/api/config")
async def api_get_config():
    return JSONResponse(get_config())


@router.put("/api/config")
async def api_update_config(request: Request):
    patch = await request.json()
    updated = update_config(patch)
    return JSONResponse(updated)


@router.post("/api/reload")
async def api_reload():
    """Reload the agent team from the current config on disk."""
    from erpclaw.agent import reload_team
    reload_team()
    return JSONResponse({"status": "ok", "message": "Agenti ricaricati con successo"})
