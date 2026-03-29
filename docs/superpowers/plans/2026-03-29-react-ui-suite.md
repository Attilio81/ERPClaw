# ERPClaw React UI Suite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sostituire le pagine Jinja2 admin-side con una React SPA (Vite + TypeScript + Tailwind + shadcn/ui + xyflow) mantenendo FastAPI come backend.

**Architecture:** `frontend/` Vite project in dev proxies le chiamate API verso FastAPI :8000. In produzione `npm run build` scrive in `frontend/dist/` e FastAPI lo serve via catch-all route. Si aggiungono endpoint JSON a config e chat per supportare il frontend React.

**Tech Stack:** Vite 6, React 19, TypeScript 5, Tailwind CSS 4, shadcn/ui, React Router 7, @xyflow/react, lucide-react, sonner

---

## File Map

**Backend modificati:**
- `erpclaw/config_panel.py` — aggiunti `GET /config/api` e `PUT /config/api`
- `erpclaw/chat.py` — aggiunti `GET /chat/api/history` e `POST /chat/api/send`
- `erpclaw/web.py` — aggiunto mount static files + SPA catch-all

**Frontend creati:**
- `frontend/package.json`, `vite.config.ts`, `tsconfig.app.json`, `index.html`
- `frontend/src/main.tsx`, `App.tsx`, `index.css`
- `frontend/src/lib/types.ts` — TypeScript types condivisi
- `frontend/src/lib/api.ts` — fetch wrappers tipizzati
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/pages/Home.tsx`
- `frontend/src/pages/ConfigPanel.tsx`
- `frontend/src/components/config/EnvSection.tsx`
- `frontend/src/pages/Chat.tsx`
- `frontend/src/pages/AgentDashboard.tsx`
- `frontend/src/components/agents/flowUtils.ts`
- `frontend/src/components/agents/TeamNode.tsx`
- `frontend/src/components/agents/AgentNode.tsx`
- `frontend/src/components/agents/ToolNode.tsx`
- `frontend/src/components/agents/MemoryNode.tsx`
- `frontend/src/components/agents/NodeEditSheet.tsx`

**Test aggiunti:**
- `tests/test_config_panel.py` — aggiunti test per `/config/api`
- `tests/test_chat_api.py` — nuovo file per `/chat/api/*`

**Altri:**
- `start.bat` — aggiunta riga per avviare `npm run dev`

---

### Task 1: Config JSON API

**Files:**
- Modify: `erpclaw/config_panel.py`
- Test: `tests/test_config_panel.py`

- [ ] **Step 1: Scrivi i test che falliscono**

Aggiungi in fondo a `tests/test_config_panel.py`:

```python
# ── JSON API endpoints ────────────────────────────────────────────────────────

def test_api_get_returns_all_keys(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=deepseek\nTELEGRAM_BOT_TOKEN=tok123\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.get("/config/api")
    assert r.status_code == 200
    data = r.json()
    assert data["LLM_PROVIDER"] == "deepseek"
    assert data["TELEGRAM_BOT_TOKEN"] == "tok123"
    assert data["ALLOWED_CHAT_ID"] == ""   # not in file → empty string


def test_api_put_updates_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.put("/config/api", json={"LLM_PROVIDER": "deepseek"})
    assert r.status_code == 200
    assert r.json()["LLM_PROVIDER"] == "deepseek"
    assert "LLM_PROVIDER=deepseek" in env.read_text()


def test_api_put_ignores_unknown_keys(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.put("/config/api", json={"UNKNOWN_KEY": "hack", "LLM_PROVIDER": "deepseek"})
    assert r.status_code == 200
    assert "UNKNOWN_KEY" not in env.read_text()
```

- [ ] **Step 2: Esegui per verificare che falliscano**

```bash
uv run --no-sync python -m pytest tests/test_config_panel.py::test_api_get_returns_all_keys -v
```
Atteso: `FAILED` (route non esiste ancora)

- [ ] **Step 3: Aggiungi i due endpoint JSON a `erpclaw/config_panel.py`**

Aggiungi dopo la route `config_post` esistente:

```python
from fastapi.responses import JSONResponse


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
```

- [ ] **Step 4: Esegui i test**

```bash
uv run --no-sync python -m pytest tests/test_config_panel.py -v
```
Atteso: tutti `PASSED`

- [ ] **Step 5: Commit**

```bash
git add erpclaw/config_panel.py tests/test_config_panel.py
git commit -m "feat: add JSON API endpoints for config panel"
```

---

### Task 2: Chat JSON API

**Files:**
- Modify: `erpclaw/chat.py`
- Create: `tests/test_chat_api.py`

- [ ] **Step 1: Crea `tests/test_chat_api.py` con i test che falliscono**

```python
"""Test per i nuovi endpoint JSON /chat/api/history e /chat/api/send."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from erpclaw.chat import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_api_history_returns_empty_list_for_new_session(client):
    r = client.get("/chat/api/history")
    assert r.status_code == 200
    assert r.json() == []


def test_api_history_sets_session_cookie(client):
    r = client.get("/chat/api/history")
    assert "chat_session" in r.cookies


def test_api_send_returns_assistant_message(client):
    with patch("erpclaw.chat.run_agent", new_callable=AsyncMock) as mock:
        mock.return_value = "Ciao! Come posso aiutarti?"
        r = client.post("/chat/api/send", json={"message": "Ciao"})
    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "assistant"
    assert "Ciao" in data["content"]  # markdown rendered, still contains the word


def test_api_send_empty_message_returns_400(client):
    r = client.post("/chat/api/send", json={"message": ""})
    assert r.status_code == 400


def test_api_send_adds_to_history(client):
    with patch("erpclaw.chat.run_agent", new_callable=AsyncMock) as mock:
        mock.return_value = "Risposta test"
        client.post("/chat/api/send", json={"message": "Domanda"})
    r = client.get("/chat/api/history")
    history = r.json()
    assert len(history) == 2  # user + assistant
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Domanda"
```

- [ ] **Step 2: Esegui per verificare che falliscano**

```bash
uv run --no-sync python -m pytest tests/test_chat_api.py -v
```
Atteso: `FAILED` (route non esistono)

- [ ] **Step 3: Aggiungi i due endpoint JSON a `erpclaw/chat.py`**

Aggiungi in fondo a `erpclaw/chat.py`:

```python
from fastapi.responses import JSONResponse


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
```

- [ ] **Step 4: Esegui i test**

```bash
uv run --no-sync python -m pytest tests/test_chat_api.py -v
```
Atteso: tutti `PASSED`

- [ ] **Step 5: Commit**

```bash
git add erpclaw/chat.py tests/test_chat_api.py
git commit -m "feat: add JSON API endpoints for chat"
```

---

### Task 3: SPA Catch-all in FastAPI

**Files:**
- Modify: `erpclaw/web.py`

Questo task non ha test automatici: la catch-all si verifica manualmente dopo il build frontend.

- [ ] **Step 1: Aggiungi static files mount e catch-all in fondo a `erpclaw/web.py`**

```python
# ── SPA catch-all (solo se frontend/dist esiste) ──────────────────────────────
from pathlib import Path as _Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_DIST = _Path("frontend/dist")

if (_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="spa-assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    index = _DIST / "index.html"
    if index.exists():
        return FileResponse(str(index))
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        "<h1>Frontend non buildato.</h1><p>Esegui: <code>cd frontend && npm run build</code></p>",
        status_code=503,
    )
```

Nota: questo blocco va aggiunto **dopo** tutti gli `app.include_router(...)` e `Admin(app, ...)` esistenti per avere la priorità corretta.

- [ ] **Step 2: Verifica che i test esistenti passino ancora**

```bash
uv run --no-sync python -m pytest tests/ -v
```
Atteso: tutti `PASSED`

- [ ] **Step 3: Commit**

```bash
git add erpclaw/web.py
git commit -m "feat: add SPA catch-all route for React frontend"
```

---

### Task 4: Frontend Project Setup

**Prerequisito:** Node.js installato (verifica con `node --version`, deve essere ≥18).

- [ ] **Step 1: Crea il progetto Vite**

Dalla root di ERPClaw:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Installa le dipendenze runtime**

```bash
npm install react-router-dom @xyflow/react lucide-react sonner
```

- [ ] **Step 3: Installa le dipendenze di sviluppo**

```bash
npm install -D tailwindcss @tailwindcss/vite @tailwindcss/typography @types/node
```

- [ ] **Step 4: Inizializza shadcn/ui**

```bash
npx shadcn@latest init
```

Quando chiede:
- Style: **Default**
- Base color: **Slate**
- CSS variables: **Yes**

- [ ] **Step 5: Aggiungi i componenti shadcn necessari**

```bash
npx shadcn@latest add button card input label select textarea sheet collapsible badge separator
```

- [ ] **Step 6: Verifica che l'app di default si avvii**

```bash
npm run dev
```
Apri `http://localhost:5173`. Deve mostrare la pagina default di Vite+React.
Chiudi con `Ctrl+C`.

- [ ] **Step 7: Commit**

```bash
cd ..
git add frontend/
git commit -m "chore: init React frontend with Vite, shadcn/ui, xyflow"
```

---

### Task 5: Vite Config, Types e API Client

**Files:**
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/tsconfig.app.json`
- Modify: `frontend/src/index.css`
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 1: Aggiorna `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    proxy: {
      '/agents': 'http://localhost:8000',
      '/config': 'http://localhost:8000',
      '/chat':   'http://localhost:8000',
      '/shop':   'http://localhost:8000',
      '/admin':  'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 2: Aggiungi path alias in `frontend/tsconfig.app.json`**

Nel campo `compilerOptions`, aggiungi:

```json
"baseUrl": ".",
"paths": {
  "@/*": ["./src/*"]
}
```

- [ ] **Step 3: Aggiorna `frontend/src/index.css`**

Sostituisci l'intero contenuto con (shadcn avrà già messo le sue variabili CSS, aggiungi solo il plugin typography):

```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";

/* Le variabili CSS di shadcn vengono aggiunte da `npx shadcn init` — non rimuoverle */
```

Se shadcn ha già generato il file con le variabili `:root { --background: ... }`, mantienile e aggiungi solo le due righe `@import` e `@plugin` in cima.

- [ ] **Step 4: Crea `frontend/src/lib/types.ts`**

```typescript
export interface Position {
  x: number
  y: number
}

