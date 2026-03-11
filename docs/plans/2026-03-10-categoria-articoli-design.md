# Categoria Articoli — Design

**Date:** 2026-03-10
**Status:** Approved

## Obiettivo

Aggiungere categorie piatte agli articoli, gestite autonomamente dall'agente AI. L'operatore non crea categorie manualmente: è l'agente che le crea e le assegna durante le operazioni ERP.

## Modello Dati

### Nuova tabella `categorie`
| Campo | Tipo | Note |
|-------|------|-------|
| id | INTEGER PK | auto-increment |
| nome | TEXT UNIQUE NOT NULL | es. "Bevande", "Snack" |

### Modifica tabella `articoli`
- Aggiunta colonna `categoria_id INTEGER REFERENCES categorie(id)` (nullable)
- Relazione SQLAlchemy: `Articolo.categoria → Categoria` (many-to-one)

La FK è nullable per non rompere gli articoli esistenti durante la migrazione.

## Tool Agente (ERPTools)

Tre nuovi tool in `erpclaw/erp_tools.py`:

- **`crea_categoria(nome)`** — crea una categoria se non esiste già; restituisce messaggio di conferma o avviso di duplicato
- **`lista_categorie()`** — elenca tutte le categorie esistenti (per consultazione prima di assegnare)
- **`assegna_categoria(codice_articolo, nome_categoria)`** — collega un articolo a una categoria esistente

## Migrazione DB

SQLite non supporta ALTER TABLE con vincoli, ma supporta ADD COLUMN nullable:

```sql
CREATE TABLE categorie (id INTEGER PRIMARY KEY, nome TEXT UNIQUE NOT NULL);
ALTER TABLE articoli ADD COLUMN categoria_id INTEGER REFERENCES categorie(id);
```

Eseguita a runtime tramite script di migrazione one-shot, oppure rilevata automaticamente se si usa `init_db()` con un check della colonna esistente.

**Approccio scelto:** script Python separato `migrate_categoria.py` da eseguire una volta.

## Admin SQLAdmin

- Nuova vista `CategoriaAdmin` (lista, ricerca, CRUD)
- `ArticoloAdmin`: aggiunta colonna `categoria` in `column_list` e nel form

## Scope Escluso (YAGNI)

- Filtro per categoria nel portale shop (possibile estensione futura)
- Categorie gerarchiche
- Import/export categorie
