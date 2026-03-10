import sys
from dataclasses import dataclass

from bubbleconf.parsers.cli_parser import parse_provided_cli_args
from bubbleconf import parse_config


@dataclass
class MyConfig:
    hosts: list[str]
    mode: str = "default"


def test_cli_parses_list(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["prog", "--hosts", "a.example", "b.example", "--mode", "fast"]
    )
    data = parse_provided_cli_args(MyConfig)
    assert "hosts" in data
    assert data["hosts"] == ["a.example", "b.example"]
    assert data["mode"] == "fast"


def test_cli_comma_separated_list(monkeypatch):
    """--hosts a.example,b.example should be split into a real list."""
    monkeypatch.setattr(
        sys, "argv", ["prog", "--hosts", "a.example,b.example,c.example"]
    )
    cfg = parse_config(MyConfig)
    assert cfg.hosts == ["a.example", "b.example", "c.example"]
