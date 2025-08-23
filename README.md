# bubbleconf

A tiny, battery-included configuration helper for Python projects. Use a dataclass to declare your configuration, then populate it from command-line arguments, environment variables, and sensible defaults with predictable priority.
<p align="center">

![](https://raw.githubusercontent.com/bubbleconf/bubbleconf/main/logo.svg)

</p>

## Installation

```bash
pip install bubbleconf
```

Or, for development from this repository:

```bash
# from the repo root
python -m pip install --upgrade pip
python -m pip install --upgrade uv
uv sync
```

## Hello example (programmatic)

```python
@config
@dataclass
class MyConfig:
	version: str
	is_cool: bool = False
	number_of_things: int = 0
	ratio: float = 1.0

def main():
	cfg = parse_config(MyConfig)
	print(cfg)

if __name__ == '__main__':
	main()
```

You can set values by environment variables (MYCONFIG_VERSION, MYCONFIG_IS_COOL, ...), by CLI flags, or by defaults in the dataclass. The parser chooses values in a predictable priority order.

## CLI example (using the included example/ project)

From the repository root you can run:

```bash
uv run example/main.py --is_cool=1 --version=0.1.1 --number_of_things=42 --ratio=0.1337
```

This will print a populated `MyConfig` instance.

## Advanced usage

- Boolean flags accept `0/1`, `true/false`, and common truthy/falsy strings.
- Unknown or invalid values raise a `ConfigError` with an easy-to-read message (TTY-aware when printed in terminals).

## Contributing

PRs are welcome. The project uses `uv` to manage the local environment. Run tests with:

```bash
uv run pytest -q
```

If you change packaging metadata, the CI workflow `.github/workflows/publish.yml` will build and either publish a dev build to TestPyPI or (for tagged commits) publish to PyPI.

## License

This project is MIT-licensed. See the `LICENSE` file for details.

---

If you'd like the README adjusted (add badges, expand examples, or include API docs), tell me what to include and I'll update it. 

## Combined sources example (JSON + env + CLI)

This example shows how `bubbleconf` composes multiple sources. The priority is: CLI flags override environment variables, which override values loaded from a JSON file. Defaults in the dataclass apply if a value is not provided from any source.

1) Create a JSON file `config.json` (example):

```json
{
  "host": "json.local",
  "port": 8080,
  "retries": 3,
  "mode": "safe"
}
```

2) Dataclass declaration (in your script):

```python
from dataclasses import dataclass
from bubbleconf import config, parse_config

@config
@dataclass
class ServiceConfig:
	host: str
	port: int = 80
	retries: int = 1
	debug: bool = False
	mode: str = "default"

def main():
	cfg = parse_config(ServiceConfig, json_file="config.json")
	print(cfg)

if __name__ == '__main__':
	main()
```

Note: pass `json_file="config.json"` (or whatever API your project exposes for loading JSON) — replace with the exact helper call if your project provides a convenience loader.

3) Export an environment variable that will override the JSON value (prefix uses the dataclass name):

```bash
export PORT=9090
export RETRIES=5
```

4) Run the program with a CLI flag that overrides env and JSON:

```bash
uv run example/main.py --host=cli.local --mode=fast
```

Expected result printed by the program (values annotated):

```
ServiceConfig(host='cli.local', port=9090, retries=5, debug=False, mode='fast')
```

Explanation:
- `host`: came from the CLI (`cli.local`).
- `port`: came from the environment (`PORT=9090`).
- `retries`: came from the environment (`RETRIES=5`) and overrides the JSON value of 3.
- `mode`: came from the CLI (`fast`), overriding the JSON value of `safe`.
- `debug`: left at the dataclass default `False` (not set in JSON/env/CLI).
