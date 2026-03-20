"""Tests for PEP 563 ``from __future__ import annotations`` compatibility.

When ``from __future__ import annotations`` is active, dataclass field.type
is a *string* (e.g. ``'int'``) instead of the actual type object.  The
parser must resolve these strings before casting.
"""

from __future__ import annotations

import os
import sys
import unittest
from dataclasses import dataclass

from bubbleconf import parse_config
from bubbleconf.parsers.env_parser import parse_config_from_env_vars


@dataclass(frozen=True)
class FutureConfig:
    name: str
    count: int
    ratio: float
    enabled: bool


class FutureAnnotationsEnvTest(unittest.TestCase):
    """parse_config_from_env_vars should cast correctly with stringified types."""

    def setUp(self):
        self._env_backup = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_env_vars_cast_int_and_float(self):
        os.environ["NAME"] = "test"
        os.environ["COUNT"] = "42"
        os.environ["RATIO"] = "3.14"
        os.environ["ENABLED"] = "true"

        config = parse_config_from_env_vars(FutureConfig)

        self.assertIsInstance(config.count, int)
        self.assertEqual(config.count, 42)
        self.assertIsInstance(config.ratio, float)
        self.assertAlmostEqual(config.ratio, 3.14)
        self.assertIsInstance(config.enabled, bool)
        self.assertTrue(config.enabled)
        self.assertEqual(config.name, "test")


class FutureAnnotationsPriorityTest(unittest.TestCase):
    """parse_config with priority should cast correctly with stringified types."""

    def setUp(self):
        self._env_backup = dict(os.environ)
        self._old_argv = list(sys.argv)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)
        sys.argv[:] = self._old_argv

    def test_env_priority_casts_types(self):
        os.environ["NAME"] = "hello"
        os.environ["COUNT"] = "7"
        os.environ["RATIO"] = "2.5"
        os.environ["ENABLED"] = "false"

        config = parse_config(FutureConfig, priority=("env", "default"))

        self.assertIsInstance(config.count, int)
        self.assertEqual(config.count, 7)
        self.assertIsInstance(config.ratio, float)
        self.assertAlmostEqual(config.ratio, 2.5)
        self.assertIsInstance(config.enabled, bool)
        self.assertFalse(config.enabled)

    def test_cli_priority_casts_types(self):
        sys.argv[:] = [
            "prog",
            "--name",
            "world",
            "--count",
            "99",
            "--ratio",
            "1.5",
            "--enabled",
            "yes",
        ]

        config = parse_config(FutureConfig, priority=("cli", "default"))

        self.assertIsInstance(config.count, int)
        self.assertEqual(config.count, 99)
        self.assertIsInstance(config.ratio, float)
        self.assertAlmostEqual(config.ratio, 1.5)
        self.assertIsInstance(config.enabled, bool)
        self.assertTrue(config.enabled)


if __name__ == "__main__":
    unittest.main()
