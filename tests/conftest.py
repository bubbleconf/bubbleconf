"""Test configuration helpers.

Ensure the repository root is on sys.path during test collection so tests can
import top-level modules like `parsers` even when pytest changes the working
directory.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    # Insert at front so local package modules (src/) are preferred over installed ones
    sys.path.insert(0, str(SRC))
