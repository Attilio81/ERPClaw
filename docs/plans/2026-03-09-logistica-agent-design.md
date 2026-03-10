# Design: Agente Logistica e Gestione Ubicazioni

**Data:** 2026-03-09
**Stato:** Approvato

---

## Obiettivo

Introdurre un agente logistico che gestisce il posizionamento fisico degli articoli in magazzino tramite ubicazioni gerarchiche, traccia ogni movimento (carico, scarico, trasferimento) e si integra con il ciclo di vita degli ordini. Estende inoltre l'anagrafica di clienti e fornitori con indirizzi multi-tipo.

---

## Modello Dati

### Gerarchia Ubicazioni (in `erp.db`)

```
Magazzino → Zona → Scaffale → Ripiano
```

| Tabella     | Campi principali                          |
|-------------|-------------------------------------------|
| `magazzini` | `id`, `codice` (unique), `nome`           |
| `zone`      | `id`, `codice` (unique), `nome`, `magazzino_id` (FK) |
| `scaffali`  | `id`, `codice` (unique), `nome`, `zona_id` (FK) |
| `ripiani`   | `id`, `codice` (unique), `nome`, `scaffale_id` (FK) |

### Stock per Ubicazione

```
StockUbicazione
────────────────────────────────────────
id (PK)
articolo_id    FK → articoli
ripiano_id     FK → ripiani
quantita       Integer >= 0
UNIQUE(articolo_id, ripiano_id)
```

### Movimenti di Magazzino

```
MovimentoMagazzino
────────────────────────────────────────
id (PK)
articolo_id              FK → articoli
ripiano_origine_id       FK → ripiani (nullable)
ripiano_destinazione_id  FK → ripiani (nullable)
quantita                 Integer > 0
tipo                     ENUM: carico | scarico | trasferimento
data_ora                 DateTime (default: now)
ordine_id                FK → ordini (nullable)
note                     Text (nullable)
```

### Indirizzi (clienti e fornitori)

```
Indirizzo
────────────────────────────────────────
id (PK)
tipo         ENUM: sede_legale | spedizione | fatturazione | altro
via
cap
citta
provincia
paese        String (default: "IT")
note         Text (nullable)
cliente_id   FK → clienti (nullable)
fornitore_id FK → fornitori (nullable)
```

### Modifica a `Articolo.giacenza`

`giacenza` diventa una `column_property` SQLAlchemy che somma `StockUbicazione.quantita` per quell'articolo. Non viene più scritto direttamente — è sempre derivato dallo stock nelle ubicazioni.

---

## Strumenti Agente

### `LogisticaTools(Toolkit)` — nuovo file `erpclaw/logistica_tools.py`

**Anagrafica ubicazioni:**
- `crea_magazzino(codice, nome)`
- `crea_zona(codice, nome, codice_magazzino)`
- `crea_scaffale(codice, nome, codice_zona)`
- `crea_ripiano(codice, nome, codice_scaffale)`
- `lista_ubicazioni(codice_magazzino=None)` — albero gerarchico in markdown

**Gestione stock:**
- `assegna_stock(codice_articolo, codice_ripiano, quantita)` — carico iniziale, genera `MovimentoMagazzino` tipo `carico`
- `trasferisci_stock(codice_articolo, codice_ripiano_origine, codice_ripiano_dest, quantita)` — genera movimento `trasferimento`
- `stock_per_articolo(codice_articolo)` — tutte le ubicazioni con quantità
- `stock_per_ubicazione(codice_ripiano)` — tutti gli articoli in una ubicazione
- `articoli_senza_ubicazione()` — articoli con giacenza > 0 ma nessuna StockUbicazione

**Integrazione ordini:**
- `scarica_ordine_da_ubicazione(numero_ordine)` — genera movimenti `scarico` per ogni riga ordine; strategia LIFO sulle ubicazioni; fallisce con errore esplicito se stock insufficiente; include nell'output l'indirizzo di spedizione del cliente (tipo `spedizione`, fallback `sede_legale`)

**Storico:**
- `storico_movimenti(codice_articolo=None, codice_ripiano=None, limit=20)` — ultimi N movimenti filtrabili

### Aggiunte a `ERPTools` — file `erpclaw/erp_tools.py`

- `aggiungi_indirizzo_cliente(codice_cliente, tipo, via, cap, citta, provincia, paese="IT", note="")`
- `aggiungi_indirizzo_fornitore(codice_fornitore, tipo, via, cap, citta, provincia, paese="IT", note="")`
- `lista_indirizzi(codice)` — mostra tutti gli indirizzi (cliente o fornitore) con tipo
- Modifica `dettaglio_ordine` per includere l'indirizzo di spedizione del cliente

---

## Architettura

### Nuovi file
- `erpclaw/logistica_tools.py` — `LogisticaTools(Toolkit)`

### File modificati
| File | Modifica |
|------|----------|
| `erpclaw/erp_db.py` | Aggiunge `Indirizzo`; `Articolo.giacenza` → `column_property` |
| `erpclaw/erp_tools.py` | Aggiunge tool indirizzi; modifica `dettaglio_ordine` |
| `erpclaw/agent.py` | Registra `LogisticaTools()` nel team principale |
| `erpclaw/web.py` | Aggiunge `ModelView` per nuovi modelli nell'admin panel |

> **Nessun nuovo database** — tutto in `erp.db` per semplicità e coerenza transazionale.

---

## Flusso: Scarico Automatico da Ordine

```
utente: "spedisci ordine ORD-0042"
  → aggiorna_stato_ordine("ORD-0042", "spedito")         [ERPTools]
  → scarica_ordine_da_ubicazione("ORD-0042")              [LogisticaTools]
     → per ogni RigaOrdine:
         - trova StockUbicazione ordinati per quantita DESC (LIFO)
         - genera MovimentoMagazzino tipo=scarico
         - decrementa StockUbicazione
     → giacenza si aggiorna automaticamente (column_property)
     → output include indirizzo spedizione cliente
```

---

## Decisioni Architetturali

| Decisione | Scelta | Motivazione |
|-----------|--------|-------------|
| Pattern agente | `LogisticaTools(Toolkit)` nel team principale | Operazioni CRUD deterministiche, coerenza con ERPTools |
| Database | Tutto in `erp.db` | Semplicità + transazioni ACID su più tabelle |
| Gerarchia ubicazioni | Magazzino→Zona→Scaffale→Ripiano | Struttura B approvata dall'utente |
| Giacenza | `column_property` derivata | Singola fonte di verità (StockUbicazione) |
| Indirizzi | Tabella unica con FK nullable | Evita duplicazione schema per clienti/fornitori |
| Strategia scarico | LIFO per ubicazione | Semplice, deterministico, facile da spiegare |
