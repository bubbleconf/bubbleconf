"""Parser for ``.env`` files.

Supports a small, common subset of the ``.env`` syntax used by tools like
`python-dotenv` and `direnv`:

- ``KEY=VALUE`` pairs, one per line.
- Blank lines and lines starting with ``#`` are ignored.
- Trailing comments after an unquoted value (``KEY=foo  # note``) are stripped.
- Optional leading ``export`` keyword (``export KEY=VALUE``).
- Values may be wrapped in single or double quotes; quotes are stripped.
- Whitespace around the key and (unquoted) value is trimmed.

No external dependency is required.
"""

from __future__ import annotations

import os
from typing import Dict, Type, TypeVar

T = TypeVar("T")


def _strip_inline_comment(value: str) -> str:
    """Strip an unquoted trailing ``# comment`` from *value*."""
    # Only strip when the '#' is preceded by whitespace (or starts the value),
    # so values like 'color#1' are preserved.
    out_chars = []
    prev_ws = True
    for ch in value:
        if ch == "#" and prev_ws:
            break
        out_chars.append(ch)
        prev_ws = ch.isspace()
    return "".join(out_chars).rstrip()


def _parse_dotenv_text(text: str) -> Dict[str, str]:
    """Parse the contents of a ``.env`` file into a dict of strings."""
    out: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].lstrip()

        if "=" not in line:
            # Skip malformed lines silently to mirror the lenient behavior of
            # the JSON source.
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue

        value = value.lstrip()
        if value[:1] in {'"', "'"}:
            quote = value[0]
            end = value.find(quote, 1)
            if end != -1:
                value = value[1:end]
            else:
                # Unterminated quote: take the rest verbatim, minus the quote.
                value = value[1:]
        else:
            value = _strip_inline_comment(value)

        out[key] = value
    return out


def _resolve_dotenv_path() -> str:
    """Return the path to the ``.env`` file to load."""
    return os.environ.get("DOTENV_FILE") or ".env"


def load_dotenv_file(path: str | None = None) -> Dict[str, str]:
    """Load and parse a ``.env`` file. Returns an empty dict if missing."""
    target = path or _resolve_dotenv_path()
    try:
        with open(target, "r", encoding="utf-8") as fh:
            return _parse_dotenv_text(fh.read())
    except FileNotFoundError:
        return {}
    except OSError:
        return {}


def provided_dotenv_vars_for(clazz: Type[T]) -> Dict[str, str]:
    """Return ``.env``-provided values for fields of *clazz*.

    Lookup is case-insensitive and matches the conventions used by
    :func:`provided_env_vars_for`: each field is tried as ``name``,
    ``NAME``, and ``name.lower()``.
    """
    if not hasattr(clazz, "__dataclass_fields__"):
        raise TypeError(f"{clazz.__name__} must be a dataclass")

    values = load_dotenv_file()
    if not values:
        return {}

    values_ci = {k.lower(): v for k, v in values.items()}

    out: Dict[str, str] = {}
    for field in clazz.__dataclass_fields__.values():  # type: ignore[attr-defined]
        for key in (field.name, field.name.upper(), field.name.lower()):
            if key in values:
                out[field.name] = values[key]
                break
            if key.lower() in values_ci:
                out[field.name] = values_ci[key.lower()]
                break
    return out
