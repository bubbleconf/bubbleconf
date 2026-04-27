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

## Short example

```python
@dataclass
class MyConfig:
  version: str
  is_cool: bool = False
  number_of_things: int = 0
  ratio: float = 1.0

cfg = parse_config(MyConfig)
print(cfg)
```

You can set values by environment variables (`VERSION`, `IS_COOL`, ...), by CLI flags, or by defaults in the dataclass. The parser chooses values in a predictable priority order:

```console
$ VERSION="0.1.2" uv run test.py --is_cool=true                           
MyConfig(version='0.1.2', is_cool=True, number_of_things=0, ratio=1.0)
```
## CLI example

![](https://raw.githubusercontent.com/bubbleconf/bubbleconf/main/image-2.png)

## Advanced usage

- Boolean flags accept `0/1`, `true/false`, and common truthy/falsy strings.
- Unknown or invalid values raise a `ConfigError` with an easy-to-read message (TTY-aware when printed in terminals).

### `.env` file support

`bubbleconf` can read configuration from a `.env` file in the working directory.
The path can be overridden with the `DOTENV_FILE` environment variable.

The `dotenv` source is included in the default priority order
(`cli`, `env`, `dotenv`, `json`, `default`), so process environment variables
still take precedence over file values. Supported syntax:

```env
# comments and blank lines are ignored
NAME=Alice
export PORT=8080
GREETING="hello world"
TOKEN='shh # not a comment inside quotes'
DEBUG=true  # trailing comments after unquoted values are stripped
```

To use only `.env` (and dataclass defaults), pass an explicit priority:

```python
cfg = parse_config(MyConfig, priority=("dotenv", "default"))
```

### Pretty-printing the resolved configuration

Pass `pretty_log=True` to log the fully resolved configuration as a
boxed table at `INFO` level on the `bubbleconf` logger:

```python
import logging
logging.basicConfig(level=logging.INFO)

cfg = parse_config(MyConfig, pretty_log=True)
```

Output (colorized when stderr is a TTY; honours `NO_COLOR` and
`BUBBLECONF_FORCE_COLOR`):

```
Resolved configuration: MyConfig
┌────────┬───────────┬────────┐
│ Field  │ Value     │ Source │
├────────┼───────────┼────────┤
│ name   │ "Alice"   │ env    │
│ port   │ 9000      │ cli    │
│ debug  │ false     │ default│
└────────┴───────────┴────────┘
```

## Contributing

PRs are welcome. The project uses `uv` to manage the local environment. Run tests with:

```bash
uv run pytest -q
```

If you change packaging metadata, the CI workflow `.github/workflows/publish.yml` will build and either publish a dev build to TestPyPI or (for tagged commits) publish to PyPI.

## License

This project is MIT-licensed. See the `LICENSE` file for details.