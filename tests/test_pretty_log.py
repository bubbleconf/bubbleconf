import logging
import os
from dataclasses import dataclass

import pytest

from bubbleconf.parsers.parse_priority import parse_config, pretty_log_config


@dataclass
class SampleConfig:
    name: str
    port: int = 8080
    debug: bool = False


@pytest.fixture(autouse=True)
def preserved_env():
    old = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


def test_pretty_log_emits_info_records(caplog, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("NAME", "Alice")
    monkeypatch.setenv("PORT", "9000")

    caplog.set_level(logging.INFO, logger="bubbleconf")
    cfg = parse_config(SampleConfig, pretty_log=True)

    assert cfg.name == "Alice"
    assert cfg.port == 9000

    info_messages = [
        r.getMessage() for r in caplog.records if r.levelno == logging.INFO
    ]
    joined = "\n".join(info_messages)
    assert "Resolved configuration: SampleConfig" in joined
    assert "Field" in joined and "Value" in joined and "Source" in joined
    assert "name" in joined and "Alice" in joined
    assert "port" in joined and "9000" in joined
    assert "debug" in joined
    # box characters
    assert "\u2502" in joined
    assert "\u250c" in joined and "\u2518" in joined


def test_pretty_log_off_by_default(caplog):
    caplog.set_level(logging.INFO, logger="bubbleconf")
    os.environ["NAME"] = "Alice"
    parse_config(SampleConfig)
    info_messages = [
        r.getMessage() for r in caplog.records if r.levelno == logging.INFO
    ]
    assert all("Resolved configuration" not in m for m in info_messages)


def test_pretty_log_no_color_when_no_color_env(monkeypatch, caplog):
    monkeypatch.setenv("NO_COLOR", "1")
    caplog.set_level(logging.INFO, logger="bubbleconf")
    pretty_log_config(
        "Demo",
        {"name": {"source": "env", "raw": "Alice", "value": "Alice"}},
    )
    info_messages = [
        r.getMessage() for r in caplog.records if r.levelno == logging.INFO
    ]
    joined = "\n".join(info_messages)
    assert "\033[" not in joined


def test_pretty_log_force_color(monkeypatch, caplog):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("BUBBLECONF_FORCE_COLOR", "1")
    caplog.set_level(logging.INFO, logger="bubbleconf")
    pretty_log_config(
        "Demo",
        {"name": {"source": "env", "raw": "Alice", "value": "Alice"}},
    )
    info_messages = [
        r.getMessage() for r in caplog.records if r.levelno == logging.INFO
    ]
    joined = "\n".join(info_messages)
    assert "\033[" in joined
