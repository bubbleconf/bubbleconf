import os
import json
import unittest
from dataclasses import dataclass

from pyconf.parsers.parse_priority import parse_config_with_priority


@dataclass
class SampleConfig:
    name: str
    min_value: int
    max_value: int
    is_enabled: bool


class JsonSourceTest(unittest.TestCase):
    def setUp(self):
        # preserve environment
        self._old_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    def test_json_env_var_parsing(self):
        payload = {"name": "Alice", "min_value": 3, "max_value": 7, "is_enabled": True}
        os.environ["CONFIG_JSON"] = json.dumps(payload)

        conf = parse_config_with_priority(SampleConfig, priority=("json", "default"))

        self.assertEqual(conf.name, "Alice")
        self.assertEqual(conf.min_value, 3)
        self.assertEqual(conf.max_value, 7)
        self.assertTrue(conf.is_enabled)


if __name__ == "__main__":
    unittest.main()
