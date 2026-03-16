# DDT e Fatture — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DDT (transport document) and Fattura (invoice) management to ERPClaw, with database persistence, PDF generation, agent tools, and web download endpoints.

**Architecture:** New `documenti_db.py` adds DDT/Fattura models sharing the existing `erp_db.Base` and `erp.db`. A `DocumentiTools` toolkit exposes 9 agent tools. `documenti_pdf.py` generates PDFs with `fpdf2` using absolute paths. A FastAPI router exposes `/documenti/*/pdf` download endpoints and two SQLAdmin views are added.

**Tech Stack:** SQLAlchemy (sync), fpdf2, FastAPI FileResponse, agno Toolkit, pytest with in-memory SQLite

**Spec:** `docs/superpowers/specs/2026-03-16-ddt-fatture-design.md`

---

## Chunk 1: Data layer

### Task 1: Add `aliquota_iva` to `Articolo`

**Files:**
- Modify: `erpclaw/erp_db.py`
- Test: `tests/test_aliquota_iva.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_aliquota_iva.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Articolo

def test_articolo_ha_aliquota_iva():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        s.add(Articolo(codice="A1", descrizione="Test", prezzo_vendita=10.0))
        s.commit()
        a = s.query(Articolo).filter_by(codice="A1").first()
        assert a.aliquota_iva == 0.22

def test_articolo_aliquota_iva_personalizzata():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        s.add(Articolo(codice="A2", descrizione="Test", prezzo_vendita=5.0, aliquota_iva=0.10))
        s.commit()
        a = s.query(Articolo).filter_by(codice="A2").first()
        assert a.aliquota_iva == 0.10
```

- [ ] **Step 2: Run test to verify it fails**

```
uv run --no-sync python -m pytest tests/test_aliquota_iva.py -v
```
Expected: `AttributeError` — `Articolo` has no `aliquota_iva`

- [ ] **Step 3: Add column to `Articolo` model in `erpclaw/erp_db.py`**

In the `Articolo` class, after `scorta_minima`, add:
```python
aliquota_iva = Column(Float, nullable=False, default=0.22, server_default="0.22")
```

In `_migrate()`, add to the `migrations` list:
```python
("articoli", "aliquota_iva", "REAL DEFAULT 0.22"),
```

- [ ] **Step 4: Run test to verify it passes**

```
uv run --no-sync python -m pytest tests/test_aliquota_iva.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Run full test suite to check no regressions**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green

- [ ] **Step 6: Commit**

```bash
git add erpclaw/erp_db.py tests/test_aliquota_iva.py
git commit -m "feat: add aliquota_iva field to Articolo (default 22%)"
```

---

### Task 2: Create `documenti_db.py`

**Files:**
- Create: `erpclaw/documenti_db.py`
- Test: `tests/test_documenti_db.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_documenti_db.py
import enum
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Import documenti_db BEFORE create_all so its models register on Base
import erpclaw.documenti_db  # noqa: F401
from erpclaw.erp_db import Base, Articolo, Cliente, Ordine, StatoOrdine
from erpclaw.documenti_db import DDT, Fattura, RigaFattura, StatoDDT, StatoFattura


def make_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def test_crea_ddt(session_with_ordine):
    s, ordine_id = session_with_ordine
    ddt = DDT(numero="DDT-20260316-001", data=date.today(), ordine_id=ordine_id)
    s.add(ddt)
    s.commit()
    assert ddt.id is not None
    assert ddt.stato == StatoDDT.bozza
    assert ddt.percorso_pdf is None


def test_ddt_unique_per_ordine(session_with_ordine):
    s, ordine_id = session_with_ordine
    s.add(DDT(numero="DDT-20260316-001", data=date.today(), ordine_id=ordine_id))
    s.commit()
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        s.add(DDT(numero="DDT-20260316-002", data=date.today(), ordine_id=ordine_id))
        s.commit()


def test_crea_fattura(session_with_cliente):
    s, cliente_id = session_with_cliente
    f = Fattura(numero="FT-2026-0001", data=date.today(), cliente_id=cliente_id)
    s.add(f)
    s.commit()
    assert f.id is not None
    assert f.stato == StatoFattura.bozza


def test_riga_fattura_snapshot(session_with_fattura):
    s, fattura_id, articolo_id = session_with_fattura
    riga = RigaFattura(
        fattura_id=fattura_id,
        articolo_id=articolo_id,
        quantita=3,
        prezzo_unitario=10.0,
        aliquota_iva=0.22,
    )
    s.add(riga)
    s.commit()
    r = s.query(RigaFattura).filter_by(fattura_id=fattura_id).first()
    assert r.quantita == 3
    assert r.prezzo_unitario == 10.0
    assert r.aliquota_iva == 0.22


def test_fattura_ddt_associazione(session_with_fattura_e_ddt):
    s, fattura, ddt = session_with_fattura_e_ddt
    fattura.ddt_collegati.append(ddt)
    s.commit()
    assert ddt in fattura.ddt_collegati


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def session_with_ordine():
    eng = make_engine()
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Test SRL")
        s.add(c)
        s.flush()
        o = Ordine(numero="ORD-0001", data=date.today(),
                   cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o)
        s.commit()
        yield s, o.id


@pytest.fixture
def session_with_cliente():
    eng = make_engine()
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Test SRL")
        s.add(c)
        s.commit()
        yield s, c.id


@pytest.fixture
def session_with_fattura():
    eng = make_engine()
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Test SRL")
        a = Articolo(codice="A1", descrizione="Art", prezzo_vendita=10.0)
        s.add_all([c, a])
        s.flush()
        f = Fattura(numero="FT-2026-0001", data=date.today(), cliente_id=c.id)
        s.add(f)
        s.commit()
        yield s, f.id, a.id


@pytest.fixture
def session_with_fattura_e_ddt():
    eng = make_engine()
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Test SRL")
        s.add(c)
        s.flush()
        o = Ordine(numero="ORD-0001", data=date.today(),
                   cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o)
        s.flush()
        ddt = DDT(numero="DDT-001", data=date.today(), ordine_id=o.id)
        fat = Fattura(numero="FT-0001", data=date.today(), cliente_id=c.id)
        s.add_all([ddt, fat])
        s.commit()
        yield s, fat, ddt
```

- [ ] **Step 2: Run test to verify it fails**

```
uv run --no-sync python -m pytest tests/test_documenti_db.py -v
```
Expected: `ModuleNotFoundError: No module named 'erpclaw.documenti_db'`

- [ ] **Step 3: Create `erpclaw/documenti_db.py`**

```python
"""Modelli SQLAlchemy per DDT e Fatture — condividono erp.db e Base con erp_db."""

import enum
from datetime import date

from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, Enum, Text,
    Table, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from erpclaw.erp_db import Base, engine, get_session, init_db  # noqa: F401


class StatoDDT(str, enum.Enum):
    bozza = "bozza"
    emesso = "emesso"


class StatoFattura(str, enum.Enum):
    bozza = "bozza"
    emessa = "emessa"
    pagata = "pagata"


