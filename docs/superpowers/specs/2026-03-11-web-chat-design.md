# Web Chat per ERPClaw — Design Spec

**Data:** 2026-03-11
**Stato:** Approvato

## Contesto

ERPClaw espone l'agente AI tramite Telegram. Questo spec aggiunge una seconda interfaccia web chat accessibile dal pannello FastAPI già esistente, per uso interno del titolare.

## Requisiti

- Accesso riservato al titolare (nessun auth — uso solo locale)
- Stessa memoria agente del canale Telegram (stesso `user_id`)
- Storia conversazione visibile durante la sessione browser
- Interfaccia minimale, coerente con lo shop portal

## Architettura

### Nuovi file

| File | Ruolo |
|------|-------|
| `erpclaw/chat.py` | `APIRouter(prefix="/chat")` — logica chat |
| `erpclaw/templates/chat/chat.html` | Pagina completa |
| `erpclaw/templates/chat/_messaggi.html` | Partial HTMX (lista messaggi) |

### File modificati

| File | Modifica |
|------|----------|
| `erpclaw/web.py` | `app.include_router(chat_router)` |
| `erpclaw/config.py` | Aggiunge `TITOLARE_TELEGRAM_ID` |
| `.env` | Aggiunge `TITOLARE_TELEGRAM_ID=<id>` |

## Route

| Route | Metodo | Comportamento |
|-------|--------|---------------|
| `/chat` | GET | Renderizza pagina; crea cookie sessione UUID se assente |
| `/chat/send` | POST | Riceve `message` (form), chiama `run_agent()`, restituisce partial HTML |

## Stato Sessione

- Dict in-memory in `chat.py`: `chat_sessions: dict[str, list[dict]]`
- Struttura entry: `{"role": "user"|"assistant", "content": str}`
- Chiave: UUID session cookie generato al primo `GET /chat`
- Reset al riavvio del server (la memoria agente in `agent.db` persiste)

## User ID

- `TITOLARE_TELEGRAM_ID` dal `.env` → passato come `user_id` a `run_agent()`
- Garantisce condivisione della memoria agente tra Telegram e web chat

## UI

Layout a colonna singola:
```
┌─────────────────────────────┐
│  ERPClaw Chat               │
├─────────────────────────────┤
│                             │
│  [user] ciao                │
│  [bot]  Ciao! Come posso... │
│  [user] lista articoli      │
│  [bot]  | Codice | ...      │
│                             │
├─────────────────────────────┤
│  [input testo    ] [Invia]  │
└─────────────────────────────┘
```

- Stile CSS inline minimalista, coerente con shop portal
- Markdown dell'agente renderizzato come HTML
- HTMX: `hx-post="/chat/send"`, `hx-target="#messaggi"`, `hx-indicator` per spinner
- Scroll automatico all'ultimo messaggio (JS inline)

## Gestione Errori

- Eccezione in `run_agent()` → messaggio di errore inline nella chat
- Cookie assente → redirect a `GET /chat`
- Nessun timeout lato server (risposte DeepSeek richiedono 5–15s)

## Dipendenze

- `markdown2` o `mistune` per rendering markdown → verificare disponibilità in `pyproject.toml`
- HTMX CDN già presente nei template shop (da verificare) o da aggiungere
