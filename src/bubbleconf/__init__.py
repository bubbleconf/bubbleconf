"""bubbleconf package (src layout)

Expose the public API: the ``config`` decorator and the
``parse_config`` function.
"""

from .config_annotation import config
from .parsers.parse_priority import parse_config

__all__ = ["config", "parse_config"]