# Tabella di associazione many-to-many Fattura ↔ DDT
fatture_ddt = Table(
    "fatture_ddt",
    Base.metadata,
    Column("fattura_id", Integer, ForeignKey("fatture.id"), primary_key=True),
    Column("ddt_id", Integer, ForeignKey("ddt.id"), primary_key=True),
)


class DDT(Base):
    __tablename__ = "ddt"
    __table_args__ = (UniqueConstraint("ordine_id", name="uq_ddt_ordine_id"),)

    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    ordine_id = Column(Integer, ForeignKey("ordini.id"), nullable=False)
    stato = Column(Enum(StatoDDT), nullable=False, default=StatoDDT.bozza)
    note = Column(Text, default="")
    percorso_pdf = Column(String, nullable=True)

    ordine = relationship("Ordine")
    fatture = relationship("Fattura", secondary=fatture_ddt, back_populates="ddt_collegati")

    def __str__(self):
        return self.numero


class Fattura(Base):
    __tablename__ = "fatture"

    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    cliente_id = Column(Integer, ForeignKey("clienti.id"), nullable=False)
    stato = Column(Enum(StatoFattura), nullable=False, default=StatoFattura.bozza)
    note = Column(Text, default="")
    percorso_pdf = Column(String, nullable=True)

    cliente = relationship("Cliente")
    righe = relationship("RigaFattura", back_populates="fattura", cascade="all, delete-orphan")
    ddt_collegati = relationship("DDT", secondary=fatture_ddt, back_populates="fatture")

    def __str__(self):
        return self.numero


class RigaFattura(Base):
    __tablename__ = "righe_fattura"

    id = Column(Integer, primary_key=True)
    fattura_id = Column(Integer, ForeignKey("fatture.id"), nullable=False)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    quantita = Column(Integer, nullable=False)
    prezzo_unitario = Column(Float, nullable=False)
    aliquota_iva = Column(Float, nullable=False)

    fattura = relationship("Fattura", back_populates="righe")
    articolo = relationship("Articolo")


def init_documenti_db() -> None:
    """Crea le tabelle DDT/Fattura se non esistono. Chiamare all'avvio."""
    Base.metadata.create_all(bind=engine, checkfirst=True)
```

- [ ] **Step 4: Run test to verify it passes**

```
uv run --no-sync python -m pytest tests/test_documenti_db.py -v
```
Expected: 5 PASSED

- [ ] **Step 5: Run full suite**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green

- [ ] **Step 6: Commit**

```bash
git add erpclaw/documenti_db.py tests/test_documenti_db.py
git commit -m "feat: add DDT and Fattura SQLAlchemy models"
```

---

## Chunk 2: PDF generation + config

### Task 3: Add AZIENDA config vars + create `documenti_pdf.py`

**Files:**
- Modify: `erpclaw/config.py`
- Create: `erpclaw/documenti_pdf.py`
- Test: `tests/test_documenti_pdf.py`

- [ ] **Step 1: Add AZIENDA vars to `erpclaw/config.py`**

At the bottom of `config.py`, append:
```python
# Dati emittente per DDT e Fatture (opzionali)
AZIENDA_NOME = os.getenv("AZIENDA_NOME", "[Da configurare]")
AZIENDA_INDIRIZZO = os.getenv("AZIENDA_INDIRIZZO", "[Da configurare]")
AZIENDA_PIVA = os.getenv("AZIENDA_PIVA", "[Da configurare]")
```

- [ ] **Step 2: Write failing PDF tests**

```python
# tests/test_documenti_pdf.py
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import erpclaw.documenti_db  # noqa: registers models on Base
from erpclaw.erp_db import Base, Articolo, Cliente, Ordine, StatoOrdine
from erpclaw.documenti_db import DDT, Fattura, RigaFattura


def make_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def ddt_con_ordine(tmp_path):
    eng = make_engine()
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Cliente Test SRL",
                    email="test@example.com")
        s.add(c)
        s.flush()
        a = Articolo(codice="A1", descrizione="Articolo Test",
                     prezzo_vendita=100.0, aliquota_iva=0.22)
        s.add(a)
        s.flush()
        o = Ordine(numero="ORD-0001", data=date.today(),
                   cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o)
        s.flush()
        from erpclaw.erp_db import RigaOrdine
        r = RigaOrdine(ordine_id=o.id, articolo_id=a.id,
                       quantita=2, prezzo_unitario=100.0)
        s.add(r)
        ddt = DDT(numero="DDT-20260316-001", data=date.today(), ordine_id=o.id)
        s.add(ddt)
        s.commit()
        yield s, ddt, tmp_path


@pytest.fixture
def fattura_con_righe(tmp_path):
    eng = make_engine()
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Cliente Test SRL")
        s.add(c)
        s.flush()
        a = Articolo(codice="A1", descrizione="Articolo Test",
                     prezzo_vendita=100.0, aliquota_iva=0.22)
        s.add(a)
        s.flush()
        o = Ordine(numero="ORD-0001", data=date.today(),
                   cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o)
        s.flush()
        ddt = DDT(numero="DDT-20260316-001", data=date.today(), ordine_id=o.id)
        s.add(ddt)
        s.flush()
        fat = Fattura(numero="FT-2026-0001", data=date.today(), cliente_id=c.id)
        fat.ddt_collegati.append(ddt)
        s.add(fat)
        s.flush()
        riga = RigaFattura(fattura_id=fat.id, articolo_id=a.id,
                           quantita=2, prezzo_unitario=100.0, aliquota_iva=0.22)
        s.add(riga)
        s.commit()
        yield s, fat, tmp_path


def test_genera_pdf_ddt(ddt_con_ordine):
    s, ddt, tmp_path = ddt_con_ordine
    import erpclaw.documenti_pdf as pdf_mod
    with patch.object(pdf_mod, "DDT_DIR", tmp_path / "ddt"):
        path = pdf_mod.genera_pdf_ddt(ddt)
    assert path.exists()
    assert path.stat().st_size > 100  # file non vuoto
    assert path.suffix == ".pdf"


def test_genera_pdf_fattura(fattura_con_righe):
    s, fat, tmp_path = fattura_con_righe
    import erpclaw.documenti_pdf as pdf_mod
    with patch.object(pdf_mod, "FATTURE_DIR", tmp_path / "fatture"):
        path = pdf_mod.genera_pdf_fattura(fat)
    assert path.exists()
    assert path.stat().st_size > 100
    assert path.suffix == ".pdf"
```

- [ ] **Step 3: Run test to verify it fails**

```
uv run --no-sync python -m pytest tests/test_documenti_pdf.py -v
```
Expected: `ModuleNotFoundError: No module named 'erpclaw.documenti_pdf'`

- [ ] **Step 4: Install fpdf2**

```
uv pip install fpdf2
```

Then add to `pyproject.toml` dependencies list:
```toml
"fpdf2>=2.8.0",
```

- [ ] **Step 5: Create `erpclaw/documenti_pdf.py`**

```python
"""Generazione PDF per DDT e Fatture con fpdf2."""

from collections import defaultdict
from pathlib import Path

