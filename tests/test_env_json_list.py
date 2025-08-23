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
