import os
import json
from dataclasses import dataclass
import pytest

from bubbleconf.parsers.parse_priority import parse_config


@dataclass
class SampleConfig:
    name: str
    min_value: int
    max_value: int
    is_enabled: bool


@pytest.fixture(autouse=True)
def preserved_env():
    """Preserve and restore the process environment for each test."""
    old = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


def test_json_env_var_parsing():
    payload = {"name": "Alice", "min_value": 3, "max_value": 7, "is_enabled": True}
    os.environ["CONFIG_JSON"] = json.dumps(payload)

    conf = parse_config(SampleConfig, priority=("json", "default"))

    assert conf.name == "Alice"
    assert conf.min_value == 3
    assert conf.max_value == 7
    assert conf.is_enabled is True
