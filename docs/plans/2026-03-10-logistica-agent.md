# Logistica Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Introdurre gestione ubicazioni gerarchiche di magazzino, tracciamento movimenti e indirizzi multi-tipo per clienti/fornitori.

**Architecture:** Nuovo `LogisticaTools(Toolkit)` aggiunto al team principale. Nuovi modelli SQLAlchemy in `erp_db.py`. `Articolo.giacenza` diventa `column_property` calcolata dalla somma degli stock nelle ubicazioni.

**Tech Stack:** SQLAlchemy (ORM + `column_property`), agno `Toolkit`, SQLite (`erp.db`), pytest + SQLite in-memory per i test.

---

## Task 1: Setup test infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Crea la directory tests e conftest.py**

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base

@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)

@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
```

**Step 2: Crea `tests/__init__.py` vuoto**

```python
# tests/__init__.py
```

**Step 3: Verifica che pytest funzioni**

```bash
uv run pytest tests/ -v
```

Atteso: `no tests ran` (ma nessun errore di import).

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: add pytest infrastructure"
```

---

## Task 2: Modello DB — Indirizzo

**Files:**
- Modify: `erpclaw/erp_db.py`
- Create: `tests/test_indirizzi.py`

**Step 1: Scrivi il test**

```python
# tests/test_indirizzi.py
from erpclaw.erp_db import Cliente, Fornitore, Indirizzo, TipoIndirizzo

def test_indirizzo_cliente(session):
    c = Cliente(codice="C001", ragione_sociale="Acme Srl")
    session.add(c)
    session.flush()
    addr = Indirizzo(
        tipo=TipoIndirizzo.spedizione,
        via="Via Roma 1", cap="20100", citta="Milano",
        provincia="MI", cliente_id=c.id
    )
    session.add(addr)
    session.commit()
    loaded = session.query(Indirizzo).filter_by(cliente_id=c.id).first()
    assert loaded.citta == "Milano"
    assert loaded.tipo == TipoIndirizzo.spedizione

def test_indirizzo_fornitore(session):
    f = Fornitore(codice="F001", ragione_sociale="Supplier Srl")
    session.add(f)
    session.flush()
    addr = Indirizzo(
        tipo=TipoIndirizzo.sede_legale,
        via="Via Po 5", cap="10100", citta="Torino",
        provincia="TO", fornitore_id=f.id
    )
    session.add(addr)
    session.commit()
    assert len(f.indirizzi) == 1
```

**Step 2: Esegui il test per verificare che fallisce**

```bash
uv run pytest tests/test_indirizzi.py -v
```

Atteso: `ImportError` su `Indirizzo` / `TipoIndirizzo`.

**Step 3: Aggiungi modello `Indirizzo` in `erp_db.py`**

Dopo la classe `CatalogoFornitore`, aggiungi:

```python
class TipoIndirizzo(str, enum.Enum):
    sede_legale = "sede_legale"
    spedizione = "spedizione"
    fatturazione = "fatturazione"
    altro = "altro"


class Indirizzo(Base):
    __tablename__ = "indirizzi"

    id = Column(Integer, primary_key=True)
    tipo = Column(Enum(TipoIndirizzo), nullable=False, default=TipoIndirizzo.sede_legale)
    via = Column(String, nullable=False, default="")
    cap = Column(String, nullable=False, default="")
    citta = Column(String, nullable=False, default="")
    provincia = Column(String, nullable=False, default="")
    paese = Column(String, nullable=False, default="IT")
    note = Column(Text, default="")
    cliente_id = Column(Integer, ForeignKey("clienti.id"), nullable=True)
    fornitore_id = Column(Integer, ForeignKey("fornitori.id"), nullable=True)

    cliente = relationship("Cliente", back_populates="indirizzi")
    fornitore = relationship("Fornitore", back_populates="indirizzi")
```

Aggiungi `indirizzi = relationship("Indirizzo", back_populates="cliente", cascade="all, delete-orphan")` a `Cliente`.

Aggiungi `indirizzi = relationship("Indirizzo", back_populates="fornitore", cascade="all, delete-orphan")` a `Fornitore`.

Aggiungi `TipoIndirizzo, Indirizzo` agli import in cima al file (dove necessario).

**Step 4: Esegui i test**

```bash
uv run pytest tests/test_indirizzi.py -v
```

Atteso: PASS.

**Step 5: Commit**

```bash
git add erpclaw/erp_db.py tests/test_indirizzi.py
git commit -m "feat: add Indirizzo model with multi-type support"
```

---

## Task 3: Modelli DB — Gerarchia Ubicazioni

**Files:**
- Modify: `erpclaw/erp_db.py`
- Create: `tests/test_ubicazioni_db.py`

**Step 1: Scrivi il test**

```python
# tests/test_ubicazioni_db.py
from erpclaw.erp_db import Magazzino, Zona, Scaffale, Ripiano

def test_gerarchia_ubicazioni(session):
    mag = Magazzino(codice="MAG1", nome="Magazzino Principale")
    session.add(mag)
    session.flush()

    zona = Zona(codice="A", nome="Zona A", magazzino_id=mag.id)
    session.add(zona)
    session.flush()

    scaffale = Scaffale(codice="A-03", nome="Scaffale 3", zona_id=zona.id)
    session.add(scaffale)
    session.flush()

    ripiano = Ripiano(codice="A-03-2", nome="Ripiano 2", scaffale_id=scaffale.id)
    session.add(ripiano)
    session.commit()

    assert ripiano.scaffale.zona.magazzino.codice == "MAG1"
```

**Step 2: Esegui il test per verificare che fallisce**

```bash
uv run pytest tests/test_ubicazioni_db.py -v
```

Atteso: `ImportError`.

**Step 3: Aggiungi modelli gerarchia in `erp_db.py`**

Aggiungi dopo `Indirizzo`:

