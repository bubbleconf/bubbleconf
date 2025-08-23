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

cfg = parse_config(MyConfig)
print(cfg)
```

You can set values by environment variables (VERSION, IS_COOL, ...), by CLI flags, or by defaults in the dataclass. The parser chooses values in a predictable priority order.

## CLI example

![](https://raw.githubusercontent.com/bubbleconf/bubbleconf/main/image-2.png)

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