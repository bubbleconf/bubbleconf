from dataclasses import MISSING, is_dataclass, fields
from typing import Type, TypeVar, Iterable, Callable, Dict, Any, Optional

from .cli_parser import parse_provided_cli_args
from .env_parser import provided_env_vars_for, _cast_str_to_type
from .config_error import ConfigError

T = TypeVar("T")


def _json_source(clazz: Type[T]) -> Dict[str, Any]:
    """Example resolver that loads JSON configuration.

    Looks for a JSON string in the environment variable `CONFIG_JSON`, then
    a file path in `CONFIG_JSON_FILE`, and finally a file named
    `config.json` in the current working directory. If none are present,
    returns an empty dict.

    The returned mapping should be field-name -> value (strings or typed
    values). Values that are strings will still be passed through the
    standard caster in this module.
    """
    import os
    import json

    # prefer direct JSON in an env var
    raw = os.environ.get("CONFIG_JSON")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # then an env var pointing to a file
    path = os.environ.get("CONFIG_JSON_FILE") or "config.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def parse_config(
    clazz: Type[T],
    priority: Iterable[str] | None = None,
    sources: Optional[Dict[str, Callable[[Type[T]], Dict[str, Any]]]] = None,
) -> T:
    """For each field, choose its value based on `priority`.

    `priority` is an iterable of source names in preference order. Built-in
    sources include: 'cli', 'env', and the example 'json'. 'default' is a
    special name that falls back to dataclass defaults. If `priority` is
    None, the default order is ('cli', 'env', 'default').

    Returns an instance of the dataclass or raises `ConfigError` with
    aggregated missing/malformed information.
    """
    if not is_dataclass(clazz):
        raise TypeError(f"{clazz.__name__} must be a dataclass")

    # Build resolvers map (name -> resolver callable). Built-ins are added
    # first, then user-provided `sources` (if any) are merged in. This makes
    # built-in and custom sources equivalent: callers can override built-ins
    # by supplying the same key in `sources`.
    resolvers: Dict[str, Callable[[Type[T]], Dict[str, Any]]] = {
        "cli": parse_provided_cli_args,
        "env": provided_env_vars_for,
        "json": _json_source,  # example built-in resolver
    }
    if sources:
        resolvers.update(sources)

    priority = tuple(priority or ("cli", "env", "default"))

    # Validate that non-'default' entries exist in resolvers
    unknown = [p for p in priority if p != "default" and p not in resolvers]
    if unknown:
        raise ValueError(
            f"Unknown source(s) in priority: {unknown}; available: {list(resolvers)} + ['default']"
        )

    # collect provided source maps once (call resolvers lazily)
    cache: Dict[str, Dict[str, Any]] = {}

    result: Dict[str, Any] = {}
    missing = []
    malformed = []

    for field in fields(clazz):
        name = field.name
        chosen = False
        for src in priority:
            if src == "default":
                default = field.default if field.default != MISSING else None
                if default is None:
                    tname = getattr(field.type, "__name__", str(field.type))
                    missing.append(f"{name} (type: {tname})")
                else:
                    result[name] = default
                chosen = True
                break

            # load resolver output into cache on first use
            if src not in cache:
                cache[src] = resolvers[src](clazz)

            src_map = cache[src]
            if name not in src_map:
                continue

            raw_val = src_map[name]
            try:
                # If value is a string, use the standard caster; otherwise
                # try to coerce via field.type or accept as-is when types match.
                if isinstance(raw_val, str):
                    result[name] = _cast_str_to_type(raw_val, field.type)
                else:
                    # direct type match when the annotation is a runtime type
                    # (annotations can be strings or typing objects; guard
                    # against those). If we have a concrete class in
                    # field.type, prefer isinstance match; otherwise try to
                    # call the type if it's callable. Fall back to the raw
                    # value when unsure.
                    ft = field.type
                    if isinstance(ft, type) and isinstance(raw_val, ft):
                        result[name] = raw_val
                    else:
                        # only attempt to call ft if it's a real type
                        # (and not a string or typing construct)
                        if isinstance(ft, type) and callable(ft):
                            try:
                                result[name] = ft(raw_val)
                            except Exception:
                                result[name] = raw_val
                        else:
                            result[name] = raw_val
            except Exception as exc:
                malformed.append(f"{name}: {exc}")
            chosen = True
            break

        if not chosen:
            default = field.default if field.default != MISSING else None
            if default is None:
                tname = getattr(field.type, "__name__", str(field.type))
                missing.append(f"{name} (type: {tname})")
            else:
                result[name] = default

    if missing or malformed:
        raise ConfigError(missing=missing, malformed=malformed)

    return clazz(**result)
