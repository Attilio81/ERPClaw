"""Test per config_panel: funzioni parse_env / write_env e route GET/POST."""
import pytest
from pathlib import Path
from erpclaw.config_panel import parse_env, write_env


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
