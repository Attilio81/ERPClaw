# DDT e Fatture — Design Spec
_ERPClaw · 2026-03-16_

## Obiettivo

Introdurre la gestione di **DDT (Documento di Trasporto)** e **Fatture** nel sistema ERPClaw, con:
- Tracciamento in database
- Generazione PDF salvati su disco
- Accesso tramite agente Telegram e pannello web `/admin`

---

## Vincoli e decisioni chiave

| Tema | Decisione |
|------|-----------|
| Relazione DDT/Fattura | Separati e indipendenti; fattura differita può coprire più DDT |
| IVA | Aliquota per articolo (`aliquota_iva` su `Articolo`, default 0.22) |
| PDF | Generati on-demand + salvati su disco; scaricabili da `/admin` |
| Agente | Crea e consulta via Telegram; download PDF solo da web |
| Libreria PDF | `fpdf2` (puro Python, leggero) |
| DDT per ordine | Un solo DDT per ordine (`UniqueConstraint` su `ddt.ordine_id`) |
| `crea_fattura` parametro DDT | `numeri_ddt: str` (stringa separata da virgola) per compatibilità LM Studio |
| Percorsi PDF | Assoluti al momento del salvataggio (`Path(__file__).parent.parent / "documenti"`) |

---

## 1. Modelli dati

### 1.1 Modifica a `erp_db.py`

Aggiunta colonna `aliquota_iva` alla tabella `articoli` via `_migrate()` (idempotente):
```python
("articoli", "aliquota_iva", "REAL DEFAULT 0.22")
```
Il valore `DEFAULT 0.22` nel DDL SQL garantisce che le righe esistenti abbiano l'aliquota standard anziché `NULL`.

Aggiunto anche campo `aliquota_iva = Column(Float, nullable=False, default=0.22)` al modello `Articolo`.

### 1.2 Nuovi modelli in `erpclaw/documenti_db.py`

Usa la stessa `erp.db` importando `engine` e `Base` da `erp_db.py` (non una nuova `Base`). Questo garantisce che `Base.metadata.create_all()` in `erp_db.init_db()` crei anche le tabelle DDT/Fattura.

Una funzione `init_documenti_db()` viene chiamata all'import di `documenti_tools.py`, analogamente al pattern `init_db()` in `erp_tools.py`.

#### Enumerazioni
```python
class StatoDDT(str, enum.Enum):
    bozza = "bozza"
    emesso = "emesso"

class StatoFattura(str, enum.Enum):
    bozza = "bozza"
    emessa = "emessa"
    pagata = "pagata"
```

#### `DDT`
```
tabella: ddt
- id (PK)
- numero: String unique (es. DDT-20260316-001)
- data: Date
- ordine_id: FK → ordini (nullable=False, UniqueConstraint → un DDT per ordine)
- stato: Enum(StatoDDT), default bozza
- note: Text
- percorso_pdf: String nullable
```

**Nota:** il contenuto del DDT (righe merci) viene letto live dall'ordine di riferimento (`ordine.righe`). Non esiste un modello `RigaDDT` — questa è una scelta deliberata per semplicità. Se l'ordine viene modificato dopo la creazione del DDT, il contenuto riflette le righe correnti. Questo è accettabile poiché il DDT viene emesso (`emesso`) subito dopo la creazione e gli ordini `spedito` non vengono modificati nel flusso normale.

#### `Fattura`
```
tabella: fatture
- id (PK)
- numero: String unique (es. FT-2026-0001)
- data: Date
- cliente_id: FK → clienti (nullable=False)
- stato: Enum(StatoFattura), default bozza
- note: Text
- percorso_pdf: String nullable
```

#### `RigaFattura`
```
tabella: righe_fattura
- id (PK)
- fattura_id: FK → fatture
- articolo_id: FK → articoli
- quantita: Integer
- prezzo_unitario: Float
- aliquota_iva: Float  ← snapshot al momento della creazione fattura
```

#### Tabella associazione `fatture_ddt`
```
- fattura_id: FK → fatture
- ddt_id: FK → ddt
- PK composta (fattura_id, ddt_id)
```

### 1.3 Algoritmo `crea_fattura` — copia righe

Per ciascun DDT incluso nella fattura:
1. Legge `ordine.righe` tramite `ddt.ordine`
2. Per ogni `RigaOrdine`, crea una `RigaFattura` con snapshot di `prezzo_unitario` e `aliquota_iva` dell'articolo al momento della creazione
3. Se lo stesso articolo appare in più DDT inclusi nella stessa fattura, vengono create righe separate (una per DDT), così la fattura differita mantiene la tracciabilità DDT per DDT

### 1.4 Cicli di vita

- **DDT:** `bozza → emesso`
- **Fattura:** `bozza → emessa → pagata`

---

## 2. Tool agente (`erpclaw/documenti_tools.py`)

Nuovo `DocumentiTools(Toolkit)` registrato nel `Team` in `agent.py`.

