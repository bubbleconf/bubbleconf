"""Marker types for annotating dataclass fields with bubbleconf semantics.

These markers are designed to be used with :data:`typing.Annotated`, e.g.::

    from typing import Annotated
    from dataclasses import dataclass
    from bubbleconf import Secret, parse_config

    @dataclass
    class ServiceConfig:
        name: str
        api_key: Annotated[str, Secret]

The marker is detected by inspecting the field's resolved type hints.
"""

from __future__ import annotations


class _SecretMarker:
    """Sentinel value indicating a field holds sensitive data."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "Secret"


# Public, importable singleton. Use as ``Annotated[str, Secret]``.
Secret = _SecretMarker()


def is_secret_annotation(metadata: tuple) -> bool:
    """Return True when an ``Annotated`` metadata tuple marks a secret field."""
    for entry in metadata:
        if entry is Secret or isinstance(entry, _SecretMarker):
            return True
        # also accept the bare class for users who write ``Annotated[str, Secret]``
        # where ``Secret`` was rebound to the class itself
        if entry is _SecretMarker:
            return True
    return False
