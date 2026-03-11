# Prezzi Articolo e Ordini Fornitori — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename `Articolo.prezzo` → `prezzo_vendita`, add `prezzo_acquisto`, and implement a full supplier order workflow (`OrdineFornitore`) with status progression `bozza → inviato → ricevuto`.

**Architecture:** New DB columns added via `_migrate()` (idempotent); new tables `ordini_fornitori` + `righe_ordini_fornitori` created via `Base.metadata.create_all()`; new agent tools added to `ERPTools`; shop portal updated to use `prezzo_vendita`.

**Tech Stack:** SQLAlchemy (sync), SQLite, agno Toolkit, FastAPI + SQLAdmin, itsdangerous (shop)

---

### Task 1: DB models — add prezzo_vendita, prezzo_acquisto, OrdineFornitore, RigaOrdineFornitore

**Files:**
- Modify: `erpclaw/erp_db.py`

**Step 1: Add `StatoOrdineFornitore` enum after `TipoMovimento`**

In `erpclaw/erp_db.py`, after the `TipoMovimento` enum (line ~37), add:

```python
class StatoOrdineFornitore(str, enum.Enum):
    bozza = "bozza"
    inviato = "inviato"
    ricevuto = "ricevuto"
```

**Step 2: Update `Articolo` model — rename `prezzo` → `prezzo_vendita`, add `prezzo_acquisto`**

Replace:
```python
prezzo = Column(Float, nullable=False)
```
With:
```python
prezzo_vendita = Column(Float, nullable=False)
prezzo_acquisto = Column(Float, nullable=True)
```

**Step 3: Add `OrdineFornitore` and `RigaOrdineFornitore` models**

Add after the `RigaOrdine` class (before `Fornitore`):

```python
class OrdineFornitore(Base):
    __tablename__ = "ordini_fornitori"

    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    fornitore_id = Column(Integer, ForeignKey("fornitori.id"), nullable=False)
    stato = Column(Enum(StatoOrdineFornitore), nullable=False, default=StatoOrdineFornitore.bozza)
    note = Column(Text, default="")

    def __str__(self):
        return self.numero

    fornitore = relationship("Fornitore", back_populates="ordini_fornitori")
    righe = relationship("RigaOrdineFornitore", back_populates="ordine_fornitore", cascade="all, delete-orphan")


class RigaOrdineFornitore(Base):
    __tablename__ = "righe_ordini_fornitori"

    id = Column(Integer, primary_key=True)
    ordine_fornitore_id = Column(Integer, ForeignKey("ordini_fornitori.id"), nullable=False)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    quantita = Column(Integer, nullable=False)
    prezzo_unitario = Column(Float, nullable=False)

    ordine_fornitore = relationship("OrdineFornitore", back_populates="righe")
    articolo = relationship("Articolo")
```

**Step 4: Add `ordini_fornitori` relationship to `Fornitore`**

In the `Fornitore` class, add after the existing relationships:
```python
ordini_fornitori = relationship("OrdineFornitore", back_populates="fornitore", cascade="all, delete-orphan")
```

**Step 5: Update `_migrate()` to add new columns**

Replace the `migrations` list in `_migrate()` with:

```python
migrations = [
    ("articoli", "categoria_id", "INTEGER REFERENCES categorie(id)"),
    ("articoli", "scorta_minima", "INTEGER DEFAULT 0"),
    ("articoli", "prezzo_vendita", "REAL"),
    ("articoli", "prezzo_acquisto", "REAL"),
]
```

Then after the loop (before `conn.commit()`), add the data copy step:

```python
# Copy prezzo → prezzo_vendita for existing rows
conn.execute(text(
    "UPDATE articoli SET prezzo_vendita = prezzo WHERE prezzo_vendita IS NULL AND prezzo IS NOT NULL"
))
```

**Step 6: Update imports at top of `erp_db.py`** — no changes needed (all types already imported).

**Step 7: Verify the file looks correct, then run a quick syntax check**

