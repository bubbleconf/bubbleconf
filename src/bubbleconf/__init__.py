"""Public API for the ``bubbleconf`` package.

This package exposes a compact, well-documented surface intended for
consumers of the library. The public API is intentionally small:

- ``config`` — a decorator used to mark configuration dataclasses.
- ``parse_config`` — the high-level function that populates a dataclass
    from configuration sources (CLI, environment, JSON, ...).
- ``ConfigError`` — exception raised when required fields are missing or
    values are malformed.

Implementation details (parsers, helpers, and other internals) are
considered private and are not exported from the package root. This
keeps tab-completion, documentation, and the surface area focused on what
users really need. If you need to access internals, import the specific
submodule directly, for example:

        import bubbleconf.parsers.parse_priority

The package enforces this policy at runtime by limiting what attributes
are available on ``bubbleconf`` itself; attempting to access an internal
name will raise ``AttributeError`` with guidance to import the appropriate
submodule.

Examples
--------
from bubbleconf import config, parse_config

@config
class MyConfig:
        host: str
        port: int = 8080

cfg = parse_config(MyConfig)
"""

from .config_annotation import config
from .parsers.parse_priority import parse_config
from .parsers.config_error import ConfigError

__all__ = ["config", "parse_config", "ConfigError"]


def __getattr__(name: str):
    """Provide only the public attributes listed in ``__all__``.

    Accessing other attributes on the package will raise AttributeError with
    a helpful message directing users to import the intended submodule
    (for example: ``from bubbleconf.parsers import parse_priority``).
    """
    if name in __all__:
        return globals()[name]

    raise AttributeError(
        f"'{name}' is internal to the 'bubbleconf' package; import the\n"
        f"submodule explicitly (for example: 'import bubbleconf.parsers')."
    )


def __dir__():
    # Show only the public API during tab-completion.
    return sorted(list(__all__))