from fpdf import FPDF

from erpclaw.config import AZIENDA_INDIRIZZO, AZIENDA_NOME, AZIENDA_PIVA

BASE_DOCUMENTI = Path(__file__).parent.parent / "documenti"
DDT_DIR = BASE_DOCUMENTI / "ddt"
FATTURE_DIR = BASE_DOCUMENTI / "fatture"

# fpdf2 ≥2.7 removed the ln=True shorthand; use new_x/new_y instead.
_NL = {"new_x": "LMARGIN", "new_y": "NEXT"}


def _intestazione_emittente(pdf: FPDF) -> None:
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, AZIENDA_NOME, **_NL)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, AZIENDA_INDIRIZZO, **_NL)
    pdf.cell(0, 5, f"P.IVA: {AZIENDA_PIVA}", **_NL)
    pdf.ln(4)


def genera_pdf_ddt(ddt) -> Path:
    """Genera il PDF del DDT e restituisce il Path assoluto del file salvato.

    NOTA: deve essere chiamata all'interno di una sessione SQLAlchemy attiva,
    perché accede a relazioni lazy (ddt.ordine, ordine.cliente, ordine.righe).
    """
    DDT_DIR.mkdir(parents=True, exist_ok=True)

    ordine = ddt.ordine
    cliente = ordine.cliente

    # Indirizzo spedizione: preferisce 'spedizione', fallback 'sede_legale'
    addr = next(
        (i for i in cliente.indirizzi if i.tipo.value == "spedizione"),
        next((i for i in cliente.indirizzi if i.tipo.value == "sede_legale"), None),
    )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    _intestazione_emittente(pdf)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"DOCUMENTO DI TRASPORTO  N. {ddt.numero}", **_NL)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, f"Data: {ddt.data}", **_NL)
    pdf.cell(0, 5, f"Ordine di riferimento: {ordine.numero}", **_NL)
    pdf.ln(4)

    # Destinatario
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "DESTINATARIO", **_NL)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, cliente.ragione_sociale, **_NL)
    if addr:
        pdf.cell(0, 5, f"{addr.via}", **_NL)
        pdf.cell(0, 5, f"{addr.cap} {addr.citta} ({addr.provincia})", **_NL)
    pdf.ln(4)

    # Tabella merci
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 7, "Codice", border=1, fill=True)
    pdf.cell(100, 7, "Descrizione", border=1, fill=True)
    pdf.cell(30, 7, "Quantita", border=1, fill=True, **_NL)

    pdf.set_font("Helvetica", size=10)
    for riga in ordine.righe:
        pdf.cell(30, 6, riga.articolo.codice, border=1)
        pdf.cell(100, 6, riga.articolo.descrizione[:60], border=1)
        pdf.cell(30, 6, str(riga.quantita), border=1, **_NL)

    pdf.ln(6)

    # Note e firma
    if ddt.note:
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, f"Note: {ddt.note}")
        pdf.ln(2)

    pdf.set_font("Helvetica", size=10)
    pdf.ln(10)
    pdf.cell(60, 5, "Firma autista: _____________________")

    dest = DDT_DIR / f"{ddt.numero}.pdf"
    pdf.output(str(dest))
    return dest


def genera_pdf_fattura(fattura) -> Path:
    """Genera il PDF della Fattura e restituisce il Path assoluto del file salvato.

    NOTA: deve essere chiamata all'interno di una sessione SQLAlchemy attiva,
    perché accede a relazioni lazy (fattura.cliente, fattura.righe, fattura.ddt_collegati).
    """
    FATTURE_DIR.mkdir(parents=True, exist_ok=True)

    cliente = fattura.cliente

    # Indirizzo fatturazione: preferisce 'fatturazione', fallback 'sede_legale'
    addr = next(
        (i for i in cliente.indirizzi if i.tipo.value == "fatturazione"),
        next((i for i in cliente.indirizzi if i.tipo.value == "sede_legale"), None),
    )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    _intestazione_emittente(pdf)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"FATTURA  N. {fattura.numero}", **_NL)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, f"Data: {fattura.data}", **_NL)
    pdf.ln(4)

    # Cliente
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "CLIENTE", **_NL)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 5, cliente.ragione_sociale, **_NL)
    if addr:
        pdf.cell(0, 5, f"{addr.via}", **_NL)
        pdf.cell(0, 5, f"{addr.cap} {addr.citta} ({addr.provincia})", **_NL)
    pdf.ln(4)

    # DDT collegati
    if fattura.ddt_collegati:
        pdf.set_font("Helvetica", "I", 9)
        numeri = ", ".join(d.numero for d in fattura.ddt_collegati)
        pdf.cell(0, 5, f"DDT di riferimento: {numeri}", **_NL)
        pdf.ln(2)

    # Tabella righe
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(28, 7, "Codice", border=1, fill=True)
    pdf.cell(72, 7, "Descrizione", border=1, fill=True)
    pdf.cell(15, 7, "Qty", border=1, fill=True)
    pdf.cell(22, 7, "Prezzo", border=1, fill=True)
    pdf.cell(15, 7, "IVA%", border=1, fill=True)
    pdf.cell(24, 7, "Imponibile", border=1, fill=True, **_NL)

    pdf.set_font("Helvetica", size=9)
    for riga in fattura.righe:
        imponibile = riga.quantita * riga.prezzo_unitario
        pdf.cell(28, 6, riga.articolo.codice, border=1)
        pdf.cell(72, 6, riga.articolo.descrizione[:45], border=1)
        pdf.cell(15, 6, str(riga.quantita), border=1)
        pdf.cell(22, 6, f"EUR{riga.prezzo_unitario:.2f}", border=1)
        pdf.cell(15, 6, f"{riga.aliquota_iva*100:.0f}%", border=1)
        pdf.cell(24, 6, f"EUR{imponibile:.2f}", border=1, **_NL)

    pdf.ln(4)

    # Riepilogo IVA per aliquota
    riepilogo: dict[float, float] = defaultdict(float)
    totale_imponibile = 0.0
    for riga in fattura.righe:
        imp = riga.quantita * riga.prezzo_unitario
        totale_imponibile += imp
        riepilogo[riga.aliquota_iva] += imp

    totale_iva = sum(imp * aliq for aliq, imp in riepilogo.items())

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Riepilogo IVA:", **_NL)
    pdf.set_font("Helvetica", size=9)
    for aliq, imp in sorted(riepilogo.items()):
        iva = imp * aliq
        pdf.cell(0, 5, f"  Aliquota {aliq*100:.0f}%: imponibile EUR{imp:.2f} - IVA EUR{iva:.2f}", **_NL)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Totale imponibile: EUR{totale_imponibile:.2f}", **_NL)
    pdf.cell(0, 6, f"Totale IVA:        EUR{totale_iva:.2f}", **_NL)
    pdf.cell(0, 6, f"TOTALE DOCUMENTO:  EUR{totale_imponibile + totale_iva:.2f}", **_NL)

    if fattura.note:
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 5, f"Note: {fattura.note}")

    dest = FATTURE_DIR / f"{fattura.numero}.pdf"
    pdf.output(str(dest))
    return dest
