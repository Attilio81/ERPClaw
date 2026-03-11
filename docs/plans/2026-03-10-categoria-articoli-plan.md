# Categoria Articoli Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Aggiungere categorie piatte agli articoli, gestite dall'agente AI tramite tre nuovi tool ERP.

**Architecture:** Nuova tabella `categorie` con FK nullable in `articoli`. L'agente usa tool dedicati per creare categorie, elencarle e assegnarle agli articoli. La migrazione DB è uno script Python one-shot. L'admin SQLAdmin espone la nuova entità.

**Tech Stack:** SQLAlchemy ORM, SQLite (ALTER TABLE), agno Toolkit, SQLAdmin, pytest in-memory SQLite.

---

### Task 1: Modello Categoria in erp_db.py

**Files:**
- Modify: `erpclaw/erp_db.py`

**Step 1: Aggiungere il modello `Categoria` e la FK in `Articolo`**

In `erp_db.py`, subito dopo le classi Enum e prima di `Articolo`, aggiungere:

```python
class Categoria(Base):
    __tablename__ = "categorie"

    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)

    def __str__(self):
        return self.nome

    articoli = relationship("Articolo", back_populates="categoria")
```

In `Articolo`, aggiungere dopo `prezzo`:
```python
categoria_id = Column(Integer, ForeignKey("categorie.id"), nullable=True)
```

E la relazione (aggiungere tra le relazioni esistenti):
```python
categoria = relationship("Categoria", back_populates="articoli")
```

Aggiornare l'import di `Categoria` nei file che ne hanno bisogno (vedi Task 2).

**Step 2: Verificare che i test esistenti passino ancora**

```bash
uv run --no-sync python -m pytest tests/ -v
```

Atteso: tutti PASS (la nuova colonna nullable non rompe nulla in-memory).

**Step 3: Commit**

```bash
git add erpclaw/erp_db.py
git commit -m "feat: add Categoria model with nullable FK on Articolo"
```

---

### Task 2: Script di migrazione DB

**Files:**
- Create: `migrate_categoria.py` (nella root del progetto)

**Step 1: Creare lo script**

```python
"""Migrazione one-shot: aggiunge tabella categorie e colonna categoria_id ad articoli."""
import sqlite3

conn = sqlite3.connect("erp.db")
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS categorie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    )
""")

# SQLite: ADD COLUMN non supporta UNIQUE/NOT NULL, ma FK nullable è OK
cur.execute("""
    ALTER TABLE articoli ADD COLUMN categoria_id INTEGER REFERENCES categorie(id)
""")

conn.commit()
conn.close()
print("Migrazione completata.")
```

**Step 2: Eseguire la migrazione**

```bash
uv run --no-sync python migrate_categoria.py
```

Atteso: `Migrazione completata.`

Se la colonna esiste già, SQLite lancia `OperationalError: duplicate column name` — ignorabile (già migrato).

**Step 3: Commit**

```bash
git add migrate_categoria.py
git commit -m "feat: add migration script for categorie table and categoria_id column"
```

---

### Task 3: Test per i nuovi tool ERP

**Files:**
- Create: `tests/test_categoria.py`

**Step 1: Scrivere i test fallenti**

