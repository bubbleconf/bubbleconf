from dataclasses import MISSING
from typing import Type, TypeVar
import sys
import argparse

T = TypeVar("T")


def parse_config_from_cli_args(clazz: Type[T]) -> T:
    """Parse configuration from command line arguments.

    Long option names are matched case-insensitively by lowercasing
    tokens that start with `--` before parsing.
    """
    if not hasattr(clazz, "__dataclass_fields__"):
        raise TypeError(f"{clazz.__name__} must be a dataclass")

    parser = argparse.ArgumentParser(description=f"Configuration for {clazz.__name__}")
    for field in clazz.__dataclass_fields__.values():  # type: ignore
        default = field.default if field.default != MISSING else None
        if default is None:
            parser.add_argument(f"--{field.name}", type=field.type, required=True)
        else:
            parser.add_argument(f"--{field.name}", type=field.type, default=default)

    # Simple case-insensitive normalization: lowercase long option tokens
    normalized = [a.lower() if a.startswith("--") else a for a in sys.argv[1:]]
    args = parser.parse_args(normalized)

    return clazz(
        **{
            field.name: getattr(args, field.name)
            for field in clazz.__dataclass_fields__.values()  # type: ignore
        }
    )


def parse_provided_cli_args(clazz: Type[T]) -> dict:
    """Return a dict of only the CLI-provided values for the dataclass fields.

    This function builds the same parser as `parse_config_from_cli_args` but
    uses argparse.SUPPRESS for defaults so that only explicitly provided
    options appear in the result.
    """
    import argparse
    import sys

    if not hasattr(clazz, "__dataclass_fields__"):
        raise TypeError(f"{clazz.__name__} must be a dataclass")

    parser = argparse.ArgumentParser(add_help=False)
    for field in clazz.__dataclass_fields__.values():  # type: ignore
        # don't supply a default so argparse will suppress missing values
        # use type=str so we can perform centralized validation and collect
        # all malformed-field errors instead of letting argparse exit.
        parser.add_argument(f"--{field.name}", type=str, default=argparse.SUPPRESS)

    normalized = [a.lower() if a.startswith("--") else a for a in sys.argv[1:]]
    ns, _ = parser.parse_known_args(normalized)
    return vars(ns)