```

- [ ] **Step 6: Run test to verify it passes**

```
uv run --no-sync python -m pytest tests/test_documenti_pdf.py -v
```
Expected: 2 PASSED

- [ ] **Step 7: Run full suite**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green

- [ ] **Step 8: Commit**

```bash
git add erpclaw/config.py erpclaw/documenti_pdf.py tests/test_documenti_pdf.py pyproject.toml
git commit -m "feat: add PDF generation for DDT and Fatture (fpdf2)"
```

---

## Chunk 3: Agent tools — DDT

### Task 4: DDT tools in `documenti_tools.py`

**Files:**
- Create: `erpclaw/documenti_tools.py` (DDT section)
- Test: `tests/test_documenti_tools_ddt.py`

- [ ] **Step 1: Write failing DDT tool tests**

```python
# tests/test_documenti_tools_ddt.py
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import erpclaw.documenti_db  # noqa: registers models
from erpclaw.erp_db import Base, Articolo, Cliente, Ordine, RigaOrdine, StatoOrdine
from erpclaw.documenti_db import DDT


def make_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def tools():
    eng = make_engine()
    def make_session():
        return Session(eng)
    with patch("erpclaw.documenti_tools.get_session", side_effect=make_session):
        from erpclaw.documenti_tools import DocumentiTools
        yield DocumentiTools(), make_session


@pytest.fixture
def tools_con_ordine(tools):
    t, make_session = tools
    with make_session() as s:
        c = Cliente(codice="C1", ragione_sociale="Cliente SRL")
        s.add(c)
        s.flush()
        a = Articolo(codice="A1", descrizione="Art", prezzo_vendita=10.0, aliquota_iva=0.22)
        s.add(a)
        s.flush()
        o = Ordine(numero="ORD-0001", data=date.today(),
                   cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o)
        s.flush()
        r = RigaOrdine(ordine_id=o.id, articolo_id=a.id,
                       quantita=5, prezzo_unitario=10.0)
        s.add(r)
        s.commit()
    return t, make_session


def test_crea_ddt_ok(tools_con_ordine):
    t, _ = tools_con_ordine
    result = t.crea_ddt("ORD-0001")
    assert "DDT-" in result
    assert "bozza" in result.lower()


def test_crea_ddt_ordine_non_spedito(tools_con_ordine):
    t, make_session = tools_con_ordine
    with make_session() as s:
        o = s.query(Ordine).filter_by(numero="ORD-0001").first()
        o.stato = StatoOrdine.confermato
        s.commit()
    result = t.crea_ddt("ORD-0001")
    assert "errore" in result.lower()


def test_crea_ddt_duplicato(tools_con_ordine):
    t, _ = tools_con_ordine
    t.crea_ddt("ORD-0001")
    result = t.crea_ddt("ORD-0001")
    assert "errore" in result.lower() or "già" in result.lower()


def test_crea_ddt_ordine_non_trovato(tools_con_ordine):
    t, _ = tools_con_ordine
    result = t.crea_ddt("ORD-9999")
    assert "errore" in result.lower() or "non trovato" in result.lower()


def _estrai_numero_ddt(result: str) -> str:
    """Estrae il numero DDT dal risultato di crea_ddt (es. 'DDT **DDT-20260316-001** ...')."""
    import re
    m = re.search(r"DDT-\d{8}-\d{3}", result)
    assert m, f"Numero DDT non trovato in: {result}"
    return m.group(0)


def test_emetti_ddt(tools_con_ordine, tmp_path):
    t, _ = tools_con_ordine
    crea_result = t.crea_ddt("ORD-0001")
    numero_ddt = _estrai_numero_ddt(crea_result)
    import erpclaw.documenti_pdf as pdf_mod
    with patch.object(pdf_mod, "DDT_DIR", tmp_path / "ddt"):
        result = t.emetti_ddt(numero_ddt)
    assert "emesso" in result.lower()


def test_emetti_ddt_non_trovato(tools_con_ordine):
    t, _ = tools_con_ordine
    result = t.emetti_ddt("DDT-XXXX")
    assert "errore" in result.lower() or "non trovato" in result.lower()


def test_lista_ddt(tools_con_ordine):
    t, _ = tools_con_ordine
    t.crea_ddt("ORD-0001")
    result = t.lista_ddt()
    assert "DDT-" in result


def test_lista_ddt_filtro_stato(tools_con_ordine, tmp_path):
    t, _ = tools_con_ordine
    crea_result = t.crea_ddt("ORD-0001")
    numero_ddt = _estrai_numero_ddt(crea_result)
    result_bozza = t.lista_ddt(stato="bozza")
    assert "DDT-" in result_bozza
    import erpclaw.documenti_pdf as pdf_mod
    with patch.object(pdf_mod, "DDT_DIR", tmp_path / "ddt"):
        t.emetti_ddt(numero_ddt)
    result_emesso = t.lista_ddt(stato="emesso")
    assert "DDT-" in result_emesso


def test_dettaglio_ddt(tools_con_ordine):
    t, _ = tools_con_ordine
    crea_result = t.crea_ddt("ORD-0001")
    numero_ddt = _estrai_numero_ddt(crea_result)
    result = t.dettaglio_ddt(numero_ddt)
    assert "A1" in result or "Art" in result
    assert "5" in result
```

- [ ] **Step 2: Run test to verify it fails**

```
uv run --no-sync python -m pytest tests/test_documenti_tools_ddt.py -v
```
Expected: `ModuleNotFoundError: No module named 'erpclaw.documenti_tools'`

- [ ] **Step 3: Create `erpclaw/documenti_tools.py`** (DDT portion only — Fattura tools added in Task 5)

```python
"""Agno Toolkit per DDT e Fatture."""

from datetime import date

from agno.tools import Toolkit

from erpclaw.documenti_db import (
    DDT, Fattura, RigaFattura, StatoDDT, StatoFattura,
    init_documenti_db,
)
from erpclaw.erp_db import get_session, Ordine, Cliente, StatoOrdine

init_documenti_db()


