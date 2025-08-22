from dataclasses import dataclass

from bubbleconf import parse_config, config


@config
@dataclass
class MyConfig:
    version: str
    is_cool: bool
    number_of_things: int
    ratio: float


def main():
    my_config = parse_config(MyConfig)
    print(my_config)


if __name__ == "__main__":
    main()
