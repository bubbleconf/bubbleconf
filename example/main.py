from dataclasses import dataclass
from typing import Annotated
from bubbleconf import Secret, parse_config


@dataclass
class ServiceConfig:
    host: str
    port: int = 80
    retries: int = 1
    debug: bool = False
    mode: str = "default"
    api_key: Annotated[str, Secret] = "dev-key"


cfg = parse_config(ServiceConfig, report=True, pretty_log=True)
print()
print(cfg)