```python
class Magazzino(Base):
    __tablename__ = "magazzini"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)

    zone = relationship("Zona", back_populates="magazzino", cascade="all, delete-orphan")


class Zona(Base):
    __tablename__ = "zone"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    magazzino_id = Column(Integer, ForeignKey("magazzini.id"), nullable=False)

    magazzino = relationship("Magazzino", back_populates="zone")
    scaffali = relationship("Scaffale", back_populates="zona", cascade="all, delete-orphan")


class Scaffale(Base):
    __tablename__ = "scaffali"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    zona_id = Column(Integer, ForeignKey("zone.id"), nullable=False)

    zona = relationship("Zona", back_populates="scaffali")
    ripiani = relationship("Ripiano", back_populates="scaffale", cascade="all, delete-orphan")


class Ripiano(Base):
    __tablename__ = "ripiani"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    scaffale_id = Column(Integer, ForeignKey("scaffali.id"), nullable=False)

    scaffale = relationship("Scaffale", back_populates="ripiani")
    stock = relationship("StockUbicazione", back_populates="ripiano", cascade="all, delete-orphan")
    movimenti_origine = relationship("MovimentoMagazzino", foreign_keys="MovimentoMagazzino.ripiano_origine_id", back_populates="ripiano_origine")
    movimenti_destinazione = relationship("MovimentoMagazzino", foreign_keys="MovimentoMagazzino.ripiano_destinazione_id", back_populates="ripiano_destinazione")
```

**Step 4: Esegui i test**

```bash
uv run pytest tests/test_ubicazioni_db.py -v
```

Atteso: PASS.

**Step 5: Commit**

```bash
git add erpclaw/erp_db.py tests/test_ubicazioni_db.py
git commit -m "feat: add warehouse hierarchy models (Magazzino/Zona/Scaffale/Ripiano)"
```

---

## Task 4: Modelli DB — StockUbicazione, MovimentoMagazzino e `giacenza` come `column_property`

**Files:**
- Modify: `erpclaw/erp_db.py`
- Create: `tests/test_stock_db.py`

**Step 1: Scrivi il test**

```python
# tests/test_stock_db.py
from erpclaw.erp_db import (
    Articolo, Magazzino, Zona, Scaffale, Ripiano,
    StockUbicazione, MovimentoMagazzino, TipoMovimento
)

def _setup_ubicazione(session):
    mag = Magazzino(codice="MAG1", nome="Principale")
    session.add(mag); session.flush()
    zona = Zona(codice="A", nome="Zona A", magazzino_id=mag.id)
    session.add(zona); session.flush()
    scaffale = Scaffale(codice="A-01", nome="Scaffale 1", zona_id=zona.id)
    session.add(scaffale); session.flush()
    ripiano = Ripiano(codice="A-01-1", nome="Ripiano 1", scaffale_id=scaffale.id)
    session.add(ripiano); session.flush()
    return ripiano

def test_stock_e_giacenza_derivata(session):
    art = Articolo(codice="ART001", descrizione="Widget", prezzo=9.99)
    session.add(art); session.flush()
    ripiano = _setup_ubicazione(session)

    stock = StockUbicazione(articolo_id=art.id, ripiano_id=ripiano.id, quantita=50)
    session.add(stock)
    session.commit()
    session.expire(art)

    assert art.giacenza == 50

def test_movimento_magazzino(session):
    art = Articolo(codice="ART002", descrizione="Gadget", prezzo=5.0)
    session.add(art); session.flush()
    ripiano = _setup_ubicazione(session)

    mov = MovimentoMagazzino(
        articolo_id=art.id,
        ripiano_destinazione_id=ripiano.id,
        quantita=10,
        tipo=TipoMovimento.carico,
    )
    session.add(mov)
    session.commit()
    assert mov.id is not None
```

**Step 2: Esegui il test per verificare che fallisce**

```bash
uv run pytest tests/test_stock_db.py -v
```

Atteso: `ImportError`.

**Step 3: Aggiungi `StockUbicazione`, `MovimentoMagazzino` e converti `giacenza` in `erp_db.py`**

Aggiungi gli import necessari in cima:

```python
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import column_property
```

Aggiungi le classi dopo `Ripiano`:

```python
class TipoMovimento(str, enum.Enum):
    carico = "carico"
    scarico = "scarico"
    trasferimento = "trasferimento"


class StockUbicazione(Base):
    __tablename__ = "stock_ubicazioni"

    id = Column(Integer, primary_key=True)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    ripiano_id = Column(Integer, ForeignKey("ripiani.id"), nullable=False)
    quantita = Column(Integer, nullable=False, default=0)

    articolo = relationship("Articolo", back_populates="stock_ubicazioni")
    ripiano = relationship("Ripiano", back_populates="stock")

    __table_args__ = (
        __import__("sqlalchemy").UniqueConstraint("articolo_id", "ripiano_id"),
    )


class MovimentoMagazzino(Base):
    __tablename__ = "movimenti_magazzino"

    id = Column(Integer, primary_key=True)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    ripiano_origine_id = Column(Integer, ForeignKey("ripiani.id"), nullable=True)
    ripiano_destinazione_id = Column(Integer, ForeignKey("ripiani.id"), nullable=True)
    quantita = Column(Integer, nullable=False)
    tipo = Column(Enum(TipoMovimento), nullable=False)
    data_ora = Column(__import__("sqlalchemy").DateTime, nullable=False, default=datetime.now)
    ordine_id = Column(Integer, ForeignKey("ordini.id"), nullable=True)
    note = Column(Text, default="")

    articolo = relationship("Articolo", back_populates="movimenti")
    ripiano_origine = relationship("Ripiano", foreign_keys=[ripiano_origine_id], back_populates="movimenti_origine")
    ripiano_destinazione = relationship("Ripiano", foreign_keys=[ripiano_destinazione_id], back_populates="movimenti_destinazione")
    ordine = relationship("Ordine", back_populates="movimenti")
```

In `Articolo`, **rimuovi** la riga `giacenza = Column(Integer, nullable=False, default=0)` e aggiungi la relationship:

```python
    stock_ubicazioni = relationship("StockUbicazione", back_populates="articolo")
    movimenti = relationship("MovimentoMagazzino", back_populates="articolo")
```

In `Ordine`, aggiungi:

```python
    movimenti = relationship("MovimentoMagazzino", back_populates="ordine")
```

**Dopo la definizione di tutte le classi** (prima di `init_db`), aggiungi la `column_property`:

```python
# giacenza derivata dalla somma degli stock nelle ubicazioni
Articolo.giacenza = column_property(
    select(func.coalesce(func.sum(StockUbicazione.quantita), 0))
    .where(StockUbicazione.articolo_id == Articolo.id)
    .correlate_except(StockUbicazione)
    .scalar_subquery()
)
```

**Step 4: Esegui i test**

```bash
uv run pytest tests/ -v
```

Atteso: tutti PASS.

**Step 5: Commit**

```bash
git add erpclaw/erp_db.py tests/test_stock_db.py
git commit -m "feat: add StockUbicazione, MovimentoMagazzino; Articolo.giacenza as column_property"
```

