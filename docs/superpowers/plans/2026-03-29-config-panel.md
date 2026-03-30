# Config Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere un pannello web su `/config` per leggere e modificare il file `.env` senza aprirlo manualmente.

**Architecture:** Un nuovo `APIRouter` in `erpclaw/config_panel.py` con due funzioni pure (`parse_env`, `write_env`) per la gestione del file, una pagina Jinja2 con toggle LLM e campi password, montata in `web.py`.

**Tech Stack:** FastAPI, Jinja2Templates, `python-dotenv` già presente, `TestClient` per i test.

---

## File Map

| Azione | File | Responsabilità |
|--------|------|----------------|
| Create | `erpclaw/config_panel.py` | Router + funzioni parse/write `.env` |
| Create | `erpclaw/templates/config/panel.html` | Form HTML con toggle LLM e campi password |
| Create | `tests/test_config_panel.py` | Test funzioni pure + route GET/POST |
| Modify | `erpclaw/web.py` | Monta il nuovo router |

---

### Task 1: Funzioni parse_env e write_env

**Files:**
- Create: `erpclaw/config_panel.py`
- Create: `tests/test_config_panel.py`

- [ ] **Step 1: Crea il file con le funzioni pure**

Crea `erpclaw/config_panel.py`:

```python
"""Pannello di configurazione .env — GET /config, POST /config"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
```

- [ ] **Step 2: Scrivi i test per le funzioni pure**

Crea `tests/test_config_panel.py`:

```python
"""Test per config_panel: funzioni parse_env / write_env e route GET/POST."""
import pytest
from pathlib import Path
from erpclaw.config_panel import parse_env, write_env


# ── parse_env ────────────────────────────────────────────────────────────────

def test_parse_env_reads_key_value(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nBAZ=qux\n")
    assert parse_env(env) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# commento\nFOO=bar\n")
    assert parse_env(env) == {"FOO": "bar"}


def test_parse_env_ignores_blank_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("\nFOO=bar\n\n")
    assert parse_env(env) == {"FOO": "bar"}


def test_parse_env_returns_empty_for_missing_file(tmp_path):
    assert parse_env(tmp_path / "nonexistent.env") == {}


def test_parse_env_handles_value_with_equals(tmp_path):
    env = tmp_path / ".env"
    env.write_text("TOKEN=abc=def=ghi\n")
    assert parse_env(env) == {"TOKEN": "abc=def=ghi"}


# ── write_env ────────────────────────────────────────────────────────────────

def test_write_env_updates_existing_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=old\n")
    write_env(env, {"FOO": "new"})
    assert parse_env(env) == {"FOO": "new"}


def test_write_env_preserves_comments(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# commento\nFOO=old\n")
    write_env(env, {"FOO": "new"})
    content = env.read_text()
    assert "# commento" in content
    assert "FOO=new" in content


def test_write_env_adds_missing_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    write_env(env, {"FOO": "bar", "NEW_KEY": "val"})
    assert parse_env(env)["NEW_KEY"] == "val"


def test_write_env_creates_file_if_missing(tmp_path):
    env = tmp_path / ".env"
    write_env(env, {"FOO": "bar"})
    assert parse_env(env) == {"FOO": "bar"}


def test_write_env_preserves_other_keys(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=keep\nBAR=update\n")
    write_env(env, {"BAR": "new"})
    result = parse_env(env)
    assert result["FOO"] == "keep"
    assert result["BAR"] == "new"
```

- [ ] **Step 3: Esegui i test — devono passare tutti**

```bash
uv run --no-sync python -m pytest tests/test_config_panel.py -v -k "parse_env or write_env"
```

Output atteso: tutti PASS (le funzioni pure non dipendono da template).

- [ ] **Step 4: Commit**

```bash
git add erpclaw/config_panel.py tests/test_config_panel.py
git commit -m "feat: add config panel parse_env/write_env with tests"
```

---

### Task 2: Template HTML

**Files:**
- Create: `erpclaw/templates/config/panel.html`

- [ ] **Step 1: Crea la directory e il template**

Crea `erpclaw/templates/config/panel.html`:

