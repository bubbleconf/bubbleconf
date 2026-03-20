from dataclasses import MISSING, is_dataclass, fields
from logging import getLogger
import logging
import json
import os
from typing import Type, TypeVar, Iterable, Callable, Dict, Any, Optional

from .cli_parser import parse_provided_cli_args
from .env_parser import (
    provided_env_vars_for,
    _cast_str_to_type,
    _is_list_type,
    _resolve_field_type,
)
from .config_error import ConfigError

T = TypeVar("T")

logging.basicConfig()
__logger = getLogger("bubbleconf")
__level = os.environ.get("BUBBLECONF_LOG_LEVEL", "INFO")
__logger.setLevel(__level)


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
    report: bool = False,
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

    priority = tuple(priority or ("cli", "env", "json", "default"))

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
    provenance: Dict[str, Dict[str, Any]] = {}
    for field in fields(clazz):
        name = field.name
        ft = _resolve_field_type(field.type, clazz)
        chosen = False
        for src in priority:
            if src == "default":
                default = field.default if field.default != MISSING else None
                if default is None:
                    tname = getattr(ft, "__name__", str(ft))
                    missing.append(f"{name} (type: {tname})")
                else:
                    result[name] = default
                    provenance[name] = {
                        "source": "default",
                        "raw": None,
                        "value": result[name],
                    }
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
                # try to coerce via ft or accept as-is when types match.
                if isinstance(raw_val, str):
                    result[name] = _cast_str_to_type(raw_val, ft)
                elif isinstance(raw_val, list) and _is_list_type(ft):
                    # Flatten comma-separated entries so that e.g.
                    # ["a,b", "c"] becomes ["a", "b", "c"].
                    flat = []
                    for item in raw_val:
                        if isinstance(item, str) and "," in item:
                            flat.extend(s.strip() for s in item.split(","))
                        else:
                            flat.append(item)
                    result[name] = flat
                else:
                    # direct type match when the annotation is a runtime type
                    # (annotations can be strings or typing objects; guard
                    # against those). If we have a concrete class in
                    # ft, prefer isinstance match; otherwise try to
                    # call the type if it's callable. Fall back to the raw
                    # value when unsure.
                    assigned = False
                    # avoid passing typing generics (e.g. list[str]) to isinstance()
                    try:
                        if isinstance(ft, type) and isinstance(raw_val, ft):
                            result[name] = raw_val
                            assigned = True
                    except TypeError:
                        assigned = False

                    if not assigned:
                        # only attempt to call ft if it's a real runtime type
                        if isinstance(ft, type) and callable(ft):
                            try:
                                result[name] = ft(raw_val)
                            except Exception:
                                result[name] = raw_val
                        else:
                            result[name] = raw_val

                # record provenance for this field
                provenance[name] = {
                    "source": src,
                    "raw": raw_val,
                    "value": result[name],
                }
            except Exception as exc:
                malformed.append(f"{name}: {exc}")
            chosen = True
            break

        if not chosen:
            default = field.default if field.default != MISSING else None
            if default is None:
                tname = getattr(ft, "__name__", str(ft))
                missing.append(f"{name} (type: {tname})")
            else:
                result[name] = default
                provenance[name] = {
                    "source": "default",
                    "raw": None,
                    "value": result[name],
                }

    if missing or malformed:
        raise ConfigError(missing=missing, malformed=malformed)

    instance = clazz(**result)
    if report:
        log_parsed_config(provenance)

    return instance


def log_parsed_config(provenance):
    """Log provenance as a strictly aligned table.

    Columns: Field | Source | Raw | Value
    Raw and Value are compact JSON-serialized to keep table single-line cells.
    """
    __logger.debug("Config parsed successfully")

    # Build rows with compact JSON for raw/value
    rows = []
    for name, info in provenance.items():
        if isinstance(info, dict):
            src = info.get("source")
            raw = info.get("raw")
            val = info.get("value")
        else:
            src = None
            raw = None
            val = info

        # compact JSON for raw and value (None -> null)
        try:
            raw_s = json.dumps(raw, separators=(",", ":"), sort_keys=True)
        except Exception:
            raw_s = str(raw)
        try:
            val_s = json.dumps(val, separators=(",", ":"), sort_keys=True)
        except Exception:
            val_s = str(val)

        rows.append((name, str(src), raw_s, val_s))

    # compute column widths
    hdr = ("Field", "Source", "Raw", "Value")
    cols = list(zip(*([hdr] + rows))) if rows else list(zip(*([hdr])))
    widths = [max((len(c) for c in col), default=0) for col in cols]

    # build each cell using computed widths, then apply ANSI styling
    def _pad(cell: str, w: int) -> str:
        return cell.ljust(w)

    # styling codes
    BOLD = "\033[1m"
    RESET = "\033[0m"
    SOURCE_COLORS = {
        "cli": "\033[94m",
        "env": "\033[92m",
        "json": "\033[95m",
        "default": "\033[90m",
    }

    # header (bold)
    header_cells = [BOLD + _pad(hdr[i], widths[i]) + RESET for i in range(len(hdr))]
    __logger.debug("  %s  |  %s  |  %s  |  %s", *header_cells)

    # separator
    sep = "  " + "  |  ".join("-" * w for w in widths)
    __logger.debug(sep)

    # rows
    # styling for source column
    BOLD = "\033[1m"
    RESET = "\033[0m"
    SOURCE_COLORS = {
        "cli": "\033[93m",  # bright yellow
        "env": "\033[92m",  # bright green
        "json": "\033[95m",  # magenta
        "default": "\033[90m",  # dim gray
    }

    for r in rows:
        # pad cells
        padded = [_pad(r[i], widths[i]) for i in range(len(r))]
        # normalize and colorize source column (index 1)
        src_plain = (r[1] or "").lower()
        color = SOURCE_COLORS.get(src_plain)
        if color:
            padded[1] = color + BOLD + padded[1] + RESET

        __logger.debug("  %s  |  %s  |  %s  |  %s", *padded)