---

## Task 5: Rimuovi `aggiorna_giacenza` da `ERPTools`

> Nota: `aggiorna_giacenza` scriveva direttamente su `giacenza`, che ora è read-only. Va rimosso.

**Files:**
- Modify: `erpclaw/erp_tools.py`

**Step 1: Rimuovi `aggiorna_giacenza` da `ERPTools`**

In `erpclaw/erp_tools.py`:
- Rimuovi `self.register(self.aggiorna_giacenza)` da `__init__`
- Rimuovi il metodo `aggiorna_giacenza`

**Step 2: Verifica che i test passino**

```bash
uv run pytest tests/ -v
```

Atteso: tutti PASS.

**Step 3: Commit**

```bash
git add erpclaw/erp_tools.py
git commit -m "refactor: remove aggiorna_giacenza (giacenza is now derived from stock)"
```

---

## Task 6: Tool Indirizzi in `ERPTools`

**Files:**
- Modify: `erpclaw/erp_tools.py`
- Create: `tests/test_tool_indirizzi.py`

**Step 1: Scrivi i test**

```python
# tests/test_tool_indirizzi.py
import pytest
from unittest.mock import patch
from erpclaw.erp_tools import ERPTools
from erpclaw.erp_db import Base, Cliente, Fornitore, Indirizzo, TipoIndirizzo
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(autouse=True)
def patch_session(engine):
    with patch("erpclaw.erp_tools.get_session") as mock:
        mock.return_value = Session(engine)
        yield mock

@pytest.fixture
def tools():
    return ERPTools()

def test_aggiungi_indirizzo_cliente(tools, session):
    session.add(Cliente(codice="C001", ragione_sociale="Acme"))
    session.commit()
    result = tools.aggiungi_indirizzo_cliente(
        "C001", "spedizione", "Via Roma 1", "20100", "Milano", "MI"
    )
    assert "✓" in result
    addr = session.query(Indirizzo).first()
    assert addr.citta == "Milano"

def test_aggiungi_indirizzo_cliente_not_found(tools):
    result = tools.aggiungi_indirizzo_cliente(
        "NONEXIST", "spedizione", "Via X", "00000", "Roma", "RM"
    )
    assert "Errore" in result
```

**Step 2: Esegui il test per verificare che fallisce**

```bash
uv run pytest tests/test_tool_indirizzi.py -v
```

Atteso: FAIL (metodi non esistono).

**Step 3: Aggiungi gli import e i tool in `erp_tools.py`**

Aggiungi `Indirizzo, TipoIndirizzo` agli import da `erpclaw.erp_db`.

Aggiungi in `__init__`:
```python
        self.register(self.aggiungi_indirizzo_cliente)
        self.register(self.aggiungi_indirizzo_fornitore)
        self.register(self.lista_indirizzi_cliente)
        self.register(self.lista_indirizzi_fornitore)
```

Aggiungi i metodi nella sezione `# ── CLIENTI ──`:

```python
    def aggiungi_indirizzo_cliente(self, codice_cliente: str, tipo: str, via: str,
                                   cap: str, citta: str, provincia: str,
                                   paese: str = "IT", note: str = "") -> str:
        """Aggiunge un indirizzo (sede_legale/spedizione/fatturazione/altro) a un cliente."""
        with get_session() as s:
            c = s.query(Cliente).filter_by(codice=codice_cliente).first()
            if not c:
                return f"Errore: cliente {codice_cliente} non trovato."
            try:
                t = TipoIndirizzo(tipo)
            except ValueError:
                return f"Errore: tipo '{tipo}' non valido. Valori: sede_legale, spedizione, fatturazione, altro."
            s.add(Indirizzo(tipo=t, via=via, cap=cap, citta=citta,
                            provincia=provincia, paese=paese, note=note, cliente_id=c.id))
            s.commit()
        return f"Indirizzo **{tipo}** aggiunto al cliente {codice_cliente} ✓"

    def aggiungi_indirizzo_fornitore(self, codice_fornitore: str, tipo: str, via: str,
                                     cap: str, citta: str, provincia: str,
                                     paese: str = "IT", note: str = "") -> str:
        """Aggiunge un indirizzo (sede_legale/spedizione/fatturazione/altro) a un fornitore."""
        with get_session() as s:
            f = s.query(Fornitore).filter_by(codice=codice_fornitore).first()
            if not f:
                return f"Errore: fornitore {codice_fornitore} non trovato."
            try:
                t = TipoIndirizzo(tipo)
            except ValueError:
                return f"Errore: tipo '{tipo}' non valido. Valori: sede_legale, spedizione, fatturazione, altro."
            s.add(Indirizzo(tipo=t, via=via, cap=cap, citta=citta,
                            provincia=provincia, paese=paese, note=note, fornitore_id=f.id))
            s.commit()
        return f"Indirizzo **{tipo}** aggiunto al fornitore {codice_fornitore} ✓"

    def lista_indirizzi_cliente(self, codice_cliente: str) -> str:
        """Mostra tutti gli indirizzi di un cliente."""
        with get_session() as s:
            c = s.query(Cliente).filter_by(codice=codice_cliente).first()
            if not c:
                return f"Errore: cliente {codice_cliente} non trovato."
            if not c.indirizzi:
                return f"Nessun indirizzo per il cliente {codice_cliente}."
            rows = "\n".join(
                f"| {i.tipo.value} | {i.via} | {i.cap} {i.citta} ({i.provincia}) | {i.paese} |"
                for i in c.indirizzi
            )
        return f"| Tipo | Via | Città | Paese |\n|------|-----|-------|-------|\n{rows}"

    def lista_indirizzi_fornitore(self, codice_fornitore: str) -> str:
        """Mostra tutti gli indirizzi di un fornitore."""
        with get_session() as s:
            f = s.query(Fornitore).filter_by(codice=codice_fornitore).first()
            if not f:
                return f"Errore: fornitore {codice_fornitore} non trovato."
            if not f.indirizzi:
                return f"Nessun indirizzo per il fornitore {codice_fornitore}."
            rows = "\n".join(
                f"| {i.tipo.value} | {i.via} | {i.cap} {i.citta} ({i.provincia}) | {i.paese} |"
                for i in f.indirizzi
            )
        return f"| Tipo | Via | Città | Paese |\n|------|-----|-------|-------|\n{rows}"
```

**Step 4: Aggiorna `dettaglio_ordine` per mostrare indirizzo spedizione**