```bash
uv run --no-sync python -c "from erpclaw.erp_db import OrdineFornitore, RigaOrdineFornitore, StatoOrdineFornitore; print('OK')"
```
Expected: `OK`

**Step 8: Commit**

```bash
git add erpclaw/erp_db.py
git commit -m "feat: add prezzo_vendita/prezzo_acquisto and OrdineFornitore models"
```

---

### Task 2: Write failing tests for ordine fornitore tools

**Files:**
- Create: `tests/test_ordini_fornitori.py`

**Step 1: Write the full test file**

```python
"""Tests for ordine fornitore tools in ERPTools."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unittest.mock import patch

from erpclaw.erp_db import Base, Articolo, Fornitore
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


@pytest.fixture
def tools_con_dati(tools):
    t, make_session = tools
    with make_session() as s:
        s.add(Fornitore(codice="FOR01", ragione_sociale="Fornitore Test"))
        s.add(Articolo(codice="ART01", descrizione="Articolo Test", prezzo_vendita=10.0, prezzo_acquisto=6.0))
        s.add(Articolo(codice="ART02", descrizione="Articolo Senza Costo", prezzo_vendita=5.0))
        s.commit()
    return t, make_session


def test_crea_ordine_fornitore(tools_con_dati):
    t, _ = tools_con_dati
    result = t.crea_ordine_fornitore("FOR01")
    assert "ORF-" in result
    assert "FOR01" in result or "Fornitore Test" in result


def test_crea_ordine_fornitore_non_trovato(tools_con_dati):
    t, _ = tools_con_dati
    result = t.crea_ordine_fornitore("XXXXXX")
    assert "errore" in result.lower() or "non trovato" in result.lower()


def test_aggiungi_riga_ordine_fornitore(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 5)
    assert "ART01" in result or "Articolo Test" in result
    assert "5" in result


def test_aggiungi_riga_usa_prezzo_acquisto_default(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 3)
    # prezzo_acquisto è 6.0, deve comparire nel risultato
    assert "6" in result


def test_aggiungi_riga_prezzo_esplicito(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 2, prezzo_unitario=7.5)
    assert "7.5" in result or "7,5" in result


def test_aggiungi_riga_senza_prezzo_acquisto(tools_con_dati):
    """Articolo senza prezzo_acquisto: deve richiedere prezzo_unitario esplicito."""
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART02", 1)
    assert "errore" in result.lower() or "prezzo" in result.lower()


def test_lista_ordini_fornitori(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.lista_ordini_fornitori()
    assert "ORF-0001" in result


def test_lista_ordini_fornitori_filtro_stato(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result_bozza = t.lista_ordini_fornitori(stato="bozza")
    assert "ORF-0001" in result_bozza
    result_inviato = t.lista_ordini_fornitori(stato="inviato")
    assert "ORF-0001" not in result_inviato


def test_visualizza_ordine_fornitore(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 4)
    result = t.visualizza_ordine_fornitore("ORF-0001")
    assert "ART01" in result
    assert "4" in result


def test_avanza_stato_bozza_inviato(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.avanza_stato_ordine_fornitore("ORF-0001")
    assert "inviato" in result.lower()


def test_avanza_stato_inviato_ricevuto(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    t.avanza_stato_ordine_fornitore("ORF-0001")  # bozza → inviato
    result = t.avanza_stato_ordine_fornitore("ORF-0001")  # inviato → ricevuto
    assert "ricevuto" in result.lower()


def test_avanza_stato_ricevuto_errore(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    t.avanza_stato_ordine_fornitore("ORF-0001")
    t.avanza_stato_ordine_fornitore("ORF-0001")
    result = t.avanza_stato_ordine_fornitore("ORF-0001")  # già ricevuto
    assert "errore" in result.lower() or "già" in result.lower()


def test_avanza_stato_ordine_non_trovato(tools_con_dati):
    t, _ = tools_con_dati
    result = t.avanza_stato_ordine_fornitore("ORF-9999")
    assert "errore" in result.lower() or "non trovato" in result.lower()
```

