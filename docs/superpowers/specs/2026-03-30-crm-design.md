# CRM Module Design — ERPClaw
**Date:** 2026-03-30

## Overview

Add a CRM module to ERPClaw for managing customer visits, calls, emails, calendar scheduling, and free-form notes. Fully integrated with Telegram (create/consult via natural language + automatic reminders) and a React monthly calendar page.

---

## 1. Database Schema

Two new tables added to `erp.db` (same pattern as existing models). Migration handled by `_migrate()` in `erp_db.py`.

### `EventoCRM`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `cliente_id` | Integer FK → `clienti.id` | nullable (event may not be tied to a client) |
| `tipo` | Enum | `visita`, `chiamata`, `email` |
| `data_ora` | DateTime | scheduled date/time |
| `durata_minuti` | Integer | nullable |
| `luogo` | String | nullable — free text, used for Google Maps link |
| `esito` | String | nullable — brief outcome |
| `note` | Text | nullable — detailed notes |
| `stato` | Enum | `pianificato`, `completato`, `annullato` |
| `reminder_inviato` | Boolean | default False — APScheduler dedup flag |

### `NotaCRM`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `cliente_id` | Integer FK → `clienti.id` | not nullable |
| `testo` | Text | free-form note content |
| `data_ora` | DateTime | default now() |
| `autore` | String | nullable — ready for multi-user future |

### Relationships

- `Cliente` gets `eventi_crm` and `note_crm` relationships (back_populates).
- `EventoCRM.cliente` → `Cliente`.

### Enums

```python
class TipoEventoCRM(str, enum.Enum):
    visita = "visita"
    chiamata = "chiamata"
    email = "email"

class StatoEventoCRM(str, enum.Enum):
    pianificato = "pianificato"
    completato = "completato"
    annullato = "annullato"
```

---

## 2. CrmTools Toolkit

New file: `erpclaw/crm_tools.py`

```python
class CrmTools(Toolkit):
    # EVENTS
    crea_evento(cliente_id, tipo, data_ora, luogo=None, note=None, durata_minuti=None) → str
    lista_eventi(data_inizio, data_fine, cliente_id=None) → str
    agenda_oggi() → str
    agenda_settimana() → str
    aggiorna_evento(evento_id, tipo=None, data_ora=None, luogo=None, note=None, durata_minuti=None, esito=None) → str
    completa_evento(evento_id, esito, note=None) → str
    annulla_evento(evento_id) → str

    # NOTES
    aggiungi_nota(cliente_id, testo) → str
    note_cliente(cliente_id) → str

    # HISTORY
    storico_cliente(cliente_id) → str   # all events + notes for a client
```

All methods return Markdown-formatted `str` for Telegram display. Uses `get_session()` as context manager, same as `ERPTools` and `LogisticaTools`.

`CrmTools` is instantiated and added to the `Team` in `erpclaw/agent.py` alongside `ERPTools` and `LogisticaTools`.

---

## 3. Reminder System

### Integration Point

`erpclaw/bot.py` — on bot startup, an `AsyncIOScheduler` (APScheduler) is started:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(check_reminders, "interval", minutes=1)
scheduler.start()
```

### `check_reminders` Logic

Runs every minute. Queries `eventi_crm` for events where:
- `stato = 'pianificato'`
- `reminder_inviato = False`
- `data_ora` is within the next 60 minutes

For each match:
1. Sends Telegram message to `ALLOWED_CHAT_ID` with: client name, event type, time, location + Google Maps link.
2. Sets `reminder_inviato = True` (prevents duplicate sends).

### Google Maps Link Format

```
https://maps.google.com/?q=<urllib.parse.quote(luogo)>
```

Included inline in the Telegram message when `luogo` is set.

### New Dependency

`apscheduler` added to `pyproject.toml` dependencies.

---

## 4. Web API

New FastAPI router: `erpclaw/crm.py` (`prefix="/crm"`), mounted in `web.py`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/crm/api/eventi?anno=&mese=` | Events for a given month (calendar feed) |
| GET | `/crm/api/eventi/{id}` | Single event detail |
| POST | `/crm/api/eventi` | Create event |
| PUT | `/crm/api/eventi/{id}` | Update event fields |
| DELETE | `/crm/api/eventi/{id}` | Soft-delete (sets `stato=annullato`) |
| GET | `/crm/api/clienti/{id}/storico` | All events + notes for a client |
| POST | `/crm/api/clienti/{id}/note` | Add a free-form note to a client |

Request/response bodies use Pydantic models (same pattern as `config_panel.py`).

---

## 5. React Calendar Page

### File

`frontend/src/pages/CrmCalendar.tsx`

### Layout

Monthly grid (7 columns × 5 rows). Each day cell shows colored event badges:

| Type | Color |
|------|-------|
| `visita` | Indigo |
| `chiamata` | Amber |
| `email` | Slate |
| `completato` | Green (overrides type color) |
| `annullato` | Gray (muted) |

### Interactions

- **Previous/Next month** arrows — refetches `/crm/api/eventi?anno=&mese=`.
- **Click on a day** → shadcn `Sheet` (drawer) opens showing: list of events for that day + "Nuovo evento" quick-add form.
- **Click on an event badge** → shadcn `Dialog` with full detail: all fields, Google Maps link button, "Completa" and "Annulla" action buttons.

### Navigation

New "CRM" entry added to the React sidebar (same pattern as Home, Dashboard, Config, Chat).

### API Client

New `crmApi` typed fetch wrapper added to `frontend/src/lib/api.ts`.

---

## 6. Agent Integration

`CrmTools` is added to `agent.py`:

```python
team = Team(
    tools=[ERPTools(), LogisticaTools(), CrmTools()],
    ...
)
```

Team `instructions` updated to describe when to use CRM tools (schedule visits, log calls, query agenda, add notes).

---

## 7. Testing

New test file `tests/test_crm_tools.py` using the same in-memory SQLite pattern as existing tool tests (`conftest.py` + `mock.patch`).

Covers:
- Create event, list events, complete event, cancel event
- Add note, list notes for client
- `storico_cliente` combining both events and notes

---

## Implementation Notes

- `reminder_inviato` flag is the dedup mechanism — no external state needed. If `data_ora` is updated via `aggiorna_evento`, `reminder_inviato` must be reset to `False` so the reminder fires again at the new time.
- `autore` on `NotaCRM` is nullable now; schema supports future multi-user without migration.
- All new DB columns go through `_migrate()` for safe upgrade of existing `erp.db`.
- Vite proxy config (`vite.config.ts`) needs `/crm` added alongside existing proxied paths.