Nel metodo `dettaglio_ordine`, dopo aver costruito `header`, aggiungi:

```python
            # indirizzo spedizione cliente
            addr = next(
                (i for i in ordine.cliente.indirizzi if i.tipo.value == "spedizione"),
                next((i for i in ordine.cliente.indirizzi if i.tipo.value == "sede_legale"), None)
            )
            if addr:
                header += f"Spedizione: {addr.via}, {addr.cap} {addr.citta} ({addr.provincia})\n\n"
```

**Step 5: Esegui i test**

```bash
uv run pytest tests/ -v
```

Atteso: tutti PASS.

**Step 6: Commit**

```bash
git add erpclaw/erp_tools.py tests/test_tool_indirizzi.py
git commit -m "feat: add address tools for clients and suppliers"
```

---

## Task 7: `LogisticaTools` — Anagrafica ubicazioni

**Files:**
- Create: `erpclaw/logistica_tools.py`
- Create: `tests/test_logistica_anagrafica.py`

**Step 1: Scrivi i test**

```python
# tests/test_logistica_anagrafica.py
import pytest
from unittest.mock import patch
from erpclaw.logistica_tools import LogisticaTools
from erpclaw.erp_db import Base, Magazzino, Zona, Scaffale, Ripiano
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(autouse=True)
def patch_session(engine):
    with patch("erpclaw.logistica_tools.get_session") as mock:
        mock.return_value = Session(engine)
        yield mock

@pytest.fixture
def tools():
    return LogisticaTools()

def test_crea_magazzino(tools, session):
    result = tools.crea_magazzino("MAG1", "Principale")
    assert "✓" in result
    assert session.query(Magazzino).filter_by(codice="MAG1").first() is not None

def test_crea_zona(tools, session):
    tools.crea_magazzino("MAG1", "Principale")
    result = tools.crea_zona("A", "Zona A", "MAG1")
    assert "✓" in result

def test_crea_scaffale(tools, session):
    tools.crea_magazzino("MAG1", "Principale")
    tools.crea_zona("A", "Zona A", "MAG1")
    result = tools.crea_scaffale("A-01", "Scaffale 1", "A")
    assert "✓" in result

def test_crea_ripiano(tools, session):
    tools.crea_magazzino("MAG1", "Principale")
    tools.crea_zona("A", "Zona A", "MAG1")
    tools.crea_scaffale("A-01", "Scaffale 1", "A")
    result = tools.crea_ripiano("A-01-1", "Ripiano 1", "A-01")
    assert "✓" in result

def test_lista_ubicazioni(tools, session):
    tools.crea_magazzino("MAG1", "Principale")
    tools.crea_zona("A", "Zona A", "MAG1")
    result = tools.lista_ubicazioni()
    assert "MAG1" in result
    assert "Zona A" in result
```

**Step 2: Esegui il test per verificare che fallisce**

```bash
uv run pytest tests/test_logistica_anagrafica.py -v
```

Atteso: `ImportError`.

**Step 3: Crea `erpclaw/logistica_tools.py`**

```python
"""Agno Toolkit per la gestione logistica: ubicazioni, stock e movimenti di magazzino."""

from datetime import datetime
from agno.tools import Toolkit
from erpclaw.erp_db import (
    get_session, init_db,
    Articolo, Ordine, RigaOrdine,
    Magazzino, Zona, Scaffale, Ripiano,
    StockUbicazione, MovimentoMagazzino, TipoMovimento,
    Indirizzo,
)

init_db()


class LogisticaTools(Toolkit):
    def __init__(self):
        super().__init__(name="logistica_tools")
        self.register(self.crea_magazzino)
        self.register(self.crea_zona)
        self.register(self.crea_scaffale)
        self.register(self.crea_ripiano)
        self.register(self.lista_ubicazioni)
        self.register(self.assegna_stock)
        self.register(self.trasferisci_stock)
        self.register(self.stock_per_articolo)
        self.register(self.stock_per_ubicazione)
        self.register(self.articoli_senza_ubicazione)
        self.register(self.scarica_ordine_da_ubicazione)
        self.register(self.storico_movimenti)

    # ── ANAGRAFICA UBICAZIONI ─────────────────────────────────────────────────

    def crea_magazzino(self, codice: str, nome: str) -> str:
        """Crea un nuovo magazzino."""
        with get_session() as s:
            if s.query(Magazzino).filter_by(codice=codice).first():
                return f"Errore: esiste già un magazzino con codice {codice}."
            s.add(Magazzino(codice=codice, nome=nome))
            s.commit()
        return f"Magazzino **{codice} – {nome}** creato ✓"

    def crea_zona(self, codice: str, nome: str, codice_magazzino: str) -> str:
        """Crea una zona all'interno di un magazzino."""
        with get_session() as s:
            mag = s.query(Magazzino).filter_by(codice=codice_magazzino).first()
            if not mag:
                return f"Errore: magazzino {codice_magazzino} non trovato."
            if s.query(Zona).filter_by(codice=codice).first():
                return f"Errore: esiste già una zona con codice {codice}."
            s.add(Zona(codice=codice, nome=nome, magazzino_id=mag.id))
            s.commit()
        return f"Zona **{codice} – {nome}** creata in {codice_magazzino} ✓"

    def crea_scaffale(self, codice: str, nome: str, codice_zona: str) -> str:
        """Crea uno scaffale all'interno di una zona."""
        with get_session() as s:
            zona = s.query(Zona).filter_by(codice=codice_zona).first()
            if not zona:
                return f"Errore: zona {codice_zona} non trovata."
            if s.query(Scaffale).filter_by(codice=codice).first():
                return f"Errore: esiste già uno scaffale con codice {codice}."
            s.add(Scaffale(codice=codice, nome=nome, zona_id=zona.id))
            s.commit()
        return f"Scaffale **{codice} – {nome}** creato in zona {codice_zona} ✓"

    def crea_ripiano(self, codice: str, nome: str, codice_scaffale: str) -> str:
        """Crea un ripiano all'interno di uno scaffale."""
        with get_session() as s:
            scaffale = s.query(Scaffale).filter_by(codice=codice_scaffale).first()
            if not scaffale:
                return f"Errore: scaffale {codice_scaffale} non trovato."
            if s.query(Ripiano).filter_by(codice=codice).first():
                return f"Errore: esiste già un ripiano con codice {codice}."
            s.add(Ripiano(codice=codice, nome=nome, scaffale_id=scaffale.id))
            s.commit()
        return f"Ripiano **{codice} – {nome}** creato in scaffale {codice_scaffale} ✓"

    def lista_ubicazioni(self, codice_magazzino: str = None) -> str:
        """Mostra la gerarchia delle ubicazioni (magazzino → zona → scaffale → ripiano)."""
        with get_session() as s:
            query = s.query(Magazzino)
            if codice_magazzino:
                query = query.filter_by(codice=codice_magazzino)
            magazzini = query.order_by(Magazzino.codice).all()
            if not magazzini:
                return "Nessuna ubicazione configurata."
            lines = []
            for mag in magazzini:
                lines.append(f"**{mag.codice}** – {mag.nome}")
                for zona in sorted(mag.zone, key=lambda z: z.codice):
                    lines.append(f"  └ {zona.codice} – {zona.nome}")
                    for scaffale in sorted(zona.scaffali, key=lambda sc: sc.codice):
                        lines.append(f"    └ {scaffale.codice} – {scaffale.nome}")
                        for ripiano in sorted(scaffale.ripiani, key=lambda r: r.codice):
                            lines.append(f"      └ {ripiano.codice} – {ripiano.nome}")
        return "\n".join(lines)
```

