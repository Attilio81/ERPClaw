# ERPClaw

Mini-ERP gestito da un agente AI tramite **Telegram**. Scrivi (o parla) in italiano — il sistema capisce e agisce.

---

## Come funziona

L'utente manda un messaggio su Telegram, anche vocale. L'agente AI (DeepSeek via [agno](https://github.com/agno-agi/agno)) interpreta la richiesta ed esegue le operazioni sul database aziendale SQLite.

```
Telegram → bot.py → agno Team (DeepSeek) → ERPTools → erp.db
                                          ↘ FornitoreResearchAgent → web search / PDF
```

## Funzionalità

- **Magazzino** — lista articoli, giacenze, aggiornamenti quantità
- **Fornitori** — ricerca web, salvataggio anagrafica, download cataloghi PDF
- **Importazione cataloghi** — parsing PDF, ricerca prezzi online, inserimento articoli con margine personalizzabile
- **Clienti** — anagrafica completa
- **Ordini** — creazione, gestione stati (`bozza → confermato → spedito → chiuso`)
- **Messaggi vocali** — trascrizione automatica via OpenAI Whisper
- **Pannello web** — admin CRUD su browser (FastAPI + SQLAdmin)
- **Memoria** — l'agente ricorda preferenze e contesto per ogni utente Telegram

## Stack tecnico

| Componente | Tecnologia |
|---|---|
| LLM agente | DeepSeek (`deepseek-reasoner`) |
| Framework agente | [agno](https://github.com/agno-agi/agno) |
| Trascrizione voce | OpenAI Whisper |
| Database ERP | SQLite + SQLAlchemy |
| Bot Telegram | python-telegram-bot |
| Pannello web | FastAPI + SQLAdmin |
| Package manager | [uv](https://github.com/astral-sh/uv) |
| Python | 3.13 |

## Requisiti

- Python 3.13
- [uv](https://github.com/astral-sh/uv)
- Token bot Telegram
- API key DeepSeek
- API key OpenAI (solo per i messaggi vocali)

## Installazione

```bash
git clone https://github.com/Attilio81/ERPClaw.git
cd ERPClaw

# Crea il file .env
cp .env.example .env   # poi compila le variabili

# Installa le dipendenze
uv sync
```

File `.env` richiesto:
```
TELEGRAM_BOT_TOKEN=...
DEEPSEEK_API_KEY=...
OPENAI_API_KEY=...
```

## Avvio

```bash
# Avvia solo il bot Telegram
uv run erpclaw

# Avvia solo il pannello web
uv run uvicorn erpclaw.web:app --reload
# → http://localhost:8000/admin

# Avvia entrambi (Windows)
start.bat
```

## Esempio d'uso

```
Utente: mi cerchi il fornitore monge? ha dei cataloghi?

ERPClaw: Ecco i risultati della ricerca online per Monge & C. S.p.A.
         Sede: Monasterolo di Savigliano (CN) | Fatturato: €512M
         ✅ Catalogo PDF disponibile. Vuoi salvarlo nel database?

Utente: sì salvami questo fornitore

ERPClaw: Fornitore salvato! Codice: MONGE | Sito: https://www.monge.it
         Vuoi che scarichi il catalogo e inserisca i primi articoli?

Utente: sì, scarica il catalogo e inserisci i primi 10 articoli

ERPClaw: Ho trovato 10 articoli. I prezzi non sono nel PDF —
         vuoi che li cerchi sui principali e-commerce italiani?

Utente: sì

ERPClaw: Prezzi trovati su Trovaprezzi, Idealo, Zooplus.
         Inserisco con +20% di margine?

Utente: procedi con opzione 2

ERPClaw: ✅ 10 articoli inseriti nel catalogo con prezzi +20%.
```

## Struttura del progetto

```
erpclaw/
├── agent.py                    # agno Team + sub-agente ricerca fornitori
├── bot.py                      # bot Telegram (testo + voce)
├── web.py                      # pannello admin FastAPI
├── erp_db.py                   # modelli SQLAlchemy + init DB
├── erp_tools.py                # tool ERP dell'agente
├── fornitore_research_tools.py # tool ricerca fornitori (PDF, web)
└── config.py                   # caricamento .env

esempi di chat/                 # export chat Telegram di esempio
MANUALE_UTENTE.md               # manuale non tecnico per l'utente finale
```

## Aggiungere nuovi tool

1. Aggiungi un metodo a `ERPTools` in `erp_tools.py` con docstring in italiano
2. Registralo con `self.register(self.nome_metodo)` in `__init__`
3. Il metodo deve restituire una stringa markdown

## Licenza

MIT
