from typing import Iterable, Optional
import sys


class ConfigError(Exception):
    """Raised for one-or-more configuration validation problems.

    Attributes:
        missing: list[str] -- names of missing required fields
        malformed: list[str] -- descriptions of malformed fields
    """

    def __init__(
        self,
        missing: Iterable[str] | None = None,
        malformed: Iterable[str] | None = None,
        *,
        is_tty: Optional[bool] = None,
    ):
        self.missing = list(missing or [])
        self.malformed = list(malformed or [])
        # Determine whether to emit ANSI styling. If caller doesn't supply
        # an explicit value, assume stderr is the destination and check
        # whether it's a TTY.
        if is_tty is None:
            try:
                effective_is_tty = bool(sys.stderr and sys.stderr.isatty())
            except Exception:
                effective_is_tty = False
        else:
            effective_is_tty = bool(is_tty)
        # store structured data; message produced by __str__ or format()
        self._is_tty = effective_is_tty

    def __str__(self) -> str:
        # Use the instance's TTY detection so printing the exception will
        # include ANSI styling when appropriate.
        try:
            is_tty = bool(getattr(self, "_is_tty", False))
        except Exception:
            is_tty = False
        return self.format(is_tty=is_tty)

    def format(self, is_tty: bool) -> str:
        """Return a formatted error message. If is_tty is True, include ANSI styling.

        The formatted output mirrors previous behavior: missing fields header in
        bold red, malformed in bold yellow; field identifiers are bold cyan.
        """
        if not is_tty:
            parts = []
            if self.missing:
                parts.append("Missing required fields: " + ", ".join(self.missing))
            if self.malformed:
                parts.append("Malformed values: " + ", ".join(self.malformed))
            return "; ".join(parts) if parts else "Configuration error"

        BOLD = "\033[1m"
        RED = "\033[31m"
        YELLOW = "\033[33m"
        CYAN = "\033[36m"
        RESET = "\033[0m"
        lines = []
        if self.missing:
            styled = []
            for item in self.missing:
                if " (type: " in item and item.endswith(")"):
                    ident, rest = item.split(" (type: ", 1)
                    tpart = rest[:-1]
                    styled.append(f"{BOLD}{CYAN}{ident}{RESET} (type: {tpart})")
                else:
                    styled.append(f"{BOLD}{CYAN}{item}{RESET}")
            lines.append(
                f"{BOLD}{RED}Missing required fields:{RESET} {', '.join(styled)}"
            )
        if self.malformed:
            styled_m = []
            for item in self.malformed:
                if ": " in item:
                    ident, reason = item.split(": ", 1)
                    styled_m.append(f"{BOLD}{CYAN}{ident}{RESET}: {reason}")
                else:
                    styled_m.append(f"{BOLD}{CYAN}{item}{RESET}")
            lines.append(
                f"{BOLD}{YELLOW}Malformed values:{RESET} {', '.join(styled_m)}"
            )

        return "\n".join(lines)