export interface TeamConfig {
  name: string
  thinking: boolean
  num_history_runs: number
  instructions: string
  tools: string[]
  members: string[]
  position: Position
}

export interface AgentNodeConfig {
  name: string
  role: string
  thinking: boolean
  instructions: string
  tools: string[]
  position: Position
}

export interface ToolConfig {
  label: string
  description: string
  methods: string[]
  position: Position
}

export interface MemoryManagerConfig {
  memory_capture_instructions: string
  position: Position
}

export interface AgentConfig {
  team: TeamConfig
  agents: Record<string, AgentNodeConfig>
  tools: Record<string, ToolConfig>
  memory_manager: MemoryManagerConfig
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface EnvConfig {
  TELEGRAM_BOT_TOKEN: string
  ALLOWED_CHAT_ID: string
  LLM_PROVIDER: string
  LLM_MODEL_ID: string
  LMSTUDIO_BASE_URL: string
  OPENAI_API_KEY: string
  DEEPSEEK_API_KEY: string
  SHOP_SECRET_KEY: string
}
```

- [ ] **Step 5: Crea `frontend/src/lib/api.ts`**

```typescript
import type { AgentConfig, ChatMessage, EnvConfig } from './types'

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json() as Promise<T>
}

export const agentApi = {
  getConfig: () =>
    apiFetch<AgentConfig>('/agents/api/config'),

  updateConfig: (config: AgentConfig) =>
    apiFetch<AgentConfig>('/agents/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    }),

  reload: () =>
    apiFetch<{ status: string; message: string }>('/agents/api/reload', {
      method: 'POST',
    }),
}

export const configApi = {
  get: () =>
    apiFetch<EnvConfig>('/config/api'),

  update: (values: Partial<EnvConfig>) =>
    apiFetch<EnvConfig>('/config/api', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    }),
}

