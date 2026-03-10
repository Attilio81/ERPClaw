# tests/test_logistica_stock.py
import pytest
from unittest.mock import patch
from erpclaw.logistica_tools import LogisticaTools
from erpclaw.erp_db import Base, Articolo, Magazzino, Zona, Scaffale, Ripiano, StockUbicazione
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def db_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as s:
        yield s


@pytest.fixture
def tools(db_engine):
    t = LogisticaTools()
    def make_session():
        return Session(db_engine)
    with patch("erpclaw.logistica_tools.get_session", side_effect=make_session):
        yield t


@pytest.fixture
def setup_db(db_session):
    art = Articolo(codice="ART001", descrizione="Widget", prezzo_vendita=9.99)
    mag = Magazzino(codice="MAG1", nome="Principale")
    db_session.add_all([art, mag]); db_session.flush()
    zona = Zona(codice="A", nome="Zona A", magazzino_id=mag.id)
    db_session.add(zona); db_session.flush()
    scaffale = Scaffale(codice="A-01", nome="Scaffale 1", zona_id=zona.id)
    db_session.add(scaffale); db_session.flush()
    r1 = Ripiano(codice="A-01-1", nome="Ripiano 1", scaffale_id=scaffale.id)
    r2 = Ripiano(codice="A-01-2", nome="Ripiano 2", scaffale_id=scaffale.id)
    db_session.add_all([r1, r2]); db_session.commit()
    return art, r1, r2


def test_assegna_stock(tools, setup_db, db_session):
    art, r1, _ = setup_db
    result = tools.assegna_stock("ART001", "A-01-1", 100)
    assert "✓" in result
    db_session.expire_all()
    assert art.giacenza == 100


def test_trasferisci_stock(tools, setup_db, db_session):
    art, r1, r2 = setup_db
    tools.assegna_stock("ART001", "A-01-1", 100)
    result = tools.trasferisci_stock("ART001", "A-01-1", "A-01-2", 30)
    assert "✓" in result
    db_session.expire_all()
    assert art.giacenza == 100  # totale invariato
    stock_r1 = db_session.query(StockUbicazione).filter_by(ripiano_id=r1.id).first()
    stock_r2 = db_session.query(StockUbicazione).filter_by(ripiano_id=r2.id).first()
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


def test_articoli_senza_ubicazione(tools, db_session):
    art = Articolo(codice="ORFANO", descrizione="Orfano", prezzo_vendita=1.0)
    db_session.add(art)
    db_session.commit()
    result = tools.articoli_senza_ubicazione()
    assert isinstance(result, str)
