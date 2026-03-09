"""SQLAlchemy models for the ERP database (erp.db)."""

from datetime import date
from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, Enum, Text, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session
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


class Articolo(Base):
    __tablename__ = "articoli"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    descrizione = Column(String, nullable=False)
    prezzo = Column(Float, nullable=False)
    giacenza = Column(Integer, nullable=False, default=0)

    righe = relationship("RigaOrdine", back_populates="articolo")


class Cliente(Base):
    __tablename__ = "clienti"

    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, nullable=False)
    ragione_sociale = Column(String, nullable=False)
    email = Column(String, default="")
    telefono = Column(String, default="")

    ordini = relationship("Ordine", back_populates="cliente")


class Ordine(Base):
    __tablename__ = "ordini"

    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    cliente_id = Column(Integer, ForeignKey("clienti.id"), nullable=False)
    stato = Column(Enum(StatoOrdine), nullable=False, default=StatoOrdine.bozza)

    cliente = relationship("Cliente", back_populates="ordini")
    righe = relationship("RigaOrdine", back_populates="ordine", cascade="all, delete-orphan")


class RigaOrdine(Base):
    __tablename__ = "righe_ordine"

    id = Column(Integer, primary_key=True)
    ordine_id = Column(Integer, ForeignKey("ordini.id"), nullable=False)
    articolo_id = Column(Integer, ForeignKey("articoli.id"), nullable=False)
    quantita = Column(Integer, nullable=False)
    prezzo_unitario = Column(Float, nullable=False)

    ordine = relationship("Ordine", back_populates="righe")
    articolo = relationship("Articolo", back_populates="righe")


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


class CatalogoFornitore(Base):
    __tablename__ = "cataloghi_fornitori"

    id = Column(Integer, primary_key=True)
    fornitore_id = Column(Integer, ForeignKey("fornitori.id"), nullable=False)
    url_originale = Column(String, default="")
    percorso_file = Column(String)       # path locale del PDF scaricato
    data_scarico = Column(Date, nullable=False, default=date.today)
    note = Column(Text, default="")

    fornitore = relationship("Fornitore", back_populates="cataloghi")


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    return Session(engine)