class DocumentiTools(Toolkit):
    def __init__(self):
        super().__init__(name="documenti_tools")
        self.register(self.crea_ddt)
        self.register(self.emetti_ddt)
        self.register(self.lista_ddt)
        self.register(self.dettaglio_ddt)
        self.register(self.crea_fattura)
        self.register(self.emetti_fattura)
        self.register(self.segna_fattura_pagata)
        self.register(self.lista_fatture)
        self.register(self.dettaglio_fattura)

    # ── DDT ───────────────────────────────────────────────────────────────────

    def crea_ddt(self, numero_ordine: str) -> str:
        """Crea un DDT in bozza per un ordine in stato 'spedito'. Un solo DDT per ordine."""
        with get_session() as s:
            ordine = s.query(Ordine).filter_by(numero=numero_ordine).first()
            if not ordine:
                return f"Errore: ordine {numero_ordine} non trovato."
            if ordine.stato != StatoOrdine.spedito:
                return f"Errore: l'ordine {numero_ordine} è in stato '{ordine.stato.value}', deve essere 'spedito'."
            if s.query(DDT).filter_by(ordine_id=ordine.id).first():
                return f"Errore: esiste già un DDT per l'ordine {numero_ordine}."
            oggi = date.today()
            count = s.query(DDT).filter(
                DDT.numero.like(f"DDT-{oggi.strftime('%Y%m%d')}-%")
            ).count()
            numero = f"DDT-{oggi.strftime('%Y%m%d')}-{count + 1:03d}"
            ddt = DDT(numero=numero, data=oggi, ordine_id=ordine.id)
            s.add(ddt)
            s.commit()
            ragione = ordine.cliente.ragione_sociale
        return f"DDT **{numero}** creato per {ragione} (ordine {numero_ordine}, stato: bozza) ✓"

    def emetti_ddt(self, numero_ddt: str) -> str:
        """Emette il DDT (bozza→emesso) e genera il PDF. Il PDF verrà salvato in ./documenti/ddt/."""
        with get_session() as s:
            ddt = s.query(DDT).filter_by(numero=numero_ddt).first()
            if not ddt:
                return f"Errore: DDT {numero_ddt} non trovato."
            if ddt.stato != StatoDDT.bozza:
                return f"Errore: il DDT {numero_ddt} è già in stato '{ddt.stato.value}'."
            from erpclaw.documenti_pdf import genera_pdf_ddt
            pdf_path = genera_pdf_ddt(ddt)
            ddt.stato = StatoDDT.emesso
            ddt.percorso_pdf = str(pdf_path)
            s.commit()
        return f"DDT **{numero_ddt}** emesso ✓\nPDF: `{pdf_path}`"

    def lista_ddt(self, stato: str = None) -> str:
        """Elenca i DDT, opzionalmente filtrati per stato (bozza/emesso)."""
        with get_session() as s:
            q = s.query(DDT)
            if stato:
                try:
                    q = q.filter(DDT.stato == StatoDDT(stato))
                except ValueError:
                    return f"Errore: stato '{stato}' non valido. Valori: bozza, emesso."
            ddts = q.order_by(DDT.numero).all()
            if not ddts:
                return "Nessun DDT trovato."
            rows = "\n".join(
                f"| {d.numero} | {d.data} | {d.ordine.numero} | {d.stato.value} |"
                for d in ddts
            )
        return f"| Numero | Data | Ordine | Stato |\n|--------|------|--------|-------|\n{rows}"

    def dettaglio_ddt(self, numero_ddt: str) -> str:
        """Mostra le righe del DDT (lette dall'ordine di riferimento)."""
        with get_session() as s:
            ddt = s.query(DDT).filter_by(numero=numero_ddt).first()
            if not ddt:
                return f"Errore: DDT {numero_ddt} non trovato."
            ordine = ddt.ordine
            header = (
                f"**DDT {ddt.numero}** — Ordine {ordine.numero}\n"
                f"Data: {ddt.data}  |  Stato: {ddt.stato.value}\n"
                f"Cliente: {ordine.cliente.ragione_sociale}\n\n"
                f"| Codice | Descrizione | Qtà |\n"
                f"|--------|-------------|-----|\n"
            )
            rows = "\n".join(
                f"| {r.articolo.codice} | {r.articolo.descrizione} | {r.quantita} |"
                for r in ordine.righe
            )
        return header + (rows if rows else "_Nessuna riga._")

    # ── FATTURE ───────────────────────────────────────────────────────────────

    def crea_fattura(self, numeri_ddt: str, note: str = "") -> str:
        """Crea una fattura da uno o più DDT (separati da virgola, es. 'DDT-001,DDT-002'). Copia le righe con snapshot IVA per articolo."""
        numeri = [n.strip() for n in numeri_ddt.split(",") if n.strip()]
        if not numeri:
            return "Errore: specificare almeno un numero DDT."
        with get_session() as s:
            ddts = []
            for num in numeri:
                ddt = s.query(DDT).filter_by(numero=num).first()
                if not ddt:
                    return f"Errore: DDT {num} non trovato."
                ddts.append(ddt)
            # Tutti i DDT devono appartenere allo stesso cliente
            clienti_ids = {ddt.ordine.cliente_id for ddt in ddts}
            if len(clienti_ids) > 1:
                return "Errore: i DDT appartengono a clienti diversi."
            cliente_id = clienti_ids.pop()
            oggi = date.today()
            count = s.query(Fattura).filter(
                Fattura.numero.like(f"FT-{oggi.year}-%")
            ).count()
            numero = f"FT-{oggi.year}-{count + 1:04d}"
            fattura = Fattura(
                numero=numero, data=oggi,
                cliente_id=cliente_id, note=note,
            )
            for ddt in ddts:
                fattura.ddt_collegati.append(ddt)
            s.add(fattura)
            s.flush()
            # Copia righe con snapshot IVA (una RigaFattura per RigaOrdine per DDT)
            for ddt in ddts:
                for riga in ddt.ordine.righe:
                    s.add(RigaFattura(
                        fattura_id=fattura.id,
                        articolo_id=riga.articolo_id,
                        quantita=riga.quantita,
                        prezzo_unitario=riga.prezzo_unitario,
                        aliquota_iva=riga.articolo.aliquota_iva,
                    ))
            s.commit()
            cliente_nome = s.get(Cliente, cliente_id).ragione_sociale
        return (
            f"Fattura **{numero}** creata per {cliente_nome} "
            f"(DDT: {', '.join(numeri)}, stato: bozza) ✓"
        )

    def emetti_fattura(self, numero_fattura: str) -> str:
        """Emette la fattura (bozza→emessa) e genera il PDF. Richiede almeno una riga."""
        with get_session() as s:
            fat = s.query(Fattura).filter_by(numero=numero_fattura).first()
            if not fat:
                return f"Errore: fattura {numero_fattura} non trovata."
            if fat.stato != StatoFattura.bozza:
                return f"Errore: la fattura {numero_fattura} è già in stato '{fat.stato.value}'."
            if not fat.righe:
                return f"Errore: la fattura {numero_fattura} non ha righe da fatturare."
            from erpclaw.documenti_pdf import genera_pdf_fattura
            pdf_path = genera_pdf_fattura(fat)
            fat.stato = StatoFattura.emessa
            fat.percorso_pdf = str(pdf_path)
            s.commit()
        return f"Fattura **{numero_fattura}** emessa ✓\nPDF: `{pdf_path}`"

    def segna_fattura_pagata(self, numero_fattura: str) -> str:
        """Segna la fattura come pagata (emessa→pagata)."""
        with get_session() as s:
            fat = s.query(Fattura).filter_by(numero=numero_fattura).first()
            if not fat:
                return f"Errore: fattura {numero_fattura} non trovata."
            if fat.stato != StatoFattura.emessa:
                return f"Errore: la fattura {numero_fattura} è in stato '{fat.stato.value}', deve essere 'emessa'."
            fat.stato = StatoFattura.pagata
            s.commit()
        return f"Fattura **{numero_fattura}** → stato **pagata** ✓"

    def lista_fatture(self, stato: str = None) -> str:
        """Elenca le fatture, opzionalmente filtrate per stato (bozza/emessa/pagata)."""
        with get_session() as s:
            q = s.query(Fattura)
            if stato:
                try:
                    q = q.filter(Fattura.stato == StatoFattura(stato))
                except ValueError:
                    return f"Errore: stato '{stato}' non valido. Valori: bozza, emessa, pagata."
            fatture = q.order_by(Fattura.numero).all()
            if not fatture:
                return "Nessuna fattura trovata."
            rows = "\n".join(
                f"| {f.numero} | {f.data} | {f.cliente.ragione_sociale} | {f.stato.value} |"
                for f in fatture
            )
        return f"| Numero | Data | Cliente | Stato |\n|--------|------|---------|-------|\n{rows}"

    def dettaglio_fattura(self, numero_fattura: str) -> str:
        """Mostra le righe, il riepilogo IVA e i totali di una fattura."""
        with get_session() as s:
            fat = s.query(Fattura).filter_by(numero=numero_fattura).first()
            if not fat:
                return f"Errore: fattura {numero_fattura} non trovata."
            header = (
                f"**Fattura {fat.numero}** — {fat.cliente.ragione_sociale}\n"
                f"Data: {fat.data}  |  Stato: {fat.stato.value}\n\n"
            )
            if fat.ddt_collegati:
                ddt_nums = ", ".join(d.numero for d in fat.ddt_collegati)
                header += f"DDT: {ddt_nums}\n\n"
            header += (
                "| Codice | Descrizione | Qtà | Prezzo | IVA% | Imponibile |\n"
                "|--------|-------------|-----|--------|------|------------|\n"
            )
            from collections import defaultdict
            riepilogo: dict[float, float] = defaultdict(float)
            totale_imp = 0.0
            rows = []
            for r in fat.righe:
                imp = r.quantita * r.prezzo_unitario
                totale_imp += imp
                riepilogo[r.aliquota_iva] += imp
                rows.append(
                    f"| {r.articolo.codice} | {r.articolo.descrizione} | "
                    f"{r.quantita} | €{r.prezzo_unitario:.2f} | "
                    f"{r.aliquota_iva*100:.0f}% | €{imp:.2f} |"
                )
            totale_iva = sum(imp * aliq for aliq, imp in riepilogo.items())
            iva_lines = "\n".join(
                f"  IVA {aliq*100:.0f}%: €{imp * aliq:.2f}"
                for aliq, imp in sorted(riepilogo.items())
            )
        return (
            header + "\n".join(rows) +
            f"\n\n**Totale imponibile: €{totale_imp:.2f}**\n" +
            iva_lines +
            f"\n**Totale IVA: €{totale_iva:.2f}**\n"
            f"**TOTALE DOCUMENTO: €{totale_imp + totale_iva:.2f}**"
        )