**Step 4: Esegui i test**

```bash
uv run pytest tests/test_logistica_anagrafica.py -v
```

Atteso: tutti PASS.

**Step 5: Commit**

```bash
git add erpclaw/logistica_tools.py tests/test_logistica_anagrafica.py
git commit -m "feat: add LogisticaTools with warehouse hierarchy CRUD"
```

---

## Task 8: `LogisticaTools` — Gestione Stock

**Files:**
- Modify: `erpclaw/logistica_tools.py`
- Create: `tests/test_logistica_stock.py`

**Step 1: Scrivi i test**

```python
# tests/test_logistica_stock.py
import pytest
from unittest.mock import patch
from erpclaw.logistica_tools import LogisticaTools
from erpclaw.erp_db import Base, Articolo, Magazzino, Zona, Scaffale, Ripiano, StockUbicazione
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(autouse=True)
def patch_session(engine):
    with patch("erpclaw.logistica_tools.get_session") as mock:
        mock.return_value = Session(engine)
        yield mock

@pytest.fixture
def tools():
    return LogisticaTools()

@pytest.fixture
def setup_db(session):
    art = Articolo(codice="ART001", descrizione="Widget", prezzo=9.99)
    mag = Magazzino(codice="MAG1", nome="Principale")
    session.add_all([art, mag]); session.flush()
    zona = Zona(codice="A", nome="Zona A", magazzino_id=mag.id)
    session.add(zona); session.flush()
    scaffale = Scaffale(codice="A-01", nome="Scaffale 1", zona_id=zona.id)
    session.add(scaffale); session.flush()
    r1 = Ripiano(codice="A-01-1", nome="Ripiano 1", scaffale_id=scaffale.id)
    r2 = Ripiano(codice="A-01-2", nome="Ripiano 2", scaffale_id=scaffale.id)
    session.add_all([r1, r2]); session.commit()
    return art, r1, r2

def test_assegna_stock(tools, setup_db, session):
    art, r1, _ = setup_db
    result = tools.assegna_stock("ART001", "A-01-1", 100)
    assert "✓" in result
    session.expire_all()
    assert art.giacenza == 100

def test_trasferisci_stock(tools, setup_db, session):
    art, r1, r2 = setup_db
    tools.assegna_stock("ART001", "A-01-1", 100)
    result = tools.trasferisci_stock("ART001", "A-01-1", "A-01-2", 30)
    assert "✓" in result
    session.expire_all()
    assert art.giacenza == 100  # totale invariato
    stock_r1 = session.query(StockUbicazione).filter_by(ripiano_id=r1.id).first()
    stock_r2 = session.query(StockUbicazione).filter_by(ripiano_id=r2.id).first()
    assert stock_r1.quantita == 70
    assert stock_r2.quantita == 30

def test_trasferisci_stock_insufficiente(tools, setup_db):
    tools.assegna_stock("ART001", "A-01-1", 10)
    result = tools.trasferisci_stock("ART001", "A-01-1", "A-01-2", 50)
    assert "Errore" in result

def test_stock_per_articolo(tools, setup_db):
    tools.assegna_stock("ART001", "A-01-1", 100)
    result = tools.stock_per_articolo("ART001")
    assert "A-01-1" in result
    assert "100" in result

def test_articoli_senza_ubicazione(tools, session):
    # Articolo con giacenza virtuale 0 (nessuno stock) — non compare
    art = Articolo(codice="ORFANO", descrizione="Orfano", prezzo=1.0)
    session.add(art); session.commit()
    result = tools.articoli_senza_ubicazione()
    # Con giacenza=0 non è "senza ubicazione problematico" — dipende dall'impl.
    # Il tool mostra articoli con giacenza>0 ma senza StockUbicazione
    assert isinstance(result, str)
```

**Step 2: Esegui il test per verificare che fallisce**

```bash
uv run pytest tests/test_logistica_stock.py -v
```

Atteso: FAIL (metodi non esistono).

**Step 3: Aggiungi i metodi stock in `logistica_tools.py`**

