import logging
import os
from dataclasses import dataclass
from typing import Annotated

import pytest

from bubbleconf import Secret, parse_config


@dataclass
class AnnotatedConfig:
    name: str
    api_key: Annotated[str, Secret]
    port: Annotated[int, Secret] = 5432
    debug: bool = False


@pytest.fixture(autouse=True)
def preserved_env():
    old = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


def test_annotated_secret_redacted_in_pretty_log(caplog, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("NAME", "svc")
    monkeypatch.setenv("API_KEY", "supersecret123")
    monkeypatch.setenv("PORT", "9000")

    caplog.set_level(logging.INFO, logger="bubbleconf")
    cfg = parse_config(AnnotatedConfig, pretty_log=True)

    # Real values preserved on the instance, with proper type casting through Annotated.
    assert cfg.api_key == "supersecret123"
    assert cfg.port == 9000
    assert isinstance(cfg.port, int)

    log_text = "\n".join(r.getMessage() for r in caplog.records)
    assert "supersecret123" not in log_text
    assert "9000" not in log_text
    assert "***" in log_text
    # Non-secret name still visible
    assert "svc" in log_text


def test_annotated_secret_redacted_from_default(caplog, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("NAME", "svc")
    monkeypatch.setenv("API_KEY", "k")

    caplog.set_level(logging.INFO, logger="bubbleconf")
    cfg = parse_config(AnnotatedConfig, pretty_log=True)
    assert cfg.port == 5432  # default

    log_text = "\n".join(r.getMessage() for r in caplog.records)
    assert "5432" not in log_text
    assert "***" in log_text


def test_annotated_secret_redacted_in_debug_report(caplog, monkeypatch):
    monkeypatch.setenv("NAME", "svc")
    monkeypatch.setenv("API_KEY", "supersecret123")

    caplog.set_level(logging.DEBUG, logger="bubbleconf")
    parse_config(AnnotatedConfig, report=True)

    log_text = "\n".join(r.getMessage() for r in caplog.records)
    assert "supersecret123" not in log_text
    assert "***" in log_text