```

- [ ] **Step 4: Run DDT tool tests**

```
uv run --no-sync python -m pytest tests/test_documenti_tools_ddt.py -v
```
Expected: all PASSED (some tests involving `emetti_ddt` will need the DDT numero; adjust test to read it from `lista_ddt` output if needed)

- [ ] **Step 5: Run full suite**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green

- [ ] **Step 6: Commit**

```bash
git add erpclaw/documenti_tools.py tests/test_documenti_tools_ddt.py
git commit -m "feat: add DocumentiTools with DDT and Fattura agent tools"
```

---

### Task 5: Fattura tool tests

**Files:**
- Test: `tests/test_documenti_tools_fattura.py`

- [ ] **Step 1: Write failing Fattura tool tests**

```python
# tests/test_documenti_tools_fattura.py
import pytest
from datetime import date
from unittest.mock import patch
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import erpclaw.documenti_db  # noqa
from erpclaw.erp_db import Base, Articolo, Cliente, Ordine, RigaOrdine, StatoOrdine
from erpclaw.documenti_db import DDT, StatoDDT


def make_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def tools_con_ddt(tmp_path):
    eng = make_engine()
    def make_session():
        return Session(eng)
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Cliente SRL")
        s.add(c)
        s.flush()
        a = Articolo(codice="A1", descrizione="Art", prezzo_vendita=100.0, aliquota_iva=0.22)
        s.add(a)
        s.flush()
        o = Ordine(numero="ORD-0001", data=date.today(),
                   cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o)
        s.flush()
        r = RigaOrdine(ordine_id=o.id, articolo_id=a.id,
                       quantita=2, prezzo_unitario=100.0)
        s.add(r)
        ddt = DDT(numero="DDT-20260316-001", data=date.today(), ordine_id=o.id)
        s.add(ddt)
        s.commit()
    with patch("erpclaw.documenti_tools.get_session", side_effect=make_session):
        from erpclaw.documenti_tools import DocumentiTools
        yield DocumentiTools(), make_session, tmp_path


def _estrai_numero_fattura(result: str) -> str:
    """Estrae il numero fattura dal risultato di crea_fattura (es. 'FT-2026-0001')."""
    import re
    m = re.search(r"FT-\d{4}-\d{4}", result)
    assert m, f"Numero fattura non trovato in: {result}"
    return m.group(0)


def test_crea_fattura_ok(tools_con_ddt):
    t, _, _ = tools_con_ddt
    result = t.crea_fattura("DDT-20260316-001")
    assert "FT-" in result
    assert "bozza" in result.lower()


def test_crea_fattura_ddt_non_trovato(tools_con_ddt):
    t, _, _ = tools_con_ddt
    result = t.crea_fattura("DDT-XXXX")
    assert "errore" in result.lower() or "non trovato" in result.lower()


def test_crea_fattura_multipli_ddt(tools_con_ddt):
    """Verifica parsing comma-separated string."""
    t, make_session, _ = tools_con_ddt
    # Aggiungi secondo ordine + DDT
    with make_session() as s:
        c = s.query(Cliente).filter_by(codice="C1").first()
        a = s.query(Articolo).filter_by(codice="A1").first()
        o2 = Ordine(numero="ORD-0002", data=date.today(),
                    cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o2)
        s.flush()
        s.add(RigaOrdine(ordine_id=o2.id, articolo_id=a.id,
                         quantita=1, prezzo_unitario=100.0))
        s.add(DDT(numero="DDT-20260316-002", data=date.today(), ordine_id=o2.id))
        s.commit()
    result = t.crea_fattura("DDT-20260316-001, DDT-20260316-002")
    assert "FT-" in result
    assert "DDT-20260316-001" in result and "DDT-20260316-002" in result


def test_emetti_fattura_ok(tools_con_ddt):
    t, _, tmp_path = tools_con_ddt
    crea_result = t.crea_fattura("DDT-20260316-001")
    numero_fat = _estrai_numero_fattura(crea_result)
    import erpclaw.documenti_pdf as pdf_mod
    with patch.object(pdf_mod, "FATTURE_DIR", tmp_path / "fatture"):
        result = t.emetti_fattura(numero_fat)
    assert "emessa" in result.lower()


