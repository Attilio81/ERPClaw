"""Tests for categoria and scorta_minima tools in ERPTools."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unittest.mock import patch

from erpclaw.erp_db import Base, Articolo, Categoria
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


def test_crea_categoria(tools):
    t, _ = tools
    result = t.crea_categoria("Bevande")
    assert "Bevande" in result
    assert "creata" in result.lower() or "✓" in result


def test_crea_categoria_duplicato(tools):
    t, _ = tools
    t.crea_categoria("Bevande")
    result = t.crea_categoria("Bevande")
    assert "esiste" in result.lower() or "già" in result.lower() or "errore" in result.lower()


def test_lista_categorie_vuota(tools):
    t, _ = tools
    result = t.lista_categorie()
    assert "nessuna" in result.lower()


def test_lista_categorie(tools):
    t, _ = tools
    t.crea_categoria("Bevande")
    t.crea_categoria("Snack")
    result = t.lista_categorie()
    assert "Bevande" in result
    assert "Snack" in result


def test_assegna_categoria(tools):
    t, make_session = tools
    t.crea_categoria("Bevande")
    with make_session() as s:
        s.add(Articolo(codice="ART01", descrizione="Test", prezzo=1.0))
        s.commit()
    result = t.assegna_categoria("ART01", "Bevande")
    assert "ART01" in result
    assert "Bevande" in result


def test_assegna_categoria_articolo_non_trovato(tools):
    t, _ = tools
    t.crea_categoria("Bevande")
    result = t.assegna_categoria("XXXXXX", "Bevande")
    assert "non trovato" in result.lower() or "errore" in result.lower()


def test_assegna_categoria_non_trovata(tools):
    t, make_session = tools
    with make_session() as s:
        s.add(Articolo(codice="ART01", descrizione="Test", prezzo=1.0))
        s.commit()
    result = t.assegna_categoria("ART01", "Inesistente")
    assert "non trovata" in result.lower() or "errore" in result.lower()


def test_articoli_sotto_scorta_minima(tools):
    t, make_session = tools
    with make_session() as s:
        # Articolo con scorta_minima=10, giacenza=0 → deve apparire
        s.add(Articolo(codice="ART01", descrizione="Sotto soglia", prezzo=1.0, scorta_minima=10))
        # Articolo senza scorta_minima → non deve apparire
        s.add(Articolo(codice="ART02", descrizione="Nessuna soglia", prezzo=1.0, scorta_minima=0))
        s.commit()
    result = t.articoli_sotto_scorta_minima()
    assert "ART01" in result
    assert "ART02" not in result


def test_articoli_sotto_scorta_minima_nessuno(tools):
    t, _ = tools
    result = t.articoli_sotto_scorta_minima()
    assert "nessun" in result.lower()
