"""Tests for ordine fornitore tools in ERPTools."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unittest.mock import patch

from erpclaw.erp_db import Base, Articolo, Fornitore
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


@pytest.fixture
def tools_con_dati(tools):
    t, make_session = tools
    with make_session() as s:
        s.add(Fornitore(codice="FOR01", ragione_sociale="Fornitore Test"))
        s.add(Articolo(codice="ART01", descrizione="Articolo Test", prezzo_vendita=10.0, prezzo_acquisto=6.0))
        s.add(Articolo(codice="ART02", descrizione="Articolo Senza Costo", prezzo_vendita=5.0))
        s.commit()
    return t, make_session


def test_crea_ordine_fornitore(tools_con_dati):
    t, _ = tools_con_dati
    result = t.crea_ordine_fornitore("FOR01")
    assert "ORF-" in result
    assert "FOR01" in result or "Fornitore Test" in result


def test_crea_ordine_fornitore_non_trovato(tools_con_dati):
    t, _ = tools_con_dati
    result = t.crea_ordine_fornitore("XXXXXX")
    assert "errore" in result.lower() or "non trovato" in result.lower()


def test_aggiungi_riga_ordine_fornitore(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 5)
    assert "ART01" in result or "Articolo Test" in result
    assert "5" in result


def test_aggiungi_riga_usa_prezzo_acquisto_default(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 3)
    # prezzo_acquisto è 6.0, deve comparire nel risultato
    assert "6" in result


def test_aggiungi_riga_prezzo_esplicito(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 2, prezzo_unitario=7.5)
    assert "7.5" in result or "7,5" in result


def test_aggiungi_riga_senza_prezzo_acquisto(tools_con_dati):
    """Articolo senza prezzo_acquisto: deve richiedere prezzo_unitario esplicito."""
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART02", 1)
    assert "errore" in result.lower() or "prezzo" in result.lower()


def test_lista_ordini_fornitori(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.lista_ordini_fornitori()
    assert "ORF-0001" in result


def test_lista_ordini_fornitori_filtro_stato(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result_bozza = t.lista_ordini_fornitori(stato="bozza")
    assert "ORF-0001" in result_bozza
    result_inviato = t.lista_ordini_fornitori(stato="inviato")
    assert "ORF-0001" not in result_inviato


def test_visualizza_ordine_fornitore(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    t.aggiungi_riga_ordine_fornitore("ORF-0001", "ART01", 4)
    result = t.visualizza_ordine_fornitore("ORF-0001")
    assert "ART01" in result
    assert "4" in result


def test_avanza_stato_bozza_inviato(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    result = t.avanza_stato_ordine_fornitore("ORF-0001")
    assert "inviato" in result.lower()


def test_avanza_stato_inviato_ricevuto(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    t.avanza_stato_ordine_fornitore("ORF-0001")  # bozza → inviato
    result = t.avanza_stato_ordine_fornitore("ORF-0001")  # inviato → ricevuto
    assert "ricevuto" in result.lower()


def test_avanza_stato_ricevuto_errore(tools_con_dati):
    t, _ = tools_con_dati
    t.crea_ordine_fornitore("FOR01")
    t.avanza_stato_ordine_fornitore("ORF-0001")
    t.avanza_stato_ordine_fornitore("ORF-0001")
    result = t.avanza_stato_ordine_fornitore("ORF-0001")  # già ricevuto
    assert "errore" in result.lower() or "già" in result.lower()


def test_avanza_stato_ordine_non_trovato(tools_con_dati):
    t, _ = tools_con_dati
    result = t.avanza_stato_ordine_fornitore("ORF-9999")
    assert "errore" in result.lower() or "non trovato" in result.lower()