export const chatApi = {
  getHistory: () =>
    apiFetch<ChatMessage[]>('/chat/api/history'),

  send: (message: string) =>
    apiFetch<ChatMessage>('/chat/api/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    }),
}
```

- [ ] **Step 6: Verifica che TypeScript compili**

```bash
cd frontend
npm run build
```
Atteso: build completata senza errori TypeScript.

- [ ] **Step 7: Commit**

```bash
cd ..
git add frontend/vite.config.ts frontend/tsconfig.app.json frontend/src/index.css \
        frontend/src/lib/types.ts frontend/src/lib/api.ts
git commit -m "feat: configure Vite proxy, TypeScript types, and API client"
```

---

### Task 6: App Shell (Router + Sidebar + TopBar)

**Files:**
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/TopBar.tsx`

- [ ] **Step 1: Aggiorna `frontend/src/main.tsx`**

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@xyflow/react/dist/style.css'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 2: Crea `frontend/src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import { Sidebar } from './components/layout/Sidebar'
import { TopBar } from './components/layout/TopBar'
import Home from './pages/Home'
import AgentDashboard from './pages/AgentDashboard'
import ConfigPanel from './pages/ConfigPanel'
import Chat from './pages/Chat'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-[#1a1a2e] text-gray-200 overflow-hidden">
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0">
          <TopBar />
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/agents" element={<AgentDashboard />} />
              <Route path="/config" element={<ConfigPanel />} />
              <Route path="/chat" element={<Chat />} />
            </Routes>
          </main>
        </div>
      </div>
      <Toaster position="bottom-center" theme="dark" />
    </BrowserRouter>
  )
}
```

- [ ] **Step 3: Crea `frontend/src/components/layout/Sidebar.tsx`**

```tsx
import { NavLink } from 'react-router-dom'
import { Home, Bot, Settings, MessageSquare, ExternalLink } from 'lucide-react'

const links = [
  { to: '/',       icon: Home,          label: 'Home',         end: true },
  { to: '/agents', icon: Bot,           label: 'Agenti',       end: false },
  { to: '/config', icon: Settings,      label: 'Config',       end: false },
  { to: '/chat',   icon: MessageSquare, label: 'Chat',         end: false },
]

export function Sidebar() {
  return (
    <nav className="w-14 md:w-52 bg-[#16213e] border-r border-[#0f3460] flex flex-col py-4 shrink-0">
      <div className="px-4 mb-6 hidden md:flex items-center gap-2">
        <span className="text-[#e94560] font-bold text-sm">ERPClaw</span>
      </div>

      <div className="flex flex-col gap-1 px-2">
        {links.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-[#0f3460] text-white'
                  : 'text-gray-400 hover:text-white hover:bg-[#0f3460]/50',
              ].join(' ')
            }
          >
            <Icon size={18} className="shrink-0" />
            <span className="hidden md:inline">{label}</span>
          </NavLink>
        ))}
      </div>

      <div className="mt-auto px-2">
        <a
          href="/admin"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-gray-400 hover:text-white hover:bg-[#0f3460]/50 transition-colors"
        >
          <ExternalLink size={18} className="shrink-0" />
          <span className="hidden md:inline">Admin DB</span>
        </a>
      </div>
    </nav>
  )
}
```

- [ ] **Step 4: Crea `frontend/src/components/layout/TopBar.tsx`**

```tsx
import { useLocation } from 'react-router-dom'

const TITLES: Record<string, string> = {
  '/':       'Home',
  '/agents': 'Agent Dashboard',
  '/config': 'Configurazione',
  '/chat':   'Chat',
}

export function TopBar() {
  const { pathname } = useLocation()
  const title = TITLES[pathname] ?? 'ERPClaw'
  return (
    <header className="h-11 bg-[#16213e] border-b border-[#0f3460] flex items-center px-4 shrink-0">
      <h1 className="text-sm font-semibold text-gray-200">{title}</h1>
    </header>
  )
}
```

- [ ] **Step 5: Crea placeholder pages temporanee**

Crea `frontend/src/pages/Home.tsx`, `AgentDashboard.tsx`, `ConfigPanel.tsx`, `Chat.tsx` con contenuto minimo:

```tsx
// Home.tsx
export default function Home() { return <div className="p-8">Home</div> }

// AgentDashboard.tsx
export default function AgentDashboard() { return <div className="p-8">Agent Dashboard</div> }

// ConfigPanel.tsx
export default function ConfigPanel() { return <div className="p-8">Config Panel</div> }

