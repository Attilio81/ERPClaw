# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ERPClaw** is a mini-ERP managed by an AI agent via Telegram. Users interact through natural language (text or voice). The AI agent (DeepSeek via the `agno` framework) translates requests into ERP operations on a SQLite database.

## Commands

This project uses `uv` as the package manager. Python version is pinned to **3.13** (`.python-version` file).

```bash
# Install/sync dependencies
uv sync

# Run the Telegram bot (main entry point)
uv run erpclaw

# Run the web admin panel + shop portal (same process)
uv run uvicorn erpclaw.web:app --reload
# Admin: http://localhost:8000/admin
# Shop:  http://localhost:8000/shop/register
```

`start.bat` launches both processes (web+shop in a separate window, then the bot).

**uv sync gotcha:** If the bot is running, `erpclaw.exe` is locked and `uv sync` fails. Install packages directly with `uv pip install <pkg>` instead. Run tests with `uv run --no-sync python -m pytest`.

## Environment Variables

A `.env` file is required:
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `DEEPSEEK_API_KEY` — DeepSeek API key (agent LLM)
- `OPENAI_API_KEY` — OpenAI API key (Whisper voice transcription only)
- `SHOP_SECRET_KEY` — Secret for shop session cookies (optional; defaults to dev value)

## Architecture

Two independent databases, two entry points:

### Databases
- **`erp.db`** — Business data (SQLAlchemy, synchronous): all ERP and logistics models (see table list below)
- **`agent.db`** — agno agent memory (AsyncSqliteDb): conversation history and user preferences per Telegram user ID
- **`./cataloghi/`** — Local directory for downloaded PDF catalogs (created automatically)

#### `erp.db` tables

| Group | Tables |
|-------|--------|
| Catalog | `articoli`, `categorie`, `stock_ubicazioni` |
| Clients | `clienti`, `indirizzi`, `clienti_auth` |
| Orders | `ordini`, `righe_ordine` |
| Suppliers | `fornitori`, `cataloghi_fornitori` |
| Warehouse | `magazzini`, `zone`, `scaffali`, `ripiani` |
| Movements | `movimenti_magazzino` |

`Articolo.giacenza` is a `column_property` (SQLAlchemy correlated subquery) summing `StockUbicazione.quantita`. It is **read-only** — never write to it directly. Stock is managed via `StockUbicazione` rows.

`Articolo.scorta_minima` is a physical column (Integer, nullable, default 0). Used by the `articoli_sotto_scorta_minima` tool to identify items needing reorder (giacenza < scorta_minima).

### Entry Points
1. **Telegram Bot** (`erpclaw/bot.py`): Handles text and voice. Voice → Whisper transcription → agent. The `user_id` passed to the agent is the Telegram numeric user ID (as string).
2. **Web Admin + Shop** (`erpclaw/web.py`): FastAPI app with two sub-systems:
   - SQLAdmin CRUD at `/admin` for all ERP/logistics models.
   - Customer shop portal at `/shop` (register, login, search articles, cart, checkout, order history).

### Data Flow
```
Telegram message → bot.py → agent.py (agno Team + deepseek-reasoner)
  → ERPTools (erp_tools.py)        → SQLAlchemy session → erp.db
  → LogisticaTools (logistica_tools.py) → SQLAlchemy session → erp.db
  → delegates to fornitore_research_agent → FornitoreResearchTools / DuckDuckGoTools
```

The `team` object (agno `Team`) is the main entry point. It holds `ERPTools` + `LogisticaTools` and delegates to `fornitore_research_agent` for supplier web research.

### agno SDK Version
Always use the latest version of `agno`. The agno API changes frequently — when upgrading, verify that `Agent` and `Team` constructor parameters are still valid. The current architecture uses `Team` (not `Agent`) as the top-level entry point because `Agent` no longer accepts a `team` parameter (removed in agno ≥2.5.x in favor of the dedicated `Team` class).