def test_emetti_fattura_vuota(tools_con_ddt):
    """Fattura creata manualmente senza righe non può essere emessa."""
    t, make_session, _ = tools_con_ddt
    from erpclaw.documenti_db import Fattura
    with make_session() as s:
        c = s.query(Cliente).filter_by(codice="C1").first()
        s.add(Fattura(numero="FT-VUOTA", data=date.today(), cliente_id=c.id))
        s.commit()
    result = t.emetti_fattura("FT-VUOTA")
    assert "errore" in result.lower() or "nessuna riga" in result.lower()


def test_segna_fattura_pagata(tools_con_ddt):
    t, _, tmp_path = tools_con_ddt
    crea_result = t.crea_fattura("DDT-20260316-001")
    numero_fat = _estrai_numero_fattura(crea_result)
    import erpclaw.documenti_pdf as pdf_mod
    with patch.object(pdf_mod, "FATTURE_DIR", tmp_path / "fatture"):
        t.emetti_fattura(numero_fat)
    result = t.segna_fattura_pagata(numero_fat)
    assert "pagata" in result.lower()


def test_segna_pagata_su_bozza_errore(tools_con_ddt):
    t, _, _ = tools_con_ddt
    crea_result = t.crea_fattura("DDT-20260316-001")
    numero_fat = _estrai_numero_fattura(crea_result)
    result = t.segna_fattura_pagata(numero_fat)  # è ancora bozza
    assert "errore" in result.lower()


def test_lista_fatture(tools_con_ddt):
    t, _, _ = tools_con_ddt
    t.crea_fattura("DDT-20260316-001")
    result = t.lista_fatture()
    assert "FT-" in result


def test_dettaglio_fattura(tools_con_ddt):
    t, _, _ = tools_con_ddt
    crea_result = t.crea_fattura("DDT-20260316-001")
    numero_fat = _estrai_numero_fattura(crea_result)
    result = t.dettaglio_fattura(numero_fat)
    assert "A1" in result or "Art" in result
    assert "22" in result  # aliquota IVA
    assert "200" in result or "244" in result  # totale o imponibile 2x100
```

- [ ] **Step 2: Run tests**

```
uv run --no-sync python -m pytest tests/test_documenti_tools_fattura.py -v
```
Expected: all PASSED

- [ ] **Step 3: Run full suite**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green

- [ ] **Step 4: Commit**

```bash
git add tests/test_documenti_tools_fattura.py
git commit -m "test: add Fattura tool tests"
```

---

## Chunk 4: Web integration + wiring

### Task 6: Create `documenti_web.py`

**Files:**
- Create: `erpclaw/documenti_web.py`
- Test: `tests/test_documenti_web.py`

- [ ] **Step 1: Write failing web endpoint test**

```python
# tests/test_documenti_web.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import date

import erpclaw.documenti_db  # noqa
from erpclaw.erp_db import Base, Cliente, Ordine, StatoOrdine
from erpclaw.documenti_db import DDT, Fattura, StatoDDT, StatoFattura


def make_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def test_download_ddt_pdf(tmp_path):
    # Crea PDF finto
    ddt_dir = tmp_path / "ddt"
    ddt_dir.mkdir()
    pdf_file = ddt_dir / "DDT-20260316-001.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    eng = make_engine()
    def make_session():
        return Session(eng)
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Test")
        s.add(c)
        s.flush()
        o = Ordine(numero="ORD-0001", data=date.today(),
                   cliente_id=c.id, stato=StatoOrdine.spedito)
        s.add(o)
        s.flush()
        ddt = DDT(numero="DDT-20260316-001", data=date.today(),
                  ordine_id=o.id, stato=StatoDDT.emesso,
                  percorso_pdf=str(pdf_file))
        s.add(ddt)
        s.commit()

    from fastapi import FastAPI
    app = FastAPI()
    with patch("erpclaw.documenti_web.get_session", side_effect=make_session):
        from erpclaw.documenti_web import router
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/documenti/ddt/DDT-20260316-001/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_download_ddt_pdf_non_trovato():
    eng = make_engine()
    def make_session():
        return Session(eng)

    from fastapi import FastAPI
    app = FastAPI()
    with patch("erpclaw.documenti_web.get_session", side_effect=make_session):
        from erpclaw.documenti_web import router
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/documenti/ddt/DDT-XXXX/pdf")
    assert resp.status_code == 404


def test_download_fattura_pdf(tmp_path):
    fat_dir = tmp_path / "fatture"
    fat_dir.mkdir()
    pdf_file = fat_dir / "FT-2026-0001.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")

    eng = make_engine()
    def make_session():
        return Session(eng)
    with Session(eng) as s:
        c = Cliente(codice="C1", ragione_sociale="Test")
        s.add(c)
        s.flush()
        fat = Fattura(numero="FT-2026-0001", data=date.today(),
                      cliente_id=c.id, stato=StatoFattura.emessa,
                      percorso_pdf=str(pdf_file))
        s.add(fat)
        s.commit()

    from fastapi import FastAPI
    app = FastAPI()
    with patch("erpclaw.documenti_web.get_session", side_effect=make_session):
        from erpclaw.documenti_web import router
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/documenti/fatture/FT-2026-0001/pdf")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

```
uv run --no-sync python -m pytest tests/test_documenti_web.py -v
```
Expected: `ModuleNotFoundError: No module named 'erpclaw.documenti_web'`

- [ ] **Step 3: Create `erpclaw/documenti_web.py`**

```python
"""FastAPI router per il download di PDF DDT e Fatture."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from erpclaw.documenti_db import DDT, Fattura
from erpclaw.erp_db import get_session

router = APIRouter(prefix="/documenti", tags=["documenti"])


@router.get("/ddt/{numero}/pdf")
def scarica_pdf_ddt(numero: str):
    """Scarica il PDF di un DDT emesso."""
    with get_session() as s:
        ddt = s.query(DDT).filter_by(numero=numero).first()
        if not ddt:
            raise HTTPException(status_code=404, detail=f"DDT {numero} non trovato.")
        percorso = ddt.percorso_pdf  # capture primitive inside session
    if not percorso:
        raise HTTPException(status_code=404, detail=f"PDF non ancora generato per DDT {numero}.")
    path = Path(percorso)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File PDF non trovato su disco.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.get("/fatture/{numero}/pdf")
def scarica_pdf_fattura(numero: str):
    """Scarica il PDF di una fattura emessa."""
    with get_session() as s:
        fat = s.query(Fattura).filter_by(numero=numero).first()
        if not fat:
            raise HTTPException(status_code=404, detail=f"Fattura {numero} non trovata.")
        percorso = fat.percorso_pdf  # capture primitive inside session
    if not percorso:
        raise HTTPException(status_code=404, detail=f"PDF non ancora generato per fattura {numero}.")
    path = Path(percorso)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File PDF non trovato su disco.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
```

- [ ] **Step 4: Run web tests**

