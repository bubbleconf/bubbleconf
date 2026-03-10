from dataclasses import dataclass

from bubbleconf import parse_config


@dataclass
class EnvConfig:
    hosts: list[str]
    debug: bool = False


def test_env_json_list(monkeypatch):
    monkeypatch.setenv("HOSTS", '["a.example","b.example"]')
    cfg = parse_config(EnvConfig)
    assert isinstance(cfg.hosts, list)
    assert cfg.hosts == ["a.example", "b.example"]


def test_env_comma_separated_list(monkeypatch):
    monkeypatch.setenv("HOSTS", "a.example,b.example,c.example")
    cfg = parse_config(EnvConfig)
    assert isinstance(cfg.hosts, list)
    assert cfg.hosts == ["a.example", "b.example", "c.example"]


def test_env_comma_separated_list_with_spaces(monkeypatch):
    monkeypatch.setenv("HOSTS", "a.example , b.example , c.example")
    cfg = parse_config(EnvConfig)
    assert cfg.hosts == ["a.example", "b.example", "c.example"]


@dataclass
class IntListConfig:
    ports: list[int]
    mode: str = "default"


def test_env_comma_separated_int_list(monkeypatch):
    monkeypatch.setenv("PORTS", "80,443,8080")
    cfg = parse_config(IntListConfig)
    assert cfg.ports == [80, 443, 8080]
