# tests/test_tool_indirizzi.py
import pytest
from unittest.mock import patch, MagicMock
from erpclaw.erp_tools import ERPTools
from erpclaw.erp_db import Base, Cliente, Fornitore, Indirizzo, TipoIndirizzo
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
    t = ERPTools()
    # patch get_session to use our in-memory engine
    def make_session():
        return Session(db_engine)
    with patch("erpclaw.erp_tools.get_session", side_effect=make_session):
        yield t


def test_aggiungi_indirizzo_cliente(tools, db_session):
    db_session.add(Cliente(codice="C001", ragione_sociale="Acme"))
    db_session.commit()
    result = tools.aggiungi_indirizzo_cliente(
        "C001", "spedizione", "Via Roma 1", "20100", "Milano", "MI"
    )
    assert "✓" in result
    addr = db_session.query(Indirizzo).first()
    assert addr.citta == "Milano"


def test_aggiungi_indirizzo_cliente_not_found(tools):
    result = tools.aggiungi_indirizzo_cliente(
        "NONEXIST", "spedizione", "Via X", "00000", "Roma", "RM"
    )
    assert "Errore" in result


def test_aggiungi_indirizzo_fornitore(tools, db_session):
    db_session.add(Fornitore(codice="F001", ragione_sociale="Supplier Srl"))
    db_session.commit()
    result = tools.aggiungi_indirizzo_fornitore(
        "F001", "sede_legale", "Via Po 5", "10100", "Torino", "TO"
    )
    assert "✓" in result


def test_lista_indirizzi_cliente(tools, db_session):
    c = Cliente(codice="C002", ragione_sociale="Beta Srl")
    db_session.add(c)
    db_session.flush()
    db_session.add(Indirizzo(tipo=TipoIndirizzo.spedizione, via="Via X", cap="00100",
                              citta="Roma", provincia="RM", cliente_id=c.id))
    db_session.commit()
    result = tools.lista_indirizzi_cliente("C002")
    assert "Roma" in result
