"""Tests for web chat HTTP routes.

NOTE: questi test richiedono i template in erpclaw/templates/chat/
I test vengono eseguiti dal project root dove erpclaw/templates/ è visibile.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from erpclaw.chat import router, chat_sessions


@pytest.fixture(autouse=True)
def clear_sessions():
    """Pulisce lo stato delle sessioni tra i test."""
    chat_sessions.clear()
    yield
    chat_sessions.clear()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_get_chat_returns_200(client):
    """GET /chat restituisce 200 e imposta il cookie sessione."""
    response = client.get("/chat")
    assert response.status_code == 200
    assert "chat_session" in response.cookies


def test_get_chat_contains_form(client):
    """GET /chat contiene il form di invio messaggio."""
    response = client.get("/chat")
    assert b'name="message"' in response.content


def test_post_send_returns_html_with_user_message(client):
    """POST /chat/send include il messaggio utente nella risposta."""
    with patch("erpclaw.chat.run_agent", new=AsyncMock(return_value="risposta agente")):
        response = client.post("/chat/send", data={"message": "ciao"})
    assert response.status_code == 200
    assert b"ciao" in response.content


def test_post_send_returns_html_with_agent_response(client):
    """POST /chat/send include la risposta dell'agente nella risposta."""
    with patch("erpclaw.chat.run_agent", new=AsyncMock(return_value="**risposta**")):
        response = client.post("/chat/send", data={"message": "test"})
    assert response.status_code == 200
    # markdown2 converte **risposta** in <strong>risposta</strong>
    assert b"risposta" in response.content


def test_post_send_handles_none_response(client):
    """POST /chat/send gestisce risposta None senza crash."""
    with patch("erpclaw.chat.run_agent", new=AsyncMock(return_value=None)):
        response = client.post("/chat/send", data={"message": "test"})
    assert response.status_code == 200


def test_post_send_handles_agent_exception(client):
    """POST /chat/send mostra errore inline se l'agente lancia eccezione."""
    with patch("erpclaw.chat.run_agent", new=AsyncMock(side_effect=Exception("errore test"))):
        response = client.post("/chat/send", data={"message": "test"})
    assert response.status_code == 200
    assert b"Errore" in response.content
