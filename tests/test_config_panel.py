"""Test per config_panel: funzioni parse_env / write_env e route GET/POST."""
import pytest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from erpclaw.config_panel import parse_env, write_env, router


# ── parse_env ────────────────────────────────────────────────────────────────

def test_parse_env_reads_key_value(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nBAZ=qux\n")
    assert parse_env(env) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# commento\nFOO=bar\n")
    assert parse_env(env) == {"FOO": "bar"}


def test_parse_env_ignores_blank_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("\nFOO=bar\n\n")
    assert parse_env(env) == {"FOO": "bar"}


def test_parse_env_returns_empty_for_missing_file(tmp_path):
    assert parse_env(tmp_path / "nonexistent.env") == {}


def test_parse_env_handles_value_with_equals(tmp_path):
    env = tmp_path / ".env"
    env.write_text("TOKEN=abc=def=ghi\n")
    assert parse_env(env) == {"TOKEN": "abc=def=ghi"}


# ── write_env ────────────────────────────────────────────────────────────────

def test_write_env_updates_existing_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=old\n")
    write_env(env, {"FOO": "new"})
    assert parse_env(env) == {"FOO": "new"}


def test_write_env_preserves_comments(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# commento\nFOO=old\n")
    write_env(env, {"FOO": "new"})
    content = env.read_text()
    assert "# commento" in content
    assert "FOO=new" in content


def test_write_env_adds_missing_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    write_env(env, {"FOO": "bar", "NEW_KEY": "val"})
    assert parse_env(env)["NEW_KEY"] == "val"


def test_write_env_creates_file_if_missing(tmp_path):
    env = tmp_path / ".env"
    write_env(env, {"FOO": "bar"})
    assert parse_env(env) == {"FOO": "bar"}


def test_write_env_preserves_other_keys(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=keep\nBAR=update\n")
    write_env(env, {"BAR": "new"})
    result = parse_env(env)
    assert result["FOO"] == "keep"
    assert result["BAR"] == "new"


# ── Route tests ──────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=True)


def test_get_config_returns_200(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    response = client.get("/config/")
    assert response.status_code == 200


def test_get_config_shows_saved_banner(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    response = client.get("/config/?saved=true")
    assert b"salvata" in response.content


def test_post_config_redirects(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    response = client.post("/config/", data={"LLM_PROVIDER": "deepseek", "LLM_MODEL_ID": "deepseek-reasoner",
        "LMSTUDIO_BASE_URL": "", "OPENAI_API_KEY": "", "DEEPSEEK_API_KEY": "sk-test",
        "TELEGRAM_BOT_TOKEN": "", "ALLOWED_CHAT_ID": "", "SHOP_SECRET_KEY": ""},
        follow_redirects=False)
    assert response.status_code == 303
    assert "/config/" in response.headers["location"]


def test_post_config_writes_env(client, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    client.post("/config/", data={"LLM_PROVIDER": "deepseek", "LLM_MODEL_ID": "deepseek-reasoner",
        "LMSTUDIO_BASE_URL": "http://localhost:1234/v1", "OPENAI_API_KEY": "",
        "DEEPSEEK_API_KEY": "sk-test", "TELEGRAM_BOT_TOKEN": "", "ALLOWED_CHAT_ID": "",
        "SHOP_SECRET_KEY": ""})
    result = parse_env(env)
    assert result["LLM_PROVIDER"] == "deepseek"
    assert result["DEEPSEEK_API_KEY"] == "sk-test"


# ── JSON API endpoints ────────────────────────────────────────────────────────

def test_api_get_returns_all_keys(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=deepseek\nTELEGRAM_BOT_TOKEN=tok123\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.get("/config/api")
    assert r.status_code == 200
    data = r.json()
    assert data["LLM_PROVIDER"] == "deepseek"
    assert data["TELEGRAM_BOT_TOKEN"] == "tok123"
    assert data["ALLOWED_CHAT_ID"] == ""   # not in file → empty string


def test_api_put_updates_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=lmstudio\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.put("/config/api", json={"LLM_PROVIDER": "deepseek"})
    assert r.status_code == 200
    assert r.json()["LLM_PROVIDER"] == "deepseek"
    assert "LLM_PROVIDER=deepseek" in env.read_text()


def test_api_put_ignores_unknown_keys(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.put("/config/api", json={"UNKNOWN_KEY": "hack", "LLM_PROVIDER": "deepseek"})
    assert r.status_code == 200
    assert "UNKNOWN_KEY" not in env.read_text()


def test_api_put_null_value_writes_empty_string(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("TELEGRAM_BOT_TOKEN=existing\n")
    monkeypatch.setattr("erpclaw.config_panel.ENV_PATH", env)
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.put("/config/api", json={"TELEGRAM_BOT_TOKEN": None})
    assert r.status_code == 200
    content = env.read_text()
    assert "TELEGRAM_BOT_TOKEN=None" not in content
    assert "TELEGRAM_BOT_TOKEN=" in content
