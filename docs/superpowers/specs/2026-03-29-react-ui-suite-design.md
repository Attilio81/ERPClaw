# React UI Suite — Design Specification
**Date:** 2026-03-29
**Status:** Approved

## 1. Overview

Sostituire le pagine Jinja2 admin-side di ERPClaw con una Single Page Application React. Il backend FastAPI rimane invariato; vengono aggiunti endpoint JSON dove mancanti. Lo shop Jinja2 (`/shop/*`) non è incluso in questo progetto.

**Pagine incluse:**
| Pagina | Path React Router | Descrizione |
|--------|------------------|-------------|
| Homepage | `/` | Navigazione rapida a tutte le sezioni |
| Agent Dashboard | `/agents` | Editor visivo xyflow per agenti/tool |
| Config Panel | `/config` | Editor variabili `.env` |
| Chat | `/chat` | Interfaccia chat con l'agente AI |

---

## 2. Architettura

```
ERPClaw/
  frontend/              ← Vite + React SPA
    src/
      pages/
        Home.tsx
        AgentDashboard.tsx
        ConfigPanel.tsx
        Chat.tsx
      components/
        layout/
          Sidebar.tsx    ← nav laterale con icone, collassabile
          TopBar.tsx     ← titolo pagina + status indicator
        agents/
          AgentNode.tsx  ← nodo xyflow custom: Team
          TeamNode.tsx
          ToolNode.tsx
          MemoryNode.tsx
          NodeEditSheet.tsx ← shadcn Sheet per editing
        config/
          EnvSection.tsx ← Card collassabile per gruppo di variabili
        chat/
          MessageBubble.tsx
          ChatInput.tsx
      lib/
        api.ts           ← fetch wrappers tipizzati verso FastAPI
        types.ts         ← TypeScript types condivisi
      App.tsx            ← React Router layout con Sidebar + TopBar
      main.tsx
    vite.config.ts       ← proxy /api/* /agents/* /config/* /chat/* → :8000
    package.json
    tailwind.config.ts
    components.json      ← shadcn/ui config
  erpclaw/               ← FastAPI invariato (con aggiunte minime)
```

**In sviluppo:** due processi — `npm run dev` (5173) e `uvicorn` (8000). Vite proxies tutti i path `/agents`, `/config`, `/chat` verso `:8000`.

**In produzione:** `npm run build` → output in `frontend/dist/`. FastAPI serve `frontend/dist` come `StaticFiles` con una catch-all route `GET /{full_path}` → `index.html`. Il catch-all ha priorità inferiore a tutti gli altri router (shop, admin, agenti, config, chat API).

---

## 3. Stack

| Tool | Versione | Ruolo |
|------|----------|-------|
| Vite | 6.x | Build tool + dev server |
| React | 19.x | UI framework |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Utility-first styling |
| shadcn/ui | latest | Componenti accessibili |
| React Router | 7.x | Client-side routing |
| @xyflow/react | latest | Canvas nodi agent dashboard |

Nessuna libreria di state management globale (useState/useEffect sufficienti per questo scope).

---

## 4. Pagine

### 4.1 Homepage (`/`)
Grid di 4 card: Agenti, Configurazione, Chat, Admin (link esterno a `/admin`). Dark theme coerente con l'attuale `#1a1a2e`. Ogni card ha icona, titolo, breve descrizione e freccia di navigazione.

### 4.2 Agent Dashboard (`/agents`)
Canvas xyflow fullscreen (sotto la Sidebar + TopBar). Nodi custom:
- **TeamNode** (rosso `#e94560`) — nome, thinking, history runs, lista members e tools
- **AgentNode** (viola `#533483`) — nome, ruolo, thinking, lista tools
- **ToolNode** (blu `#0f3460`) — label, descrizione, conteggio metodi
- **MemoryNode** (verde `#1b6b3a`) — memory capture instructions (troncate)

