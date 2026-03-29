"""Web chat interface for ERPClaw — accessible at /chat."""

import html
import uuid
from typing import Any

import markdown2
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from erpclaw.agent import run_agent
from erpclaw.config import ALLOWED_CHAT_ID

router = APIRouter(prefix="/chat")
templates = Jinja2Templates(directory="erpclaw/templates")

COOKIE_NAME = "chat_session"

# In-memory session store: {session_id: [{"role": str, "content": str}]}
chat_sessions: dict[str, list[dict[str, Any]]] = {}


# --- Session helpers (pure functions, testable) ---

def _get_or_create_session_id(cookie_value: str | None) -> str:
    """Return existing session ID from cookie, or generate a new UUID."""
    if cookie_value:
        return cookie_value
    return str(uuid.uuid4())


def _get_history(session_id: str) -> list[dict[str, Any]]:
    """Return message history for a session (empty list if new)."""
    return chat_sessions.get(session_id, [])


def _add_message(session_id: str, role: str, content: str) -> None:
    """Append a message to the session history."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    chat_sessions[session_id].append({"role": role, "content": content})


# --- Routes ---

@router.get("", response_class=HTMLResponse)
async def chat_page(request: Request):
    sid = _get_or_create_session_id(request.cookies.get(COOKIE_NAME))
    history = _get_history(sid)
    resp = templates.TemplateResponse(request, "chat/chat.html", {"history": history})
    resp.set_cookie(COOKIE_NAME, sid, httponly=True, samesite="lax")
    return resp


@router.post("/send", response_class=HTMLResponse)
async def chat_send(request: Request, message: str = Form(...)):
    sid = _get_or_create_session_id(request.cookies.get(COOKIE_NAME))

    _add_message(sid, "user", message)

    try:
        # user_id condiviso con il bot Telegram: memoria agente unificata per il titolare
        raw_response = await run_agent(message, user_id=ALLOWED_CHAT_ID)
        html_response = markdown2.markdown(
            raw_response or "(risposta vuota)",
            extras=["tables", "fenced-code-blocks", "strike"],
        )
        _add_message(sid, "assistant", html_response)
    except Exception as e:
        _add_message(sid, "assistant", f"<p class='text-danger'>Errore: {html.escape(str(e))}</p>")

    history = _get_history(sid)
    resp = templates.TemplateResponse(request, "chat/_messaggi.html", {"history": history})
    resp.set_cookie(COOKIE_NAME, sid, httponly=True, samesite="lax")
    return resp


@router.get("/api/history")
async def chat_api_history(request: Request):
    sid = _get_or_create_session_id(request.cookies.get(COOKIE_NAME))
    history = _get_history(sid)
    resp = JSONResponse(history)
    resp.set_cookie(COOKIE_NAME, sid, httponly=True, samesite="lax")
    return resp


@router.post("/api/send")
async def chat_api_send(request: Request):
    data = await request.json()
    message = (data.get("message") or "").strip()
    if not message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    sid = _get_or_create_session_id(request.cookies.get(COOKIE_NAME))
    _add_message(sid, "user", message)

    try:
        raw = await run_agent(message, user_id=ALLOWED_CHAT_ID)
        content = markdown2.markdown(
            raw or "(risposta vuota)",
            extras=["tables", "fenced-code-blocks", "strike"],
        )
        _add_message(sid, "assistant", content)
    except Exception as e:
        content = f"<p>Errore: {html.escape(str(e))}</p>"
        _add_message(sid, "assistant", content)

    resp = JSONResponse({"role": "assistant", "content": content})
    resp.set_cookie(COOKIE_NAME, sid, httponly=True, samesite="lax")
    return resp