```html
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ERPClaw — Configurazione</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#1a1a2e;color:#e0e0e0;min-height:100vh}

.topbar{height:52px;background:#16213e;display:flex;align-items:center;padding:0 20px;border-bottom:1px solid #0f3460}
.topbar h1{font-size:16px;font-weight:600;color:#e94560;margin-right:auto}
.topbar h1 span{color:#999;font-weight:400;margin-left:8px;font-size:13px}
.topbar a{color:#7eb8f7;font-size:13px;text-decoration:none;margin-left:16px}
.topbar a:hover{color:#e0e0e0}

.container{max-width:640px;margin:40px auto;padding:0 20px}

.banner{padding:12px 16px;border-radius:8px;margin-bottom:24px;font-size:14px}
.banner.ok{background:#1b3a2a;border:1px solid #2a9d5c;color:#2a9d5c}
.banner.info{background:#1a2a3e;border:1px solid #0f3460;color:#7eb8f7}

.section{background:#16213e;border:1px solid #0f3460;border-radius:10px;margin-bottom:20px;overflow:hidden}
.section-title{padding:12px 16px;background:#0f1d35;font-size:12px;font-weight:600;color:#7eb8f7;text-transform:uppercase;letter-spacing:.05em}

.field{padding:14px 16px;border-bottom:1px solid #0f2040}
.field:last-child{border-bottom:none}
.field label{display:block;font-size:12px;color:#888;margin-bottom:6px}
.field-input{display:flex;gap:8px;align-items:center}
.field input[type=text],.field input[type=password]{flex:1;background:#1a2a3e;border:1px solid #0f3460;color:#e0e0e0;padding:8px 12px;border-radius:6px;font-size:13px;font-family:monospace}
.field input:focus{outline:none;border-color:#2a6ad4}
.toggle-vis{background:#0f3460;border:none;color:#7eb8f7;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:12px;flex-shrink:0}
.toggle-vis:hover{background:#1a4a8a}

/* LLM Provider toggle */
.provider-toggle{display:flex;gap:0;padding:14px 16px}
.provider-toggle label{flex:1;text-align:center;padding:10px;cursor:pointer;border:1px solid #0f3460;font-size:13px;transition:all .2s}
.provider-toggle label:first-of-type{border-radius:8px 0 0 8px}
.provider-toggle label:last-of-type{border-radius:0 8px 8px 0;border-left:none}
.provider-toggle input[type=radio]{display:none}
.provider-toggle input[type=radio]:checked + label{background:#0f3460;color:#7eb8f7;border-color:#2a6ad4}
.provider-toggle label:hover{background:#0f2040}

.actions{display:flex;align-items:center;gap:12px;margin-top:8px}
.btn-save{background:#1b6b3a;color:#e0e0e0;border:1px solid #2a9d5c;padding:10px 24px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;transition:all .2s}
.btn-save:hover{background:#2a9d5c}
.note{font-size:12px;color:#666}
</style>
</head>
<body>

<div class="topbar">
  <h1>ERPClaw <span>Configurazione</span></h1>
  <a href="/admin">Admin</a>
  <a href="/agents/">Agenti</a>
</div>

<div class="container">

{% if saved %}
<div class="banner ok">Configurazione salvata. Le modifiche avranno effetto al prossimo riavvio del bot.</div>
{% endif %}

<div class="banner info">Modifica le variabili di configurazione. Riavvia il bot dopo il salvataggio.</div>

<form method="post" action="/config/">
<input type="hidden" name="LLM_PROVIDER" id="llm_provider_value" value="{{ values.get('LLM_PROVIDER', 'lmstudio') }}">

<!-- LLM Provider -->
<div class="section">
  <div class="section-title">Provider AI</div>
  <div class="provider-toggle">
    <input type="radio" name="_provider" id="prov_lmstudio" value="lmstudio"
      {% if values.get('LLM_PROVIDER', 'lmstudio') == 'lmstudio' %}checked{% endif %}
      onchange="setProvider('lmstudio')">
    <label for="prov_lmstudio">LM Studio (locale)</label>
    <input type="radio" name="_provider" id="prov_deepseek" value="deepseek"
      {% if values.get('LLM_PROVIDER') == 'deepseek' %}checked{% endif %}
      onchange="setProvider('deepseek')">
    <label for="prov_deepseek">DeepSeek (cloud)</label>
  </div>

  <div class="field">
    <label for="LLM_MODEL_ID">Modello (LLM_MODEL_ID)</label>
    <input type="text" id="LLM_MODEL_ID" name="LLM_MODEL_ID"
      value="{{ values.get('LLM_MODEL_ID', '') }}" autocomplete="off">
  </div>

  <div class="field" id="field_lmstudio_url">
    <label for="LMSTUDIO_BASE_URL">URL LM Studio (LMSTUDIO_BASE_URL)</label>
    <input type="text" id="LMSTUDIO_BASE_URL" name="LMSTUDIO_BASE_URL"
      value="{{ values.get('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1') }}" autocomplete="off">
  </div>

  <div class="field" id="field_deepseek_key">
    <label for="DEEPSEEK_API_KEY">DeepSeek API Key (DEEPSEEK_API_KEY)</label>
    <div class="field-input">
      <input type="password" id="DEEPSEEK_API_KEY" name="DEEPSEEK_API_KEY"
        value="{{ values.get('DEEPSEEK_API_KEY', '') }}" autocomplete="off">
      <button type="button" class="toggle-vis" onclick="toggleVis('DEEPSEEK_API_KEY', this)">mostra</button>
    </div>
  </div>
</div>

<!-- Telegram -->
<div class="section">
  <div class="section-title">Telegram</div>
  <div class="field">
    <label for="TELEGRAM_BOT_TOKEN">Bot Token (TELEGRAM_BOT_TOKEN)</label>
    <div class="field-input">
      <input type="password" id="TELEGRAM_BOT_TOKEN" name="TELEGRAM_BOT_TOKEN"
        value="{{ values.get('TELEGRAM_BOT_TOKEN', '') }}" autocomplete="off">
      <button type="button" class="toggle-vis" onclick="toggleVis('TELEGRAM_BOT_TOKEN', this)">mostra</button>
    </div>
  </div>
  <div class="field">
    <label for="ALLOWED_CHAT_ID">Chat ID consentito (ALLOWED_CHAT_ID)</label>
    <div class="field-input">
      <input type="password" id="ALLOWED_CHAT_ID" name="ALLOWED_CHAT_ID"
        value="{{ values.get('ALLOWED_CHAT_ID', '') }}" autocomplete="off">
      <button type="button" class="toggle-vis" onclick="toggleVis('ALLOWED_CHAT_ID', this)">mostra</button>
    </div>
  </div>
</div>

<!-- API Keys -->
<div class="section">
  <div class="section-title">API Keys</div>
  <div class="field">
    <label for="OPENAI_API_KEY">OpenAI API Key — Whisper (OPENAI_API_KEY)</label>
    <div class="field-input">
      <input type="password" id="OPENAI_API_KEY" name="OPENAI_API_KEY"
        value="{{ values.get('OPENAI_API_KEY', '') }}" autocomplete="off">
      <button type="button" class="toggle-vis" onclick="toggleVis('OPENAI_API_KEY', this)">mostra</button>
    </div>
  </div>
</div>

<!-- Shop -->
<div class="section">
  <div class="section-title">Shop</div>
  <div class="field">
    <label for="SHOP_SECRET_KEY">Chiave sessione (SHOP_SECRET_KEY)</label>
    <div class="field-input">
      <input type="password" id="SHOP_SECRET_KEY" name="SHOP_SECRET_KEY"
        value="{{ values.get('SHOP_SECRET_KEY', '') }}" autocomplete="off">
      <button type="button" class="toggle-vis" onclick="toggleVis('SHOP_SECRET_KEY', this)">mostra</button>
    </div>
  </div>
</div>

<div class="actions">
  <button type="submit" class="btn-save">Salva</button>
  <span class="note">Riavvia il bot per applicare le modifiche.</span>
</div>

</form>
</div>

<script>
function toggleVis(id, btn) {
  const input = document.getElementById(id);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = 'nascondi';
  } else {
    input.type = 'password';
    btn.textContent = 'mostra';
  }
}

function setProvider(provider) {
  document.getElementById('llm_provider_value').value = provider;
  document.getElementById('field_lmstudio_url').style.display =
    provider === 'lmstudio' ? '' : 'none';
  document.getElementById('field_deepseek_key').style.display =
    provider === 'deepseek' ? '' : 'none';
}

// Init on load
setProvider(document.getElementById('llm_provider_value').value);
</script>

</body>
</html>
```

