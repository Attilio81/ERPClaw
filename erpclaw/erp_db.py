"""SQLAlchemy models for the ERP database (erp.db)."""

from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, Enum, Text, create_engine,
    select, func, UniqueConstraint, DateTime, Boolean, text
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session, column_property
import enum

DATABASE_URL = "sqlite:///./erp.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class StatoOrdine(str, enum.Enum):
    bozza = "bozza"
    confermato = "confermato"
    spedito = "spedito"
    chiuso = "chiuso"


class TipoIndirizzo(str, enum.Enum):
    sede_legale = "sede_legale"
    spedizione = "spedizione"
    fatturazione = "fatturazione"
    altro = "altro"


class TipoMovimento(str, enum.Enum):
    carico = "carico"
    scarico = "scarico"
    trasferimento = "trasferimento"


class StatoOrdineFornitore(str, enum.Enum):
    bozza = "bozza"
    inviato = "inviato"
    ricevuto = "ricevuto"


class Categoria(Base):
    __tablename__ = "categorie"

    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)

    def __str__(self):
        return self.nome

    articoli = relationship("Articolo", back_populates="categoria")


class Articolo(Base):
    __tablename__ = "articoli"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    descrizione = Column(String, nullable=False)
    prezzo_vendita = Column(Float, nullable=False)
    prezzo_acquisto = Column(Float, nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorie.id"), nullable=True)
    scorta_minima = Column(Integer, nullable=True, default=0)

    def __str__(self):
        return f"{self.codice} — {self.descrizione}"

    righe = relationship("RigaOrdine", back_populates="articolo")
    stock_ubicazioni = relationship("StockUbicazione", back_populates="articolo")
    movimenti = relationship("MovimentoMagazzino", back_populates="articolo")
    categoria = relationship("Categoria", back_populates="articoli")


class Cliente(Base):
    __tablename__ = "clienti"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    ragione_sociale = Column(String, nullable=False)
    email = Column(String, default="")
    telefono = Column(String, default="")

    def __str__(self):
        return f"{self.codice} — {self.ragione_sociale}"

    ordini = relationship("Ordine", back_populates="cliente")
    indirizzi = relationship("Indirizzo", back_populates="cliente", cascade="all, delete-orphan")


class Ordine(Base):
    __tablename__ = "ordini"

    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    cliente_id = Column(Integer, ForeignKey("clienti.id"), nullable=False)
    stato = Column(Enum(StatoOrdine), nullable=False, default=StatoOrdine.bozza)

    def __str__(self):
        return self.numero

    cliente = relationship("Cliente", back_populates="ordini")
    righe = relationship("RigaOrdine", back_populates="ordine", cascade="all, delete-orphan")
    movimenti = relationship("MovimentoMagazzino", back_populates="ordine")


class RigaOrdine(Base):
    __tablename__ = "righe_ordine"

    id = Column(Integer, primary_key=True)
    ordine_id = Column(Integer, ForeignKey("ordini.id"), nullable=False)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    quantita = Column(Integer, nullable=False)
    prezzo_unitario = Column(Float, nullable=False)

    ordine = relationship("Ordine", back_populates="righe")
    articolo = relationship("Articolo", back_populates="righe")


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


class Fornitore(Base):
    __tablename__ = "fornitori"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    ragione_sociale = Column(String, nullable=False)
    email = Column(String, default="")
    telefono = Column(String, default="")
    sito_web = Column(String, default="")
    settore = Column(String, default="")  # es. "elettronica", "ufficio"

    cataloghi = relationship("CatalogoFornitore", back_populates="fornitore", cascade="all, delete-orphan")
    indirizzi = relationship("Indirizzo", back_populates="fornitore", cascade="all, delete-orphan")
    ordini_fornitori = relationship("OrdineFornitore", back_populates="fornitore", cascade="all, delete-orphan")


class CatalogoFornitore(Base):
    __tablename__ = "cataloghi_fornitori"

    id = Column(Integer, primary_key=True)
    fornitore_id = Column(Integer, ForeignKey("fornitori.id"), nullable=False)
    url_originale = Column(String, default="")
    percorso_file = Column(String)       # path locale del PDF scaricato
    data_scarico = Column(Date, nullable=False, default=date.today)
    note = Column(Text, default="")

    fornitore = relationship("Fornitore", back_populates="cataloghi")


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


class ClienteAuth(Base):
    __tablename__ = "clienti_auth"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clienti.id"), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    confermato = Column(Boolean, nullable=False, default=True)

    cliente = relationship("Cliente", backref="auth")


class Magazzino(Base):
    __tablename__ = "magazzini"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)

    def __str__(self):
        return f"{self.codice} — {self.nome}"

    zone = relationship("Zona", back_populates="magazzino", cascade="all, delete-orphan")