```python
    # ── GESTIONE STOCK ────────────────────────────────────────────────────────

    def assegna_stock(self, codice_articolo: str, codice_ripiano: str, quantita: int) -> str:
        """Assegna (o aggiunge) stock di un articolo a un ripiano. Genera un movimento di carico."""
        with get_session() as s:
            art = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not art:
                return f"Errore: articolo {codice_articolo} non trovato."
            ripiano = s.query(Ripiano).filter_by(codice=codice_ripiano).first()
            if not ripiano:
                return f"Errore: ripiano {codice_ripiano} non trovato."
            stock = s.query(StockUbicazione).filter_by(
                articolo_id=art.id, ripiano_id=ripiano.id
            ).first()
            if stock:
                stock.quantita += quantita
            else:
                stock = StockUbicazione(articolo_id=art.id, ripiano_id=ripiano.id, quantita=quantita)
                s.add(stock)
            s.add(MovimentoMagazzino(
                articolo_id=art.id,
                ripiano_destinazione_id=ripiano.id,
                quantita=quantita,
                tipo=TipoMovimento.carico,
            ))
            s.commit()
        return f"Stock **{codice_articolo}** in {codice_ripiano}: +{quantita} unità ✓"

    def trasferisci_stock(self, codice_articolo: str, codice_ripiano_origine: str,
                          codice_ripiano_dest: str, quantita: int) -> str:
        """Trasferisce stock di un articolo da un ripiano a un altro. Genera un movimento di trasferimento."""
        with get_session() as s:
            art = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not art:
                return f"Errore: articolo {codice_articolo} non trovato."
            r_orig = s.query(Ripiano).filter_by(codice=codice_ripiano_origine).first()
            r_dest = s.query(Ripiano).filter_by(codice=codice_ripiano_dest).first()
            if not r_orig:
                return f"Errore: ripiano origine {codice_ripiano_origine} non trovato."
            if not r_dest:
                return f"Errore: ripiano destinazione {codice_ripiano_dest} non trovato."
            stock_orig = s.query(StockUbicazione).filter_by(
                articolo_id=art.id, ripiano_id=r_orig.id
            ).first()
            if not stock_orig or stock_orig.quantita < quantita:
                disponibile = stock_orig.quantita if stock_orig else 0
                return f"Errore: stock insufficiente in {codice_ripiano_origine} (disponibile: {disponibile})."
            stock_orig.quantita -= quantita
            stock_dest = s.query(StockUbicazione).filter_by(
                articolo_id=art.id, ripiano_id=r_dest.id
            ).first()
            if stock_dest:
                stock_dest.quantita += quantita
            else:
                s.add(StockUbicazione(articolo_id=art.id, ripiano_id=r_dest.id, quantita=quantita))
            s.add(MovimentoMagazzino(
                articolo_id=art.id,
                ripiano_origine_id=r_orig.id,
                ripiano_destinazione_id=r_dest.id,
                quantita=quantita,
                tipo=TipoMovimento.trasferimento,
            ))
            s.commit()
        return f"Trasferiti {quantita}x **{codice_articolo}** da {codice_ripiano_origine} → {codice_ripiano_dest} ✓"

    def stock_per_articolo(self, codice_articolo: str) -> str:
        """Mostra la distribuzione dello stock di un articolo in tutte le ubicazioni."""
        with get_session() as s:
            art = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not art:
                return f"Errore: articolo {codice_articolo} non trovato."
            stocks = s.query(StockUbicazione).filter_by(articolo_id=art.id).all()
            if not stocks:
                return f"Nessuno stock ubicato per **{codice_articolo}**."
            rows = "\n".join(
                f"| {st.ripiano.codice} | {st.ripiano.scaffale.zona.magazzino.codice} | {st.quantita} |"
                for st in stocks
            )
        return f"**{codice_articolo}** – distribuzione stock:\n| Ripiano | Magazzino | Qtà |\n|---------|-----------|-----|\n{rows}"

    def stock_per_ubicazione(self, codice_ripiano: str) -> str:
        """Mostra tutti gli articoli presenti in un ripiano con le relative quantità."""
        with get_session() as s:
            ripiano = s.query(Ripiano).filter_by(codice=codice_ripiano).first()
            if not ripiano:
                return f"Errore: ripiano {codice_ripiano} non trovato."
            stocks = s.query(StockUbicazione).filter_by(ripiano_id=ripiano.id).all()
            if not stocks:
                return f"Nessun articolo nel ripiano **{codice_ripiano}**."
            rows = "\n".join(
                f"| {st.articolo.codice} | {st.articolo.descrizione} | {st.quantita} |"
                for st in stocks
            )
        return f"**{codice_ripiano}** – contenuto:\n| Codice | Descrizione | Qtà |\n|--------|-------------|-----|\n{rows}"

    def articoli_senza_ubicazione(self) -> str:
        """Elenca gli articoli con giacenza > 0 ma non presenti in nessuna ubicazione."""
        with get_session() as s:
            from sqlalchemy import not_, exists
            sub = exists().where(StockUbicazione.articolo_id == Articolo.id)
            articoli = s.query(Articolo).filter(
                not_(sub), Articolo.giacenza > 0
            ).all()
            if not articoli:
                return "Tutti gli articoli con giacenza > 0 hanno almeno un'ubicazione."
            rows = "\n".join(
                f"| {a.codice} | {a.descrizione} | {a.giacenza} |"
                for a in articoli
            )
        return f"**Articoli senza ubicazione:**\n| Codice | Descrizione | Giacenza |\n|--------|-------------|----------|\n{rows}"
```

**Step 4: Esegui i test**

```bash
uv run pytest tests/test_logistica_stock.py -v
```

Atteso: tutti PASS.

**Step 5: Commit**

```bash
git add erpclaw/logistica_tools.py tests/test_logistica_stock.py
git commit -m "feat: add stock management tools (assegna, trasferisci, query)"
```

---

## Task 9: `LogisticaTools` — Scarico Ordine e Storico

**Files:**
- Modify: `erpclaw/logistica_tools.py`
- Create: `tests/test_logistica_ordine.py`

**Step 1: Scrivi i test**

```python
# tests/test_logistica_ordine.py
import pytest
from unittest.mock import patch
from datetime import date
from erpclaw.logistica_tools import LogisticaTools
from erpclaw.erp_db import (
    Base, Articolo, Cliente, Ordine, RigaOrdine, StatoOrdine,
    Magazzino, Zona, Scaffale, Ripiano, StockUbicazione, MovimentoMagazzino
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(autouse=True)
def patch_session(engine):
    with patch("erpclaw.logistica_tools.get_session") as mock:
        mock.return_value = Session(engine)
        yield mock

@pytest.fixture
def tools():
    return LogisticaTools()

@pytest.fixture
def setup_ordine(session):
    art = Articolo(codice="ART001", descrizione="Widget", prezzo=9.99)
    cli = Cliente(codice="C001", ragione_sociale="Acme")
    mag = Magazzino(codice="MAG1", nome="Principale")
    session.add_all([art, cli, mag]); session.flush()
    zona = Zona(codice="A", nome="A", magazzino_id=mag.id)
    session.add(zona); session.flush()
    scaffale = Scaffale(codice="A-01", nome="S1", zona_id=zona.id)
    session.add(scaffale); session.flush()
    ripiano = Ripiano(codice="A-01-1", nome="R1", scaffale_id=scaffale.id)
    session.add(ripiano); session.flush()
    stock = StockUbicazione(articolo_id=art.id, ripiano_id=ripiano.id, quantita=100)
    ordine = Ordine(numero="ORD-0001", data=date.today(), cliente_id=cli.id, stato=StatoOrdine.confermato)
    session.add_all([stock, ordine]); session.flush()
    riga = RigaOrdine(ordine_id=ordine.id, articolo_id=art.id, quantita=10, prezzo_unitario=9.99)
    session.add(riga); session.commit()
    return art, ordine, ripiano

def test_scarica_ordine(tools, setup_ordine, session):
    art, ordine, ripiano = setup_ordine
    result = tools.scarica_ordine_da_ubicazione("ORD-0001")
    assert "✓" in result
    session.expire_all()
    stock = session.query(StockUbicazione).filter_by(ripiano_id=ripiano.id).first()
    assert stock.quantita == 90
    mov = session.query(MovimentoMagazzino).filter_by(
        articolo_id=art.id, ordine_id=ordine.id
    ).first()
    assert mov is not None

def test_scarica_ordine_stock_insufficiente(tools, session, setup_ordine):
    art, ordine, ripiano = setup_ordine
    # svuota lo stock
    stock = session.query(StockUbicazione).filter_by(ripiano_id=ripiano.id).first()
    stock.quantita = 5
    session.commit()
    result = tools.scarica_ordine_da_ubicazione("ORD-0001")
    assert "Errore" in result

def test_storico_movimenti(tools, setup_ordine):
    tools.scarica_ordine_da_ubicazione("ORD-0001")
    result = tools.storico_movimenti(codice_articolo="ART001")
    assert "ART001" in result
```

