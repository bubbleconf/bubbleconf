import sys
import unittest
from dataclasses import dataclass

from bubbleconf.parsers.cli_parser import (
    parse_config_from_cli_args,
    parse_provided_cli_args,
)


@dataclass
class SampleConfig:
    name: str
    min_value: int
    max_value: int
    is_enabled: bool


class CliParserTest(unittest.TestCase):
    def setUp(self):
        self._old_argv = list(sys.argv)

    def tearDown(self):
        sys.argv[:] = self._old_argv

    def test_parse_config_from_cli_args_success(self):
        sys.argv[:] = [
            "prog",
            "--name",
            "Bob",
            "--min_value",
            "1",
            "--max_value",
            "5",
            "--is_enabled",
            "True",
        ]
        conf = parse_config_from_cli_args(SampleConfig)
        self.assertEqual(conf.name, "Bob")
        self.assertEqual(conf.min_value, 1)
        self.assertEqual(conf.max_value, 5)
        self.assertTrue(conf.is_enabled)

    def test_case_insensitive_flags(self):
        sys.argv[:] = [
            "prog",
            "--NaMe",
            "Carol",
            "--MIN_VALUE",
            "2",
            "--Max_Value",
            "8",
            "--Is_Enabled",
            "True",
        ]
        conf = parse_config_from_cli_args(SampleConfig)
        self.assertEqual(conf.name, "Carol")
        self.assertEqual(conf.min_value, 2)
        self.assertEqual(conf.max_value, 8)
        self.assertTrue(conf.is_enabled)

    def test_parse_provided_cli_args_only_returns_provided(self):
        sys.argv[:] = ["prog", "--name", "Dana", "--min_value", "4"]
        provided = parse_provided_cli_args(SampleConfig)
        self.assertEqual(provided, {"name": "Dana", "min_value": "4"})


if __name__ == "__main__":
    unittest.main()
