from dataclasses import dataclass
from .config_annotation import config
from .parsers.config_error import ConfigError
from .parsers.parse_priority import parse_config_with_priority


@config
@dataclass
class MyConfig:
    name: str
    min_value: int
    max_value: int
    is_enabled: bool


def main():
    try:
        conf: MyConfig = parse_config_with_priority(MyConfig)
    except ConfigError as err:
        import sys

        is_tty = getattr(sys.stderr, "isatty", lambda: False)()
        print(err.format(is_tty), file=sys.stderr)
        sys.exit(2)
    else:
        print(conf)


if __name__ == "__main__":
    main()