// Chat.tsx
export default function Chat() { return <div className="p-8">Chat</div> }
```

- [ ] **Step 6: Verifica in browser**

```bash
cd frontend && npm run dev
```
Apri `http://localhost:5173`. Verifica:
- Sidebar visibile con link
- TopBar mostra il titolo corretto navigando tra le pagine
- Nessun errore in console

- [ ] **Step 7: Commit**

```bash
cd ..
git add frontend/src/
git commit -m "feat: add React app shell with router, sidebar, topbar"
```

---

### Task 7: Homepage

**Files:**
- Modify: `frontend/src/pages/Home.tsx`

- [ ] **Step 1: Implementa `frontend/src/pages/Home.tsx`**

```tsx
import { useNavigate } from 'react-router-dom'
import { Bot, Settings, MessageSquare, ExternalLink } from 'lucide-react'

interface NavCard {
  icon: React.ReactNode
  title: string
  description: string
  action: () => void
  external?: boolean
}

export default function Home() {
  const navigate = useNavigate()

  const cards: NavCard[] = [
    {
      icon: <Bot size={28} className="text-[#e94560]" />,
      title: 'Agent Dashboard',
      description: 'Visualizza e configura il team di agenti AI con editor visivo',
      action: () => navigate('/agents'),
    },
    {
      icon: <Settings size={28} className="text-[#7b2d8e]" />,
      title: 'Configurazione',
      description: 'Modifica le variabili d\'ambiente (provider LLM, token, chiavi API)',
      action: () => navigate('/config'),
    },
    {
      icon: <MessageSquare size={28} className="text-[#2a9d5c]" />,
      title: 'Chat',
      description: 'Invia messaggi all\'agente ERP direttamente dal browser',
      action: () => navigate('/chat'),
    },
    {
      icon: <ExternalLink size={28} className="text-[#1a4a8a]" />,
      title: 'Admin DB',
      description: 'Gestisci articoli, clienti, ordini e magazzino via SQLAdmin',
      action: () => window.open('/admin', '_blank'),
      external: true,
    },
  ]

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">ERPClaw</h2>
        <p className="text-gray-400 text-sm">Mini-ERP gestito da agente AI via Telegram</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {cards.map((card) => (
          <button
            key={card.title}
            onClick={card.action}
            className="bg-[#16213e] border border-[#0f3460] rounded-xl p-6 text-left
                       hover:border-[#1a4a8a] hover:bg-[#1e2a4a] transition-all group"
          >
            <div className="mb-4">{card.icon}</div>
            <h3 className="font-semibold text-white mb-1 group-hover:text-[#7eb8f7] transition-colors">
              {card.title}
            </h3>
            <p className="text-gray-400 text-sm leading-relaxed">{card.description}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verifica in browser**

```bash
cd frontend && npm run dev
```
Apri `http://localhost:5173`. Verifica che le 4 card siano visibili e i link funzionino.

- [ ] **Step 3: Commit**

```bash
cd ..
git add frontend/src/pages/Home.tsx
git commit -m "feat: add homepage with navigation cards"
```

---

### Task 8: Config Panel Page

**Files:**
- Create: `frontend/src/components/config/EnvSection.tsx`
- Modify: `frontend/src/pages/ConfigPanel.tsx`

- [ ] **Step 1: Crea `frontend/src/components/config/EnvSection.tsx`**

```tsx
import { useState } from 'react'
import { ChevronDown, Eye, EyeOff } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { EnvConfig } from '@/lib/types'

interface Field {
  key: keyof EnvConfig
  label: string
  type?: 'text' | 'password' | 'select'
  options?: string[]
  placeholder?: string
}

interface EnvSectionProps {
  title: string
  fields: Field[]
  values: Partial<EnvConfig>
  onChange: (key: keyof EnvConfig, value: string) => void
}

export function EnvSection({ title, fields, values, onChange }: EnvSectionProps) {
  const [open, setOpen] = useState(true)
  const [showSecrets, setShowSecrets] = useState(false)

  return (
    <div className="bg-[#16213e] border border-[#0f3460] rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold hover:bg-[#1e2a4a] transition-colors"
      >
        {title}
        <ChevronDown size={16} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-4">
          {fields.some(f => f.type === 'password') && (
            <button
              type="button"
              onClick={() => setShowSecrets(!showSecrets)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
            >
              {showSecrets ? <EyeOff size={12} /> : <Eye size={12} />}
              {showSecrets ? 'Nascondi valori' : 'Mostra valori'}
            </button>
          )}

          {fields.map((field) => (
            <div key={field.key}>
              <Label className="text-xs text-gray-400 uppercase tracking-wide mb-1 block">
                {field.label}
              </Label>
              {field.type === 'select' ? (
                <Select
                  value={values[field.key] || ''}
                  onValueChange={(v) => onChange(field.key, v)}
                >
                  <SelectTrigger className="bg-[#1a1a2e] border-[#0f3460]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {field.options?.map(opt => (
                      <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  type={field.type === 'password' && !showSecrets ? 'password' : 'text'}
                  value={values[field.key] || ''}
                  placeholder={field.placeholder}
                  onChange={(e) => onChange(field.key, e.target.value)}
                  className="bg-[#1a1a2e] border-[#0f3460] focus:border-[#533483]"
                />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Implementa `frontend/src/pages/ConfigPanel.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Save } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { EnvSection } from '@/components/config/EnvSection'
import { configApi } from '@/lib/api'
import type { EnvConfig } from '@/lib/types'

const EMPTY: EnvConfig = {
  TELEGRAM_BOT_TOKEN: '', ALLOWED_CHAT_ID: '',
  LLM_PROVIDER: 'lmstudio', LLM_MODEL_ID: '',
  LMSTUDIO_BASE_URL: '', OPENAI_API_KEY: '',
  DEEPSEEK_API_KEY: '', SHOP_SECRET_KEY: '',
}

