from dataclasses import MISSING
import builtins
from typing import Type, TypeVar, get_origin, get_args, get_type_hints

T = TypeVar("T")


def _is_list_type(tp) -> bool:
    """Return True when *tp* is ``list``, ``list[X]``, or ``List[X]``."""
    return tp is list or get_origin(tp) is list


def _cast_str_to_type(value: str, to_type):
    # quick JSON detection: if the string looks like a JSON array or object,
    # attempt to parse it so env vars like '["a","b"]' become lists.
    try:
        s = value.strip()
        if (s.startswith("[") and s.endswith("]")) or (
            s.startswith("{") and s.endswith("}")
        ):
            import json

            try:
                return json.loads(s)
            except Exception:
                # fall through to normal casting
                pass
    except Exception:
        pass

    if _is_list_type(to_type):
        # comma-separated string → list, e.g. "a,b,c" → ["a", "b", "c"]
        items = [item.strip() for item in value.split(",")]
        # if the generic has an inner type (e.g. list[int]), cast each element
        inner_args = get_args(to_type)
        if inner_args and inner_args[0] is not str:
            return [_cast_str_to_type(item, inner_args[0]) for item in items]
        return items

    if to_type is int:
        return int(value)
    if to_type is float:
        return float(value)
    if to_type is bool:
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"Cannot parse boolean value from '{value}'")
    if to_type is str:
        return value
    try:
        return to_type(value)
    except Exception:
        return value


def _resolve_field_type(field_type, clazz: type):
    """Resolve a possibly-stringified annotation to a real type."""
    if isinstance(field_type, type):
        return field_type
    if isinstance(field_type, str):
        # Try get_type_hints first (handles 'list[int]' etc.)
        try:
            hints = get_type_hints(clazz)
            for _name, hint in hints.items():
                if str(field_type) == str(hint) or (
                    hasattr(hint, "__name__") and hint.__name__ == field_type
                ):
                    return hint
        except Exception:
            pass
        resolved = getattr(builtins, field_type, None)
        if isinstance(resolved, type):
            return resolved
    return field_type


def parse_config_from_env_vars(clazz: Type[T]) -> T:
    """Parse configuration from environment variables (case-insensitive).

    For each dataclass field `name`, checks `name`, `NAME`, and lowercase
    variants in the environment. If a field has no default, it's required.
    """
    import os

    if not hasattr(clazz, "__dataclass_fields__"):
        raise TypeError(f"{clazz.__name__} must be a dataclass")

    env = os.environ
    env_ci = {k.lower(): v for k, v in env.items()}

    result = {}
    for field in clazz.__dataclass_fields__.values():  # type: ignore
        candidates = [field.name, field.name.upper(), field.name.lower()]
        raw = None
        for key in candidates:
            if key in env:
                raw = env[key]
                break
            if key.lower() in env_ci:
                raw = env_ci[key.lower()]
                break

        if raw is None:
            default = field.default if field.default != MISSING else None
            if default is None:
                tried = ", ".join(candidates)
                raise EnvironmentError(
                    f"Required environment variable for field '{field.name}' not set (tried: {tried})"
                )
            result[field.name] = default
        else:
            ft = _resolve_field_type(field.type, clazz)
            result[field.name] = _cast_str_to_type(raw, ft)

    return clazz(**result)


def provided_env_vars_for(clazz: Type[T]) -> dict:
    """Return a dict of env var values (strings) for fields that are present.

    Keys are the dataclass field names. Lookup is case-insensitive.
    """
    import os

    if not hasattr(clazz, "__dataclass_fields__"):
        raise TypeError(f"{clazz.__name__} must be a dataclass")

    env = os.environ
    env_ci = {k.lower(): v for k, v in env.items()}
    out = {}
    for field in clazz.__dataclass_fields__.values():  # type: ignore
        for key in (field.name, field.name.upper(), field.name.lower()):
            if key in env:
                out[field.name] = env[key]
                break
            if key.lower() in env_ci:
                out[field.name] = env_ci[key.lower()]
                break
    return out
