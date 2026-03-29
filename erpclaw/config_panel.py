"""Pannello di configurazione .env — GET /config, POST /config"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

ENV_PATH = Path(".env")

ENV_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "ALLOWED_CHAT_ID",
    "LLM_PROVIDER",
    "LLM_MODEL_ID",
    "LMSTUDIO_BASE_URL",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
    "SHOP_SECRET_KEY",
]


def parse_env(path: Path) -> dict[str, str]:
    """Legge il file .env e restituisce dict KEY→valore.
    Ignora righe vuote e commenti. Restituisce dict vuoto se il file non esiste."""
    result: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return result


def write_env(path: Path, updates: dict[str, str]) -> None:
    """Aggiorna il file .env con i nuovi valori.
    Preserva commenti e righe vuote. Aggiunge in fondo le chiavi non presenti."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:
        lines = []

    updated: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _, _ = stripped.partition("=")
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated.add(key)
                continue
        new_lines.append(line if line.endswith("\n") else line + "\n")

    for key, value in updates.items():
        if key not in updated:
            new_lines.append(f"{key}={value}\n")

    path.write_text("".join(new_lines), encoding="utf-8")


router = APIRouter(prefix="/config")
templates = Jinja2Templates(directory="erpclaw/templates")


@router.get("/", response_class=HTMLResponse)
async def config_get(request: Request, saved: bool = False):
    values = parse_env(ENV_PATH)
    return templates.TemplateResponse(
        request, "config/panel.html", {"values": values, "saved": saved}
    )


@router.post("/", response_class=RedirectResponse)
async def config_post(request: Request):
    form = await request.form()
    updates = {k: str(form.get(k, "")) for k in ENV_KEYS}
    write_env(ENV_PATH, updates)
    return RedirectResponse(url="/config/?saved=true", status_code=303)


@router.get("/api")
async def config_api_get():
    values = parse_env(ENV_PATH)
    return JSONResponse({k: values.get(k, "") for k in ENV_KEYS})


@router.put("/api")
async def config_api_put(request: Request):
    updates = await request.json()
    safe = {k: str(v) for k, v in updates.items() if k in ENV_KEYS}
    write_env(ENV_PATH, safe)
    values = parse_env(ENV_PATH)
    return JSONResponse({k: values.get(k, "") for k in ENV_KEYS})
