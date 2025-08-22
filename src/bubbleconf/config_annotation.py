# Annotation to denote a data class used for configuration


def config(cls):
    """
    Decorator to mark a dataclass as a configuration class.
    Usage:
        @config
        @dataclass
        class MyConfig:
            ...
    """
    if not hasattr(cls, "__dataclass_fields__"):
        raise TypeError(f"{cls.__name__} must also be annotated with @dataclass")
    cls.__is_config__ = True
    return cls