Edges animati con `animated: true`, colore per tipo di connessione (stesso schema attuale).

Interazioni:
- **Doppio click** su nodo → apre shadcn `Sheet` laterale con form di editing
- **Toolbar** (pannello xyflow controls): Salva config, Ricarica agenti, Fit view, Minimap toggle
- Il layout iniziale delle posizioni viene da `GET /agents/api/config` (campo `position` per ogni nodo)
- Drag → aggiorna posizione nel config locale; Salva → `PUT /agents/api/config`

### 4.3 Config Panel (`/config`)
Form a sezioni collapsible (shadcn `Collapsible`):
- **Telegram** — `TELEGRAM_BOT_TOKEN`, `ALLOWED_CHAT_ID`
- **LLM** — `LLM_PROVIDER` (select: lmstudio/deepseek), `LLM_MODEL_ID`, `LMSTUDIO_BASE_URL`, `DEEPSEEK_API_KEY`
- **OpenAI** — `OPENAI_API_KEY`
- **Shop** — `SHOP_SECRET_KEY`

Campi token/chiavi API: `type="password"` con toggle show/hide. Bottone "Salva" → `PUT /config/api`. Toast di conferma/errore.

### 4.4 Chat (`/chat`)
Layout a colonna piena:
- Lista messaggi scorrevole (utente destra, agente sinistra)
- Messaggi agente renderizzati come HTML (il backend restituisce già markdown→HTML)
- Input in basso (textarea, invio con Enter o bottone)
- Durante il caricamento: indicatore "..." animato
- `POST /chat/api/send` con `{ message: string }` → `{ html: string, role: "assistant" }`
- Storico pre-caricato da `GET /chat/api/history`

---

## 5. API Contract

### Endpoint esistenti (nessuna modifica)
| Method | Path | Uso |
|--------|------|-----|
| GET | `/agents/api/config` | Legge config agenti |
| PUT | `/agents/api/config` | Salva config agenti |
| POST | `/agents/api/reload` | Ricarica team da config |

### Nuovi endpoint da aggiungere a FastAPI

**`erpclaw/config_panel.py`**
```
GET  /config/api        → { TELEGRAM_BOT_TOKEN: str, ... }  (tutti gli ENV_KEYS)
PUT  /config/api        → body: { key: value, ... } → 200 OK
```

**`erpclaw/chat.py`**
```
GET  /chat/api/history  → [ { role: "user"|"assistant", content: str }, ... ]
POST /chat/api/send     → body: { message: str }
                        → { role: "assistant", content: str }
```
`content` è già HTML (markdown2 renderizzato), come nell'implementazione attuale.

---

## 6. Modifiche a FastAPI

**`erpclaw/web.py`** — aggiungere in fondo (dopo tutti gli altri router):
```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    return FileResponse("frontend/dist/index.html")
```
Questo viene eseguito solo in produzione (quando `frontend/dist` esiste). In dev, Vite serve la SPA.

**`erpclaw/config_panel.py`** — aggiungere due route JSON mantenendo le route Jinja2 esistenti (retrocompatibilità durante la migrazione).

**`erpclaw/chat.py`** — aggiungere due route JSON mantenendo le route Jinja2 esistenti.

---

## 7. Dev Workflow

```bash
# Terminale 1 — backend
uv run uvicorn erpclaw.web:app --reload

# Terminale 2 — frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

`start.bat` verrà aggiornato per avviare anche `npm run dev` nella cartella `frontend`.

---

## 8. Build & Deploy

```bash
cd frontend
npm run build
# → frontend/dist/

# FastAPI serve automaticamente frontend/dist via spa_fallback
uv run uvicorn erpclaw.web:app
```

---

## 9. Fuori scope

- Autenticazione per le pagine admin (non esiste nell'attuale sistema)
- Shop portal (rimane Jinja2)
- SQLAdmin (`/admin`) — rimane invariato, link nella homepage
- Test E2E per il frontend
- SSR / SSG
