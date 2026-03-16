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

---

## 1. Modelli dati

### 1.1 Modifica a `erp_db.py`

Aggiunta colonna `aliquota_iva` (Float, default `0.22`) alla tabella `articoli` via `_migrate()` (idempotente).

### 1.2 Nuovi modelli in `erpclaw/documenti_db.py`

Stessa `erp.db`, stessa istanza di engine importata da `erp_db.py`.

#### `DDT`
```
tabella: ddt
- id (PK)
- numero: String unique (es. DDT-20260316-001)
- data: Date
- ordine_id: FK → ordini (nullable=False)
- stato: Enum("bozza", "emesso")
- note: Text
- percorso_pdf: String nullable
```

#### `Fattura`
```
tabella: fatture
- id (PK)
- numero: String unique (es. FT-2026-0001)
- data: Date
- cliente_id: FK → clienti (nullable=False)
- stato: Enum("bozza", "emessa", "pagata")
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
- aliquota_iva: Float  ← snapshot al momento dell'emissione
```

#### Tabella associazione `fatture_ddt`
```
- fattura_id: FK → fatture
- ddt_id: FK → ddt
- PK composta (fattura_id, ddt_id)
```

### 1.3 Cicli di vita

- **DDT:** `bozza → emesso`
- **Fattura:** `bozza → emessa → pagata`

---

## 2. Tool agente (`erpclaw/documenti_tools.py`)

Nuovo `DocumentiTools(Toolkit)` registrato nel `Team` in `agent.py`.

| Tool | Firma | Note |
|------|-------|------|
| `crea_ddt` | `(numero_ordine: str) → str` | Ordine deve essere in stato `spedito` |
| `emetti_ddt` | `(numero_ddt: str) → str` | Stato bozza→emesso, genera PDF |
| `lista_ddt` | `(stato: str = None) → str` | Filtra per stato opzionale |
| `dettaglio_ddt` | `(numero_ddt: str) → str` | Righe da ordine di riferimento |
| `crea_fattura` | `(numeri_ddt: list[str], note: str = "") → str` | Copia righe con snapshot IVA |
| `emetti_fattura` | `(numero_fattura: str) → str` | Stato bozza→emessa, genera PDF |
| `segna_fattura_pagata` | `(numero_fattura: str) → str` | Stato emessa→pagata |
| `lista_fatture` | `(stato: str = None) → str` | Filtra per stato opzionale |
| `dettaglio_fattura` | `(numero_fattura: str) → str` | Righe + riepilogo IVA per aliquota + totali |

### Numerazione automatica
- DDT: `DDT-YYYYMMDD-NNN` (progressivo per data)
- Fattura: `FT-YYYY-NNNN` (progressivo per anno)

---

## 3. Generazione PDF (`erpclaw/documenti_pdf.py`)

### Libreria
`fpdf2` — aggiunta a `pyproject.toml` come dipendenza diretta.

### Template DDT
- Header: dati emittente (da `.env`), dati cliente, indirizzo spedizione
- Tabella merci: codice, descrizione, quantità
- Piè di pagina: riferimento ordine, note, spazio firma

### Template Fattura
- Header: dati emittente, dati cliente (P.IVA/CF se disponibili), numero e data
- Lista DDT di riferimento
- Tabella righe: codice, descrizione, qtà, prezzo unitario, aliquota IVA %, subtotale
- Riepilogo IVA per aliquota (imponibile → IVA)
- Totale imponibile | Totale IVA | **Totale documento**

### Percorsi file
```
./documenti/ddt/DDT-YYYYMMDD-NNN.pdf
./documenti/fatture/FT-YYYY-NNNN.pdf
```
Directory create automaticamente (`mkdir -p`) alla prima generazione.

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
- `DDTAdmin` — colonne: numero, data, ordine, stato; action download PDF
- `FatturaAdmin` — colonne: numero, data, cliente, stato; action download PDF

### 4.2 Router FastAPI (`erpclaw/documenti_web.py`)

```
GET /documenti/ddt/{numero}/pdf      → FileResponse (404 se percorso_pdf è None)
GET /documenti/fatture/{numero}/pdf  → FileResponse (404 se percorso_pdf è None)
```

Montato in `web.py` insieme a `shop_router`.

---

## 5. Modifiche ai file esistenti

| File | Modifica |
|------|---------|
| `erpclaw/erp_db.py` | Aggiunta `aliquota_iva` a `_migrate()` e al modello `Articolo` |
| `erpclaw/agent.py` | Import e registrazione `DocumentiTools` nel `Team` |
| `erpclaw/web.py` | Aggiunta SQLAdmin views + mount router `/documenti` |
| `pyproject.toml` | Aggiunta dipendenza `fpdf2` |
| `.env` / `.env.example` | Aggiunta variabili `AZIENDA_*` |
| `CLAUDE.md` | Aggiornamento architettura e tabelle |

---

## 6. File nuovi

| File | Responsabilità |
|------|---------------|
| `erpclaw/documenti_db.py` | Modelli `DDT`, `Fattura`, `RigaFattura`, tabella associazione |
| `erpclaw/documenti_tools.py` | `DocumentiTools(Toolkit)` per l'agente |
| `erpclaw/documenti_pdf.py` | Generazione PDF con `fpdf2` |
| `erpclaw/documenti_web.py` | Router FastAPI per download PDF |

---

## 7. Out of scope

- Invio fattura via email
- Firma digitale PDF
- Integrazione SDI (Sistema di Interscambio) per fatturazione elettronica
- P.IVA/CF sui clienti (campo non ancora presente in `Cliente`)
