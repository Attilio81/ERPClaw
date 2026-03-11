# ERPClaw S.r.l. — Organigramma Aziendale

> *Ogni ruolo è ricoperto da un agente AI. L'azienda non dorme mai, non va in ferie e non chiede aumenti.*

---

## Struttura Organizzativa

```mermaid
graph TD
    OWNER["📱 **Titolare**
    —
    Telegram
    —
    Proprietario dell'azienda.
    Impartisce ordini in italiano,
    anche dal telefono e a voce.
    Non conosce SQL."]

    CEO["🧠 **Direttore Generale**
    —
    Team Leader
    (agno Team · deepseek-reasoner)
    —
    Coordina tutte le operazioni.
    Riceve le richieste, decide chi
    deve fare cosa e supervisiona
    l'esecuzione."]

    SEC["🗂️ **Assistente di Direzione**
    —
    Memory Manager
    (deepseek-chat)
    —
    Ricorda preferenze, nomi e
    contesto di ogni utente.
    Aggiorna il taccuino dopo
    ogni conversazione."]

    FRONT1["🌐 **Addetta Portale Clienti**
    —
    Shop Portal
    (FastAPI · HTMX)
    —
    Accoglie i clienti sul web,
    gestisce registrazione, login,
    carrello e checkout."]

    ADMIN["🖥️ **Responsabile Back Office**
    —
    Pannello Admin
    (SQLAdmin)
    —
    Vista tabellare su tutti i dati.
    Modifiche manuali dirette
    al database quando serve."]

    ERP["📋 **Responsabile Commerciale**
    —
    ERPTools
    —
    Gestisce articoli (prezzi duali),
    clienti, ordini di vendita,
    fornitori, categorie e
    ordini di acquisto."]

    LOG["📦 **Responsabile Magazzino**
    —
    LogisticaTools
    —
    Gestisce la struttura fisica
    (Magazzino→Zona→Scaffale→Ripiano),
    stock per ubicazione, carico,
    scarico e trasferimenti."]

    RIC["🔍 **Agente Ricerca Fornitori**
    —
    FornitoreResearchAgent
    (deepseek-reasoner)
    —
    Sub-agente specializzato.
    Cerca fornitori sul web,
    scarica e analizza i
    cataloghi PDF."]

    PDF["📄 **Archivista Cataloghi**
    —
    FornitoreResearchTools
    (httpx · pdfplumber)
    —
    Scarica i PDF, li legge,
    estrae gli articoli e
    li salva nel database."]

    WEB["🌍 **Navigatore Web**
    —
    DuckDuckGoTools
    —
    Esegue le ricerche online
    per trovare fornitori,
    prezzi e informazioni
    di mercato."]

    DB1["🗄️ **Archivio Aziendale**
    —
    erp.db
    (SQLite)
    —
    Custodisce tutti i dati:
    articoli, clienti, ordini,
    fornitori, magazzino."]

    DB2["🧠 **Archivio Memorie**
    —
    agent.db
    (SQLite · agno)
    —
    Conversazioni e preferenze
    per utente Telegram."]

    %% Gerarchia
    OWNER --> FRONT1
    OWNER --> FRONT2
    FRONT1 --> CEO
    FRONT2 --> CEO
    CEO --> SEC
    CEO --> ERP
    CEO --> LOG
    CEO --> RIC
    CEO --> ADMIN

    RIC --> PDF
    RIC --> WEB

    %% Accesso ai dati
    ERP -.-> DB1
    LOG -.-> DB1
    PDF -.-> DB1
    FRONT2 -.-> DB1
    ADMIN -.-> DB1
    SEC -.-> DB2
```

---

## Chi fa cosa

| Persona | Ruolo | Strumento |
|---------|-------|-----------|
| 🧠 Direttore Generale | Coordina, delega, risponde all'utente | `agent.py` — agno `Team` |
| 🗂️ Assistente di Direzione | Memoria utenti, preferenze, contesto | `agent.py` — `memory_manager` |
| 📱 Receptionist Telegram | Ingresso messaggi testo e vocali | `bot.py` |
| 🌐 Addetta Portale Clienti | Shop web per ordini clienti autonomi | `shop.py` |
| 🖥️ Responsabile Back Office | Admin CRUD da browser | `web.py` — SQLAdmin |
| 📋 Responsabile Commerciale | Articoli, clienti, ordini, fornitori | `erp_tools.py` — `ERPTools` |
| 📦 Responsabile Magazzino | Ubicazioni, stock, movimenti | `logistica_tools.py` — `LogisticaTools` |
| 🔍 Agente Ricerca Fornitori | Sub-agente web research | `agent.py` — `fornitore_research_agent` |
| 📄 Archivista Cataloghi | Download PDF, parsing, inserimento | `fornitore_research_tools.py` |
| 🌍 Navigatore Web | Ricerche DuckDuckGo | agno `DuckDuckGoTools` |
| 🗄️ Archivio Aziendale | Tutti i dati ERP | `erp.db` |
| 🧠 Archivio Memorie | Storia conversazioni per utente | `agent.db` |

---

## Flusso di una richiesta tipica

```
Utente Telegram
    │
    ▼
📱 Receptionist (bot.py)
    │  trascrisce se vocale (Whisper)
    ▼
🧠 Direttore Generale (Team Leader)
    │  consulta la memoria con l'Assistente
    │
    ├─── operazione commerciale ──▶ 📋 Resp. Commerciale (ERPTools)
    │                                        │
    ├─── operazione magazzino ───▶ 📦 Resp. Magazzino (LogisticaTools)
    │                                        │
    └─── ricerca fornitore ──────▶ 🔍 Agente Ricerca
                                        ├─▶ 🌍 Navigatore Web
                                        └─▶ 📄 Archivista Cataloghi
                                                     │
                                              tutte ──▶ 🗄️ erp.db
```
