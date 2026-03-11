# Design: Prezzi Articolo e Ordini Fornitori

**Data:** 2026-03-10
**Stato:** Approvato

## Obiettivo

Aggiungere `prezzo_acquisto` e `prezzo_vendita` agli articoli, e implementare il workflow ordini fornitore (bozza → inviato → ricevuto) con carico magazzino gestito dall'agente.

## Modello Dati

### Modifiche a `Articolo`
- `prezzo` rinominato → `prezzo_vendita` (Float, not null)
- Aggiunto `prezzo_acquisto` (Float, nullable)
- La colonna `prezzo` viene deprecata ma non eliminata fisicamente (sicurezza migrazione)

### Nuove tabelle

#### `ordini_fornitori`
| Campo | Tipo | Note |
|-------|------|-------|
| id | Integer PK | |
| numero | String UNIQUE | Formato ORF-0001 |
| data | Date | default oggi |
| fornitore_id | FK fornitori.id | not null |
| stato | Enum | bozza, inviato, ricevuto |
| note | Text | nullable |

#### `righe_ordini_fornitori`
| Campo | Tipo | Note |
|-------|------|-------|
| id | Integer PK | |
| ordine_fornitore_id | FK ordini_fornitori.id | cascade delete |
| articolo_id | FK articoli.id | not null |
| quantita | Integer | not null |
| prezzo_unitario | Float | not null |

### Relazioni
- `OrdineFornitore` → `Fornitore` (many-to-one)
- `OrdineFornitore` → `[RigaOrdineFornitore]` (one-to-many, cascade delete)
- `RigaOrdineFornitore` → `Articolo` (many-to-one)

## Tool dell'Agente

### Tool aggiornati
| Tool | Modifica |
|------|---------|
| `crea_articolo` | Parametro `prezzo` → `prezzo_vendita`; aggiunto `prezzo_acquisto=None` |
| `aggiorna_articolo` | Parametro `prezzo` → `prezzo_vendita`; aggiunto `prezzo_acquisto=None` |
| `lista_articoli` | Mostra entrambi i prezzi |
| `cerca_articolo` | Mostra entrambi i prezzi |
| `aggiungi_riga` | Usa `articolo.prezzo_vendita` come `prezzo_unitario` |

### Nuovi tool in `ERPTools`
| Tool | Descrizione |
|------|-------------|
| `crea_ordine_fornitore(fornitore_codice, note=None)` | Crea ordine bozza, genera numero ORF-NNNN |
| `aggiungi_riga_ordine_fornitore(numero_ordine, codice_articolo, quantita, prezzo_unitario=None)` | Aggiunge riga; se prezzo_unitario omesso usa prezzo_acquisto dell'articolo |
| `lista_ordini_fornitori(stato=None)` | Lista ordini, filtro opzionale per stato |
| `visualizza_ordine_fornitore(numero_ordine)` | Dettaglio righe + totale |
| `avanza_stato_ordine_fornitore(numero_ordine)` | Transizione bozza→inviato→ricevuto |

### Workflow post-ricezione
Quando l'ordine diventa `ricevuto`, l'agente usa i tool di logistica esistenti (`carica_magazzino`, `assegna_stock`) per posizionare la merce nelle ubicazioni di magazzino.

## Migrazione DB

Pattern `_migrate()` già in uso in `erp_db.py`:
1. Aggiunge colonna `articoli.prezzo_vendita` copiando da `prezzo` (se esiste)
2. Aggiunge colonna `articoli.prezzo_acquisto` (nullable, default NULL)
3. Crea tabelle `ordini_fornitori` e `righe_ordini_fornitori` con `CREATE TABLE IF NOT EXISTS`
4. La colonna `articoli.prezzo` rimane ma viene ignorata dal codice

## Admin Panel e Shop

- `ArticoloAdmin` in `web.py`: mostra `prezzo_vendita` e `prezzo_acquisto`
- Nuove viste SQLAdmin: `OrdineFornitoreAdmin`, `RigaOrdineFornitoreAdmin`
- Shop portal (`shop.py` + template): `a.prezzo` → `a.prezzo_vendita`

## Test

- TDD: test scritti prima dell'implementazione
- File: `tests/test_ordini_fornitori.py`
- Copertura: `crea_ordine_fornitore`, `aggiungi_riga_ordine_fornitore`, `avanza_stato_ordine_fornitore`, `crea_articolo` con doppio prezzo
- Pattern: SQLite in-memory + `patch('erpclaw.erp_tools.get_session', side_effect=make_session)`