export default function ConfigPanel() {
  const [values, setValues] = useState<EnvConfig>(EMPTY)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    configApi.get()
      .then(setValues)
      .catch(() => toast.error('Errore caricamento configurazione'))
  }, [])

  function handleChange(key: keyof EnvConfig, value: string) {
    setValues(prev => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    setSaving(true)
    try {
      const saved = await configApi.update(values)
      setValues(saved)
      toast.success('Configurazione salvata')
    } catch {
      toast.error('Errore durante il salvataggio')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-gray-400">Modifica il file <code className="text-[#7eb8f7]">.env</code></p>
        <Button onClick={handleSave} disabled={saving} size="sm"
          className="bg-[#1b6b3a] hover:bg-[#2a9d5c] border-none">
          <Save size={14} className="mr-1" />
          {saving ? 'Salvataggio…' : 'Salva'}
        </Button>
      </div>

      <EnvSection
        title="Telegram"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'TELEGRAM_BOT_TOKEN', label: 'Bot Token', type: 'password', placeholder: '123456:ABC...' },
          { key: 'ALLOWED_CHAT_ID',    label: 'Chat ID',   type: 'text',     placeholder: '12345678' },
        ]}
      />

      <EnvSection
        title="LLM"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'LLM_PROVIDER',      label: 'Provider',         type: 'select', options: ['lmstudio', 'deepseek'] },
          { key: 'LLM_MODEL_ID',      label: 'Model ID',         type: 'text',   placeholder: 'qwen/qwen3.5-9b' },
          { key: 'LMSTUDIO_BASE_URL', label: 'LM Studio URL',    type: 'text',   placeholder: 'http://localhost:1234/v1' },
          { key: 'DEEPSEEK_API_KEY',  label: 'DeepSeek API Key', type: 'password' },
        ]}
      />

      <EnvSection
        title="OpenAI (Whisper)"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'OPENAI_API_KEY', label: 'API Key', type: 'password', placeholder: 'sk-...' },
        ]}
      />

      <EnvSection
        title="Shop"
        values={values}
        onChange={handleChange}
        fields={[
          { key: 'SHOP_SECRET_KEY', label: 'Secret Key', type: 'password' },
        ]}
      />
    </div>
  )
}
```

- [ ] **Step 3: Verifica in browser**

Con FastAPI e `npm run dev` entrambi in esecuzione:
Apri `http://localhost:5173/config`. Verifica:
- Le sezioni si aprono/chiudono
- I valori del `.env` reale sono caricati
- Salva funziona (toast verde)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ConfigPanel.tsx frontend/src/components/config/
git commit -m "feat: add Config Panel page"
```

---

### Task 9: Chat Page

**Files:**
- Modify: `frontend/src/pages/Chat.tsx`

- [ ] **Step 1: Implementa `frontend/src/pages/Chat.tsx`**

```tsx
import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { chatApi } from '@/lib/api'
import type { ChatMessage } from '@/lib/types'

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatApi.getHistory()
      .then(setMessages)
      .catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const reply = await chatApi.send(text)
      setMessages(prev => [...prev, reply])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '<p>Errore di rete.</p>' }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-center text-gray-500 text-sm mt-8">
            Scrivi un messaggio per iniziare
          </p>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={[
                'max-w-[80%] rounded-xl px-4 py-2.5 text-sm',
                msg.role === 'user'
                  ? 'bg-[#533483] text-white rounded-br-sm'
                  : 'bg-[#16213e] border border-[#0f3460] text-gray-200 rounded-bl-sm',
              ].join(' ')}
            >
              {msg.role === 'user' ? (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              ) : (
                <div
                  className="prose prose-sm prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: msg.content }}
                />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#16213e] border border-[#0f3460] rounded-xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#0f3460] p-4 bg-[#16213e]">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Scrivi un messaggio… (Invio per inviare, Shift+Invio per nuova riga)"
            rows={2}
            className="bg-[#1a1a2e] border-[#0f3460] focus:border-[#533483] resize-none flex-1"
          />
          <Button
            onClick={send}
            disabled={!input.trim() || loading}
            className="bg-[#533483] hover:bg-[#7b2d8e] border-none self-end"
          >
            <Send size={16} />
          </Button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verifica in browser**

Con entrambi i server in esecuzione, apri `http://localhost:5173/chat`. Verifica:
- Storico caricato (se hai messaggi precedenti nella sessione)
- Invio messaggio → risposta agente con markdown renderizzato
- Animazione dots durante attesa
- Auto-scroll al fondo

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Chat.tsx
git commit -m "feat: add Chat page with message history"
```

---

### Task 10: Agent Dashboard — Nodi xyflow

**Files:**
- Create: `frontend/src/components/agents/flowUtils.ts`
- Create: `frontend/src/components/agents/TeamNode.tsx`
- Create: `frontend/src/components/agents/AgentNode.tsx`
- Create: `frontend/src/components/agents/ToolNode.tsx`
- Create: `frontend/src/components/agents/MemoryNode.tsx`

- [ ] **Step 1: Crea `frontend/src/components/agents/flowUtils.ts`**

```typescript
import type { Node, Edge } from '@xyflow/react'
import type { AgentConfig } from '@/lib/types'

export function configToFlow(config: AgentConfig): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []

  nodes.push({
    id: 'memory_manager',
    type: 'memoryNode',
    position: config.memory_manager.position,
    data: { ...config.memory_manager },
  })

  nodes.push({
    id: 'team',
    type: 'teamNode',
    position: config.team.position,
    data: { ...config.team },
  })

  edges.push({
    id: 'memory-team',
    source: 'memory_manager',
    target: 'team',
    animated: true,
    style: { stroke: '#2a9d5c', strokeWidth: 2 },
  })

  for (const [key, agent] of Object.entries(config.agents)) {
    nodes.push({
      id: `agent:${key}`,
      type: 'agentNode',
      position: agent.position,
      data: { ...agent, _key: key },
    })
    if (config.team.members.includes(key)) {
      edges.push({
        id: `team-agent:${key}`,
        source: 'team',
        target: `agent:${key}`,
        animated: true,
        style: { stroke: '#e94560', strokeWidth: 2 },
      })
    }
  }

  for (const [key, tool] of Object.entries(config.tools)) {
    nodes.push({
      id: `tool:${key}`,
      type: 'toolNode',
      position: tool.position,
      data: { ...tool, _key: key },
    })
    if (config.team.tools.includes(key)) {
      edges.push({
        id: `tool:${key}-team`,
        source: `tool:${key}`,
        target: 'team',
        animated: true,
        style: { stroke: '#1a4a8a', strokeWidth: 2 },
      })
    }
    for (const [agentKey, agent] of Object.entries(config.agents)) {
      if (agent.tools.includes(key)) {
        edges.push({
          id: `tool:${key}-agent:${agentKey}`,
          source: `tool:${key}`,
          target: `agent:${agentKey}`,
          animated: true,
          style: { stroke: '#7b2d8e', strokeWidth: 2 },
        })
      }
    }
  }

  return { nodes, edges }
}

export function extractPositions(nodes: Node[]): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {}
  for (const node of nodes) {
    positions[node.id] = node.position
  }
  return positions
}
```

- [ ] **Step 2: Crea `frontend/src/components/agents/TeamNode.tsx`**

```tsx
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import type { TeamConfig } from '@/lib/types'

