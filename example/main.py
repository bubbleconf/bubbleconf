from dataclasses import dataclass

from bubbleconf import config, parse_config


@config
@dataclass
class ServiceConfig:
    """A sample service configuration used by the combined-sources demo.

    Sources used (in precedence order): CLI, environment, JSON file, dataclass defaults.
    The built-in JSON resolver will look for CONFIG_JSON, CONFIG_JSON_FILE, or
    a local `config.json` file by default.
    """

    host: str
    port: int = 80
    retries: int = 1
    debug: bool = False
    mode: str = "default"


def main():
    # parse_config will consult the built-in sources: CLI, env, and the example JSON
    # resolver (which will read ./config.json in this example). You can still
    # override values with env vars or CLI flags.
    cfg = parse_config(ServiceConfig)
    print(cfg)


if __name__ == "__main__":
    main()
