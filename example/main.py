from dataclasses import dataclass
from bubbleconf import parse_config


@dataclass
class ServiceConfig:
    host: str
    port: int = 80
    retries: int = 1
    debug: bool = False
    mode: str = "default"


cfg = parse_config(ServiceConfig, report=True)
print()
print(cfg)