```python
"""Tests for categoria tools in ERPTools."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unittest.mock import patch

from erpclaw.erp_db import Base, Articolo, Categoria
from erpclaw.erp_tools import ERPTools


def make_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def tools():
    eng = make_engine()
    def make_session():
        return Session(eng)
    with patch("erpclaw.erp_tools.get_session", side_effect=make_session):
        yield ERPTools(), make_session


def test_crea_categoria(tools):
    t, _ = tools
    result = t.crea_categoria("Bevande")
    assert "Bevande" in result
    assert "creata" in result.lower()


def test_crea_categoria_duplicato(tools):
    t, _ = tools
    t.crea_categoria("Bevande")
    result = t.crea_categoria("Bevande")
    assert "esiste" in result.lower() or "già" in result.lower()


def test_lista_categorie_vuota(tools):
    t, _ = tools
    result = t.lista_categorie()
    assert "nessuna" in result.lower()


def test_lista_categorie(tools):
    t, _ = tools
    t.crea_categoria("Bevande")
    t.crea_categoria("Snack")
    result = t.lista_categorie()
    assert "Bevande" in result
    assert "Snack" in result


def test_assegna_categoria(tools):
    t, make_session = tools
    # Prerequisiti
    t.crea_categoria("Bevande")
    with make_session() as s:
        s.add(Articolo(codice="ART01", descrizione="Test", prezzo=1.0))
        s.commit()
    result = t.assegna_categoria("ART01", "Bevande")
    assert "ART01" in result
    assert "Bevande" in result


def test_assegna_categoria_articolo_non_trovato(tools):
    t, _ = tools
    t.crea_categoria("Bevande")
    result = t.assegna_categoria("XXXXXX", "Bevande")
    assert "non trovato" in result.lower() or "errore" in result.lower()


def test_assegna_categoria_non_trovata(tools):
    t, make_session = tools
    with make_session() as s:
        s.add(Articolo(codice="ART01", descrizione="Test", prezzo=1.0))
        s.commit()
    result = t.assegna_categoria("ART01", "Inesistente")
    assert "non trovata" in result.lower() or "errore" in result.lower()
```

**Step 2: Eseguire i test per verificare che falliscano**

```bash
uv run --no-sync python -m pytest tests/test_categoria.py -v
```

Atteso: FAIL con `AttributeError: 'ERPTools' object has no attribute 'crea_categoria'`

**Step 3: Commit**

```bash
git add tests/test_categoria.py
git commit -m "test: add failing tests for categoria tools"
```

---

### Task 4: Implementare i tool in ERPTools

**Files:**
- Modify: `erpclaw/erp_tools.py`

**Step 1: Aggiornare gli import**

Aggiungere `Categoria` all'import da `erp_db`:

```python
from erpclaw.erp_db import (
    get_session, init_db,
    Articolo, Cliente, Ordine, RigaOrdine, StatoOrdine,
    Fornitore, CatalogoFornitore,
    Indirizzo, TipoIndirizzo,
    Categoria,
)
```

**Step 2: Registrare i nuovi tool in `__init__`**

Aggiungere dopo `self.register(self.lista_indirizzi_fornitore)`:

```python
self.register(self.crea_categoria)
self.register(self.lista_categorie)
self.register(self.assegna_categoria)
```

**Step 3: Aggiungere i metodi**

Aggiungere nella sezione ARTICOLI (o in una nuova sezione `# ── CATEGORIE ──`):

```python
# ── CATEGORIE ─────────────────────────────────────────────────────────────

def crea_categoria(self, nome: str) -> str:
    """Crea una nuova categoria articoli. Usa prima lista_categorie per evitare duplicati."""
    with get_session() as s:
        if s.query(Categoria).filter_by(nome=nome).first():
            return f"Errore: la categoria **{nome}** esiste già."
        s.add(Categoria(nome=nome))
        s.commit()
    return f"Categoria **{nome}** creata ✓"

def lista_categorie(self) -> str:
    """Restituisce l'elenco di tutte le categorie articoli disponibili."""
    with get_session() as s:
        cats = s.query(Categoria).order_by(Categoria.nome).all()
        if not cats:
            return "Nessuna categoria presente."
        rows = "\n".join(f"- {c.nome}" for c in cats)
    return f"**Categorie disponibili:**\n{rows}"

def assegna_categoria(self, codice_articolo: str, nome_categoria: str) -> str:
    """Assegna una categoria a un articolo esistente."""
    with get_session() as s:
        articolo = s.query(Articolo).filter_by(codice=codice_articolo).first()
        if not articolo:
            return f"Errore: articolo **{codice_articolo}** non trovato."
        categoria = s.query(Categoria).filter_by(nome=nome_categoria).first()
        if not categoria:
            return f"Errore: categoria **{nome_categoria}** non trovata. Usa crea_categoria prima."
        articolo.categoria_id = categoria.id
        s.commit()
    return f"Articolo **{codice_articolo}** assegnato alla categoria **{nome_categoria}** ✓"
```