export function TeamNode({ data, selected }: NodeProps) {
  const d = data as TeamConfig & { _key?: string }
  return (
    <div className={`min-w-[200px] max-w-[280px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#e94560]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#e94560' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #e94560, #c22d4b)' }}>
        <span className="text-xl">👥</span>
        <span className="font-semibold text-sm text-white truncate">{d.name}</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div>{d.members?.length ?? 0} membri · thinking: {d.thinking ? 'sì' : 'no'}</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {d.tools?.map(t => (
            <span key={t} className="bg-[#0f3460] text-[#7eb8f7] px-1.5 py-0.5 rounded text-[10px]">{t}</span>
          ))}
        </div>
        <div className="mt-1 text-[#888]">{d.num_history_runs} history runs</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#e94560' }} />
    </div>
  )
}
```

- [ ] **Step 3: Crea `frontend/src/components/agents/AgentNode.tsx`**

```tsx
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import type { AgentNodeConfig } from '@/lib/types'

export function AgentNode({ data, selected }: NodeProps) {
  const d = data as AgentNodeConfig & { _key?: string }
  return (
    <div className={`min-w-[200px] max-w-[280px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#7b2d8e]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#7b2d8e' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #533483, #7b2d8e)' }}>
        <span className="text-xl">🤖</span>
        <span className="font-semibold text-sm text-white truncate">{d.name}</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div className="truncate">{d.role}</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {d.tools?.map(t => (
            <span key={t} className="bg-[#0f3460] text-[#7eb8f7] px-1.5 py-0.5 rounded text-[10px]">{t}</span>
          ))}
        </div>
        <div className="mt-1 text-[#888]">thinking: {d.thinking ? 'sì' : 'no'}</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#7b2d8e' }} />
    </div>
  )
}
```

- [ ] **Step 4: Crea `frontend/src/components/agents/ToolNode.tsx`**

```tsx
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import type { ToolConfig } from '@/lib/types'

export function ToolNode({ data, selected }: NodeProps) {
  const d = data as ToolConfig & { _key?: string }
  return (
    <div className={`min-w-[180px] max-w-[260px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#1a4a8a]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#1a4a8a' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #0f3460, #1a4a8a)' }}>
        <span className="text-xl">🔧</span>
        <span className="font-semibold text-sm text-white truncate">{d.label}</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div className="truncate">{d.description}</div>
        <div className="mt-1 text-[#7eb8f7]">{d.methods?.length ?? 0} metodi</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#1a4a8a' }} />
    </div>
  )
}
```

- [ ] **Step 5: Crea `frontend/src/components/agents/MemoryNode.tsx`**

```tsx
import { Handle, Position } from '@xyflow/react'
import type { NodeProps } from '@xyflow/react'
import type { MemoryManagerConfig } from '@/lib/types'

export function MemoryNode({ data, selected }: NodeProps) {
  const d = data as MemoryManagerConfig
  const preview = (d.memory_capture_instructions || '').slice(0, 60)
  return (
    <div className={`min-w-[180px] max-w-[260px] rounded-lg shadow-xl ${selected ? 'ring-2 ring-[#2a9d5c]' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#2a9d5c' }} />
      <div className="px-3 py-2 rounded-t-lg flex items-center gap-2"
           style={{ background: 'linear-gradient(135deg, #1b6b3a, #2a9d5c)' }}>
        <span className="text-xl">🧠</span>
        <span className="font-semibold text-sm text-white">Memory Manager</span>
      </div>
      <div className="px-3 py-2 bg-[#1e2640] rounded-b-lg text-xs text-gray-400">
        <div>{preview}{preview.length === 60 ? '…' : ''}</div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#2a9d5c' }} />
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/agents/
git commit -m "feat: add custom xyflow node components for agent dashboard"
```

---

### Task 11: Agent Dashboard — Canvas + Editor

**Files:**
- Create: `frontend/src/components/agents/NodeEditSheet.tsx`
- Modify: `frontend/src/pages/AgentDashboard.tsx`

- [ ] **Step 1: Crea `frontend/src/components/agents/NodeEditSheet.tsx`**

```tsx
import { useState, useEffect } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetFooter } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { AgentConfig } from '@/lib/types'

interface NodeEditSheetProps {
  nodeId: string | null
  config: AgentConfig
  onClose: () => void
  onSave: (updated: AgentConfig) => void
}

export function NodeEditSheet({ nodeId, config, onClose, onSave }: NodeEditSheetProps) {
  const [draft, setDraft] = useState<AgentConfig>(config)

  useEffect(() => {
    setDraft(config)
  }, [config, nodeId])

  if (!nodeId) return null

  function set(path: string[], value: unknown) {
    setDraft(prev => {
      const next = structuredClone(prev) as Record<string, unknown>
      let cur = next
      for (let i = 0; i < path.length - 1; i++) {
        cur = cur[path[i]] as Record<string, unknown>
      }
      cur[path[path.length - 1]] = value
      return next as AgentConfig
    })
  }

  function handleSave() {
    onSave(draft)
    onClose()
  }

  let title = ''
  let body: React.ReactNode = null

  if (nodeId === 'team') {
    const t = draft.team
    title = `Team: ${t.name}`
    body = (
      <div className="space-y-4">
        <div>
          <Label>Nome</Label>
          <Input value={t.name} onChange={e => set(['team', 'name'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Thinking</Label>
          <Select value={String(t.thinking)} onValueChange={v => set(['team', 'thinking'], v === 'true')}>
            <SelectTrigger className="bg-[#1a1a2e] border-[#0f3460] mt-1"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="true">Sì</SelectItem>
              <SelectItem value="false">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>History Runs</Label>
          <Input type="number" min={0} max={20} value={t.num_history_runs}
            onChange={e => set(['team', 'num_history_runs'], parseInt(e.target.value) || 0)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Instructions</Label>
          <Textarea value={t.instructions} rows={10}
            onChange={e => set(['team', 'instructions'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1 font-mono text-xs" />
        </div>
      </div>
    )
  } else if (nodeId === 'memory_manager') {
    const m = draft.memory_manager
    title = 'Memory Manager'
    body = (
      <div>
        <Label>Memory Capture Instructions</Label>
        <Textarea value={m.memory_capture_instructions} rows={10}
          onChange={e => set(['memory_manager', 'memory_capture_instructions'], e.target.value)}
          className="bg-[#1a1a2e] border-[#0f3460] mt-1 font-mono text-xs" />
      </div>
    )
  } else if (nodeId.startsWith('agent:')) {
    const key = nodeId.split(':')[1]
    const a = draft.agents[key]
    title = `Agente: ${a.name}`
    body = (
      <div className="space-y-4">
        <div>
          <Label>Nome</Label>
          <Input value={a.name} onChange={e => set(['agents', key, 'name'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Ruolo</Label>
          <Input value={a.role} onChange={e => set(['agents', key, 'role'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Thinking</Label>
          <Select value={String(a.thinking)} onValueChange={v => set(['agents', key, 'thinking'], v === 'true')}>
            <SelectTrigger className="bg-[#1a1a2e] border-[#0f3460] mt-1"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="true">Sì</SelectItem>
              <SelectItem value="false">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Instructions</Label>
          <Textarea value={a.instructions} rows={10}
            onChange={e => set(['agents', key, 'instructions'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1 font-mono text-xs" />
        </div>
      </div>
    )
  } else if (nodeId.startsWith('tool:')) {
    const key = nodeId.split(':')[1]
    const t = draft.tools[key]
    title = `Tool: ${t.label}`
    body = (
      <div className="space-y-4">
        <div>
          <Label>Label</Label>
          <Input value={t.label} onChange={e => set(['tools', key, 'label'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label>Descrizione</Label>
          <Input value={t.description} onChange={e => set(['tools', key, 'description'], e.target.value)}
            className="bg-[#1a1a2e] border-[#0f3460] mt-1" />
        </div>
        <div>
          <Label className="text-xs text-gray-400">Metodi ({t.methods.length}) — sola lettura</Label>
          <div className="flex flex-wrap gap-1 mt-2">
            {t.methods.map(m => (
              <span key={m} className="bg-[#0f3460] text-[#7eb8f7] px-2 py-0.5 rounded text-xs">{m}</span>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <Sheet open={!!nodeId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="bg-[#16213e] border-[#0f3460] text-gray-200 w-[480px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-gray-200">✏️ {title}</SheetTitle>
        </SheetHeader>
        <div className="mt-6">{body}</div>
        <SheetFooter className="mt-6 flex gap-2">
          <Button variant="outline" onClick={onClose}
            className="flex-1 border-[#0f3460] text-gray-400">Annulla</Button>
          <Button onClick={handleSave}
            className="flex-1 bg-[#533483] hover:bg-[#7b2d8e] border-none">Applica</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
```

- [ ] **Step 2: Implementa `frontend/src/pages/AgentDashboard.tsx`**

```tsx
import { useCallback, useEffect, useState } from 'react'
import {
  ReactFlow, useNodesState, useEdgesState,
  Controls, MiniMap, Background, BackgroundVariant,
} from '@xyflow/react'
import { toast } from 'sonner'
import { Save, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { TeamNode }   from '@/components/agents/TeamNode'
import { AgentNode }  from '@/components/agents/AgentNode'
import { ToolNode }   from '@/components/agents/ToolNode'
import { MemoryNode } from '@/components/agents/MemoryNode'
import { NodeEditSheet } from '@/components/agents/NodeEditSheet'
import { configToFlow, extractPositions } from '@/components/agents/flowUtils'
import { agentApi } from '@/lib/api'
import type { AgentConfig } from '@/lib/types'

const NODE_TYPES = {
  teamNode:   TeamNode,
  agentNode:  AgentNode,
  toolNode:   ToolNode,
  memoryNode: MemoryNode,
}

export default function AgentDashboard() {
  const [config, setConfig] = useState<AgentConfig | null>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [editNodeId, setEditNodeId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    agentApi.getConfig()
      .then(cfg => {
        setConfig(cfg)
        const { nodes: n, edges: e } = configToFlow(cfg)
        setNodes(n)
        setEdges(e)
      })
      .catch(() => toast.error('Errore caricamento configurazione agenti'))
  }, [])

  const handleNodeDoubleClick = useCallback((_: React.MouseEvent, node: { id: string }) => {
    setEditNodeId(node.id)
  }, [])

  async function handleSave() {
    if (!config) return
    setSaving(true)
    try {
      const positions = extractPositions(nodes)
      const updated: AgentConfig = structuredClone(config)
      if (positions['team']) updated.team.position = positions['team']
      if (positions['memory_manager']) updated.memory_manager.position = positions['memory_manager']
      for (const [id, pos] of Object.entries(positions)) {
        if (id.startsWith('agent:')) {
          const key = id.split(':')[1]
          if (updated.agents[key]) updated.agents[key].position = pos
        } else if (id.startsWith('tool:')) {
          const key = id.split(':')[1]
          if (updated.tools[key]) updated.tools[key].position = pos
        }
      }
      const saved = await agentApi.updateConfig(updated)
      setConfig(saved)
      toast.success('Configurazione salvata su disco')
    } catch {
      toast.error('Errore durante il salvataggio')
    } finally {
      setSaving(false)
    }
  }

  async function handleReload() {
    try {
      await agentApi.reload()
      toast.success('Agenti ricaricati')
    } catch {
      toast.error('Errore ricarica agenti')
    }
  }

  function handleSheetSave(updated: AgentConfig) {
    setConfig(updated)
    const { nodes: n, edges: e } = configToFlow(updated)
    // Preserve current positions
    setNodes(prev => n.map(newNode => {
      const existing = prev.find(p => p.id === newNode.id)
      return existing ? { ...newNode, position: existing.position } : newNode
    }))
    setEdges(e)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#16213e] border-b border-[#0f3460]">
        <Button onClick={handleSave} disabled={saving || !config} size="sm"
          className="bg-[#1b6b3a] hover:bg-[#2a9d5c] border-none">
          <Save size={14} className="mr-1" />
          {saving ? 'Salvataggio…' : 'Salva'}
        </Button>
        <Button onClick={handleReload} disabled={!config} size="sm" variant="outline"
          className="border-[#7b2d8e] text-[#7b2d8e] hover:bg-[#533483] hover:text-white">
          <RefreshCw size={14} className="mr-1" />
          Ricarica Agenti
        </Button>
        <span className="text-xs text-gray-500 ml-2">Doppio click su un nodo per modificarlo</span>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeDoubleClick={handleNodeDoubleClick}
          nodeTypes={NODE_TYPES}
          fitView
          colorMode="dark"
        >
          <Controls />
          <MiniMap nodeColor={(node) => {
            if (node.type === 'teamNode')   return '#e94560'
            if (node.type === 'agentNode')  return '#7b2d8e'
            if (node.type === 'toolNode')   return '#1a4a8a'
            if (node.type === 'memoryNode') return '#2a9d5c'
            return '#888'
          }} />
          <Background variant={BackgroundVariant.Dots} gap={24} color="#1e2749" />
        </ReactFlow>
      </div>

      {config && (
        <NodeEditSheet
          nodeId={editNodeId}
          config={config}
          onClose={() => setEditNodeId(null)}
          onSave={handleSheetSave}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 3: Verifica in browser**

Con entrambi i server in esecuzione, apri `http://localhost:5173/agents`. Verifica:
- I nodi appaiono sul canvas con i colori corretti
- Minimap visibile
- Drag dei nodi funziona
- Doppio click apre lo Sheet laterale
- Salva → toast verde, config scritta su disco

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AgentDashboard.tsx frontend/src/components/agents/NodeEditSheet.tsx
git commit -m "feat: add Agent Dashboard with xyflow and node editor"
```

---

### Task 12: Aggiorna start.bat e verifica build di produzione

**Files:**
- Modify: `start.bat`

- [ ] **Step 1: Aggiorna `start.bat`**

Aggiungi questo blocco dopo la sezione `uv sync` e prima dei messaggi `echo`:

```bat
:: Avvia frontend React in dev (se node_modules esiste)
if exist "frontend\node_modules\" (
    echo Avvio frontend React...
    start "ERPClaw Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
    timeout /t 2 /nobreak >nul
)
```

- [ ] **Step 2: Verifica build di produzione**

```bash
cd frontend
npm run build
cd ..
uv run uvicorn erpclaw.web:app
```

Apri `http://localhost:8000`. Deve servire la SPA React. Naviga alle varie sezioni e verifica che funzionino.

- [ ] **Step 3: Esegui tutti i test Python**

```bash
uv run --no-sync python -m pytest tests/ -v
```
Atteso: tutti `PASSED`

- [ ] **Step 4: Commit finale**

```bash
git add start.bat
git commit -m "chore: update start.bat to launch React dev server"
```