class Zona(Base):
    __tablename__ = "zone"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    magazzino_id = Column(Integer, ForeignKey("magazzini.id"), nullable=False)

    def __str__(self):
        return f"{self.codice} — {self.nome}"

    magazzino = relationship("Magazzino", back_populates="zone")
    scaffali = relationship("Scaffale", back_populates="zona", cascade="all, delete-orphan")


class Scaffale(Base):
    __tablename__ = "scaffali"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    zona_id = Column(Integer, ForeignKey("zone.id"), nullable=False)

    def __str__(self):
        return f"{self.codice} — {self.nome}"

    zona = relationship("Zona", back_populates="scaffali")
    ripiani = relationship("Ripiano", back_populates="scaffale", cascade="all, delete-orphan")


class Ripiano(Base):
    __tablename__ = "ripiani"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    scaffale_id = Column(Integer, ForeignKey("scaffali.id"), nullable=False)

    def __str__(self):
        return f"{self.codice} — {self.nome}"

    scaffale = relationship("Scaffale", back_populates="ripiani")
    stock = relationship("StockUbicazione", back_populates="ripiano", cascade="all, delete-orphan")
    movimenti_origine = relationship("MovimentoMagazzino", foreign_keys="MovimentoMagazzino.ripiano_origine_id", back_populates="ripiano_origine")
    movimenti_destinazione = relationship("MovimentoMagazzino", foreign_keys="MovimentoMagazzino.ripiano_destinazione_id", back_populates="ripiano_destinazione")


class StockUbicazione(Base):
    __tablename__ = "stock_ubicazioni"

    id = Column(Integer, primary_key=True)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    ripiano_id = Column(Integer, ForeignKey("ripiani.id"), nullable=False)
    quantita = Column(Integer, nullable=False, default=0)

    articolo = relationship("Articolo", back_populates="stock_ubicazioni")
    ripiano = relationship("Ripiano", back_populates="stock")

    __table_args__ = (UniqueConstraint("articolo_id", "ripiano_id"),)


class MovimentoMagazzino(Base):
    __tablename__ = "movimenti_magazzino"

    id = Column(Integer, primary_key=True)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    ripiano_origine_id = Column(Integer, ForeignKey("ripiani.id"), nullable=True)
    ripiano_destinazione_id = Column(Integer, ForeignKey("ripiani.id"), nullable=True)
    quantita = Column(Integer, nullable=False)
    tipo = Column(Enum(TipoMovimento), nullable=False)
    data_ora = Column(DateTime, nullable=False, default=datetime.now)
    ordine_id = Column(Integer, ForeignKey("ordini.id"), nullable=True)
    note = Column(Text, default="")

    articolo = relationship("Articolo", back_populates="movimenti")
    ripiano_origine = relationship("Ripiano", foreign_keys=[ripiano_origine_id], back_populates="movimenti_origine")
    ripiano_destinazione = relationship("Ripiano", foreign_keys=[ripiano_destinazione_id], back_populates="movimenti_destinazione")
    ordine = relationship("Ordine", back_populates="movimenti")


# giacenza derivata dalla somma degli stock nelle ubicazioni
Articolo.giacenza = column_property(
    select(func.coalesce(func.sum(StockUbicazione.quantita), 0))
    .where(StockUbicazione.articolo_id == Articolo.id)
    .correlate_except(StockUbicazione)
    .scalar_subquery()
)


def init_db() -> None:
    """Create all tables if they don't exist, and migrate missing columns."""
    Base.metadata.create_all(bind=engine, checkfirst=True)
    _migrate(engine)


def _migrate(engine) -> None:
    """Add missing columns to existing tables (idempotent)."""
    migrations = [
        ("articoli", "categoria_id", "INTEGER REFERENCES categorie(id)"),
        ("articoli", "scorta_minima", "INTEGER DEFAULT 0"),
        ("articoli", "prezzo_vendita", "REAL"),
        ("articoli", "prezzo_acquisto", "REAL"),
    ]
    with engine.connect() as conn:
        for table, column, col_def in migrations:
            rows = conn.execute(
                text(f"PRAGMA table_info({table})")
            ).fetchall()
            existing = [r[1] for r in rows]
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
        # Copy prezzo → prezzo_vendita only if old prezzo column still exists
        articoli_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(articoli)")).fetchall()]
        if "prezzo" in articoli_cols:
            conn.execute(text(
                "UPDATE articoli SET prezzo_vendita = prezzo WHERE prezzo_vendita IS NULL AND prezzo IS NOT NULL"
            ))
        conn.commit()


def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    return Session(engine)
