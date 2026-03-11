"""Tests for shop authentication helpers."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Cliente, ClienteAuth
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


def test_password_hash_verify(session):
    cliente = Cliente(codice="WEB-TEST", ragione_sociale="Test Srl", email="a@b.com")
    session.add(cliente)
    session.flush()
    hashed = pwd_ctx.hash("secret123")
    auth = ClienteAuth(cliente_id=cliente.id, password_hash=hashed, confermato=True)
    session.add(auth)
    session.commit()

    assert pwd_ctx.verify("secret123", auth.password_hash)
    assert not pwd_ctx.verify("wrong", auth.password_hash)


def test_prossimo_numero_ordine(session):
    from erpclaw.shop import _prossimo_numero_ordine
    n = _prossimo_numero_ordine(session)
    assert n.startswith("WEB-")
    parts = n.split("-")
    assert len(parts) == 3
    assert int(parts[2]) == 1
