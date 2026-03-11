"""Tests for web chat session management helpers."""
import uuid
from erpclaw.chat import _get_or_create_session_id, _get_history, _add_message, chat_sessions


def test_get_or_create_session_id_generates_uuid():
    """Se non c'è cookie, genera un UUID valido."""
    sid = _get_or_create_session_id(None)
    uuid.UUID(sid)  # lancia ValueError se non è UUID valido


def test_get_or_create_session_id_preserves_existing():
    """Se il cookie esiste, lo restituisce invariato."""
    existing = str(uuid.uuid4())
    assert _get_or_create_session_id(existing) == existing


def test_get_history_empty_for_new_session():
    """Sessione nuova ha storia vuota."""
    sid = str(uuid.uuid4())
    assert _get_history(sid) == []


def test_add_message_appends_entry():
    """add_message aggiunge entry con role e content."""
    sid = str(uuid.uuid4())
    _add_message(sid, "user", "ciao")
    _add_message(sid, "assistant", "risposta")
    history = _get_history(sid)
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "ciao"}
    assert history[1] == {"role": "assistant", "content": "risposta"}


def test_add_message_multiple_sessions_isolated():
    """Sessioni diverse hanno storie indipendenti."""
    sid1 = str(uuid.uuid4())
    sid2 = str(uuid.uuid4())
    _add_message(sid1, "user", "messaggio sid1")
    assert _get_history(sid2) == []
