"""Tests for ClienteAuth model."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Cliente, ClienteAuth


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_cliente_auth_created_with_defaults(session):
    cliente = Cliente(codice="C001", ragione_sociale="Test Srl", email="test@example.com")
    session.add(cliente)
    session.flush()

    auth = ClienteAuth(cliente_id=cliente.id, password_hash="hashed")
    session.add(auth)
    session.commit()

    assert auth.id is not None
    assert auth.confermato is True
    assert auth.cliente.ragione_sociale == "Test Srl"
