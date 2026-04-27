import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from bubbleconf.parsers.parse_priority import parse_config
from bubbleconf.parsers.dotenv_parser import (
    _parse_dotenv_text,
    load_dotenv_file,
    provided_dotenv_vars_for,
)


@dataclass
class SampleConfig:
    name: str
    min_value: int
    max_value: int
    is_enabled: bool


@pytest.fixture(autouse=True)
def preserved_env():
    old = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


@pytest.fixture
def chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_parse_dotenv_text_basic():
    text = """
    # a comment
    NAME=Alice
    MIN_VALUE=3
    MAX_VALUE = 7
    IS_ENABLED=true
    """
    parsed = _parse_dotenv_text(text)
    assert parsed == {
        "NAME": "Alice",
        "MIN_VALUE": "3",
        "MAX_VALUE": "7",
        "IS_ENABLED": "true",
    }


def test_parse_dotenv_text_quotes_export_and_inline_comment():
    text = (
        'export NAME="Bob the Builder"\n'
        "GREETING='hello # world'\n"
        "MIN_VALUE=4  # inline comment\n"
        "URL=https://example.com/#anchor\n"
    )
    parsed = _parse_dotenv_text(text)
    assert parsed["NAME"] == "Bob the Builder"
    assert parsed["GREETING"] == "hello # world"
    assert parsed["MIN_VALUE"] == "4"
    # '#anchor' is part of the value because '#' is not preceded by whitespace
    assert parsed["URL"] == "https://example.com/#anchor"


def test_parse_dotenv_text_skips_malformed_lines():
    text = "VALID=1\nNOT_AN_ASSIGNMENT\n=missing_key\n"
    parsed = _parse_dotenv_text(text)
    assert parsed == {"VALID": "1"}


def test_load_dotenv_file_missing_returns_empty(chdir_tmp):
    assert load_dotenv_file() == {}


def test_load_dotenv_file_default_path(chdir_tmp):
    (chdir_tmp / ".env").write_text("NAME=Alice\n")
    assert load_dotenv_file() == {"NAME": "Alice"}


def test_load_dotenv_file_honours_dotenv_file_env(chdir_tmp, monkeypatch):
    custom = chdir_tmp / "custom.env"
    custom.write_text("NAME=Custom\n")
    monkeypatch.setenv("DOTENV_FILE", str(custom))
    assert load_dotenv_file() == {"NAME": "Custom"}


def test_provided_dotenv_vars_for_case_insensitive(chdir_tmp):
    (chdir_tmp / ".env").write_text(
        "name=Alice\nMIN_VALUE=3\nmax_value=7\nIS_ENABLED=true\n"
    )
    out = provided_dotenv_vars_for(SampleConfig)
    assert out == {
        "name": "Alice",
        "min_value": "3",
        "max_value": "7",
        "is_enabled": "true",
    }


def test_parse_config_uses_dotenv_source(chdir_tmp):
    (chdir_tmp / ".env").write_text(
        "NAME=Alice\nMIN_VALUE=3\nMAX_VALUE=7\nIS_ENABLED=true\n"
    )
    cfg = parse_config(SampleConfig, priority=("dotenv", "default"))
    assert cfg.name == "Alice"
    assert cfg.min_value == 3
    assert cfg.max_value == 7
    assert cfg.is_enabled is True


def test_parse_config_env_takes_priority_over_dotenv(chdir_tmp, monkeypatch):
    (chdir_tmp / ".env").write_text(
        "NAME=FromDotenv\nMIN_VALUE=1\nMAX_VALUE=2\nIS_ENABLED=false\n"
    )
    monkeypatch.setenv("NAME", "FromEnv")
    cfg = parse_config(SampleConfig, priority=("env", "dotenv", "default"))
    assert cfg.name == "FromEnv"
    # Other fields fall back to dotenv
    assert cfg.min_value == 1
    assert cfg.max_value == 2
    assert cfg.is_enabled is False


def test_parse_config_dotenv_in_default_priority(chdir_tmp):
    (chdir_tmp / ".env").write_text(
        "NAME=Alice\nMIN_VALUE=3\nMAX_VALUE=7\nIS_ENABLED=true\n"
    )
    # Default priority should now include 'dotenv'.
    cfg = parse_config(SampleConfig)
    assert cfg.name == "Alice"
    assert cfg.is_enabled is True
