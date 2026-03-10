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
def setup_ordine(db_session):
    art = Articolo(codice="ART001", descrizione="Widget", prezzo=9.99)
    cli = Cliente(codice="C001", ragione_sociale="Acme")
    mag = Magazzino(codice="MAG1", nome="Principale")
    db_session.add_all([art, cli, mag]); db_session.flush()
    zona = Zona(codice="A", nome="A", magazzino_id=mag.id)
    db_session.add(zona); db_session.flush()
    scaffale = Scaffale(codice="A-01", nome="S1", zona_id=zona.id)
    db_session.add(scaffale); db_session.flush()
    ripiano = Ripiano(codice="A-01-1", nome="R1", scaffale_id=scaffale.id)
    db_session.add(ripiano); db_session.flush()
    stock = StockUbicazione(articolo_id=art.id, ripiano_id=ripiano.id, quantita=100)
    ordine = Ordine(numero="ORD-0001", data=date.today(), cliente_id=cli.id, stato=StatoOrdine.confermato)
    db_session.add_all([stock, ordine]); db_session.flush()
    riga = RigaOrdine(ordine_id=ordine.id, articolo_id=art.id, quantita=10, prezzo_unitario=9.99)
    db_session.add(riga); db_session.commit()
    return art, ordine, ripiano


def test_scarica_ordine(tools, setup_ordine, db_session):
    art, ordine, ripiano = setup_ordine
    result = tools.scarica_ordine_da_ubicazione("ORD-0001")
    assert "✓" in result
    db_session.expire_all()
    stock = db_session.query(StockUbicazione).filter_by(ripiano_id=ripiano.id).first()
    assert stock.quantita == 90
    mov = db_session.query(MovimentoMagazzino).filter_by(
        articolo_id=art.id, ordine_id=ordine.id
    ).first()
    assert mov is not None


def test_scarica_ordine_stock_insufficiente(tools, setup_ordine, db_session):
    art, ordine, ripiano = setup_ordine
    # svuota lo stock
    stock = db_session.query(StockUbicazione).filter_by(ripiano_id=ripiano.id).first()
    stock.quantita = 5
    db_session.commit()
    result = tools.scarica_ordine_da_ubicazione("ORD-0001")
    assert "Errore" in result


def test_storico_movimenti(tools, setup_ordine):
    tools.scarica_ordine_da_ubicazione("ORD-0001")
    result = tools.storico_movimenti(codice_articolo="ART001")
    assert "ART001" in result
