"""Tests for shop cart utilities."""
from erpclaw.shop import _carrello_totale, _prossimo_numero_ordine
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Cliente, Ordine
import pytest
from datetime import date


@pytest.fixture
def session():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def test_carrello_totale_vuoto():
    assert _carrello_totale([]) == 0.0


def test_carrello_totale():
    carrello = [
        {"articolo_id": 1, "codice": "A1", "descrizione": "X", "prezzo": 10.0, "qty": 2},
        {"articolo_id": 2, "codice": "A2", "descrizione": "Y", "prezzo": 5.5, "qty": 1},
    ]
    assert _carrello_totale(carrello) == 25.5


def test_prossimo_numero_ordine_incrementa(session):
    cliente = Cliente(codice="C1", ragione_sociale="T", email="t@t.com")
    session.add(cliente)
    session.flush()
    today = date.today().strftime("%Y%m%d")
    ordine = Ordine(numero=f"WEB-{today}-0001", cliente_id=cliente.id, data=date.today())
    session.add(ordine)
    session.commit()

    n = _prossimo_numero_ordine(session)
    assert n == f"WEB-{today}-0002"
