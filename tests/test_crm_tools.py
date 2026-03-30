"""Tests for CrmTools."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unittest.mock import patch

from erpclaw.erp_db import Base, Cliente, EventoCRM, StatoEventoCRM


def make_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def tools():
    eng = make_engine()

    def make_session():
        return Session(eng)

    from erpclaw.crm_tools import CrmTools
    with patch("erpclaw.crm_tools.get_session", side_effect=make_session):
        yield CrmTools(), make_session


@pytest.fixture
def tools_con_cliente(tools):
    t, make_session = tools
    with make_session() as s:
        s.add(Cliente(codice="C001", ragione_sociale="Test Srl", email="test@test.it", telefono=""))
        s.commit()
    with make_session() as s:
        c_id = s.query(Cliente).filter_by(codice="C001").first().id
    return t, make_session, c_id


def test_crea_evento_visita(tools):
    t, _ = tools
    result = t.crea_evento(tipo="visita", data_ora="2026-04-01 10:00")
    assert "creato" in result
    assert "visita" in result


def test_crea_evento_con_cliente(tools_con_cliente):
    t, _, c_id = tools_con_cliente
    result = t.crea_evento(tipo="visita", data_ora="2026-04-01 10:00", cliente_id=c_id, luogo="Via Roma 1")
    assert "creato" in result
    assert "Test Srl" in result


def test_crea_evento_tipo_invalido(tools):
    t, _ = tools
    result = t.crea_evento(tipo="fax", data_ora="2026-04-01 10:00")
    assert "Errore" in result
    assert "tipo" in result


def test_crea_evento_data_invalida(tools):
    t, _ = tools
    result = t.crea_evento(tipo="chiamata", data_ora="non-una-data")
    assert "Errore" in result


def test_lista_eventi(tools):
    t, _ = tools
    t.crea_evento(tipo="chiamata", data_ora="2026-04-05 14:00")
    result = t.lista_eventi("2026-04-01", "2026-04-30")
    assert "chiamata" in result


def test_lista_eventi_vuota(tools):
    t, _ = tools
    result = t.lista_eventi("2026-01-01", "2026-01-02")
    assert "Nessun" in result


def test_agenda_oggi(tools):
    t, _ = tools
    oggi = datetime.now().strftime("%Y-%m-%d %H:%M")
    t.crea_evento(tipo="email", data_ora=oggi)
    result = t.agenda_oggi()
    assert "email" in result


def test_agenda_settimana(tools):
    t, _ = tools
    from datetime import timedelta
    tra_3_giorni = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
    t.crea_evento(tipo="visita", data_ora=tra_3_giorni)
    result = t.agenda_settimana()
    assert "visita" in result


def test_completa_evento(tools):
    t, ms = tools
    t.crea_evento(tipo="visita", data_ora="2026-04-01 09:00")
    with ms() as s:
        ev_id = s.query(EventoCRM).first().id
    result = t.completa_evento(ev_id, esito="Ordine firmato")
    assert "completato" in result
    with ms() as s:
        ev = s.get(EventoCRM, ev_id)
        assert ev.stato == StatoEventoCRM.completato
        assert ev.esito == "Ordine firmato"


def test_annulla_evento(tools):
    t, ms = tools
    t.crea_evento(tipo="chiamata", data_ora="2026-04-02 11:00")
    with ms() as s:
        ev_id = s.query(EventoCRM).first().id
    result = t.annulla_evento(ev_id)
    assert "annullato" in result
    with ms() as s:
        ev = s.get(EventoCRM, ev_id)
        assert ev.stato == StatoEventoCRM.annullato


def test_aggiorna_evento_resetta_reminder(tools):
    t, ms = tools
    t.crea_evento(tipo="visita", data_ora="2026-04-01 10:00")
    with ms() as s:
        ev = s.query(EventoCRM).first()
        ev.reminder_inviato = True
        s.commit()
        ev_id = ev.id
    t.aggiorna_evento(ev_id, data_ora="2026-04-02 10:00")
    with ms() as s:
        ev = s.get(EventoCRM, ev_id)
        assert ev.reminder_inviato is False


def test_aggiungi_nota(tools_con_cliente):
    t, _, c_id = tools_con_cliente
    result = t.aggiungi_nota(c_id, "Cliente interessato al prodotto X")
    assert "aggiunta" in result


def test_aggiungi_nota_cliente_inesistente(tools):
    t, _ = tools
    result = t.aggiungi_nota(9999, "nota")
    assert "Errore" in result


def test_note_cliente(tools_con_cliente):
    t, _, c_id = tools_con_cliente
    t.aggiungi_nota(c_id, "Prima nota")
    t.aggiungi_nota(c_id, "Seconda nota")
    result = t.note_cliente(c_id)
    assert "Prima nota" in result or "Seconda nota" in result


def test_storico_cliente(tools_con_cliente):
    t, _, c_id = tools_con_cliente
    t.crea_evento(tipo="visita", data_ora="2026-04-01 10:00", cliente_id=c_id)
    t.aggiungi_nota(c_id, "Note generali")
    result = t.storico_cliente(c_id)
    assert "Storico CRM" in result
    assert "visita" in result
    assert "Note generali" in result