**Step 2: Run tests to confirm they all fail**

```bash
uv run --no-sync python -m pytest tests/test_ordini_fornitori.py -v
```
Expected: All FAIL with `AttributeError` (tools don't exist yet)

**Step 3: Commit**

```bash
git add tests/test_ordini_fornitori.py
git commit -m "test: add failing TDD tests for ordine fornitore tools"
```

---

### Task 3: Update existing tools in erp_tools.py (prezzo rename)

**Files:**
- Modify: `erpclaw/erp_tools.py`

**Step 1: Update imports to include new models**

Replace the import block at the top:
```python
from erpclaw.erp_db import (
    get_session, init_db,
    Articolo, Cliente, Ordine, RigaOrdine, StatoOrdine,
    Fornitore, CatalogoFornitore,
    Indirizzo, TipoIndirizzo,
    Categoria,
    OrdineFornitore, RigaOrdineFornitore, StatoOrdineFornitore,
)
```

**Step 2: Update `crea_articolo` signature and body**

Replace:
```python
def crea_articolo(self, codice: str, descrizione: str, prezzo: float) -> str:
    """Crea un nuovo articolo nel catalogo."""
    with get_session() as s:
        if s.query(Articolo).filter_by(codice=codice).first():
            return f"Errore: esiste già un articolo con codice {codice}."
        s.add(Articolo(codice=codice, descrizione=descrizione, prezzo=prezzo))
        s.commit()
    return f"Articolo **{codice}** creato ✓"
```
With:
```python
def crea_articolo(self, codice: str, descrizione: str, prezzo_vendita: float, prezzo_acquisto: float = None) -> str:
    """Crea un nuovo articolo nel catalogo con prezzo di vendita e (opzionale) prezzo di acquisto."""
    with get_session() as s:
        if s.query(Articolo).filter_by(codice=codice).first():
            return f"Errore: esiste già un articolo con codice {codice}."
        s.add(Articolo(codice=codice, descrizione=descrizione,
                       prezzo_vendita=prezzo_vendita, prezzo_acquisto=prezzo_acquisto))
        s.commit()
    return f"Articolo **{codice}** creato ✓"
```

**Step 3: Update `lista_articoli` display**

Replace the rows formatting in `lista_articoli`:
```python
rows = "\n".join(
    f"| {a.codice} | {a.descrizione} | {a.categoria.nome if a.categoria else '—'} | €{a.prezzo_vendita:.2f} | {f'€{a.prezzo_acquisto:.2f}' if a.prezzo_acquisto else '—'} | {a.giacenza} |"
    for a in articoli
)
return f"| Codice | Descrizione | Categoria | Prezzo Vendita | Prezzo Acquisto | Giacenza |\n|--------|-------------|-----------|----------------|-----------------|----------|\n{rows}"
```

**Step 4: Update `cerca_articolo` display** — same change as `lista_articoli` (same row format and header).

**Step 5: Update `aggiorna_articolo`**

Replace:
```python
def aggiorna_articolo(self, codice: str, descrizione: str = None, prezzo: float = None) -> str:
    """Aggiorna descrizione o prezzo di un articolo esistente."""
    with get_session() as s:
        a = s.query(Articolo).filter_by(codice=codice).first()
        if not a:
            return f"Errore: articolo {codice} non trovato."
        if descrizione is not None:
            a.descrizione = descrizione
        if prezzo is not None:
            a.prezzo = prezzo
        s.commit()
    return f"Articolo **{codice}** aggiornato ✓"
```
With:
```python
def aggiorna_articolo(self, codice: str, descrizione: str = None,
                      prezzo_vendita: float = None, prezzo_acquisto: float = None) -> str:
    """Aggiorna descrizione, prezzo di vendita o prezzo di acquisto di un articolo esistente."""
    with get_session() as s:
        a = s.query(Articolo).filter_by(codice=codice).first()
        if not a:
            return f"Errore: articolo {codice} non trovato."
        if descrizione is not None:
            a.descrizione = descrizione
        if prezzo_vendita is not None:
            a.prezzo_vendita = prezzo_vendita
        if prezzo_acquisto is not None:
            a.prezzo_acquisto = prezzo_acquisto
        s.commit()
    return f"Articolo **{codice}** aggiornato ✓"
```

**Step 6: Update `aggiungi_riga` to use `prezzo_vendita`**

Replace the two occurrences of `articolo.prezzo` and `a.prezzo`:
- `prezzo_unitario=articolo.prezzo` → `prezzo_unitario=articolo.prezzo_vendita`
- `articolo_prezzo = articolo.prezzo` → `articolo_prezzo = articolo.prezzo_vendita`

**Step 7: Run existing tests to see what breaks**

```bash
uv run --no-sync python -m pytest tests/ -v --ignore=tests/test_ordini_fornitori.py 2>&1 | head -50
```
Expected: `test_categoria.py` fails (uses `prezzo=` in Articolo constructor)

**Step 8: Commit**

```bash
git add erpclaw/erp_tools.py
git commit -m "feat: rename prezzo→prezzo_vendita, add prezzo_acquisto in existing tools"
```

---

### Task 4: Fix existing tests that use `prezzo=`

**Files:**
- Modify: `tests/test_categoria.py`
- Check and modify if needed: `tests/test_shop_cart.py`, `tests/test_shop_routes_auth.py`

**Step 1: Check which test files reference `prezzo=`**

```bash
grep -rn "prezzo=" tests/
```

**Step 2: In `tests/test_categoria.py`, replace all `prezzo=1.0` with `prezzo_vendita=1.0`**

There are 4 occurrences (lines 59, 76, 86, 87). Change each:
```python
# Before
s.add(Articolo(codice="ART01", descrizione="Test", prezzo=1.0))
# After
s.add(Articolo(codice="ART01", descrizione="Test", prezzo_vendita=1.0))
```

```python
# Before
s.add(Articolo(codice="ART01", descrizione="Sotto soglia", prezzo=1.0, scorta_minima=10))
s.add(Articolo(codice="ART02", descrizione="Nessuna soglia", prezzo=1.0, scorta_minima=0))
# After
s.add(Articolo(codice="ART01", descrizione="Sotto soglia", prezzo_vendita=1.0, scorta_minima=10))
s.add(Articolo(codice="ART02", descrizione="Nessuna soglia", prezzo_vendita=1.0, scorta_minima=0))
```

**Step 3: Fix any other test files** that reference `prezzo=` (from grep output in Step 1).

**Step 4: Run the full test suite (excluding new failing tests)**

```bash
uv run --no-sync python -m pytest tests/ -v --ignore=tests/test_ordini_fornitori.py
```
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/
git commit -m "test: update prezzo→prezzo_vendita in existing test fixtures"
```

---

### Task 5: Implement new ordine fornitore tools

**Files:**
- Modify: `erpclaw/erp_tools.py`

**Step 1: Register new tools in `__init__`**

After `self.register(self.articoli_sotto_scorta_minima)`, add:
```python
self.register(self.crea_ordine_fornitore)
self.register(self.aggiungi_riga_ordine_fornitore)
self.register(self.lista_ordini_fornitori)
self.register(self.visualizza_ordine_fornitore)
self.register(self.avanza_stato_ordine_fornitore)
```

**Step 2: Add new tools section at the end of `ERPTools`**

```python
# ── ORDINI FORNITORI ───────────────────────────────────────────────────────

def crea_ordine_fornitore(self, fornitore_codice: str, note: str = "") -> str:
    """Crea un nuovo ordine di acquisto per un fornitore in stato bozza. Usa aggiungi_riga_ordine_fornitore per aggiungere articoli."""
    with get_session() as s:
        fornitore = s.query(Fornitore).filter_by(codice=fornitore_codice).first()
        if not fornitore:
            return f"Errore: fornitore {fornitore_codice} non trovato."
        count = s.query(OrdineFornitore).count()
        numero = f"ORF-{count + 1:04d}"
        from datetime import date
        ordine = OrdineFornitore(
            numero=numero,
            data=date.today(),
            fornitore_id=fornitore.id,
            note=note,
        )
        s.add(ordine)
        s.commit()
        ragione_sociale = fornitore.ragione_sociale
    return (
        f"Ordine fornitore **{numero}** creato per {ragione_sociale} (stato: bozza) ✓\n"
        f"Aggiungi le righe con `aggiungi_riga_ordine_fornitore`."
    )

def aggiungi_riga_ordine_fornitore(self, numero_ordine: str, codice_articolo: str,
                                    quantita: int, prezzo_unitario: float = None) -> str:
    """Aggiunge una riga a un ordine fornitore. Se prezzo_unitario è omesso, usa il prezzo_acquisto dell'articolo."""
    with get_session() as s:
        ordine = s.query(OrdineFornitore).filter_by(numero=numero_ordine).first()
        if not ordine:
            return f"Errore: ordine fornitore {numero_ordine} non trovato."
        articolo = s.query(Articolo).filter_by(codice=codice_articolo).first()
        if not articolo:
            return f"Errore: articolo {codice_articolo} non trovato."
        prezzo = prezzo_unitario if prezzo_unitario is not None else articolo.prezzo_acquisto
        if prezzo is None:
            return (
                f"Errore: l'articolo {codice_articolo} non ha un prezzo di acquisto. "
                f"Specifica prezzo_unitario."
            )
        riga = s.query(RigaOrdineFornitore).filter_by(
            ordine_fornitore_id=ordine.id, articolo_id=articolo.id
        ).first()
        if riga:
            riga.quantita += quantita
        else:
            riga = RigaOrdineFornitore(
                ordine_fornitore_id=ordine.id,
                articolo_id=articolo.id,
                quantita=quantita,
                prezzo_unitario=prezzo,
            )
            s.add(riga)
        s.commit()
        righe = s.query(RigaOrdineFornitore).filter_by(ordine_fornitore_id=ordine.id).all()
        totale = sum(r.quantita * r.prezzo_unitario for r in righe)
        articolo_desc = articolo.descrizione
        subtotale = quantita * prezzo
    return (
        f"Riga aggiunta: {quantita}x **{articolo_desc}** @ €{prezzo:.2f} = €{subtotale:.2f}\n"
        f"Totale ordine **{numero_ordine}**: €{totale:.2f}"
    )

def lista_ordini_fornitori(self, stato: str = None) -> str:
    """Elenca gli ordini fornitore, opzionalmente filtrati per stato (bozza/inviato/ricevuto)."""
    with get_session() as s:
        q = s.query(OrdineFornitore)
        if stato:
            try:
                q = q.filter(OrdineFornitore.stato == StatoOrdineFornitore(stato))
            except ValueError:
                return f"Errore: stato '{stato}' non valido. Valori: bozza, inviato, ricevuto."
        ordini = q.order_by(OrdineFornitore.numero).all()
        if not ordini:
            return "Nessun ordine fornitore trovato."
        rows = "\n".join(
            f"| {o.numero} | {o.data} | {o.fornitore.ragione_sociale} | {o.stato.value} |"
            for o in ordini
        )
    return f"| Numero | Data | Fornitore | Stato |\n|--------|------|-----------|-------|\n{rows}"

def visualizza_ordine_fornitore(self, numero_ordine: str) -> str:
    """Mostra le righe e il totale di un ordine fornitore."""
    with get_session() as s:
        ordine = s.query(OrdineFornitore).filter_by(numero=numero_ordine).first()
        if not ordine:
            return f"Errore: ordine fornitore {numero_ordine} non trovato."
        righe = s.query(RigaOrdineFornitore).filter_by(ordine_fornitore_id=ordine.id).all()
        header = (
            f"**Ordine Fornitore {ordine.numero}** – {ordine.fornitore.ragione_sociale}\n"
            f"Data: {ordine.data}  |  Stato: {ordine.stato.value}\n\n"
            f"| Codice | Descrizione | Qtà | Prezzo | Subtotale |\n"
            f"|--------|-------------|-----|--------|-----------|\n"
        )
        if not righe:
            return header + "_Nessuna riga._"
        rows = "\n".join(
            f"| {r.articolo.codice} | {r.articolo.descrizione} | {r.quantita} | €{r.prezzo_unitario:.2f} | €{r.quantita * r.prezzo_unitario:.2f} |"
            for r in righe
        )
        totale = sum(r.quantita * r.prezzo_unitario for r in righe)
    return header + rows + f"\n\n**Totale: €{totale:.2f}**"

def avanza_stato_ordine_fornitore(self, numero_ordine: str) -> str:
    """Avanza lo stato dell'ordine fornitore: bozza→inviato→ricevuto. Quando ricevuto, usare i tool di logistica per caricare la merce in magazzino."""
    transizioni = {
        StatoOrdineFornitore.bozza: StatoOrdineFornitore.inviato,
        StatoOrdineFornitore.inviato: StatoOrdineFornitore.ricevuto,
    }
    with get_session() as s:
        ordine = s.query(OrdineFornitore).filter_by(numero=numero_ordine).first()
        if not ordine:
            return f"Errore: ordine fornitore {numero_ordine} non trovato."
        nuovo_stato = transizioni.get(ordine.stato)
        if nuovo_stato is None:
            return f"Errore: l'ordine **{numero_ordine}** è già in stato **ricevuto**."
        ordine.stato = nuovo_stato
        s.commit()
        stato_str = nuovo_stato.value
    msg = f"Ordine **{numero_ordine}** → stato **{stato_str}** ✓"
    if nuovo_stato == StatoOrdineFornitore.ricevuto:
        msg += "\nMerce attesa in arrivo. Usare i tool di logistica per caricare gli articoli nelle ubicazioni di magazzino."
    return msg
```

**Step 3: Run the new test suite**

```bash
uv run --no-sync python -m pytest tests/test_ordini_fornitori.py -v
```
Expected: All PASS

**Step 4: Run full test suite**

```bash
uv run --no-sync python -m pytest tests/ -v
```
Expected: All PASS

**Step 5: Commit**

```bash
git add erpclaw/erp_tools.py
git commit -m "feat: implement crea_ordine_fornitore and related tools"
```

---

### Task 6: Update web admin (web.py)

**Files:**
- Modify: `erpclaw/web.py`

**Step 1: Update imports**

Replace the import from `erp_db`:
```python
from erpclaw.erp_db import (
    engine, init_db,
    Categoria, Articolo, Cliente, Ordine, RigaOrdine, Fornitore, CatalogoFornitore,
    Indirizzo,
    Magazzino, Zona, Scaffale, Ripiano, StockUbicazione, MovimentoMagazzino,
    OrdineFornitore, RigaOrdineFornitore,
)
```

**Step 2: Update `ArticoloAdmin`**

Replace:
```python
column_list = [Articolo.codice, Articolo.descrizione, Articolo.categoria, Articolo.prezzo, Articolo.giacenza, Articolo.scorta_minima]
column_searchable_list = [Articolo.codice, Articolo.descrizione]
column_sortable_list = [Articolo.codice, Articolo.prezzo, Articolo.giacenza]
form_excluded_columns = ["giacenza"]
```
With:
```python
column_list = [Articolo.codice, Articolo.descrizione, Articolo.categoria, Articolo.prezzo_vendita, Articolo.prezzo_acquisto, Articolo.giacenza, Articolo.scorta_minima]
column_searchable_list = [Articolo.codice, Articolo.descrizione]
column_sortable_list = [Articolo.codice, Articolo.prezzo_vendita, Articolo.giacenza]
form_excluded_columns = ["giacenza"]
```

**Step 3: Add `OrdineFornitoreAdmin` and `RigaOrdineFornitoreAdmin`** after `CatalogoFornitoreAdmin`:

```python
class OrdineFornitoreAdmin(ModelView, model=OrdineFornitore):
    name = "Ordine Fornitore"
    name_plural = "Ordini Fornitori"
    icon = "fa-solid fa-truck-ramp-box"
    column_list = [OrdineFornitore.numero, OrdineFornitore.data, OrdineFornitore.fornitore, OrdineFornitore.stato]
    column_searchable_list = [OrdineFornitore.numero]
    column_sortable_list = [OrdineFornitore.numero, OrdineFornitore.data, OrdineFornitore.stato]
    column_details_list = [OrdineFornitore.numero, OrdineFornitore.data, OrdineFornitore.stato, OrdineFornitore.fornitore, OrdineFornitore.righe, OrdineFornitore.note]


class RigaOrdineFornitoreAdmin(ModelView, model=RigaOrdineFornitore):
    name = "Riga Ordine Fornitore"
    name_plural = "Righe Ordini Fornitori"
    icon = "fa-solid fa-list"
    column_list = [RigaOrdineFornitore.ordine_fornitore, RigaOrdineFornitore.articolo, RigaOrdineFornitore.quantita, RigaOrdineFornitore.prezzo_unitario]
    column_sortable_list = [RigaOrdineFornitore.quantita, RigaOrdineFornitore.prezzo_unitario]
```

**Step 4: Register the new views with `admin.add_view(...)`**

Find the section where views are registered (near the bottom of `web.py`) and add:
```python
admin.add_view(OrdineFornitoreAdmin)
admin.add_view(RigaOrdineFornitoreAdmin)
```

**Step 5: Verify the app imports without error**

```bash
uv run --no-sync python -c "from erpclaw.web import app; print('OK')"
```
Expected: `OK`

**Step 6: Commit**

```bash
git add erpclaw/web.py
git commit -m "feat: add OrdineFornitore admin views, update ArticoloAdmin for prezzo_vendita"
```

---

### Task 7: Update shop portal (shop.py)

**Files:**
- Modify: `erpclaw/shop.py`

**Step 1: Find all references to `a.prezzo` or `.prezzo` in shop.py**

```bash
grep -n "\.prezzo" erpclaw/shop.py
```

**Step 2: Replace `a.prezzo` with `a.prezzo_vendita`**

There are occurrences at lines ~208, ~230, ~242. Replace each:
- `"prezzo": a.prezzo` → `"prezzo": a.prezzo_vendita`
- `codice, descrizione, prezzo = a.codice, a.descrizione, a.prezzo` → `codice, descrizione, prezzo = a.codice, a.descrizione, a.prezzo_vendita`

(The `prezzo` local variable name in the cart dict can stay as `prezzo` — it's just a dict key, not the DB column.)

**Step 3: Verify shop imports**

```bash
uv run --no-sync python -c "from erpclaw.shop import router; print('OK')"
```
Expected: `OK`

**Step 4: Run full test suite**

```bash
uv run --no-sync python -m pytest tests/ -v
```
Expected: All PASS

**Step 5: Commit**

```bash
git add erpclaw/shop.py
git commit -m "fix: update shop portal to use prezzo_vendita"
```

---

### Task 8: Final verification

**Step 1: Run complete test suite**

```bash
uv run --no-sync python -m pytest tests/ -v
```
Expected: All PASS, no warnings about unknown columns.

**Step 2: Verify app startup**

```bash
uv run --no-sync python -c "
from erpclaw.erp_db import init_db, OrdineFornitore, RigaOrdineFornitore, StatoOrdineFornitore
from erpclaw.erp_tools import ERPTools
from erpclaw.web import app
init_db()
t = ERPTools()
print('All tools:', [f for f in dir(t) if 'ordine_fornitore' in f or 'prezzo' in f.lower()])
print('OK')
"
```
Expected: Lists the new tools, prints `OK`

**Step 3: Commit summary if needed, then done**

```bash
git log --oneline -8
```