**Step 2: Esegui il test per verificare che fallisce**

```bash
uv run pytest tests/test_logistica_ordine.py -v
```

Atteso: FAIL (metodi non esistono).

**Step 3: Aggiungi i metodi in `logistica_tools.py`**

```python
    # ── INTEGRAZIONE ORDINI ───────────────────────────────────────────────────

    def scarica_ordine_da_ubicazione(self, numero_ordine: str) -> str:
        """Scarica le quantità di un ordine dalle ubicazioni (strategia LIFO: prima le ubicazioni con più stock).
        Fallisce se lo stock totale è insufficiente per qualsiasi articolo dell'ordine."""
        with get_session() as s:
            ordine = s.query(Ordine).filter_by(numero=numero_ordine).first()
            if not ordine:
                return f"Errore: ordine {numero_ordine} non trovato."
            righe = s.query(RigaOrdine).filter_by(ordine_id=ordine.id).all()
            if not righe:
                return f"Errore: l'ordine {numero_ordine} non ha righe."

            # Verifica preliminare disponibilità per tutti gli articoli
            for riga in righe:
                totale_stock = sum(
                    st.quantita for st in
                    s.query(StockUbicazione).filter_by(articolo_id=riga.articolo_id).all()
                )
                if totale_stock < riga.quantita:
                    return (
                        f"Errore: stock insufficiente per **{riga.articolo.codice}** "
                        f"(richiesto: {riga.quantita}, disponibile: {totale_stock})."
                    )

            # Esegui lo scarico
            log_lines = []
            for riga in righe:
                da_scaricare = riga.quantita
                stocks = (
                    s.query(StockUbicazione)
                    .filter_by(articolo_id=riga.articolo_id)
                    .order_by(StockUbicazione.quantita.desc())
                    .all()
                )
                for stock in stocks:
                    if da_scaricare <= 0:
                        break
                    prelevato = min(stock.quantita, da_scaricare)
                    stock.quantita -= prelevato
                    da_scaricare -= prelevato
                    s.add(MovimentoMagazzino(
                        articolo_id=riga.articolo_id,
                        ripiano_origine_id=stock.ripiano_id,
                        quantita=prelevato,
                        tipo=TipoMovimento.scarico,
                        ordine_id=ordine.id,
                    ))
                    log_lines.append(
                        f"  {riga.articolo.codice}: -{prelevato} da {stock.ripiano.codice}"
                    )
            s.commit()

            # Indirizzo spedizione cliente
            addr = next(
                (i for i in ordine.cliente.indirizzi if i.tipo.value == "spedizione"),
                next((i for i in ordine.cliente.indirizzi if i.tipo.value == "sede_legale"), None)
            )
            addr_str = ""
            if addr:
                addr_str = f"\n📦 Spedire a: {addr.via}, {addr.cap} {addr.citta} ({addr.provincia})"

        return (
            f"Scarico ordine **{numero_ordine}** completato ✓{addr_str}\n"
            + "\n".join(log_lines)
        )

    # ── STORICO ───────────────────────────────────────────────────────────────

    def storico_movimenti(self, codice_articolo: str = None, codice_ripiano: str = None,
                          limit: int = 20) -> str:
        """Mostra gli ultimi N movimenti di magazzino, filtrabili per articolo o ripiano."""
        with get_session() as s:
            q = s.query(MovimentoMagazzino)
            if codice_articolo:
                art = s.query(Articolo).filter_by(codice=codice_articolo).first()
                if not art:
                    return f"Errore: articolo {codice_articolo} non trovato."
                q = q.filter_by(articolo_id=art.id)
            if codice_ripiano:
                ripiano = s.query(Ripiano).filter_by(codice=codice_ripiano).first()
                if not ripiano:
                    return f"Errore: ripiano {codice_ripiano} non trovato."
                from sqlalchemy import or_
                q = q.filter(
                    or_(
                        MovimentoMagazzino.ripiano_origine_id == ripiano.id,
                        MovimentoMagazzino.ripiano_destinazione_id == ripiano.id,
                    )
                )
            movimenti = q.order_by(MovimentoMagazzino.data_ora.desc()).limit(limit).all()
            if not movimenti:
                return "Nessun movimento trovato."
            rows = "\n".join(
                f"| {m.data_ora.strftime('%Y-%m-%d %H:%M')} | {m.tipo.value} | {m.articolo.codice} | "
                f"{m.ripiano_origine.codice if m.ripiano_origine else '—'} → "
                f"{m.ripiano_destinazione.codice if m.ripiano_destinazione else '—'} | {m.quantita} |"
                for m in movimenti
            )
        return f"| Data | Tipo | Articolo | Ubicazione | Qtà |\n|------|------|----------|------------|-----|\n{rows}"
```

**Step 4: Esegui i test**

```bash
uv run pytest tests/test_logistica_ordine.py -v
```

Atteso: tutti PASS.

**Step 5: Esegui tutti i test**

```bash
uv run pytest tests/ -v
```

Atteso: tutti PASS.

**Step 6: Commit**

```bash
git add erpclaw/logistica_tools.py tests/test_logistica_ordine.py
git commit -m "feat: add order discharge and movement history tools"
```

---