- [ ] **Step 2: Commit il template**

```bash
git add erpclaw/templates/config/panel.html
git commit -m "feat: add config panel HTML template with LLM provider toggle"
```

---

### Task 3: Test route GET/POST e mount in web.py

**Files:**
- Modify: `tests/test_config_panel.py` (aggiungere test route)
- Modify: `erpclaw/web.py`

- [ ] **Step 1: Aggiungi i test per le route al file di test esistente**

Apri `tests/test_config_panel.py` e aggiungi in fondo:

```python
# ── Route tests ──────────────────────────────────────────────────────────────

import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from erpclaw.config_panel import router, parse_env, write_env, ENV_PATH


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_get_config_returns_200(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    response = client.get("/config/")
    assert response.status_code == 200


def test_get_config_shows_saved_banner(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    response = client.get("/config/?saved=true")
    assert b"salvata" in response.content


def test_post_config_redirects(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    response = client.post("/config/", data={"LLM_PROVIDER": "deepseek", "LLM_MODEL_ID": "deepseek-reasoner",
        "LMSTUDIO_BASE_URL": "", "OPENAI_API_KEY": "", "DEEPSEEK_API_KEY": "sk-test",
        "TELEGRAM_BOT_TOKEN": "", "ALLOWED_CHAT_ID": "", "SHOP_SECRET_KEY": ""},
        follow_redirects=False)
    assert response.status_code == 303
    assert "/config/" in response.headers["location"]


def test_post_config_writes_env(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    client.post("/config/", data={"LLM_PROVIDER": "deepseek", "LLM_MODEL_ID": "deepseek-reasoner",
        "LMSTUDIO_BASE_URL": "http://localhost:1234/v1", "OPENAI_API_KEY": "",
        "DEEPSEEK_API_KEY": "sk-test", "TELEGRAM_BOT_TOKEN": "", "ALLOWED_CHAT_ID": "",
        "SHOP_SECRET_KEY": ""})
    result = parse_env(env)
    assert result["LLM_PROVIDER"] == "deepseek"
    assert result["DEEPSEEK_API_KEY"] == "sk-test"
```

