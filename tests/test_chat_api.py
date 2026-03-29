"""Test per i nuovi endpoint JSON /chat/api/history e /chat/api/send."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
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


def test_api_history_returns_empty_list_for_new_session(client):
    r = client.get("/chat/api/history")
    assert r.status_code == 200
    assert r.json() == []


def test_api_history_sets_session_cookie(client):
    r = client.get("/chat/api/history")
    assert "chat_session" in r.cookies


def test_api_send_returns_assistant_message(client):
    with patch("erpclaw.chat.run_agent", new_callable=AsyncMock) as mock:
        mock.return_value = "Ciao! Come posso aiutarti?"
        r = client.post("/chat/api/send", json={"message": "Ciao"})
    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "assistant"
    assert "Ciao" in data["content"]  # markdown rendered, still contains the word


def test_api_send_empty_message_returns_400(client):
    r = client.post("/chat/api/send", json={"message": ""})
    assert r.status_code == 400


def test_api_send_adds_to_history(client):
    with patch("erpclaw.chat.run_agent", new_callable=AsyncMock) as mock:
        mock.return_value = "Risposta test"
        client.post("/chat/api/send", json={"message": "Domanda"})
    r = client.get("/chat/api/history")
    history = r.json()
    assert len(history) == 2  # user + assistant
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Domanda"