| Tool | Firma | Note |
|------|-------|------|
| `crea_ddt` | `(numero_ordine: str) → str` | Ordine deve essere in stato `spedito`; errore se DDT già esistente per quell'ordine |
| `emetti_ddt` | `(numero_ddt: str) → str` | Stato bozza→emesso, genera PDF |
| `lista_ddt` | `(stato: str = None) → str` | Filtra per stato opzionale |
| `dettaglio_ddt` | `(numero_ddt: str) → str` | Righe lette live dall'ordine di riferimento |
| `crea_fattura` | `(numeri_ddt: str, note: str = "") → str` | `numeri_ddt` è una stringa separata da virgole (es. `"DDT-20260316-001,DDT-20260316-002"`); compatibile con LM Studio |
| `emetti_fattura` | `(numero_fattura: str) → str` | Valida che ci siano righe; stato bozza→emessa, genera PDF |
| `segna_fattura_pagata` | `(numero_fattura: str) → str` | Stato emessa→pagata |
| `lista_fatture` | `(stato: str = None) → str` | Filtra per stato opzionale |
| `dettaglio_fattura` | `(numero_fattura: str) → str` | Righe + riepilogo IVA per aliquota + totali |

### Numerazione automatica
- DDT: `DDT-YYYYMMDD-NNN` (progressivo per data, basato su `COUNT` delle DDT nella data odierna + 1)
- Fattura: `FT-YYYY-NNNN` (progressivo per anno, basato su `COUNT` delle fatture nell'anno + 1)
- Nota: SQLite serializza le scritture, quindi la race condition sul numeratore è bassa in questo contesto mono-processo.

### Validazioni e casi d'errore

| Caso | Comportamento |
|------|--------------|
| `crea_ddt` su ordine non `spedito` | Errore con stato corrente |
| `crea_ddt` su ordine già con DDT | Errore: DDT già esistente |
| `crea_fattura` con DDT non trovato | Errore con numero DDT non valido |
| `emetti_fattura` con zero righe | Errore: nessuna riga da fatturare |
| `segna_fattura_pagata` su fattura non `emessa` | Errore con stato corrente |

---

## 3. Generazione PDF (`erpclaw/documenti_pdf.py`)

### Libreria
`fpdf2` — aggiunta a `pyproject.toml` come dipendenza diretta.

### Template DDT
- Header: dati emittente (da `.env`), dati cliente, indirizzo di spedizione (da `Indirizzo(tipo=spedizione)` o fallback a `sede_legale`)
- Tabella merci: codice, descrizione, quantità
- Piè di pagina: riferimento ordine, note, spazio firma autista

### Template Fattura
- Header: dati emittente, dati cliente con indirizzo di fatturazione (da `Indirizzo(tipo=fatturazione)` se presente, altrimenti `sede_legale`), numero e data fattura
- Lista DDT di riferimento
- Tabella righe: codice, descrizione, qtà, prezzo unitario, aliquota IVA %, subtotale imponibile
- Riepilogo IVA raggruppato per aliquota (imponibile → IVA → subtotale per aliquota)
- Totale imponibile | Totale IVA | **Totale documento**

### Percorsi file
I percorsi vengono calcolati con path assoluti al momento del salvataggio:
```python
BASE_DOCUMENTI = Path(__file__).parent.parent / "documenti"
DDT_DIR = BASE_DOCUMENTI / "ddt"
FATTURE_DIR = BASE_DOCUMENTI / "fatture"
```
Questo garantisce la coerenza indipendentemente dalla directory di lavoro del processo (bot vs. server web).

Directory create con `mkdir(parents=True, exist_ok=True)` alla prima generazione.

### Dati emittente (`.env`, tutti opzionali)
```
AZIENDA_NOME=
AZIENDA_INDIRIZZO=
AZIENDA_PIVA=
```
Se assenti, il PDF mostra placeholder `[Da configurare]`.

---

## 4. Integrazione web

### 4.1 SQLAdmin (`web.py`)
Aggiunta di due ModelView:
- `DDTAdmin` — colonne: numero, data, ordine, stato; link scarica PDF
- `FatturaAdmin` — colonne: numero, data, cliente, stato; link scarica PDF

### 4.2 Router FastAPI (`erpclaw/documenti_web.py`)

```
GET /documenti/ddt/{numero}/pdf      → FileResponse (404 se percorso_pdf è None o file non trovato)
GET /documenti/fatture/{numero}/pdf  → FileResponse (404 se percorso_pdf è None o file non trovato)
```

Montato in `web.py` insieme a `shop_router`.

---

## 5. Modifiche ai file esistenti

| File | Modifica |
|------|---------|
| `erpclaw/erp_db.py` | Aggiunta `aliquota_iva` al modello `Articolo` e a `_migrate()` con `REAL DEFAULT 0.22` |
| `erpclaw/agent.py` | Import e registrazione `DocumentiTools` nel `Team` |
| `erpclaw/web.py` | Aggiunta SQLAdmin views + mount router `/documenti` |
| `pyproject.toml` | Aggiunta dipendenza `fpdf2` |
| `.env` / `.env.example` | Aggiunta variabili `AZIENDA_*` |
| `CLAUDE.md` | Aggiornamento architettura, tabelle, e sezione nuovi tool |

---

## 6. File nuovi

| File | Responsabilità |
|------|---------------|
| `erpclaw/documenti_db.py` | Modelli `DDT`, `Fattura`, `RigaFattura`, tabella `fatture_ddt`, enumerazioni stato, `init_documenti_db()` |
| `erpclaw/documenti_tools.py` | `DocumentiTools(Toolkit)` per l'agente |
| `erpclaw/documenti_pdf.py` | Generazione PDF con `fpdf2`, calcolo percorsi assoluti |
| `erpclaw/documenti_web.py` | Router FastAPI per download PDF |

---

## 7. Out of scope

- Invio fattura via email
- Firma digitale PDF
- Integrazione SDI (Sistema di Interscambio) per fatturazione elettronica
- P.IVA/CF sui clienti (campo non ancora presente in `Cliente`)
- Gestione note di credito