- [ ] **Step 2: Esegui i test delle route — devono passare**

```bash
uv run --no-sync python -m pytest tests/test_config_panel.py -v
```

Output atteso: tutti PASS.

- [ ] **Step 3: Monta il router in web.py**

In `erpclaw/web.py`, aggiungi dopo le altre import di router:

```python
from erpclaw.config_panel import router as config_router
```

E dopo `app.include_router(agents_router)`:

```python
app.include_router(config_router)
```

Il blocco aggiornato sarà:

```python
from erpclaw.shop import router as shop_router
from erpclaw.chat import router as chat_router
from erpclaw.agents_dashboard import router as agents_router
from erpclaw.config_panel import router as config_router
app.include_router(shop_router)
app.include_router(chat_router)
app.include_router(agents_router)
app.include_router(config_router)
```

- [ ] **Step 4: Commit finale**

```bash
git add tests/test_config_panel.py erpclaw/web.py
git commit -m "feat: mount config panel router, add route tests"
```

---

## Self-Review

**Spec coverage:**
- ✅ Pagina separata `/config`
- ✅ Tutte le variabili del `.env` modificabili (gruppo A + C)
- ✅ Nessuna autenticazione
- ✅ Salva solo il file, nessun riavvio automatico
- ✅ Toggle LLM Provider con campi condizionali
- ✅ Campi sensibili come `type="password"` con toggle visibilità
- ✅ Banner di conferma post-salvataggio
- ✅ Commenti `.env` preservati

**Placeholder scan:** Nessun TBD o TODO.

**Type consistency:** `parse_env` e `write_env` usano `Path` ovunque. `ENV_KEYS` lista usata coerentemente nel router e nei test.