### Key Files
- `erpclaw/config.py` — Loads `.env`; fails fast if variables are missing. Exports `SHOP_SECRET_KEY` with dev default.
- `erpclaw/erp_db.py` — SQLAlchemy models and `get_session()` / `init_db()`. `init_db()` is called at import time in both `erp_tools.py`, `logistica_tools.py`, and `web.py`. Also runs `_migrate()` to add missing columns to existing DBs (idempotent).
- `erpclaw/erp_tools.py` — `ERPTools(Toolkit)`: tools for articles, clients, orders, suppliers, and addresses. Includes category tools (`crea_categoria`, `lista_categorie`, `assegna_categoria`) and `articoli_sotto_scorta_minima` for reorder alerts. Tools return markdown strings.
- `erpclaw/logistica_tools.py` — `LogisticaTools(Toolkit)`: tools for warehouse locations (Magazzino→Zona→Scaffale→Ripiano), stock assignment/transfer, order discharge, and movement history.
- `erpclaw/fornitore_research_tools.py` — `FornitoreResearchTools(Toolkit)`: PDF catalog download (httpx), parsing (pdfplumber), DB management.
- `erpclaw/agent.py` — `team` (agno `Team`) + `fornitore_research_agent` sub-agent + `memory_manager`. The `Team` is the entry point; it holds `ERPTools` + `LogisticaTools`, `db`, memory, and delegates to `fornitore_research_agent`. Memory manager uses `deepseek-chat`; both team leader and sub-agent use `deepseek-reasoner`.
- `erpclaw/shop.py` — FastAPI `APIRouter(prefix="/shop")`: register/login/logout, article search (HTMX), cart (cookie JSON), checkout, order history. Auth via `itsdangerous` + `passlib[bcrypt]`.
- `erpclaw/templates/shop/` — Jinja2 templates: `base.html`, `register.html`, `login.html`, `search.html`, `orders.html`, `_risultati.html` (HTMX partial), `_carrello.html` (HTMX partial).

### Agent Memory
- `enable_agentic_memory=True` + `add_history_to_context=True` (last 5 runs) per user.
- Memory capture instructions are in Italian and collect user name/preferences.

### Order Status Lifecycle
`bozza` → `confermato` → `spedito` → `chiuso`

When an order is marked `spedito`, the agent should propose running `scarica_ordine_da_ubicazione` to discharge quantities from warehouse locations (LIFO strategy).

## Adding New ERP Tools

1. Add a method to `ERPTools` in `erpclaw/erp_tools.py` with a clear Italian docstring (the agent uses it to decide when to call the tool).
2. Register it with `self.register(self.method_name)` in `ERPTools.__init__`.
3. Methods must return `str` (markdown-formatted for Telegram display).
4. Use `get_session()` as a context manager (`with get_session() as s:`).

## Adding New Logistics Tools

1. Add a method to `LogisticaTools` in `erpclaw/logistica_tools.py` with a clear Italian docstring.
2. Register it with `self.register(self.method_name)` in `LogisticaTools.__init__`.
3. Methods must return `str` (markdown-formatted for Telegram display).
4. Add a mention in the team's `instructions` in `agent.py` so the LLM knows when to use it.

## Tests

```bash
uv run --no-sync python -m pytest tests/ -v
```

`pytest` is in `[optional-dependencies]` dev and not installed by default. Install once: `uv pip install pytest`.

Tests use SQLite in-memory databases (via `tests/conftest.py`) and `unittest.mock.patch` to redirect `get_session` calls. When patching `get_session` for tools tests, use `side_effect=make_session` where `make_session` returns a new `Session(engine)` per call.

## DB Session Pattern

`get_session()` returns a plain `Session`. Always use it as a context manager. After writing, call `s.commit()` before accessing generated IDs or relationships outside the `with` block.

**DetachedInstanceError:** After `s.commit()`, SQLAlchemy expires all ORM attributes (`expire_on_commit=True` default). Accessing them after the `with` block closes raises `DetachedInstanceError`. Rule: never use ORM objects outside `with get_session()`. Either `return` inside the `with`, or capture primitive values (str/float/int) as local variables before the block ends.

## Shop Portal

- Routes: `erpclaw/shop.py`, `APIRouter(prefix="/shop")`, mounted in `web.py`.
- Auth: `itsdangerous.URLSafeSerializer` for signed session cookies + `passlib[bcrypt]` for password hashing.
- Cart: stored in a plain JSON cookie (`shop_cart`).
- **bcrypt constraint:** `passlib[bcrypt]>=1.7.4` requires `bcrypt<5.0.0` — bcrypt 5+ broke the passlib API. Pinned in `pyproject.toml`.
- Order numbering: `WEB-YYYYMMDD-NNNN` (distinct from agent orders `ORD-NNNN`).

## pyproject.toml Notes

- `tool.uv.package = true` is required for the `erpclaw` entry point script to be installed by `uv sync`.
- `requires-python = ">=3.13"` and `.python-version = 3.13` pin away from a broken uv-managed CPython 3.12 distribution.
