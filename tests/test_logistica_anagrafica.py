# tests/test_logistica_anagrafica.py
import pytest
from unittest.mock import patch
from erpclaw.logistica_tools import LogisticaTools
from erpclaw.erp_db import Base, Magazzino, Zona, Scaffale, Ripiano
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


def test_crea_magazzino(tools, db_session):
    result = tools.crea_magazzino("MAG1", "Principale")
    assert "✓" in result
    assert db_session.query(Magazzino).filter_by(codice="MAG1").first() is not None


def test_crea_zona(tools, db_session):
    tools.crea_magazzino("MAG1", "Principale")
    result = tools.crea_zona("A", "Zona A", "MAG1")
    assert "✓" in result


def test_crea_scaffale(tools, db_session):
    tools.crea_magazzino("MAG1", "Principale")
    tools.crea_zona("A", "Zona A", "MAG1")
    result = tools.crea_scaffale("A-01", "Scaffale 1", "A")
    assert "✓" in result


def test_crea_ripiano(tools, db_session):
    tools.crea_magazzino("MAG1", "Principale")
    tools.crea_zona("A", "Zona A", "MAG1")
    tools.crea_scaffale("A-01", "Scaffale 1", "A")
    result = tools.crea_ripiano("A-01-1", "Ripiano 1", "A-01")
    assert "✓" in result


def test_lista_ubicazioni(tools, db_session):
    tools.crea_magazzino("MAG1", "Principale")
    tools.crea_zona("A", "Zona A", "MAG1")
    result = tools.lista_ubicazioni()
    assert "MAG1" in result
    assert "Zona A" in result