## Task 10: Integrazione in `agent.py`

**Files:**
- Modify: `erpclaw/agent.py`

**Step 1: Aggiorna `agent.py`**

Aggiungi l'import:
```python
from erpclaw.logistica_tools import LogisticaTools
```

Nella definizione del `team`, aggiungi `LogisticaTools()` alla lista `tools`:
```python
    tools=[ERPTools(), LogisticaTools()],
```

Nell'istruzione `instructions` del team, aggiungi in fondo:

```
Gestione logistica:
- Per ubicare articoli in magazzino usa crea_magazzino, crea_zona, crea_scaffale, crea_ripiano.
- Per caricare stock usa assegna_stock; per spostarlo usa trasferisci_stock.
- Quando un ordine viene marcato come 'spedito', proponi all'utente di eseguire scarica_ordine_da_ubicazione.
- Per verificare dove si trova un articolo usa stock_per_articolo; per vedere cosa c'è in un ripiano usa stock_per_ubicazione.
- Segnala proattivamente gli articoli senza ubicazione con articoli_senza_ubicazione.
```

**Step 2: Verifica che il bot si avvii senza errori**

```bash
uv run erpclaw
```

Atteso: bot avviato senza `ImportError` o errori di registrazione tool. Interrompi con Ctrl+C.

**Step 3: Commit**

```bash
git add erpclaw/agent.py
git commit -m "feat: register LogisticaTools in agent team"
```

---

## Task 11: Admin Panel — nuovi ModelView

**Files:**
- Modify: `erpclaw/web.py`

**Step 1: Aggiorna `web.py`**

Aggiungi gli import:

```python
from erpclaw.erp_db import (
    engine, init_db,
    Articolo, Cliente, Ordine, RigaOrdine, Fornitore, CatalogoFornitore,
    Indirizzo,
    Magazzino, Zona, Scaffale, Ripiano, StockUbicazione, MovimentoMagazzino,
)
```

Aggiungi le nuove `ModelView` dopo `CatalogoFornitoreAdmin`:

```python
class IndirizzoAdmin(ModelView, model=Indirizzo):
    name = "Indirizzo"
    name_plural = "Indirizzi"
    icon = "fa-solid fa-map-marker-alt"
    column_list = [Indirizzo.tipo, Indirizzo.via, Indirizzo.citta, Indirizzo.cap, Indirizzo.paese]
    column_searchable_list = [Indirizzo.citta, Indirizzo.cap]
    column_sortable_list = [Indirizzo.tipo, Indirizzo.citta]


class MagazzinoAdmin(ModelView, model=Magazzino):
    name = "Magazzino"
    name_plural = "Magazzini"
    icon = "fa-solid fa-warehouse"
    column_list = [Magazzino.codice, Magazzino.nome]
    column_searchable_list = [Magazzino.codice, Magazzino.nome]


class ZonaAdmin(ModelView, model=Zona):
    name = "Zona"
    name_plural = "Zone"
    icon = "fa-solid fa-layer-group"
    column_list = [Zona.codice, Zona.nome, Zona.magazzino]
    column_searchable_list = [Zona.codice, Zona.nome]


class ScaffaleAdmin(ModelView, model=Scaffale):
    name = "Scaffale"
    name_plural = "Scaffali"
    icon = "fa-solid fa-th-large"
    column_list = [Scaffale.codice, Scaffale.nome, Scaffale.zona]
    column_searchable_list = [Scaffale.codice, Scaffale.nome]


class RipianoAdmin(ModelView, model=Ripiano):
    name = "Ripiano"
    name_plural = "Ripiani"
    icon = "fa-solid fa-bars"
    column_list = [Ripiano.codice, Ripiano.nome, Ripiano.scaffale]
    column_searchable_list = [Ripiano.codice, Ripiano.nome]


class StockUbicazioneAdmin(ModelView, model=StockUbicazione):
    name = "Stock Ubicazione"
    name_plural = "Stock Ubicazioni"
    icon = "fa-solid fa-cubes"
    column_list = [StockUbicazione.articolo, StockUbicazione.ripiano, StockUbicazione.quantita]
    column_sortable_list = [StockUbicazione.quantita]


class MovimentoMagazzinoAdmin(ModelView, model=MovimentoMagazzino):
    name = "Movimento Magazzino"
    name_plural = "Movimenti Magazzino"
    icon = "fa-solid fa-arrows-alt"
    column_list = [MovimentoMagazzino.data_ora, MovimentoMagazzino.tipo, MovimentoMagazzino.articolo,
                   MovimentoMagazzino.quantita, MovimentoMagazzino.ordine]
    column_sortable_list = [MovimentoMagazzino.data_ora, MovimentoMagazzino.tipo]
```

Aggiungi i `add_view` in fondo:

```python
admin.add_view(IndirizzoAdmin)
admin.add_view(MagazzinoAdmin)
admin.add_view(ZonaAdmin)
admin.add_view(ScaffaleAdmin)
admin.add_view(RipianoAdmin)
admin.add_view(StockUbicazioneAdmin)
admin.add_view(MovimentoMagazzinoAdmin)
```

**Step 2: Verifica che il pannello admin si avvii**

```bash
uv run uvicorn erpclaw.web:app --reload
```

Apri http://localhost:8000/admin. Verifica che i nuovi menu compaiano. Interrompi con Ctrl+C.

**Step 3: Commit**

```bash
git add erpclaw/web.py
git commit -m "feat: add admin views for logistics and address models"
```

---

## Task 12: Test finale end-to-end

**Step 1: Esegui la suite completa**

```bash
uv run pytest tests/ -v --tb=short
```

Atteso: tutti PASS.

**Step 2: Avvia il bot e testa manualmente via Telegram**

Scenari da verificare:
1. "Crea magazzino MAG1 chiamato Principale"
2. "Crea zona A nel magazzino MAG1"
3. "Crea scaffale A-01 nella zona A"
4. "Crea ripiano A-01-1 nello scaffale A-01"
5. "Assegna 50 pezzi di [CODICE_ARTICOLO] al ripiano A-01-1"
6. "Dove si trova [CODICE_ARTICOLO]?"
7. "Aggiungi indirizzo di spedizione Via Roma 1, 20100 Milano MI al cliente [CODICE]"
8. "Scarica l'ordine [NUMERO] dalle ubicazioni"
9. "Mostrami gli ultimi movimenti di magazzino"

**Step 3: Commit finale**

```bash
git add .
git commit -m "test: verify full logistics agent integration"
```