**Step 4: Eseguire i test**

```bash
uv run --no-sync python -m pytest tests/test_categoria.py -v
```

Atteso: tutti PASS

**Step 5: Eseguire tutti i test per regressioni**

```bash
uv run --no-sync python -m pytest tests/ -v
```

Atteso: tutti PASS

**Step 6: Commit**

```bash
git add erpclaw/erp_tools.py
git commit -m "feat: add crea_categoria, lista_categorie, assegna_categoria tools"
```

---

### Task 5: Admin SQLAdmin

**Files:**
- Modify: `erpclaw/web.py`

**Step 1: Aggiornare import**

Aggiungere `Categoria` all'import da `erp_db`:

```python
from erpclaw.erp_db import (
    engine, init_db,
    Articolo, Cliente, Ordine, RigaOrdine, Fornitore, CatalogoFornitore,
    Indirizzo,
    Magazzino, Zona, Scaffale, Ripiano, StockUbicazione, MovimentoMagazzino,
    Categoria,
)
```

**Step 2: Aggiungere `CategoriaAdmin`**

Aggiungere subito prima di `ArticoloAdmin`:

```python
class CategoriaAdmin(ModelView, model=Categoria):
    name = "Categoria"
    name_plural = "Categorie"
    icon = "fa-solid fa-tag"
    column_list = [Categoria.nome]
    column_searchable_list = [Categoria.nome]
    column_sortable_list = [Categoria.nome]
```

**Step 3: Aggiungere `categoria` alla vista articoli**

In `ArticoloAdmin`, aggiornare `column_list`:

```python
column_list = [Articolo.codice, Articolo.descrizione, Articolo.categoria, Articolo.prezzo, Articolo.giacenza]
```

**Step 4: Registrare la vista**

Aggiungere `admin.add_view(CategoriaAdmin)` come prima riga di registrazione viste (prima di `ArticoloAdmin`).

**Step 5: Riavviare uvicorn e verificare manualmente**

```bash
uv run uvicorn erpclaw.web:app --reload
```

Verificare:
- `/admin/categoria/list` — lista categorie visibile
- `/admin/articolo/list` — colonna categoria presente

**Step 6: Commit**

```bash
git add erpclaw/web.py
git commit -m "feat: add CategoriaAdmin view and categoria column to ArticoloAdmin"
```

---

### Task 6: Aggiornare lista_articoli e cerca_articolo per mostrare la categoria

**Files:**
- Modify: `erpclaw/erp_tools.py`

**Step 1: Aggiornare `lista_articoli`**

```python
def lista_articoli(self) -> str:
    """Restituisce la lista di tutti gli articoli."""
    with get_session() as s:
        articoli = s.query(Articolo).order_by(Articolo.codice).all()
        if not articoli:
            return "Nessun articolo presente."
        rows = "\n".join(
            f"| {a.codice} | {a.descrizione} | {a.categoria.nome if a.categoria else '—'} | €{a.prezzo:.2f} | {a.giacenza} |"
            for a in articoli
        )
    return f"| Codice | Descrizione | Categoria | Prezzo | Giacenza |\n|--------|-------------|-----------|--------|----------|\n{rows}"
```

**Step 2: Aggiornare `cerca_articolo` allo stesso modo**

Stessa modifica: aggiungere `| {a.categoria.nome if a.categoria else '—'} |` nella riga.

**Step 3: Eseguire tutti i test**

```bash
uv run --no-sync python -m pytest tests/ -v
```

Atteso: tutti PASS

**Step 4: Commit**

```bash
git add erpclaw/erp_tools.py
git commit -m "feat: show categoria in lista_articoli and cerca_articolo output"
```
