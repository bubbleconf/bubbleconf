from dataclasses import MISSING
from typing import Type, TypeVar

T = TypeVar("T")


def _cast_str_to_type(value: str, to_type):
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
            result[field.name] = _cast_str_to_type(raw, field.type)

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
