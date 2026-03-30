# Config Panel — Design Spec

**Data:** 2026-03-29
**Stato:** Approvato

## Obiettivo

Pannello web per modificare il file `.env` senza aprirlo manualmente. Accessibile su `/config`, senza autenticazione (rete locale assumita privata). Le modifiche prendono effetto al riavvio dell'app.

## Architettura

### Nuovi file
- `erpclaw/config_panel.py` — `APIRouter(prefix="/config")` con due route
- `erpclaw/templates/config/panel.html` — form HTML Jinja2

### Modifica a file esistenti
- `erpclaw/web.py` — aggiunge `app.include_router(config_router)`

### Route
| Metodo | Path | Descrizione |
|--------|------|-------------|
| `GET` | `/config` | Legge `.env`, renderizza il form |
| `POST` | `/config` | Riceve form, aggiorna `.env`, redirect GET con flash message |

### Parsing `.env`
Nessuna libreria nuova. Il file viene letto riga per riga:
- Righe `KEY=VALUE` vengono aggiornate con i nuovi valori
- Commenti (`# ...`) e righe vuote vengono preservati invariati
- Ordine delle righe preservato

## UI

### Controllo principale: toggle LLM Provider
Switch visibile (radio button stile toggle) con due opzioni:

```
[ LM Studio (locale) ]   [ DeepSeek (cloud) ]
```

- Selezione **LM Studio** → mostra `LLM_MODEL_ID`, `LMSTUDIO_BASE_URL`; nasconde `DEEPSEEK_API_KEY`
- Selezione **DeepSeek** → mostra `LLM_MODEL_ID`, `DEEPSEEK_API_KEY`; nasconde `LMSTUDIO_BASE_URL`
- Comportamento gestito con JavaScript puro (nessuna dipendenza aggiuntiva)
- `LLM_PROVIDER` viene impostato automaticamente in base alla selezione

### Gruppi di campi

| Gruppo | Variabile | Tipo input |
|--------|-----------|------------|
| **Telegram** | `TELEGRAM_BOT_TOKEN` | password + toggle visibilità |
| **Telegram** | `ALLOWED_CHAT_ID` | password + toggle visibilità |
| **AI / LLM** | `LLM_PROVIDER` | hidden (settato dal toggle) |
| **AI / LLM** | `LLM_MODEL_ID` | text |
| **AI / LLM** | `LMSTUDIO_BASE_URL` | text (visibile solo con LM Studio) |
| **API Keys** | `OPENAI_API_KEY` | password + toggle visibilità |
| **API Keys** | `DEEPSEEK_API_KEY` | password + toggle visibilità (visibile solo con DeepSeek) |
| **Shop** | `SHOP_SECRET_KEY` | password + toggle visibilità |

### Feedback
- Pulsante **Salva** in fondo al form
- Banner verde di conferma dopo salvataggio riuscito
- Banner rosso in caso di errore (es. file `.env` non scrivibile)
- Avviso informativo: "Le modifiche avranno effetto al prossimo riavvio del bot"

### Stile
Coerente con il dashboard agenti: Bootstrap, stessa navbar/layout.

## Comportamento edge case
- Se una variabile non esiste nel `.env` (es. `DEEPSEEK_API_KEY` commentata), viene aggiunta come nuova riga al fondo del file quando valorizzata
- Valori vuoti lasciati vuoti nel form → la riga rimane nel `.env` con valore vuoto (`KEY=`)
- Il file `.env` originale non viene mai cancellato; viene riscritto in-place preservando i commenti