```
uv run --no-sync python -m pytest tests/test_documenti_web.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Run full suite**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green

- [ ] **Step 6: Commit**

```bash
git add erpclaw/documenti_web.py tests/test_documenti_web.py
git commit -m "feat: add FastAPI download endpoints for DDT and Fattura PDFs"
```

---

### Task 7: Wire everything together (`web.py` + `agent.py`)

**Files:**
- Modify: `erpclaw/web.py`
- Modify: `erpclaw/agent.py`

- [ ] **Step 1: Update `erpclaw/web.py`**

Add imports at the top (after existing erp_db imports):
```python
import erpclaw.documenti_db  # noqa: registers DDT/Fattura models on Base
from erpclaw.documenti_db import DDT, Fattura
from erpclaw.documenti_web import router as documenti_router
```

After the `app.include_router(chat_router)` line, add:
```python
app.include_router(documenti_router)
```

Add two new SQLAdmin views after the last existing ModelView (e.g., after `MovimentoMagazzinoAdmin`):
```python
class DDTAdmin(ModelView, model=DDT):
    name = "DDT"
    name_plural = "DDT"
    icon = "fa-solid fa-truck-fast"
    column_list = [DDT.numero, DDT.data, DDT.ordine, DDT.stato]
    column_searchable_list = [DDT.numero]
    column_sortable_list = [DDT.numero, DDT.data, DDT.stato]
    column_details_list = [DDT.numero, DDT.data, DDT.ordine, DDT.stato, DDT.percorso_pdf, DDT.note]


class FatturaAdmin(ModelView, model=Fattura):
    name = "Fattura"
    name_plural = "Fatture"
    icon = "fa-solid fa-file-invoice-dollar"
    column_list = [Fattura.numero, Fattura.data, Fattura.cliente, Fattura.stato]
    column_searchable_list = [Fattura.numero]
    column_sortable_list = [Fattura.numero, Fattura.data, Fattura.stato]
    column_details_list = [Fattura.numero, Fattura.data, Fattura.cliente, Fattura.stato, Fattura.percorso_pdf, Fattura.righe, Fattura.note]
```

- [ ] **Step 2: Update `erpclaw/agent.py`**

Add import after existing tool imports:
```python
from erpclaw.documenti_tools import DocumentiTools
```

In the `Team(...)` constructor, update the `tools` list from:
```python
tools=[ERPTools(), LogisticaTools()],
```
to:
```python
tools=[ERPTools(), LogisticaTools(), DocumentiTools()],
```

Add DDT/Fattura instructions to the team's `instructions` string, after the logistica section:
```
Gestione DDT e Fatture:
- Crea un DDT con crea_ddt quando un ordine viene spedito (stato 'spedito').
- Emetti il DDT con emetti_ddt per generare il PDF.
- Crea una fattura con crea_fattura fornendo i numeri DDT separati da virgola.
- Emetti la fattura con emetti_fattura per generare il PDF.
- I PDF sono scaricabili dal pannello web /admin.
- Segna la fattura come pagata con segna_fattura_pagata quando il pagamento è ricevuto.
```

- [ ] **Step 3: Smoke test — import the web app without errors**

```
uv run --no-sync python -c "from erpclaw.web import app; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Smoke test — import agent without errors**

```
uv run --no-sync python -c "from erpclaw.agent import team; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Run full test suite**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green

- [ ] **Step 6: Commit**

```bash
git add erpclaw/web.py erpclaw/agent.py
git commit -m "feat: wire DocumentiTools into agent team and web admin"
```

---

## Chunk 5: Docs

### Task 8: Update CLAUDE.md and .env documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.env` (add AZIENDA_ vars as comments/examples)

- [ ] **Step 1: Add AZIENDA vars to `.env`**

Append to `.env` (as commented examples — actual values are blank by default):
```
# Dati emittente per DDT e Fatture (opzionali, default: [Da configurare])
# AZIENDA_NOME=La Mia Azienda SRL
# AZIENDA_INDIRIZZO=Via Roma 1, 20100 Milano (MI)
# AZIENDA_PIVA=IT12345678901
```

- [ ] **Step 2: Update `CLAUDE.md`**

In the `#### erp.db tables` section, add a new row to the table:
```
| Documents | `ddt`, `fatture`, `righe_fattura`, `fatture_ddt` |
```

In the `### Key Files` section, add entries for new files:
```
- `erpclaw/documenti_db.py` — SQLAlchemy models `DDT`, `Fattura`, `RigaFattura`, association table `fatture_ddt`. Imports `Base` and `engine` from `erp_db.py` (shared DB). `init_documenti_db()` called at import of `documenti_tools.py`.
- `erpclaw/documenti_tools.py` — `DocumentiTools(Toolkit)`: 9 tools for DDT and Fattura lifecycle (crea_ddt, emetti_ddt, lista_ddt, dettaglio_ddt, crea_fattura, emetti_fattura, segna_fattura_pagata, lista_fatture, dettaglio_fattura). `crea_fattura` accepts comma-separated DDT numbers as a string for LM Studio compatibility.
- `erpclaw/documenti_pdf.py` — PDF generation with `fpdf2`. Uses absolute paths (`Path(__file__).parent.parent / "documenti"`). Reads AZIENDA_* from config.
- `erpclaw/documenti_web.py` — FastAPI router `GET /documenti/ddt/{numero}/pdf` and `GET /documenti/fatture/{numero}/pdf`.
```

Add a section on order status lifecycle update:
```
When an order is marked `spedito`, the agent should:
1. Propose running `scarica_ordine_da_ubicazione` to discharge warehouse stock
2. Propose creating a DDT with `crea_ddt` and emitting it with `emetti_ddt`
```

In the Environment Variables section, add:
```
- `AZIENDA_NOME` — Company name for PDF headers (optional, default: `[Da configurare]`)
- `AZIENDA_INDIRIZZO` — Company address for PDF headers (optional)
- `AZIENDA_PIVA` — Company VAT number for PDF headers (optional)
```

In the `Articolo` description, note:
```
`Articolo.aliquota_iva` (Float, not null, default 0.22) — IVA rate used in Fattura PDF and RigaFattura snapshot.
```

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md .env
git commit -m "docs: update CLAUDE.md with DDT/Fattura architecture and env vars"
```

---

## Final verification

- [ ] **Run the complete test suite one last time**

```
uv run --no-sync python -m pytest tests/ -v
```
Expected: all green, no warnings about missing tables or import errors

- [ ] **Verify DB tables are created correctly**

```
uv run --no-sync python -c "
from erpclaw.erp_db import init_db, engine
import erpclaw.documenti_db
init_db()
from sqlalchemy import inspect
i = inspect(engine)
tables = i.get_table_names()
print('Tables:', sorted(tables))
assert 'ddt' in tables
assert 'fatture' in tables
assert 'righe_fattura' in tables
assert 'fatture_ddt' in tables
assert 'articoli' in tables
print('OK - all DDT/Fattura tables present')
"
```
Expected: lists all tables including `ddt`, `fatture`, `righe_fattura`, `fatture_ddt`

- [ ] **Final commit if any cleanup needed, otherwise done**

```bash
git log --oneline -10
```
